"""Step 5's supply view: committed seasonal drops plus an unconfirmed replenishment estimate."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from conftest import ROOT, SERIES, read, run_script, series_level

PLAN = "05_outputs/ibp_decisions/DemandIQ_Step5_IBP_Decision_Plan.csv"
V1_PLAN = "05_outputs/v1_published_plan/DemandIQ_Step5_IBP_Decision_Plan.csv"
INVENTORY = "02_data/processed/DemandIQ_Step3C_v5_Seasonal_Buy_Inventory.csv"
SKU_GROWTH = {"APS-001": 0.040, "CTS-001": 0.055, "IMH-001": 0.065}
FORECAST_ORIGIN = pd.Timestamp("2026-06-22")
LATEST_PROJECTED_ARRIVAL = FORECAST_ORIGIN + pd.Timedelta(weeks=3)  # 3-week DC lead time

EXPECTED_RISK = {
    ("APS-001", "ECOM"): "LOW_COVERAGE_RISK",
    ("APS-001", "RETAIL"): "LOW_COVERAGE_RISK",
    ("APS-001", "WHOLESALE"): "LOW_COVERAGE_RISK",
    ("CTS-001", "ECOM"): "BALANCED",
    ("CTS-001", "RETAIL"): "LOW_COVERAGE_RISK",
    ("CTS-001", "WHOLESALE"): "BALANCED",
    ("IMH-001", "ECOM"): "LOW_COVERAGE_RISK",
    ("IMH-001", "RETAIL"): "SEVERE_SCENARIO_RISK",
    ("IMH-001", "WHOLESALE"): "LOW_COVERAGE_RISK",
}


@pytest.fixture(scope="module")
def plan() -> pd.DataFrame:
    return read(PLAN, parse_dates=["forecast_week_start"])


@pytest.fixture(scope="module")
def expected_replenishment() -> pd.Series:
    """Independent recomputation: last year's replenishment receipts, shifted 52 weeks, grown."""
    inv = read(INVENTORY, usecols=["week_start", "sku_id", "channel_id", "replenishment_receipt_units"],
               parse_dates=["week_start"])
    weekly = inv.groupby(["week_start"] + SERIES, as_index=False).replenishment_receipt_units.sum()
    weekly["forecast_week_start"] = weekly.week_start + pd.Timedelta(weeks=52)
    weekly = weekly[weekly.forecast_week_start.between("2026-06-29", "2026-09-21")]
    weekly["units"] = weekly.replenishment_receipt_units * (1 + weekly.sku_id.map(SKU_GROWTH))
    return weekly.set_index(["forecast_week_start"] + SERIES).units


def test_supply_view_is_labelled(plan):
    assert set(plan.supply_view) == {"SEASONAL_DROPS_PLUS_ESTIMATED_REPLENISHMENT"}
    assert set(plan.replenishment_confirmation_status) == {"UNCONFIRMED_ESTIMATE"}


def test_replenishment_matches_last_years_receipts(plan, expected_replenishment):
    got = plan.set_index(["forecast_week_start"] + SERIES).estimated_replenishment_receipt_units
    expected = expected_replenishment.reindex(got.index).fillna(0.0)
    assert np.allclose(got, expected, rtol=0, atol=1e-3)  # Step 5 writes 3 decimals
    assert got.sum() == pytest.approx(6512.17, abs=0.01)


def test_projected_replenishment_lands_before_the_demand_it_serves(plan):
    arriving = plan[plan.estimated_replenishment_receipt_units > 0]
    assert arriving.forecast_week_start.max() <= LATEST_PROJECTED_ARRIVAL
    assert sorted(arriving.horizon_week.unique()) == [1, 2, 3]


def test_planned_receipts_are_committed_plus_estimate(plan):
    total = plan.committed_receipt_units + plan.estimated_replenishment_receipt_units
    assert np.allclose(plan.planned_receipt_units, total, rtol=0, atol=2e-3)


def test_committed_receipts_are_the_v1_seasonal_drops(plan):
    """'Committed' keeps its v1 meaning: seasonal drops only, never the estimate."""
    v1 = read(V1_PLAN, parse_dates=["forecast_week_start"]).set_index(["forecast_week_start"] + SERIES)
    seasonal = plan.set_index(["forecast_week_start"] + SERIES).committed_receipt_units
    assert np.allclose(seasonal, v1.committed_receipt_units.reindex(seasonal.index), rtol=0, atol=1e-9)


def test_calls_if_the_estimate_arrives_as_modelled(plan):
    calls = series_level(plan, ["risk_type", "priority_tier", "planner_action"])
    assert calls.risk_type.to_dict() == EXPECTED_RISK
    assert calls.planner_action.value_counts().to_dict() == {"PROTECT": 7, "HOLD": 2}
    assert (calls.priority_tier != "P1").all()


def test_service_holds_every_week(plan):
    assert plan.base_fill_rate.min() == pytest.approx(1.0)
    assert plan.base_lost_demand_units.sum() == pytest.approx(0.0)


def test_decision_layer_agrees_with_step5(plan):
    series = read("05_outputs/decision_layer/DemandIQ_Step6A_Series_Decision_Summary.csv").set_index(SERIES)
    calls = series_level(plan, ["risk_type", "planner_action"])
    assert series.risk_type.to_dict() == calls.risk_type.to_dict()
    exec_row = read("05_outputs/decision_layer/DemandIQ_Step6A_Executive_KPI_Summary.csv").iloc[0]
    assert (exec_row.escalate_series, exec_row.protect_series, exec_row.hold_series) == (0, 7, 2)
    assert exec_row.estimated_replenishment_13w_units == pytest.approx(6512.17, abs=0.01)
    assert exec_row.supply_view == "SEASONAL_DROPS_PLUS_ESTIMATED_REPLENISHMENT"
    zero = (exec_row.zero_replenishment_escalate_series, exec_row.zero_replenishment_protect_series,
            exec_row.zero_replenishment_hold_series)
    assert zero == (3, 6, 0)
    assert exec_row.zero_replenishment_escalations == "APS-001 WHOLESALE; CTS-001 RETAIL; IMH-001 WHOLESALE"


def test_seasonal_only_reproduces_the_v1_plan(tmp_path):
    run_script("04_scripts/step5/step5_ibp_decision_engine.py",
               "--supply-view", "seasonal_only", "--output-dir", str(tmp_path))
    v1 = pd.read_csv(ROOT / V1_PLAN, dtype=str, keep_default_na=False)
    rebuilt = pd.read_csv(tmp_path / "DemandIQ_Step5_IBP_Decision_Plan.csv", dtype=str, keep_default_na=False)
    added = [c for c in rebuilt.columns if c not in v1.columns]
    assert added == ["estimated_replenishment_receipt_units", "planned_receipt_units", "supply_view",
                     "seasonal_receipt_projection_status", "seasonal_receipt_provenance",
                     "replenishment_receipt_provenance", "replenishment_confirmation_status", "call_condition"]
    assert set(rebuilt.seasonal_receipt_projection_status) == {"PROJECTED_NOT_CONFIRMED"}
    assert (rebuilt.estimated_replenishment_receipt_units.astype(float) == 0).all()
    assert set(rebuilt.supply_view) == {"SEASONAL_DROPS_ONLY"}
    differing = [c for c in v1.columns if not v1[c].equals(rebuilt[c])]
    assert differing == []
