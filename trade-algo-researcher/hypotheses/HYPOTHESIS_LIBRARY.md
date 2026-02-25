# Hypothesis Library: Multi-Asset Research Ideas

**Date:** 2026-02-18  
**Goal:** 5+ hypotheses per asset class  
**Source:** Academic literature, market microstructure research, practitioner forums

---

## EQUITIES (5 Hypotheses)

### E1: Peer Firm Information Lag (Shell ↔ Sinopec Pattern)
**Status:** idea  
**Asset:** Equities (sector peers)  
**Direction:** Long/Short  
**Horizon:** 1-3 days  
**Sharpe Target:** 1.2-1.8

**Core Idea:** When major integrated oil company (Shell, XOM) announces earnings or strategic shift, smaller peers (Sinopec, CNPC, regional E&Ps) lag by 1-3 days in price adjustment.

**Academic Basis:**
- Menzly & Ozbas (2010): "Market Segmentation and Cross-Predictability of Returns"
- Cohen & Frazzini (2008): "Economic Links and Predictable Returns"

**Universe:**
- Majors: XOM, CVX, Shell, BP, Total
- Nationals: SNP (Sinopec), PTR (PetroChina), EC (Ecopetrol)
- Regionals: DVN, MRO, APA

**Signal:**
- Shell announces earnings miss → Short Sinopec next day
- XOM announces capex increase → Long energy services (SLB, HAL) with 2-day lag

**Validation:** Cross-correlation analysis at τ=1,2,3 days

---

### E2: ADR-Local Share Arbitrage
**Status:** idea  
**Asset:** Equities (ADR vs local)  
**Direction:** Neutral  
**Horizon:** Intraday to 1 day  
**Sharpe Target:** 1.5-2.5

**Core Idea:** Dual-listed stocks (e.g., BABA US vs 9988.HK, TSM US vs 2330.TW) exhibit temporary mispricing during market hours overlap due to liquidity differences and information asymmetry.

**Academic Basis:**
- Gagnon & Karolyi (2010): "Multi-market trading and arbitrage"
- Rabinovitch et al. (2003): ADR pricing dynamics

**Universe:**
- China: BABA/9988, JD/9618, NIO/9866
- Taiwan: TSM/2330, UMC/2303
- Japan: SONY/6758, Takeda/4502

**Signal:** Price deviation >1% during overlap hours → Trade convergence

**Risk:** Currency hedging required

---

### E3: Index Inclusion Pre-Announcement Drift
**Status:** idea  
**Asset:** Equities  
**Direction:** Long  
**Horizon:** 1-4 weeks  
**Sharpe Target:** 1.0-1.5

**Core Idea:** Stocks added to major indices (S&P 500, MSCI) exhibit upward drift in weeks before official announcement due to leakage and anticipatory buying.

**Academic Basis:**
- Chen et al. (2004): "The Information Content of Index Revisions"
- Petajisto (2011): "The index premium and its hidden cost"

**Signal Sources:**
- MSCI quarterly review dates (predictable)
- S&P 500 committee meeting patterns
- Market cap threshold tracking

**Universe:** Stocks near index inclusion thresholds

---

### E4: Short Interest Squeeze Predictor
**Status:** idea  
**Asset:** Equities (heavily shorted)  
**Direction:** Long  
**Horizon:** 1-5 days  
**Sharpe Target:** 1.5-2.5

**Core Idea:** Heavily shorted stocks with sudden positive news + high borrow costs are prone to gamma/short squeezes. Predictable from options market maker positioning.

**Academic Basis:**
- Bollen & Whaley (2004): "Does Net Buying Pressure Affect the Shape of Implied Volatility Functions?"
- Evans et al. (2009): Short interest and returns

**Signal Components:**
- Short interest >20% of float
- Cost to borrow increasing
- Call option gamma concentration
- Positive news catalyst

**Examples:** GME (2021), AMC (2021), numerous biotechs

---

### E5: ESG Rating Divergence Arbitrage
**Status:** idea  
**Asset:** Equities  
**Direction:** Long/Short  
**Horizon:** 1-3 months  
**Sharpe Target:** 0.8-1.2

**Core Idea:** Same company rated differently by MSCI vs Sustainalytics vs ISS creates temporary mispricing as ESG flows chase ratings upgrades/downgrades.

**Academic Basis:**
- Berg et al. (2022): "Aggregate Confusion: The Divergence of ESG Ratings"
- Pedersen et al. (2021): "Responsible investing: The ESG-efficient frontier"

**Signal:** MSCI upgrades while Sustainalytics lags → Long before ESG flows arrive

