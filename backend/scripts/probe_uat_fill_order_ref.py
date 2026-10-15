#!/usr/bin/env python3
"""Regression probe — kanban t_02e14081.

Proves end-to-end that a TAGGED order's fill survives attribution:

  1. places a tagged order DIRECTLY at the gateway (separate clientId — this
     reproduces the 2026-10-09/10-15 incident shape, where qr_etl fired via
     its own connection and the backend's trades() cache never saw the order),
  2. waits for the fill,
  3. asserts GET /api/ib/tws/uat/fills echoes the fill with order_ref intact,
  4. (--run-mirror) runs qr_etl sync_paper_uat_to_gold.py and asserts the row
     in gold.paper_uat_fills carries order_ref.

Default instrument is a HK board lot (3988.HK x1000) so the probe can run
while HKEX is open; pass a US symbol during US hours if preferred. The
position is flattened again immediately (round trip) unless --no-flatten.

NOTE for the UAT registry guard: the probe order_ref (default
PROBE_t_02e14081) is not a 'strat:' ref, so mirror rows land with
strategy_id NULL by design. Exempt this ref in the guard like the
RECON_FLATTEN_* single-use exemptions.

Run:  ./.venv/bin/python scripts/probe_uat_fill_order_ref.py --run-mirror
"""
import argparse
import asyncio
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())  # py3.14 eventkit workaround

from ib_insync import IB, Stock, MarketOrder

ACCT = "DUP825942"
BACKEND = "http://127.0.0.1:8000"
ETL_SYNC = "/home/ubuntu/.hermes/profiles/qr_etl/home/trading-platform/agents/etl/sync_paper_uat_to_gold.py"
ETL_PYTHON = "/home/ubuntu/.venv/bin/python"


def backend_fills():
    with urllib.request.urlopen(f"{BACKEND}/api/ib/tws/uat/fills", timeout=20) as r:
        return json.loads(r.read().decode())


def wait_fill(trade, ib, timeout=90):
    start = time.time()
    while time.time() - start < timeout:
        ib.sleep(1)
        if trade.orderStatus.status == "Filled":
            return True
        if trade.orderStatus.status in ("Cancelled", "Inactive", "ApiCancelled"):
            return False
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=14002)
    ap.add_argument("--client-id", type=int, default=79)
    ap.add_argument("--symbol", default="3988.HK")
    ap.add_argument("--qty", type=int, default=1000,
                    help="HK board lot for 3988.HK is 1000; US round lot is 100")
    ap.add_argument("--order-ref", default="PROBE_t_02e14081")
    ap.add_argument("--no-flatten", action="store_true")
    ap.add_argument("--run-mirror", action="store_true",
                    help="run qr_etl sync_paper_uat_to_gold.py and verify the DB row")
    args = ap.parse_args()

    sym = args.symbol
    hk = sym.upper().endswith(".HK")
    ticker = sym[:-3] if hk else sym
    currency = "HKD" if hk else "USD"

    before = backend_fills()
    if not before.get("connected"):
        print("FATAL: backend UAT session not connected"); sys.exit(2)
    known_execs = {f.get("exec_id") for f in (before.get("data") or [])}
    print(f"backend connected, {len(known_execs)} existing fills today")

    ib = IB()
    ib.connect(args.host, args.port, clientId=args.client_id, timeout=15)
    order_ids = []
    try:
        if ACCT not in ib.managedAccounts():
            print(f"FATAL: {ACCT} not in managed accounts — refusing to trade"); sys.exit(2)

        contract = Stock(ticker, "SEHK" if hk else "SMART", currency)
        ib.qualifyContracts(contract)

        def fire(action):
            order = MarketOrder(action, args.qty)
            order.account = ACCT
            order.tif = "DAY"
            order.outsideRth = False
            order.orderRef = args.order_ref
            t = ib.placeOrder(contract, order)
            ib.sleep(2)
            print(f"{action} {args.qty} {sym}: ib_order_id={t.order.orderId} "
                  f"status={t.orderStatus.status} ref={t.order.orderRef!r}")
            return t

        buy = fire("BUY")
        if not wait_fill(buy, ib):
            print(f"FATAL: buy not filled (status={buy.orderStatus.status}) — cancelling, no retry")
            ib.cancelOrder(buy.order)
            sys.exit(2)
        order_ids.append(buy.order.orderId)

        if not args.no_flatten:
            sell = fire("SELL")
            if not wait_fill(sell, ib):
                print(f"WARN: flatten sell not filled (status={sell.orderStatus.status})")
            else:
                order_ids.append(sell.order.orderId)
    finally:
        ib.disconnect()

    # 3. Assert the backend endpoint echoes the ref.
    deadline = time.time() + 60
    echoed = {}
    while time.time() < deadline:
        resp = backend_fills()
        for f in (resp.get("data") or []):
            if f.get("order_id") in order_ids and f.get("exec_id") not in known_execs:
                echoed[f["order_id"]] = f
        if len(echoed) == len(order_ids):
            break
        time.sleep(3)
    missing = [oid for oid in order_ids if oid not in echoed]
    if missing:
        print(f"FATAL: fills for order_ids {missing} never appeared on /api/ib/tws/uat/fills")
        sys.exit(1)
    for oid, f in echoed.items():
        print(f"endpoint fill: order_id={oid} exec_id={f['exec_id']} "
              f"{f['side']} {f['qty']} {f['symbol']} @ {f['price']} order_ref={f['order_ref']!r}")
        if f.get("order_ref") != args.order_ref:
            print(f"FATAL: order_ref mismatch for order {oid}: "
                  f"expected {args.order_ref!r}, got {f.get('order_ref')!r}")
            sys.exit(1)
    print("PASS: /api/ib/tws/uat/fills echoes order_ref for all probe fills")

    if not args.run_mirror:
        print("(skipping DB leg; pass --run-mirror to verify gold.paper_uat_fills)")
        return

    # 4. Mirror + DB assertion.
    print("running qr_etl mirror sync ...")
    r = subprocess.run([ETL_PYTHON, ETL_SYNC], capture_output=True, text=True, timeout=180)
    print(r.stdout[-2000:])
    if r.returncode != 0:
        print(f"FATAL: mirror sync exited {r.returncode}: {r.stderr[-1000:]}")
        sys.exit(1)

    check = subprocess.run([ETL_PYTHON, "-c", """
import sys
sys.path.insert(0, '/home/ubuntu/.hermes/profiles/qr_etl/home/trading-platform/agents/etl/shared/scripts')
from db import get_connection
exec_ids = %r
conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT exec_id, order_id, order_ref, strategy_id, symbol, side, qty FROM gold.paper_uat_fills WHERE exec_id = ANY(%%s)", (exec_ids,))
for row in cur.fetchall():
    print(row)
cur.close(); conn.close()
""" % ([str(f["exec_id"]) for f in echoed.values()],)], capture_output=True, text=True, timeout=60)
    print(check.stdout)
    if check.returncode != 0:
        print(f"FATAL: DB check failed: {check.stderr[-1000:]}"); sys.exit(1)
    rows = [l for l in check.stdout.strip().splitlines() if l.strip()]
    ok = all(args.order_ref in l for l in rows) and len(rows) >= len(echoed)
    if not ok:
        print("FATAL: gold.paper_uat_fills rows missing or order_ref not intact")
        sys.exit(1)
    print("PASS: gold.paper_uat_fills rows carry order_ref intact")
    print(f"PROBE RESULT: GREEN ({datetime.now(timezone.utc).isoformat()})")


if __name__ == "__main__":
    main()
