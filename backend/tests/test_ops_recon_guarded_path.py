"""Tests for the guarded OPS_RECON order path (kanban t_a374fbeb / t_631f74bb).

OPS_RECON is the user-approved reconciliation route: account-management
covers (RECON_FLATTEN_<task_id>) that own no sleeve. The guard contract:

  1. Validation matrix — non-uat book, missing/wrong-prefix order_ref,
     missing idempotency_key, non-LMT order types, wrong account, and the
     REDUCE-ONLY position guard: a cover may never exceed, flip, or open a
     position (BUY needs an existing short >= qty; SELL an existing long).
  2. Idempotency — same key + same params replays the original result
     without a second broker order; same key + different params conflicts.
     The registry is persisted, so a retry after a backend restart still
     cannot duplicate the broker order.
  3. Mocked-gateway end-to-end LMT: a filled cover must surface via
     get_fills() with its RECON_FLATTEN_* order_ref and land on the qr_etl
     mirror with strategy_id='OPS_RECON' (never NULL).
  4. Registry durability — the orderRef/idempotency registry must live
     OUTSIDE the git checkout (a redeploy/git-clean must not wipe it), with
     rotating backups, and migrate the legacy repo-local file forward.

Everything here runs OFFLINE: stub IB handles, tmp registry paths, no
gateway, no live orders.
"""
import importlib.util
import json
import os
import sys
import types
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routes import ibkr as ibkr_routes
from app.routes.ibkr import place_ibkr_order
from app.services import ib_service
from app.services.ib_service import IBKRThreadedService


# ---------------------------------------------------------------------------
# Route-level stubs
# ---------------------------------------------------------------------------

class _StubUatService:
    """Stands in for ib_uat_service at the route layer: reports positions,
    records any place_order call (which must never fire for refused orders).
    """
    def __init__(self, positions):
        self._positions = positions
        self.placed = []

    def get_positions(self):
        return self._positions

    def place_order(self, **kwargs):
        self.placed.append(kwargs)
        return {"success": True, "order_id": 9001, "status": "Submitted"}


def _pos(symbol, qty):
    return {"symbol": symbol, "ticker": symbol, "qty": float(qty),
            "sec_type": "STK", "account": "DUP825942"}


def _payload(**over):
    p = {
        "symbol": "IEF", "action": "BUY", "quantity": 100,
        "order_type": "LMT", "limit_price": 95.0, "time_in_force": "DAY",
        "outside_rth": False,
        "book": "uat", "strategy_id": "OPS_RECON",
        "order_ref": "RECON_FLATTEN_t_test", "idempotency_key": "test-key-1",
    }
    p.update(over)
    return p


@pytest.fixture
def short_200(monkeypatch):
    """UAT book: short 200 IEF."""
    stub = _StubUatService([_pos("IEF", -200)])
    monkeypatch.setattr(ibkr_routes, "ib_uat_service", stub)
    return stub


# ---------------------------------------------------------------------------
# 1. Validation matrix
# ---------------------------------------------------------------------------

def test_rejects_non_uat_book(short_200):
    with pytest.raises(HTTPException) as ei:
        place_ibkr_order(_payload(book="live"), db=None)
    assert ei.value.status_code == 422
    assert "book='uat'" in ei.value.detail
    assert short_200.placed == []


def test_rejects_missing_order_ref(short_200):
    p = _payload()
    del p["order_ref"]
    with pytest.raises(HTTPException) as ei:
        place_ibkr_order(p, db=None)
    assert ei.value.status_code == 422
    assert "RECON_FLATTEN_" in ei.value.detail


def test_rejects_wrong_prefix_order_ref(short_200):
    with pytest.raises(HTTPException) as ei:
        place_ibkr_order(_payload(order_ref="strat:OPS_RECON"), db=None)
    assert ei.value.status_code == 422
    assert "RECON_FLATTEN_" in ei.value.detail


