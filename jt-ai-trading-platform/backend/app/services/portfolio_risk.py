"""
Portfolio Risk Management Module
Calculates risk metrics, correlations, and exposure analysis
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db.session import SessionLocal, QuantStrategy, Trade, Inventory

logger = logging.getLogger(__name__)


class PortfolioRiskManager:
    """Portfolio-level risk analysis and monitoring"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
    
    def get_portfolio_summary(self) -> Dict:
        """Get overall portfolio risk summary"""
        try:
            # Get all active strategies
            strategies = self.db.query(QuantStrategy).filter(
                QuantStrategy.is_active == True
            ).all()
            
            # Get open positions
            positions = self.db.query(Inventory).filter(
                Inventory.status == 'held'
            ).all()
            
            # Get recent trades
            recent_trades = self.db.execute(text("""
                SELECT * FROM consumption.trades 
                WHERE timestamp > NOW() - INTERVAL '30 days'
                ORDER BY timestamp DESC
            """)).fetchall()
            
            # Calculate metrics
            total_allocated = sum(
                s.params.get('allocated_capital', 10000) 
                for s in strategies if s.params
            )
            
            total_pnl = sum(s.current_pnl or 0 for s in strategies)
            total_trades = sum(s.total_trades or 0 for s in strategies)
            
            # Calculate drawdown from equity curves
            max_drawdown = self._calculate_portfolio_drawdown(strategies)
            
            # Risk by asset class
            asset_exposure = self._calculate_asset_exposure(strategies, positions)
            
            return {
                "summary": {
                    "total_strategies": len(strategies),
                    "open_positions": len(positions),
                    "total_allocated": round(total_allocated, 2),
                    "total_pnl": round(total_pnl, 2),
                    "total_return_pct": round((total_pnl / total_allocated) * 100, 2) if total_allocated else 0,
                    "total_trades": total_trades,
                    "max_drawdown_pct": round(max_drawdown, 2),
                    "risk_status": self._assess_risk_status(max_drawdown, total_pnl, total_allocated)
                },
                "asset_exposure": asset_exposure,
                "strategies": [{
                    "id": s.id,
                    "name": s.name,
                    "ticker": s.target_ticker,
                    "pnl": round(s.current_pnl or 0, 2),
                    "return_pct": round(((s.current_pnl or 0) / (s.params.get('allocated_capital', 10000) if s.params else 10000)) * 100, 2),
                    "trades": s.total_trades or 0,
                    "win_rate": round((s.winning_trades / s.total_trades * 100), 1) if s.total_trades else 0,
                    "status": "active" if s.is_active else "inactive"
                } for s in strategies]
            }
            
        except Exception as e:
            logger.error(f"Portfolio summary error: {e}")
            return {"error": str(e)}
    
    def get_correlation_matrix(self) -> Dict:
        """Calculate correlation matrix between strategies"""
        try:
            # Get strategies with equity curves
            strategies = self.db.query(QuantStrategy).filter(
                QuantStrategy.equity_curve.isnot(None)
            ).all()
            
            if len(strategies) < 2:
                return {
                    "message": "Need at least 2 strategies with equity curves",
                    "correlations": []
                }
            
            # Build equity curve DataFrame
            data = {}
            for s in strategies:
                if s.equity_curve and len(s.equity_curve) > 10:
                    # Extract equity values
                    equity_values = [point.get('val', 10000) for point in s.equity_curve]
                    # Calculate daily returns
                    returns = pd.Series(equity_values).pct_change().dropna()
                    if len(returns) > 5:
                        data[s.name] = returns
            
            if len(data) < 2:
                return {
                    "message": "Insufficient equity curve data",
                    "correlations": []
                }
            
            # Create DataFrame and calculate correlation
            df = pd.DataFrame(data)
            corr_matrix = df.corr()
            
            # Convert to list format
            correlations = []
            for i, strat1 in enumerate(corr_matrix.index):
                for j, strat2 in enumerate(corr_matrix.columns):
                    if i < j:  # Only upper triangle
                        correlations.append({
                            "strategy_1": strat1,
                            "strategy_2": strat2,
                            "correlation": round(corr_matrix.loc[strat1, strat2], 3)
                        })
            
            # Find highly correlated pairs (>0.7)
            high_corr = [c for c in correlations if abs(c["correlation"]) > 0.7]
            
            return {
                "strategies": list(data.keys()),
                "correlations": correlations,
                "high_correlation_pairs": high_corr,
                "diversification_score": round(1 - (len(high_corr) / len(correlations) if correlations else 0), 2)
            }
            
        except Exception as e:
            logger.error(f"Correlation matrix error: {e}")
            return {"error": str(e)}
    
    def get_var_analysis(self, confidence: float = 0.95) -> Dict:
        """Calculate Value at Risk (VaR) for the portfolio"""
        try:
            strategies = self.db.query(QuantStrategy).filter(
                QuantStrategy.equity_curve.isnot(None)
            ).all()
            
            all_returns = []
            for s in strategies:
                if s.equity_curve and len(s.equity_curve) > 10:
                    equity_values = [point.get('val', 10000) for point in s.equity_curve]
                    returns = pd.Series(equity_values).pct_change().dropna()
                    all_returns.extend(returns.tolist())
            
            if not all_returns:
                return {"message": "Insufficient data for VaR calculation"}
            
            returns_series = pd.Series(all_returns)
            
            # Calculate VaR
            var_95 = np.percentile(returns_series, 5)
            var_99 = np.percentile(returns_series, 1)
            
            # Calculate expected shortfall (CVaR)
            cvar_95 = returns_series[returns_series <= var_95].mean()
            
            # Get total portfolio value
            total_value = sum(
                s.params.get('allocated_capital', 10000) + (s.current_pnl or 0)
                for s in strategies if s.params
            )
            
            return {
                "confidence_levels": {
                    "95%": {
                        "var_pct": round(var_95 * 100, 2),
                        "var_amount": round(var_95 * total_value, 2),
                        "cvar_pct": round(cvar_95 * 100, 2),
                        "cvar_amount": round(cvar_95 * total_value, 2)
                    },
                    "99%": {
                        "var_pct": round(var_99 * 100, 2),
                        "var_amount": round(var_99 * total_value, 2)
                    }
                },
                "total_portfolio_value": round(total_value, 2),
                "volatility_annual": round(returns_series.std() * np.sqrt(252) * 100, 2),
                "sharpe_ratio": round(returns_series.mean() / returns_series.std() * np.sqrt(252), 2) if returns_series.std() > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"VaR analysis error: {e}")
            return {"error": str(e)}
    
    def get_concentration_risk(self) -> Dict:
        """Analyze position concentration risk"""
        try:
            strategies = self.db.query(QuantStrategy).filter(
                QuantStrategy.is_active == True
            ).all()
            
            if not strategies:
                return {"message": "No active strategies"}
            
            # Calculate allocations
            allocations = []
            for s in strategies:
                allocated = s.params.get('allocated_capital', 10000) if s.params else 10000
                allocations.append({
                    "strategy_id": s.id,
                    "name": s.name,
                    "ticker": s.target_ticker,
                    "allocated": allocated,
                    "pnl": s.current_pnl or 0
                })
            
            total = sum(a["allocated"] for a in allocations)
            
            # Calculate concentration percentages
            for a in allocations:
                a["allocation_pct"] = round((a["allocated"] / total) * 100, 2)
            
            # Sort by allocation
            allocations.sort(key=lambda x: x["allocation_pct"], reverse=True)
            
            # Check for concentration risk (>25% in single strategy)
            high_concentration = [a for a in allocations if a["allocation_pct"] > 25]
            
            return {
                "total_allocated": round(total, 2),
                "allocations": allocations,
                "concentration_risk": {
                    "high_concentration_strategies": high_concentration,
                    "largest_position_pct": allocations[0]["allocation_pct"] if allocations else 0,
                    "top_3_concentration": round(sum(a["allocation_pct"] for a in allocations[:3]), 2)
                },
                "recommendations": self._generate_concentration_recommendations(allocations)
            }
            
        except Exception as e:
            logger.error(f"Concentration risk error: {e}")
            return {"error": str(e)}
    
    def get_risk_alerts(self) -> List[Dict]:
        """Generate risk alerts based on portfolio conditions"""
        alerts = []
        
        try:
            strategies = self.db.query(QuantStrategy).filter(
                QuantStrategy.is_active == True
            ).all()
            
            # Check for large drawdowns
            for s in strategies:
                if s.params and s.current_pnl:
                    allocated = s.params.get('allocated_capital', 10000)
                    return_pct = (s.current_pnl / allocated) * 100
                    
                    if return_pct < -10:
                        alerts.append({
                            "level": "HIGH",
                            "type": "DRAWDOWN",
                            "strategy": s.name,
                            "message": f"Strategy {s.name} down {return_pct:.1f}%",
                            "recommendation": "Consider stopping strategy"
                        })
                        # Send Telegram alert
                        try:
                            from app.services.telegram_alerts import telegram_alerts
                            telegram_alerts.alert_drawdown(
                                strategy_name=s.name,
                                drawdown_pct=abs(return_pct),
                                current_pnl=s.current_pnl,
                                allocated=allocated
                            )
                        except Exception as e:
                            logger.error(f"Failed to send drawdown alert: {e}")
                    elif return_pct < -5:
                        alerts.append({
                            "level": "MEDIUM",
                            "type": "DRAWDOWN",
                            "strategy": s.name,
                            "message": f"Strategy {s.name} down {return_pct:.1f}%",
                            "recommendation": "Monitor closely"
                        })
            
            # Check correlation risk
            corr_data = self.get_correlation_matrix()
            if "high_correlation_pairs" in corr_data and corr_data["high_correlation_pairs"]:
                for pair in corr_data["high_correlation_pairs"]:
                    alerts.append({
                        "level": "MEDIUM",
                        "type": "CORRELATION",
                        "strategy": f"{pair['strategy_1']} / {pair['strategy_2']}",
                        "message": f"High correlation: {pair['correlation']:.2f}",
                        "recommendation": "Consider reducing one position"
                    })
            
            # Check concentration risk
            conc_data = self.get_concentration_risk()
            if "concentration_risk" in conc_data:
                if conc_data["concentration_risk"]["largest_position_pct"] > 30:
                    alerts.append({
                        "level": "HIGH",
                        "type": "CONCENTRATION",
                        "strategy": "Portfolio",
                        "message": f"Largest position is {conc_data['concentration_risk']['largest_position_pct']:.1f}% of portfolio",
                        "recommendation": "Reduce position size"
                    })
            
            return sorted(alerts, key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x["level"]])
            
        except Exception as e:
            logger.error(f"Risk alerts error: {e}")
            return []
    
    def _calculate_portfolio_drawdown(self, strategies: List[QuantStrategy]) -> float:
        """Calculate max drawdown across portfolio"""
        try:
            # Combine all equity curves
            combined_equity = {}
            
            for s in strategies:
                if s.equity_curve:
                    for point in s.equity_curve:
                        date = point.get('ts', '')
                        val = point.get('val', 10000)
                        if date:
                            if date in combined_equity:
                                combined_equity[date] += val
                            else:
                                combined_equity[date] = val
            
            if not combined_equity:
                return 0.0
            
            # Calculate drawdown
            sorted_dates = sorted(combined_equity.keys())
            peak = combined_equity[sorted_dates[0]]
            max_dd = 0.0
            
            for date in sorted_dates:
                equity = combined_equity[date]
                if equity > peak:
                    peak = equity
                dd = (peak - equity) / peak
                if dd > max_dd:
                    max_dd = dd
            
            return max_dd * 100  # Return as percentage
            
        except Exception as e:
            logger.error(f"Drawdown calculation error: {e}")
            return 0.0
    
    def _calculate_asset_exposure(
        self,
        strategies: List[QuantStrategy],
        positions: List[Inventory]
    ) -> Dict:
        """Calculate exposure by asset class"""
        exposure = {
            "FX": {"allocated": 0, "pnl": 0, "count": 0},
            "STOCK": {"allocated": 0, "pnl": 0, "count": 0},
            "CRYPTO": {"allocated": 0, "pnl": 0, "count": 0},
            "COMMODITY": {"allocated": 0, "pnl": 0, "count": 0}
        }
        
        for s in strategies:
            asset_class = "FX"  # Default
            if s.params:
                asset_class = s.params.get('asset_class', 'FX')
            elif s.target_ticker:
                if '=X' in s.target_ticker:
                    asset_class = 'FX'
                elif '-USD' in s.target_ticker:
                    asset_class = 'CRYPTO'
                else:
                    asset_class = 'STOCK'
            
            allocated = s.params.get('allocated_capital', 10000) if s.params else 10000
            
            if asset_class in exposure:
                exposure[asset_class]["allocated"] += allocated
                exposure[asset_class]["pnl"] += s.current_pnl or 0
                exposure[asset_class]["count"] += 1
        
        # Calculate percentages
        total = sum(e["allocated"] for e in exposure.values())
        if total > 0:
            for asset in exposure:
                exposure[asset]["allocation_pct"] = round((exposure[asset]["allocated"] / total) * 100, 2)
        
        return exposure
    
    def _assess_risk_status(self, drawdown: float, pnl: float, allocated: float) -> str:
        """Assess overall portfolio risk status"""
        if drawdown > 15 or (allocated > 0 and pnl / allocated < -0.15):
            return "CRITICAL"
        elif drawdown > 10 or (allocated > 0 and pnl / allocated < -0.10):
            return "HIGH"
        elif drawdown > 5 or (allocated > 0 and pnl / allocated < -0.05):
            return "ELEVATED"
        else:
            return "NORMAL"
    
    def _generate_concentration_recommendations(self, allocations: List[Dict]) -> List[str]:
        """Generate recommendations for concentration issues"""
        recommendations = []
        
        if not allocations:
            return recommendations
        
        # Check largest position
        if allocations[0]["allocation_pct"] > 30:
            recommendations.append(f"Reduce {allocations[0]['name']} - over 30% allocation")
        
        # Check top 3 concentration
        top3_pct = sum(a["allocation_pct"] for a in allocations[:3])
        if top3_pct > 70:
            recommendations.append(f"Top 3 positions account for {top3_pct}% - consider diversifying")
        
        # Check for underperforming concentrated positions
        for a in allocations[:3]:
            if a["allocation_pct"] > 20 and a["pnl"] < 0:
                recommendations.append(f"Concentrated position {a['name']} is losing money - consider exiting")
        
        return recommendations


# Initialize
portfolio_risk_manager = PortfolioRiskManager()