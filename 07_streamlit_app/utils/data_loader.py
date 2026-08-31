"""Governed, cached data-loading layer for the DemandIQ dashboard.

Single source of truth for file paths + loading + validation. Pages 1-4
read the frozen Step 6A semantic layer; Page 5 reads frozen Step 4A/4B/4C
evidence. Nothing here recomputes business logic or writes any file.

If a governed file is missing or malformed, loaders raise `DataLoadError`.
Pages catch it and stop safely (see utils.validation / page modules).
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

try:
    import streamlit as st
    _cache = st.cache_data
except Exception:  # allows import / unit use without a Streamlit runtime
    def _cache(func=None, **_kw):
        if func is None:
            return lambda f: f
        return func


class DataLoadError(Exception):
    """Raised when a governed frozen file is missing or fails validation."""


# ------------------------------------------------------------------
# Paths — resolved robustly from this file, no hardcoded drive letters.
#   utils/ -> 07_streamlit_app/ -> <PROJECT_ROOT>
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DECISION_DIR = PROJECT_ROOT / "05_outputs" / "decision_layer"

EXEC_PATH = DECISION_DIR / "DemandIQ_Step6A_Executive_KPI_Summary.csv"
SERIES_PATH = DECISION_DIR / "DemandIQ_Step6A_Series_Decision_Summary.csv"
WEEKLY_PATH = DECISION_DIR / "DemandIQ_Step6A_Weekly_Planning_Trajectory.csv"

# Page 5 frozen evidence
RECON_PATH = (PROJECT_ROOT / "03_model_evidence" / "step4a_reconstruction"
              / "DemandIQ_Step4A_Method_Comparison.csv")
CHAMPION_PATH = (PROJECT_ROOT / "05_outputs" / "champion_selection"
                 / "DemandIQ_Step4B_Champion_Selection.csv")
WEATHER_PATH = (PROJECT_ROOT / "05_outputs" / "weather_forward"
                / "DemandIQ_Step4C_Forward_Weather_Framework.csv")

# Governed expectations
EXPECTED_SERIES = 9
EXPECTED_WEEKS = 13
EXPECTED_WEEKLY_ROWS = EXPECTED_SERIES * EXPECTED_WEEKS  # 117
ALL_SKUS = ["APS-001", "CTS-001", "IMH-001"]
ALL_CHANNELS = ["ECOM", "RETAIL", "WHOLESALE"]

# Forbidden hidden-truth / generator-only fields (leakage guard)
FORBIDDEN_FIELDS = {
    "true_demand_units", "audit_hidden_demand", "weather_effect_pct",
    "weather_factor", "positive_spike_factor", "negative_shock_factor",
    "noise_factor",
}


def _read(path: Path, label: str, required_cols: set[str]) -> pd.DataFrame:
    if not path.exists():
        raise DataLoadError(
            f"Required {label} file not found:\n{path}\n"
            "The frozen Step 6A / evidence output is missing. "
            "This dashboard does not rebuild upstream steps."
        )
    try:
        df = pd.read_csv(path)
    except Exception as exc:  # malformed
        raise DataLoadError(f"Could not read {label} file:\n{path}\n{exc}") from exc

    missing = required_cols - set(df.columns)
    if missing:
        raise DataLoadError(
            f"{label} file is malformed — missing columns: {sorted(missing)}\n{path}"
        )
    leaked = FORBIDDEN_FIELDS & set(df.columns)
    if leaked:
        raise DataLoadError(
            f"{label} file contains forbidden hidden-truth fields: {sorted(leaked)}"
        )
    return df


# ------------------------------------------------------------------
# Step 6A semantic layer (Pages 1-4)
# ------------------------------------------------------------------

@_cache
def load_executive() -> pd.DataFrame:
    df = _read(EXEC_PATH, "Executive KPI Summary", {
        "base_13w_demand_units", "base_13w_fill_rate", "service_target_fill_rate",
        "p1_weekly_service_risk_series", "p2_low_coverage_risk_series",
        "immediate_chase_release_units", "immediate_reallocation_units",
        "portfolio_decision_status",
    })
    if len(df) != 1:
        raise DataLoadError(
            f"Executive KPI Summary must be exactly 1 row, found {len(df)}."
        )
    return df


@_cache
def load_series() -> pd.DataFrame:
    df = _read(SERIES_PATH, "Series Decision Summary", {
        "sku_id", "channel_id", "risk_type", "priority_tier", "planner_action",
        "action_reason", "base_13w_fill_rate", "min_weekly_base_fill_rate",
        "worst_base_service_week", "worst_week_service_gap_units",
        "weeks_below_service_target", "weekly_service_exception_flag",
        "base_final_wos", "chase_capacity_units",
    })
    if len(df) != EXPECTED_SERIES:
        raise DataLoadError(
            f"Series Decision Summary must be {EXPECTED_SERIES} rows, found {len(df)}."
        )
    df["worst_base_service_week"] = pd.to_datetime(df["worst_base_service_week"])
    return df


@_cache
def load_weekly() -> pd.DataFrame:
    df = _read(WEEKLY_PATH, "Weekly Planning Trajectory", {
        "forecast_week_start", "horizon_week", "sku_id", "channel_id",
        "base_forecast_units", "mild_scenario_forecast_units",
        "severe_scenario_forecast_units", "committed_receipt_units",
        "base_shipped_units", "base_fill_rate", "base_weeks_of_supply",
        "safety_stock_units", "service_target_fill_rate", "priority_tier",
        "risk_type", "planner_action", "weekly_base_fill_below_target_flag",
    })
    if len(df) != EXPECTED_WEEKLY_ROWS:
        raise DataLoadError(
            f"Weekly Trajectory must be {EXPECTED_WEEKLY_ROWS} rows, found {len(df)}."
        )
    df["forecast_week_start"] = pd.to_datetime(df["forecast_week_start"])
    n_weeks = df["forecast_week_start"].nunique()
    n_series = df[["sku_id", "channel_id"]].drop_duplicates().shape[0]
    if n_weeks != EXPECTED_WEEKS or n_series != EXPECTED_SERIES:
        raise DataLoadError(
            f"Weekly Trajectory grain invalid: {n_weeks} weeks x {n_series} series "
            f"(expected {EXPECTED_WEEKS} x {EXPECTED_SERIES})."
        )
    return df


# ------------------------------------------------------------------
# Page 5 frozen evidence
# ------------------------------------------------------------------

@_cache
def load_reconstruction_evidence() -> pd.DataFrame:
    return _read(RECON_PATH, "Step 4A Method Comparison",
                 {"method", "segment", "WAPE", "Bias", "lost_demand_recovery_pct"})


@_cache
def load_champion_evidence() -> pd.DataFrame:
    return _read(CHAMPION_PATH, "Step 4B Champion Selection", {
        "sku_id", "channel_id", "selected_champion", "selected_family",
        "champion_wape_pct", "champion_bias_pct", "governance_override_flag",
        "selection_reason", "evaluation_folds", "forecast_horizon_weeks",
    })


@_cache
def load_weather_evidence() -> pd.DataFrame:
    return _read(WEATHER_PATH, "Step 4C Forward Weather Framework", {
        "horizon_week", "weather_horizon_mode", "nowcast_available_flag",
        "future_realized_weather_used_flag", "sku_mild_policy_cap_pct",
        "sku_severe_policy_cap_pct", "scenario_method", "nowcast_governance",
    })


# ------------------------------------------------------------------
# Filtering helper (Pages 2-4). Empty selection == "All".
#   Filtering only SUBSETS frozen rows; it never recomputes any
#   risk_type / priority_tier / planner_action.
# ------------------------------------------------------------------

def apply_series_filter(df: pd.DataFrame, skus, channels) -> pd.DataFrame:
    out = df
    if skus:
        out = out[out["sku_id"].isin(skus)]
    if channels:
        out = out[out["channel_id"].isin(channels)]
    return out


# ------------------------------------------------------------------
# UI wrappers: load-or-stop. Show a clear error and halt the page
# safely if a governed file is missing/malformed (never substitute).
# ------------------------------------------------------------------

def get_step6a():
    """Return (exec_df, series_df, weekly_df) or stop the page with an error."""
    import streamlit as st
    try:
        return load_executive(), load_series(), load_weekly()
    except DataLoadError as exc:
        st.error(f"**Cannot load the frozen Step 6A decision layer.**\n\n{exc}")
        st.stop()


def get_evidence():
    """Return (reconstruction, champion, weather) evidence or stop with an error."""
    import streamlit as st
    try:
        return (load_reconstruction_evidence(), load_champion_evidence(),
                load_weather_evidence())
    except DataLoadError as exc:
        st.error(f"**Cannot load the frozen Step 4A/4B/4C evidence.**\n\n{exc}")
        st.stop()
