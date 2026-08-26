"""Regression tests for the news trust overlay (app/services/news_trust.py).

Cases are drawn from the live 2026-08-17 feed: the exact clusters that gamed
the impact ranking, plus legitimate multi-outlet events that must NOT sink.
Run on every change to the scoring model.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.news_trust import score_cluster, apply_trust, _norm_headline


def _cluster(headline, stories, outlets, member_outlets=None, asset="US",
             tickers=None, llm_rationale=None, impact=70, member_headlines=None):
    outs = member_outlets or ["reuters.com"] * outlets
    heads = member_headlines or [headline] * stories
    members = [
        {"outlet": outs[i % len(outs)], "headline": heads[i % len(heads)],
         "url": f"https://{outs[i % len(outs)]}/a{i}", "lang": "en",
         "published_at": "2026-08-16T10:00:00"}
        for i in range(stories)
    ]
    return {
        "cluster_id": "x", "canonical_headline": headline,
        "story_count": stories, "outlet_count": outlets,
        "asset_class": asset, "tickers": tickers or [],
        "llm_direction": None, "llm_confidence": None,
        "llm_rationale": llm_rationale, "impact_score": impact,
        "members": members,
    }


# --- the live offenders (must sink) -----------------------------------------

OKX_FARM = _cluster(
    "How to Safely Register an OKX Account _ 2026 Latest Hong Kong User "
    "Exclusive 20 % Rebate Full Tutorial 【34978585】",
    stories=26, outlets=1, member_outlets=["blog.udn.com"], asset="CRYPTO",
    llm_rationale="NOISE/SPAM: exchange referral-code promotional blog spam. "
                  "Down-weighted.", impact=78,
    member_headlines=[
        "How to Safely Register on Bitget _ Referral Code 【BG3388】",
        "2026 Latest Binance Mobile Registration Full Tutorial 【BTC45】",
        "OKX Register Guide Invitation Code Rebate",
    ] * 9)

JXG_CONTRAST = _cluster(
    "JX Luxventure Group ( NASDAQ : JXG ) and LKQ ( NASDAQ : LKQ ) Financial Contrast",
    stories=11, outlets=3,
    member_outlets=["americanbankingnews.com", "defenseworld.net",
                    "tickerreport.com"], impact=71)

EVMOS_MICROCAP = _cluster(
    "Evmos Self Reported Market Capitalization Reaches $259 . 18 Thousand ( EVMOS )",
    stories=31, outlets=3, asset="CRYPTO", tickers=["EVMOS"],
    member_outlets=["americanbankingnews.com", "theolympiareport.com",
                    "modernreaders.com"], impact=69)

COQ_INU = _cluster(
    "Coq Inu Price Tops $0 . 0000 on Top Exchanges ( COQ )",
    stories=12, outlets=3, asset="CRYPTO",
    member_outlets=["americanbankingnews.com", "wkrb13.com",
                    "thecerbatgem.com"], impact=62)

RADICLE_FARM = _cluster(
    "Radicle Price Hits $0 . 23 on Major Exchanges ( RAD )",
    stories=8, outlets=1, asset="CRYPTO",
    member_outlets=["americanbankingnews.com"], impact=60)

STAKE_BOT = _cluster(
    "Fifth Third Bancorp Boosts Stake in Vanguard S & P 500 Growth ETF $VOOG",
    stories=6, outlets=4,
    member_outlets=["marketbeat.com", "defenseworld.net"], impact=71)

WALLSTREETZEN_BOT = _cluster(
    "Deep Fission ( NASDAQ : FISN ) Upgraded by Wall Street Zen to Hold Rating",
    stories=5, outlets=1, member_outlets=["marketbeat.com"], impact=44)

# --- legitimate coverage (must survive) -------------------------------------

WEEK_AHEAD = _cluster(
    "Wall Street week ahead : Home Depot and Walmart report earnings , minutes of Fed meeting",
    stories=12, outlets=12,
    member_outlets=["reuters.com", "cnbc.com", "bloomberg.com", "ft.com",
                    "wsj.com", "marketwatch.com", "finance.yahoo.com",
                    "investing.com", "barrons.com", "apnews.com", "bbc.com",
                    "nytimes.com"],
    member_headlines=[
        "Wall Street week ahead: Home Depot and Walmart report earnings",
        "The economic week ahead: jobs data and Fed minutes",
        "What to watch in markets this week: retail earnings, FOMC minutes",
        "Week ahead: Walmart, Home Depot results and Fed minutes in focus",
        "Investors eye retail earnings and Fed minutes this week",
        "Markets week ahead: earnings from big retailers, Fed minutes",
        "Fed minutes and retail earnings headline holiday-shortened week",
        "US week ahead: Fed minutes, Walmart and Home Depot earnings",
        "The week ahead in markets: retail earnings and Fed minutes",
        "Retailers report as Fed minutes loom: week ahead",
        "Wall Street looks to Walmart earnings and Fed minutes",
        "Week ahead preview: retail earnings, Fed minutes"],
    impact=69)

SP_RECORD = _cluster(
    "S & P 500 notches record high , Nasdaq rallies after soft inflation data",
    stories=9, outlets=8,
    member_outlets=["reuters.com", "cnbc.com", "apnews.com", "bloomberg.com",
                    "marketwatch.com", "finance.yahoo.com", "investing.com",
                    "ft.com"],
    member_headlines=[
        "S&P 500 notches record high, Nasdaq rallies after soft inflation data",
        "Stocks rally to records as inflation cools",
        "Wall Street hits record highs on soft inflation reading",
        "Nasdaq surges, S&P 500 at record after tame inflation data",
        "US stocks climb to fresh records on inflation relief",
        "Record close for S&P 500 as inflation data calms markets",
        "S&P 500 ends at record high after inflation report",
        "Stocks jump after cool inflation data lifts rate-cut hopes",
        "Markets rally: S&P 500 record on soft inflation print"],
    impact=44)

SYNDICATED_WIRE = _cluster(
    "US payrolls rise 120k in July, unemployment steady at 4.1%",
    stories=12, outlets=12,
    member_outlets=["marketbeat.com", "defenseworld.net", "tickerreport.com",
                    "markets.financialcontent.com", "theolympiareport.com",
                    "modernreaders.com", "wkrb13.com", "thecerbatgem.com",
                    "dailypolitical.com", "rivertonroll.com", "slugline.co",
                    "beatdaily.com"],
    member_headlines=[
        "US payrolls rise 120k in July, unemployment steady at 4.1%"] * 12,
    impact=55)


def test_okx_content_farm_sinks():
    t = score_cluster(OKX_FARM)
    kinds = {p["kind"] for p in t["penalties"]}
    assert {"affiliate", "tutorial", "llm_flagged_spam"} <= kinds
    assert t["trust_score"] <= 2, t


def test_financial_contrast_template_sinks():
    t = score_cluster(JXG_CONTRAST)
    assert any(p["kind"] == "auto_generated" for p in t["penalties"])
    assert t["trust_score"] <= 8, t


def test_microcap_self_reported_sinks():
    t = score_cluster(EVMOS_MICROCAP)
    kinds = {p["kind"] for p in t["penalties"]}
    assert {"microcap_crypto", "press_release", "auto_generated"} <= kinds
    assert t["trust_score"] <= 3, t


def test_subpenny_memecoin_sinks():
    t = score_cluster(COQ_INU)
    assert any(p["kind"] == "microcap_crypto" for p in t["penalties"])
    assert t["trust_score"] <= 4, t


def test_single_outlet_farm_sinks():
    t = score_cluster(RADICLE_FARM)
    assert t["outlet_diversity"] <= 0.2
    assert t["trust_score"] <= 8, t


def test_13f_stake_bot_penalized():
    t = score_cluster(STAKE_BOT)
    assert any(p["kind"] == "auto_generated" for p in t["penalties"])
    assert t["trust_score"] < STAKE_BOT["impact_score"] * 0.3


def test_wallstreetzen_template_penalized():
    t = score_cluster(WALLSTREETZEN_BOT)
    assert any(p["kind"] == "auto_generated" for p in t["penalties"])


def test_legit_diverse_event_survives():
    t = score_cluster(WEEK_AHEAD)
    assert t["penalties"] == []
    assert t["outlet_diversity"] >= 0.9
    assert t["trust_score"] >= 55, t


def test_legit_record_high_survives():
    t = score_cluster(SP_RECORD)
    assert t["penalties"] == []
    assert t["trust_score"] >= 35, t


def test_syndicated_wire_below_diverse_coverage():
    """Same wire text on 12 junk outlets < 12 outlets with own coverage."""
    t_wire = score_cluster(SYNDICATED_WIRE)
    t_legit = score_cluster(WEEK_AHEAD)
    assert t_wire["distinct_headlines"] == 1
    assert t_wire["trust_score"] < t_legit["trust_score"] * 0.4


def test_trading_lower_template_penalized():
    c = _cluster("TokenFi ( TOKEN ) Trading 9 . 6 % Lower Over Last Week",
                 stories=2, outlets=2, asset="CRYPTO",
                 member_outlets=["americanbankingnews.com", "wkrb13.com"])
    assert any(p["kind"] == "auto_generated" for p in score_cluster(c)["penalties"])


def test_upgraded_at_wallstreetzen_penalized():
    c = _cluster("Virtuix ( NASDAQ : VTIX ) Upgraded to Sell at Wall Street Zen",
                 stories=2, outlets=2, member_outlets=["marketbeat.com"])
    assert any(p["kind"] == "auto_generated" for p in score_cluster(c)["penalties"])


def test_short_interest_template_penalized():
    c = _cluster("WisdomTree Bitcoin Fund ( BATS : BTCW ) Short Interest Update",
                 stories=2, outlets=2, member_outlets=["americanbankingnews.com"])
    assert any(p["kind"] == "auto_generated" for p in score_cluster(c)["penalties"])


def test_microcap_exempt_when_held():
    t = score_cluster(EVMOS_MICROCAP, held={"EVMOS"})
    assert not any(p["kind"] == "microcap_crypto" for p in t["penalties"])


def test_microcap_exempt_for_majors():
    c = _cluster("Bitcoin Self Reported Market Capitalization Reaches $2 . 1 Trillion",
                 stories=5, outlets=3, asset="CRYPTO", tickers=["BTC-USD"])
    t = score_cluster(c)
    assert not any(p["kind"] == "microcap_crypto" for p in t["penalties"])


def test_apply_trust_never_mutates_raw_impact():
    rows = [dict(OKX_FARM), dict(WEEK_AHEAD)]
    apply_trust(rows)
    assert rows[0]["impact_score"] == 78
    assert "trust" in rows[0] and "trust" in rows[1]


def test_norm_headline_wire_dedup():
    a = _norm_headline("US payrolls rise 120k in July (UPDATE 2)")
    b = _norm_headline("US payrolls rise 120k in July")
    assert a == b


def test_chinese_affiliate_detected():
    c = _cluster("幣安註冊教學：最新邀請碼【BTC45】享20%返佣", stories=10, outlets=1,
                 member_outlets=["blog.udn.com"], asset="CRYPTO")
    t = score_cluster(c)
    kinds = {p["kind"] for p in t["penalties"]}
    assert {"affiliate", "tutorial"} & kinds, t
