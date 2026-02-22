import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from sqlalchemy import text
import logging
import datetime
import json
import random
from app.db.session import (
    SessionLocal, ConsumptionStock, ConsumptionFx, ConsumptionCommodity, ConsumptionCrypto, ConsumptionMarket, GlobalState
)
from app.core_logic.analysis.time_series.prophet_forecast import get_prophet_prediction
from app.core_logic.agents.research_swarm import research_swarm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def to_native(val):
    if val is None: return None
    if isinstance(val, (np.float64, np.float32)): return float(val)
    if isinstance(val, (np.int64, np.int32)): return int(val)
    if pd.isna(val): return None
    return val

def generate_sparkline(prices):
    if len(prices) < 2: return []
    p_min, p_max = min(prices), max(prices)
    if p_max == p_min: return [50] * len(prices)
    return [round(((p - p_min) / (p_max - p_min)) * 100, 1) for p in prices]

def hkt_now():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)

def detect_candlestick_patterns(df):
    """
    Heuristic-based candlestick pattern detection.
    """
    try:
        if len(df) < 10: return None, 0.0
        
        # Last 3 candles
        c1 = df.iloc[-1] # Current
        c2 = df.iloc[-2] # Previous
        c3 = df.iloc[-3] # Before previous
        
        o, h, l, c = c1['Open'], c1['High'], c1['Low'], c1['Close']
        body = abs(c - o)
        total_range = h - l
        if total_range == 0: return None, 0.0
        
        # 1. DOJI
        if body / total_range < 0.1:
            return "DOJI", 0.0
        
        # 2. HAMMER (Small body at top, long lower wick)
        wick_bottom = min(o, c) - l
        wick_top = h - max(o, c)
        if wick_bottom > body * 1.5 and wick_top < body * 0.5:
            return "HAMMER", 1.0
            
        # 3. SHOOTING STAR (Small body at bottom, long upper wick)
        if wick_top > body * 1.5 and wick_bottom < body * 0.5:
            return "SHOOTING STAR", -1.0
            
        # 4. ENGULFING
        o2, c2_val = c2['Open'], c2['Close']
        body2 = abs(c2_val - o2)
        if body > body2:
            if c > o and c2_val < o2: return "BULLISH ENGULFING", 1.0
            if c < o and c2_val > o2: return "BEARISH ENGULFING", -1.0

        # 5. MARUBOZU (Long body, almost no wicks)
        if body / total_range > 0.9:
            return "MARUBOZU", (1.0 if c > o else -1.0)
                
        return None, 0.0
    except: return None, 0.0

# --- INSTITUTIONAL BACKTESTING ENGINE (High Fidelity) ---
def calculate_risk_metrics(returns):
    if len(returns) < 5: return {"sharpe": 0.0, "mdd": "0.0%"}
    avg_ret = np.mean(returns); std_ret = np.std(returns)
    sharpe = (avg_ret * 252 - 0.02) / (std_ret * np.sqrt(252)) if std_ret > 0 else 0.0
    cum_ret = np.cumsum(returns); peak = np.maximum.accumulate(cum_ret); drawdown = peak - cum_ret; mdd = np.max(drawdown)
    return { "sharpe": round(float(sharpe), 2), "mdd": f"{float(mdd*100):.1f}%" }

def simulate_historical_accuracy(df, horizon_type, ticker, asset_class='STOCK'):
    db = SessionLocal()
    st_thresh = db.execute(text("SELECT target_pct FROM gold.strategy_thresholds WHERE horizon = '1D'")).fetchone()
    config = db.execute(text("SELECT win_rate_target FROM gold.strategy_configs WHERE asset_class = :ac"), {"ac": asset_class}).fetchone()
    target_wr = config[0] if config else 0.50
    db.close()
    
    target_pct = (st_thresh[0] if st_thresh else 1.5)
    if target_wr > 0.65: target_pct *= 0.8 
    days = 5 if asset_class != 'FX' else 3
    if horizon_type == 'Long Term': days = 10; target_pct = 5.0
    
    if len(df) < 60: return 0.55, {"sharpe": 1.0, "mdd": "10.0%"}
    wins = 0; total = 0; returns = []
    for i in range(len(df)-90, len(df)-days):
        total += 1
        entry = df['Close'].iloc[i]; window = df['Close'].iloc[i+1 : i+days+1]
        if not window.empty:
            if window.max() > entry * (1 + target_pct/100.0): wins += 1
        returns.append(window.iloc[0]/entry - 1 if not window.empty else 0)
    
    wr = round(wins / (total or 1), 2)
    return wr, calculate_risk_metrics(returns)

