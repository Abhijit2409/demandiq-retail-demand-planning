import argparse
import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# DEMANDIQ
# STEP 6A — FINAL KPI & DECISION LAYER
#
# PURPOSE
# ------------------------------------------------------------
# Convert the FROZEN Step 4D forecast and Step 5 IBP decision
# output into a small, auditable, presentation-ready decision
# layer that answers four planning questions:
#
#   1. What demand are we planning for (next 13 weeks)?
#   2. Can current inventory + planned supply protect service?
#      (planned = PROJECTED seasonal drops + ESTIMATED replenishment;
#      neither is a confirmed supplier order, so the zero-
#      replenishment calls are carried alongside for comparison.
#      The seasonal drops keep the v1 column name
#      committed_receipt_units for compatibility only.)
#   3. Where are the important service / inventory risks?
#   4. What should the planner do?
#
# GOVERNANCE
# ------------------------------------------------------------
# Step 6A does NOT create new forecasting, inventory, risk, or
# classification logic. It only READS, AGGREGATES, RESHAPES and
# RECONCILES frozen outputs.
#
#   - No re-computation of a metric that already has a frozen
#     authoritative value (fill rate, risk_type, priority_tier,
#     planner_action, safety gaps, economics, etc.).
#   - No hidden synthetic truth fields.
#   - No realized future weather.
#   - Economic values are exposure proxies, NOT accounting profit.
#
# If reconciliation QA fails, the outputs are NOT written.
# ============================================================


# ============================================================
# 1. PATHS
# ============================================================

# Repository root: this file lives in 04_scripts/step6/.
PROJECT_DIR = Path(__file__).resolve().parents[2]

STEP4D_FILE = (
    PROJECT_DIR
    / "05_outputs" / "forecasts"
    / "DemandIQ_Step4D_Final_13Week_Forecast.csv"
)

parser = argparse.ArgumentParser(description="DemandIQ Step 6A: KPI and decision layer.")
parser.add_argument(
    "--step5-file",
    type=Path,
    default=PROJECT_DIR / "05_outputs" / "ibp_decisions" / "DemandIQ_Step5_IBP_Decision_Plan.csv",
)
parser.add_argument(
    "--zero-replenishment-file",
    type=Path,
    default=PROJECT_DIR / "05_outputs" / "v1_published_plan" / "DemandIQ_Step5_IBP_Decision_Plan.csv",
    help="Step 5 plan with zero replenishment (the published v1 list), for comparison.",
)
parser.add_argument(
    "--output-dir",
    type=Path,
    default=PROJECT_DIR / "05_outputs" / "decision_layer",
)
ARGS = parser.parse_args()

STEP5_FILE = ARGS.step5_file
ZERO_REPLENISHMENT_FILE = ARGS.zero_replenishment_file

OUTPUT_DIR = ARGS.output_dir
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXEC_FILE = OUTPUT_DIR / "DemandIQ_Step6A_Executive_KPI_Summary.csv"
SERIES_FILE = OUTPUT_DIR / "DemandIQ_Step6A_Series_Decision_Summary.csv"
WEEKLY_FILE = OUTPUT_DIR / "DemandIQ_Step6A_Weekly_Planning_Trajectory.csv"


# ============================================================
# 2. GOVERNED CONSTANTS (for QA reconciliation only)
# ============================================================

SERVICE_TARGET_FILL_RATE = 0.92
EXPECTED_SERIES = 9
FORECAST_HORIZON = 13
EXPECTED_ROWS = EXPECTED_SERIES * FORECAST_HORIZON

EXPECTED_BASE_13W_DEMAND = 36434.66
RECON_TOLERANCE_UNITS = 1.0

# Risk type -> priority tier, as governed in Step 5 section 39.
TIER_BY_RISK = {
    "BASE_SERVICE_RISK": "P1",
    "WEEKLY_SERVICE_RISK": "P1",
    "LOW_COVERAGE_RISK": "P2",
    "SEVERE_SCENARIO_RISK": "P2",
    "EXCESS_INVENTORY_RISK": "P3",
    "BALANCED": "P4",
}