---

## FX (5 Hypotheses)

### F1: Carry Trade with Volatility Scaling
**Status:** idea  
**Asset:** FX (G10 + EM)  
**Direction:** Long carry  
**Horizon:** 1-4 weeks  
**Sharpe Target:** 1.0-1.4

**Core Idea:** Traditional FX carry (long high yield, short low yield) enhanced by volatility scaling — reduce size when VIX >25 or FX vol spikes.

**Academic Basis:**
- Brunnermeier et al. (2009): "Carry Trades and Currency Crashes"
- Menkhoff et al. (2012): "Currency Momentum Strategies"

**Universe:** AUD, NZD, BRL, MXN, ZAR vs JPY, CHF, EUR

---

### F2: Central Bank Communication Pre-Drift
**Status:** idea  
**Asset:** FX (policy-sensitive pairs)  
**Direction:** Long/Short  
**Horizon:** 1-3 days  
**Sharpe Target:** 1.2-1.8

**Core Idea:** NLP analysis of central bank speeches (Fed, ECB, BOJ) predicts FX moves 1-3 days before official policy announcements.

**Academic Basis:**
- Lucca & Trebbi (2009): "Measuring Central Bank Communication"
- Hansen & McMahon (2016): "Shocking language"

**Signal:** Hawkish/dovish tone shift in speeches → Position before meeting

---

### F3: Asian Session Liquidity Gaps
**Status:** idea  
**Asset:** FX (USD/JPY, AUD/USD)  
**Direction:** Mean reversion  
**Horizon:** Intraday  
**Sharpe Target:** 1.5-2.0

**Core Idea:** Large moves in thin Asian session (Tokyo open) often reverse during London/NY session as liquidity returns.

**Academic Basis:**
- Ito & Hashimoto (2006): "Microstructure of FX market"
- Breedon & Ranaldo (2013): Intraday patterns

**Signal:** >1% move in Asian session with no news → Fade in London

---

### F4: Terms of Trade Momentum
**Status:** idea  
**Asset:** FX (commodity currencies)  
**Direction:** Long/Short  
**Horizon:** 1-3 months  
**Sharpe Target:** 0.9-1.3

**Core Idea:** Currencies of commodity exporters (AUD, CAD, NOK, BRL) follow terms of trade shifts with 1-2 month lag.

**Academic Basis:**
- Chen & Rogoff (2003): "Commodity Currencies"
- Clements & Lan (2010): Terms of trade forecasting

**Signal:** Commodity price index change → FX position 1 month later

---

### F5: SAFE Haven Rotation
**Status:** idea  
**Asset:** FX (JPY, CHF, USD)  
**Direction:** Rotation  
**Horizon:** 1-2 weeks  
**Sharpe Target:** 1.0-1.5

**Core Idea:** During risk-off, safe havens rotate: JPY first (Asia hours), then CHF (Europe), then USD (US). Predictable sequence.

**Academic Basis:**
- Ranaldo & Söderlind (2010): "Safe Haven Currencies"
- Hossfeld & MacDonald (2015): Carry and safe havens

**Signal:** VIX spike → Buy JPY, rotate to CHF 6 hours later, USD 12 hours later

---

## CRYPTO (5 Hypotheses)

### C1: Exchange Funding Rate Arbitrage
**Status:** backtested (existing strategy)  
**Asset:** Crypto perpetuals  
**Direction:** Neutral  
**Horizon:** Hours to days  
**Sharpe Target:** 2.5

**Core Idea:** Capture funding payments by shorting perp + long spot when funding is positive. Cross-exchange variant.

**Already implemented:** See strategies/crypto/funding_rate_arb/

---

### C2: Halving Cycle Regime Detection
**Status:** idea  
**Asset:** BTC, ETH  
**Direction:** Long/Neutral  
**Horizon:** Months  
**Sharpe Target:** 2.0+

**Core Idea:** 4-year halving cycle creates predictable boom-bust. Use HMM to detect regime (accumulation, bull, distribution, bear) and only trade bull phases.

**Academic Basis:**
- Baur & Dimpfl (2021): "The volatility of Bitcoin"
- Akyildirim et al. (2021): Bitcoin return predictability

---

### C3: Stablecoin Depeg Recovery
**Status:** idea  
**Asset:** Stablecoins (USDT, USDC, DAI)  
**Direction:** Mean reversion  
**Horizon:** Hours to days  
**Sharpe Target:** 2.0-3.0

**Core Idea:** Major stablecoins (USDT, USDC) depeg during stress but recover within days. Buy when <$0.995, sell when >$0.999.

