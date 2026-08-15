"""Serve-time macro-event grouping for the news cluster feed (kanban t_9f70a327).

Why this exists: on macro event days (CPI, FOMC, payrolls ...) the same event
produces 2-3 angle-distinct clusters (pre-event positioning, Asia-session
reaction, US-session reaction) that the embedding cluster layer provably
cannot merge (same-event centroid cosine 0.392 < cross-event pairs 0.459-0.657
— see t_2113ec95 for the measurements). The feed goal is "top N rows = N
distinct events", so the grouping happens here, at serve time, anchored on the
macro calendar instead of embedding similarity.

Pure functions only — no DB, no FastAPI — so the logic is unit-testable and
reusable from any route.

Design (candidate (c) from t_2113ec95):
  * Events come from the macro calendar (consumption.macro_calendar at the
    call site) and are mapped to anchor-token sets mirroring the ETL-side
    _ANCHOR_MAP in agents/etl/consumption/market/build_news_clusters.py.
  * A cluster joins an event group iff its canonical headline contains >=1 of
    the event's anchor tokens AND shares >=1 corroborating token with the
    group seed (highest-impact candidate). Corroborating tokens exclude ALL
    macro anchor vocabulary ('fed', 'cpi', 'inflation', ...) — otherwise every
    Hormuz/geopolitics headline that name-drops 'CPI' or 'Fed' would chain
    into the group (the failure mode that killed the relaxed-DF merge pass).
  * Grouping is per (anchor key, asset class) and events are gated by region
    -> asset class (a US CPI event never collapses METAL gold rows).
  * Anti-chaining: candidates are tested against the SEED row only, never
    against the growing group union.
  * Nothing is mutated: the kept row passes through verbatim (impact_score /
    impact_components untouched) and gains one additive 'event_group'
    annotation; collapsed rows are returned in the annotation's 'related'
    list so drill-down data is preserved in-payload.
"""
import re
from datetime import date, datetime

# Mirror of ETL _ANCHOR_MAP (build_news_clusters.py). Keep token sets in sync
# with the build side; the serve side must not invent anchors the build does
# not know about.
ANCHOR_MAP = {
    "cpi": {"cpi", "inflation"},
    "fomc": {"fomc", "fed"},
    "payrolls": {"payrolls", "jobs", "nfp"},
    "rba": {"rba"},
    "boj": {"boj"},
    "ecb": {"ecb"},
    "pboc": {"pboc", "lpr"},
    "gdp": {"gdp"},
    "ppi": {"ppi"},
    "pce": {"pce"},
}

# Event-name -> anchor key, matched against the calendar event label
# ('US CPI (Jul 2026)', 'FOMC Rate Decision', 'US Payrolls (May 2026)', ...).
_EVENT_NAME_PATTERNS = [
    ("cpi", re.compile(r"\bcpi\b", re.I)),
    ("fomc", re.compile(r"\bfomc\b", re.I)),
    ("payrolls", re.compile(r"payrolls?|\bnfp\b|non-?farm", re.I)),
    ("rba", re.compile(r"\brba\b", re.I)),
    ("boj", re.compile(r"\bboj\b", re.I)),
    ("ecb", re.compile(r"\becb\b", re.I)),
    ("pboc", re.compile(r"pboc|\blpr\b", re.I)),
    ("gdp", re.compile(r"\bgdp\b", re.I)),
    ("ppi", re.compile(r"\bppi\b", re.I)),
    ("pce", re.compile(r"\bpce\b", re.I)),
]

# Region -> asset classes an event may group. Conservative on purpose: a US
# rate event groups US-equity clusters only; AU/JP/EZ/UK rate decisions land
# in the FX scope; HK/CN events land in HK. Unknown regions are skipped
# rather than applied feed-wide.
REGION_TO_ASSETS = {
    "US": {"US"},
    "HK": {"HK"},
    "CN": {"HK"},
    "AU": {"FX"},
    "JP": {"FX"},
    "EA": {"FX"},
    "EZ": {"FX"},
    "EU": {"FX"},
    "UK": {"FX"},
}

# Union of every anchor token — excluded from corroboration so that generic
# macro vocabulary ('fed', 'inflation', 'data'-like anchors) cannot be the
# token that pulls an unrelated headline into an event group.
GLOBAL_ANCHOR_TOKENS = set().union(*ANCHOR_MAP.values())

_STOPWORDS = {
    "the", "and", "for", "with", "from", "says", "said", "after", "over",
    "amid", "ahead", "are", "was", "were", "has", "have", "had", "will",
    "would", "could", "should", "about", "into", "near", "this", "that",
    "these", "those", "than", "then", "them", "they", "their", "its", "his",
    "her", "not", "but", "all", "can", "may", "new", "now", "out", "off",
    "per", "via", "who", "why", "how", "what", "when", "where", "which",
    "while", "you", "your", "our", "more", "most", "some", "such", "also",
    "just", "still", "here", "there", "been", "being", "between", "against",
    "under", "above", "before", "during", "week", "month", "year", "day",
    "today", "says", "update", "live", "watch", "analysis", "report",
    "reports", "latest", "breaking",
}