# Outputs carry the plan date, not the wall-clock run time, so a
# rebuild is byte-identical.
SOURCE_NOTE = (
    "DERIVED from frozen DemandIQ_Step4D_Final_13Week_Forecast.csv "
    "and DemandIQ_Step5_IBP_Decision_Plan.csv"
)


# ============================================================
# 3. LOAD FROZEN INPUTS
# ============================================================

for path in (STEP4D_FILE, STEP5_FILE):
    if not path.exists():
        raise FileNotFoundError(f"Required frozen input not found:\n{path}")

forecast_4d = pd.read_csv(STEP4D_FILE, parse_dates=["forecast_week_start"])
step5 = pd.read_csv(STEP5_FILE, parse_dates=["forecast_week_start"])



def add_supply_fields(plan):
    """Plans written before the supply-view fix carry seasonal drops only."""
    if "estimated_replenishment_receipt_units" not in plan.columns:
        plan["estimated_replenishment_receipt_units"] = 0.0
        plan["planned_receipt_units"] = plan["committed_receipt_units"]
        plan["supply_view"] = "SEASONAL_DROPS_ONLY"
        plan["replenishment_receipt_provenance"] = "NONE COUNTED (ZERO REPLENISHMENT)"
        plan["replenishment_confirmation_status"] = "NOT_APPLICABLE"
        plan["call_condition"] = (
            "ZERO-REPLENISHMENT VIEW: THE PUBLISHED (V1) ESCALATION LIST; ITS "
            "SEASONAL DROPS ARE ALSO PROJECTED, NOT CONFIRMED SUPPLIER ORDERS"
        )
    if "seasonal_receipt_projection_status" not in plan.columns:
        plan["seasonal_receipt_projection_status"] = "PROJECTED_NOT_CONFIRMED"
        plan["seasonal_receipt_provenance"] = (
            "PROJECTION: PRIOR-YEAR SEASONAL RECEIPTS SHIFTED 52 WEEKS X (1 + SKU GROWTH); "
            "NOT CONFIRMED SUPPLIER ORDERS. COLUMN committed_receipt_units KEEPS ITS V1 NAME "
            "FOR COMPATIBILITY ONLY"
        )
    return plan


step5 = add_supply_fields(step5)

if not ZERO_REPLENISHMENT_FILE.exists():
    raise FileNotFoundError(
        f"Zero-replenishment comparison plan not found:\n{ZERO_REPLENISHMENT_FILE}"
    )
zero_plan = add_supply_fields(
    pd.read_csv(ZERO_REPLENISHMENT_FILE, parse_dates=["forecast_week_start"])
)
if (zero_plan["estimated_replenishment_receipt_units"] != 0).any():
    raise RuntimeError("The comparison plan must count zero replenishment.")

SUPPLY_VIEW = step5["supply_view"].iloc[0]
USES_ESTIMATE = bool(step5["estimated_replenishment_receipt_units"].sum() > 0)
PLAN_AS_OF_DATE = step5["forecast_week_start"].min().strftime("%Y-%m-%d")

print("=" * 92)
print("STEP 6A — FINAL KPI & DECISION LAYER")
print("=" * 92)
print("Step 4D forecast :", STEP4D_FILE, forecast_4d.shape)
print("Step 5 decisions :", STEP5_FILE, step5.shape)


# ============================================================
# 4. LEAKAGE GUARD
#
# Assert no forbidden hidden-truth / generator-only field is
# present in anything we carry into the presentation layer.
# ============================================================

FORBIDDEN_FIELDS = {
    "true_demand_units",
    "lost_demand_units",              # historical generator field
    "audit_hidden_demand",
    "weather_effect_pct",
    "weather_factor",
    "positive_spike_factor",
    "negative_shock_factor",
    "noise_factor",
}

# Note: Step 5's FORWARD simulation fields such as
# base_lost_demand_units are DERIVED planning outputs, not the
# forbidden historical generator field of the same stem. We only
# guard against the exact forbidden names above.
forbidden_present = FORBIDDEN_FIELDS & set(step5.columns)
if forbidden_present:
    raise RuntimeError(
        f"Forbidden hidden-truth field found in Step 5 input: {sorted(forbidden_present)}"
    )


