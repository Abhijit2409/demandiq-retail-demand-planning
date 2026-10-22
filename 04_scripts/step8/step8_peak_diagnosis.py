"""DemandIQ - Step 8: peak-season diagnosis and decision inputs.

Business question
    Peak-season (Dec-Feb) fill has fallen for four plan years. Why, and what
    should the Demand Planner change in the next fall/winter buy, chase plan
    and launch allocation to recover lost sales without building excess?

This script reads only committed DemandIQ files and writes:
    05_outputs/peak_season_diagnosis/DemandIQ_Step8_*.csv
    08_assets/charts/step8_*.png

Evidence basis (stated on every output)
    PLANNER_VIEW      data a planner can observe: sales, in-stock days,
                      receipts, buys, plans, and reconstructed demand (Step 4A,
                      recovered here from the committed Step 4B backtest
                      actuals, which equal sales on every uncensored week).
    SIMULATION_TRUTH  generator-only columns (true and lost demand). Used to
                      size the problem and to check the planner view, never as
                      a planning input.

The peak-buy recommendation (Peak_Buy_Recommendation, Peak_Buy_by_Region,
Peak_Move_Feasibility) uses PLANNER_VIEW data only. SIMULATION_TRUTH appears
in the diagnosis, for sizing, and in Peak_Buy_Validation, never in a decision.

The recommendation is retrospective: it is evaluated at the published plan's
as-of date, 2026-06-29, and its order and chase deadlines (Jun 29 to Oct 5,
2026) are what the planner should have decided then.

Run from anywhere:
    python 04_scripts/step8/step8_peak_diagnosis.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "05_outputs" / "peak_season_diagnosis"
CHART_DIR = ROOT / "08_assets" / "charts"

HISTORY_FILE = ROOT / "02_data/processed/DemandIQ_Step3D_v4_Retail_Economics.csv"
RECON_FILE = ROOT / "03_model_evidence/step4b_forecasting/baseline/DemandIQ_Step4B_Baseline_Predictions.csv"
# The 13-week counterfactuals analyse the plan as first published (v1: seasonal
# drops only). Step 5 now counts in-transit replenishment; Step 8B reconciles
# that corrected plan with this script's queue.
TRAJECTORY_FILE = ROOT / "05_outputs/v1_published_plan/DemandIQ_Step6A_Weekly_Planning_Trajectory.csv"
SERIES_DECISION_FILE = ROOT / "05_outputs/v1_published_plan/DemandIQ_Step6A_Series_Decision_Summary.csv"
CHAMPION_FILE = ROOT / "05_outputs/champion_selection/DemandIQ_Step4B_Champion_Selection.csv"
LAUNCH_BUY_FILE = ROOT / "05_outputs/launch_step7e/DemandIQ_Step7E_Initial_Buy_Plan.csv"
LAUNCH_ACTUALS_FILE = ROOT / "05_outputs/launch_step7e/DemandIQ_Step7E_Launch_Weekly_Actuals.csv"
LAUNCH_POLICY_FILE = ROOT / "05_outputs/launch_step7f/DemandIQ_Step7F_Policy_Sensitivity.csv"

# Frozen policies from Step 5 and the Step 3A assumptions workbook.
TARGET_FILL = 0.92
SAFETY_STOCK_WEEKS = 2.5
WEEKLY_EXCEPTION_WEEKS = 2
CHASE_CAP_SHARE = 0.08
CHASE_EARLY_WEEKS = (8, 13)  # opening of the chase window, plan weeks
PEAK_BLOCK_START_WEEK = 14  # October drop
PEAK_MONTHS = (12, 1, 2)
SPRING_MONTHS = (3, 4, 5, 6)  # replenishment that lands after the peak
PLAN_AS_OF = pd.Timestamp("2026-06-29")  # first week of the published 13-week plan
OVERSEAS_LEAD_WEEKS = 22  # seasonal buy lane, assumptions workbook
CHASE_LEAD_WEEKS = 10  # chase lane, assumptions workbook
# Policy assumption, to agree with finance: add no new units to a series whose
# inventory-based over-buy exposure is already >= 50% of its estimated lost revenue.
GUARDRAIL_OVERBUY_RATIO = 0.5
DIAGNOSIS, RECOMMENDATION, VALIDATION = "DIAGNOSIS", "RECOMMENDATION", "VALIDATION"
SKU_GROWTH = {"APS-001": 0.040, "CTS-001": 0.055, "IMH-001": 0.065}
LATEST_PY = "PY2026"
SERIES = ["sku_id", "channel_id"]
CELL = ["sku_id", "region_id", "channel_id"]
WINDOWS = {
    "S&OE window, last year (Jun 30-Sep 22, 2025)": ("2025-06-30", "2025-09-22"),
    "Peak build and season (Oct 6, 2025-Jan 26, 2026)": ("2025-10-06", "2026-01-26"),
    "Dec-Feb, PY2026": ("2025-12-01", "2026-02-23"),
    "Full plan year PY2026": ("2025-06-30", "2026-06-22"),
}
TRUTH, PLANNER = "SIMULATION_TRUTH", "PLANNER_VIEW"

# Chart tokens (dataviz reference palette, light surface).
SURFACE, INK, INK_2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, ACCENT, DATA_GREY = "#e1e0d9", "#c3c2b7", "#2a78d6", "#b4b2a9"

HISTORY_COLUMNS = [
    "week_start", "plan_year", "plan_week", "month", "sku_id", "region_id", "channel_id",
    "true_demand_units", "observed_sales_units", "lost_demand_units", "shipped_units",
    "sales_censored_flag", "in_stock_days", "planning_basis_type", "planning_basis_annual_units",
    "planner_growth_assumption_pct", "committed_buy_units_plan_year", "weekly_plan_units",
    "seasonal_receipt_units", "replenishment_receipt_units", "chase_receipt_units",
    "chase_triggered_flag", "return_restock_units", "beginning_inventory_units",
    "ending_inventory_units", "lost_revenue_opportunity_cad", "net_revenue_after_returns_cad",
    "total_overbuy_event_exposure_cad", "net_asp_cad", "receipt_event_label",
]


# --------------------------------------------------------------------------- inputs

def read_history() -> pd.DataFrame:
    """Week x SKU x region x channel history (Step 3C/3D), with an identity check."""
    df = pd.read_csv(HISTORY_FILE, usecols=HISTORY_COLUMNS, parse_dates=["week_start"])
    gap = (df.observed_sales_units + df.lost_demand_units - df.true_demand_units).abs()
    if gap.max() > 0.51:
        raise ValueError("Sales + lost demand does not equal true demand; history is inconsistent.")
    return df


def read_series_history(history: pd.DataFrame) -> pd.DataFrame:
    """Series-week history (SKU x channel) joined to reconstructed demand.

    Reconstructed demand covers 2023-07-03 to 2026-06-22 (PY2024-PY2026): the
    weeks the Step 4B backtest scored. Earlier weeks were training-only.
    """
    series = history.groupby(["week_start", "plan_year", "month"] + SERIES, as_index=False).agg(
        observed_units=("observed_sales_units", "sum"),
        true_units=("true_demand_units", "sum"),
        censored_rows=("sales_censored_flag", "sum"),
        replenishment_units=("replenishment_receipt_units", "sum"),
    )
    backtest = pd.read_csv(RECON_FILE, parse_dates=["forecast_date"])
    recon = (
        backtest.drop_duplicates(SERIES + ["forecast_date"])
        .rename(columns={"forecast_date": "week_start", "actual_units": "reconstructed_units"})
        [SERIES + ["week_start", "reconstructed_units"]]
    )
    series = series.merge(recon, on=SERIES + ["week_start"], how="left")
    clean = series[(series.censored_rows == 0) & series.reconstructed_units.notna()]
    if not np.allclose(clean.reconstructed_units, clean.observed_units, atol=0.6):
        raise ValueError("Reconstructed demand differs from sales on uncensored weeks.")
    return series


# --------------------------------------------------------------------------- diagnosis

def fill_trend(history: pd.DataFrame, series: pd.DataFrame) -> pd.DataFrame:
    """Annual and Dec-Feb fill by plan year, with lost units and lost revenue."""
    peak = history.month.isin(PEAK_MONTHS)
    year = history.groupby("plan_year").agg(
        true_units=("true_demand_units", "sum"),
        sold_units=("observed_sales_units", "sum"),
        lost_units=("lost_demand_units", "sum"),
        lost_revenue_cad=("lost_revenue_opportunity_cad", "sum"),
        net_revenue_cad=("net_revenue_after_returns_cad", "sum"),
    )
    peak_year = history[peak].groupby("plan_year").agg(
        peak_true_units=("true_demand_units", "sum"),
        peak_sold_units=("observed_sales_units", "sum"),
        peak_lost_units=("lost_demand_units", "sum"),
    )
    planner = (
        series[series.month.isin(PEAK_MONTHS)].dropna(subset=["reconstructed_units"])
        .groupby("plan_year")[["observed_units", "reconstructed_units"]].sum()
    )
    out = year.join(peak_year).join(planner)
    out["annual_fill_truth"] = out.sold_units / out.true_units
    out["peak_fill_truth"] = out.peak_sold_units / out.peak_true_units
    out["peak_fill_planner_view"] = out.observed_units / out.reconstructed_units
    out["peak_share_of_lost_units"] = out.peak_lost_units / out.lost_units
    out["lost_revenue_share_of_net_revenue"] = out.lost_revenue_cad / out.net_revenue_cad
    out = out.drop(columns=["observed_units", "reconstructed_units"])
    out["basis"] = f"{TRUTH}; peak_fill_planner_view is {PLANNER} (PY2024+)"
    return out.reset_index()


def buy_basis(history: pd.DataFrame, series: pd.DataFrame) -> pd.DataFrame:
    """How far each plan year's buy basis sat below last year's demand."""
    cell_year = history.groupby(["plan_year"] + CELL).agg(
        basis_units=("planning_basis_annual_units", "first"),
        basis_type=("planning_basis_type", "first"),
        growth_assumption=("planner_growth_assumption_pct", "first"),
        committed_buy_units=("committed_buy_units_plan_year", "first"),
        true_units=("true_demand_units", "sum"),
        sold_units=("observed_sales_units", "sum"),
    )
    year = cell_year.groupby("plan_year").agg(
        basis_units=("basis_units", "sum"),
        basis_type=("basis_type", lambda s: "; ".join(sorted(set(s)))),
        mean_growth_assumption=("growth_assumption", "mean"),
        committed_buy_units=("committed_buy_units", "sum"),
        true_units=("true_units", "sum"),
        sold_units=("sold_units", "sum"),
    )
    recon_year = series.dropna(subset=["reconstructed_units"]).groupby("plan_year").reconstructed_units.sum()
    year["prior_year_sold_units"] = year.sold_units.shift(1)
    year["prior_year_true_units"] = year.true_units.shift(1)
    year["prior_year_reconstructed_units"] = recon_year.reindex(year.index).shift(1)
    year["basis_gap_vs_prior_true_pct"] = (year.basis_units / year.prior_year_true_units - 1) * 100
    year["basis_gap_vs_prior_reconstructed_pct"] = (
        year.basis_units / year.prior_year_reconstructed_units - 1
    ) * 100
    year["committed_buy_vs_true_demand"] = year.committed_buy_units / year.true_units
    year["true_demand_growth_pct"] = (year.true_units / year.prior_year_true_units - 1) * 100
    year["basis"] = f"{TRUTH} for true units; {PLANNER} for reconstructed units"
    return year.reset_index()


def loss_split(history: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split lost units into quantity and timing, per cell-year.

    quantity: the plan year's total supply in that cell was below its demand.
    timing:   supply existed within the plan year but arrived after the
              stockout weeks (or sat elsewhere in time).
    """
    keys = ["plan_year"] + CELL
    opening = history.sort_values("week_start").groupby(keys).beginning_inventory_units.first()
    cells = history.groupby(keys).agg(
        true_units=("true_demand_units", "sum"),
        lost_units=("lost_demand_units", "sum"),
        seasonal_units=("seasonal_receipt_units", "sum"),
        replenishment_units=("replenishment_receipt_units", "sum"),
        chase_units=("chase_receipt_units", "sum"),
        restocked_return_units=("return_restock_units", "sum"),
    )
    cells["opening_units"] = opening
    cells["season_supply_units"] = cells[
        ["opening_units", "seasonal_units", "replenishment_units", "chase_units", "restocked_return_units"]
    ].sum(axis=1)
    shortfall = (cells.true_units - cells.season_supply_units).clip(lower=0)
    cells["quantity_lost_units"] = np.minimum(cells.lost_units, shortfall)
    cells["timing_lost_units"] = cells.lost_units - cells.quantity_lost_units
    by_year = cells.groupby("plan_year")[["lost_units", "quantity_lost_units", "timing_lost_units"]].sum()
    by_year["timing_share"] = by_year.timing_lost_units / by_year.lost_units
    by_year["basis"] = TRUTH
    return by_year.reset_index(), cells


