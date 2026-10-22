"""Reusable governance/reconciliation validation for the DemandIQ dashboard.

Confirms the Step 6A layer is internally consistent and follows the Step 5
governance rules. The checks are rules, not expected counts, so they hold for
any supply view (the plan with estimated replenishment and the zero-replenishment v1 plan).
Read-only: never mutates or rebuilds any upstream data.
"""
from __future__ import annotations
import math

EXPECTED_BASE_DEMAND = 36434.66
SERVICE_TARGET = 0.92
SAFETY_STOCK_WEEKS = 2.5
WEEKLY_EXCEPTION_WEEKS = 2

TIER_BY_RISK = {
    "BASE_SERVICE_RISK": "P1",
    "WEEKLY_SERVICE_RISK": "P1",
    "LOW_COVERAGE_RISK": "P2",
    "SEVERE_SCENARIO_RISK": "P2",
    "EXCESS_INVENTORY_RISK": "P3",
    "BALANCED": "P4",
}


def _close(a, b, tol=1.0):
    return abs(float(a) - float(b)) <= tol


def run_validation(exec_df, series_df, weekly_df) -> dict:
    """Return {check_name: bool}. All True == governed state intact."""
    checks: dict[str, bool] = {}
    e = exec_df.iloc[0]

    # ---- structure ----
    checks["Executive rows = 1"] = len(exec_df) == 1
    checks["Series rows = 9"] = len(series_df) == 9
    checks["Weekly rows = 117"] = len(weekly_df) == 117
    checks["Weeks = 13"] = weekly_df["forecast_week_start"].nunique() == 13
    checks["SKU x Channel series = 9"] = (
        weekly_df[["sku_id", "channel_id"]].drop_duplicates().shape[0] == 9
    )
    checks["No duplicate Week x SKU x Channel"] = (
        weekly_df.duplicated(["forecast_week_start", "sku_id", "channel_id"]).sum() == 0
    )

    # ---- classification rules ----
    weekly_risk = series_df[series_df["risk_type"] == "WEEKLY_SERVICE_RISK"]
    low_cover = series_df[series_df["risk_type"] == "LOW_COVERAGE_RISK"]
    checks["Priority tier follows the risk hierarchy"] = bool(
        (series_df["risk_type"].map(TIER_BY_RISK) == series_df["priority_tier"]).all()
    )
    checks["Weekly service risk -> ESCALATE"] = bool(
        (weekly_risk["planner_action"] == "ESCALATE").all()
    )
    checks["Weekly service risk has 2+ weekly misses"] = bool(
        (weekly_risk["weeks_below_service_target"] >= WEEKLY_EXCEPTION_WEEKS).all()
    )
    checks["Weekly exception flag only on P1"] = bool(
        series_df.loc[series_df["weekly_service_exception_flag"] == 1, "priority_tier"]
        .eq("P1").all()
    )
    checks["Low coverage -> PROTECT, below policy"] = bool(
        (low_cover["planner_action"] == "PROTECT").all()
        and (low_cover["base_final_wos"] < SAFETY_STOCK_WEEKS).all()
    )
    checks["No weekly service risk auto-converted to CHASE"] = bool(
        (weekly_risk["planner_action"] != "CHASE").all()
        and math.isclose(
            float(weekly_risk["recommended_chase_release_units"].sum()), 0.0, abs_tol=1e-9
        )
    )
    checks["Service target = 92%"] = _close(e["service_target_fill_rate"], SERVICE_TARGET, 1e-6)

    # ---- immediate execution: only an aggregate service failure releases stock ----
    not_base = series_df["risk_type"] != "BASE_SERVICE_RISK"
    checks["Immediate chase only on base service risk"] = bool(
        series_df.loc[not_base, "recommended_chase_release_units"].eq(0).all()
    )
    checks["Immediate reallocation only on base service risk"] = bool(
        series_df.loc[not_base, "recommended_reallocation_units"].eq(0).all()
    )

    # ---- reconciliation ----
    checks["Base demand = 36,434.66"] = _close(e["base_13w_demand_units"], EXPECTED_BASE_DEMAND, 1.0)
    checks["Exec base demand == weekly sum"] = _close(
        e["base_13w_demand_units"], weekly_df["base_forecast_units"].sum(), 1.0
    )
    checks["Exec receipts == weekly sum"] = _close(
        e["committed_receipts_13w_units"], weekly_df["committed_receipt_units"].sum(), 1.0
    ) and (
        "planned_receipts_13w_units" not in e.index
        or _close(e["planned_receipts_13w_units"], weekly_df["planned_receipt_units"].sum(), 1.0)
    )
    if "seasonal_receipt_projection_status" in e.index:
        checks["Seasonal drops marked projected, not confirmed"] = (
            e["seasonal_receipt_projection_status"] == "PROJECTED_NOT_CONFIRMED"
        )
    if float(e.get("estimated_replenishment_13w_units", 0.0) or 0.0) > 0:
        checks["Estimated replenishment marked unconfirmed"] = (
            e.get("replenishment_confirmation_status") == "UNCONFIRMED_ESTIMATE"
        )
    checks["Exec weekly-risk count == series count"] = (
        int(e["p1_weekly_service_risk_series"]) == len(weekly_risk)
    )
    checks["Exec low-coverage count == series count"] = (
        int(e["p2_low_coverage_risk_series"]) == len(low_cover)
    )

    return checks


def all_passed(checks: dict) -> bool:
    return all(checks.values())