# ============================================================
# 5. SERIES-LEVEL FROZEN VALUES
#
# Every series-level column in Step 5 is constant across the 13
# weekly rows of a series (verified). We take the first row per
# series as the authoritative frozen value.
# ============================================================

GROUP = ["sku_id", "channel_id"]

# Guard: confirm the series-level columns really are constant so
# that "take first" is a safe, non-distorting selection.
SERIES_CONST_COLS = [
    "base_13w_fill_rate", "severe_13w_fill_rate",
    "min_weekly_base_fill_rate", "worst_base_service_week",
    "worst_week_service_gap_units", "weeks_below_service_target",
    "max_consecutive_weeks_below_target", "weekly_service_exception_flag",
    "base_final_inventory_units", "base_final_wos", "base_safety_gap_units",
    "base_protection_gap_units", "chase_capacity_units",
    "forward_seasonal_commitment_units", "opening_inventory_units",
    "recommended_reallocation_units", "recommended_chase_release_units",
    "base_uncovered_gap_after_action_units",
    "contingency_reallocation_option_units", "contingency_chase_option_units",
    "contingency_uncovered_gap_units",
    "base_13w_lost_revenue_opportunity_cad",
    "severe_13w_lost_revenue_opportunity_cad",
    "base_13w_carrying_cost_proxy_cad",
    "priority_tier", "risk_type", "planner_action", "action_reason",
    "service_target_fill_rate",
]
nonconst = [
    c for c in SERIES_CONST_COLS
    if c in step5.columns and step5.groupby(GROUP)[c].nunique().max() > 1
]
if nonconst:
    raise RuntimeError(
        f"Expected series-level constants vary within a series: {nonconst}. "
        "Cannot safely reshape."
    )

first_per_series = step5.sort_values(GROUP + ["horizon_week"]).groupby(GROUP).first()
last_per_series = step5.sort_values(GROUP + ["horizon_week"]).groupby(GROUP).last()

# Aggregations of frozen weekly values (no frozen series column exists).
agg = step5.groupby(GROUP).agg(
    base_13w_demand_units=("base_forecast_units", "sum"),
    mild_13w_demand_units=("mild_scenario_forecast_units", "sum"),
    severe_13w_demand_units=("severe_scenario_forecast_units", "sum"),
    base_13w_projected_shipments_units=("base_shipped_units", "sum"),
    forward_committed_receipts_13w=("committed_receipt_units", "sum"),
    forward_estimated_replenishment_13w=("estimated_replenishment_receipt_units", "sum"),
    forward_planned_receipts_13w=("planned_receipt_units", "sum"),
    weekly_below_target_count=(  # for QA cross-check vs weeks_below_service_target
        "base_fill_rate",
        lambda s: int((s < SERVICE_TARGET_FILL_RATE).sum()),
    ),
)

# ending_safety_stock: frozen last-week weekly safety_stock_units (reshape/selection).
ending_safety = last_per_series["safety_stock_units"].rename("ending_safety_stock_units")


# ============================================================
# 6. OUTPUT 2 — SKU x CHANNEL DECISION SUMMARY (9 rows)
# ============================================================

series = (
    first_per_series[[
        # service (frozen)
        "base_13w_fill_rate", "severe_13w_fill_rate",
        "min_weekly_base_fill_rate", "worst_base_service_week",
        "worst_week_service_gap_units", "weeks_below_service_target",
        "max_consecutive_weeks_below_target", "weekly_service_exception_flag",
        # inventory / coverage (frozen)
        "base_final_inventory_units", "base_final_wos", "base_safety_gap_units",
        # supply / options (frozen)
        "chase_capacity_units",
        "recommended_reallocation_units", "recommended_chase_release_units",
        "contingency_chase_option_units",
        # decision (frozen)
        "priority_tier", "risk_type", "planner_action", "action_reason",
        # economics (frozen)
        "base_13w_lost_revenue_opportunity_cad",
        "severe_13w_lost_revenue_opportunity_cad",
        "base_13w_carrying_cost_proxy_cad",
    ]]
    .join(agg[[
        "base_13w_demand_units", "mild_13w_demand_units", "severe_13w_demand_units",
        "forward_committed_receipts_13w",
        "forward_estimated_replenishment_13w", "forward_planned_receipts_13w",
    ]])
    .join(ending_safety)
    .reset_index()
)

