# New Hypotheses from Recent Academic Research (2020-2026)

**Date:** 2026-02-19  
**Source:** Post-2020 quant finance research trends  
**New Hypotheses:** 5  

---

## Summary

| # | Hypothesis | Source | Theme | Data Required |
|---|------------|--------|-------|---------------|
| 1 | **ESG Momentum** | Bolton et al. (2023), Pedersen (2021) | Greenium effect | MSCI/Sustainalytics ESG ratings |
| 2 | **Retail Order Flow** | Barber/Odean (2023), Welch (2022) | Post-meme stock retail behavior | Whalesburg, social media |
| 3 | **Supply Chain Reshoring** | Baldwin (2022), IMF (2023) | Geo-economic fragmentation | Earnings NLP, gov contracts |
| 4 | **Inflation Regime Switching** | Reis (2022), Blanchard (2023) | Transitory vs persistent inflation | CPI, wage data, breakevens |
| 5 | **LLM/NLP Sentiment** | Lopez-Lira (2023), Kim (2024) | ChatGPT/LLM in finance | LLM API, earnings transcripts |

---

## 1. ESG Momentum (Greenium)

**Academic Basis:**
- Bolton, P. et al. (2023). "Sustainable Investing." *Journal of Finance*
- Pedersen, L. et al. (2021). "Responsible Investing." *NBER*

**Core Idea:** ESG rating upgrades predict outperformance due to institutional mandate flows and lower cost of capital.

**Signal:** Long ESG upgrades, hold 6-12 months
**Target:** 55-60% win rate, 8-12% annual return
**Risk:** ESG premium arbitrage away as flows increase

**Status:** ⏳ Needs ESG rating data (MSCI/Sustainalytics subscription)

---

## 2. Retail Order Flow Imbalance

**Academic Basis:**
- Barber, B. & Odean, T. (2023). "The Behavior of Individual Investors."
- Welch, I. (2022). "The Wisdom of the Robinhood Crowd."

**Core Idea:** Retail investors are noise traders. Extreme retail buying predicts short-term reversal (overreaction).

**Signal:** Fade retail FOMO (short extreme buying), buy retail panic
**Target:** 58-62% win rate, 2-4% per trade
**Data:** Whalesburg, Reddit sentiment, small-lot options

**Status:** ⏳ Needs alternative data (Whalesburg, social media APIs)

---

## 3. Supply Chain Reshoring

**Academic Basis:**
- Baldwin, R. (2022). "Globalization 2.0: Supply Chains in the 2020s."
- IMF (2023). "Geo-economic Fragmentation and the Future of Multilateralism."

**Core Idea:** Post-COVID + geopolitical tensions = massive reshoring trend. Companies relocating to US/Mexico/Vietnam/India benefit from subsidies and lower risk.

**Signal:** Long CHIPS Act winners, Mexico REITs, reshoring announcements
**Target:** 60-65% win rate, 15-25% annual return
**Duration:** 3-5 year theme (2023-2028)

**Status:** ⏳ Needs earnings NLP + government contract data

---

## 4. Inflation Regime Switching

**Academic Basis:**
- Reis, R. (2022). "Losing the Inflation Anchor." *Jackson Hole Symposium*
- Blanchard, O. (2023). "Why I Was Wrong About Inflation."
- Cieslak, A. (2023). "Inflation and Asset Returns."

**Core Idea:** Markets exhibit distinct inflationary vs disinflationary regimes. ML classifiers predict switches using CPI, wage growth, supply chain pressure.

**Signal:** 
- Inflationary: Long commodities/REITs, short bonds
- Disinflationary: Long tech/bonds, short commodities

**Target:** 60-70% regime prediction accuracy
**Data:** CPI, Atlanta Fed Wage Tracker, NY Fed Supply Chain Index

**Status:** ⏳ Needs real-time macro data feeds

---

## 5. LLM/NLP Sentiment Edge

**Academic Basis:**
- Lopez-Lira, A. (2023). "Can ChatGPT Forecast Stock Price Movements?"
- Kim, A. et al. (2024). "Large Language Models and Financial Sentiment."

**Core Idea:** LLMs (GPT-4) extract nuanced sentiment from earnings transcripts better than traditional keyword methods. Predicts 1-5 day drift.

**Signal:** LLM sentiment score > +3 → Long; < -3 → Short
**Target:** 58-65% win rate, 1.0-1.4 Sharpe
**Cost:** $100-500/month for API calls
**Decay Risk:** Edge temporary as adoption increases

**Status:** ⏳ Needs LLM API + earnings transcript data

---

## Data Requirements Summary

| Hypothesis | Free Data | Paid Data | Est. Cost |
|------------|-----------|-----------|-----------|
| ESG Momentum | ESG ETF holdings | MSCI/Sustainalytics | $500-2000/mo |
| Retail Flow | Reddit API | Whalesburg, social | $100-500/mo |
| Reshoring | Gov contracts (public) | Earnings NLP, Dodge | $200-1000/mo |
| Inflation Regime | CPI, BLS data | Real-time feeds | $50-200/mo |
| LLM Sentiment | OpenAI API | FactSet transcripts | $100-1000/mo |

---

## Testing Priority

**High Priority (Easy Data):**
1. Inflation Regime - BLS data free, clear signal
2. LLM Sentiment - OpenAI API accessible

**Medium Priority (Moderate Cost):**
3. Retail Flow - Whalesburg subscription
4. Reshoring - NLP on earnings calls

**Lower Priority (Expensive):**
5. ESG Momentum - MSCI ratings costly

---

## Total Hypothesis Count

- Previous: 75
- New: 5
- **Total: 80 active hypotheses**

---

**Research trend: Post-2020 focus on alternative data, ML/AI, ESG, and geopolitical themes.**
