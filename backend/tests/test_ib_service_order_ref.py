"""Unit tests for the orderRef attribution registry (kanban t_02e14081).

Regression: GET /api/ib/tws/uat/fills used to resolve order_ref ONLY from
ib.trades() — this client connection's live cache. Fills arrive account-wide
via reqExecutions, so fills from orders placed by other clients (qr_etl
direct-gateway scripts) or before a reconnect surfaced with order_ref NULL,
breaking mirror/guard attribution (gold.paper_uat_fills NULL order_ref rows
for the 2026-10-09 RECON_FLATTEN fills).

These tests run fully offline: the IB handle is a stub, no gateway needed.
"""
import json
from types import SimpleNamespace

import pytest

from app.services.ib_service import IBKRThreadedService


def _make_service(tmp_path, monkeypatch):
    monkeypatch.setenv("IBKR_ORDER_REF_REGISTRY", str(tmp_path / "registry.json"))
    svc = IBKRThreadedService(host="127.0.0.1", port=14002, client_id=2)
    # Stub the refresh so get_fills doesn't queue/poll against a dead thread.
    svc._refresh_completed_order_refs = lambda timeout=5: None
    return svc


def _stub_ib(trades=(), fills=()):
    return SimpleNamespace(
        trades=lambda: list(trades),
        fills=lambda: list(fills),
    )


def _trade(order_id, order_ref, perm_id=0):
    return SimpleNamespace(order=SimpleNamespace(orderId=order_id, orderRef=order_ref,
                                                 permId=perm_id))


def _fill(exec_id, order_id, symbol="IEF", side="BOT", shares=100, price=95.5,
          perm_id=0, order_ref=""):
    return SimpleNamespace(
        contract=SimpleNamespace(symbol=symbol, localSymbol=symbol),
        execution=SimpleNamespace(
            execId=exec_id, orderId=order_id, side=side, shares=shares,
            price=price, time=None, acctNumber="DUP825942",
            permId=perm_id, orderRef=order_ref),
    )


def test_fill_from_foreign_client_resolves_via_registry(tmp_path, monkeypatch):
    """The 2026-10-09 regression: order placed by ANOTHER client — trades()
    is empty, but the registry (stamped at placement / completed refresh)
    still yields the ref."""
    svc = _make_service(tmp_path, monkeypatch)
    svc._connected = True
    svc._ib = _stub_ib(trades=[], fills=[_fill("0001e1", 4)])
    svc._record_order_ref(4, "RECON_FLATTEN_t_7d69ab61")

    fills = svc.get_fills()
    assert fills and fills[0]["order_ref"] == "RECON_FLATTEN_t_7d69ab61"
    assert fills[0]["order_id"] == 4
    assert fills[0]["side"] == "BUY"


def test_live_trades_override_registry(tmp_path, monkeypatch):
    svc = _make_service(tmp_path, monkeypatch)
    svc._connected = True
    svc._ib = _stub_ib(trades=[_trade(7, "strat:fresh")], fills=[_fill("0001e2", 7)])
    svc._record_order_ref(7, "strat:stale")
    # live trades() with a non-empty ref wins
    assert svc.get_fills()[0]["order_ref"] == "strat:fresh"
    # but a live trade with an EMPTY ref must not erase a good registry entry
    svc._ib = _stub_ib(trades=[_trade(7, "")], fills=[_fill("0001e2", 7)])
    assert svc.get_fills()[0]["order_ref"] == "strat:stale"


def test_exec_id_fallback(tmp_path, monkeypatch):
    svc = _make_service(tmp_path, monkeypatch)
    svc._connected = True
    svc._ib = _stub_ib(trades=[], fills=[_fill("0001e3", 99)])
    svc._record_order_ref(None, "strat:exec_only", exec_ids=["0001e3"])
    assert svc.get_fills()[0]["order_ref"] == "strat:exec_only"


def test_untagged_order_stays_null(tmp_path, monkeypatch):
    """Honesty contract: an order that genuinely carried no tag must surface
    order_ref None (the guard's UNTAGGED_FILL tripwire), never a fabricated
    value."""
    svc = _make_service(tmp_path, monkeypatch)
    svc._connected = True
    svc._ib = _stub_ib(trades=[], fills=[_fill("0001e4", 42)])
    assert svc.get_fills()[0]["order_ref"] is None


def test_disconnected_returns_none(tmp_path, monkeypatch):
    svc = _make_service(tmp_path, monkeypatch)
    assert svc.get_fills() is None


def test_refresh_completed_orders_merges_refs(tmp_path, monkeypatch):
    """reqCompletedOrders(apiOnly=False) recovers refs for orders placed by
    other clients — including execId-level mappings from their fills."""
    svc = _make_service(tmp_path, monkeypatch)
    completed = SimpleNamespace(
        order=SimpleNamespace(orderId=8, orderRef="RECON_FLATTEN_t_72843934", permId=1861250084),
        fills=[_fill("0001f5", 8, symbol="GLD", side="BOT", shares=50, price=380.0)],
    )
    svc._ib = SimpleNamespace(reqCompletedOrders=lambda apiOnly: [completed],
                              reqExecutions=lambda: [])
    svc._process_refresh_completed_orders({"request_id": "r1"})
    assert svc._results["r1"] == {"success": True, "completed_orders": 1, "refs": 1,
                                  "executions": 0}
    assert svc._ref_registry["orders"]["8"] == "RECON_FLATTEN_t_72843934"
    assert svc._ref_registry["perms"]["1861250084"] == "RECON_FLATTEN_t_72843934"
    assert svc._ref_registry["execs"]["0001f5"] == "RECON_FLATTEN_t_72843934"