def test_rejects_missing_idempotency_key(short_200):
    p = _payload()
    del p["idempotency_key"]
    with pytest.raises(HTTPException) as ei:
        place_ibkr_order(p, db=None)
    assert ei.value.status_code == 422
    assert "idempotency_key" in ei.value.detail


def test_rejects_market_order(short_200):
    p = _payload(order_type="MKT")
    del p["limit_price"], p["time_in_force"], p["outside_rth"]
    with pytest.raises(HTTPException) as ei:
        place_ibkr_order(p, db=None)
    assert ei.value.status_code == 422
    assert "LMT-only" in ei.value.detail


def test_rejects_wrong_account(short_200):
    with pytest.raises(HTTPException) as ei:
        place_ibkr_order(_payload(account="DU9999999"), db=None)
    assert ei.value.status_code == 403
    assert "account guard" in ei.value.detail


def test_rejects_buy_qty_exceeding_short(short_200):
    """Covering more than the short would FLIP the book long — refused."""
    with pytest.raises(HTTPException) as ei:
        place_ibkr_order(_payload(quantity=300), db=None)
    assert ei.value.status_code == 422
    assert "flip" in ei.value.detail.lower() or "exceeds" in ei.value.detail.lower()


def test_rejects_buy_with_no_short(monkeypatch):
    """BUY with no existing short would OPEN a long — refused."""
    stub = _StubUatService([_pos("IEF", 150)])  # long, not short
    monkeypatch.setattr(ibkr_routes, "ib_uat_service", stub)
    with pytest.raises(HTTPException) as ei:
        place_ibkr_order(_payload(), db=None)
    assert ei.value.status_code == 422
    assert "no short" in ei.value.detail.lower()


def test_rejects_buy_when_flat(monkeypatch):
    """No position at all: any BUY opens a position — refused."""
    stub = _StubUatService([])
    monkeypatch.setattr(ibkr_routes, "ib_uat_service", stub)
    with pytest.raises(HTTPException) as ei:
        place_ibkr_order(_payload(), db=None)
    assert ei.value.status_code == 422


def test_rejects_sell_with_no_long(monkeypatch):
    """Symmetric guard: SELL against a short opens nothing — refused."""
    stub = _StubUatService([_pos("IEF", -100)])
    monkeypatch.setattr(ibkr_routes, "ib_uat_service", stub)
    with pytest.raises(HTTPException) as ei:
        place_ibkr_order(_payload(action="SELL"), db=None)
    assert ei.value.status_code == 422
    assert "no long" in ei.value.detail.lower()


def test_rejects_sell_qty_exceeding_long(monkeypatch):
    stub = _StubUatService([_pos("IEF", 100)])
    monkeypatch.setattr(ibkr_routes, "ib_uat_service", stub)
    with pytest.raises(HTTPException) as ei:
        place_ibkr_order(_payload(action="SELL", quantity=150), db=None)
    assert ei.value.status_code == 422


def test_rejects_when_positions_unavailable(monkeypatch):
    """Fail closed: positions unreadable (session down) -> 503, no order."""
    stub = _StubUatService(None)
    monkeypatch.setattr(ibkr_routes, "ib_uat_service", stub)
    with pytest.raises(HTTPException) as ei:
        place_ibkr_order(_payload(), db=None)
    assert ei.value.status_code == 503
    assert stub.placed == []


def test_full_cover_passes_and_stamps_ref(short_200):
    """Covering the ENTIRE short (qty == |short|) is the legitimate case."""
    out = place_ibkr_order(_payload(quantity=200), db=None)
    assert out["success"] is True
    assert out["order_ref"] == "RECON_FLATTEN_t_test"
    assert out["strategy_id"] == "OPS_RECON"
    assert short_200.placed and short_200.placed[0]["order_ref"] == "RECON_FLATTEN_t_test"
    assert short_200.placed[0]["idempotency_key"] == "test-key-1"
    assert short_200.placed[0]["order_type"] == "LMT"


