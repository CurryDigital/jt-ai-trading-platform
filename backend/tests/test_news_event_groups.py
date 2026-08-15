"""Unit tests for serve-time macro-event grouping (kanban t_9f70a327).

Pure-logic tests — no DB. Scenarios replay the production evidence from
t_2113ec95: the July-CPI event produced 3 angle-distinct clusters that no
cosine threshold can merge, while cross-event pairs (Hormuz, gold) share
macro vocabulary and must NOT group.
"""
from datetime import date

from app.core_logic.news_event_groups import (
    event_anchor_keys,
    group_clusters_by_events,
    tokenize,
)

CPI_EVENT = {"event": "US CPI (Jul 2026)", "date": date(2026, 8, 12),
             "region": "US"}


def _c(cid, headline, impact, ac="US"):
    return {
        "cluster_id": cid,
        "canonical_headline": headline,
        "impact_score": impact,
        "impact_components": {"attention": impact},  # opaque pass-through
        "story_count": 10,
        "outlet_count": 5,
        "first_seen_utc": "2026-08-12T13:00:00",
        "last_seen_utc": "2026-08-13T01:00:00",
        "asset_class": ac,
        "lang": "en",
    }


# The exact production rows cited in t_9f70a327.
CPI_ASIA = _c(1, "Asian stocks rise as US inflation data dents September Fed "
                 "hike bets", 85)
CPI_US = _c(3, "Wall St gains as AI earnings lift tech, inflation data "
               "supports rate-hold bets", 84)
CPI_PRE = _c(6, "Treasury yields are little changed as investors await key "
                "inflation data", 78)
HORMUZ = _c(2, "Hormuz Deadlock: Where oil prices could head next as "
               "prospects for an imminent deal fade", 85)
GOLD = _c(4, "Gold rises near $4,400 as Hormuz doubts, CPI keep Fed path in "
             "focus", 83, ac="METAL")


def test_tokenize_basic():
    toks = tokenize("Wall St gains as AI earnings lift tech")
    assert "wall" in toks and "gains" in toks and "earnings" in toks
    assert "st" not in toks and "ai" not in toks and "as" not in toks


def test_event_anchor_keys():
    assert event_anchor_keys("US CPI (Jul 2026)") == ["cpi"]
    assert event_anchor_keys("FOMC Rate Decision") == ["fomc"]
    assert event_anchor_keys("US Payrolls (May 2026)") == ["payrolls"]
    assert event_anchor_keys("PBoC LPR Fixing") == ["pboc"]
    assert event_anchor_keys("RBA Cash Rate Decision") == ["rba"]
    assert event_anchor_keys("Some random summit") == []


def test_cpi_angles_collapse_to_one_row():
    out, stats = group_clusters_by_events(
        [CPI_ASIA, HORMUZ, CPI_US, GOLD, CPI_PRE], [CPI_EVENT])
    ids = [c["cluster_id"] for c in out]
    # One CPI row (the highest-impact angle) + Hormuz + gold survive.
    assert sorted(ids) == [1, 2, 4]
    assert stats["groups"] == 1 and stats["collapsed"] == 2
    seed = next(c for c in out if c["cluster_id"] == 1)
    eg = seed["event_group"]
    assert eg["event"] == "US CPI (Jul 2026)"
    assert eg["event_date"] == "2026-08-12"
    assert eg["anchor"] == "cpi"
    assert eg["related_count"] == 2
    assert {r["cluster_id"] for r in eg["related"]} == {3, 6}
    # Drill-down data preserved in-payload.
    assert all(r["canonical_headline"] for r in eg["related"])


def test_impact_fields_never_mutated():
    out, _ = group_clusters_by_events([CPI_ASIA, CPI_US, CPI_PRE],
                                      [CPI_EVENT])
    seed = next(c for c in out if c["cluster_id"] == 1)
    assert seed["impact_score"] == 85
    assert seed["impact_components"] == {"attention": 85}
    assert seed["story_count"] == 10


def test_hormuz_mentioning_cpi_does_not_join():
    # A US-scope Hormuz row that name-drops CPI shares ONLY anchor
    # vocabulary with the seed -> must not group (the failure mode that
    # killed the relaxed-DF merge pass in t_2113ec95).
    hormuz_cpi = _c(9, "Oil climbs as Hormuz tensions keep CPI and Fed in "
                       "focus", 80)
    out, stats = group_clusters_by_events(
        [CPI_ASIA, CPI_US, hormuz_cpi], [CPI_EVENT])
    ids = sorted(c["cluster_id"] for c in out)
    assert ids == [1, 9]
    assert stats["groups"] == 1 and stats["collapsed"] == 1


def test_region_asset_gating():
    # The gold row mentions CPI but sits in METAL scope; a US event only
    # groups US rows.
    out, stats = group_clusters_by_events([CPI_ASIA, GOLD], [CPI_EVENT])
    assert len(out) == 2 and stats["groups"] == 0


def test_no_event_no_grouping():
    out, stats = group_clusters_by_events([CPI_ASIA, CPI_US], [])
    assert len(out) == 2 and stats["groups"] == 0
    assert "event_group" not in out[0]


def test_single_candidate_no_group():
    out, stats = group_clusters_by_events([CPI_ASIA, HORMUZ], [CPI_EVENT])
    assert len(out) == 2 and stats["groups"] == 0


def test_no_corroborator_no_group():
    # Two CPI-anchor rows sharing nothing but anchor tokens stay separate.
    a = _c(1, "CPI surprises markets", 80)
    b = _c(2, "Inflation prints hot", 70)
    out, stats = group_clusters_by_events([a, b], [CPI_EVENT])
    assert len(out) == 2 and stats["groups"] == 0


def test_hk_event_groups_hk_rows_not_us():
    hk_cpi = {"event": "HK CPI (Jul 2026)", "date": date(2026, 8, 20),
              "region": "HK"}
    hk1 = _c(1, "Hong Kong inflation accelerates as rents climb", 70,
             ac="HK")
    hk2 = _c(2, "Hong Kong CPI data lifts property shares", 60, ac="HK")
    out, stats = group_clusters_by_events([hk1, hk2, CPI_US], [hk_cpi])
    ids = sorted(c["cluster_id"] for c in out)
    assert ids == [1, 3]  # US row untouched, HK rows grouped
    assert stats["groups"] == 1


def test_order_preserved_and_seed_annotated_inplace():
    out, _ = group_clusters_by_events([CPI_US, CPI_ASIA, CPI_PRE],
                                      [CPI_EVENT])
    assert [c["cluster_id"] for c in out] == [1]  # highest impact wins
    assert out[0]["event_group"]["related_count"] == 2


def test_inputs_never_mutated():
    # Pure-function contract: caller's row dicts must not gain annotations
    # (shared module-level fixtures would otherwise leak event_group across
    # tests; cached payloads would leak across requests).
    rows = [_c(1, CPI_ASIA["canonical_headline"], 85),
            _c(3, CPI_US["canonical_headline"], 84),
            _c(6, CPI_PRE["canonical_headline"], 78)]
    out, _ = group_clusters_by_events(rows, [CPI_EVENT])
    assert all("event_group" not in r for r in rows)
    seed = next(c for c in out if c["cluster_id"] == 1)
    assert seed["event_group"]["related_count"] == 2
