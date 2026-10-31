"""Non-strategy bookkeeping leg identification (CLEANSE-1, kanban t_070590de).

The CLEANSE-1 book hygiene wave (2026-10-28, qr_research evidence
workspace/cleanse1_partA_2026-10-28.md) flattened stale/orphan paper positions
per operator directive and labeled every affected leg in
gold.paper_trade_skip_log:

  skip_kind = 'CLEANSE1_CLOSURE'   — book paused/retired; leg closed per the
                                     Part-C consolidation directive.
  skip_kind = 'RESET_STALE_SIGNAL' AND reason ILIKE '%flattened%'
                                   — orphaned stale holding flattened
                                     (e.g. us_stk_sue_mom_01_v2's 7 stale Aug
                                     positions + 1-share AVGO stub, +$63.1k).

These legs are bookkeeping, NOT strategy performance. Read-side rule for every
performance surface (Strategy Lab, Performance cards, Strategy Detail, Command
monthly P&L, Execution book overview):

  * EXCLUDE them from aggregated performance numbers (P&L, WR, PF, trade
    counts, monthly/yearly rollups, equity curves).
  * ANNOTATE them when the leg itself is listed (ledger rows).
  * SURFACE the excluded amount as `non_strategy_*` fields so the UI can show
    what was held back — never silently drop.

A ledger row matches a labeled closure on (strategy_id, ticker,
exit_date = skip_date): the flatten script stamped the synthetic-ledger exit
and the skip-log label on the same date. RESET_STALE_SIGNAL 're-sync entry'
rows (the replacement October book) are deliberately NOT matched — those
positions are the strategy's true current book.

Phantom positions: consumption.portfolio_positions_current is a derived ETL
cache that still listed the flattened legs as ACTIVE after the cleanse. A
positions_current row is a phantom iff its (strategy_id, ticker) carries a
closure label AND no OPEN paper_trades_synthetic row with the same share count
backs it (quantity match distinguishes a re-entered name like SJM from its
flattened predecessor). The durable fix is the ETL re-sync (qr_etl task);
serve-side we exclude phantoms from unrealized-P&L aggregates and report the
excluded amount as `non_strategy_unrealized`.
"""

from sqlalchemy import text

from app.db.safe_query import safe_query

# SQL predicate fragment. {alias} is the paper_trades_synthetic table alias.
# TRUE when the closed ledger row is a labeled non-strategy closure leg.
NON_STRATEGY_LEG_EXISTS = """
EXISTS (
    SELECT 1 FROM gold.paper_trade_skip_log k
    WHERE k.strategy_id = {alias}.strategy_id
      AND k.ticker = {alias}.ticker
      AND k.skip_date = {alias}.exit_date
      AND (
          k.skip_kind = 'CLEANSE1_CLOSURE'
          OR (k.skip_kind = 'RESET_STALE_SIGNAL' AND k.reason ILIKE '%flattened%')
      )
)
"""


def non_strategy_leg_exists(alias: str = "t") -> str:
    return NON_STRATEGY_LEG_EXISTS.format(alias=alias)


def fetch_closure_legs(db, strategy_ids=None):
    """{(strategy_id, ticker): {skip_kind, reason, skip_date}} for labeled
    non-strategy closure legs. Python-side map for row annotation."""
    sql = """
        SELECT strategy_id, ticker, skip_kind, reason, skip_date
        FROM gold.paper_trade_skip_log
        WHERE skip_kind = 'CLEANSE1_CLOSURE'
           OR (skip_kind = 'RESET_STALE_SIGNAL' AND reason ILIKE '%flattened%')
    """
    params = {}
    if strategy_ids:
        sql += " AND strategy_id = ANY(:ids)"
        params["ids"] = list(strategy_ids)
    try:
        rows = safe_query(db, sql, params, label="non_strategy_closure_legs")
    except Exception:
        return {}
    out = {}
    for r in rows:
        out[(r.strategy_id, r.ticker)] = {
            "skip_kind": r.skip_kind,
            "reason": r.reason,
            "skip_date": r.skip_date.isoformat() if r.skip_date else None,
        }
    return out


def fetch_phantom_position_keys(db, strategy_ids):
    """Set of (strategy_id, ticker, quantity) positions_current rows that are
    closure-labeled AND have no quantity-matching open ledger row — i.e. stale
    cache rows for legs the cleanse already flattened. Scoped to the closure
    label set so unrelated ETL lag is never masked."""
    closures = fetch_closure_legs(db, strategy_ids)
    if not closures:
        return set()
    closure_sids = sorted({sid for sid, _ in closures})
    try:
        pos_rows = safe_query(
            db,
            """
            SELECT strategy_id, ticker, quantity
            FROM consumption.portfolio_positions_current
            WHERE strategy_id = ANY(:ids)
              AND status = 'ACTIVE'
              AND execution_mode = 'PAPER_TRADING'
            """,
            {"ids": closure_sids},
            label="non_strategy_phantom_positions",
        )
        open_rows = safe_query(
            db,
            """
            SELECT strategy_id, ticker, n_shares
            FROM gold.paper_trades_synthetic
            WHERE strategy_id = ANY(:ids) AND status = 'open'
            """,
            {"ids": closure_sids},
            label="non_strategy_open_ledger",
        )
    except Exception:
        return set()
    open_qty = {}
    for r in open_rows:
        open_qty.setdefault((r.strategy_id, r.ticker), []).append(
            float(r.n_shares) if r.n_shares is not None else None)
    phantom = set()
    for p in pos_rows:
        key = (p.strategy_id, p.ticker)
        if key not in closures:
            continue
        qty = float(p.quantity) if p.quantity is not None else None
        backed = any(
            q is not None and qty is not None and abs(q - qty) < 1e-4
            for q in open_qty.get(key, [])
        )
        if not backed:
            phantom.add((p.strategy_id, p.ticker, round(qty or 0.0, 4)))
    return phantom