def calculate_horizon_estimates(p_7d_raw, vol_ann, win_rate):
    """
    Conservative horizon estimates with realistic caps.
    A good strategy should target 5-15% monthly, not 25%+.
    """
    p_7d = float(p_7d_raw)
    
    # More conservative confidence adjustment
    # Win rate of 0.5 = 50% confidence, win rate of 0.7 = 75% confidence
    confidence_adj = 0.3 + (win_rate * 0.5)
    
    # 1D estimate - very conservative, typically 0.1-0.5%
    est_1d = (p_7d / 7.0) * confidence_adj * 0.5  # Additional 50% dampening
    
    # Monthly estimate with strong mean reversion dampening
    time_ratio = 30.0 / 7.0
    # Higher damping for longer timeframes (square root rule with adjustment)
    damping_exponent = 0.5 if vol_ann > 0.5 else 0.6
    scaling_factor = (time_ratio ** damping_exponent) * confidence_adj * 0.7
    est_1m = p_7d * scaling_factor
    
    # STRICT LIMITS - Realistic trading returns:
    # Conservative: 2-5% monthly
    # Moderate: 5-10% monthly  
    # Aggressive: 10-15% monthly (rare)
    # Anything above 15% is unrealistic for sustained periods
    base_limit = 8.0 if vol_ann < 0.3 else 12.0 if vol_ann < 0.5 else 15.0
    
    # Further reduce limit based on win rate - low win rate = lower expectations
    adjusted_limit = base_limit * (0.5 + win_rate * 0.5)
    
    est_1m = max(min(est_1m, adjusted_limit), -adjusted_limit)
    est_1d = max(min(est_1d, 2.0), -2.0)  # Daily moves rarely > 2%
    
    # 7D estimate - moderate between 1D and 1M
    est_7d = p_7d * confidence_adj * 0.8
    est_7d = max(min(est_7d, adjusted_limit * 0.6), -adjusted_limit * 0.6)
    
    return { 
        "1d": f"{est_1d:+.2f}%", 
        "7d": f"{est_7d:+.2f}%", 
        "1m": f"{est_1m:+.2f}%" 
    }

