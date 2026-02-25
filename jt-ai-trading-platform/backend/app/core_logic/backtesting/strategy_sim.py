import yfinance as yf
import pandas as pd
import numpy as np
import datetime
from sqlalchemy import text
from app.db.session import SessionLocal

def hkt_now():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)

async def simulate_strategy_performance():
    db = SessionLocal()
    now = hkt_now()
    
    # 1. Configuration
    benchmark_sym = "^GSPC" # S&P 500
    strategy_universe = ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN"] # Core 5
    
    # 2. Fetch History
    start_date = "2024-01-01"
    data = yf.download([benchmark_sym] + strategy_universe, start=start_date, interval="1d")['Close']
    if data.empty: return
    
    # 3. Calculate Returns
    returns = data.pct_change().dropna()
    
    # Strategy = Equal weight core 5
    strategy_returns = returns[strategy_universe].mean(axis=1)
    benchmark_returns = returns[benchmark_sym]
    
    # 4. Generate Cumulative Performance
    # YTD, QTD, MTD, 1D
    def get_cum_ret(series, start_dt):
        subset = series[series.index >= start_dt]
        if subset.empty: return 0.0
        return float((1 + subset).prod() - 1)

    today = returns.index[-1]
    jan_1 = pd.Timestamp(year=today.year, month=1, day=1)
    month_start = pd.Timestamp(year=today.year, month=today.month, day=1)
    q_month = ((today.month - 1) // 3) * 3 + 1
    q_start = pd.Timestamp(year=today.year, month=q_month, day=1)
    
    performance_map = {
        "YEARLY": get_cum_ret(strategy_returns, jan_1),
        "QUARTERLY": get_cum_ret(strategy_returns, q_start),
        "MONTHLY": get_cum_ret(strategy_returns, month_start),
        "DAILY": float(strategy_returns.iloc[-1])
    }
    
    bench_map = {
        "YEARLY": get_cum_ret(benchmark_returns, jan_1),
        "QUARTERLY": get_cum_ret(benchmark_returns, q_start),
        "MONTHLY": get_cum_ret(benchmark_returns, month_start),
        "DAILY": float(benchmark_returns.iloc[-1])
    }

    # 5. Persist to Gold Layer
    db.execute(text("DELETE FROM gold.strategy_performance WHERE true"))
    for period, ret in performance_map.items():
        db.execute(text("""
            INSERT INTO gold.strategy_performance (date, strategy_return, benchmark_return, period)
            VALUES (:d, :sr, :br, :p)
        """), {"d": today.date(), "sr": ret, "br": bench_map[period], "p": period})
    
    # 6. Generate Curve Data (Last 30 days for graph)
    db.execute(text("DELETE FROM gold.backtest_curve_data WHERE true"))
    strat_cum = (1 + strategy_returns.tail(30)).cumprod() * 100
    bench_cum = (1 + benchmark_returns.tail(30)).cumprod() * 100
    
    for i in range(len(strat_cum)):
        db.execute(text("""
            INSERT INTO gold.backtest_curve_data (timestamp, equity_value, benchmark_value)
            VALUES (:ts, :ev, :bv)
        """), {"ts": strat_cum.index[i].to_pydatetime(), "ev": float(strat_cum.iloc[i]), "bv": float(bench_cum.iloc[i])})
        
    db.commit()
    db.close()
    print("Strategy Backtest simulation complete.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(simulate_strategy_performance())
