# Hypothesis: Federal Reserve Speech NLP Alpha

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** Equities / FX / Rates  
**Direction:** Long/Short (hawkish/dovish)  
**Horizon:** 1-5 days  
**Target Win Rate:** 58-65%

---

## Core Idea

Fed Chair and FOMC member speeches contain predictive language. NLP analysis of hawkish vs dovish tone predicts rate move probabilities and market direction. Academic research confirms 50-100bp drift in 24 hours.

**The Edge:**
- Market parses speeches slowly (information processing delay)
- Tone shifts precede policy changes by 2-4 weeks
- "Fedspeak" NLP models capture subtle shifts

---

## Signal Construction

**Hawkish Keywords:**
```
inflation, tightening, restrict, patient, vigilance, 
price stability, above target, upside risks
```

**Dovish Keywords:**
```
accommodative, support, gradual, patient, data-dependent,
employment, downside risks, below target, symmetric
```

**Signal Scoring:**
```python
# Hawkish score
hawkish_count = count_keywords(text, hawkish_dict)
dovish_count = count_keywords(text, dovish_dict)
sentiment_score = (hawkish_count - dovish_count) / total_words

# Market impact prediction
IF sentiment_score > 0.3 (hawkish shift):
    → Short TLT (rates up), long USD, short QQQ
    
IF sentiment_score < -0.3 (dovish shift):
    → Long TLT (rates down), short USD, long QQQ
```

---

## Expected Performance

| Speaker | Impact | Win Rate | Sharpe |
|---------|--------|----------|--------|
| Fed Chair (Powell) | High | 65% | 1.4 |
| Vice Chair | Medium | 58% | 1.0 |
| Regional Presidents | Low | 52% | 0.6 |
| FOMC Minutes | High | 60% | 1.2 |

**Best Opportunities:**
- Post-meeting press conferences (Q&A = unscripted)
- Jackson Hole speech (policy framework)
- Congressional testimony (forced clarity)

---

## Data Requirements

- **Fed speech calendar** - scheduled appearances
- **Transcript API** - real-time text extraction
- **FinBERT/LM Dictionary** - financial sentiment
- **Latency:** <10 minutes speech to signal

**Sources:**
- Federal Reserve website (transcripts)
- Bloomberg/Reuters (live coverage)
- YouTube/Stream (real-time audio)

---

## Trade Mapping

| Signal | Long | Short | Duration |
|--------|------|-------|----------|
| Hawkish | DXY (dollar) | TLT, QQQ, GLD | 2-3 days |
| Dovish | TLT, QQQ, GLD | DXY | 2-3 days |
| Uncertain | VIX options | — | 1-2 days |

---

## Academic Support

- Lucca & Moench (2015): Pre-FOMC announcement drift (50bp)
- Cieslak et al. (2019): Fed policy news and stock returns
- Fischer et al. (2022): NLP on central bank communication
- Bollerslev et al. (2020): Treasury market news effects

---

## Risk Factors

1. **Fed put** — Market expects Powell to support stocks
2. **Communication strategy** — Deliberate obfuscation ("data-dependent")
3. **Global coordination** — ECB/BOJ speeches confound signal
4. **Algo parsing** — Fast money front-runs within seconds

---

## Implementation

**Pre-positioning:** 
- Enter before scheduled speech (calendar known)
- Size: 1-2% (medium conviction)

**Post-speech:**
- Scale in on confirmation (5-min momentum)
- Hold 24-48 hours
- Exit before next Fed speaker (noise)

---

*The most predictable news alpha — central bank communication.*
