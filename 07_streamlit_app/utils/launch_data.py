"""Governed, cached data layer for Page 6 — New Product Launch Planning (Step 7G).

Reads the FROZEN Step 7B–7F launch outputs. Contains no forecasting, buy, or
reforecast logic and writes no file. Only presentation transformations
(sum / groupby / pivot / filter / ratio / reshape) are performed here.

Governance highlights:
  - `latent_demand_units_HIDDEN_EVAL_ONLY` is QUARANTINED: the operational
    loader drops it; a separate explicit accessor exposes it for the
    evaluation-only toggle only. It never feeds a KPI.
  - `STEP7E_SUPPLY_CONTEXT` is DISPLAY METADATA ONLY (text-sourced from the
    frozen Step 7E decision record). It is never used in any calculation.
  - Reuses the frozen data_loader primitives (`_read`, `DataLoadError`,
    `PROJECT_ROOT`, `_cache`) — data_loader.py itself is not modified.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

from utils.data_loader import _read, DataLoadError, PROJECT_ROOT, _cache

# ------------------------------------------------------------------
# Frozen Step 7B–7F output paths (resolved from PROJECT_ROOT)
# ------------------------------------------------------------------
_OUT = PROJECT_ROOT / "05_outputs"
DIR_7B = _OUT / "launch_step7b"
DIR_7C = _OUT / "launch_step7c"
DIR_7D = _OUT / "launch_step7d"
DIR_7E = _OUT / "launch_step7e"
DIR_7F = _OUT / "launch_step7f"

P_SCORECARD = DIR_7B / "DemandIQ_Step7B_Analog_Scorecard.csv"
P_ASSUMPTIONS = DIR_7B / "DemandIQ_Step7B_Launch_Assumptions.csv"
P_18M = DIR_7C / "DemandIQ_Step7C_18M_Analytical_Forecast.csv"
P_VERSIONS = DIR_7D / "DemandIQ_Step7D_Forecast_Versions.csv"
P_BUY = DIR_7E / "DemandIQ_Step7E_Initial_Buy_Plan.csv"
P_WEEKLY = DIR_7E / "DemandIQ_Step7E_Launch_Weekly_Actuals.csv"
P_CHECK = DIR_7E / "DemandIQ_Step7E_Checkpoint_Reforecast.csv"
P_DECIS = DIR_7E / "DemandIQ_Step7E_Planner_Decisions.csv"
P_FVA = DIR_7F / "DemandIQ_Step7F_FVA_Analysis.csv"
P_CYCLE02 = DIR_7F / "DemandIQ_Step7F_Cycle02_Rolling_Forecast.csv"
P_HANDOFF = DIR_7F / "DemandIQ_Step7F_Lifecycle_Handoff.csv"
P_POLICY = DIR_7F / "DemandIQ_Step7F_Policy_Sensitivity.csv"

CHANNELS = ["ECOM", "RETAIL", "WHOLESALE"]
LATENT_COL = "latent_demand_units_HIDDEN_EVAL_ONLY"

# DISPLAY METADATA ONLY — text-sourced from the frozen Step 7E decision record,
# NOT a CSV column. Never used in any Page-6 calculation, forecast, or decision.
STEP7E_SUPPLY_CONTEXT = {
    "effective_replenishment_lead": "~8 weeks",
    "chase_capacity": "<=15% of initial buy",
    "source": "Frozen Step 7E Launch Execution Decision Record",
    "provenance": "SYNTHETIC SUPPLY PLANNING ASSUMPTION",
}


# ==================================================================
# Loaders (cached). Each validates required columns via the frozen _read.
# ==================================================================
@_cache
def load_scorecard() -> pd.DataFrame:
    df = _read(P_SCORECARD, "Step 7B Analog Scorecard",
               {"candidate", "rank", "final_score"})
    return df.sort_values("final_score", ascending=False).reset_index(drop=True)


@_cache
def load_assumptions() -> dict:
    df = _read(P_ASSUMPTIONS, "Step 7B Launch Assumptions",
               {"assumption_name", "value"})
    return dict(zip(df["assumption_name"], df["value"]))


@_cache
def load_v0_18m() -> pd.DataFrame:
    """V0 analytical baseline, BASE/NORMAL, Month × Channel."""
    df = _read(P_18M, "Step 7C 18-Month Analytical Forecast",
               {"planning_month", "channel_id", "analytical_baseline_units",
                "launch_scenario", "weather_scenario", "lifecycle_phase"})
    v0 = df[(df["launch_scenario"] == "BASE") & (df["weather_scenario"] == "NORMAL")].copy()
    return v0[["planning_month", "channel_id", "analytical_baseline_units",
               "lifecycle_phase"]].reset_index(drop=True)


@_cache
def load_versions() -> pd.DataFrame:
    """V0/V1/V2/V3 monthly forecast, Version × Month × Channel."""
    return _read(P_VERSIONS, "Step 7D Forecast Versions",
                 {"forecast_version", "planning_month", "channel_id", "forecast_units"})


@_cache
def load_buy() -> pd.Series:
    """The frozen recommended (BALANCED) initial-buy row."""
    df = _read(P_BUY, "Step 7E Initial Buy Plan",
               {"buy_position", "recommended_flag", "initial_buy_units", "reserve_units",
                "covered_demand_units", "buffer_units", "buffer_pct",
                "alloc_ecom", "alloc_retail", "alloc_wholesale"})
    rec = df[df["recommended_flag"] == 1]
    if len(rec) != 1:
        raise DataLoadError(
            f"Step 7E buy plan must have exactly one recommended row, found {len(rec)}.")
    return rec.iloc[0]


@_cache
def _weekly_raw() -> pd.DataFrame:
    return _read(P_WEEKLY, "Step 7E Launch Weekly Actuals",
                 {"launch_week_number", "week_start", "channel_id",
                  "planned_units_approved", "observed_sales_units",
                  "lost_demand_units", "stockout_flag"})


def load_launch_actuals() -> pd.DataFrame:
    """OPERATIONAL weekly actuals with the hidden latent column DROPPED (quarantine)."""
    df = _weekly_raw().copy()
    if LATENT_COL in df.columns:
        df = df.drop(columns=[LATENT_COL])
    df["week_start"] = pd.to_datetime(df["week_start"])
    return df


def load_launch_latent_eval_only() -> pd.DataFrame:
    """EVALUATION-ONLY hidden latent demand. The ONLY accessor for the latent column.

    Used solely behind the default-off Page-6 toggle. Never call from a KPI path.
    """
    df = _weekly_raw()
    if LATENT_COL not in df.columns:
        raise DataLoadError("Latent evaluation column missing from Step 7E weekly actuals.")
    out = df[["launch_week_number", "week_start", "channel_id", LATENT_COL]].copy()
    out["week_start"] = pd.to_datetime(out["week_start"])
    return out.rename(columns={LATENT_COL: "latent_units"})


@_cache
def load_checkpoints() -> pd.DataFrame:
    return _read(P_CHECK, "Step 7E Checkpoint Reforecast",
                 {"forecast_version", "remaining_horizon_units"})


@_cache
def load_planner_decisions() -> pd.DataFrame:
    return _read(P_DECIS, "Step 7E Planner Decisions",
                 {"checkpoint", "attainment_pct", "reforecast_total_units",
                  "max_channel_mix_dev_pp", "max_dev_channel", "exception_status",
                  "planner_action"})


@_cache
def load_fva() -> pd.DataFrame:
    return _read(P_FVA, "Step 7F FVA Analysis",
                 {"forecast_stage", "WAPE", "FVA_WAPE_pp", "FVA_status",
                  "evaluation_start", "evaluation_end"})


@_cache
def load_cycle02() -> pd.DataFrame:
    return _read(P_CYCLE02, "Step 7F Cycle-02 Rolling Forecast",
                 {"planning_month", "channel_id", "previous_cycle_units",
                  "cycle02_units", "revision_pct", "forecast_version", "lifecycle_phase"})


@_cache
def load_handoff() -> pd.Series:
    df = _read(P_HANDOFF, "Step 7F Lifecycle Handoff",
               {"current_lifecycle_status", "observed_weeks", "one_season_history_flag",
                "mature_104w_eligible_flag", "recommended_forecast_method"})
    if len(df) != 1:
        raise DataLoadError(f"Lifecycle handoff must be 1 row, found {len(df)}.")
    return df.iloc[0]


@_cache
def load_policy() -> pd.DataFrame:
    return _read(P_POLICY, "Step 7F Policy Sensitivity",
                 {"threshold_pp", "would_trigger", "reserve_available_units",
                  "reserve_transfer_lead_weeks"})


# ==================================================================
# Presentation-only derived helpers (sum / ratio — never new analytics)
# ==================================================================
PLANNED_MIX = {"ECOM": 0.45, "RETAIL": 0.35, "WHOLESALE": 0.20}  # frozen 7B launch mix


def filter_channel(df: pd.DataFrame, channel: str) -> pd.DataFrame:
    """Single central channel filter. 'ALL' (or falsy) returns the full frame.

    Only subsets frozen rows — never mutates or recomputes any business value.
    """
    if channel and channel != "ALL" and "channel_id" in df.columns:
        return df[df["channel_id"] == channel]
    return df


# backwards-compatible alias
channel_subset = filter_channel


def v3_13w_demand(weekly: pd.DataFrame, channel: str = "ALL") -> float:
    """Approved V3 13-week demand (Σ planned_units_approved), channel-scoped."""
    return float(filter_channel(weekly, channel)["planned_units_approved"].sum())


def observed_total(weekly: pd.DataFrame, channel: str = "ALL") -> float:
    return float(filter_channel(weekly, channel)["observed_sales_units"].sum())


def lost_total(weekly: pd.DataFrame, channel: str = "ALL") -> float:
    return float(filter_channel(weekly, channel)["lost_demand_units"].sum())


def observed_mix_share(weekly: pd.DataFrame, channel: str) -> float:
    """Channel share of TOTAL observed sales (operational; never latent)."""
    tot = float(weekly["observed_sales_units"].sum())
    if not tot or channel in (None, "ALL"):
        return float("nan")
    return observed_total(weekly, channel) / tot


def allocated_buy(buy, channel: str = "ALL") -> float:
    """ALL → frozen initial buy (incl. reserve). Channel → that channel's pre-allocation."""
    if not channel or channel == "ALL":
        return float(buy["initial_buy_units"])
    return float(buy[f"alloc_{channel.lower()}"])