_TOKEN_RE = re.compile(r"[a-z]+")


def tokenize(text):
    """Lowercase alpha tokens, len>=3, stopworded. Numbers and 1-2 letter
    tokens ('us', 'st', 'ai') are dropped — they carry no corroborating
    signal."""
    if not text:
        return set()
    return {t for t in _TOKEN_RE.findall(text.lower())
            if len(t) >= 3 and t not in _STOPWORDS}


def event_anchor_keys(event_name):
    """Anchor keys for a calendar event label, e.g. 'US CPI (Jul 2026)' ->
    ['cpi']; 'PBoC LPR Fixing' -> ['pboc']."""
    name = event_name or ""
    return [key for key, pat in _EVENT_NAME_PATTERNS if pat.search(name)]


def _iso(d):
    if d is None:
        return None
    if isinstance(d, (date, datetime)):
        return d.isoformat()
    return str(d)


def _related_slim(c):
    return {
        "cluster_id": c.get("cluster_id"),
        "canonical_headline": c.get("canonical_headline"),
        "impact_score": c.get("impact_score"),
        "story_count": c.get("story_count"),
        "outlet_count": c.get("outlet_count"),
        "first_seen_utc": c.get("first_seen_utc"),
        "last_seen_utc": c.get("last_seen_utc"),
        "asset_class": c.get("asset_class"),
        "lang": c.get("lang"),
    }


def group_clusters_by_events(clusters, events):
    """Group angle-split clusters of the same macro event into one feed row.

    Args:
        clusters: serialized cluster dicts (impact-sorted desc preferred;
                  the seed of a group is its highest-impact member regardless).
        events:   calendar event dicts with keys 'event', 'date' (date or ISO
                  str), 'region'. Callers must pre-filter to the served window.

    Returns:
        (out_clusters, stats) — out_clusters preserves input order minus
        collapsed rows; kept group seeds gain an additive 'event_group'
        annotation. stats = {'active_events': [...], 'groups': int,
        'collapsed': int}.
    """
    clusters = list(clusters or [])

    # Active anchors: (anchor_key, event dict), most recent event first so the
    # freshest release seeds before older same-anchor events.
    def _ev_key(e):
        d = e.get("date")
        if isinstance(d, datetime):
            return d.date().isoformat()
        if isinstance(d, date):
            return d.isoformat()
        return str(d or "")

    active = []
    seen_anchor = set()
    for ev in sorted(events or [], key=_ev_key, reverse=True):
        for key in event_anchor_keys(ev.get("event")):
            if key in seen_anchor:
                continue  # one event per anchor key (nearest/recent wins)
            seen_anchor.add(key)
            active.append((key, ev))

    if not active or not clusters:
        return clusters, {"active_events": [], "groups": 0, "collapsed": 0}

    # Pre-tokenize canonical headlines once.
    tokens = [tokenize(c.get("canonical_headline")) for c in clusters]
    consumed = set()   # indexes already grouped (as seed or collapsed member)
    groups = 0
    collapsed = 0

    for key, ev in active:
        anchor = ANCHOR_MAP[key]
        assets = REGION_TO_ASSETS.get((ev.get("region") or "").upper())
        if not assets:
            continue
        for ac in sorted(assets):
            cand_idx = [i for i, c in enumerate(clusters)
                        if i not in consumed
                        and (c.get("asset_class") or "").upper() == ac
                        and tokens[i] & anchor]
            if len(cand_idx) < 2:
                continue
            # Seed = highest-impact candidate (stable: fall back to input order).
            seed_i = max(cand_idx,
                         key=lambda i: ((clusters[i].get("impact_score") or 0),
                                        -i))
            seed_corr = tokens[seed_i] - GLOBAL_ANCHOR_TOKENS
            members = [seed_i]
            for i in cand_idx:
                if i == seed_i:
                    continue
                corr = tokens[i] - GLOBAL_ANCHOR_TOKENS
                if corr & seed_corr:
                    members.append(i)
            if len(members) < 2:
                continue
            # Copy before annotating: the helper is pure — caller's row
            # dicts are never mutated in place (test isolation, cache
            # safety if a caller reuses serialized rows across requests).
            seed = dict(clusters[seed_i])
            clusters[seed_i] = seed
            related = [clusters[i] for i in members if i != seed_i]
            related.sort(key=lambda c: -(c.get("impact_score") or 0))
            seed["event_group"] = {
                "event": ev.get("event"),
                "event_date": _iso(ev.get("date")),
                "region": ev.get("region"),
                "anchor": key,
                "related_count": len(related),
                "related": [_related_slim(c) for c in related],
            }
            consumed.update(members)
            groups += 1
            collapsed += len(related)

    out = [c for i, c in enumerate(clusters)
           if i not in consumed or "event_group" in c]
    stats = {
        "active_events": [ev.get("event") for _, ev in active],
        "groups": groups,
        "collapsed": collapsed,
    }
    return out, stats
