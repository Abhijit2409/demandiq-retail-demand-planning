"""The two-page brief: built from the CSVs, and its numbers agree with them."""

from __future__ import annotations

import importlib.util
import sys

import pandas as pd
import pytest

from conftest import ROOT, read

DIR = "05_outputs/peak_season_diagnosis/"


@pytest.fixture(scope="module")
def brief():
    path = ROOT / "04_scripts/step8/step8c_build_brief.py"
    spec = importlib.util.spec_from_file_location("step8c_build_brief", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_committed_pdf_passes_verification(brief):
    """Two pages, readable text, every number derived from a CSV or declared policy."""
    assert brief.verify() == []


def test_every_fact_names_an_existing_source(brief):
    sources = {"Step 8 headline metrics", "Step 8 peak-buy recommendation", "Step 8 move feasibility",
               "Step 8 validation", "Step 8 corrected queue", "Step 8 loss concentration",
               "Step 8B summary", "Step 7E initial buy", "Step 7F policy sensitivity"}
    assert {fact.source for fact in brief.facts().values()} <= sources
    assert all(path.exists() for path in brief.SOURCES.values())


def test_key_facts_match_an_independent_reading_of_the_csvs(brief):
    """Recompute the brief's headline figures straight from the CSVs."""
    f = {k: v.text for k, v in brief.facts().items()}
    rec = read(DIR + "DemandIQ_Step8_Peak_Buy_Recommendation.csv")
    feas = read(DIR + "DemandIQ_Step8_Peak_Move_Feasibility.csv", parse_dates=["latest_order_overseas_lane"])
    head = read(DIR + "DemandIQ_Step8_Headline_Metrics.csv").set_index("metric").value
    s8b = read(DIR + "DemandIQ_Step8B_Summary_Metrics.csv").set_index("metric").value

    assert f["change"] == f"{rec.change_units.sum():,.0f}" == "10,339"
    assert (f["moved"], f["new"], f["accepted_gap"]) == ("4,574", "5,613", "152")
    assert f["change_vs_sales"] == "+22%"  # 10,339 / 46,470 Dec-Feb units sold
    assert f["uplift"] == "21%"            # reconstructed vs sold, Dec-Feb
    assert (f["order_first"], f["order_last"]) == (
        f"{feas.latest_order_overseas_lane.min():%b %-d}", f"{feas.latest_order_overseas_lane.max():%b %-d}")
    assert f["top20_observable"] == f"{float(head['Top 20 cells by stockout days (observable selection), share of true lost revenue']):.1f}%" == "53.4%"
    assert f["top20_truth"] == "60.2%"
    assert (f["step5_escalate"], f["step5_protect"], f["step5_hold"], f["watch"]) == ("0", "7", "2", "1")
    est = "Estimated replenishment in the 13-week projection (unconfirmed, not open orders)"
    assert f["est_replen"] == f"{float(s8b[est]):,.0f}" == "6,512"
    assert (f["v1_escalations"], f["replen_week_error"], f["replen_stress"], f["replen_needed"]) == (
        "3", "57–71%", "29.5%", "30%")
    assert f["window_share"] == "1.1%"


def test_series_table_matches_the_recommendation(brief):
    rows = brief.series_rows()
    rec = read(DIR + "DemandIQ_Step8_Peak_Buy_Recommendation.csv").sort_values("priority_rank")
    assert len(rows) == len(rec) == 9
    assert sum(int(r[2].replace(",", "")) for r in rows) == int(rec.change_units.sum())
    assert [r[5] for r in rows] == list(rec.call)
