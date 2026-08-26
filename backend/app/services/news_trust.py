"""News cluster trust scoring — serving-layer anti-spam overlay.

Consumes serialized /api/news/clusters payloads (dicts with canonical_headline,
story_count, outlet_count, members[], tickers[], asset_class, llm_*) and emits a
trust-adjusted score with an itemized, explainable penalty list. Raw
impact_score is NEVER mutated — the trust layer is additive metadata plus a
re-ranking key, so downstream consumers can audit exactly why a cluster moved.

Design goals (goal of 2026-08-17):
- outlet diversity acts as a divisor, raw story volume never as a multiplier:
  26 stories from 1 outlet (content farm) must score below 6 stories from 6
  outlets.
- syndication dedup: one wire story on 12 sites is one signal (measured via
  distinct normalized headlines, not just outlet_count).
- named, itemized penalties: affiliate / tutorial / press_release /
  auto_generated / microcap_crypto / llm_flagged_spam.
- source reputation weighting with an explicit, maintainable list.

All functions are pure — unit-testable without a DB.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Source reputation list. Keys are canonical hosts (www. stripped). Weight in
# [0,1]; 1.0 = primary wire/major, ~0.4 = auto-generation-heavy aggregator,
# <=0.3 = open blog platform. Unknown outlets get DEFAULT_OUTLET_WEIGHT.
# Extend deliberately — this list IS the reputation model.
# ---------------------------------------------------------------------------
SOURCE_WEIGHTS = {
    # primary wires / global majors
    "reuters.com": 1.0, "apnews.com": 1.0, "bloomberg.com": 1.0,
    "ft.com": 1.0, "wsj.com": 1.0, "nytimes.com": 0.95, "bbc.com": 0.95,
    "bbc.co.uk": 0.95, "cnbc.com": 0.95, "economist.com": 0.95,
    "barrons.com": 0.9, "scmp.com": 0.9, "theguardian.com": 0.9,
    "marketwatch.com": 0.85, "finance.yahoo.com": 0.8, "yahoo.com": 0.8,
    "investing.com": 0.8, "thestandard.com.hk": 0.8, "aastocks.com": 0.75,
    "hket.com": 0.8, "mingpao.com": 0.8, "stheadline.com": 0.75,
    # crypto-native
    "coindesk.com": 0.75, "theblock.co": 0.75, "cointelegraph.com": 0.6,
    "decrypt.co": 0.65,
    # mainstream-analysis (human-written but mixed quality)
    "fool.com": 0.7, "seekingalpha.com": 0.7, "benzinga.com": 0.6,
    "zacks.com": 0.6, "substack.com": 0.5, "wallstreetzen.com": 0.5,
    # auto-generation-heavy aggregators
    "marketbeat.com": 0.45, "americanbankingnews.com": 0.4,
    "defenseworld.net": 0.4, "tickerreport.com": 0.4,
    "markets.financialcontent.com": 0.4, "theolympiareport.com": 0.35,
    "dailypolitical.com": 0.35, "wkrb13.com": 0.35, "modernreaders.com": 0.35,
    "techknowbits.com": 0.35, "thecerbatgem.com": 0.35,
    "communitynewspapergroup.com": 0.35, "rivertonroll.com": 0.35,
    "slugline.co": 0.35, "beatdaily.com": 0.35, "linesandlifestyle.com": 0.35,
    "sportsperspectives.com": 0.35, "theenterpriseleader.com": 0.35,
    "transcriptdaily.com": 0.35, "watchwirenews.com": 0.35,
    "fintechdaily.news": 0.35, "marketsdaily.news": 0.35,
    # press-release distribution (also PR_WIRES below)
    "globenewswire.com": 0.35, "accesswire.com": 0.35, "prnewswire.com": 0.35,
    "businesswire.com": 0.35, "einpresswire.com": 0.3, "openpr.com": 0.3,
    # open blog platforms (content farms live here)
    "blog.udn.com": 0.25, "blogspot.com": 0.25, "wordpress.com": 0.25,
    "medium.com": 0.4, "pixnet.net": 0.25, "xuite.net": 0.25,
}
DEFAULT_OUTLET_WEIGHT = 0.7

PR_WIRE_HOSTS = {
    "globenewswire.com", "accesswire.com", "prnewswire.com",
    "businesswire.com", "einpresswire.com", "openpr.com", "pr.com",
    "newswire.ca", "prweb.com",
}

# Major crypto assets exempt from the micro-cap penalty (plus anything held —
# the caller passes the held set; a position you own is never "noise").
MAJOR_CRYPTO = {
    "BTC", "ETH", "SOL", "XRP", "BNB", "DOGE", "ADA", "TRX", "AVAX", "LINK",
    "LTC", "BCH", "DOT", "UNI", "AAVE", "BTC-USD", "ETH-USD",
}

# ---------------------------------------------------------------------------
# Penalty patterns. Each: (kind, factor, compiled regex, human detail).
# Factors multiply; the product is floored so a cluster can be driven to ~0
# but the arithmetic stays inspectable.
# ---------------------------------------------------------------------------
_AFFILIATE = re.compile(
    r"\b(referral|invitation|promo)\s*code\b|\brebate\b|\b返[利佣]\b"
    r"|\bsign[- ]?up bonus\b|\bexclusive (benefits|rewards)\b"
    r"|【\s*[A-Z0-9]{4,10}\s*】|\[\s*[A-Z0-9]{5,8}\s*\]"
    r"|邀请码|邀請碼|推荐码|推薦碼",
    re.IGNORECASE)
_TUTORIAL = re.compile(
    r"\bhow to (safely )?(register|sign up|open an account|create an account)\b"
    r"|\bfull tutorial\b|\b\d+\s*-\s*minute tutorial\b|\bstep[- ]by[- ]step guide\b"
    r"|註冊教學|注册教程|開戶教學|开户教程",
    re.IGNORECASE)
_SELF_REPORTED = re.compile(r"\bself[- ]reported\b", re.IGNORECASE)

_AUTOGEN_RES = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\bfinancial contrast\b",
        r"\bhead[- ]to[- ]head (comparison|review|analysis|contrast)\b",
        r"\bcritical comparison\b",
        r"\bcontrasting\b",
        r"\bself[- ]reported market capitali[sz]ation\b",
        r"\bprice (tops|hits|reaches|falls to|drops to)\b.{0,40}\$",
        r"\bprice (down|up) [\d.]+% over last 7 days\b",
        r"\bone day (trading )?volume (hits|reaches|falls|drops)\b",
        r"\b(boosts|cuts|raises|lowers|increases|decreases|trims) "
        r"(stake|position|holdings) in\b",
        r"\b(stake|position|holdings) in .{0,60} (boosted|cut|raised|lowered|trimmed)\b",
        r"\b(purchases|sells|acquires) [\d,]+ shares\b",
        r"\bnew (stake|position) in\b",
        r"\b(up|down)grad\w*\b.{0,40}\bwall street zen\b",
        r"\bannounces quarterly earnings results\b",
        r"\bwhich is the better (etf|stock)\b",
        r"\breceives? [\w.]+ (rating|price target) from\b",
        r"\bshares (bought|sold) by\b",
        r"\bprice target (raised|lowered|increased|cut) to\b",
        r"\btrading\s+[\d\s.]+%\s*(lower|higher)\s+over\s+(the\s+)?last\s+(week|7 days|month)\b",
        r"\bshort interest (update|report|alert)\b",
        r"\b(decline|increase|growth|surge) in short interest\b",
    ]
]

_MICROCAP_USD = re.compile(r"\$\s*[\d,.]+\s*(thousand|million)\b", re.IGNORECASE)
_SUBPENNY = re.compile(r"\$\s*0\s*\.\s*0{2,}\d*")
_MICROCAP_WORDS = re.compile(
    r"\bmarket capitali[sz]ation\b|\bone day (trading )?volume\b", re.IGNORECASE)

_LLM_SPAM = re.compile(r"^\s*(noise|spam)\b|\bspam\b.{0,30}(down[- ]?weight|no signal)",
                       re.IGNORECASE)

_PENALTY_FLOOR = 0.05


def _norm_headline(h: str | None) -> str:
    """Normalized headline key for syndication detection: same wire text on
    many outlets collapses to one bucket; paraphrases stay distinct."""
    if not h:
        return ""
    h = re.sub(r"\([^)]*\)|【[^】]*】", " ", h.lower())
    h = re.sub(r"[^a-z0-9一-鿿]+", " ", h)
    return " ".join(h.split())


def _canon_host(outlet: str | None) -> str:
    if not outlet:
        return ""
    h = outlet.strip().lower().split(":")[0]
    if h.startswith("www."):
        h = h[4:]
    return h


def _outlet_weight(host: str) -> float:
    if not host:
        return DEFAULT_OUTLET_WEIGHT
    if host in SOURCE_WEIGHTS:
        return SOURCE_WEIGHTS[host]
    # suffix match: blog.udn.com covered exactly; catch subdomains of listed hosts
    for known, w in SOURCE_WEIGHTS.items():
        if host.endswith("." + known):
            return w
    return DEFAULT_OUTLET_WEIGHT


def score_cluster(cluster: dict, held: set[str] | None = None) -> dict:
    """Compute the trust overlay for one serialized cluster.

    Returns {
      trust_score: int 0-100 (raw impact reweighted),
      penalties: [{kind, factor, detail}],
      outlet_diversity: float, distinct_headlines: int,
      source_factor: float, source_outlets: [host...],
    }
    """
    held = held or set()
    raw = float(cluster.get("impact_score") or 0)
    story_count = max(1, int(cluster.get("story_count") or 1))
    outlet_count = max(1, int(cluster.get("outlet_count") or 1))
    canonical = cluster.get("canonical_headline") or ""
    members = cluster.get("members") or []
    tickers = {str(t).upper() for t in (cluster.get("tickers") or [])}
    asset_class = (cluster.get("asset_class") or "").upper()

    # ---- independent-outlet diversity ---------------------------------------
    # distinct normalized headlines = original reporting units: one AP wire
    # copy carried by 12 regional papers is 1 unit; 12 outlets writing their
    # own story is 12. outlet_count only CAPS units (a farm posting 26 variants
    # on 1 blog is still 1 unit). Breadth scales linearly to 6 independent
    # outlets, which matches the ETL impact model's coverage saturation.
    distinct_headlines = len({
        _norm_headline(m.get("headline")) for m in members
        if _norm_headline(m.get("headline"))
    }) or 1
    independent_outlets = min(outlet_count, distinct_headlines)
    breadth_factor = min(1.0, independent_outlets / 6.0)
    diversity = independent_outlets / story_count

    # ---- source reputation --------------------------------------------------
    hosts = sorted({_canon_host(m.get("outlet")) for m in members} - {""})
    best_w = max((_outlet_weight(h) for h in hosts), default=DEFAULT_OUTLET_WEIGHT)
    source_factor = 0.4 + 0.6 * best_w

    # ---- itemized penalties -------------------------------------------------
    penalties = []

    def _add(kind, factor, detail):
        penalties.append({"kind": kind, "factor": factor, "detail": detail})

    if _AFFILIATE.search(canonical) or any(
            _AFFILIATE.search(m.get("headline") or "") for m in members[:40]):
        _add("affiliate", 0.10,
             "referral/invitation-code or rebate promotion detected")

    if _TUTORIAL.search(canonical):
        _add("tutorial", 0.20, "tutorial/how-to format, not news")

    member_hosts = {_canon_host(m.get("outlet")) for m in members}
    if (member_hosts & PR_WIRE_HOSTS) or _SELF_REPORTED.search(canonical):
        _add("press_release", 0.30,
             "press-release wire or self-reported content")

    if any(r.search(canonical) for r in _AUTOGEN_RES):
        _add("auto_generated", 0.25,
             "templated auto-generated headline pattern")

    if asset_class == "CRYPTO" and not (tickers & (held | MAJOR_CRYPTO)):
        if (_MICROCAP_USD.search(canonical) or _SUBPENNY.search(canonical)
                or _MICROCAP_WORDS.search(canonical)):
            _add("microcap_crypto", 0.20,
                 "micro/sub-$1M-cap crypto, not held and not a major asset")

    rationale = (cluster.get("llm_rationale") or "")
    if _LLM_SPAM.search(rationale):
        _add("llm_flagged_spam", 0.10,
             "LLM enrichment flagged this cluster as noise/spam")

    product = 1.0
    for p in penalties:
        product *= p["factor"]
    product = max(_PENALTY_FLOOR, product)

    # Breadth reweighting: the ETL impact model's coverage+attention points
    # (0-50) are the story-volume-driven part; recency/keyword/llm are not
    # volume-driven. Reweight only the breadth part by independent-outlet
    # diversity so raw story count can never act as a multiplier. Legacy rows
    # without impact_components fall back to a 50% assumed breadth share.
    comp = cluster.get("impact_components")
    if isinstance(comp, dict):
        breadth_pts = float(comp.get("coverage") or 0) + float(comp.get("attention") or 0)
        non_breadth_pts = max(0.0, raw - breadth_pts)
    else:
        breadth_pts = raw * 0.5
        non_breadth_pts = raw - breadth_pts
    reweighted = non_breadth_pts + breadth_pts * breadth_factor

    trust_score = int(round(reweighted * source_factor * product))

    return {
        "trust_score": max(0, min(100, trust_score)),
        "penalties": penalties,
        "outlet_diversity": round(diversity, 3),
        "independent_outlets": independent_outlets,
        "breadth_factor": round(breadth_factor, 3),
        "distinct_headlines": distinct_headlines,
        "source_factor": round(source_factor, 3),
        "source_outlets": hosts,
    }


def apply_trust(clusters: list[dict], held: set[str] | None = None) -> list[dict]:
    """Attach c['trust'] to every cluster. Does not reorder or mutate
    impact_score — callers sort by trust.trust_score when rank=trust."""
    for c in clusters:
        c["trust"] = score_cluster(c, held=held)
    return clusters