**Academic Basis:**
- Lyons & Viswanath-Natraj (2020): "What Keeps Stablecoins Stable?"
- Auer (2022): BIS stablecoin analysis

**Risk:** Tail risk of permanent depeg (UST example)

---

### C4: Miner Capitulation Bottom Indicator
**Status:** idea  
**Asset:** BTC  
**Direction:** Long  
**Horizon:** 1-3 months  
**Sharpe Target:** 1.5-2.5

**Core Idea:** When BTC price drops below all-in miner cost of production, miners capitulate and sell. This marks local bottoms.

**Academic Basis:**
- Hayes (2019): "Bitcoin Miner Capitulation"
- Kaloudis (2021): Coin Metrics miner analysis

**Signal:** Hash ribbons (30d MA crossing below 60d MA) + price < mining cost

---

### C5: Altcoin Beta to ETH Momentum
**Status:** idea  
**Asset:** Altcoins (SOL, AVAX, MATIC, etc.)  
**Direction:** Long  
**Horizon:** 1-2 weeks  
**Sharpe Target:** 1.2-1.8

**Core Idea:** Large-cap alts (SOL, AVAX, etc.) exhibit 1-3 day lag to ETH moves with 1.2-1.5x beta. Trade the catch-up.

**Academic Basis:**
- Liu (2019): "Altcoin return spillovers"
- Crypto market microstructure studies

**Signal:** ETH +5% in 24h → Long altcoin basket next day

---

## COMMODITIES (5 Hypotheses)

### M1: Energy Crack Spread Arb
**Status:** idea  
**Asset:** Oil products (CL, RB, HO)  
**Direction:** Spread  
**Horizon:** 1-2 weeks  
**Sharpe Target:** 1.0-1.5

**Core Idea:** 3:2:1 crack spread (3 crude → 2 gasoline + 1 heating oil) mean-reverts. Trade when spread >2 std dev from historical.

**Academic Basis:**
- Girma & Paulson (1999): "Risk arbitrage opportunities in petroleum spreads"
- Commodity trading classics

---

### M2: Precious Metals Ratio Rotation
**Status:** idea  
**Asset:** Gold, Silver, Platinum  
**Direction:** Long/Short  
**Horizon:** 1-3 months  
**Sharpe Target:** 0.8-1.2

**Core Idea:** Gold/Silver ratio mean-reverts (historical ~50-80). When ratio >80, long silver/short gold.

**Academic Basis:**
- Lucey et al. (2006): "The relationship between gold and silver prices"
- Escribano & Granger (1998): Cointegration in metals

---

### M3: LNG Shipping Rate Lag
**Status:** idea  
**Asset:** Natural Gas (NG) + Shipping (dry bulk proxies)  
**Direction:** Long/Short  
**Horizon:** 2-4 weeks  
**Sharpe Target:** 1.0-1.4

**Core Idea:** LNG shipping rates (BDI proxy) lead natural gas prices by 2-4 weeks. High shipping demand → gas demand follows.

**Universe:** NG futures, BDI index, LNG shipping stocks (FRO, GLNG)

---

### M4: Agricultural Weather Delta
**Status:** idea  
**Asset:** Corn, Wheat, Soybeans  
**Direction:** Long/Short  
**Horizon:** Days to weeks  
**Sharpe Target:** 1.0-1.5

**Core Idea:** NOAA weather forecasts (drought, planting conditions) predict ag prices but market underreacts to 7-14 day forecasts vs immediate conditions.

**Academic Basis:**
- Tannura et al. (2008): "Weather effects on corn yields"
- USDA + weather forecasting literature

---

### M5: LME Warehouse Stock Shadow
**Status:** idea  
**Asset:** Industrial metals (Copper, Aluminum, Zinc)  
**Direction:** Long/Short  
**Horizon:** 1-4 weeks  
**Sharpe Target:** 0.9-1.3

**Core Idea:** LME warehouse inventory changes predict futures prices with 1-2 week lag. Stock builds → price drops.

**Academic Basis:**
- Geman (2005): "Commodities and Commodity Derivatives"
- Inventory-price relationship in metals

---

## CROSS-ASSET (5 Hypotheses)

### X1: VIX Contango Roll Yield
**Status:** idea  
**Asset:** VIX futures, SPX options  
**Direction:** Short vol  
**Horizon:** 1-4 weeks  
**Sharpe Target:** 1.0-1.4

**Core Idea:** VIX futures in contango (majority of time) creates persistent roll yield. Short VIX futures captures this.

