"""DemandIQ Step 8B: reconcile Step 5's supply views with Step 8's S&OE queue.

Step 5 now adds an ESTIMATE of replenishment receipts to the seasonal drops:
last year's replenishment receipts in the same weeks, shifted 52 weeks and
grown by SKU. The estimate is not a list of confirmed open orders. Its timing
check validates the projected dates against the Step 3A policy, not supplier
commitments. So Step 5's calls are conditional on the estimate arriving as
modelled, and the zero-replenishment calls (the published v1 list) stay the
comparison until a planner confirms open-order quantities and receipt dates.

This script:

1. Backtests the replenishment estimate on the earlier plan years, for the
   portfolio and for each series.
2. Re-simulates Step 5's inventory flow and risk hierarchy from Step 5's own
   output. The replica must reproduce the plan with the estimate and, with
   the estimate removed, the published zero-replenishment plan.
3. Stresses the estimate: a uniform cut by the worst backtest series WAPE, a
   uniform uplift, all units on the last projected date, all units in the
   last week of the window; and finds the share of its estimate each series
   needs to avoid escalation. These are scenarios, not bounds.
4. Compares Step 5's calls with Step 8's error-band queue series by series.
   Every difference must match a known mechanism, or the script stops.

Run after Steps 5, 6A and 8. Planner view only: no simulation-truth fields.

    python 04_scripts/step8/step8b_step5_reconciliation.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "05_outputs" / "peak_season_diagnosis"

INVENTORY_FILE = ROOT / "02_data/processed/DemandIQ_Step3C_v5_Seasonal_Buy_Inventory.csv"
STEP5_PLAN_FILE = ROOT / "05_outputs/ibp_decisions/DemandIQ_Step5_IBP_Decision_Plan.csv"
STEP5_V1_FILE = ROOT / "05_outputs/v1_published_plan/DemandIQ_Step5_IBP_Decision_Plan.csv"
STEP8_QUEUE_FILE = OUT_DIR / "DemandIQ_Step8_Corrected_SOE_Queue.csv"
ESTIMATE_SUPPLY_VIEW = "SEASONAL_DROPS_PLUS_ESTIMATED_REPLENISHMENT"

# Step 5 governed policy (Step 3A assumptions workbook).
TARGET_FILL = 0.92
SAFETY_STOCK_WEEKS = 2.5
WEEKLY_EXCEPTION_WEEKS = 2
EXCESS_WOS = 8.0
FORECAST_WEEKS = 13
SKU_GROWTH = {"APS-001": 0.040, "CTS-001": 0.055, "IMH-001": 0.065}

SERIES = ["sku_id", "channel_id"]
PLANNER = "PLANNER_VIEW"
TIER_BY_RISK = {
    "BASE_SERVICE_RISK": "P1", "WEEKLY_SERVICE_RISK": "P1",
    "LOW_COVERAGE_RISK": "P2", "SEVERE_SCENARIO_RISK": "P2",
    "EXCESS_INVENTORY_RISK": "P3", "BALANCED": "P4",
}
# Step 5 tiers in Step 8's queue vocabulary.
CALL_BY_TIER = {"P1": "ESCALATE", "P2": "PROTECT", "P3": "REDUCE", "P4": "NO ACTION"}
CALL_RANK = {"ESCALATE": 0, "WATCH": 1, "PROTECT": 2, "REDUCE": 3, "NO ACTION": 4}

COVER_TOLERANCE_WEEKS = 0.005  # Step 5 rounds its output to 3 dp


# --------------------------------------------------------------------------- 1. proxy backtest

def backtest_weeks() -> tuple[pd.DataFrame, list, np.ndarray]:
    """Replenishment receipts in plan weeks 1-13 by plan year, with SKU growth factors."""
    inv = pd.read_csv(INVENTORY_FILE, usecols=["plan_year", "plan_week", "sku_id", "channel_id",
                                               "replenishment_receipt_units"])
    window = inv[inv.plan_week.between(1, FORECAST_WEEKS)]
    weekly = window.groupby(["plan_year", "plan_week"] + SERIES).replenishment_receipt_units.sum()
    weekly = weekly.unstack("plan_year").fillna(0.0)
    years = sorted(weekly.columns)
    growth = 1 + weekly.index.get_level_values("sku_id").map(SKU_GROWTH).to_numpy()
    # The first two plan years are excluded as targets: the simulation starts in
    # PY2022 with no replenishment on order, so PY2022's weeks 1-3 hold none and a
    # PY2023 estimate built from them is zero by construction.
    return weekly, list(zip(years[1:], years[2:])), growth


def replenishment_proxy_backtest() -> pd.DataFrame:
    """Last year's replenishment in plan weeks 1-13, grown, against what arrived (portfolio)."""
    weekly, pairs, growth = backtest_weeks()
    rows = []
    for prior, target in pairs:
        proxy_w = weekly[prior].to_numpy() * growth
        actual_w = weekly[target].to_numpy()
        totals = pd.DataFrame({"proxy": proxy_w, "actual": actual_w}, index=weekly.index).groupby(SERIES).sum()
        early = weekly[target][weekly.index.get_level_values("plan_week") <= 3].sum()
        rows.append({
            "target_plan_year": target,
            "proxy_source_plan_year": prior,
            "actual_units_weeks_1_13": actual_w.sum(),
            "proxy_units_weeks_1_13": proxy_w.sum(),
            "portfolio_error_pct": (proxy_w.sum() - actual_w.sum()) / actual_w.sum() * 100,
            "series_wape_pct": (totals.proxy - totals.actual).abs().sum() / totals.actual.sum() * 100,
            "series_week_wape_pct": np.abs(proxy_w - actual_w).sum() / actual_w.sum() * 100,
            "share_arriving_weeks_1_3_pct": early / actual_w.sum() * 100,
            "basis": PLANNER,
        })
    return pd.DataFrame(rows)