def launch_fill_rate(weekly: pd.DataFrame, channel: str = "ALL") -> float:
    """Observed fill = Σobserved / (Σobserved + Σlost), channel-scoped. Operational (no latent)."""
    w = filter_channel(weekly, channel)
    obs = float(w["observed_sales_units"].sum())
    lost = float(w["lost_demand_units"].sum())
    denom = obs + lost
    return obs / denom if denom else float("nan")


def realized_channel_mix(weekly: pd.DataFrame) -> pd.Series:
    """Observed sales share by channel (operational)."""
    tot = weekly.groupby("channel_id")["observed_sales_units"].sum()
    return tot / tot.sum()


def cycle02_overlap_revision(cycle02: pd.DataFrame, channel: str = "ALL") -> dict:
    """Like-for-like revision over the 17 continuing months (previous_cycle present).

    Uses only CYCLE_02_ANALYTICAL_UPDATE rows where a previous-cycle value exists
    (Oct 2026 → Feb 2028), channel-scoped. Returns totals + pct; pure sum/ratio.
    (Revision % is mix-preserving, so channels match ALL by design — but it is
    genuinely recomputed from the selected channel's rows, not reused.)
    """
    d = cycle02[cycle02["forecast_version"] == "CYCLE_02_ANALYTICAL_UPDATE"].copy()
    d = filter_channel(d, channel)
    d["previous_cycle_units"] = pd.to_numeric(d["previous_cycle_units"], errors="coerce")
    d["cycle02_units"] = pd.to_numeric(d["cycle02_units"], errors="coerce")
    d = d.dropna(subset=["previous_cycle_units"])
    prev = float(d["previous_cycle_units"].sum())
    new = float(d["cycle02_units"].sum())
    months = sorted(d["planning_month"].unique())
    return {"previous_total": prev, "cycle02_total": new,
            "revision_units": new - prev,
            "revision_pct": (new / prev - 1) if prev else float("nan"),
            "n_months": len(months),
            "month_min": months[0] if months else None,
            "month_max": months[-1] if months else None}


def get_launch_data():
    """Load-or-stop: return the full frozen Step 7B–7F bundle for Page 6."""
    import streamlit as st
    try:
        return {
            "scorecard": load_scorecard(),
            "assumptions": load_assumptions(),
            "v0_18m": load_v0_18m(),
            "versions": load_versions(),
            "buy": load_buy(),
            "weekly": load_launch_actuals(),
            "checkpoints": load_checkpoints(),
            "decisions": load_planner_decisions(),
            "fva": load_fva(),
            "cycle02": load_cycle02(),
            "handoff": load_handoff(),
            "policy": load_policy(),
        }
    except DataLoadError as exc:
        st.error(f"**Cannot load the frozen Step 7B–7F launch outputs.**\n\n{exc}")
        st.stop()