def test_hk_symbol_matches_bare_position_symbol(monkeypatch):
    """HK orders carry the .HK suffix while positions report the bare code."""
    stub = _StubUatService([_pos("3988", -1000)])
    monkeypatch.setattr(ibkr_routes, "ib_uat_service", stub)
    out = place_ibkr_order(_payload(symbol="3988.HK", quantity=1000), db=None)
    assert out["success"] is True
    with pytest.raises(HTTPException):
        place_ibkr_order(_payload(symbol="3988.HK", quantity=1001), db=None)


def test_conflict_maps_to_409(monkeypatch):
    """Same key + different params surfaces as 409 Conflict, not a 500."""
    stub = _StubUatService([_pos("IEF", -200)])

    def _conflict(**_kw):
        return {"success": False,
                "error": "idempotency key 'k1' already used with different order params"}
    stub.place_order = _conflict
    monkeypatch.setattr(ibkr_routes, "ib_uat_service", stub)
    with pytest.raises(HTTPException) as ei:
        place_ibkr_order(_payload(), db=None)
    assert ei.value.status_code == 409
    assert "idempotency key" in ei.value.detail


def test_replay_response_is_flagged(monkeypatch):
    """A replayed order echoes idempotent_replay so the caller KNOWS no new
    order hit the gateway."""
    stub = _StubUatService([_pos("IEF", -200)])

    def _replay(**_kw):
        return {"success": True, "order_id": 9001, "status": "Filled",
                "idempotent_replay": True}
    stub.place_order = _replay
    monkeypatch.setattr(ibkr_routes, "ib_uat_service", stub)
    out = place_ibkr_order(_payload(), db=None)
    assert out["success"] is True
    assert out["idempotent_replay"] is True


# ---------------------------------------------------------------------------
# 2. Idempotency (service layer, offline)
# ---------------------------------------------------------------------------

def _make_service(tmp_path, monkeypatch):
    monkeypatch.setenv("IBKR_ORDER_REF_REGISTRY", str(tmp_path / "registry.json"))
    svc = IBKRThreadedService(host="127.0.0.1", port=14002, client_id=2)
    svc._refresh_completed_order_refs = lambda timeout=5: None
    return svc


class _CountingIb:
    """Stub gateway: counts placeOrder calls, fills LMT orders immediately."""
    def __init__(self, fill_status="Filled"):
        self.place_calls = []
        self._status = fill_status

    def qualifyContracts(self, contract):
        return [SimpleNamespace(symbol="IEF", localSymbol="IEF")]

    def placeOrder(self, contract, order):
        self.place_calls.append(order)
        n = len(self.place_calls)
        return SimpleNamespace(
            order=SimpleNamespace(orderId=100 + n,
                                  orderRef=getattr(order, "orderRef", None),
                                  permId=5000 + n),
            orderStatus=SimpleNamespace(status=self._status),
            fills=[SimpleNamespace(execution=SimpleNamespace(
                price=order.lmtPrice, shares=order.totalQuantity,
                execId=f"exec-{n}"))],
        )

    def sleep(self, _s):
        return None

    def trades(self):
        return []

    def fills(self):
        return []


def _cmd(request_id, key, qty=100, ref="RECON_FLATTEN_t_test"):
    return {"request_id": request_id, "symbol": "IEF", "action": "BUY",
            "quantity": qty, "order_type": "LMT", "limit_price": 95.0,
            "time_in_force": "DAY", "outside_rth": False,
            "order_ref": ref, "idempotency_key": key}


def test_idempotent_replay_returns_original_no_second_order(tmp_path, monkeypatch):
    svc = _make_service(tmp_path, monkeypatch)
    ib = _CountingIb()
    svc._ib = ib
    svc._process_order_request(_cmd("r1", "k1"))
    first = svc._results["r1"]
    assert first["success"] is True and first["order_id"] == 101

    svc._process_order_request(_cmd("r2", "k1"))  # retry, same key + params
    replay = svc._results["r2"]
    assert replay["success"] is True
    assert replay.get("idempotent_replay") is True
    assert replay["order_id"] == 101
    assert len(ib.place_calls) == 1  # NO second broker order