**Academic Basis:**
- Whaley (2013): "Fear and Greed in Financial Markets"
- Simon & Campasano (2014): "The VIX Futures Basis"

**Risk:** Tail events (Feb 2018 "Volmageddon")

---

### X2: Credit-Equity Lag (HYG/SPY Divergence)
**Status:** idea  
**Asset:** High yield bonds (HYG) + S&P 500 (SPY)  
**Direction:** Long/Short  
**Horizon:** 1-2 weeks  
**Sharpe Target:** 1.0-1.5

**Core Idea:** High yield bonds lead equity during credit stress. HYG decline predicts SPY drop with 3-5 day lag.

**Academic Basis:**
- Kwan (1996): "Can bond yields predict equity returns?"
- Gilchrist & Zakrajšek (2012): "Credit Spreads and Business Cycle Fluctuations"

---

### X3: Term Structure Slope Rotation
**Status:** idea  
**Asset:** Bonds (TLT, IEF, SHY)  
**Direction:** Rotation  
**Horizon:** 1-3 months  
**Sharpe Target:** 0.8-1.2

**Core Idea:** Yield curve steepening/flattening predicts sector rotation. Steepener → long banks/financials, short utilities.

**Academic Basis:**
- Estrella & Hardouvelis (1991): "The Term Structure as a Predictor of Real Economic Activity"
- Yield curve literature

---

### X4: Gold vs Real Rates Macro Hedge
**Status:** live (existing)  
**Asset:** Gold + TIPS  
**Direction:** Long gold  
**Horizon:** Months  
**Sharpe Target:** 1.3

**Core Idea:** Gold inversely correlated with real rates (TIPS yields). When real rates <0.5% and falling, long gold.

**Already implemented:** See strategies/cross_asset/macro/gold_real_rates/

---

### X5: Quantitative Tightening Liquidity Crunch
**Status:** idea  
**Asset:** Cross-asset  
**Direction:** Risk-off positioning  
**Horizon:** 1-4 weeks  
**Sharpe Target:** 1.0-1.5

**Core Idea:** Fed QT + RRP drainage creates predictable liquidity crunches. Monitor Fed balance sheet → reduce risk when liquidity drops >$100B/week.

**Academic Basis:**
- Pozsar (2022): "Global Money Notes"
- Fed balance sheet and market liquidity studies

---

## SUMMARY TABLE

| Asset | Hypothesis | Status | Sharpe Target |
|-------|-----------|--------|---------------|
| **Equities** | E1 Peer Lag | idea | 1.2-1.8 |
| **Equities** | E2 ADR Arbitrage | idea | 1.5-2.5 |
| **Equities** | E3 Index Inclusion | idea | 1.0-1.5 |
| **Equities** | E4 Short Squeeze | idea | 1.5-2.5 |
| **Equities** | E5 ESG Divergence | idea | 0.8-1.2 |
| **FX** | F1 Carry + Vol | idea | 1.0-1.4 |
| **FX** | F2 CB NLP | idea | 1.2-1.8 |
| **FX** | F3 Asian Liquidity | idea | 1.5-2.0 |
| **FX** | F4 Terms of Trade | idea | 0.9-1.3 |
| **FX** | F5 Safe Haven Rotation | idea | 1.0-1.5 |
| **Crypto** | C1 Funding Arb | backtested | 2.5 |
| **Crypto** | C2 Halving HMM | idea | 2.0+ |
| **Crypto** | C3 Stablecoin Depeg | idea | 2.0-3.0 |
| **Crypto** | C4 Miner Capitulation | idea | 1.5-2.5 |
| **Crypto** | C5 Altcoin Beta | idea | 1.2-1.8 |
| **Commodities** | M1 Crack Spread | idea | 1.0-1.5 |
| **Commodities** | M2 Metals Ratio | idea | 0.8-1.2 |
| **Commodities** | M3 LNG Shipping | idea | 1.0-1.4 |
| **Commodities** | M4 Ag Weather | idea | 1.0-1.5 |
| **Commodities** | M5 LME Inventory | idea | 0.9-1.3 |
| **Cross-Asset** | X1 VIX Contango | idea | 1.0-1.4 |
| **Cross-Asset** | X2 Credit-Equity | idea | 1.0-1.5 |
| **Cross-Asset** | X3 Yield Curve | idea | 0.8-1.2 |
| **Cross-Asset** | X4 Gold/Real Rates | live | 1.3 |
| **Cross-Asset** | X5 QT Liquidity | idea | 1.0-1.5 |

**Total: 25 hypotheses (5 per asset class)**

---

*Next step: Prioritize which to validate first based on data availability and expected Sharpe.*
