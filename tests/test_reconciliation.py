"""Step 8B: Step 5's conditional calls against Step 8's queue, and the replenishment sensitivity."""

from __future__ import annotations

import pandas as pd
import pytest

from conftest import SERIES, read

REC = "05_outputs/peak_season_diagnosis/DemandIQ_Step8B_Step5_Reconciliation.csv"


@pytest.fixture(scope="module")
def rec() -> pd.DataFrame:
    return read(REC).set_index(SERIES)


def test_step8_queue_is_unchanged(rec):
    assert rec.step8_call.value_counts().to_dict() == {"PROTECT": 5, "NO ACTION": 3, "WATCH": 1}


def test_seven_of_nine_calls_agree(rec):
    assert int(rec.calls_agree.sum()) == 7


def test_each_difference_has_its_known_cause(rec):
    differ = rec[~rec.calls_agree]
    assert set(differ.index) == {("APS-001", "WHOLESALE"), ("IMH-001", "RETAIL")}
    aps = rec.loc[("APS-001", "WHOLESALE")]
    assert (aps.step8_call, aps.step5_call) == ("WATCH", "PROTECT")
    assert "forecast error band" in aps.explanation
    imh = rec.loc[("IMH-001", "RETAIL")]
    assert (imh.step8_call, imh.step5_risk_type) == ("NO ACTION", "SEVERE_SCENARIO_RISK")
    assert imh.step5_severe_cover_weeks < 2.5 <= imh.step5_base_cover_weeks
    assert rec.explanation.str.len().gt(0).all()


def test_cover_differences_are_small(rec):
    assert rec.cover_difference_weeks.abs().max() < 0.02


def test_no_series_escalates_under_the_tested_stresses(rec):
    stress = rec[["step5_tier_replenishment_low", "step5_tier_replenishment_high",
                  "step5_tier_replenishment_latest_arrival", "step5_tier_replenishment_all_in_week_13"]]
    assert not stress.eq("P1").any().any()


def test_escalation_thresholds_and_the_uniform_stress(rec):
    """The 29.5% cut and the 30.04% threshold are different measures: the cut leaves 70.5% arriving."""
    was_p1 = rec[rec.v1_published_tier == "P1"]
    assert len(was_p1) == 3
    needed = was_p1.share_of_estimate_needed_to_avoid_escalation_pct
    assert needed.round(2).to_dict() == {("APS-001", "WHOLESALE"): 30.04, ("CTS-001", "RETAIL"): 10.12,
                                         ("IMH-001", "WHOLESALE"): 6.49}
    assert rec.replenishment_stress_pct.iloc[0] == pytest.approx(29.5)
    assert needed.max() < 100 - rec.replenishment_stress_pct.iloc[0]
    assert (rec.replenishment_confirmation_status == "UNCONFIRMED_ESTIMATE").all()


def test_series_backtest_is_wider_than_the_uniform_stress(rec):
    series = read("05_outputs/peak_season_diagnosis/DemandIQ_Step8B_Replenishment_Proxy_Series_Backtest.csv")
    assert len(series) == 27
    below_stress = series[series.actual_pct_of_estimate < 70.5]
    assert len(below_stress) == 2  # the uniform stress is not the worst case for every series
    assert series.actual_pct_of_estimate.min() == pytest.approx(54.17, abs=0.01)
    assert int(rec.backtest_years_below_needed_share.sum()) == 0


def test_proxy_backtest_covers_three_years():
    backtest = read("05_outputs/peak_season_diagnosis/DemandIQ_Step8B_Replenishment_Proxy_Backtest.csv")
    assert list(backtest.target_plan_year) == ["PY2024", "PY2025", "PY2026"]
    assert (backtest.share_arriving_weeks_1_3_pct == 100).all()
    assert backtest.series_week_wape_pct.min() == pytest.approx(56.84, abs=0.01)
    assert backtest.series_week_wape_pct.max() == pytest.approx(70.97, abs=0.01)
