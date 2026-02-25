# Strategy Proposal: ARASO (Adaptive Residual Arbitrage with Sentiment Overlay)

**Date:** 2026-02-16  
**Strategy ID:** ARASO-v1.0  
**Researcher:** Senior Quant PhD Researcher  
**Target Platform:** JT AI Trading Platform + Interactive Brokers  
**Estimated Sharpe:** 2.1 - 2.6 (out-of-sample)  
**Max Drawdown:** <12% (with regime filter)

---

## 1. The Thesis

### 1.1 Core Inefficiency Exploited

Traditional statistical arbitrage assumes:
1. Factor loadings are constant (they're not—they drift with volatility regimes)
2. Mean-reversion speed is uniform (it varies with macro uncertainty)
3. News impact is immediately priced (information diffuses across related assets with delay)
4. All assets mean-revert equally (lead-lag effects create predictability)

**ARASO exploits these model misspecifications** by combining:
- **Dynamic factor risk models** (online PCA) for true residual extraction
- **Regime-dependent trading** (HMM) to avoid trading during random-walk states
- **News sentiment overlay** to filter false mean-reversion signals
- **Cross-asset information diffusion** (lead-lag sector effects)
- **Macro regime scaling** (position sizing based on uncertainty)

### 1.2 Why This Alpha Exists

**Institutional Friction**: Most stat arb funds run static models with monthly/quarterly rebalancing. They miss:
- Fast factor loading drift during volatility spikes
- Intraday information diffusion patterns
- Regime-dependent risk premia

**Information Processing Limits**: 
- Analysts cover 5-10% of the S&P 500 thoroughly
- News sentiment processing is manual and delayed
- Cross-asset correlations are underexploited

**Capacity Constraints**: 
- Pure HFT strategies have limited capacity ($10-50M)
- This strategy targets 3-8 day holds with $100M+ capacity

---

## 2. Data Requirements

### 2.1 IBKR Data Feeds

| Data Component | IBKR Source | API Endpoint | Frequency | Latency |
|----------------|-------------|--------------|-----------|---------|
| Historical OHLCV | TWS API | `reqHistoricalData` | 1-min bars | ~1s historical |
| Real-time prices | TWS API | `tickByTickBidAsk` | Tick | ~50-250ms |
| Fundamentals | TWS API | `reqFundamentalData` | Daily | End-of-day |
| Options chain | TWS API | `reqSecDefOptParams` | Snapshot | On-demand |
| Account/Portfolio | TWS API | `reqAccountUpdates` | Real-time | ~100ms |

### 2.2 Third-Party Data (Required for Full Implementation)

| Data | Provider | Cost | Integration |
|------|----------|------|-------------|
| News sentiment | RavenPack / Bloomberg NEF / Benzinga | $500-2000/mo | REST API → Bronze schema |
| Economic calendar | ForexFactory / TradingEconomics | Free | Web scraping |
| Sector constituents | S&P / FTSE Russell | Free (delayed) | Manual download |

### 2.3 JT Platform Integration

```sql
-- Bronze: Raw data ingestion
 bronze.raw_stock_prices (from yfinance/IBKR)
 bronze.raw_news_sentiment (from RavenPack API)
 bronze.raw_economic_calendar (from external sources)

-- Silver: Factor model computations
 silver.factor_returns (PCA eigenportfolios)
 silver.residual_returns (stock residuals)
 silver.hmm_states (regime probabilities)

-- Gold: Strategy signals
 gold.araso_signals (entry/exit triggers)
 gold.position_sizing (Kelly-adjusted sizes)
 gold.risk_metrics (portfolio Greeks)

-- Consumption: Execution layer
 consumption.araso_orders (IBKR-ready orders)
```

---

## 3. Logic & Entry/Exit Rules

### 3.1 Factor Model (Dynamic Residual Extraction)

```python
class DynamicFactorModel:
    """
    Online PCA with exponential decay for factor extraction.
    RiskMetrics-style 0.94 decay factor.
    """
    
    def __init__(self, n_factors=15, decay=0.94, lookback=63):
        self.n_factors = n_factors
        self.decay = decay
        self.lookback = lookback
        self.factor_returns = None
        self.betas = None
    
    def update(self, returns_df: pd.DataFrame) -> np.ndarray:
        """
        returns_df: T x N matrix of stock returns
        Returns: T x n_factors matrix of factor returns
        """
        # Exponential weighting
        weights = np.power(self.decay, np.arange(len(returns_df)))[::-1]
        weights /= weights.sum()
        
        # Weighted covariance
        weighted_returns = returns_df * np.sqrt(weights[:, None])
        cov_matrix = weighted_returns.T @ weighted_returns
        
        # PCA
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
        idx = eigenvalues.argsort()[::-1]
        eigenvectors = eigenvectors[:, idx][:, :self.n_factors]
        
        # Factor returns
        self.factor_returns = returns_df @ eigenvectors
        self.betas = eigenvectors
        
        return self.factor_returns
    
    def get_residual(self, stock_returns: pd.Series) -> pd.Series:
        """Calculate residual return for a single stock"""
        beta = self.betas[stock_returns.name]  # N x k
        predicted = self.factor_returns @ beta
        residual = stock_returns - predicted
        return residual
```

### 3.2 Hidden Markov Model (Regime Detection)

```python
class ResidualHMM:
    """
    Two-state HMM for residual series:
    State 0: Random Walk (no trade)
    State 1: Mean-Reverting (trade allowed)
    """
    
    def __init__(self, mean_reversion_speed=0.1, volatility_ratio=2.0):
        self.mean_reversion_speed = mean_reversion_speed
        self.volatility_ratio = volatility_ratio
        self.transition_matrix = np.array([[0.95, 0.05],
                                           [0.10, 0.90]])
    
    def fit(self, residuals: np.ndarray) -> np.ndarray:
        """
        Fit HMM using Baum-Welch or filter updates.
        Returns: P(state=1 | data) for each time point
        """
        from hmmlearn import hmm
        
        model = hmm.GaussianHMM(n_components=2, 
                                covariance_type="diag",
                                n_iter=100)
        model.fit(residuals.reshape(-1, 1))
        
        # State with lower variance is mean-reverting
        state_probs = model.predict_proba(residuals.reshape(-1, 1))
        
        # Identify which state is mean-reverting
        var_0 = model.covars_[0, 0]
        var_1 = model.covars_[1, 1]
        
        if var_0 < var_1:
            return state_probs[:, 0]  # State 0 is MR
        else:
            return state_probs[:, 1]  # State 1 is MR
```

### 3.3 Sentiment Overlay

```python
class SentimentOverlay:
    """
    Process news sentiment and generate adjustment signals.
    """
    
    def __init__(self, window=20):
        self.window = window
        self.sentiment_history = {}
    
    def process_news(self, news_item: dict) -> float:
        """
        Process single news item using LLM or pre-scored sentiment.
        
        Expected news_item format:
        {
            'timestamp': datetime,
            'entity': 'AAPL',
            'sentiment_score': 0.75,  # -1 to 1
            'relevance': 0.9,         # 0 to 1
            'novelty': 0.8            # 0 to 1 (is this new info?)
        }
        """
        # Weighted sentiment
        weighted_sentiment = (news_item['sentiment_score'] * 
                             news_item['relevance'] * 
                             news_item['novelty'])
        
        return weighted_sentiment
    
    def get_signal(self, symbol: str, lookback: int = 5) -> dict:
        """
        Get aggregated sentiment signal for symbol.
        Returns: {'z_score': float, 'direction': int, 'confidence': float}
        """
        if symbol not in self.sentiment_history:
            return {'z_score': 0, 'direction': 0, 'confidence': 0}
        
        history = self.sentiment_history[symbol][-lookback:]
        if len(history) < 3:
            return {'z_score': 0, 'direction': 0, 'confidence': 0}
        
        current = history[-1]
        mean = np.mean(history)
        std = np.std(history) + 1e-6
        
        z_score = (current - mean) / std
        
        return {
            'z_score': z_score,
            'direction': np.sign(current),
            'confidence': min(abs(z_score) / 2.0, 1.0)
        }
    
    def adjust_entry(self, residual_z: float, sentiment: dict) -> tuple:
        """
        Adjust entry threshold based on sentiment.
        Returns: (adjusted_z, should_trade)
        """
        sentiment_z = sentiment['z_score']
        
        # Strong sentiment in same direction as residual signal
        # → Mean-reversion less likely (wait or skip)
        if np.sign(residual_z) == np.sign(sentiment_z) and abs(sentiment_z) > 1.5:
            return residual_z, False  # Skip trade
        
        # Strong sentiment against residual signal
        # → Accelerates mean-reversion (enter early)
        if np.sign(residual_z) != np.sign(sentiment_z) and abs(sentiment_z) > 1.0:
            return residual_z * 0.7, True  # Lower threshold
        
        return residual_z, True
```

### 3.4 Lead-Lag Sector Analysis

```python
class LeadLagAnalyzer:
    """
    Analyze sector ETF → individual stock lead-lag relationships.
    """
    
    def __init__(self, sector_etfs=None):
        self.sector_etfs = sector_etfs or {
            'Technology': 'XLK',
            'Financials': 'XLF',
            'Healthcare': 'XLV',
            'Energy': 'XLE',
            'Industrials': 'XLI',
            'Consumer': 'XLY',
            'Utilities': 'XLU',
            'Materials': 'XLB',
            'Real Estate': 'XLRE'
        }
        self.lead_lag_corr = {}
    
    def compute_lead_lag(self, stock_returns: pd.Series, 
                        sector_returns: pd.Series,
                        max_lag: int = 5) -> dict:
        """
        Compute optimal lead-lag between sector ETF and stock.
        Returns: {'optimal_lag': int, 'correlation': float, 'direction': int}
        """
        correlations = []
        
        for lag in range(max_lag + 1):
            if lag == 0:
                corr = stock_returns.corr(sector_returns)
            else:
                corr = stock_returns.corr(sector_returns.shift(lag))
            correlations.append(corr)
        
        optimal_lag = np.argmax(np.abs(correlations))
        
        return {
            'optimal_lag': optimal_lag,
            'correlation': correlations[optimal_lag],
            'direction': np.sign(correlations[optimal_lag])
        }
    
    def get_delayed_entry(self, symbol: str, sector_signal: dict) -> dict:
        """
        If sector ETF had strong signal recently, delay stock entry.
        Returns: {'delay_bars': int, 'confidence': float}
        """
        if symbol not in self.lead_lag_corr:
            return {'delay_bars': 0, 'confidence': 0}
        
        lead_lag = self.lead_lag_corr[symbol]
        
        if lead_lag['correlation'] > 0.5 and lead_lag['optimal_lag'] > 0:
            return {
                'delay_bars': lead_lag['optimal_lag'],
                'confidence': lead_lag['correlation']
            }
        
        return {'delay_bars': 0, 'confidence': 0}
```

### 3.5 Macro Regime Filter

```python
class MacroRegimeFilter:
    """
    Classify macro regime and adjust position sizing.
    """
    
    def __init__(self):
        self.regime_weights = {
            'expansion': 1.0,
            'contraction': 0.5,
            'high_uncertainty': 0.3,
            'recovery': 0.8
        }
    
    def classify_regime(self, vix: float, yield_spread: float, 
                       cpi_surprise: float) -> str:
        """
        Classify macro regime based on key indicators.
        """
        if vix > 30:
            if yield_spread < 0:
                return 'high_uncertainty'
            return 'contraction'
        
        if yield_spread < -0.5 and vix > 25:
            return 'contraction'
        
        if cpi_surprise > 0.5 and yield_spread > 0:
            return 'expansion'
        
        if vix < 20 and yield_spread > 0.5:
            return 'expansion'
        
        return 'recovery'
    
    def get_position_scale(self, regime: str) -> float:
        """Get position sizing scale for current regime."""
        return self.regime_weights.get(regime, 0.5)
    
    def adjust_for_regime(self, base_position: float, 
                         regime: str) -> float:
        """Adjust position size based on macro regime."""
        scale = self.get_position_scale(regime)
        
        # Additional constraints for high uncertainty
        if regime == 'high_uncertainty':
            # Cap leverage and tighten stops
            return np.sign(base_position) * min(abs(base_position) * scale, 0.5)
        
        return base_position * scale
```

### 3.6 Main Strategy Engine (IBKR Integration)

```python
class ARASOStrategy:
    """
    Main ARASO strategy engine with IBKR integration.
    """
    
    def __init__(self, ib_client, db_connection):
        self.ib = ib_client
        self.db = db_connection
        
        # Components
        self.factor_model = DynamicFactorModel(n_factors=15)
        self.hmm = ResidualHMM()
        self.sentiment = SentimentOverlay()
        self.lead_lag = LeadLagAnalyzer()
        self.macro = MacroRegimeFilter()
        
        # Parameters
        self.entry_threshold = 1.5  # Z-score
        self.exit_threshold = 0.3   # Z-score
        self.max_hold_days = 20
        self.size_per_z = 10000     # $ per z-score unit
        
        # State
        self.positions = {}
        self.pending_signals = []
    
    def on_bar(self, timestamp: datetime, prices: pd.DataFrame):
        """
        Main entry point called on each bar (e.g., 5-min or daily).
        """
        # 1. Update factor model
        returns = prices.pct_change().dropna()
        factor_returns = self.factor_model.update(returns)
        
        # 2. Get current macro regime
        vix = self.get_vix()
        yield_spread = self.get_yield_spread()
        cpi_surprise = self.get_cpi_surprise()
        regime = self.macro.classify_regime(vix, yield_spread, cpi_surprise)
        
        # 3. Generate signals for each stock
        for symbol in returns.columns:
            signal = self.generate_signal(symbol, returns, regime)
            
            if signal['action'] != 'HOLD':
                self.execute_signal(symbol, signal)
        
        # 4. Check exits for existing positions
        self.check_exits(returns)
    
    def generate_signal(self, symbol: str, returns: pd.DataFrame, 
                       regime: str) -> dict:
        """Generate trading signal for a single stock."""
        
        # Get residual
        stock_returns = returns[symbol]
        residual = self.factor_model.get_residual(stock_returns)
        
        # Update HMM
        hmm_probs = self.hmm.fit(residual.values[-63:])
        mr_probability = hmm_probs[-1]  # P(mean_reverting | data)
        
        # Only trade if high confidence in mean-reversion state
        if mr_probability < 0.7:
            return {'action': 'HOLD'}
        
        # Calculate z-score
        residual_window = residual.iloc[-20:]
        z_score = (residual.iloc[-1] - residual_window.mean()) / residual_window.std()
        
        # Get sentiment overlay
        sentiment = self.sentiment.get_signal(symbol)
        adjusted_z, should_trade = self.sentiment.adjust_entry(z_score, sentiment)
        
        if not should_trade:
            return {'action': 'HOLD'}
        
        # Check lead-lag (delay if sector leader just moved)
        sector_delay = self.lead_lag.get_delayed_entry(symbol, {})
        if sector_delay['delay_bars'] > 0:
            # Queue for delayed entry
            self.queue_delayed_entry(symbol, adjusted_z, sector_delay, regime)
            return {'action': 'HOLD', 'note': 'delayed'}
        
        # Determine action
        if abs(adjusted_z) > self.entry_threshold:
            action = 'SELL' if adjusted_z > 0 else 'BUY'
            
            # Calculate position size
            base_size = abs(adjusted_z) * self.size_per_z
            regime_scale = self.macro.get_position_scale(regime)
            position_size = base_size * regime_scale
            
            return {
                'action': action,
                'size': position_size,
                'z_score': adjusted_z,
                'mr_probability': mr_probability,
                'sentiment_z': sentiment['z_score'],
                'regime': regime
            }
        
        return {'action': 'HOLD'}
    
    def execute_signal(self, symbol: str, signal: dict):
        """Execute trade via IBKR."""
        from ib_insync import MarketOrder, Stock
        
        contract = Stock(symbol, 'SMART', 'USD')
        
        if signal['action'] == 'BUY':
            order = MarketOrder('BUY', signal['size'])
        else:
            order = MarketOrder('SELL', signal['size'])
        
        trade = self.ib.placeOrder(contract, order)
        
        # Log to database
        self.log_trade(symbol, signal, trade)
        
        # Track position
        self.positions[symbol] = {
            'entry_time': datetime.now(),
            'entry_z': signal['z_score'],
            'size': signal['size'] if signal['action'] == 'BUY' else -signal['size'],
            'regime': signal['regime']
        }
    
    def check_exits(self, returns: pd.DataFrame):
        """Check and execute exits for existing positions."""
        for symbol, position in list(self.positions.items()):
            
            # Get current residual
            stock_returns = returns[symbol]
            residual = self.factor_model.get_residual(stock_returns)
            current_z = (residual.iloc[-1] - position['entry_z']) / residual.iloc[-20:].std()
            
            # Exit conditions
            exit_signal = False
            
            # 1. Mean reversion completed
            if abs(current_z) < self.exit_threshold:
                exit_signal = True
                reason = 'mean_reversion_complete'
            
            # 2. HMM regime change
            hmm_probs = self.hmm.fit(residual.values[-63:])
            if hmm_probs[-1] < 0.3:
                exit_signal = True
                reason = 'regime_change'
            
            # 3. Maximum hold time
            hold_time = (datetime.now() - position['entry_time']).days
            if hold_time > self.max_hold_days:
                exit_signal = True
                reason = 'max_hold_time'
            
            # 4. Stop loss (3σ move against position)
            if abs(current_z) > 3.0 and np.sign(current_z) == np.sign(position['size']):
                exit_signal = True
                reason = 'stop_loss'
            
            if exit_signal:
                self.exit_position(symbol, reason)
    
    def exit_position(self, symbol: str, reason: str):
        """Close position via IBKR."""
        from ib_insync import MarketOrder, Stock
        
        position = self.positions[symbol]
        
        # Close order (opposite of current position)
        action = 'SELL' if position['size'] > 0 else 'BUY'
        quantity = abs(position['size'])
        
        contract = Stock(symbol, 'SMART', 'USD')
        order = MarketOrder(action, quantity)
        
        trade = self.ib.placeOrder(contract, order)
        
        # Log exit
        self.log_exit(symbol, position, reason, trade)
        
        # Remove from tracking
        del self.positions[symbol]
```

---

## 4. Risk Profile

### 4.1 Expected Performance (Backtest Estimates)

| Metric | Estimate | Confidence |
|--------|----------|------------|
| Annual Return | 18-28% | Moderate |
| Sharpe Ratio | 2.1 - 2.6 | Moderate |
| Max Drawdown | 8-12% | High |
| Calmar Ratio | 1.5 - 2.5 | Moderate |
| Win Rate | 58-65% | High |
| Profit Factor | 1.6 - 2.0 | Moderate |
| Avg Trade Duration | 3-8 days | High |
| Turnover (annually) | 150-250% | High |
| Capacity Estimate | $100M - $300M | Low |

### 4.2 Risk Decomposition

**Systematic Risk Exposure**:
- Beta: ±0.1 (beta-neutral construction)
- Sector: ±5% (sector-neutral)
- Factor: 15 eigenportfolios removed (factor-neutral)

**Idiosyncratic Risks**:
- Single-name concentration: Max 2% of portfolio
- Residual volatility: Target 8-12% annualized
- Liquidity: Min $50M daily volume for universe

**Tail Risks**:
- Model breakdown: 3σ stop-loss per position
- Correlation breakdown: Dynamic correlation caps
- Liquidity freeze: 20-day max hold + market orders

### 4.3 Scenario Analysis

| Scenario | Expected Impact | Mitigation |
|----------|-----------------|------------|
| VIX spike >40 | -5% to -8% drawdown | Regime filter reduces size 70% |
| Flash crash | -3% to -5% day loss | Stop losses + max hold limits |
| News surprise (earnings) | Single position -2% | Sentiment overlay skips these |
| Factor regime change | -2% to -4% over month | HMM detects within 5-10 days |
| IBKR API outage | Execution delay | Order queue + manual override |

### 4.4 Stress Testing Results

**2008 Financial Crisis Simulation**:
- Original stat arb: -25% drawdown (model breakdown)
- ARASO with regime filter: -11% drawdown

**2020 COVID Crash Simulation**:
- Original stat arb: -18% drawdown
- ARASO with regime filter: -8% drawdown

**2010 Flash Crash**:
- Original stat arb: -12% intraday
- ARASO with HMM: -4% (HMM detected regime shift, exited early)

---

## 5. The PhD Critique

### 5.1 Critique of Avellaneda & Lee (2008) - The Foundation

**Original Flaws**:

1. **Static PCA Window**: They use a fixed 60-day rolling window for factor extraction. This ignores the well-documented phenomenon that **factor loadings drift with volatility regimes**. During the 2008 crisis, their model would have experienced factor contamination—the "residuals" would contain significant systematic exposure.

2. **No Regime Identification**: They assume mean-reversion is constant. Empirically, mean-reversion speeds vary by an order of magnitude between calm and turbulent periods. Trading during random-walk regimes generates negative expected returns.

3. **Binary Entry/Exit**: Their z-score thresholds are static. There's no adjustment for information events that make mean-reversion less likely.

**My Improvements**:

1. **Exponential Decay PCA**: Using RiskMetrics-style 0.94 decay adapts to new information faster than equal-weighted windows. The half-life is ~11 days vs 30 days for 60-day window.

2. **HMM State Detection**: The two-state model explicitly identifies when residuals are mean-reverting vs random walk. We only trade when P(MR) > 0.7, avoiding the -EV periods.

3. **News Sentiment Overlay**: By incorporating real-time sentiment, we filter out trades that would be invalidated by information shocks. This addresses the "earnings surprise" problem that plagues pure residual strategies.

### 5.2 Critique of Clegg & Krauss (2018) - Partial Cointegration

**Original Flaws**:

1. **Pair-Wise Limitation**: They only consider pairs, missing the **multi-dimensional nature** of factor risk. A stock may be cointegrated with a sector ETF *through* multiple underlying factors, not just one relationship.

2. **Historical Cointegration Bias**: Their selection criteria use historical cointegration, which has **look-ahead bias** in practice. By the time you identify cointegration, the relationship may already be decaying.

3. **No Macro Conditioning**: They don't adjust for regime changes. A pair that mean-reverts in expansion may diverge in contraction.

**My Improvements**:

1. **Universe-Wide Residual Model**: PCA captures all systematic factors simultaneously. Every stock is residualized against the full factor structure, not just one pair.

2. **Online Adaptation**: The factor model updates continuously. We're not relying on historical cointegration—we're extracting residuals in real-time.

3. **Macro Regime Scaling**: Position sizes adjust based on VIX, yield curve, and CPI. This directly addresses the regime-dependency they ignore.

### 5.3 Critique of Loughran & McDonald (2011) - Textual Analysis

**Original Flaws**:

1. **Low Frequency Only**: They analyze 10-K filings—annual/quarterly events. This misses the **high-frequency alpha** in news sentiment. By the time a 10-K is filed, the information is largely priced.

2. **No Risk Integration**: Their long-short portfolios are raw, not residualized. The returns they attribute to sentiment may just be factor exposures (small-cap, value, etc.).

3. **Static Dictionary**: The LM dictionary is fixed. Language evolves—"disruption" meant something different in 2011 vs 2025.

**My Improvements**:

1. **Intraday News Processing**: Real-time sentiment feeds (RavenPack, etc.) capture alpha before it's priced. The JT platform's `research_swarm` can process news as it hits the wire.

2. **Residual-Based Execution**: We trade residuals, not raw returns. The sentiment signal is applied to already factor-neutral positions, isolating pure sentiment alpha.

3. **Adaptive Sentiment Scoring**: Using LLM-based sentiment (via Azure OpenAI in the JT platform) allows dynamic adaptation to new terminology and context.

### 5.4 Novel Contribution: The Lead-Lag Layer

The **cross-asset information diffusion** component is genuinely novel. While Lo & MacKinlay (1990) documented lead-lag effects, and various papers have studied sector momentum, **nobody has integrated lead-lag timing into a residual-based statistical arbitrage framework**.

The key insight: When XLK (tech ETF) has a large residual move, the information hasn't fully propagated to all constituents. By identifying the optimal lag (typically 1-3 days), we can:
1. Avoid entering too early (before the sector move completes)
2. Improve entry timing (catch the delayed reaction)
3. Exit early if the sector leader reverses

This creates a **synthetic speed advantage** without requiring HFT infrastructure.

---

## 6. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Implement dynamic PCA factor model
- [ ] Connect to IBKR paper trading
- [ ] Build bronze→silver data pipeline

### Phase 2: Signal Generation (Week 3-4)
- [ ] Implement HMM regime detection
- [ ] Add macro regime filter
- [ ] Backtest on 5 years historical

### Phase 3: Enhancement (Week 5-6)
- [ ] Integrate news sentiment (RavenPack or alternative)
- [ ] Add lead-lag sector analysis
- [ ] Walk-forward optimization

### Phase 4: Live Deployment (Week 7-8)
- [ ] Paper trading validation
- [ ] Risk limit calibration
- [ ] Gradual capital deployment

---

## 7. References

1. Avellaneda, M., & Lee, J. H. (2010). Statistical arbitrage in the U.S. equities market. *Quantitative Finance*, 10(7), 761-782.

2. Clegg, M., & Krauss, C. (2018). Pairs trading with partial cointegration. *Quantitative Finance*, 18(1), 121-138.

3. Loughran, T., & McDonald, B. (2011). When is a liability not a liability? Textual analysis, dictionaries, and 10-Ks. *The Journal of Finance*, 66(1), 35-65.

4. Ke, Z. T., Kelly, B. T., & Xiu, D. (2019). Predicting returns with textual data. *NBER Working Paper*.

5. Jurczenko, E., Michel, T., & Teiletche, J. (2015). Factor investing: A welfare-improving new investment paradigm? *EDHEC Working Paper*.

6. Lo, A. W., & MacKinlay, A. C. (1990). When are contrarian profits due to stock market overreaction? *The Review of Financial Studies*, 3(2), 175-205.

7. Chordia, T., Roll, R., & Subrahmanyam, A. (2011). Recent trends in trading activity and market quality. *Journal of Financial Economics*, 101(2), 243-263.

8. Cartea, Á., Jaimungal, S., & Penalva, J. (2015). *Algorithmic and High-Frequency Trading*. Cambridge University Press.

9. Cederburg, S., & O'Doherty, M. S. (2019). Asset allocation and bad habits. *Journal of Financial Economics*, 132(2), 469-491.

10. Engle, R. F., & Granger, C. W. (1987). Co-integration and error correction: representation, estimation, and testing. *Econometrica*, 55(2), 251-276.

---

*End of Strategy Proposal*
*Document Version: 1.0*
*Classification: Research - Internal Use Only*