# Ordered, decision-relevant column layout.
series = series[[
    # identity
    "sku_id", "channel_id",
    # demand
    "base_13w_demand_units", "mild_13w_demand_units", "severe_13w_demand_units",
    # service
    "base_13w_fill_rate", "severe_13w_fill_rate",
    "min_weekly_base_fill_rate", "worst_base_service_week",
    "worst_week_service_gap_units", "weeks_below_service_target",
    "max_consecutive_weeks_below_target", "weekly_service_exception_flag",
    # inventory / coverage
    "base_final_inventory_units", "base_final_wos",
    "ending_safety_stock_units", "base_safety_gap_units",
    # supply / options
    "forward_committed_receipts_13w",
    "forward_estimated_replenishment_13w", "forward_planned_receipts_13w",
    "chase_capacity_units",
    "recommended_reallocation_units", "recommended_chase_release_units",
    "contingency_chase_option_units",
    # decision
    "priority_tier", "risk_type", "planner_action", "action_reason",
    # economics
    "base_13w_lost_revenue_opportunity_cad",
    "severe_13w_lost_revenue_opportunity_cad",
    "base_13w_carrying_cost_proxy_cad",
]].sort_values(["sku_id", "channel_id"]).reset_index(drop=True)

# Zero-replenishment comparison (the published v1 calls), per series.
zero_calls = (
    zero_plan.sort_values(GROUP + ["horizon_week"])
    .groupby(GROUP)[["priority_tier", "risk_type", "planner_action"]]
    .first()
    .add_prefix("zero_replenishment_")
    .reset_index()
)
series = series.merge(zero_calls, on=GROUP, how="left", validate="one_to_one")
series["call_depends_on_estimated_replenishment"] = (
    series["planner_action"] != series["zero_replenishment_planner_action"]
).astype(int)
for column in (
    "seasonal_receipt_projection_status",
    "replenishment_confirmation_status", "call_condition",
):
    series[column] = step5[column].iloc[0]

series["data_classification"] = "DERIVED"
series["provenance"] = SOURCE_NOTE


# ============================================================
# 7. OUTPUT 3 — WEEKLY PLANNING TRAJECTORY (117 rows)
# ============================================================

weekly = step5[[
    "forecast_week_start", "horizon_week", "sku_id", "channel_id",
    # demand
    "base_forecast_units",
    "mild_scenario_forecast_units", "severe_scenario_forecast_units",
    # supply: planned = projected seasonal drops (legacy name committed_receipt_units)
    #         + estimated replenishment
    "committed_receipt_units",
    "estimated_replenishment_receipt_units", "planned_receipt_units",
    # base inventory flow (frozen simulation outputs)
    "base_beginning_inventory_units", "base_return_restock_units",
    "base_available_units", "base_shipped_units", "base_lost_demand_units",
    "base_ending_inventory_units", "base_fill_rate", "base_weeks_of_supply",
    # policy / decision
    "safety_stock_units", "service_target_fill_rate",
    "priority_tier", "risk_type", "planner_action",
    # series-level context (constant per series) kept for filtering in viz
    "weekly_service_exception_flag",
]].copy()

# DERIVED per-week flag: does THIS individual week miss the 92% target?
# Distinct from the series-level weekly_service_exception_flag (>= 2 misses).
weekly["weekly_base_fill_below_target_flag"] = (
    weekly["base_fill_rate"] < SERVICE_TARGET_FILL_RATE
).astype(int)

weekly = weekly.rename(
    columns={"weekly_service_exception_flag": "series_weekly_service_exception_flag"}
)

weekly = weekly.sort_values(
    ["sku_id", "channel_id", "horizon_week"]
).reset_index(drop=True)