def chase_signal(history: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Does the chase lever fire, and order, where the peak losses happen?"""
    keys = ["plan_year"] + CELL
    peak = history.month.isin(PEAK_MONTHS)
    early = history[history.plan_week.between(*CHASE_EARLY_WEEKS)].groupby(keys)[
        ["shipped_units", "weekly_plan_units"]
    ].sum()
    cells = pd.DataFrame({
        "peak_lost_units": history[peak].groupby(keys).lost_demand_units.sum(),
        "first_trigger_plan_week": history[history.chase_triggered_flag == 1].groupby(keys).plan_week.min(),
        "chase_units": history.groupby(keys).chase_receipt_units.sum(),
        "early_shipped_vs_plan": early.shipped_units / early.weekly_plan_units,
        "first_peak_stockout_week": history[
            (history.in_stock_days < 7) & (history.plan_week >= PEAK_BLOCK_START_WEEK)
        ].groupby(keys).plan_week.min(),
        "first_chase_arrival_week": history[history.chase_receipt_units > 0].groupby(keys).plan_week.min(),
    }).fillna({"peak_lost_units": 0.0, "chase_units": 0.0})
    labels = ["Q1 lowest loss", "Q2", "Q3", "Q4 highest loss"]
    cells["peak_loss_quartile"] = pd.qcut(cells.peak_lost_units.rank(method="first"), 4, labels=labels)
    by_quartile = cells.groupby("peak_loss_quartile", observed=True).agg(
        cell_years=("peak_lost_units", "size"),
        mean_peak_lost_units=("peak_lost_units", "mean"),
        chase_trigger_rate=("first_trigger_plan_week", lambda s: s.notna().mean()),
        median_first_trigger_plan_week=("first_trigger_plan_week", "median"),
        mean_chase_units=("chase_units", "mean"),
        median_early_shipped_vs_plan=("early_shipped_vs_plan", "median"),
    )
    by_quartile["basis"] = f"quartiles on {TRUTH}; trigger, chase and shipments are {PLANNER}"

    commitment = history.groupby(keys).committed_buy_units_plan_year.first().groupby("plan_year").sum()
    by_year = pd.DataFrame({
        "chase_units": history.groupby("plan_year").chase_receipt_units.sum(),
        "chase_capacity_units": commitment * CHASE_CAP_SHARE,
        "peak_lost_units": history[peak].groupby("plan_year").lost_demand_units.sum(),
    })
    by_year["chase_used_share_of_commitment"] = by_year.chase_units / commitment
    by_year["unused_chase_capacity_units"] = by_year.chase_capacity_units - by_year.chase_units
    by_year["basis"] = f"{PLANNER}; peak_lost_units is {TRUTH}"

    stocked = cells.dropna(subset=["first_peak_stockout_week"])
    timing = {
        "cell_years_with_peak_stockout": len(stocked),
        "chase_landed_before_first_stockout_share": float(
            (stocked.first_chase_arrival_week < stocked.first_peak_stockout_week).mean()
        ),
        "no_chase_share": float(stocked.first_chase_arrival_week.isna().mean()),
        "median_first_trigger_plan_week": float(cells.first_trigger_plan_week.median()),
        "median_first_peak_stockout_week": float(stocked.first_peak_stockout_week.median()),
    }
    return by_quartile.reset_index(), by_year.reset_index(), timing


def loss_concentration(history: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Where PY2026 lost revenue sits, with an observable cross-check."""
    latest = history[history.plan_year == LATEST_PY].assign(stockout_days=lambda d: 7 - d.in_stock_days)
    cells = latest.groupby(CELL).agg(
        lost_revenue_cad=("lost_revenue_opportunity_cad", "sum"),
        lost_units=("lost_demand_units", "sum"),
        true_units=("true_demand_units", "sum"),
        sold_units=("observed_sales_units", "sum"),
        stockout_days=("stockout_days", "sum"),
    ).sort_values("lost_revenue_cad", ascending=False)
    cells["fill_truth"] = cells.sold_units / cells.true_units
    cells["rank_by_lost_revenue"] = np.arange(1, len(cells) + 1)
    cells["share_of_lost_revenue"] = cells.lost_revenue_cad / cells.lost_revenue_cad.sum()
    cells["cumulative_share"] = cells.share_of_lost_revenue.cumsum()
    cells["rank_by_stockout_days"] = cells.stockout_days.rank(ascending=False, method="min").astype(int)
    # The planner's selection: top 20 by stockout days, ties broken by sales
    # (both observable). Its true lost revenue is a validation, not an input.
    observable_order = cells.sort_values(["stockout_days", "sold_units"], ascending=False, kind="mergesort")
    top20_stockout = set(observable_order.index[:20])
    top20_revenue = set(cells.index[:20])
    cells["in_observable_top20"] = cells.index.isin(list(top20_stockout))
    cells["basis"] = f"lost revenue and fill: {TRUTH}; stockout days and sales: {PLANNER}"
    summary = {
        "cells": len(cells),
        "top20_share_of_lost_revenue": float(cells.share_of_lost_revenue.iloc[:20].sum()),
        "observable_top20_share_of_true_lost_revenue": float(
            cells.loc[cells.in_observable_top20, "share_of_lost_revenue"].sum()),
        "spearman_lost_revenue_vs_stockout_days": float(
            cells.lost_revenue_cad.rank().corr(cells.stockout_days.rank())
        ),
        "top20_overlap_with_stockout_ranking": len(top20_revenue & top20_stockout),
    }
    return cells.reset_index(), summary


def censoring_by_window(series: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """How much reconstruction changes demand in each planning window."""
    rows = []
    for name, (start, end) in WINDOWS.items():
        w = series[series.week_start.between(start, end)]
        sold, recon, true = w.observed_units.sum(), w.reconstructed_units.sum(), w.true_units.sum()
        rows.append({
            "window": name,
            "sold_units": sold,
            "reconstructed_units": recon,
            "true_units": true,
            "reconstructed_vs_sold_pct": (recon / sold - 1) * 100,
            "true_vs_sold_pct": (true / sold - 1) * 100,
            "share_of_true_gap_recovered": (recon - sold) / (true - sold) if true > sold else np.nan,
        })
    windows = pd.DataFrame(rows).assign(basis=f"{PLANNER}; true units are {TRUTH}")
    start, end = WINDOWS["Dec-Feb, PY2026"]
    dec_feb = series[series.week_start.between(start, end)].groupby(SERIES)[
        ["observed_units", "reconstructed_units", "true_units"]
    ].sum()
    dec_feb["reconstructed_vs_sold_pct"] = (dec_feb.reconstructed_units / dec_feb.observed_units - 1) * 100
    dec_feb["true_vs_sold_pct"] = (dec_feb.true_units / dec_feb.observed_units - 1) * 100
    return windows, dec_feb.reset_index()


# --------------------------------------------------------------------------- forward plan

def project_forward(plan: pd.DataFrame, demand_col: str, extra_receipts_col: str | None = None) -> pd.DataFrame:
    """Replicates the Step 6A weekly inventory roll and its P1/P2 tiers.

    available = beginning inventory + committed receipts + restocked returns
    shipped   = min(available, demand); ending = available - shipped
    P1 if 13-week fill < target or 2+ weeks below target; P2 if ending cover
    (ending inventory / last-4-week average demand) < safety-stock weeks.
    Severe-weather and excess tiers are not re-evaluated here.
    """
    rows = []
    for (sku, channel), g in plan.sort_values("forecast_week_start").groupby(SERIES):
        inventory = g.base_beginning_inventory_units.iloc[0]
        fills, shipped_total, demand_total = [], 0.0, 0.0
        for row in g.itertuples(index=False):
            demand = getattr(row, demand_col)
            receipts = row.committed_receipt_units + (getattr(row, extra_receipts_col) if extra_receipts_col else 0.0)
            available = inventory + receipts + row.base_return_restock_units
            shipped = min(available, demand)
            inventory = available - shipped
            fills.append(shipped / demand if demand > 0 else 1.0)
            shipped_total += shipped
            demand_total += demand
        fill_13w = shipped_total / demand_total
        weeks_below = int(sum(f < TARGET_FILL for f in fills))
        cover = inventory / g[demand_col].tail(4).mean()
        if fill_13w < TARGET_FILL or weeks_below >= WEEKLY_EXCEPTION_WEEKS:
            tier = "P1 ESCALATE"
        elif cover < SAFETY_STOCK_WEEKS:
            tier = "P2 PROTECT"
        else:
            tier = "BALANCED"
        rows.append({"sku_id": sku, "channel_id": channel, "demand_13w_units": demand_total,
                     "fill_13w": fill_13w, "worst_weekly_fill": min(fills),
                     "weeks_below_target": weeks_below, "ending_cover_weeks": cover, "tier": tier})
    return pd.DataFrame(rows)


def forward_inputs(series: pd.DataFrame) -> pd.DataFrame:
    """Published 13-week plan plus the alternative inputs used in the tests."""
    plan = pd.read_csv(TRAJECTORY_FILE, parse_dates=["forecast_week_start"])

    def lagged(column: str, weeks: int, name: str) -> pd.DataFrame:
        lag = series[SERIES + ["week_start", column]].copy()
        lag["forecast_week_start"] = lag.week_start + pd.Timedelta(weeks=weeks)
        return lag.drop(columns="week_start").rename(columns={column: name})

    for column, weeks, name in [("reconstructed_units", 52, "naive_reconstructed"),
                                ("reconstructed_units", 104, "reconstructed_two_years_ago"),
                                ("observed_units", 52, "naive_sales"),
                                ("replenishment_units", 52, "replenishment_last_year")]:
        plan = plan.merge(lagged(column, weeks, name), on=SERIES + ["forecast_week_start"], how="left")
    plan["two_year_average"] = (plan.naive_reconstructed + plan.reconstructed_two_years_ago) / 2
    plan["replenishment_forward"] = plan.replenishment_last_year * (1 + plan.sku_id.map(SKU_GROWTH))
    needed = ["naive_reconstructed", "reconstructed_two_years_ago", "naive_sales", "replenishment_last_year"]
    if plan[needed].isna().any().any():
        raise ValueError("Missing history for a forward-plan comparison.")
    return plan


def forward_counterfactuals(plan: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Change one input at a time and count series whose planner action changes."""
    published = pd.read_csv(SERIES_DECISION_FILE)[SERIES + ["priority_tier"]]
    base = project_forward(plan, "base_forecast_units")
    check = base.merge(published, on=SERIES)
    if not (check.tier.str[:2] == check.priority_tier).all():
        raise ValueError("Forward-plan replica does not reproduce the published Step 6A tiers.")

    cases = {
        "Published: champion ETS forecast": ("base_forecast_units", None, "none"),
        "Mild weather scenario": ("mild_scenario_forecast_units", None, "weather"),
        "Severe weather scenario": ("severe_scenario_forecast_units", None, "weather"),
        "Seasonal naive on reconstructed demand": ("naive_reconstructed", None, "forecast model"),
        "Seasonal naive on raw sales (no stockout correction)": ("naive_sales", None, "stockout correction"),
        "Seasonal two-year average": ("two_year_average", None, "forecast model"),
        "Published forecast, last year's replenishment added to supply": (
            "base_forecast_units", "replenishment_forward", "supply view"),
    }
    # The stockout-correction test compares like with like: the same naive
    # model on raw sales vs on reconstructed demand. Every other case is
    # compared with the published plan.
    reference_case = {"Seasonal naive on raw sales (no stockout correction)": "Seasonal naive on reconstructed demand"}
    results = {name: project_forward(plan, demand_col, extra_col).assign(case=name)
               for name, (demand_col, extra_col, _) in cases.items()}
    summary, tiers = [], []
    for name, (demand_col, extra_col, input_changed) in cases.items():
        result = results[name]
        tiers.append(result)
        reference = results[reference_case.get(name, "Published: champion ETS forecast")]
        changed = (result.tier.values != reference.tier.values).sum()
        summary.append({
            "case": name, "input_changed": input_changed,
            "compared_with": reference_case.get(name, "Published: champion ETS forecast"),
            "demand_13w_units": result.demand_13w_units.sum(),
            "demand_vs_published_pct": (result.demand_13w_units.sum() / base.demand_13w_units.sum() - 1) * 100,
            "p1_escalate_series": int(result.tier.str.startswith("P1").sum()),
            "p2_protect_series": int(result.tier.str.startswith("P2").sum()),
            "balanced_series": int((result.tier == "BALANCED").sum()),
            "series_whose_action_changes": int(changed),
            "escalated_series": ", ".join(f"{r.sku_id} {r.channel_id}" for r in result.itertuples() if r.tier.startswith("P1")),
        })
    out = pd.DataFrame(summary).assign(basis=PLANNER)
    return out, pd.concat(tiers, ignore_index=True)


def corrected_queue(plan: pd.DataFrame) -> pd.DataFrame:
    """S&OE queue with replenishment in supply and flags tested across the forecast's error band.

    The band is the published forecast x (1 -/+ the champion's backtest WAPE).
    ESCALATE: shortfall even at the low end. WATCH: shortfall only at the
    high end. PROTECT: cover below policy at the published forecast.
    """
    wape = pd.read_csv(CHAMPION_FILE).set_index(SERIES).champion_wape_pct / 100
    banded = plan.join(wape.rename("wape"), on=SERIES)
    banded["demand_low"] = banded.base_forecast_units * (1 - banded.wape)
    banded["demand_high"] = banded.base_forecast_units * (1 + banded.wape)
    published = project_forward(plan, "base_forecast_units")
    low = project_forward(banded, "demand_low", "replenishment_forward")
    mid = project_forward(banded, "base_forecast_units", "replenishment_forward")
    high = project_forward(banded, "demand_high", "replenishment_forward")
    out = published[SERIES + ["tier"]].rename(columns={"tier": "published_tier"})
    out["wape_band"] = out.set_index(SERIES).index.map(wape).values
    out["fill_13w_high_demand"] = high.fill_13w.values
    out["worst_weekly_fill_high_demand"] = high.worst_weekly_fill.values
    out["ending_cover_weeks"] = mid.ending_cover_weeks.values
    out["corrected_action"] = np.select(
        [low.tier.str.startswith("P1").values, high.tier.str.startswith("P1").values,
         (mid.ending_cover_weeks < SAFETY_STOCK_WEEKS).values],
        ["ESCALATE", "WATCH", "PROTECT"], default="NO ACTION")
    out["basis"] = PLANNER
    return out


# --------------------------------------------------------------------------- recommendation (planner view only)

def _peak_cells(history: pd.DataFrame) -> pd.DataFrame:
    """Observable inputs per SKU x region x channel for the peak buy."""
    latest = history[history.plan_year == LATEST_PY]
    start, end = WINDOWS["Dec-Feb, PY2026"]
    peak = latest[latest.week_start.between(start, end)].assign(stockout_days=lambda d: 7 - d.in_stock_days)
    cells = peak.groupby(CELL).agg(peak_stockout_days=("stockout_days", "sum"),
                                   peak_sold_units=("observed_sales_units", "sum"))
    season_end = latest[latest.week_start == latest.week_start.max()]
    cells["season_end_stock_units"] = season_end.groupby(CELL).ending_inventory_units.sum()
    cells["spring_replenishment_units"] = (
        latest[latest.month.isin(SPRING_MONTHS)].groupby(CELL).replenishment_receipt_units.sum()
    )
    return cells.fillna(0.0).reset_index()


def _allocate_change(cells: pd.DataFrame, change: pd.Series, blocks_new: pd.Series) -> pd.DataFrame:
    """Allocate each series' change to regions, then split it into moved and new units.

    Regions receive the change in proportion to their Dec-Feb stockout days
    (by sales if a series had none). In each region, stock that was still
    unsold at season end and had arrived as spring replenishment can be moved
    into the pre-peak delivery. The rest is new units, unless the guardrail
    blocks new units for the series, in which case it is an accepted gap.
    """
    out = cells.merge(change.rename("series_change").reset_index(), on=SERIES)
    out = out.merge(blocks_new.rename("blocks_new").reset_index(), on=SERIES)
    stockout_total = out.groupby(SERIES).peak_stockout_days.transform("sum")
    sales_total = out.groupby(SERIES).peak_sold_units.transform("sum")
    weight = np.where(stockout_total > 0, out.peak_stockout_days / stockout_total.where(stockout_total > 0, 1),
                      out.peak_sold_units / sales_total)
    out["allocated_change_units"] = np.round(out.series_change * weight)
    out["movable_units"] = np.floor(np.minimum(out.season_end_stock_units, out.spring_replenishment_units))
    out["moved_units"] = np.minimum(out.allocated_change_units, out.movable_units)
    remainder = out.allocated_change_units - out.moved_units
    out["new_units"] = np.where(out.blocks_new, 0.0, remainder)
    out["accepted_gap_units"] = remainder - out.new_units
    return out.drop(columns=["series_change", "blocks_new"])


def _call(moved: pd.Series, new: pd.Series) -> pd.Series:
    """Name the action from the quantities, so the label can never contradict them."""
    labels = np.select([(new > 0) & (moved > 0), new > 0, moved > 0],
                       ["Buy and re-time", "Buy only", "Re-time only"], default="No change")
    return pd.Series(labels, index=moved.index)


def peak_buy_recommendation(series: pd.DataFrame, history: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Indicative next-peak scenario by SKU x channel, from observable data only.

    1. Gap: last season's Dec-Feb reconstructed demand minus sales, grown by
       the SKU growth assumption.
    2. Allocate it to regions by Dec-Feb stockout days (they rank with lost
       revenue at rho 0.90; see Loss_Concentration).
    3. Move before you buy: re-time stock that sat unsold at season end and
       arrived as spring replenishment; only the remainder is new units.
    4. Guardrail: no new units where the inventory-based over-buy exposure is
       already >= GUARDRAIL_OVERBUY_RATIO of estimated lost revenue
       (reconstructed minus sold units for the year, at net price).
    The scenario stays indicative until the open items in
    Peak_Move_Feasibility are confirmed with supply planning.
    """
    start, end = WINDOWS["Dec-Feb, PY2026"]
    latest = history[history.plan_year == LATEST_PY]
    this_year = series[series.plan_year == LATEST_PY]
    rec = (this_year[this_year.week_start.between(start, end)]
           .groupby(SERIES)[["observed_units", "reconstructed_units"]].sum()
           .rename(columns={"observed_units": "decfeb_sold_units",
                            "reconstructed_units": "decfeb_reconstructed_units"}))
    year = this_year.groupby(SERIES)[["observed_units", "reconstructed_units"]].sum()
    rec["gap_units"] = rec.decfeb_reconstructed_units - rec.decfeb_sold_units
    rec["gap_pct_of_sales"] = rec.gap_units / rec.decfeb_sold_units * 100
    rec["growth"] = rec.index.get_level_values("sku_id").map(SKU_GROWTH).to_numpy()
    sold = latest.groupby(SERIES).observed_sales_units.sum()
    rec["net_asp_cad"] = (latest.net_asp_cad * latest.observed_sales_units).groupby(
        [latest.sku_id, latest.channel_id]).sum() / sold
    rec["estimated_lost_revenue_cad"] = (year.reconstructed_units - year.observed_units) * rec.net_asp_cad
    rec["overbuy_exposure_cad"] = latest.groupby(SERIES).total_overbuy_event_exposure_cad.sum()
    rec["overbuy_vs_estimated_lost_revenue"] = rec.overbuy_exposure_cad / rec.estimated_lost_revenue_cad
    rec["guardrail_blocks_new_units"] = rec.overbuy_vs_estimated_lost_revenue >= GUARDRAIL_OVERBUY_RATIO
    regions = _allocate_change(_peak_cells(history), rec.gap_units * (1 + rec.growth), rec.guardrail_blocks_new_units)
    totals = regions.groupby(SERIES)[["allocated_change_units", "moved_units", "new_units", "accepted_gap_units"]].sum()
    rec = rec.join(totals.rename(columns={"allocated_change_units": "change_units"}))
    rec["call"] = _call(rec.moved_units, rec.new_units)
    rec["priority_rank"] = rec.estimated_lost_revenue_cad.rank(ascending=False, method="min").astype(int)
    rec["status"] = "INDICATIVE, evaluated at the 2026-06-29 plan date; open supply checks in Peak_Move_Feasibility"
    rec["basis"] = PLANNER
    regions["basis"] = PLANNER
    return rec.reset_index().sort_values("priority_rank"), regions


def peak_move_feasibility(history: pd.DataFrame, rec: pd.DataFrame) -> pd.DataFrame:
    """Check the scenario against receipt dates and the supply limits DemandIQ models.

    Required arrival: last season's first Dec-Feb stockout week in the series,
    one year on. Moved units are spring replenishment pulled forward, which is
    a purchase-order change; PO-change windows are not modelled, so that stays
    open. New units need a 22-week overseas order by the latest date, or the
    10-week chase lane within its capacity cap.
    """
    latest = history[history.plan_year == LATEST_PY]
    start, end = WINDOWS["Dec-Feb, PY2026"]
    peak = latest[latest.week_start.between(start, end)]
    first_stockout = peak[peak.in_stock_days < 7].groupby(SERIES).week_start.min()
    spring = (latest[latest.month.isin(SPRING_MONTHS)]
              .groupby(SERIES + ["week_start"]).replenishment_receipt_units.sum().reset_index())
    spring["cumulative_share"] = (spring.groupby(SERIES).replenishment_receipt_units.cumsum()
                                  / spring.groupby(SERIES).replenishment_receipt_units.transform("sum"))
    spring_half = spring[spring.cumulative_share >= 0.5].groupby(SERIES).week_start.min()
    commitment = latest.groupby(CELL).committed_buy_units_plan_year.first().groupby(SERIES).sum()
    october_drop = latest[latest.receipt_event_label == "OCT_PEAK"].week_start.min()

    out = rec.set_index(SERIES)[["change_units", "moved_units", "new_units", "call",
                                 "guardrail_blocks_new_units"]].copy()
    out["last_peak_first_stockout"] = first_stockout
    out["required_arrival_next_peak"] = first_stockout + pd.Timedelta(weeks=52)
    out["spring_receipts_half_arrived"] = spring_half
    out["weeks_earlier_for_moved_units"] = (spring_half - first_stockout).dt.days / 7
    out["october_drop_order_date_next_peak"] = october_drop + pd.Timedelta(weeks=52 - OVERSEAS_LEAD_WEEKS)
    out["latest_order_overseas_lane"] = out.required_arrival_next_peak - pd.Timedelta(weeks=OVERSEAS_LEAD_WEEKS)
    out["days_left_at_plan_date_overseas_lane"] = (out.latest_order_overseas_lane - PLAN_AS_OF).dt.days
    out["latest_order_chase_lane"] = out.required_arrival_next_peak - pd.Timedelta(weeks=CHASE_LEAD_WEEKS)
    out["chase_headroom_last_season_units"] = (
        commitment * CHASE_CAP_SHARE - latest.groupby(SERIES).chase_receipt_units.sum())
    out["moved_units_check"] = np.where(
        out.moved_units > 0, "OPEN at plan date: pull spring orders forward; PO-change window not modelled",
        "Not needed")
    out["new_units_check"] = np.select(
        [out.new_units == 0, out.days_left_at_plan_date_overseas_lane >= 0,
         out.new_units <= out.chase_headroom_last_season_units],
        ["Not needed", "OPEN at plan date: 22-week order possible; supplier capacity not modelled",
         "At plan date: chase lane, within last season's unused capacity"],
        default="OPEN at plan date: exceeds chase capacity; needs supplier capacity")
    out["new_units_fit_chase_headroom"] = out.new_units <= out.chase_headroom_last_season_units
    # Floor: if neither a PO change nor a new 22-week order is possible, only
    # chase can land before the stockouts, and chase units are new units.
    out["chase_only_units"] = np.where(
        out.guardrail_blocks_new_units, 0.0,
        np.minimum(out.moved_units + out.new_units, np.floor(out.chase_headroom_last_season_units.clip(lower=0))))
    out["basis"] = PLANNER
    return out.reset_index()


# --------------------------------------------------------------------------- validation (simulation truth)

def peak_buy_validation(rec: pd.DataFrame, history: pd.DataFrame, series: pd.DataFrame,
                        truth_cells: pd.DataFrame) -> pd.DataFrame:
    """Score the planner-view scenario against simulation truth. Never an input to it."""
    start, end = WINDOWS["Dec-Feb, PY2026"]
    peak = series[series.week_start.between(start, end)].groupby(SERIES)[["observed_units", "true_units"]].sum()
    latest = history[history.plan_year == LATEST_PY]
    v = rec.set_index(SERIES)[["gap_units", "change_units", "moved_units", "new_units", "call",
                               "priority_rank", "overbuy_exposure_cad", "estimated_lost_revenue_cad"]].copy()
    v["true_gap_units"] = peak.true_units - peak.observed_units
    v["gap_recovered_share"] = v.gap_units / v.true_gap_units
    v["true_lost_revenue_cad"] = latest.groupby(SERIES).lost_revenue_opportunity_cad.sum()
    v["true_priority_rank"] = v.true_lost_revenue_cad.rank(ascending=False, method="min").astype(int)
    split = truth_cells.loc[LATEST_PY].groupby(SERIES)[["lost_units", "quantity_lost_units"]].sum()
    v["planner_new_share"] = v.new_units / v.change_units
    v["true_quantity_share"] = split.quantity_lost_units / split.lost_units
    growth = v.index.get_level_values("sku_id").map(SKU_GROWTH).to_numpy()
    true_blocks = v.overbuy_exposure_cad / v.true_lost_revenue_cad >= GUARDRAIL_OVERBUY_RATIO
    truth = _allocate_change(_peak_cells(history), v.true_gap_units * (1 + growth), true_blocks)
    truth_totals = truth.groupby(SERIES)[["moved_units", "new_units"]].sum().reindex(v.index)
    v["call_with_true_demand"] = _call(truth_totals.moved_units, truth_totals.new_units)
    v["call_agrees"] = v.call == v.call_with_true_demand
    v["basis"] = TRUTH
    return v.reset_index().sort_values("priority_rank")


def launch_rule() -> dict:
    """Numbers behind the launch reserve-release rule (Steps 7E/7F)."""
    buy = pd.read_csv(LAUNCH_BUY_FILE)
    chosen = buy[buy.recommended_flag == 1].iloc[0]
    actuals = pd.read_csv(LAUNCH_ACTUALS_FILE)
    policy = pd.read_csv(LAUNCH_POLICY_FILE)
    fires = policy[policy.would_trigger == "YES"].sort_values("threshold_pp").iloc[0]
    latent = actuals.latent_demand_units_HIDDEN_EVAL_ONLY.sum()
    return {
        "initial_buy_units": float(chosen.initial_buy_units),
        "reserve_units": float(chosen.reserve_units),
        "latent_demand_units": float(latent),
        "buy_vs_latent_pct": float((chosen.initial_buy_units / latent - 1) * 100),
        "ecom_lost_units": float(actuals.loc[actuals.channel_id == "ECOM", "lost_demand_units"].sum()),
        "trigger_threshold_pp": float(fires.threshold_pp),
        "trigger_checkpoint": str(fires.first_trigger_checkpoint),
        "mix_deviation_pp": float(fires.mix_dev_at_trigger_pp),
    }


# --------------------------------------------------------------------------- charts

def _style(ax: plt.Axes) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=10, length=0)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _title(fig: plt.Figure, title: str, subtitle: str) -> None:
    fig.text(0.02, 0.95, title, fontsize=13.5, fontweight="bold", color=INK, ha="left", va="top")
    fig.text(0.02, 0.885, subtitle, fontsize=10.5, color=INK_2, ha="left", va="top")


def chart_fill_trend(trend: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.4), dpi=160, facecolor=SURFACE)
    _style(ax)
    years = trend.plan_year.tolist()
    x = np.arange(len(years))
    annual, peak = trend.annual_fill_truth * 100, trend.peak_fill_truth * 100
    ax.axhline(TARGET_FILL * 100, color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(x[0] - 0.1, TARGET_FILL * 100 - 1.4, "92% service target", color=INK_2, fontsize=9.5)
    ax.plot(x, annual, color=DATA_GREY, linewidth=2, marker="o", markersize=5, label="Annual fill")
    ax.plot(x, peak, color=ACCENT, linewidth=2.4, marker="o", markersize=6, label="Dec–Feb fill")
    for series_values, color, weight, name in [(annual, INK_2, "normal", "Annual"), (peak, INK, "bold", "Dec–Feb")]:
        ax.text(x[-1] + 0.12, series_values.iloc[-1], f"{name} {series_values.iloc[-1]:.1f}%",
                va="center", fontsize=10, color=color, fontweight=weight)
        ax.text(x[0], series_values.iloc[0] + 1.4, f"{series_values.iloc[0]:.1f}%",
                ha="center", fontsize=9.5, color=color, fontweight=weight)
    ax.set_xticks(x, years)
    ax.set_xlim(-0.4, len(years) - 1 + 1.25)
    ax.set_ylim(70, 100)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.legend(loc="lower left", frameon=False, fontsize=9.5, labelcolor=INK_2)
    lost0, lost1 = trend.lost_revenue_cad.iloc[0] / 1e6, trend.lost_revenue_cad.iloc[-1] / 1e6
    _title(fig, f"Peak-season fill fell from {peak.iloc[0]:.0f}% to {peak.iloc[-1]:.0f}% in four plan years",
           f"Lost-sales exposure rose from CAD {lost0:.1f}M to {lost1:.1f}M a year · simulated history, units sold ÷ true demand")
    fig.subplots_adjust(top=0.80, bottom=0.1, left=0.08, right=0.97)
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def chart_lost_by_month(history: pd.DataFrame, path: Path) -> None:
    order = [7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6]
    names = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    lost = history.groupby("month").lost_demand_units.sum().reindex(order)
    share = lost / lost.sum() * 100
    window_share = share.loc[[7, 8, 9]].sum()
    peak_share = share.loc[list(PEAK_MONTHS)].sum()
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=160, facecolor=SURFACE)
    _style(ax)
    x = np.arange(len(order))
    ax.axvspan(-0.5, 2.5, color=GRID, alpha=0.6, linewidth=0)
    ax.text(1, 34, "13-week S&OE window\nJun 29–Sep 21", ha="center", fontsize=9.5, color=INK_2)
    colors = [ACCENT if m in PEAK_MONTHS else DATA_GREY for m in order]
    ax.bar(x, share.values, width=0.5, color=colors)
    for xi, value, month in zip(x, share.values, order):
        ax.text(xi, value + 0.6, f"{value:.1f}", ha="center", fontsize=9,
                color=INK if month in PEAK_MONTHS else INK_2, fontweight="bold" if month in PEAK_MONTHS else "normal")
    ax.set_xticks(x, names)
    ax.set_ylim(0, 40)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    _title(fig, f"{peak_share:.0f}% of lost demand falls in Dec–Feb; the S&OE window holds {window_share:.1f}%",
           "Share of simulated lost units by month, plan years PY2022–PY2026")
    fig.subplots_adjust(top=0.80, bottom=0.1, left=0.08, right=0.97)
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def chart_forward_sensitivity(counterfactuals: pd.DataFrame, path: Path) -> None:
    def changed(cases: list[str]) -> int:
        return int(counterfactuals.set_index("case").loc[cases, "series_whose_action_changes"].max())

    rows = [
        ("Weather scenario", changed(["Mild weather scenario", "Severe weather scenario"])),
        ("Stockout correction", changed(["Seasonal naive on raw sales (no stockout correction)"])),
        ("Forecast model (ETS vs naive)", changed(["Seasonal naive on reconstructed demand"])),
        ("Supply view (+ replenishment)",
         changed(["Published forecast, last year's replenishment added to supply"])),
    ]
    fig, ax = plt.subplots(figsize=(8, 3.6), dpi=160, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(AXIS)
    ax.tick_params(colors=INK_2, labelsize=10, length=0)
    y = np.arange(len(rows))[::-1]
    values = [v for _, v in rows]
    colors = [ACCENT if v == max(values) else DATA_GREY for v in values]
    ax.barh(y, values, height=0.42, color=colors)
    for yi, value in zip(y, values):
        ax.text(value + 0.12, yi, f"{value} of 9", va="center", fontsize=10,
                color=INK if value == max(values) else INK_2, fontweight="bold" if value == max(values) else "normal")
    ax.set_yticks(y, [name for name, _ in rows])
    ax.set_xlim(0, 9)
    ax.set_xticks([])
    _title(fig, "The 13-week queue moves with supply, not forecasting technique",
           "Series whose planner action changes when one input is changed (of 9)")
    fig.subplots_adjust(top=0.76, bottom=0.05, left=0.30, right=0.97)
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


# --------------------------------------------------------------------------- run

def _date(value: pd.Timestamp) -> str:
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def headline_metrics(trend, basis, split, quartiles, chase_years, chase_timing, concentration,
                     windows, counterfactuals, queue, launch, recommendation, feasibility,
                     validation) -> pd.DataFrame:
    """Every headline number, with its evidence basis and its role.

    DIAGNOSIS sizes and explains the problem; RECOMMENDATION is computed from
    PLANNER_VIEW data only; VALIDATION scores the recommendation against
    SIMULATION_TRUTH.
    """
    t = trend.set_index("plan_year")
    b = basis.set_index("plan_year")
    s = split.set_index("plan_year")
    c = chase_years.set_index("plan_year")
    w = windows.set_index("window")
    cf = counterfactuals.set_index("case")
    q = quartiles.set_index("peak_loss_quartile")
    rec, f, v = recommendation, feasibility, validation
    buying = f[f.new_units > 0]
    top3_planner = set(rec.nsmallest(3, "priority_rank")[SERIES].apply(tuple, axis=1))
    top3_truth = set(v.nsmallest(3, "true_priority_rank")[SERIES].apply(tuple, axis=1))
    plan_rows = [
        ("Indicative next-peak change", rec.change_units.sum(), "units", PLANNER),
        ("  of which moved forward from spring replenishment", rec.moved_units.sum(), "units", PLANNER),
        ("  of which new units", rec.new_units.sum(), "units", PLANNER),
        ("  of which accepted gap (guardrail blocks new units)", rec.accepted_gap_units.sum(), "units", PLANNER),
        ("Series: re-time only", int((rec.call == "Re-time only").sum()), "of 9", PLANNER),
        ("Series: buy and re-time", int((rec.call == "Buy and re-time").sum()), "of 9", PLANNER),
        ("Series where the guardrail blocks new units", int(rec.guardrail_blocks_new_units.sum()), "of 9", PLANNER),
        ("Regular October-drop order date for the next peak", _date(f.october_drop_order_date_next_peak.iloc[0]), "date", PLANNER),
        ("Plan as-of date", _date(PLAN_AS_OF), "date", PLANNER),
        ("Latest 22-week order date for the next peak, earliest series", _date(f.latest_order_overseas_lane.min()), "date", PLANNER),
        ("Series needing new units that fit last season's chase headroom", f"{int(buying.new_units_fit_chase_headroom.sum())} of {len(buying)}", "series", PLANNER),
        ("Chase-only floor at the plan date (orders due by 2026-09-21 or 2026-10-05)", f.chase_only_units.sum(), "units", PLANNER),
    ]
    validation_rows = [
        ("Planner Dec-Feb gap as share of true gap", rec.gap_units.sum() / v.true_gap_units.sum() * 100, "%", TRUTH),
        ("Calls unchanged when recomputed with true demand", int(v.call_agrees.sum()), "of 9", TRUTH),
        ("Top 20 cells by stockout days (observable selection), share of true lost revenue", concentration["observable_top20_share_of_true_lost_revenue"] * 100, "%", f"{PLANNER} selection; {TRUTH} value"),
        ("Top-3 priority series shared with the true ranking", len(top3_planner & top3_truth), "of 3", TRUTH),
        ("New-unit share of the change, planner view", rec.new_units.sum() / rec.change_units.sum() * 100, "%", PLANNER),
        ("Quantity share of lost units, simulation truth", s.loc[LATEST_PY, "quantity_lost_units"] / s.loc[LATEST_PY, "lost_units"] * 100, "%", TRUTH),
    ]
    rows = [
        ("Dec-Feb fill, PY2022", t.loc["PY2022", "peak_fill_truth"] * 100, "%", TRUTH),
        ("Dec-Feb fill, PY2026", t.loc[LATEST_PY, "peak_fill_truth"] * 100, "%", TRUTH),
        ("Dec-Feb fill on reconstructed demand, PY2026", t.loc[LATEST_PY, "peak_fill_planner_view"] * 100, "%", PLANNER),
        ("Annual fill, PY2026", t.loc[LATEST_PY, "annual_fill_truth"] * 100, "%", TRUTH),
        ("Lost revenue, PY2022", t.loc["PY2022", "lost_revenue_cad"], "CAD", TRUTH),
        ("Lost revenue, PY2026", t.loc[LATEST_PY, "lost_revenue_cad"], "CAD", TRUTH),
        ("Lost revenue as share of net revenue, PY2026", t.loc[LATEST_PY, "lost_revenue_share_of_net_revenue"] * 100, "%", TRUTH),
        ("Share of PY2026 lost units in Dec-Feb", t.loc[LATEST_PY, "peak_share_of_lost_units"] * 100, "%", TRUTH),
        ("Buy basis vs prior-year true demand, PY2023", b.loc["PY2023", "basis_gap_vs_prior_true_pct"], "%", TRUTH),
        ("Buy basis vs prior-year true demand, PY2026", b.loc[LATEST_PY, "basis_gap_vs_prior_true_pct"], "%", TRUTH),
        ("Buy basis vs prior-year reconstructed demand, PY2026", b.loc[LATEST_PY, "basis_gap_vs_prior_reconstructed_pct"], "%", PLANNER),
        ("Timing share of PY2026 lost units", s.loc[LATEST_PY, "timing_share"] * 100, "%", TRUTH),
        ("Chase trigger rate, lowest-loss quartile", q.loc["Q1 lowest loss", "chase_trigger_rate"] * 100, "%", PLANNER),
        ("Chase trigger rate, highest-loss quartile", q.loc["Q4 highest loss", "chase_trigger_rate"] * 100, "%", PLANNER),
        ("Chase units per cell-year, lowest-loss quartile", q.loc["Q1 lowest loss", "mean_chase_units"], "units", PLANNER),
        ("Chase units per cell-year, highest-loss quartile", q.loc["Q4 highest loss", "mean_chase_units"], "units", PLANNER),
        ("Peak lost units per cell-year, highest-loss quartile", q.loc["Q4 highest loss", "mean_peak_lost_units"], "units", TRUTH),
        ("Median first chase trigger, plan week", chase_timing["median_first_trigger_plan_week"], "week", PLANNER),
        ("Median first peak stockout, plan week", chase_timing["median_first_peak_stockout_week"], "week", PLANNER),
        ("Unused chase capacity, PY2026", c.loc[LATEST_PY, "unused_chase_capacity_units"], "units", PLANNER),
        ("Peak lost units, PY2026", c.loc[LATEST_PY, "peak_lost_units"], "units", TRUTH),
        ("Top 20 cells by true lost revenue, share of PY2026 lost revenue", concentration["top20_share_of_lost_revenue"] * 100, "%", TRUTH),
        ("Rank correlation: lost revenue vs stockout days", concentration["spearman_lost_revenue_vs_stockout_days"], "rho", PLANNER),
        ("Top-20 cells by lost revenue also top 20 by stockout days", concentration["top20_overlap_with_stockout_ranking"], "of 20", PLANNER),
        ("Series changed: stockout correction (naive on sales vs reconstructed)", cf.loc["Seasonal naive on raw sales (no stockout correction)", "series_whose_action_changes"], "of 9", PLANNER),
        ("Reconstruction uplift, S&OE window last year", w.loc["S&OE window, last year (Jun 30-Sep 22, 2025)", "reconstructed_vs_sold_pct"], "%", PLANNER),
        ("Reconstruction uplift, Dec-Feb PY2026", w.loc["Dec-Feb, PY2026", "reconstructed_vs_sold_pct"], "%", PLANNER),
        ("Share of true Dec-Feb gap recovered by reconstruction", w.loc["Dec-Feb, PY2026", "share_of_true_gap_recovered"] * 100, "%", TRUTH),
        ("Series changed: weather scenario", cf.loc[["Mild weather scenario", "Severe weather scenario"], "series_whose_action_changes"].max(), "of 9", PLANNER),
        ("Series changed: seasonal naive instead of ETS", cf.loc["Seasonal naive on reconstructed demand", "series_whose_action_changes"], "of 9", PLANNER),
        ("Series changed: replenishment added to supply", cf.loc["Published forecast, last year's replenishment added to supply", "series_whose_action_changes"], "of 9", PLANNER),
        ("Corrected queue: ESCALATE", int((queue.corrected_action == "ESCALATE").sum()), "series", PLANNER),
        ("Corrected queue: WATCH", int((queue.corrected_action == "WATCH").sum()), "series", PLANNER),
        ("Launch buy vs latent demand", launch["buy_vs_latent_pct"], "%", TRUTH),
        ("Launch ECOM lost units with reserve idle", launch["ecom_lost_units"], "units", TRUTH),
        ("Launch reserve units", launch["reserve_units"], "units", PLANNER),
    ]
    table = ([(*row, DIAGNOSIS) for row in rows] + [(*row, RECOMMENDATION) for row in plan_rows]
             + [(*row, VALIDATION) for row in validation_rows])
    out = pd.DataFrame(table, columns=["metric", "value", "unit", "basis", "role"])
    out["value"] = [round(float(x), 3) if isinstance(x, (int, float, np.integer, np.floating)) else x
                    for x in out.value]
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    history = read_history()
    series = read_series_history(history)

    trend = fill_trend(history, series)
    basis = buy_basis(history, series)
    split, cells = loss_split(history)
    quartiles, chase_years, chase_timing = chase_signal(history)
    concentration_cells, concentration = loss_concentration(history)
    windows, dec_feb_series = censoring_by_window(series)
    plan = forward_inputs(series)
    counterfactuals, counterfactual_tiers = forward_counterfactuals(plan)
    queue = corrected_queue(plan)
    recommendation, recommendation_regions = peak_buy_recommendation(series, history)
    feasibility = peak_move_feasibility(history, recommendation)
    validation = peak_buy_validation(recommendation, history, series, cells)
    launch = launch_rule()
    metrics = headline_metrics(trend, basis, split, quartiles, chase_years, chase_timing, concentration,
                               windows, counterfactuals, queue, launch, recommendation, feasibility,
                               validation)

    outputs = {
        "DemandIQ_Step8_Fill_Trend.csv": trend,
        "DemandIQ_Step8_Buy_Basis.csv": basis,
        "DemandIQ_Step8_Loss_Quantity_vs_Timing.csv": split,
        "DemandIQ_Step8_Chase_Signal_by_Loss_Quartile.csv": quartiles,
        "DemandIQ_Step8_Chase_Capacity_by_Year.csv": chase_years,
        "DemandIQ_Step8_Loss_Concentration_PY2026.csv": concentration_cells,
        "DemandIQ_Step8_Censoring_by_Window.csv": windows,
        "DemandIQ_Step8_DecFeb_Censoring_by_Series.csv": dec_feb_series,
        "DemandIQ_Step8_Forward_Plan_Counterfactuals.csv": counterfactuals,
        "DemandIQ_Step8_Forward_Plan_Tiers_by_Case.csv": counterfactual_tiers,
        "DemandIQ_Step8_Corrected_SOE_Queue.csv": queue,
        "DemandIQ_Step8_Peak_Buy_Recommendation.csv": recommendation,
        "DemandIQ_Step8_Peak_Buy_by_Region.csv": recommendation_regions,
        "DemandIQ_Step8_Peak_Move_Feasibility.csv": feasibility,
        "DemandIQ_Step8_Peak_Buy_Validation.csv": validation,
        "DemandIQ_Step8_Headline_Metrics.csv": metrics,
    }
    for name, frame in outputs.items():
        numeric = frame.select_dtypes("number").columns
        frame.round({column: 4 for column in numeric}).to_csv(OUT_DIR / name, index=False, date_format="%Y-%m-%d")

    chart_fill_trend(trend, CHART_DIR / "step8_fill_trend.png")
    chart_lost_by_month(history, CHART_DIR / "step8_lost_demand_by_month.png")
    chart_forward_sensitivity(counterfactuals, CHART_DIR / "step8_forward_plan_sensitivity.png")

    pd.set_option("display.width", 200)
    print(metrics.to_string(index=False))
    print(f"\nWrote {len(outputs)} files to {OUT_DIR.relative_to(ROOT)} and 3 charts to {CHART_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
