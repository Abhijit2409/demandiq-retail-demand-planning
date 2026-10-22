"""Step 8B: Step 5's corrected calls against Step 8's error-band queue."""

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


def test_no_series_escalates_under_replenishment_stress(rec):
    stress = rec[["step5_tier_replenishment_low", "step5_tier_replenishment_high",
                  "step5_tier_replenishment_latest_arrival"]]
    assert not stress.eq("P1").any().any()


def test_v1_escalations_clear_with_part_of_the_pipeline(rec):
    was_p1 = rec[rec.v1_published_tier == "P1"]
    assert len(was_p1) == 3
    assert was_p1.share_of_proxy_needed_to_avoid_escalation_pct.max() < 100 - rec.replenishment_stress_pct.iloc[0]


def test_proxy_backtest_covers_three_years():
    backtest = read("05_outputs/peak_season_diagnosis/DemandIQ_Step8B_Replenishment_Proxy_Backtest.csv")
    assert list(backtest.target_plan_year) == ["PY2024", "PY2025", "PY2026"]
    assert (backtest.share_arriving_weeks_1_3_pct == 100).all()