def test_cross_client_join_on_perm_id(tmp_path, monkeypatch):
    """The exact 2026-10-15 observation: completedOrders and execDetails both
    report orderId=0 for orders placed by another API client. The permId map
    must still attribute the fill."""
    svc = _make_service(tmp_path, monkeypatch)
    completed = SimpleNamespace(
        order=SimpleNamespace(orderId=0, orderRef="PROBE_t_02e14081", permId=1861250085),
        fills=[])
    svc._connected = True
    svc._ib = SimpleNamespace(
        reqCompletedOrders=lambda apiOnly: [completed],
        # foreign fill: orderId=0, no orderRef on the execution
        reqExecutions=lambda: [_fill("0000f0e6.6ad00188.01.01", 0, symbol="3988",
                                     side="BOT", shares=1000, price=6.095,
                                     perm_id=1861250085)],
        trades=lambda: [], fills=lambda: [])
    svc._refresh_completed_order_refs = lambda timeout=5: svc._process_refresh_completed_orders({"request_id": "x"})
    fills = svc.get_fills()
    assert len(fills) == 1
    assert fills[0]["order_ref"] == "PROBE_t_02e14081"
    assert fills[0]["perm_id"] == 1861250085
    # garbage "0" orderId must never enter the registry orders map
    assert "0" not in svc._ref_registry["orders"]


def test_order_ref_direct_from_execution(tmp_path, monkeypatch):
    """TWS execDetails carries orderRef on the execution itself — prefer it."""
    svc = _make_service(tmp_path, monkeypatch)
    svc._connected = True
    svc._ib = _stub_ib(trades=[], fills=[_fill("0001e9", 55, order_ref="strat:direct")])
    assert svc.get_fills()[0]["order_ref"] == "strat:direct"


def test_foreign_client_fill_visible_via_exec_cache(tmp_path, monkeypatch):
    """The 2026-10-15 probe finding: a fill placed by ANOTHER client never
    reaches this connection's fills() in real time. reqExecutions() recovers
    it; get_fills merges the cache, dedupes on exec_id, and attributes via
    the completed-orders ref map."""
    svc = _make_service(tmp_path, monkeypatch)
    svc._refresh_completed_order_refs = IBKRThreadedService._refresh_completed_order_refs.__get__(svc)
    # drive the refresh synchronously instead of via the queue
    svc._refresh_completed_order_refs = lambda timeout=5: svc._process_refresh_completed_orders({"request_id": "x"})
    foreign_fill = _fill("0001c9", 21, symbol="3988", side="BOT", shares=1000, price=4.6)
    completed = SimpleNamespace(
        order=SimpleNamespace(orderId=21, orderRef="PROBE_t_02e14081"),
        fills=[foreign_fill])
    svc._connected = True
    svc._ib = SimpleNamespace(
        reqCompletedOrders=lambda apiOnly: [completed],
        reqExecutions=lambda: [foreign_fill],
        trades=lambda: [], fills=lambda: [])
    svc._results.pop("x", None)
    fills = svc.get_fills()
    assert len(fills) == 1
    assert fills[0]["exec_id"] == "0001c9"
    assert fills[0]["order_ref"] == "PROBE_t_02e14081"


def test_exec_cache_dedupes_against_live_fills(tmp_path, monkeypatch):
    svc = _make_service(tmp_path, monkeypatch)
    live = _fill("0001d1", 30)
    svc._connected = True
    svc._ib = _stub_ib(trades=[], fills=[live])
    svc._exec_cache = {"0001d1": {"exec_id": "0001d1", "order_id": 30, "symbol": "IEF",
                                  "side": "BUY", "qty": 100.0, "price": 95.5,
                                  "time": None, "account": "DUP825942"}}
    fills = svc.get_fills()
    assert len(fills) == 1  # not double-counted


def test_refresh_completed_orders_failure_reported(tmp_path, monkeypatch):
    svc = _make_service(tmp_path, monkeypatch)
    def _boom(apiOnly):
        raise RuntimeError("gateway gone")
    svc._ib = SimpleNamespace(reqCompletedOrders=_boom)
    svc._process_refresh_completed_orders({"request_id": "r2"})
    assert svc._results["r2"]["success"] is False
    assert "gateway gone" in svc._results["r2"]["error"]


def test_registry_persists_across_restart(tmp_path, monkeypatch):
    svc = _make_service(tmp_path, monkeypatch)
    svc._record_order_ref(11, "strat:persist_me", exec_ids=["0001aa"])
    # simulate backend restart: new instance, same registry path
    svc2 = _make_service(tmp_path, monkeypatch)
    svc2._connected = True
    svc2._ib = _stub_ib(trades=[], fills=[_fill("0001aa", 11)])
    assert svc2.get_fills()[0]["order_ref"] == "strat:persist_me"
