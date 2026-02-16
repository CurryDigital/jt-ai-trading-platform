# Strategy Reference Doc

## Core Strategy Papers
1. **Trading strategies and Financial Performances: A simulation approach** (ScienceDirect 2024)
   - Source: https://www.sciencedirect.com/science/article/pii/S1057521924003582
   - Focus: Multi-agent simulation comparing Sharpe Ratio maximization vs. Expected Shortfall (CVaR) minimization.
   - Orchestra Implementation: Added `expected_shortfall_95` and `sharpe_ratio` to Gold layer for all assets.
2. **Quantformer: Attention-based Quantitative Trading**
   - Source: https://arxiv.org/html/2404.00424v3
   - Focus: Cross-sectional Z-score ranking and transformer-based return forecasting.

## FX & High-Volume Strategy Papers (Target for FX Enhancement)
3. **On-Chain Liquidity Cycles in Cryptocurrencies**
   - Focus: Using stablecoin (USDT/USDC) mint/burn events as leading indicators for BTC/ETH volatility and liquidity flushes.
4. **High-Frequency Factor Fusion using Temporal Transformers**
   - Focus: Merging technical indicators (RSI/MACD) with macro-fundamental data (Yields/PE) via time-attention mechanisms for intraday precision.
5. **Geopolitical Shock Modeling in FX Markets**
   - Focus: Quantification of news sentiment (e.g., "Trump Tariffs") into vectors to predict volatility spikes and liquidation events in major fiat pairs.

## Crypto Specialized Strategy Papers (Target for Crypto Upgrade)
6. **Multi-Agent Framework for On-Chain and Sentiment Fusion** (Arxiv 2024/2025)
   - Concept: **Liquidity-Sentiment Divergence (LSD)**.
   - Alpha: Detecting "Quiet Accumulation" by institutional players when on-chain inflows rise while social sentiment (Fear/Greed) remains low.
   - Orchestra Plan: Implement a divergence detector comparing `exchange_inflow_proxy` against the `fear_greed_index` to identify 10%+ volatility "Jump" events.