def replenishment_series_backtest() -> pd.DataFrame:
    """Per series and plan year: units that arrived in weeks 1-13 as a share of the estimate."""
    weekly, pairs, growth = backtest_weeks()
    frames = []
    for prior, target in pairs:
        frame = pd.DataFrame({"estimate_units": weekly[prior].to_numpy() * growth,
                              "actual_units": weekly[target].to_numpy()},
                             index=weekly.index).groupby(SERIES).sum().reset_index()
        frame.insert(0, "target_plan_year", target)
        frame.insert(1, "estimate_source_plan_year", prior)
        frames.append(frame)
    out = pd.concat(frames, ignore_index=True)
    out["actual_pct_of_estimate"] = out.actual_units / out.estimate_units * 100
    out["basis"] = PLANNER
    return out


# --------------------------------------------------------------------------- 2. Step 5 replica

def simulate(plan: pd.DataFrame, demand_col: str, receipts: pd.Series) -> pd.DataFrame:
    """Step 5 section 25: weekly flow with restocked returns from last week's shipments."""
    rows = []
    for _, g in plan.groupby(SERIES, sort=True):
        g = g.sort_values("forecast_week_start")
        inventory = float(g.opening_inventory_units.iloc[0])
        prior_ship = float(g.prior_week_shipped_units.iloc[0])
        return_rate = float(g.returns_rate.iloc[0])
        restock_share = float(g.sellable_restock_share.iloc[0])
        for idx, row in g.iterrows():
            demand = max(0.0, float(row[demand_col]))
            available = inventory + max(0.0, float(receipts[idx])) + prior_ship * return_rate * restock_share
            shipped = min(available, demand)
            inventory = max(0.0, available - shipped)
            rows.append({"row": idx, "demand": demand, "shipped": shipped, "ending": inventory})
            prior_ship = shipped
    return pd.DataFrame(rows).set_index("row").reindex(plan.index)