def test_idempotency_conflict_same_key_different_params(tmp_path, monkeypatch):
    svc = _make_service(tmp_path, monkeypatch)
    ib = _CountingIb()
    svc._ib = ib
    svc._process_order_request(_cmd("r1", "k1"))
    svc._process_order_request(_cmd("r2", "k1", qty=50))  # same key, new params
    conflict = svc._results["r2"]
    assert conflict["success"] is False
    assert "idempotency key" in conflict["error"]
    assert len(ib.place_calls) == 1


def test_idempotency_survives_backend_restart(tmp_path, monkeypatch):
    """The registry is persisted: a retry after a restart replays, never
    duplicates — this is what makes retiring the direct scripts safe."""
    svc1 = _make_service(tmp_path, monkeypatch)
    svc1._ib = _CountingIb()
    svc1._process_order_request(_cmd("r1", "k-restart"))
    assert svc1._results["r1"]["order_id"] == 101

    svc2 = _make_service(tmp_path, monkeypatch)  # fresh process, same registry
    svc2._ib = _CountingIb()
    svc2._process_order_request(_cmd("r2", "k-restart"))
    replay = svc2._results["r2"]
    assert replay.get("idempotent_replay") is True
    assert replay["order_id"] == 101
    assert len(svc2._ib.place_calls) == 0


# ---------------------------------------------------------------------------
# 3. Mocked-gateway end-to-end LMT -> fills -> mirror attribution
# ---------------------------------------------------------------------------

