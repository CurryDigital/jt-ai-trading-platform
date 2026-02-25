# Hypothesis: PEAD Enhanced with LLM NLP

**Status:** testing  
**Created:** 2026-02-19  
**Academic Basis:** Ball & Brown (1968) + Lopez-Lira (2023)  
**Asset Class:** Equities  
**Direction:** Long/Short  
**Horizon:** 1-5 days  
**Target Win Rate:** 65-70%

---

## Core Idea

**Classic PEAD (Ball & Brown 1968):** Stock prices drift in direction of earnings surprise for days/weeks after announcement. Markets underreact to earnings news.

**Enhancement (Lopez-Lira 2023):** LLMs (ChatGPT/GPT-4) extract nuanced sentiment from earnings call transcripts better than traditional keyword methods. Combining PEAD + LLM sentiment improves entry timing and win rates.

---

## Signal Construction

### Step 1: Earnings Surprise Calculation
```python
# Standardized unexpected earnings (SUE)
sue = (actual_eps - consensus_eps) / std_eps_estimates

# Earnings surprise categories
if sue > 2.0:
    surprise = "large_positive"
elif sue > 0.5:
    surprise = "positive"
elif sue > -0.5:
    surprise = "neutral"
elif sue > -2.0:
    surprise = "negative"
else:
    surprise = "large_negative"
```

### Step 2: LLM Sentiment Analysis
```python
def llm_sentiment(transcript_text):
    """
    Use GPT-4 to analyze earnings call sentiment
    """
    prompt = f"""
    Analyze this earnings call transcript excerpt.
    
    Rate on scale -5 (very negative) to +5 (very positive):
    1. Management confidence in guidance
    2. Tone regarding macro environment
    3. Enthusiasm about new products/initiatives
    4. Defensiveness on questions
    
    Transcript: {transcript_text}
    
    Return JSON with scores and overall sentiment.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    sentiment_score = parse_json(response)
    return sentiment_score  # -5 to +5
```

### Step 3: Combined Signal
```python
# PEAD + LLM combo signal
if surprise == "large_positive" and llm_sentiment > 3:
    signal = "STRONG_LONG"
    confidence = 0.9
    
elif surprise == "positive" and llm_sentiment > 1:
    signal = "MODERATE_LONG"
    confidence = 0.75
    
elif surprise == "large_negative" and llm_sentiment < -3:
    signal = "STRONG_SHORT"
    confidence = 0.9
    
elif surprise == "negative" and llm_sentiment < -1:
    signal = "MODERATE_SHORT"
    confidence = 0.75
    
else:
    signal = "NO_TRADE"
    confidence = 0
```

---

## Entry Rules

```python
# ENTRY: After market close on earnings day
IF earnings_announced_today:
    
    # Get LLM sentiment from transcript
    transcript = fetch_call_transcript(ticker)
    sentiment = llm_sentiment(transcript)
    sue = calculate_sue(ticker)
    
    # Combined decision
    IF sue > 1.5 AND sentiment > 2:
        # Enter next day at open
        position_size = base_size * (0.5 + 0.5 * min(sentiment/5, 1))
        LONG
        
    ELIF sue < -1.5 AND sentiment < -2:
        position_size = base_size * (0.5 + 0.5 * abs(sentiment)/5)
        SHORT
```

---

## Exit Rules

```python
# Time-based (classic PEAD window)
IF hold_days >= 5:
    EXIT

# Momentum exhaustion
IF long_position AND price < entry_price * 0.97:  # -3% from entry
    EXIT  # Failed breakout
    
IF short_position AND price > entry_price * 1.03:  # +3% against us
    EXIT  # Failed breakdown

# Profit target
IF return > 5%:  # PEAD typically 2-5%
    EXIT 75%  # Take most profits
    
IF return > 8%:
    EXIT 100%  # Full exit on exceptional move
```

---

## Expected Performance

| Metric | Classic PEAD | PEAD + LLM | Improvement |
|--------|--------------|------------|-------------|
| Win Rate | 58-62% | 65-70% | +7-8% |
| Avg Return | 2-3% | 3-4% | +33% |
| Sharpe | 1.0-1.2 | 1.3-1.6 | +0.3-0.4 |
| False Signals | 38-42% | 30-35% | -8% |

**Academic Basis:** Lopez-Lira (2023) found LLM sentiment added 150-300bps annually to PEAD strategies.

---

## Data Requirements

- **Earnings data:** IBES/Zacks/Bloomberg (consensus vs actual)
- **Transcripts:** FactSet, Bloomberg, or Seeking Alpha (earnings call transcripts)
- **LLM API:** OpenAI GPT-4 ($0.03 per 1K tokens, ~$0.50 per transcript)
- **Timing:** After-hours earnings, trade next day open

---

## Risk Management

```python
# Position sizing based on confidence
if confidence > 0.85:
    position_size = 0.03  # 3%
elif confidence > 0.70:
    position_size = 0.02  # 2%
else:
    position_size = 0.01  # 1%

# Max exposure
max_earnings_exposure = 0.15  # 15% total in PEAD trades
max_same_day_earnings = 3  # Max 3 stocks reporting same day

# Stop loss
hard_stop = -0.04  # 4% max loss
```

---

## Backtest Plan

**Universe:** S&P 500 + Russell 1000  
**Period:** 2020-2024 (4 years, includes LLM era)  
**Frequency:** Daily during earnings season (Jan, Apr, Jul, Oct)  
**Benchmark:** S&P 500

**Test Variants:**
1. **Classic PEAD:** SUE only (baseline)
2. **PEAD + Keywords:** SUE + Loughran-McDonald sentiment
3. **PEAD + LLM:** SUE + GPT-4 sentiment (proposed)

**Success Criteria:**
- Win rate > 65%
- Sharpe > 1.3
- Positive alpha vs classic PEAD
- LLM variant beats keyword variant

---

## Academic Citations

```bibtex
@article{ball1968empirical,
  title={An empirical evaluation of accounting income numbers},
  author={Ball, Ray and Brown, Philip},
  journal={Journal of Accounting Research},
  year={1968}
}

@article{lopezlira2023chatgpt,
  title={Can ChatGPT Forecast Stock Price Movements?},
  author={Lopez-Lira, Alejandro and Tang, Yuehua},
  year={2023},
  institution={University of Florida}
}

@article{bernard1989post,
  title={Post-earnings-announcement drift: Delayed price response or risk premium?},
  author={Bernard, Victor L and Thomas, Jacob K},
  journal={Journal of Accounting Research},
  year={1989}
}
```

---

*The classic anomaly, enhanced by AI.*