def risk_calls(plan: pd.DataFrame, receipts: pd.Series) -> pd.DataFrame:
    """Step 5 sections 29 and 39: series risk type and tier for a given receipt stream."""
    runs = {s: simulate(plan, f"{s}_forecast_units" if s == "base" else f"{s}_scenario_forecast_units", receipts)
            for s in ("base", "mild", "severe")}
    out = []
    for key, g in plan.groupby(SERIES, sort=True):
        idx = g.sort_values("forecast_week_start").index
        base, mild, severe = (runs[s].loc[idx] for s in ("base", "mild", "severe"))
        weekly_fill = np.where(base.demand > 0, base.shipped / base.demand.where(base.demand > 0, 1), 1.0).clip(0, 1)
        base_fill = base.shipped.sum() / base.demand.sum()
        severe_fill = severe.shipped.sum() / severe.demand.sum()
        weeks_below = int((weekly_fill < TARGET_FILL).sum())
        run_rate = float(plan.loc[idx[-1], "forecast_run_rate_units"])
        safety_end = float(plan.loc[idx[-1], "safety_stock_units"])
        base_end, mild_end, severe_end = (float(x.ending.iloc[-1]) for x in (base, mild, severe))
        if base_fill < TARGET_FILL:
            risk = "BASE_SERVICE_RISK"
        elif weeks_below >= WEEKLY_EXCEPTION_WEEKS:
            risk = "WEEKLY_SERVICE_RISK"
        elif base_end < safety_end:
            risk = "LOW_COVERAGE_RISK"
        elif severe_fill < TARGET_FILL or severe_end < safety_end:
            risk = "SEVERE_SCENARIO_RISK"
        elif mild_end / run_rate > EXCESS_WOS:
            risk = "EXCESS_INVENTORY_RISK"
        else:
            risk = "BALANCED"
        out.append({
            "sku_id": key[0], "channel_id": key[1],
            "base_13w_fill_rate": base_fill, "min_weekly_fill_rate": float(weekly_fill.min()),
            "weeks_below_target": weeks_below,
            "base_final_wos": base_end / run_rate, "severe_final_wos": severe_end / run_rate,
            "risk_type": risk, "priority_tier": TIER_BY_RISK[risk],
        })
    return pd.DataFrame(out)


def receipts_at(plan: pd.DataFrame, scale: float) -> pd.Series:
    """Projected seasonal drops (legacy column committed_receipt_units) plus the scaled estimate."""
    return plan.committed_receipt_units + scale * plan.estimated_replenishment_receipt_units


def receipts_all_in_week(plan: pd.DataFrame, week: pd.Timestamp) -> pd.Series:
    """Seasonal drops plus each series' whole replenishment estimate landing in `week`."""
    replenishment = plan.estimated_replenishment_receipt_units
    series_total = replenishment.groupby([plan.sku_id, plan.channel_id]).transform("sum")
    late = np.where(plan.forecast_week_start == week, series_total, 0.0)
    return plan.committed_receipt_units + pd.Series(late, index=plan.index)


def last_projected_arrival(plan: pd.DataFrame) -> pd.Timestamp:
    return plan.loc[plan.estimated_replenishment_receipt_units > 0, "forecast_week_start"].max()


def escalation_threshold(plan: pd.DataFrame, sku: str, channel: str) -> float:
    """Smallest share of the replenishment estimate that keeps the series out of P1 (0 if none needed)."""
    one = plan[(plan.sku_id == sku) & (plan.channel_id == channel)]

    def is_p1(scale: float) -> bool:
        return risk_calls(one, receipts_at(one, scale)).priority_tier.iloc[0] == "P1"

    if not is_p1(0.0):
        return 0.0
    if is_p1(1.0):
        return float("nan")
    low, high = 0.0, 1.0
    for _ in range(30):
        mid = (low + high) / 2
        low, high = (mid, high) if is_p1(mid) else (low, mid)
    return high


SERIES_FIELDS = ["risk_type", "priority_tier", "planner_action", "base_final_wos", "severe_final_wos"]


def first_row(plan: pd.DataFrame) -> pd.DataFrame:
    """Series-level Step 5 fields (constant across a series' 13 rows)."""
    cols = SERIES + ["horizon_week"] + SERIES_FIELDS
    return plan[cols].sort_values("horizon_week").groupby(SERIES, sort=True).first().reset_index()


