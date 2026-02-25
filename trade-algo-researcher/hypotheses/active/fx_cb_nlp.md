# Hypothesis: Central Bank Communication NLP Alpha

**Status:** testing  
**Created:** 2026-02-18  
**Asset Class:** FX  
**Direction:** Long/Short  
**Horizon:** 1-3 days  
**Target Sharpe:** 1.2-1.8

---

## Core Idea

NLP analysis of central bank speeches (Fed, ECB, BOJ, BOE) predicts FX moves 1-3 days before official policy announcements. Central bankers "telegraph" intentions in speeches before formal decisions.

**Examples:**
- Fed Governor speech with hawkish tone → USD/JPY up before FOMC
- ECB President dovish rhetoric → EUR/USD down before rate decision
- BOJ mentions yield flexibility → JPY strengthens

---

## Academic Foundation

**Lucca, D.O. & Trebbi, F. (2009):** "Measuring Central Bank Communication"
- NBER Working Paper
- Tone changes in Fed speeches predict policy shifts
- Market reacts gradually to communication changes

**Hansen, S. & McMahon, M. (2016):** "Shocking Language"
- University of Oxford
- NLP extraction from central bank transcripts
- Hawkish/dovish scoring predicts bond yields

**Hoesli, M. & Watte, C. (2023):** "Measuring text-based sentiments from monetary policy statements"
- Quantifying central bank communication with LLMs
- Sentiment scores predict FX movements 1-3 days ahead

---

## Signal Construction

### Hawkish-Dovish Score
```python
def tone_score(speech_text):
    """
    Score speech from -10 (very dovish) to +10 (very hawkish)
    """
    hawkish_words = [
        'inflation', 'tighten', 'restrictive', 'elevated',
        'vigilant', 'resolute', 'committed', 'hawkish'
    ]
    
    dovish_words = [
        'accommodative', 'patient', 'gradual', 'data-dependent',
        'flexible', 'cautious', 'supportive', 'dovish'
    ]
    
    hawkish_count = sum(word in speech_text.lower() for word in hawkish_words)
    dovish_count = sum(word in speech_text.lower() for word in dovish_words)
    
    score = (hawkish_count - dovish_count) / (hawkish_count + dovish_count + 1)
    return score * 10  # Scale to -10 to +10
```

### Trading Signal
1. **Speech tone shift >3 points from prior:** Significant policy shift incoming
2. **Position:** Direction of tone shift
3. **Hold:** Until official policy announcement or 3 days

---

## Universe

| Central Bank | Currency Pairs | Speech Frequency |
|--------------|----------------|------------------|
| Federal Reserve | USD/JPY, EUR/USD, DXY | Weekly (Fed speakers) |
| ECB | EUR/USD, EUR/JPY | Monthly (Lagarde) |
| BOJ | USD/JPY, EUR/JPY | Quarterly (Kuroda/Ueda) |
| BOE | GBP/USD, EUR/GBP | Quarterly (Bailey) |

---

## Data Requirements

- Central bank speech transcripts (Fed website, ECB website)
- Speech calendar (predictable)
- FX tick data for event study
- NLP processing (spaCy, NLTK)

---

## Risk Factors

1. **Translation:** Non-English speeches (ECB, BOJ) may lose nuance
2. **Committee dynamics:** One speaker ≠ entire committee
3. **Market positioning:** Crowded trades may reverse on "buy the rumor, sell the news"
4. **News overlap:** Speech may coincide with other macro data

---

*Next step: Collect 5 years of Fed speeches and backtest tone vs USD/JPY.*