weekly["data_classification"] = "DERIVED"
weekly["provenance"] = SOURCE_NOTE


# ============================================================
# 8. OUTPUT 1 — EXECUTIVE KPI SUMMARY (1 row)
# ============================================================

# Portfolio demand / supply (aggregations of frozen values).
base_demand = float(step5["base_forecast_units"].sum())
mild_demand = float(step5["mild_scenario_forecast_units"].sum())
severe_demand = float(step5["severe_scenario_forecast_units"].sum())
base_ship = float(step5["base_shipped_units"].sum())
severe_ship = float(step5["severe_shipped_units"].sum())

# Peak base-demand week — independently derived from Step 4D (not hardcoded).
peak_4d = forecast_4d.groupby("forecast_week_start")["base_forecast_units"].sum()
peak_week = peak_4d.idxmax()
peak_units = float(peak_4d.max())

# Counts by risk type (kept for the app) and by tier and action.
p1_count = int((series["risk_type"] == "WEEKLY_SERVICE_RISK").sum())
p2_count = int((series["risk_type"] == "LOW_COVERAGE_RISK").sum())
severe_count = int((series["risk_type"] == "SEVERE_SCENARIO_RISK").sum())
tier_counts = series["priority_tier"].value_counts()
action_counts = series["planner_action"].value_counts()

immediate_chase = float(first_per_series["recommended_chase_release_units"].sum())
immediate_reallocation = float(first_per_series["recommended_reallocation_units"].sum())
exception_series = int(series["weekly_service_exception_flag"].sum())

zero_first = zero_plan.sort_values(GROUP + ["horizon_week"]).groupby(GROUP).first()
zero_action_counts = zero_first["planner_action"].value_counts()
zero_escalations = "; ".join(
    f"{sku} {channel}"
    for (sku, channel) in zero_first.index[zero_first["planner_action"] == "ESCALATE"]
)

portfolio_decision_status = (
    ("IF ESTIMATED REPLENISHMENT ARRIVES AS MODELLED: " if USES_ESTIMATE else "")
    + f"{'ACTION REQUIRED' if tier_counts.get('P1', 0) else 'NO ESCALATION'} - "
    + " + ".join(
        f"{n} {action}" for action, n in sorted(action_counts.items())
    )
    + f"; aggregate Base fill {base_ship / base_demand * 100:.1f}% vs "
    f"{SERVICE_TARGET_FILL_RATE * 100:.0f}% target; "
    f"{exception_series} series with 2+ weeks below target; "
    f"{immediate_chase:,.0f} chase and {immediate_reallocation:,.0f} "
    f"reallocation units released automatically"
    + (
        "; WITH ZERO REPLENISHMENT (PUBLISHED LIST): "
        + " + ".join(f"{n} {a}" for a, n in sorted(zero_action_counts.items()))
        + "; CONFIRM OPEN-ORDER QUANTITIES AND RECEIPT DATES BEFORE REPLACING "
        "THE PUBLISHED ESCALATION LIST"
        if USES_ESTIMATE else ""
    )
    + "; SEASONAL DROPS ARE PROJECTED FROM LAST YEAR, NOT CONFIRMED SUPPLIER ORDERS"
)