def detect_market_regime():
    try:
        t = yf.Ticker("^DJI"); df = t.history(period="1mo")
        if df.empty: return "STAGNANT"
        vol = df['Close'].pct_change().std() * np.sqrt(252)
        trend = (df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1
        if vol > 0.35: return "CRASH" if trend < -0.05 else "PANIC"
        if vol < 0.15: return "GROWTH" if trend > 0.02 else "STAGNANT"
        return "STAGNANT"
    except: return "STAGNANT"

def calculate_correlation(df, benchmark_ticker):
    try:
        b_t = yf.Ticker(benchmark_ticker); b_df = b_t.history(period="1y")
        if b_df.empty: return 0.5
        combined = pd.concat([df['Close'], b_df['Close']], axis=1).dropna()
        if len(combined) < 20: return 0.5
        return round(float(combined.tail(30).pct_change().corr().iloc[0, 1]), 2)
    except: return 0.5

def calculate_atr_stops(df, multiplier=2.0):
    try:
        tr = pd.concat([df['High']-df['Low'], np.abs(df['High']-df['Close'].shift()), np.abs(df['Low']-df['Close'].shift())], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean().iloc[-1]
        curr_p = df['Close'].iloc[-1]
        return { "sl": f"${float(curr_p - atr*multiplier):.2f}", "rr": "1:2.0", "atr": round(float(atr), 2) }
    except: return {"sl": "---", "rr": "---", "atr": 0}

def get_macro_drag():
    try:
        t_df = yf.Ticker("^TNX").history(period="5d"); d_df = yf.Ticker("DX-Y.NYB").history(period="5d")
        yield_spike = (t_df['Close'].iloc[-1]/t_df['Close'].iloc[0])-1 if not t_df.empty else 0
        dollar_strength = (d_df['Close'].iloc[-1]/d_df['Close'].iloc[0])-1 if not d_df.empty else 0
        drag = 1.0
        if yield_spike > 0.02: drag -= 0.1
        if dollar_strength > 0.01: drag -= 0.05
        return drag
    except: return 1.0

async def get_news_sentiment_score(ticker):
    try:
        from app.core_logic.tools.search import search_tool
        news = search_tool.search_market_news(f"{ticker} stock latest news sentiment")
        res = await research_swarm.llm.ainvoke(f"Analyze news for {ticker}: {news}. Return ONLY a number between 0.0 and 1.0.")
        return max(0.0, min(1.0, float(res.content.strip())))
    except: return 0.5

# --- WORKER 5: STOCKS ---
async def refresh_stock_layer():
    db = SessionLocal(); now = hkt_now(); regime = detect_market_regime(); macro_drag = get_macro_drag()
    
    # Import new backtester
    from app.core_logic.backtesting.strategy_backtester import StrategyBacktester, generate_signals_from_backtest
    backtester = StrategyBacktester()
    
    res = db.execute(text("SELECT * FROM gold.asset_registry WHERE asset_class = 'STOCK' AND is_active = True"))
    stocks = res.fetchall()
    db.execute(text("DELETE FROM consumption.stock WHERE true")); db.commit()
    
    for s in stocks:
        try:
            t = yf.Ticker(s.ticker); df = t.history(period="1y")
            if df.empty: continue
            if len(df) < 60: continue  # Need minimum data
            
            info = t.info; pe = to_native(info.get('trailingPE') or info.get('forwardPE')) or 0.0
            fcf = to_native(info.get('freeCashflow')); fcf_str = f"${fcf/1e9:.1f}B" if fcf else "---"
            curr_p = to_native(df['Close'].iloc[-1]); prev_p = to_native(df['Close'].iloc[-2]) if len(df)>1 else curr_p
            rsi = to_native(ta.rsi(df['Close'], length=14).iloc[-1]) or 50
            
            # NEW: Use proper backtester with entry/exit rules
            signal_data = generate_signals_from_backtest(df, s.ticker)
            win_rate = signal_data['win_rate']
            
            # Get best strategy result for additional metrics
            strategy_name, result = backtester.get_best_strategy(df)
            
            # Calculate estimates based on backtest performance
            est_1d = f"{signal_data['expected_return']/5:+.2f}%" if signal_data['expected_return'] else "+0.00%"
            est_7d = f"{signal_data['expected_return']:+.2f}%" if signal_data['expected_return'] else "+0.00%"
            est_1m = f"{signal_data['expected_return']*4:+.2f}%" if signal_data['expected_return'] else "+0.00%"
            
            # Sentiment
            sent = await get_news_sentiment_score(s.ticker)
            cdl_pattern, cdl_sentiment = detect_candlestick_patterns(df)
            
            # NEW SCORING: Based on backtest metrics
            # score = (win_rate * 0.4) + (sharpe_ratio * 0.2) + (sentiment * 0.2) + (signal_strength * 0.2)
            sharpe_contrib = max(0, min(1, result.sharpe_ratio / 3.0))  # Normalize Sharpe to 0-1
            signal_strength = 1.0 if signal_data['signal'] == 'BUY' else 0.5 if signal_data['signal'] == 'HOLD' else 0.0
            
            score = ((win_rate * 0.35) + 
                    (sharpe_contrib * 0.25) + 
                    (sent * 0.20) + 
                    (signal_strength * 0.20)) * macro_drag
            score = round(max(min(score, 0.98), 0.10), 2)
            
            # Filter out poor performers
            if result.sharpe_ratio < 0.5 or win_rate < 0.4: 
                continue
            
            # Strategy tags based on best strategy
            tags = []
            if result.win_rate > 0.65:
                tags.append("HIGH_ACCURACY")
            if strategy_name == 'mean_reversion':
                tags.append("MEAN_REVERSION")
            elif strategy_name == 'trend_following':
                tags.append("TREND_FOLLOW")
            elif strategy_name == 'breakout':
                tags.append("BREAKOUT")
            if cdl_pattern:
                tags.append(f"CDL_{cdl_pattern.replace(' ','_')}")
            
            # Calculate ATR-based stop
            try:
                atr = ta.atr(df['High'], df['Low'], df['Close'], length=14).iloc[-1]
                stop_loss = f"${curr_p - (2 * atr):.2f}"
                rr_ratio = "1:2.0"
            except:
                stop_loss = f"${curr_p * 0.95:.2f}"
                rr_ratio = "1:2.0"
            
            # Logic summary with backtest info
            logic_summary = (f"{strategy_name.replace('_', ' ').title()} strategy. "
                           f"Backtest: {win_rate*100:.0f}% WR, {result.sharpe_ratio:.2f} Sharpe, "
                           f"{result.num_trades} trades. "
                           f"Signal: {signal_data['signal']}. "
                           f"{cdl_pattern or 'No pattern'} detected. "
                           f"Sentiment: {sent*100:.0f}%.")
            
            db.execute(text("INSERT INTO gold.stock_metrics (date, ticker, sector, close, rsi_14, prophet_forecast, candlestick_pattern, candlestick_sentiment) VALUES (:ts, :t, 'Equity', :c, :rsi, :pf, :cp, :cs) ON CONFLICT (ticker, date) DO NOTHING"), { "ts": now, "t": s.ticker, "c": curr_p, "rsi": rsi, "pf": 0.0, "cp": cdl_pattern, "cs": cdl_sentiment })
            
            db.add(ConsumptionStock(
                timestamp=now, 
                ticker=s.ticker, 
                market=s.market, 
                horizon=s.horizon, 
                final_score=score, 
                close_price=curr_p, 
                daily_change=((curr_p-prev_p)/prev_p*100), 
                est_1d=est_1d, 
                est_7d=est_7d, 
                est_1m=est_1m, 
                win_rate=win_rate, 
                strategy_tags=tags, 
                stop_loss=stop_loss, 
                rr_ratio=rr_ratio, 
                candlestick_pattern=cdl_pattern, 
                sparkline=generate_sparkline(df['Close'].tail(24).tolist()), 
                logic_summary=logic_summary,
                metrics={
                    "rsi": round(rsi,1), 
                    "pe": pe, 
                    "fcf": fcf_str, 
                    "sharpe": result.sharpe_ratio, 
                    "mdd": f"{result.max_drawdown:.1f}%",
                    "regime": regime,
                    "strategy": strategy_name,
                    "signal": signal_data['signal'],
                    "trades": result.num_trades
                }
            ))
            db.commit()
        except Exception as e:
            print(f"Error processing {s.ticker}: {e}")
            db.rollback()
    db.close()

async def get_crypto_native_metrics(ticker, df):
    """
    Iteration 32: Fetch/Estimate Crypto-Native Institutional Metrics.
    """
    try:
        # 1. Fear & Greed Proxy (Heuristic based on RSI if API fails)
        fg_val = 50
        try:
            import requests
            r = requests.get("https://api.alternative.me/fng/", timeout=1)
            if r.ok: fg_val = int(r.json()['data'][0]['value'])
        except:
            rsi = ta.rsi(df['Close'], length=14).iloc[-1]
            fg_val = int(rsi) # Simple proxy
            
        # 2. Institutional Proxies
        curr = df['Close'].iloc[-1]
        # Use 50D SMA if 200D is too long for the dataset
        sma = df['Close'].rolling(window=min(len(df), 50)).mean().iloc[-1]
        std = df['Close'].rolling(window=min(len(df), 50)).std().iloc[-1]
        
        mvrv_proxy = (curr - sma) / std if std > 0 else 1.0
        
        rsi_val = ta.rsi(df['Close'], length=14).iloc[-1]
        funding_proxy = (rsi_val - 50) * 0.002 
        gas_proxy = 15.0 + (rsi_val - 45) * 0.8 if 'ETH' in ticker else 0.0
        
        return {
            "fg": int(fg_val),
            "mvrv": round(float(mvrv_proxy), 2),
            "funding": round(float(funding_proxy), 3),
            "gas": round(float(gas_proxy), 1)
        }
    except Exception as e:
        logger.error(f"Crypto Metric Error: {e}")
        return {"fg": 50, "mvrv": 0.0, "funding": 0.0, "gas": 0.0}

async def refresh_crypto_layer():
    db = SessionLocal(); now = hkt_now(); macro_drag = get_macro_drag()
    res = db.execute(text("SELECT ticker, name FROM gold.asset_registry WHERE asset_class = 'CRYPTO' AND is_active = True")).fetchall()
    db.execute(text("DELETE FROM consumption.crypto WHERE true")); db.commit()
    for a in res:
        try:
            t = yf.Ticker(a.ticker); df = t.history(period="1y")
            if df.empty: continue
            curr_p = to_native(df['Close'].iloc[-1]); prev_p = to_native(df['Close'].iloc[-2]) if len(df)>1 else curr_p
            p_v = to_native(get_prophet_prediction(a.ticker).get('P_7d')) if get_prophet_prediction(a.ticker) else 0.0
            win_rate, risk = simulate_historical_accuracy(df, 'CRYPTO_LSD', a.ticker, 'CRYPTO')
            est = calculate_horizon_estimates(p_v, 0.85, win_rate)
            cdl_pattern, cdl_sentiment = detect_candlestick_patterns(df)
            
            # Restoration of Crypto Native Metrics
            c_metrics = await get_crypto_native_metrics(a.ticker, df)
            
            db.execute(text("""
                INSERT INTO gold.crypto_metrics (date, ticker, close_price, prophet_forecast, candlestick_pattern, candlestick_sentiment, mvrv_z_score, fear_greed_index, funding_rate) 
                VALUES (:ts, :t, :c, :pf, :cp, :cs, :mvrv, :fg, :fund) 
                ON CONFLICT (ticker, date) DO NOTHING
            """), { 
                "ts": now, "t": a.ticker, "c": curr_p, "pf": p_v, "cp": cdl_pattern, "cs": cdl_sentiment,
                "mvrv": c_metrics['mvrv'], "fg": c_metrics['fg'], "fund": c_metrics['funding']
            })
            
            db.add(ConsumptionCrypto(
                timestamp=now, asset=a.name, ticker=a.ticker, action="HOLD", close_price=curr_p,
                daily_change=((curr_p-prev_p)/prev_p*100), est_1d=est['1d'], est_7d=est['7d'], est_1m=est['1m'],
                win_rate=win_rate, strategy_tags=["LSD_FUSION", f"CDL_{cdl_pattern.replace(' ','_')}" if cdl_pattern else "SYNC"],
                sparkline=generate_sparkline(df['Close'].tail(30).tolist()),
                reasoning=f"Candle: {cdl_pattern or 'None'}. Accuracy: {win_rate*100:.0f}%.",
                swarm_confidence=round(win_rate*macro_drag, 2), trad_confidence=0.7,
                candlestick_pattern=cdl_pattern,
                mvrv_z_score=c_metrics['mvrv'], fear_greed_index=c_metrics['fg'],
                funding_rate=c_metrics['funding'], gas_price_gwei=c_metrics['gas']
            ))
            db.commit()
        except Exception as e:
            logger.error(f"Crypto error {a.ticker}: {e}")
            db.rollback()
    db.close()

async def refresh_fx_layer():
    db = SessionLocal(); now = hkt_now(); macro_drag = get_macro_drag()
    res = db.execute(text("SELECT ticker, name FROM gold.asset_registry WHERE asset_class = 'FX' AND is_active = True")).fetchall()
    db.execute(text("DELETE FROM consumption.fx WHERE true")); db.commit()
    for a in res:
        try:
            t = yf.Ticker(a.ticker); df = t.history(period="1y")
            if df.empty: continue
            curr_p = to_native(df['Close'].iloc[-1]); prev_p = to_native(df['Close'].iloc[-2]) if len(df)>1 else curr_p
            p_v = to_native(get_prophet_prediction(a.ticker).get('P_7d')) if get_prophet_prediction(a.ticker) else 0.0
            win_rate, risk = simulate_historical_accuracy(df, 'CARRY_TRADE', a.ticker, 'FX')
            est = calculate_horizon_estimates(p_v, 0.1, win_rate); cdl_pattern, cdl_sentiment = detect_candlestick_patterns(df)
            db.execute(text("INSERT INTO gold.fx_metrics (date, ticker, close_price, prophet_forecast, candlestick_pattern, candlestick_sentiment) VALUES (:ts, :t, :c, :pf, :cp, :cs) ON CONFLICT (ticker, date) DO NOTHING"), { "ts": now, "t": a.ticker, "c": curr_p, "pf": p_v, "cp": cdl_pattern, "cs": cdl_sentiment })
            db.add(ConsumptionFx(timestamp=now, pair=a.ticker.replace("=X",""), action="HOLD", confidence=0.7, win_rate=win_rate, close_price=curr_p, daily_change=((curr_p-prev_p)/prev_p*100), est_1d=est['1d'], est_7d=est['7d'], est_1m=est['1m'], reasoning=f"Pattern: {cdl_pattern or 'None'}. Carry-Trade Accuracy: {win_rate*100:.0f}%.", candlestick_pattern=cdl_pattern))
            db.commit()
        except Exception as e:
            logger.error(f"FX error {a.ticker}: {e}")
            db.rollback()
    db.close()

async def refresh_commodity_layer():
    db = SessionLocal(); now = hkt_now(); macro_drag = get_macro_drag()
    res = db.execute(text("SELECT ticker, name, horizon FROM gold.asset_registry WHERE asset_class = 'COMMODITY' AND is_active = True")).fetchall()
    db.execute(text("DELETE FROM consumption.commodities WHERE true")); db.commit()
    for a in res:
        try:
            t = yf.Ticker(a.ticker); df = t.history(period="1y")
            if df.empty: continue
            curr_p = to_native(df['Close'].iloc[-1]); prev_p = to_native(df['Close'].iloc[-2]) if len(df)>1 else curr_p
            p_v = to_native(get_prophet_prediction(a.ticker).get('P_7d')) if get_prophet_prediction(a.ticker) else 0.0
            
            # Institutional Logic (Iteration 33)
            win_rate, risk = simulate_historical_accuracy(df, a.horizon, a.ticker, 'COMMODITY')
            est = calculate_horizon_estimates(p_v, 0.3, win_rate)
            cdl_pattern, cdl_sentiment = detect_candlestick_patterns(df)
            rsi = to_native(ta.rsi(df['Close'], length=14).iloc[-1]) or 50
            
            # Multi-Factor Score for Commodities
            # Factor in RSI mean-reversion + Prophet drift
            score = (win_rate * 0.4) + (max(0, p_v / 25) * 0.4) + (0.2 if rsi < 40 else 0.1)
            score = round(max(min(score * macro_drag, 0.98), 0.1), 2)
            
            db.execute(text("""
                INSERT INTO gold.commodity_metrics (date, ticker, close_price, prophet_forecast, candlestick_pattern, candlestick_sentiment, rsi_14) 
                VALUES (:ts, :t, :c, :pf, :cp, :cs, :rsi) 
                ON CONFLICT (ticker, date) DO NOTHING
            """), { "ts": now, "t": a.ticker, "c": curr_p, "pf": p_v, "cp": cdl_pattern, "cs": cdl_sentiment, "rsi": rsi })
            
            db.add(ConsumptionCommodity(
                timestamp=now, asset=a.name, ticker=a.ticker, action="HOLD", 
                win_rate=win_rate, close_price=curr_p, daily_change=((curr_p-prev_p)/prev_p*100), 
                est_1d=est['1d'], est_7d=est['7d'], est_1m=est['1m'], 
                sparkline=generate_sparkline(df['Close'].tail(30).tolist()), 
                reasoning=f"Macro cycle accuracy: {win_rate*100:.0f}%. Candle: {cdl_pattern or 'None'}.",
                trad_confidence=round(win_rate, 2),
                swarm_confidence=score,
                candlestick_pattern=cdl_pattern
            ))
            db.commit()
        except Exception as e:
            logger.error(f"Commodity error {a.ticker}: {e}")
            db.rollback()
    db.close()

async def refresh_indices_and_mood():
    db = SessionLocal()
    try:
        indices = { "DJI": "^DJI", "HSI": "^HSI", "STOXX50": "^STOXX50E", "SSE": "000001.SS", "STI": "^STI" }; avg_7d = 0; valid = 0; now = hkt_now()
        for label, sym in indices.items():
            try:
                # 1. Real-time Price Logic
                stock = yf.Ticker(sym); df = stock.history(period="2d")
                price = df['Close'].iloc[-1] if not df.empty else 0
                prev = df['Close'].iloc[-2] if len(df) > 1 else price
                change = ((price - prev) / prev * 100) if prev != 0 else 0
                
                # Save raw metrics
                db.execute(text("INSERT INTO consumption.global_state (key, value, category, timestamp) VALUES (:k, :v, 'index', :ts) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"), {"k": f"index_price_{label}", "v": str(price), "ts": now})
                db.execute(text("INSERT INTO consumption.global_state (key, value, category, timestamp) VALUES (:k, :v, 'index', :ts) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"), {"k": f"index_change_{label}", "v": str(change), "ts": now})
                
                p_data = get_prophet_prediction(sym); p_7d = to_native(p_data['P_7d']) if p_data else 0.0
                avg_7d += p_7d; valid += 1
                
                # Structured Swarm Invoke (Iteration 31)
                prompt = f"""
                Perform a Sentiment Swarm Analysis for the {label} market.
                7-Day Statistical Forecast: {p_7d:+.2f}%.
                
                Return ONLY a valid JSON object with:
                {{
                    "market_mood": "Bullish/Bearish/Neutral/Cautious",
                    "conclusion": "1-sentence executive summary.",
                    "rationale": "Brief professional narrative.",
                    "recommended_industries": {{
                        "short_term": ["Industry A", "Industry B"],
                        "long_term": ["Industry C", "Industry D"]
                    }}
                }}
                """
                res = await research_swarm.llm.ainvoke(prompt)
                try:
                    clean_json = res.content.replace('```json', '').replace('```', '').strip()
                    market_swarm = json.loads(clean_json)
                except:
                    market_swarm = {
                        "market_mood": "Neutral",
                        "conclusion": "Syncing swarm...",
                        "rationale": res.content[:200],
                        "recommended_industries": {"short_term": ["Tech"], "long_term": ["Energy"]}
                    }

                estimates = { "1d": f"{p_7d/7:+.2f}%", "1w": f"{p_7d:+.2f}%", "1m": f"{p_7d*np.sqrt(30/7)*0.85:+.2f}%" }
                
                sql = text("""
                    INSERT INTO consumption.global_state (key, value, category, rationale, estimates, timestamp) 
                    VALUES (:k, :v, 'index', :r, CAST(:est AS JSONB), :ts) 
                    ON CONFLICT (key) DO UPDATE SET 
                        value = EXCLUDED.value, 
                        rationale = EXCLUDED.rationale,
                        estimates = EXCLUDED.estimates, 
                        timestamp = EXCLUDED.timestamp
                """)
                db.execute(sql, { 
                    "k": f"index_rationale_{label}", 
                    "v": market_swarm['market_mood'], 
                    "r": json.dumps(market_swarm), 
                    "est": json.dumps(estimates), 
                    "ts": now 
                })
                db.commit()
            except Exception as e:
                logger.error(f"Index sync error {label}: {e}")
                db.rollback()
        
        mood = "Neutral"
        if valid > 0:
            avg = avg_7d / valid
            if avg > 1.0: mood = "Bullish"
            elif avg < -1.0: mood = "Bearish"
        db.execute(text("INSERT INTO consumption.global_state (key, value, category, timestamp) VALUES ('market_mood_index', :v, 'market', :ts) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"), {"v": mood, "ts": now})
        db.commit()
    finally:
        db.close()

async def refresh_hft_layer():
    db = SessionLocal(); now = hkt_now()
    hft_universe = [
        {"t": "EURUSD=X", "c": "FX"}, {"t": "USDJPY=X", "c": "FX"}, {"t": "GBPUSD=X", "c": "FX"},
        {"t": "USDHKD=X", "c": "FX"}, {"t": "GBPJPY=X", "c": "FX"}, {"t": "EURJPY=X", "c": "FX"},
        {"t": "BTC-USD", "c": "CRYPTO"}, {"t": "ETH-USD", "c": "CRYPTO"},
        {"t": "GC=F", "c": "COMMODITY"}, {"t": "CL=F", "c": "COMMODITY"}
    ]
    db.execute(text("DELETE FROM consumption.hft_matrix WHERE true")); db.commit()
    for item in hft_universe:
        try:
            # Iteration 34: Micro-Timeframe Velocity Integration (1m, 5m, 30m, 1h)
            t = yf.Ticker(item['t'])
            df_m = t.history(period="1d", interval="1m")
            if df_m.empty: continue
            
            curr = df_m['Close'].iloc[-1]
            def get_drift(mins):
                # Correct index: if mins is 5, we want the price 5 bars ago
                idx = mins + 1
                if len(df_m) < idx: return 0.0
                prev = df_m['Close'].iloc[-idx]
                return ((curr - prev) / prev) * 100

            vel_est = {
                "1m": f"{get_drift(2):+.3f}%",
                "5m": f"{get_drift(5):+.3f}%",
                "30m": f"{get_drift(30):+.2f}%",
                "1h": f"{get_drift(60):+.2f}%"
            }

            # Iteration 35: OFI Proxy (Order Flow Imbalance)
            v_delta = to_native(df_m['Volume'].iloc[-1] / (df_m['Volume'].tail(20).mean() + 1)) or 1.0
            price_change = (df_m['Close'].iloc[-1] - df_m['Close'].iloc[-2])
            pressure = to_native(v_delta * price_change * 1000)

            signal = "NEUTRAL"
            if pressure > 5.0 and get_drift(5) > 0.01: signal = "SCALP BUY"
            if pressure < -5.0 and get_drift(5) < -0.01: signal = "SCALP SELL"

            db.execute(text("""
                INSERT INTO consumption.hft_matrix 
                (timestamp, ticker, asset_class, liquidity_momentum, pressure_value, reasoning, fusion_signal, velocity_estimates) 
                VALUES (:ts, :t, :ac, :lm, :pv, :rea, :fs, CAST(:est AS JSONB))
            """), { 
                "ts": now, "t": item['t'], "ac": item['c'], "lm": "HIGH" if v_delta > 2.0 else "NORMAL", 
                "pv": pressure, "rea": f"Velocity check complete. {signal} bias.", "fs": signal, "est": json.dumps(vel_est)
            })
            db.commit()
        except Exception as e:
            logger.error(f"HFT error {item['t']}: {e}")
            db.rollback()
    db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(refresh_stock_layer())

# --- NEW: ETF DATA INGESTION (Daily) ---
async def refresh_etf_layer():
    """Daily ETF data ingestion for XLK, XLU, SPY, QQQ, IWM"""
    etfs = ['XLK', 'XLU', 'SPY', 'QQQ', 'IWM']
    logger.info(f"[ETF] Starting daily refresh for {len(etfs)} ETFs...")
    
    db = SessionLocal()
    today = datetime.datetime.now().date()
    
    for etf in etfs:
        try:
            ticker = yf.Ticker(etf)
            df = ticker.history(period="2d")  # Get last 2 days
            
            if df.empty or len(df) < 1:
                logger.warning(f"[ETF] No data for {etf}")
                continue
            
            # Get latest data
            latest = df.iloc[-1]
            date = df.index[-1].date()
            
            # Skip if already ingested today
            existing = db.execute(text("""
                SELECT 1 FROM gold.etf_daily_data 
                WHERE ticker = :ticker AND date = :date
            """), {"ticker": etf, "date": date}).fetchone()
            
            if existing:
                logger.info(f"[ETF] {etf} already up-to-date ({date})")
                continue
            
            # Insert/update data
            db.execute(text("""
                INSERT INTO gold.etf_daily_data 
                (ticker, date, open_price, high_price, low_price, close_price, volume, created_at)
                VALUES (:ticker, :date, :open, :high, :low, :close, :volume, NOW())
                ON CONFLICT (ticker, date) DO UPDATE SET
                    open_price = EXCLUDED.open_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    close_price = EXCLUDED.close_price,
                    volume = EXCLUDED.volume
            """), {
                "ticker": etf,
                "date": date,
                "open": float(latest['Open']),
                "high": float(latest['High']),
                "low": float(latest['Low']),
                "close": float(latest['Close']),
                "volume": int(latest['Volume'])
            })
            db.commit()
            logger.info(f"[ETF] ✓ {etf} updated: ${latest['Close']:.2f} ({date})")
            
        except Exception as e:
            logger.error(f"[ETF] Error processing {etf}: {e}")
            db.rollback()
    
    db.close()
    logger.info("[ETF] Daily refresh complete")

# --- NEW: ACCRUALS QUALITY DATA INGESTION (Weekly) ---
async def refresh_accruals_quality():
    """Weekly accruals quality data update for S&P 100 stocks"""
    # S&P 100 subset (top 50 for weekly updates)
    sp100_stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'AVGO', 'WMT',
        'JPM', 'V', 'PG', 'UNH', 'MA', 'HD', 'LLY', 'MRK', 'PEP', 'KO',
        'ABBV', 'COST', 'TMO', 'DIS', 'ADBE', 'WFC', 'VZ', 'NKE', 'TXN', 'CMCSA',
        'PFE', 'MS', 'CRM', 'ABT', 'INTC', 'NEE', 'QCOM', 'RTX', 'HON', 'AMGN',
        'UPS', 'LOW', 'PM', 'UNP', 'IBM', 'CAT', 'MDT', 'GE', 'CVX', 'XOM'
    ]
    
    logger.info(f"[ACCRUALS] Starting weekly quality update for {len(sp100_stocks)} stocks...")
    
    db = SessionLocal()
    updated = 0
    
    for ticker in sp100_stocks:
        try:
            stock = yf.Ticker(ticker)
            
            # Get quarterly financials
            income = stock.quarterly_financials
            cashflow = stock.quarterly_cashflow
            balance = stock.quarterly_balance_sheet
            
            if income is None or balance is None:
                continue
            
            # Process latest quarter
            for col in income.columns[:1]:  # Only latest quarter
                try:
                    quarter = col.strftime('%Y-%m-%d') if hasattr(col, 'strftime') else str(col)[:10]
                    
                    # Extract Net Income
                    net_income = None
                    for field in ['Net Income', 'NetIncome']:
                        if field in income.index:
                            net_income = income.loc[field].get(col, None)
                            if net_income is not None:
                                break
                    
                    # Extract Total Assets
                    total_assets = None
                    for field in ['Total Assets', 'TotalAssets']:
                        if field in balance.index:
                            total_assets = balance.loc[field].get(col, None)
                            if total_assets is not None:
                                break
                    
                    # Extract Operating Cash Flow
                    ocf = None
                    if cashflow is not None:
                        for field in ['Operating Cash Flow', 'Total Cash From Operating Activities', 'OperatingCashFlow']:
                            if field in cashflow.index:
                                ocf = cashflow.loc[field].get(col, None)
                                if ocf is not None:
                                    break
                    
                    if net_income is None or total_assets is None:
                        continue
                    
                    # Calculate metrics
                    ni = float(net_income)
                    ta = float(total_assets)
                    ocf_val = float(ocf) if ocf else None
                    
                    accruals = ni - ocf_val if ocf_val else None
                    accruals_ratio = (accruals / ta) if (accruals and ta != 0) else None
                    
                    # Quality score: 1 - normalized accruals ratio
                    quality_score = None
                    if accruals_ratio is not None:
                        quality_score = max(0, min(1, 1 - abs(accruals_ratio) * 10))
                    
                    # Insert/update
                    db.execute(text("""
                        INSERT INTO gold.accruals_quality 
                        (ticker, quarter, net_income, operating_cash_flow, total_assets, 
                         accruals, accruals_ratio, quality_score, created_at)
                        VALUES (:ticker, :quarter, :ni, :ocf, :assets, :accruals, :ratio, :quality, NOW())
                        ON CONFLICT (ticker, quarter) DO UPDATE SET
                            net_income = EXCLUDED.net_income,
                            operating_cash_flow = EXCLUDED.operating_cash_flow,
                            total_assets = EXCLUDED.total_assets,
                            accruals = EXCLUDED.accruals,
                            accruals_ratio = EXCLUDED.accruals_ratio,
                            quality_score = EXCLUDED.quality_score
                    """), {
                        "ticker": ticker,
                        "quarter": quarter,
                        "ni": ni,
                        "ocf": ocf_val,
                        "assets": ta,
                        "accruals": accruals,
                        "ratio": accruals_ratio,
                        "quality": quality_score
                    })
                    db.commit()
                    updated += 1
                    
                    logger.info(f"[ACCRUALS] ✓ {ticker} Q{quarter}: Quality={quality_score:.2f if quality_score else 'N/A'}")
                    
                except Exception as e:
                    logger.error(f"[ACCRUALS] Error processing {ticker} quarter: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"[ACCRUALS] Error fetching {ticker}: {e}")
            continue
    
    db.close()
    logger.info(f"[ACCRUALS] Weekly update complete: {updated} records updated")

# --- MASTER REFRESH FUNCTION ---
async def run_daily_ingestion():
    """Run all daily data ingestion pipelines"""
    logger.info("=" * 60)
    logger.info("STARTING DAILY INGESTION PIPELINE")
    logger.info("=" * 60)
    
    # Core layers
    await refresh_indices_and_mood()
    await refresh_stock_layer()
    await refresh_fx_layer()
    await refresh_commodity_layer()
    await refresh_crypto_layer()
    
    # New data sources
    await refresh_etf_layer()
    # await refresh_accruals_quality()  # Run weekly, not daily
    
    logger.info("=" * 60)
    logger.info("DAILY INGESTION COMPLETE")
    logger.info("=" * 60)
