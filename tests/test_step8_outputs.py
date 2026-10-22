"""Key Step 8 outputs that the README, decision page, brief and portfolio copy quote."""

from __future__ import annotations

import pandas as pd
import pytest

from conftest import SERIES, read

DIR = "05_outputs/peak_season_diagnosis/"


@pytest.fixture(scope="module")
def m() -> pd.Series:
    return read(DIR + "DemandIQ_Step8_Headline_Metrics.csv").set_index("metric").value


def num(m: pd.Series, key: str) -> float:
    return float(m[key])


@pytest.mark.parametrize("key, expected, places", [
    ("Dec-Feb fill, PY2022", 85.9, 1),
    ("Dec-Feb fill, PY2026", 78.1, 1),
    ("Dec-Feb fill on reconstructed demand, PY2026", 82.6, 1),
    ("Buy basis vs prior-year reconstructed demand, PY2026", -9.0, 1),
    ("Timing share of PY2026 lost units", 59, 0),
    ("Share of PY2026 lost units in Dec-Feb", 83, 0),
    ("Reconstruction uplift, Dec-Feb PY2026", 21, 0),
    ("Top 20 cells by true lost revenue, share of PY2026 lost revenue", 60.2, 1),
    ("Top 20 cells by stockout days (observable selection), share of true lost revenue", 53.4, 1),
    ("Rank correlation: lost revenue vs stockout days", 0.90, 2),
    ("Indicative next-peak change", 10339, 0),
    ("Chase-only floor at the plan date (orders due by 2026-09-21 or 2026-10-05)", 4355, 0),
    ("Calls unchanged when recomputed with true demand", 9, 0),
])
def test_headline(m, key, expected, places):
    assert round(num(m, key), places) == pytest.approx(expected)


def test_change_splits_into_moved_new_and_accepted(m):
    parts = ["  of which moved forward from spring replenishment", "  of which new units",
             "  of which accepted gap (guardrail blocks new units)"]
    keys = [k for k in m.index if k.strip() in {p.strip() for p in parts}]
    assert len(keys) == 3
    assert sum(num(m, k) for k in keys) == num(m, "Indicative next-peak change")
    assert [round(num(m, k)) for k in keys] == [4574, 5613, 152]


def test_recommendation_tables_add_up(m):
    rec = read(DIR + "DemandIQ_Step8_Peak_Buy_Recommendation.csv")
    region = read(DIR + "DemandIQ_Step8_Peak_Buy_by_Region.csv")
    for column in ["moved_units", "new_units"]:
        assert rec[column].sum() == pytest.approx(region[column].sum())
    assert (rec.moved_units + rec.new_units).sum() == pytest.approx(10339 - 152)
    assert rec.call.value_counts().to_dict() == {"Buy and re-time": 8, "Re-time only": 1}


def test_queue_on_the_published_plan(m):
    queue = read(DIR + "DemandIQ_Step8_Corrected_SOE_Queue.csv")
    assert queue.corrected_action.value_counts().to_dict() == {"PROTECT": 5, "NO ACTION": 3, "WATCH": 1}
    assert (queue.published_tier.str.startswith("P1")).sum() == 3
    assert num(m, "Corrected queue: ESCALATE") == 0 and num(m, "Corrected queue: WATCH") == 1


def test_every_output_states_its_evidence_basis():
    for name in ["Fill_Trend", "Buy_Basis", "Peak_Buy_Recommendation", "Peak_Buy_Validation",
                 "Corrected_SOE_Queue", "Headline_Metrics"]:
        frame = read(DIR + f"DemandIQ_Step8_{name}.csv")
        assert "basis" in frame.columns and frame.basis.notna().all(), name


def test_recommendation_uses_planner_view_only():
    rec = read(DIR + "DemandIQ_Step8_Peak_Buy_Recommendation.csv")
    assert set(rec.basis) == {"PLANNER_VIEW"}
    assert not any("true" in c or "lost_demand" in c for c in rec.columns)