exec_row = {
    # demand
    "base_13w_demand_units": base_demand,
    "mild_13w_demand_units": mild_demand,
    "severe_13w_demand_units": severe_demand,
    "mild_vs_base_pct": (mild_demand - base_demand) / base_demand * 100,
    "severe_vs_base_pct": (severe_demand - base_demand) / base_demand * 100,
    "scenario_width_units": severe_demand - mild_demand,
    # service / supply
    "base_13w_projected_shipments_units": base_ship,
    "base_13w_fill_rate": base_ship / base_demand,
    "severe_13w_fill_rate": severe_ship / severe_demand,
    "service_target_fill_rate": SERVICE_TARGET_FILL_RATE,
    "opening_inventory_units": float(
        first_per_series["opening_inventory_units"].sum()
    ),
    "committed_receipts_13w_units": float(step5["committed_receipt_units"].sum()),
    "estimated_replenishment_13w_units": float(
        step5["estimated_replenishment_receipt_units"].sum()
    ),
    "planned_receipts_13w_units": float(step5["planned_receipt_units"].sum()),
    "total_chase_capacity_units": float(
        first_per_series["chase_capacity_units"].sum()
    ),
    # risk counts
    "p1_weekly_service_risk_series": p1_count,
    "p2_low_coverage_risk_series": p2_count,
    "p2_severe_scenario_risk_series": severe_count,
    "p1_series": int(tier_counts.get("P1", 0)),
    "p2_series": int(tier_counts.get("P2", 0)),
    "p3_series": int(tier_counts.get("P3", 0)),
    "p4_series": int(tier_counts.get("P4", 0)),
    "escalate_series": int(action_counts.get("ESCALATE", 0)),
    "protect_series": int(action_counts.get("PROTECT", 0)),
    "hold_series": int(action_counts.get("HOLD", 0)),
    "total_series": int(series.shape[0]),
    # comparison: zero replenishment (the published v1 list)
    "zero_replenishment_escalate_series": int(zero_action_counts.get("ESCALATE", 0)),
    "zero_replenishment_protect_series": int(zero_action_counts.get("PROTECT", 0)),
    "zero_replenishment_hold_series": int(zero_action_counts.get("HOLD", 0)),
    "zero_replenishment_escalations": zero_escalations,
    "series_whose_call_depends_on_estimate": int(
        series["call_depends_on_estimated_replenishment"].sum()
    ),
    # protection / immediate action (frozen governance)
    "base_safety_stock_protection_gap_units": float(
        first_per_series["base_protection_gap_units"].sum()
    ),
    "immediate_reallocation_units": float(
        first_per_series["recommended_reallocation_units"].sum()
    ),
    "immediate_chase_release_units": float(
        first_per_series["recommended_chase_release_units"].sum()
    ),
    "base_uncovered_service_gap_units": float(
        first_per_series["base_uncovered_gap_after_action_units"].sum()
    ),
    # contingency options (frozen)
    "contingency_reallocation_option_units": float(
        first_per_series["contingency_reallocation_option_units"].sum()
    ),
    "contingency_chase_option_units": float(
        first_per_series["contingency_chase_option_units"].sum()
    ),
    "contingency_uncovered_gap_units": float(
        first_per_series["contingency_uncovered_gap_units"].sum()
    ),
    # economics (exposure proxies, NOT accounting profit)
    "base_lost_revenue_opportunity_cad": float(
        first_per_series["base_13w_lost_revenue_opportunity_cad"].sum()
    ),
    "severe_lost_revenue_opportunity_cad": float(
        first_per_series["severe_13w_lost_revenue_opportunity_cad"].sum()
    ),
    "base_carrying_cost_proxy_cad": float(
        first_per_series["base_13w_carrying_cost_proxy_cad"].sum()
    ),
    # peak demand
    "peak_base_demand_week": peak_week.strftime("%Y-%m-%d"),
    "peak_base_weekly_demand_units": peak_units,
    # decision
    "portfolio_decision_status": portfolio_decision_status,
    # provenance
    "data_classification": "DERIVED",
    "economic_value_basis": "planning exposure proxy (not accounting profit)",
    "provenance": SOURCE_NOTE,
    "supply_view": SUPPLY_VIEW,
    "seasonal_receipt_projection_status": step5["seasonal_receipt_projection_status"].iloc[0],
    "seasonal_receipt_provenance": step5["seasonal_receipt_provenance"].iloc[0],
    "replenishment_receipt_provenance": step5["replenishment_receipt_provenance"].iloc[0],
    "replenishment_confirmation_status": step5["replenishment_confirmation_status"].iloc[0],
    "call_condition": step5["call_condition"].iloc[0],
    "plan_as_of_date": PLAN_AS_OF_DATE,
}
executive = pd.DataFrame([exec_row])


# ============================================================
# 9. QA — STRUCTURE, RECONCILIATION, GOVERNANCE
# ============================================================

qa = {}

