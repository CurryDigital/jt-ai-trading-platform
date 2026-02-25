# Archive Index

**What is this?** Decayed or superseded evidence. Moved here when weight drops below threshold (0.3) or expiry date reached.

---

## Archive Policy

**Auto-archive triggers:**
- Fact weight decays below 0.3
- Expiry date reached (typically 3-6 months)
- Superseded by higher-confidence evidence
- Market regime change invalidates previous findings

**Decay function:**
```
weight_t = weight_0 * exp(-λ * days)
where λ = 0.01 (half-life ~69 days)
```

---

## Archived Items

*None yet. Archive will populate as facts age or get superseded.*

---

## Archive Structure

```
archive/
├── superseded/          # Replaced by better evidence
├── expired/            # Past expiry date
├── regime_invalidated/ # No longer valid in current regime
└── low_confidence/     # Never reached sufficient weight
```

---

*Archived items can be retrieved for historical analysis but don't load into working context.*