def _load_mirror_module():
    """Import the qr_etl mirror script (its `db` import is stubbed — only
    attribute_strategy is exercised, no DB connection is opened)."""
    path = os.path.expanduser(
        "~/.hermes/profiles/qr_etl/home/trading-platform/agents/etl/"
        "sync_paper_uat_to_gold.py")
    if not os.path.exists(path):
        pytest.skip("qr_etl mirror script not present on this host")
    if "db" not in sys.modules:
        stub = types.ModuleType("db")
        stub.get_connection = lambda *a, **k: None
        sys.modules["db"] = stub
    spec = importlib.util.spec_from_file_location("sync_paper_uat_to_gold", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fill(exec_id, order_id, symbol="IEF", side="BOT", shares=100, price=95.0,
          perm_id=0, order_ref=""):
    return SimpleNamespace(
        contract=SimpleNamespace(symbol=symbol, localSymbol=symbol),
        execution=SimpleNamespace(
            execId=exec_id, orderId=order_id, side=side, shares=shares,
            price=price, time=None, acctNumber="DUP825942",
            permId=perm_id, orderRef=order_ref),
    )


def test_e2e_lmt_cover_lands_on_mirror_as_ops_recon(tmp_path, monkeypatch):
    """Full offline chain: place LMT cover via the service with a stub
    gateway, watch it fill, recover it through get_fills(), and verify the
    qr_etl mirror attributes it strategy_id='OPS_RECON' (not NULL)."""
    svc = _make_service(tmp_path, monkeypatch)
    ib = _CountingIb()
    svc._ib = ib
    svc._process_order_request(_cmd("r1", "k-e2e", ref="RECON_FLATTEN_t_e2e"))
    result = svc._results["r1"]
    assert result["success"] is True
    assert result["status"] == "Filled"
    assert result["fill_price"] == 95.0
    # registry stamped at placement AND at fill observation
    assert svc._ref_registry["orders"]["101"] == "RECON_FLATTEN_t_e2e"
    assert svc._ref_registry["perms"]["5001"] == "RECON_FLATTEN_t_e2e"
    assert svc._ref_registry["execs"]["exec-1"] == "RECON_FLATTEN_t_e2e"

    # The fill surfaces through the same path the mirror consumes
    svc._connected = True
    svc._ib = _stub_ib_for_fills(
        fills=[_fill("exec-1", 101, perm_id=5001)])
    fills = svc.get_fills()
    assert len(fills) == 1
    assert fills[0]["order_ref"] == "RECON_FLATTEN_t_e2e"

    mirror = _load_mirror_module()
    assert mirror.attribute_strategy(fills[0]["order_ref"]) == "OPS_RECON"
    # row shape check: sync_fills must not count it as unattributed
    rows, unattributed = mirror.sync_fills(
        conn=None, fills=fills, as_of="2026-10-15T00:00:00+00:00", dry_run=True)
    assert rows == 1 and unattributed == 0


def _stub_ib_for_fills(trades=(), fills=()):
    return SimpleNamespace(trades=lambda: list(trades),
                           fills=lambda: list(fills))


def test_mirror_keeps_strat_refs_and_nulls_garbage():
    """Regression guard on the mirror change: strat: refs still map, unknown
    refs stay NULL (never fabricate attribution)."""
    mirror = _load_mirror_module()
    assert mirror.attribute_strategy("strat:HK_Quality_BlueChips") == "HK_Quality_BlueChips"
    assert mirror.attribute_strategy("RECON_FLATTEN_t_72843934") == "OPS_RECON"
    assert mirror.attribute_strategy("PROBE_t_02e14081") is None
    assert mirror.attribute_strategy(None) is None
    assert mirror.attribute_strategy("") is None


# ---------------------------------------------------------------------------
# 4. Registry durability: durable path, backups, legacy migration
# ---------------------------------------------------------------------------

def test_default_registry_lives_outside_the_repo(tmp_path, monkeypatch):
    """A redeploy / git-clean of the checkout must not wipe attribution."""
    monkeypatch.delenv("IBKR_ORDER_REF_REGISTRY", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    svc = IBKRThreadedService(host="127.0.0.1", port=14002, client_id=2)
    path = svc._ref_registry_path
    assert path.startswith(str(tmp_path)), path
    assert "jt-ai-trading-platform" not in path


def test_registry_writes_rotating_backups(tmp_path, monkeypatch):
    monkeypatch.setenv("IBKR_ORDER_REF_REGISTRY", str(tmp_path / "registry.json"))
    monkeypatch.setattr(ib_service, "_REGISTRY_BACKUP_KEEP", 2, raising=False)
    svc = IBKRThreadedService(host="127.0.0.1", port=14002, client_id=2)
    for i in range(3):
        svc._record_order_ref(100 + i, f"strat:t{i}")
    backup_dir = tmp_path / "backups"
    backups = sorted(backup_dir.glob("*.json"))
    assert 1 <= len(backups) <= 2  # rotated, bounded
    # newest backup is a valid registry snapshot
    data = json.loads(backups[-1].read_text())
    assert "orders" in data and "idempotency" in data


def test_legacy_repo_local_registry_migrates(tmp_path, monkeypatch):
    """The existing backend/data/ib_order_ref_registry_14002_2.json must be
    adopted, not abandoned, when the service moves to the durable path."""
    monkeypatch.delenv("IBKR_ORDER_REF_REGISTRY", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    legacy_dir = tmp_path / "legacy"
    legacy_dir.mkdir()
    legacy = legacy_dir / "ib_order_ref_registry_14002_2.json"
    legacy.write_text(json.dumps({
        "orders": {"4": "RECON_FLATTEN_t_7d69ab61"},
        "execs": {"0001e1": "RECON_FLATTEN_t_7d69ab61"},
        "perms": {"1861250084": "RECON_FLATTEN_t_72843934"},
        "idempotency": {"k-old": {"params": {"symbol": "IEF"},
                                  "result": {"order_id": 4}}},
    }))
    monkeypatch.setattr(ib_service, "_LEGACY_REGISTRY_DIR", str(legacy_dir),
                        raising=False)
    svc = IBKRThreadedService(host="127.0.0.1", port=14002, client_id=2)
    assert svc._ref_registry["orders"]["4"] == "RECON_FLATTEN_t_7d69ab61"
    assert svc._ref_registry["perms"]["1861250084"] == "RECON_FLATTEN_t_72843934"
    # migrated: durable copy now exists at the new location
    assert os.path.exists(svc._ref_registry_path)