# ---- structure ----
qa["Executive summary = 1 row"] = executive.shape[0] == 1
qa["Series summary = 9 rows"] = series.shape[0] == EXPECTED_SERIES
qa["Weekly trajectory = 117 rows"] = weekly.shape[0] == EXPECTED_ROWS
qa["Weekly has 13 unique forecast weeks"] = (
    weekly["forecast_week_start"].nunique() == FORECAST_HORIZON
)
qa["Weekly has 9 unique series"] = (
    weekly[GROUP].drop_duplicates().shape[0] == EXPECTED_SERIES
)
qa["No duplicate Week x SKU x Channel"] = (
    weekly.duplicated(["forecast_week_start", "sku_id", "channel_id"]).sum() == 0
)
qa["Series summary grain unique"] = (
    series.duplicated(GROUP).sum() == 0
)

# ---- reconciliation ----
qa["Base 13W demand = 36,434.66 (+/- 1)"] = (
    abs(base_demand - EXPECTED_BASE_13W_DEMAND) <= RECON_TOLERANCE_UNITS
)
qa["Step5 base demand == Step4D base demand"] = np.isclose(
    base_demand, float(forecast_4d["base_forecast_units"].sum()), atol=1e-6
)
qa["Exec demand == series demand sum"] = np.isclose(
    base_demand, float(series["base_13w_demand_units"].sum()), atol=1e-6
)
qa["Exec demand == weekly demand sum"] = np.isclose(
    base_demand, float(weekly["base_forecast_units"].sum()), atol=1e-6
)
qa["Exec shipments == weekly base_shipped sum"] = np.isclose(
    base_ship, float(weekly["base_shipped_units"].sum()), atol=1e-6
)
qa["Planned receipts = projected seasonal drops + estimated replenishment"] = bool(np.allclose(
    step5["planned_receipt_units"],
    step5["committed_receipt_units"]
    + step5["estimated_replenishment_receipt_units"],
    atol=1e-6,
))
qa["Exec receipts == weekly receipts sum"] = np.isclose(
    exec_row["planned_receipts_13w_units"],
    float(weekly["planned_receipt_units"].sum()), atol=1e-6
) and np.isclose(
    exec_row["committed_receipts_13w_units"],
    float(weekly["committed_receipt_units"].sum()), atol=1e-6
)
qa["Estimated replenishment carries an unconfirmed status"] = (
    not USES_ESTIMATE
    or exec_row["replenishment_confirmation_status"] == "UNCONFIRMED_ESTIMATE"
)
qa["Seasonal drops carry a projected status"] = (
    exec_row["seasonal_receipt_projection_status"] == "PROJECTED_NOT_CONFIRMED"
)
qa["Zero-replenishment comparison covers every series"] = bool(
    series["zero_replenishment_planner_action"].notna().all()
)

# ---- decision governance (rules, not expected counts) ----
qa["Priority tier follows the Step 5 risk hierarchy"] = bool(
    (series["risk_type"].map(TIER_BY_RISK) == series["priority_tier"]).all()
)
qa["Exec tier counts == series tier counts"] = (
    sum(exec_row[f"p{i}_series"] for i in range(1, 5)) == series.shape[0]
)
not_base_service = series["risk_type"] != "BASE_SERVICE_RISK"
qa["Immediate chase only on BASE_SERVICE_RISK"] = bool(
    series.loc[not_base_service, "recommended_chase_release_units"].eq(0).all()
)
qa["Immediate reallocation only on BASE_SERVICE_RISK"] = bool(
    series.loc[not_base_service, "recommended_reallocation_units"].eq(0).all()
)