def validate_replica(plan: pd.DataFrame, v1: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The replica must reproduce Step 5's calls with the estimate and, without it, the v1 calls."""
    with_estimate = risk_calls(plan, receipts_at(plan, 1.0))
    step5 = first_row(plan)
    if not (with_estimate.risk_type.to_numpy() == step5.risk_type.to_numpy()).all():
        raise ValueError("Replica does not reproduce Step 5's risk types with the estimate.")
    gap = np.abs(with_estimate.base_final_wos.to_numpy() - step5.base_final_wos.to_numpy()).max()
    if gap > COVER_TOLERANCE_WEEKS:
        raise ValueError(f"Replica cover differs from Step 5 by {gap:.4f} weeks.")

    zero_replenishment = risk_calls(plan, receipts_at(plan, 0.0))
    v1_calls = first_row(v1)
    if not (zero_replenishment.risk_type.to_numpy() == v1_calls.risk_type.to_numpy()).all():
        raise ValueError("Replica without replenishment does not reproduce the v1 published calls.")
    return with_estimate, zero_replenishment


# --------------------------------------------------------------------------- 3-4. reconciliation

def explain(row: pd.Series) -> str:
    """Rule-derived explanation; raises when a difference matches no known mechanism."""
    notes = []
    if row.step8_call == "WATCH" and row.step5_priority_tier != "P1":
        notes.append(
            f"Step 8 tests the forecast error band: at +{row.step8_wape_band:.1%} demand this series "
            f"misses 92% in 2+ weeks (worst week {row.step8_worst_weekly_fill_high_demand:.1%}), "
            f"which Step 8 ranks as WATCH. Step 5 plans on the point forecast, where service holds "
            f"and cover is {row.step5_base_cover_weeks:.2f} weeks against the 2.5-week policy, so "
            f"{row.step5_action}. Both say protect stock and do not escalate.")
    elif row.step5_risk_type == "SEVERE_SCENARIO_RISK" and row.step8_call == "NO ACTION":
        notes.append(
            f"Step 5 also tests the severe-weather scenario: cover falls to "
            f"{row.step5_severe_cover_weeks:.2f} weeks, under the 2.5-week policy "
            f"(base case {row.step5_base_cover_weeks:.2f}). Step 8 has no weather scenario.")
    elif not row.calls_agree:
        raise ValueError(f"Unexplained call difference for {row.sku_id} {row.channel_id}: "
                         f"Step 5 {row.step5_call}, Step 8 {row.step8_call}.")
    else:
        notes.append("Same call.")
    if abs(row.cover_difference_weeks) >= 0.0005:
        notes.append(
            f"Cover differs by {row.cover_difference_weeks:+.3f} weeks: Step 8 holds restocked "
            f"returns at the published plan's values, while Step 5 recomputes them from the "
            f"higher shipments once the estimated replenishment is counted.")
    return " ".join(notes)


def reconcile(plan: pd.DataFrame, v1: pd.DataFrame, stress: float,
              series_backtest: pd.DataFrame) -> pd.DataFrame:
    queue = pd.read_csv(STEP8_QUEUE_FILE)
    step5 = first_row(plan)
    published = first_row(v1)

    out = published[SERIES].copy()
    out["v1_published_tier"] = published.priority_tier.to_numpy()
    out["v1_published_action"] = published.planner_action.to_numpy()
    out["estimated_replenishment_units"] = (
        plan.groupby(SERIES, sort=True).estimated_replenishment_receipt_units.sum().to_numpy())
    out["replenishment_confirmation_status"] = plan.replenishment_confirmation_status.iloc[0]
    out["step5_risk_type"] = step5.risk_type.to_numpy()
    out["step5_priority_tier"] = step5.priority_tier.to_numpy()
    out["step5_action"] = step5.planner_action.to_numpy()
    out["step5_call"] = out.step5_priority_tier.map(CALL_BY_TIER)
    out["step5_base_cover_weeks"] = step5.base_final_wos.to_numpy()
    out["step5_severe_cover_weeks"] = step5.severe_final_wos.to_numpy()
    out = out.merge(queue[SERIES + ["corrected_action", "ending_cover_weeks", "wape_band",
                                    "worst_weekly_fill_high_demand"]], on=SERIES, validate="one_to_one")
    out = out.rename(columns={"corrected_action": "step8_call", "ending_cover_weeks": "step8_cover_weeks",
                              "wape_band": "step8_wape_band",
                              "worst_weekly_fill_high_demand": "step8_worst_weekly_fill_high_demand"})
    out["calls_agree"] = out.step5_call == out.step8_call
    out["cover_difference_weeks"] = out.step5_base_cover_weeks - out.step8_cover_weeks
    out["combined_call"] = [min(a, b, key=CALL_RANK.get) for a, b in zip(out.step5_call, out.step8_call)]

    stresses = {
        "step5_tier_replenishment_low": receipts_at(plan, 1 - stress),
        "step5_tier_replenishment_high": receipts_at(plan, 1 + stress),
        "step5_tier_replenishment_latest_arrival": receipts_all_in_week(plan, last_projected_arrival(plan)),
        "step5_tier_replenishment_all_in_week_13": receipts_all_in_week(
            plan, plan.forecast_week_start.max()),
    }
    for column, receipts in stresses.items():
        out[column] = risk_calls(plan, receipts).priority_tier.to_numpy()
    out["replenishment_stress_pct"] = stress * 100
    out["share_of_estimate_needed_to_avoid_escalation_pct"] = [
        escalation_threshold(plan, r.sku_id, r.channel_id) * 100 for r in out.itertuples()]

    by_series = series_backtest.groupby(SERIES, sort=True)
    out["backtest_min_actual_pct_of_estimate"] = by_series.actual_pct_of_estimate.min().to_numpy()
    out["backtest_max_actual_pct_of_estimate"] = by_series.actual_pct_of_estimate.max().to_numpy()
    needed = out.set_index(SERIES).share_of_estimate_needed_to_avoid_escalation_pct
    below = series_backtest.join(needed, on=SERIES)
    below = below.actual_pct_of_estimate < below.share_of_estimate_needed_to_avoid_escalation_pct
    out["backtest_years_below_needed_share"] = below.groupby(
        [series_backtest.sku_id, series_backtest.channel_id], sort=True).sum().to_numpy()
    out["backtest_years"] = by_series.size().to_numpy()
    out["explanation"] = out.apply(explain, axis=1)
    out["basis"] = PLANNER
    return out


def summary_metrics(backtest: pd.DataFrame, series_backtest: pd.DataFrame, rec: pd.DataFrame,
                    plan: pd.DataFrame) -> pd.DataFrame:
    def count(col: str, value: str) -> int:
        return int((rec[col] == value).sum())

    stress_cols = ["step5_tier_replenishment_low", "step5_tier_replenishment_high",
                   "step5_tier_replenishment_latest_arrival", "step5_tier_replenishment_all_in_week_13"]
    changed = rec[stress_cols].ne(rec.step5_priority_tier, axis=0).any(axis=1)
    escalated_under_stress = int(rec[stress_cols].eq("P1").any(axis=1).sum())
    was_p1 = rec[rec.v1_published_tier == "P1"]
    hardest = was_p1.loc[was_p1.share_of_estimate_needed_to_avoid_escalation_pct.idxmax()]
    stress_arrival = 100 - rec.replenishment_stress_pct.iloc[0]
    worse_than_stress = series_backtest[series_backtest.actual_pct_of_estimate < stress_arrival]
    lowest = series_backtest.loc[series_backtest.actual_pct_of_estimate.idxmin()]
    former = series_backtest.merge(was_p1[SERIES], on=SERIES)
    rows = [
        ("Estimated replenishment in the 13-week projection (unconfirmed, not open orders)",
         plan.estimated_replenishment_receipt_units.sum(), "units"),
        ("Last projected replenishment arrival (projected date, not a supplier date)",
         last_projected_arrival(plan).strftime("%Y-%m-%d"), "date"),
        ("Replenishment confirmation status", plan.replenishment_confirmation_status.iloc[0], "status"),
        ("Projected seasonal drops in the 13-week projection (not confirmed supplier orders)",
         plan.committed_receipt_units.sum(), "units"),
        ("Seasonal drop projection status", plan.seasonal_receipt_projection_status.iloc[0], "status"),
        ("Replenishment proxy series WAPE, worst backtest year", backtest.series_wape_pct.max(), "%"),
        ("Replenishment proxy portfolio error, worst backtest year", backtest.portfolio_error_pct.abs().max(), "%"),
        ("Replenishment proxy series-week WAPE, best backtest year", backtest.series_week_wape_pct.min(), "%"),
        ("Replenishment proxy series-week WAPE, worst backtest year", backtest.series_week_wape_pct.max(), "%"),
        ("v1 published (zero replenishment): ESCALATE", count("v1_published_action", "ESCALATE"), "series"),
        ("v1 published (zero replenishment): PROTECT", count("v1_published_action", "PROTECT"), "series"),
        ("v1 published (zero replenishment): escalated series",
         ", ".join(f"{r.sku_id} {r.channel_id}" for r in was_p1.itertuples()), "series"),
        ("Step 5 if the estimate arrives as modelled: ESCALATE", count("step5_action", "ESCALATE"), "series"),
        ("Step 5 if the estimate arrives as modelled: PROTECT", count("step5_action", "PROTECT"), "series"),
        ("Step 5 if the estimate arrives as modelled: PROTECT on low coverage",
         count("step5_risk_type", "LOW_COVERAGE_RISK"), "series"),
        ("Step 5 if the estimate arrives as modelled: PROTECT on the severe-weather test",
         count("step5_risk_type", "SEVERE_SCENARIO_RISK"), "series"),
        ("Step 5 if the estimate arrives as modelled: HOLD", count("step5_action", "HOLD"), "series"),
        ("Step 8 queue: ESCALATE", count("step8_call", "ESCALATE"), "series"),
        ("Step 8 queue: WATCH", count("step8_call", "WATCH"), "series"),
        ("Step 8 queue: PROTECT", count("step8_call", "PROTECT"), "series"),
        ("Step 8 queue: NO ACTION", count("step8_call", "NO ACTION"), "series"),
        ("Series where Step 5 and Step 8 agree", int(rec.calls_agree.sum()), "of 9"),
        ("Largest cover difference, Step 5 vs Step 8", rec.cover_difference_weeks.abs().max(), "weeks"),
        ("Combined queue: ESCALATE", count("combined_call", "ESCALATE"), "series"),
        ("Combined queue: WATCH", count("combined_call", "WATCH"), "series"),
        ("Combined queue: PROTECT", count("combined_call", "PROTECT"), "series"),
        ("Combined queue: NO ACTION", count("combined_call", "NO ACTION"), "series"),
        ("Replenishment stress applied (worst backtest series WAPE)", rec.replenishment_stress_pct.iloc[0], "%"),
        ("Share of the estimate arriving under the uniform stress", stress_arrival, "%"),
        ("Series whose Step 5 tier changes under a stress", int(changed.sum()), "of 9"),
        ("Series whose tier changes under a stress (list)",
         ", ".join(f"{r.sku_id} {r.channel_id}" for r in rec[changed].itertuples()), "series"),
        ("Series escalated (P1) under the tested stresses", escalated_under_stress, "of 9"),
        ("Most replenishment any v1 escalation needs to clear",
         was_p1.share_of_estimate_needed_to_avoid_escalation_pct.max(), "% of estimate"),
        ("Series needing the most of its estimate", f"{hardest.sku_id} {hardest.channel_id}", "series"),
        ("Backtest series-years arriving below the uniform stress",
         f"{len(worse_than_stress)} of {len(series_backtest)}", "series-years"),
        ("Lowest backtest arrival", lowest.actual_pct_of_estimate, "% of estimate"),
        ("Lowest backtest arrival (series, plan year)",
         f"{lowest.sku_id} {lowest.channel_id}, {lowest.target_plan_year}", "series"),
        ("Backtest series-years below a v1 escalation's needed share",
         f"{int(was_p1.backtest_years_below_needed_share.sum())} of {len(former)}", "series-years"),
    ]
    out = pd.DataFrame(rows, columns=["metric", "value", "unit"])
    out["value"] = [round(v, 3) if isinstance(v, (float, np.floating)) else v for v in out.value]
    out["basis"] = PLANNER
    return out


def main() -> None:
    plan = pd.read_csv(STEP5_PLAN_FILE, parse_dates=["forecast_week_start"])
    v1 = pd.read_csv(STEP5_V1_FILE, parse_dates=["forecast_week_start"])
    if plan.supply_view.iloc[0] != ESTIMATE_SUPPLY_VIEW:
        raise ValueError("Step 5 output does not include the replenishment estimate; rerun Step 5 with defaults.")
    if plan.replenishment_confirmation_status.iloc[0] != "UNCONFIRMED_ESTIMATE":
        raise ValueError("Step 5 output does not mark the replenishment estimate as unconfirmed.")

    backtest = replenishment_proxy_backtest()
    series_backtest = replenishment_series_backtest()
    validate_replica(plan, v1)
    stress = round(float(backtest.series_wape_pct.max()) / 100, 3)
    rec = reconcile(plan, v1, stress, series_backtest)
    summary = summary_metrics(backtest, series_backtest, rec, plan)

    outputs = {
        "DemandIQ_Step8B_Replenishment_Proxy_Backtest.csv": backtest,
        "DemandIQ_Step8B_Replenishment_Proxy_Series_Backtest.csv": series_backtest,
        "DemandIQ_Step8B_Step5_Reconciliation.csv": rec,
        "DemandIQ_Step8B_Summary_Metrics.csv": summary,
    }
    for name, frame in outputs.items():
        frame = frame.copy()
        numeric = frame.select_dtypes("number").columns
        frame[numeric] = frame[numeric].round(4)
        frame.to_csv(OUT_DIR / name, index=False)

    pd.set_option("display.width", 200)
    print(backtest.round(1).to_string(index=False))
    print()
    print(rec[SERIES + ["v1_published_action", "step5_action", "step8_call", "combined_call",
                        "step5_base_cover_weeks", "cover_difference_weeks"]].round(3).to_string(index=False))
    print()
    print(summary.to_string(index=False))
    print(f"\nWrote {len(outputs)} files to {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
