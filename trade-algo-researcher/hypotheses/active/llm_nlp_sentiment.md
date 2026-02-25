# Hypothesis: LLM/NLP Sentiment Edge

**Status:** idea  
**Created:** 2026-02-19  
**Source:** LLM revolution (ChatGPT 2022+) applied to finance  
**Asset Class:** Equities  
**Direction:** Long/Short  
**Horizon:** 1-5 days  
**Target Win Rate:** 58-65%

---

## Core Idea

Large Language Models (GPT-4, Claude) extract sentiment from:
- Earnings call transcripts (tone analysis)
- SEC filings (10-K, 10-Q forward-looking statements)
- Social media (Reddit, Twitter)
- News articles

Better than traditional keyword methods (Loughran-McDonald) because:
1. Context understanding (irony, nuance)
2. Entity recognition ("Apple" vs "apple")
3. Temporal reasoning ("will increase" vs "increased")

**Academic Support:**
- Ke et al. (2019) updated with LLMs (2023-2024 papers)
- Lopez-Lira (2023): "Can ChatGPT Forecast Stock Returns?"
- Kim et al. (2024): "LLM sentiment and stock returns"

---

## Signal Construction

**LLM Pipeline:**
```python
# Input: Earnings transcript paragraph
prompt = "Analyze the sentiment of this earnings statement. 
          Is management confident, cautious, or concerned?
          Rate -5 (very negative) to +5 (very positive)."

sentiment_score = LLM(prompt)

IF sentiment_score > 3 AND revenue_beat:
    Long stock
    
IF sentiment_score < -3 AND revenue_miss:
    Short stock
```

**Data Sources:**
- Earnings transcripts (FactSet, Bloomberg)
- SEC filings (EDGAR)
- Social media APIs

---

## Expected Performance

| Metric | Target |
|--------|--------|
| Win Rate | 58-65% |
| Sharpe | 1.0-1.4 |
| Information Ratio | 0.8-1.2 vs traditional NLP |
| Cost | API calls ($0.01-0.10 per analysis) |

---

## Implementation

**Approaches:**
1. **Fine-tuned model:** Train LLM on financial sentiment (expensive)
2. **Prompt engineering:** Use GPT-4 with custom prompts (easier)
3. **Pre-built:** Use BloombergGPT, FinBERT (limited)

**Edge Decay:** As more funds use LLMs, edge will diminish (2024-2026 risk)

---

## Data Requirements

- **LLM API:** OpenAI, Anthropic, or open-source (Llama)
- **Transcripts:** FactSet, Seeking Alpha, company IR
- **Compute:** ~$100-500/month for API calls

---

*The AI advantage (temporary).*