# ---- weekly service governance ----
p1_rows = series[series["risk_type"] == "WEEKLY_SERVICE_RISK"]
qa["All WEEKLY_SERVICE_RISK have weeks_below >= 2"] = bool(
    (p1_rows["weeks_below_service_target"] >= 2).all()
)
qa["All WEEKLY_SERVICE_RISK exception_flag == 1"] = bool(
    (p1_rows["weekly_service_exception_flag"] == 1).all()
)
qa["Weekly exceptions appear only on P1 series"] = bool(
    series.loc[series["weekly_service_exception_flag"] == 1, "priority_tier"]
    .eq("P1").all()
)
qa["All WEEKLY_SERVICE_RISK action == ESCALATE"] = bool(
    (p1_rows["planner_action"] == "ESCALATE").all()
)
qa["No WEEKLY_SERVICE_RISK auto-converted to CHASE"] = bool(
    (p1_rows["planner_action"] != "CHASE").all()
    and np.isclose(p1_rows["recommended_chase_release_units"].sum(), 0.0)
)
# per-week flag reconciles to frozen weeks_below_service_target
wk_flag_count = (
    weekly.groupby(GROUP)["weekly_base_fill_below_target_flag"].sum()
    .reindex(series.set_index(GROUP).index).values
)
qa["Weekly flag count == frozen weeks_below_service_target"] = bool(
    np.array_equal(wk_flag_count, series["weeks_below_service_target"].values)
)

# ---- peak demand (independently derived) ----
qa["Peak base week independently derived (Step4D)"] = (
    peak_week.strftime("%Y-%m-%d") == "2026-09-07"
)

# ---- leakage ----
all_out_cols = set(executive.columns) | set(series.columns) | set(weekly.columns)
qa["No forbidden hidden-truth field in outputs"] = (
    len(FORBIDDEN_FIELDS & all_out_cols) == 0
)

qa_pass = all(qa.values())


# ============================================================
# 10. CONSOLE REPORT
# ============================================================

print("\n" + "=" * 92)
print("STEP 6A QA RESULTS")
print("=" * 92)
for name, passed in qa.items():
    print(f"  [{'PASS' if passed else 'FAIL'}]  {name}")
print("-" * 92)
print(f"  OVERALL: {'PASS' if qa_pass else 'FAIL'}  "
      f"({sum(qa.values())}/{len(qa)} checks)")

if not qa_pass:
    failed = [n for n, p in qa.items() if not p]
    raise RuntimeError(
        "Step 6A reconciliation QA FAILED. Outputs NOT written.\n"
        f"Failed checks: {failed}"
    )

# Executive KPI summary (transposed for readability).
print("\n" + "=" * 92)
print("EXECUTIVE KPI SUMMARY")
print("=" * 92)
for k, v in exec_row.items():
    if isinstance(v, float):
        print(f"  {k:<44} {v:,.2f}")
    else:
        print(f"  {k:<44} {v}")

# 9-series decision table.
print("\n" + "=" * 92)
print("SKU x CHANNEL DECISION SUMMARY")
print("=" * 92)
view = series[[
    "sku_id", "channel_id", "base_13w_fill_rate", "min_weekly_base_fill_rate",
    "weeks_below_service_target", "base_final_wos",
    "priority_tier", "risk_type", "planner_action",
]].copy()
view["base_13w_fill_rate"] = (view["base_13w_fill_rate"] * 100).round(1)
view["min_weekly_base_fill_rate"] = (view["min_weekly_base_fill_rate"] * 100).round(1)
view["base_final_wos"] = view["base_final_wos"].round(2)
view = view.rename(columns={
    "base_13w_fill_rate": "base_fill_%",
    "min_weekly_base_fill_rate": "min_wk_fill_%",
    "weeks_below_service_target": "wks_below",
    "base_final_wos": "end_wos",
})
print(view.to_string(index=False))


# ============================================================
# 11. WRITE OUTPUTS (only after QA passes)
# ============================================================

executive.to_csv(EXEC_FILE, index=False)
series.to_csv(SERIES_FILE, index=False)
weekly.to_csv(WEEKLY_FILE, index=False)

print("\n" + "=" * 92)
print("FILES CREATED")
print("=" * 92)
print(f"  {EXEC_FILE}   ({executive.shape[0]} row x {executive.shape[1]} cols)")
print(f"  {SERIES_FILE}   ({series.shape[0]} rows x {series.shape[1]} cols)")
print(f"  {WEEKLY_FILE}   ({weekly.shape[0]} rows x {weekly.shape[1]} cols)")
print("\nStep 6A complete. QA PASSED. Frozen Steps 4A-5 untouched.")
