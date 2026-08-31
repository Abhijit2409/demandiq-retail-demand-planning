"""Reusable governance/reconciliation validation for the DemandIQ dashboard.

Confirms the frozen Step 6A layer still matches the governed state. Used by
the Step 6C smoke test and available to surface a governance badge in the UI.
Read-only: never mutates or rebuilds any upstream data.
"""
from __future__ import annotations
import math

EXPECTED_P1_SERIES = {
    ("APS-001", "WHOLESALE"),
    ("CTS-001", "RETAIL"),
    ("IMH-001", "WHOLESALE"),
}
EXPECTED_BASE_DEMAND = 36434.66
SERVICE_TARGET = 0.92
SAFETY_STOCK_WEEKS = 2.5


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

    # ---- frozen classifications ----
    p1 = series_df[series_df["risk_type"] == "WEEKLY_SERVICE_RISK"]
    p2 = series_df[series_df["risk_type"] == "LOW_COVERAGE_RISK"]
    checks["P1 WEEKLY_SERVICE_RISK = 3"] = len(p1) == 3
    checks["P2 LOW_COVERAGE_RISK = 6"] = len(p2) == 6
    checks["Exact P1 series set"] = (
        set(map(tuple, p1[["sku_id", "channel_id"]].values)) == EXPECTED_P1_SERIES
    )
    checks["All P1 action = ESCALATE"] = bool((p1["planner_action"] == "ESCALATE").all())
    checks["All P2 action = PROTECT"] = bool((p2["planner_action"] == "PROTECT").all())

    # ---- service governance ----
    checks["All P1 weekly exception flag = 1"] = bool(
        (p1["weekly_service_exception_flag"] == 1).all()
    )
    checks["All P1 weeks_below >= 2"] = bool((p1["weeks_below_service_target"] >= 2).all())
    checks["No P1 auto-converted to CHASE"] = bool(
        (p1["planner_action"] != "CHASE").all()
        and math.isclose(float(p1["recommended_chase_release_units"].sum()), 0.0, abs_tol=1e-9)
        if "recommended_chase_release_units" in p1.columns
        else (p1["planner_action"] != "CHASE").all()
    )
    checks["Service target = 92%"] = _close(e["service_target_fill_rate"], SERVICE_TARGET, 1e-6)

    # ---- immediate execution ----
    checks["Immediate chase release = 0"] = _close(e["immediate_chase_release_units"], 0.0, 1e-9)
    checks["Immediate reallocation = 0"] = _close(e["immediate_reallocation_units"], 0.0, 1e-9)

    # ---- reconciliation ----
    checks["Base demand = 36,434.66"] = _close(e["base_13w_demand_units"], EXPECTED_BASE_DEMAND, 1.0)
    checks["Exec base demand == weekly sum"] = _close(
        e["base_13w_demand_units"], weekly_df["base_forecast_units"].sum(), 1.0
    )
    checks["Exec P1 count == series P1 count"] = (
        int(e["p1_weekly_service_risk_series"]) == len(p1)
    )
    checks["Exec P2 count == series P2 count"] = (
        int(e["p2_low_coverage_risk_series"]) == len(p2)
    )

    return checks


def all_passed(checks: dict) -> bool:
    return all(checks.values())
