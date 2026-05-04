"""Portfolio risk analysis service.

Provides portfolio-level risk metrics including VaR, concentration analysis,
correlation proxies, and automated risk alerts.
"""

import logging
import math
from typing import List, Dict, Any

from app.db.session import SessionLocal
from app.db.safe_query import safe_query

logger = logging.getLogger(__name__)


class PortfolioRiskManager:
    """Analyzes portfolio risk across all active paper strategies."""

    def _get_db(self):
        """Create a new DB session."""
        return SessionLocal()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Aggregate portfolio-level summary statistics."""
        db = self._get_db()
        try:
            rows = safe_query(
                db,
                """
                SELECT strategy_id, ticker, invested_capital, unrealized_pnl,
                       realized_pnl, status, entry_price, current_price
                FROM gold.paper_strategies
                WHERE status = 'ACTIVE'
                """,
                label="portfolio_summary_positions",
            )

            if not rows:
                return self._empty_portfolio_summary()

            total_invested = 0.0
            total_unrealized = 0.0
            total_realized = 0.0
            strategy_pnl: Dict[str, float] = {}
            long_exposure = 0.0
            short_exposure = 0.0

            for r in rows:
                invested = float(r.invested_capital or 0)
                unrealized = float(r.unrealized_pnl or 0)
                realized = float(r.realized_pnl or 0)

                total_invested += invested
                total_unrealized += unrealized
                total_realized += realized

                sid = r.strategy_id or "unknown"
                strategy_pnl[sid] = strategy_pnl.get(sid, 0.0) + unrealized + realized

                # Approximate long/short exposure from price direction
                entry = float(r.entry_price or 0)
                current = float(r.current_price or 0)
                if entry > 0 and current > 0:
                    if current >= entry:
                        long_exposure += invested
                    else:
                        short_exposure += invested
                else:
                    long_exposure += invested

            best_strategy = max(strategy_pnl.items(), key=lambda x: x[1]) if strategy_pnl else ("", 0.0)
            worst_strategy = min(strategy_pnl.items(), key=lambda x: x[1]) if strategy_pnl else ("", 0.0)

            strategies_count_rows = safe_query(
                db,
                """
                SELECT COUNT(DISTINCT strategy_id) as cnt
                FROM gold.paper_strategies
                WHERE status = 'ACTIVE'
                """,
                label="portfolio_summary_strategy_count",
            )
            strategies_count = int(strategies_count_rows[0].cnt) if strategies_count_rows else 0

            return {
                "total_invested": round(total_invested, 2),
                "total_unrealized_pnl": round(total_unrealized, 2),
                "total_realized_pnl": round(total_realized, 2),
                "active_positions": len(rows),
                "strategies_count": strategies_count,
                "best_strategy": {"id": best_strategy[0], "pnl": round(best_strategy[1], 2)},
                "worst_strategy": {"id": worst_strategy[0], "pnl": round(worst_strategy[1], 2)},
                "long_exposure": round(long_exposure, 2),
                "short_exposure": round(short_exposure, 2),
                "net_exposure": round(long_exposure - short_exposure, 2),
            }
        except Exception as e:
            logger.error(f"Error in get_portfolio_summary: {e}")
            return self._empty_portfolio_summary()
        finally:
            db.close()

    def get_correlation_matrix(self) -> Dict[str, Any]:
        """Compute a ticker-overlap-based correlation proxy between strategies."""
        db = self._get_db()
        try:
            # Get active strategy tickers
            rows = safe_query(
                db,
                """
                SELECT ps.strategy_id, ps.ticker
                FROM gold.paper_strategies ps
                WHERE ps.status = 'ACTIVE'
                """,
                label="correlation_tickers",
            )

            if not rows:
                return {"strategies": [], "matrix": []}

            # Build strategy -> set of tickers
            strategy_tickers: Dict[str, set] = {}
            for r in rows:
                sid = r.strategy_id or "unknown"
                ticker = r.ticker or ""
                if sid not in strategy_tickers:
                    strategy_tickers[sid] = set()
                strategy_tickers[sid].add(ticker)

            strategies = sorted(strategy_tickers.keys())
            n = len(strategies)
            matrix = [[0.0] * n for _ in range(n)]

            for i in range(n):
                for j in range(n):
                    if i == j:
                        matrix[i][j] = 1.0
                    else:
                        tickers_i = strategy_tickers[strategies[i]]
                        tickers_j = strategy_tickers[strategies[j]]
                        union = tickers_i | tickers_j
                        if union:
                            overlap = len(tickers_i & tickers_j) / len(union)
                        else:
                            overlap = 0.0
                        matrix[i][j] = round(overlap, 4)

            return {
                "strategies": strategies,
                "matrix": matrix,
            }
        except Exception as e:
            logger.error(f"Error in get_correlation_matrix: {e}")
            return {"strategies": [], "matrix": []}
        finally:
            db.close()

    def get_var_analysis(self, confidence: float = 0.95) -> Dict[str, Any]:
        """Compute Value-at-Risk from historical trade PnL distribution."""
        db = self._get_db()
        try:
            rows = safe_query(
                db,
                """
                SELECT pnl, executed_at
                FROM gold.trade_executions
                WHERE pnl IS NOT NULL
                ORDER BY executed_at
                """,
                label="var_trade_pnl",
            )

            if not rows:
                return self._empty_var(confidence)

            pnl_values = [float(r.pnl) for r in rows]
            n = len(pnl_values)

            if n < 2:
                return self._empty_var(confidence)

            avg_pnl = sum(pnl_values) / n
            variance = sum((x - avg_pnl) ** 2 for x in pnl_values) / (n - 1)
            std_pnl = math.sqrt(variance)

            # Parametric VaR using normal approximation
            z_score = self._norm_ppf(1.0 - confidence)
            daily_var = avg_pnl + z_score * std_pnl
            monthly_var = daily_var * math.sqrt(21)  # ~21 trading days

            max_loss = min(pnl_values)

            return {
                "confidence": confidence,
                "daily_var": round(daily_var, 2),
                "monthly_var": round(monthly_var, 2),
                "max_loss_observed": round(max_loss, 2),
                "avg_daily_pnl": round(avg_pnl, 2),
                "pnl_std": round(std_pnl, 2),
                "n_observations": n,
            }
        except Exception as e:
            logger.error(f"Error in get_var_analysis: {e}")
            return self._empty_var(confidence)
        finally:
            db.close()

    def get_concentration_risk(self) -> Dict[str, Any]:
        """Analyze portfolio concentration by ticker, strategy, and asset class."""
        db = self._get_db()
        try:
            # Position data
            rows = safe_query(
                db,
                """
                SELECT ps.strategy_id, ps.ticker, ps.invested_capital,
                       COALESCE(sd.asset_class, 'UNKNOWN') as asset_class
                FROM gold.paper_strategies ps
                LEFT JOIN gold.strategy_definitions sd
                    ON ps.strategy_id = sd.strategy_id
                WHERE ps.status = 'ACTIVE'
                """,
                label="concentration_positions",
            )

            if not rows:
                return self._empty_concentration()

            total_invested = sum(float(r.invested_capital or 0) for r in rows)
            if total_invested <= 0:
                return self._empty_concentration()

            # Aggregate by ticker
            by_ticker: Dict[str, float] = {}
            by_strategy: Dict[str, float] = {}
            by_asset_class: Dict[str, float] = {}

            for r in rows:
                invested = float(r.invested_capital or 0)
                ticker = r.ticker or "UNKNOWN"
                sid = r.strategy_id or "UNKNOWN"
                ac = r.asset_class or "UNKNOWN"

                by_ticker[ticker] = by_ticker.get(ticker, 0.0) + invested
                by_strategy[sid] = by_strategy.get(sid, 0.0) + invested
                by_asset_class[ac] = by_asset_class.get(ac, 0.0) + invested

            def to_sorted_list(data: Dict[str, float], key_name: str, limit: int = 0):
                items = [
                    {
                        key_name: k,
                        "weight_pct": round((v / total_invested) * 100, 2),
                        "invested": round(v, 2),
                    }
                    for k, v in data.items()
                ]
                items.sort(key=lambda x: x["weight_pct"], reverse=True)
                if limit:
                    items = items[:limit]
                return items

            ticker_list = to_sorted_list(by_ticker, "ticker", limit=20)
            strategy_list = to_sorted_list(by_strategy, "strategy_id")
            asset_class_list = to_sorted_list(by_asset_class, "asset_class")

            # HHI calculation (sum of squared market shares, scale 0-10000)
            hhi = sum((v / total_invested * 100) ** 2 for v in by_ticker.values())

            # Top 5 concentration
            top_weights = sorted(
                [(v / total_invested) * 100 for v in by_ticker.values()], reverse=True
            )
            top_5 = sum(top_weights[:5])

            return {
                "by_ticker": ticker_list,
                "by_strategy": strategy_list,
                "by_asset_class": asset_class_list,
                "hhi_ticker": round(hhi, 2),
                "top_5_concentration": round(top_5, 2),
            }
        except Exception as e:
            logger.error(f"Error in get_concentration_risk: {e}")
            return self._empty_concentration()
        finally:
            db.close()

    def get_risk_alerts(self) -> List[Dict[str, Any]]:
        """Generate risk alerts based on predefined thresholds."""
        alerts: List[Dict[str, Any]] = []

        try:
            summary = self.get_portfolio_summary()
            concentration = self.get_concentration_risk()

            total_invested = summary.get("total_invested", 0)
            total_unrealized = summary.get("total_unrealized_pnl", 0)

            # Check single position concentration
            if total_invested > 0:
                for item in concentration.get("by_ticker", []):
                    weight = item.get("weight_pct", 0)
                    if weight > 35:
                        alerts.append({
                            "level": "critical",
                            "type": "position_concentration",
                            "message": f"Ticker {item['ticker']} represents {weight:.1f}% of portfolio (>35%)",
                            "value": weight,
                        })
                    elif weight > 20:
                        alerts.append({
                            "level": "warning",
                            "type": "position_concentration",
                            "message": f"Ticker {item['ticker']} represents {weight:.1f}% of portfolio (>20%)",
                            "value": weight,
                        })

            # Unrealized loss check
            if total_invested > 0 and total_unrealized < 0:
                loss_pct = abs(total_unrealized) / total_invested * 100
                if loss_pct > 10:
                    alerts.append({
                        "level": "warning",
                        "type": "unrealized_loss",
                        "message": f"Total unrealized loss is {loss_pct:.1f}% of invested capital (>10%)",
                        "value": round(loss_pct, 2),
                    })

            # HHI concentration check
            hhi = concentration.get("hhi_ticker", 0)
            if hhi > 2500:
                alerts.append({
                    "level": "warning",
                    "type": "hhi_concentration",
                    "message": f"Portfolio HHI is {hhi:.0f} (>2500), indicating high concentration",
                    "value": round(hhi, 2),
                })

            # Consecutive losses check
            self._check_consecutive_losses(alerts)

        except Exception as e:
            logger.error(f"Error generating risk alerts: {e}")

        return alerts

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_consecutive_losses(self, alerts: List[Dict[str, Any]]) -> None:
        """Check for strategies with consecutive losing trades."""
        db = self._get_db()
        try:
            rows = safe_query(
                db,
                """
                SELECT strategy_id, pnl, executed_at
                FROM gold.trade_executions
                WHERE pnl IS NOT NULL
                ORDER BY strategy_id, executed_at DESC
                """,
                label="consecutive_losses",
            )

            if not rows:
                return

            # Group by strategy and count recent consecutive losses
            current_strategy = None
            consecutive_losses = 0
            max_consecutive: Dict[str, int] = {}

            for r in rows:
                sid = r.strategy_id
                pnl = float(r.pnl)

                if sid != current_strategy:
                    # Save previous
                    if current_strategy is not None:
                        max_consecutive[current_strategy] = consecutive_losses
                    current_strategy = sid
                    consecutive_losses = 0

                if pnl < 0:
                    consecutive_losses += 1
                else:
                    # We only care about the most recent streak (from latest trade)
                    if current_strategy not in max_consecutive:
                        max_consecutive[current_strategy] = consecutive_losses
                    # Once we hit a win, the streak is broken; move on
                    # But we're iterating DESC so this is the latest streak
                    if sid not in max_consecutive:
                        max_consecutive[sid] = consecutive_losses
                    # Skip remaining trades for this strategy
                    # We can't skip easily, so just stop counting
                    consecutive_losses = -9999  # sentinel to ignore further

            # Don't forget the last strategy
            if current_strategy is not None and current_strategy not in max_consecutive:
                max_consecutive[current_strategy] = consecutive_losses

            for sid, streak in max_consecutive.items():
                if streak > 5:
                    alerts.append({
                        "level": "warning",
                        "type": "consecutive_losses",
                        "message": f"Strategy {sid} has {streak} consecutive losing trades",
                        "value": float(streak),
                    })
        except Exception as e:
            logger.error(f"Error checking consecutive losses: {e}")
        finally:
            db.close()

    @staticmethod
    def _norm_ppf(p: float) -> float:
        """Approximate inverse normal CDF (percent-point function).

        Uses the rational approximation by Abramowitz and Stegun (formula 26.2.23).
        Accurate to ~4.5e-4 for 0 < p < 1.
        """
        if p <= 0:
            return -4.0
        if p >= 1:
            return 4.0
        if p == 0.5:
            return 0.0

        if p > 0.5:
            return -PortfolioRiskManager._norm_ppf(1.0 - p)

        # Rational approximation for p < 0.5
        t = math.sqrt(-2.0 * math.log(p))
        c0 = 2.515517
        c1 = 0.802853
        c2 = 0.010328
        d1 = 1.432788
        d2 = 0.189269
        d3 = 0.001308
        z = t - (c0 + c1 * t + c2 * t * t) / (1.0 + d1 * t + d2 * t * t + d3 * t * t * t)
        return -z

    @staticmethod
    def _empty_portfolio_summary() -> Dict[str, Any]:
        return {
            "total_invested": 0.0,
            "total_unrealized_pnl": 0.0,
            "total_realized_pnl": 0.0,
            "active_positions": 0,
            "strategies_count": 0,
            "best_strategy": {"id": "", "pnl": 0.0},
            "worst_strategy": {"id": "", "pnl": 0.0},
            "long_exposure": 0.0,
            "short_exposure": 0.0,
            "net_exposure": 0.0,
        }

    @staticmethod
    def _empty_var(confidence: float) -> Dict[str, Any]:
        return {
            "confidence": confidence,
            "daily_var": 0.0,
            "monthly_var": 0.0,
            "max_loss_observed": 0.0,
            "avg_daily_pnl": 0.0,
            "pnl_std": 0.0,
            "n_observations": 0,
        }

    @staticmethod
    def _empty_concentration() -> Dict[str, Any]:
        return {
            "by_ticker": [],
            "by_strategy": [],
            "by_asset_class": [],
            "hhi_ticker": 0.0,
            "top_5_concentration": 0.0,
        }


# Module-level singleton
portfolio_risk_manager = PortfolioRiskManager()
