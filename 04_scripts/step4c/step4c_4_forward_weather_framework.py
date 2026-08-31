import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# DEMANDIQ
# STEP 4C.4 — FORWARD WEATHER SCENARIO FRAMEWORK
# CORRECTED SCENARIO CALIBRATION
#
# Purpose:
#
# Build the forward 13-week weather planning framework that
# will later be merged with Step 4D champion forecasts.
#
# Weeks 1–3:
#     NOWCAST_REQUIRED
#
# Weeks 4–13:
#     MILD / NORMAL / SEVERE planning scenarios
#
# IMPORTANT GOVERNANCE:
#
# - No realized future weather is used.
# - NORMAL remains the base statistical forecast: 0%.
# - MILD/SEVERE scenarios are calibrated from historical
#   regional exposure when those conditions ACTUALLY occurred.
#
# This corrects the previous approach, which used P20/P80
# of all net weather adjustments and therefore produced
# overly weak "SEVERE" scenarios.
# ============================================================


# ============================================================
# 1. PATHS
# ============================================================

PROJECT_DIR = Path(
    r"D:\Downloads\DemandIQ"
)

HISTORICAL_OVERLAY_FILE = (
    PROJECT_DIR
    / "05_outputs"
    / "weather_overlay"
    / "DemandIQ_Step4C_Weather_Planning_Overlay.csv"
)

OUTPUT_DIR = (
    PROJECT_DIR
    / "05_outputs"
    / "weather_forward"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "DemandIQ_Step4C_Forward_Weather_Framework.csv"
)


# ============================================================
# 2. FROZEN FORECAST DESIGN
# ============================================================

EXPECTED_FORECAST_ORIGIN = pd.Timestamp(
    "2026-06-22"
)

FORECAST_HORIZON_WEEKS = 13

NOWCAST_HORIZON_WEEKS = 3

EXPECTED_SERIES = 9

EXPECTED_OUTPUT_ROWS = (
    FORECAST_HORIZON_WEEKS
    * EXPECTED_SERIES
)


EXPECTED_SKUS = {
    "APS-001",
    "CTS-001",
    "IMH-001"
}

EXPECTED_CHANNELS = {
    "ECOM",
    "RETAIL",
    "WHOLESALE"
}


# ============================================================
# 3. SEASONAL ANALOG GOVERNANCE
#
# Start with:
#     same ISO week ± 2 weeks
#
# If too few scenario-specific observations exist,
# gradually widen to:
#
#     ±3
#     ±4
#     ±5
#     ±6
#
# This keeps the comparison seasonal while ensuring that the
# MILD and SEVERE scenarios are supported by actual historical
# occurrences rather than one isolated observation.
# ============================================================

ANALOG_RADII = [
    2,
    3,
    4,
    5,
    6
]

MIN_TOTAL_ANALOGS = 12

MIN_POSITIVE_SCENARIO_OBS = 4


# ============================================================
# 4. SCENARIO INTENSITY GOVERNANCE
#
# We use P75 of scenario-specific regional exposure.
#
# Example:
#
# Historical comparable severe-weather weeks show:
#
#     severe exposure shares =
#     0.20, 0.31, 0.45, 0.53, ...
#
# We use the 75th percentile as a "strong but plausible"
# severe planning scenario.
#
# Then:
#
#     scenario exposure × frozen SKU adjustment cap
#
# Example:
#
# APS severe cap = +6%
# P75 severe exposure = 45%
#
# Severe scenario:
#
#     0.45 × 6% = +2.7%
#
# This is still a PROJECT ASSUMPTION framework.
# It is NOT an empirical elasticity.
# ============================================================

SCENARIO_EXPOSURE_QUANTILE = 0.75


# ============================================================
# 5. FILE QA
# ============================================================

print("\n" + "=" * 100)
print("STEP 4C.4 — CORRECTED FORWARD WEATHER SCENARIO FRAMEWORK")
print("=" * 100)

print(
    "Historical weather overlay:",
    HISTORICAL_OVERLAY_FILE
)

if not HISTORICAL_OVERLAY_FILE.exists():

    raise FileNotFoundError(
        f"\nHistorical overlay not found:\n"
        f"{HISTORICAL_OVERLAY_FILE}"
    )

print(
    "Input file status: FOUND"
)


# ============================================================
# 6. LOAD HISTORICAL OVERLAY
# ============================================================

historical = pd.read_csv(
    HISTORICAL_OVERLAY_FILE
)

print(
    "\nHistorical overlay shape:",
    historical.shape
)


# ============================================================
# 7. REQUIRED SCHEMA
# ============================================================

REQUIRED_COLUMNS = {

    "week_start",

    "sku_id",
    "channel_id",

    "mild_exposure_share",
    "normal_exposure_share",
    "severe_exposure_share",
    "reference_unavailable_share",

    "weather_adjustment_pct",

    "overlay_eligible_flag",

    "mild_adjustment_pct",
    "severe_adjustment_pct",

    "weather_adjustment_provenance"
}


missing_columns = (
    REQUIRED_COLUMNS
    - set(historical.columns)
)


schema_pass = (
    len(missing_columns) == 0
)


print(
    "\nHistorical overlay schema:",
    "PASS" if schema_pass else "FAIL"
)


if not schema_pass:

    print(
        "Missing columns:",
        sorted(missing_columns)
    )

    raise ValueError(
        "Step 4C.4 historical overlay schema is incomplete."
    )


# ============================================================
# 8. DATE PARSING
# ============================================================

historical["week_start"] = pd.to_datetime(
    historical["week_start"],
    format="%Y-%m-%d",
    errors="raise"
)


# ============================================================
# 9. FORECAST ORIGIN
# ============================================================

forecast_origin = (
    historical["week_start"].max()
)


forecast_origin_pass = (
    forecast_origin
    == EXPECTED_FORECAST_ORIGIN
)


if not forecast_origin_pass:

    raise ValueError(
        f"Unexpected forecast origin: {forecast_origin.date()}"
    )


first_forecast_week = (
    forecast_origin
    + pd.Timedelta(weeks=1)
)


last_forecast_week = (
    forecast_origin
    + pd.Timedelta(
        weeks=FORECAST_HORIZON_WEEKS
    )
)


print("\n" + "=" * 100)
print("FORECAST CALENDAR")
print("=" * 100)

print(
    "Forecast origin:",
    forecast_origin.date()
)

print(
    "First forecast week:",
    first_forecast_week.date()
)

print(
    "Last forecast week:",
    last_forecast_week.date()
)

print(
    "Forecast horizon:",
    FORECAST_HORIZON_WEEKS,
    "weeks"
)


# ============================================================
# 10. DIMENSION QA
# ============================================================

sku_pass = (
    set(historical["sku_id"].unique())
    == EXPECTED_SKUS
)


channel_pass = (
    set(historical["channel_id"].unique())
    == EXPECTED_CHANNELS
)


series_count = (
    historical[
        [
            "sku_id",
            "channel_id"
        ]
    ]
    .drop_duplicates()
    .shape[0]
)


series_pass = (
    series_count
    == EXPECTED_SERIES
)


print("\n" + "=" * 100)
print("HISTORICAL DIMENSION QA")
print("=" * 100)

print(
    "3 SKUs:",
    "PASS" if sku_pass else "FAIL"
)

print(
    "3 channels:",
    "PASS" if channel_pass else "FAIL"
)

print(
    "9 SKU × Channel series:",
    "PASS" if series_pass else "FAIL"
)


if not all([
    sku_pass,
    channel_pass,
    series_pass
]):

    raise ValueError(
        "Historical overlay dimensions are invalid."
    )


# ============================================================
# 11. ELIGIBLE HISTORICAL ANALOG POOL
#
# Remove the initial reference-unavailable year.
# ============================================================

eligible_history = (
    historical[
        historical["overlay_eligible_flag"] == 1
    ]
    .copy()
)


eligible_history["iso_week"] = (
    eligible_history["week_start"]
    .dt.isocalendar()
    .week
    .astype(int)
)


eligible_history["calendar_year"] = (
    eligible_history["week_start"]
    .dt.year
)


print("\n" + "=" * 100)
print("HISTORICAL ANALOG POOL")
print("=" * 100)

print(
    "Eligible historical rows:",
    len(eligible_history)
)

print(
    "Eligible historical weeks:",
    eligible_history["week_start"].nunique()
)

print(
    "Historical years:",
    sorted(
        eligible_history["calendar_year"].unique()
    )
)

print(
    "Maximum historical date:",
    eligible_history["week_start"].max().date()
)


# ============================================================
# 12. HINDSIGHT LEAKAGE GUARD
# ============================================================

future_history_rows = (
    eligible_history["week_start"]
    .gt(forecast_origin)
    .sum()
)


hindsight_pass = (
    future_history_rows == 0
)


print(
    "\nFuture rows present in analog pool:",
    future_history_rows
)

print(
    "Hindsight leakage guard:",
    "PASS" if hindsight_pass else "FAIL"
)


if not hindsight_pass:

    raise ValueError(
        "Future realized weather detected."
    )


# ============================================================
# 13. FUTURE 13-WEEK CALENDAR
# ============================================================

future_calendar = pd.DataFrame({

    "horizon_week":
        range(
            1,
            FORECAST_HORIZON_WEEKS + 1
        ),

    "forecast_week_start":
        [
            forecast_origin
            + pd.Timedelta(weeks=i)

            for i in range(
                1,
                FORECAST_HORIZON_WEEKS + 1
            )
        ]

})


future_calendar["iso_week"] = (
    future_calendar["forecast_week_start"]
    .dt.isocalendar()
    .week
    .astype(int)
)


future_calendar["weather_horizon_mode"] = np.where(

    future_calendar["horizon_week"]
    <= NOWCAST_HORIZON_WEEKS,

    "NOWCAST_REQUIRED",

    "SCENARIO_ANALOG"

)


# ============================================================
# 14. CYCLICAL WEEK DISTANCE
# ============================================================

def seasonal_week_distance(
    historical_week,
    target_week
):

    direct = abs(
        int(historical_week)
        - int(target_week)
    )

    return min(
        direct,
        52 - min(direct, 52)
    )


# ============================================================
# 15. ANALOG SELECTION FUNCTION
#
# Select the narrowest seasonal radius that gives us:
#
# - >= 12 total analog observations
# - >= 4 positive mild-exposure observations
# - >= 4 positive severe-exposure observations
#
# This ensures scenario-specific support.
# ============================================================

def select_analog_pool(
    series_history,
    target_iso_week
):

    final_result = None


    for radius in ANALOG_RADII:

        mask = (
            series_history["iso_week"]
            .apply(
                lambda x:
                seasonal_week_distance(
                    x,
                    target_iso_week
                )
                <= radius
            )
        )


        analogs = (
            series_history[mask]
            .copy()
        )


        mild_positive = (
            analogs[
                analogs["mild_exposure_share"]
                > 0
            ]
        )


        severe_positive = (
            analogs[
                analogs["severe_exposure_share"]
                > 0
            ]
        )


        result = {

            "radius":
                radius,

            "analogs":
                analogs,

            "mild_positive":
                mild_positive,

            "severe_positive":
                severe_positive
        }


        final_result = result


        if (
            len(analogs)
            >= MIN_TOTAL_ANALOGS

            and

            len(mild_positive)
            >= MIN_POSITIVE_SCENARIO_OBS

            and

            len(severe_positive)
            >= MIN_POSITIVE_SCENARIO_OBS
        ):

            return result


    return final_result


# ============================================================
# 16. BUILD FORWARD FRAMEWORK
# ============================================================

forward_rows = []


series_list = (
    eligible_history[
        [
            "sku_id",
            "channel_id"
        ]
    ]
    .drop_duplicates()
    .sort_values(
        [
            "sku_id",
            "channel_id"
        ]
    )
)


for _, series_row in series_list.iterrows():

    sku_id = (
        series_row["sku_id"]
    )

    channel_id = (
        series_row["channel_id"]
    )


    series_history = (
        eligible_history[
            (
                eligible_history["sku_id"]
                == sku_id
            )
            &
            (
                eligible_history["channel_id"]
                == channel_id
            )
        ]
        .copy()
    )


    # --------------------------------------------------------
    # Frozen Step 4C.3 policy caps
    # --------------------------------------------------------

    mild_policy_cap = float(
        series_history[
            "mild_adjustment_pct"
        ]
        .iloc[0]
    )


    severe_policy_cap = float(
        series_history[
            "severe_adjustment_pct"
        ]
        .iloc[0]
    )


    for _, future_row in future_calendar.iterrows():

        horizon_week = int(
            future_row["horizon_week"]
        )

        forecast_week_start = (
            future_row["forecast_week_start"]
        )

        target_iso_week = int(
            future_row["iso_week"]
        )

        weather_horizon_mode = (
            future_row["weather_horizon_mode"]
        )


        # ----------------------------------------------------
        # Select historically comparable seasonal observations
        # ----------------------------------------------------

        analog_result = select_analog_pool(
            series_history,
            target_iso_week
        )


        analogs = (
            analog_result["analogs"]
        )

        mild_positive = (
            analog_result["mild_positive"]
        )

        severe_positive = (
            analog_result["severe_positive"]
        )

        radius_used = int(
            analog_result["radius"]
        )


        total_analog_count = len(
            analogs
        )

        mild_positive_count = len(
            mild_positive
        )

        severe_positive_count = len(
            severe_positive
        )


        # ----------------------------------------------------
        # Support classification
        # ----------------------------------------------------

        scenario_support_flag = (

            "ADEQUATE"

            if (
                total_analog_count
                >= MIN_TOTAL_ANALOGS

                and

                mild_positive_count
                >= MIN_POSITIVE_SCENARIO_OBS

                and

                severe_positive_count
                >= MIN_POSITIVE_SCENARIO_OBS
            )

            else "LIMITED"
        )


        # ----------------------------------------------------
        # MILD scenario exposure
        #
        # Conditional on mild exposure actually occurring.
        # ----------------------------------------------------

        if mild_positive_count > 0:

            mild_exposure_scenario = float(

                np.quantile(

                    mild_positive[
                        "mild_exposure_share"
                    ],

                    SCENARIO_EXPOSURE_QUANTILE

                )

            )

        else:

            mild_exposure_scenario = 0.0


        # ----------------------------------------------------
        # SEVERE scenario exposure
        #
        # Conditional on severe exposure actually occurring.
        # ----------------------------------------------------

        if severe_positive_count > 0:

            severe_exposure_scenario = float(

                np.quantile(

                    severe_positive[
                        "severe_exposure_share"
                    ],

                    SCENARIO_EXPOSURE_QUANTILE

                )

            )

        else:

            severe_exposure_scenario = 0.0


        # ----------------------------------------------------
        # Bound exposure shares to valid 0–1 range.
        # ----------------------------------------------------

        mild_exposure_scenario = float(
            np.clip(
                mild_exposure_scenario,
                0.0,
                1.0
            )
        )


        severe_exposure_scenario = float(
            np.clip(
                severe_exposure_scenario,
                0.0,
                1.0
            )
        )


        # ----------------------------------------------------
        # Scenario adjustments
        #
        # Exposure × frozen SKU cap
        # ----------------------------------------------------

        mild_scenario_pct = (
            mild_exposure_scenario
            * mild_policy_cap
        )


        normal_scenario_pct = 0.0


        severe_scenario_pct = (
            severe_exposure_scenario
            * severe_policy_cap
        )


        # ----------------------------------------------------
        # Net historical adjustment distribution retained
        # ONLY as diagnostic context.
        #
        # It does NOT determine the scenario anymore.
        # ----------------------------------------------------

        analog_adjustment_median = float(

            analogs[
                "weather_adjustment_pct"
            ]
            .median()

        )


        analog_adjustment_min = float(

            analogs[
                "weather_adjustment_pct"
            ]
            .min()

        )


        analog_adjustment_max = float(

            analogs[
                "weather_adjustment_pct"
            ]
            .max()

        )


        # ----------------------------------------------------
        # Weeks 1–3:
        #
        # no archived point-in-time weather forecast supplied.
        #
        # We therefore do NOT select an operational weather
        # adjustment.
        # ----------------------------------------------------

        recommended_base_adjustment_pct = 0.0

        nowcast_available_flag = 0

        future_realized_weather_used_flag = 0


        if weather_horizon_mode == "NOWCAST_REQUIRED":

            weather_data_status = (
                "POINT_IN_TIME_NOWCAST_NOT_SUPPLIED"
            )

        else:

            weather_data_status = (
                "FORWARD_SCENARIO_BAND"
            )


        scenario_width_pp = (
            severe_scenario_pct
            - mild_scenario_pct
        )


        forward_rows.append({

            "forecast_origin":
                forecast_origin,

            "horizon_week":
                horizon_week,

            "forecast_week_start":
                forecast_week_start,

            "iso_week":
                target_iso_week,

            "sku_id":
                sku_id,

            "channel_id":
                channel_id,

            "weather_horizon_mode":
                weather_horizon_mode,

            "weather_data_status":
                weather_data_status,

            "nowcast_available_flag":
                nowcast_available_flag,

            "future_realized_weather_used_flag":
                future_realized_weather_used_flag,


            # ----------------------------
            # Analog support
            # ----------------------------

            "analog_week_radius_used":
                radius_used,

            "analog_observation_count":
                total_analog_count,

            "mild_positive_analog_count":
                mild_positive_count,

            "severe_positive_analog_count":
                severe_positive_count,

            "scenario_support_flag":
                scenario_support_flag,


            # ----------------------------
            # Exposure calibration
            # ----------------------------

            "mild_scenario_exposure_share":
                mild_exposure_scenario,

            "severe_scenario_exposure_share":
                severe_exposure_scenario,

            "scenario_exposure_quantile":
                SCENARIO_EXPOSURE_QUANTILE,


            # ----------------------------
            # Frozen policy caps
            # ----------------------------

            "sku_mild_policy_cap_pct":
                mild_policy_cap,

            "sku_severe_policy_cap_pct":
                severe_policy_cap,


            # ----------------------------
            # Forward scenario adjustments
            # ----------------------------

            "mild_scenario_adjustment_pct":
                mild_scenario_pct,

            "normal_scenario_adjustment_pct":
                normal_scenario_pct,

            "severe_scenario_adjustment_pct":
                severe_scenario_pct,

            "recommended_base_adjustment_pct":
                recommended_base_adjustment_pct,

            "scenario_width_pp":
                scenario_width_pp,


            # ----------------------------
            # Diagnostics only
            # ----------------------------

            "analog_net_adjustment_median_pct":
                analog_adjustment_median,

            "analog_net_adjustment_min_pct":
                analog_adjustment_min,

            "analog_net_adjustment_max_pct":
                analog_adjustment_max,


            # ----------------------------
            # Governance
            # ----------------------------

            "scenario_method":
                (
                    "CONDITIONAL_P75_SCENARIO_EXPOSURE"
                    "_X_FROZEN_SKU_POLICY_CAP"
                ),

            "scenario_provenance":
                (
                    "HISTORICAL_PUBLIC_WEATHER_DERIVED_OVERLAY"
                ),

            "scenario_threshold_provenance":
                (
                    "PROJECT_ASSUMPTION"
                ),

            "nowcast_governance":
                (
                    "NO_REALIZED_FUTURE_WEATHER_USED"
                )

        })


forward_df = pd.DataFrame(
    forward_rows
)


# ============================================================
# 17. STRUCTURAL QA
# ============================================================

row_count_pass = (
    len(forward_df)
    == EXPECTED_OUTPUT_ROWS
)


series_count_pass = (
    forward_df[
        [
            "sku_id",
            "channel_id"
        ]
    ]
    .drop_duplicates()
    .shape[0]
    == EXPECTED_SERIES
)


week_count_pass = (
    forward_df[
        "forecast_week_start"
    ]
    .nunique()
    == FORECAST_HORIZON_WEEKS
)


duplicate_count = (
    forward_df
    .duplicated(
        subset=[
            "forecast_week_start",
            "sku_id",
            "channel_id"
        ]
    )
    .sum()
)


grain_pass = (
    duplicate_count == 0
)


weeks_per_series = (
    forward_df
    .groupby(
        [
            "sku_id",
            "channel_id"
        ]
    )
    ["forecast_week_start"]
    .nunique()
)


weeks_per_series_pass = (
    weeks_per_series
    .eq(FORECAST_HORIZON_WEEKS)
    .all()
)


monday_pass = (
    forward_df[
        "forecast_week_start"
    ]
    .dt.dayofweek
    .eq(0)
    .all()
)


start_pass = (
    forward_df[
        "forecast_week_start"
    ]
    .min()
    == first_forecast_week
)


end_pass = (
    forward_df[
        "forecast_week_start"
    ]
    .max()
    == last_forecast_week
)


# ============================================================
# 18. ANALOG SUPPORT QA
# ============================================================

total_analog_pass = (
    forward_df[
        "analog_observation_count"
    ]
    .ge(MIN_TOTAL_ANALOGS)
    .all()
)


mild_support_pass = (
    forward_df[
        "mild_positive_analog_count"
    ]
    .ge(MIN_POSITIVE_SCENARIO_OBS)
    .all()
)


severe_support_pass = (
    forward_df[
        "severe_positive_analog_count"
    ]
    .ge(MIN_POSITIVE_SCENARIO_OBS)
    .all()
)


support_flag_pass = (
    forward_df[
        "scenario_support_flag"
    ]
    .eq("ADEQUATE")
    .all()
)


# ============================================================
# 19. EXPOSURE QA
# ============================================================

mild_exposure_pass = (
    forward_df[
        "mild_scenario_exposure_share"
    ]
    .between(
        0,
        1
    )
    .all()
)


severe_exposure_pass = (
    forward_df[
        "severe_scenario_exposure_share"
    ]
    .between(
        0,
        1
    )
    .all()
)


# ============================================================
# 20. SCENARIO DIRECTION QA
# ============================================================

mild_direction_pass = (
    forward_df[
        "mild_scenario_adjustment_pct"
    ]
    .le(0)
    .all()
)


normal_zero_pass = (
    forward_df[
        "normal_scenario_adjustment_pct"
    ]
    .eq(0)
    .all()
)


severe_direction_pass = (
    forward_df[
        "severe_scenario_adjustment_pct"
    ]
    .ge(0)
    .all()
)


scenario_order_pass = (
    (
        forward_df[
            "mild_scenario_adjustment_pct"
        ]
        <=
        forward_df[
            "normal_scenario_adjustment_pct"
        ]
    )
    &
    (
        forward_df[
            "normal_scenario_adjustment_pct"
        ]
        <=
        forward_df[
            "severe_scenario_adjustment_pct"
        ]
    )
).all()


# ============================================================
# 21. POLICY CAP QA
# ============================================================

mild_cap_pass = (
    forward_df[
        "mild_scenario_adjustment_pct"
    ]
    .ge(
        forward_df[
            "sku_mild_policy_cap_pct"
        ]
        - 1e-10
    )
    .all()
)


severe_cap_pass = (
    forward_df[
        "severe_scenario_adjustment_pct"
    ]
    .le(
        forward_df[
            "sku_severe_policy_cap_pct"
        ]
        + 1e-10
    )
    .all()
)


# ============================================================
# 22. HINDSIGHT / HORIZON QA
# ============================================================

realized_weather_pass = (
    forward_df[
        "future_realized_weather_used_flag"
    ]
    .eq(0)
    .all()
)


nowcast_rows = (
    forward_df[
        forward_df[
            "weather_horizon_mode"
        ]
        == "NOWCAST_REQUIRED"
    ]
)


scenario_rows = (
    forward_df[
        forward_df[
            "weather_horizon_mode"
        ]
        == "SCENARIO_ANALOG"
    ]
)


nowcast_row_pass = (
    len(nowcast_rows)
    ==
    (
        NOWCAST_HORIZON_WEEKS
        * EXPECTED_SERIES
    )
)


scenario_row_pass = (
    len(scenario_rows)
    ==
    (
        (
            FORECAST_HORIZON_WEEKS
            - NOWCAST_HORIZON_WEEKS
        )
        * EXPECTED_SERIES
    )
)


nowcast_status_pass = (
    nowcast_rows[
        "weather_data_status"
    ]
    .eq(
        "POINT_IN_TIME_NOWCAST_NOT_SUPPLIED"
    )
    .all()
)


# ============================================================
# 23. FINAL QA
# ============================================================

qa_checks = {

    "Historical overlay schema valid":
        schema_pass,

    "Forecast origin = 2026-06-22":
        forecast_origin_pass,

    "No future realized weather in analog pool":
        hindsight_pass,

    "Output rows = 117":
        row_count_pass,

    "Exactly 9 forecasting series":
        series_count_pass,

    "13 forward weeks":
        week_count_pass,

    "Week × SKU × Channel grain unique":
        grain_pass,

    "Each series contains 13 weeks":
        weeks_per_series_pass,

    "All forecast weeks are Monday":
        monday_pass,

    "Forecast starts at week 1":
        start_pass,

    "Forecast ends at week 13":
        end_pass,

    "Enough total seasonal analogs":
        total_analog_pass,

    "Enough historical MILD exposure observations":
        mild_support_pass,

    "Enough historical SEVERE exposure observations":
        severe_support_pass,

    "All scenario support flags ADEQUATE":
        support_flag_pass,

    "MILD exposure share within 0–1":
        mild_exposure_pass,

    "SEVERE exposure share within 0–1":
        severe_exposure_pass,

    "MILD adjustment <= 0":
        mild_direction_pass,

    "NORMAL adjustment = 0":
        normal_zero_pass,

    "SEVERE adjustment >= 0":
        severe_direction_pass,

    "MILD <= NORMAL <= SEVERE":
        scenario_order_pass,

    "MILD within frozen policy cap":
        mild_cap_pass,

    "SEVERE within frozen policy cap":
        severe_cap_pass,

    "No realized future weather used":
        realized_weather_pass,

    "Weeks 1–3 marked NOWCAST_REQUIRED":
        nowcast_row_pass,

    "Weeks 4–13 marked SCENARIO_ANALOG":
        scenario_row_pass,

    "Nowcast unavailable explicitly documented":
        nowcast_status_pass

}


overall_pass = all(
    qa_checks.values()
)


print("\n" + "=" * 100)
print("FINAL STEP 4C.4 QA")
print("=" * 100)


for name, passed in qa_checks.items():

    print(
        f"{name}:",
        "PASS" if passed else "FAIL"
    )


# ============================================================
# 24. SCENARIO SUMMARY BY SERIES
# ============================================================

summary = (
    forward_df
    .groupby(
        [
            "sku_id",
            "channel_id"
        ],
        as_index=False
    )
    .agg(

        avg_mild_exposure_share=(
            "mild_scenario_exposure_share",
            "mean"
        ),

        avg_severe_exposure_share=(
            "severe_scenario_exposure_share",
            "mean"
        ),

        avg_mild_scenario_pct=(
            "mild_scenario_adjustment_pct",
            "mean"
        ),

        avg_severe_scenario_pct=(
            "severe_scenario_adjustment_pct",
            "mean"
        ),

        min_mild_scenario_pct=(
            "mild_scenario_adjustment_pct",
            "min"
        ),

        max_severe_scenario_pct=(
            "severe_scenario_adjustment_pct",
            "max"
        ),

        avg_scenario_width_pp=(
            "scenario_width_pp",
            "mean"
        ),

        min_mild_positive_analogs=(
            "mild_positive_analog_count",
            "min"
        ),

        min_severe_positive_analogs=(
            "severe_positive_analog_count",
            "min"
        ),

        max_analog_radius_used=(
            "analog_week_radius_used",
            "max"
        )

    )
)


print("\n" + "=" * 100)
print("FORWARD WEATHER SCENARIO SUMMARY BY SERIES")
print("=" * 100)


summary_display = (
    summary.copy()
)


numeric_columns = [
    column
    for column in summary_display.columns
    if column not in [
        "sku_id",
        "channel_id"
    ]
]


summary_display[
    numeric_columns
] = (
    summary_display[
        numeric_columns
    ]
    .round(3)
)


print(
    summary_display
    .to_string(
        index=False
    )
)


# ============================================================
# 25. FORWARD MODE TABLE
# ============================================================

print("\n" + "=" * 100)
print("FORWARD WEATHER MODE BY HORIZON")
print("=" * 100)


print(
    future_calendar[
        [
            "horizon_week",
            "forecast_week_start",
            "iso_week",
            "weather_horizon_mode"
        ]
    ]
    .to_string(
        index=False
    )
)


# ============================================================
# 26. SCENARIO EXAMPLES
# ============================================================

print("\n" + "=" * 100)
print("FORWARD WEATHER SCENARIO EXAMPLES")
print("=" * 100)


example = (
    forward_df[
        [
            "forecast_week_start",

            "horizon_week",

            "sku_id",

            "channel_id",

            "weather_horizon_mode",

            "analog_week_radius_used",

            "mild_positive_analog_count",

            "severe_positive_analog_count",

            "mild_scenario_exposure_share",

            "severe_scenario_exposure_share",

            "mild_scenario_adjustment_pct",

            "normal_scenario_adjustment_pct",

            "severe_scenario_adjustment_pct",

            "scenario_width_pp"
        ]
    ]
    .head(25)
    .copy()
)


example_numeric_columns = [

    "mild_scenario_exposure_share",

    "severe_scenario_exposure_share",

    "mild_scenario_adjustment_pct",

    "normal_scenario_adjustment_pct",

    "severe_scenario_adjustment_pct",

    "scenario_width_pp"

]


example[
    example_numeric_columns
] = (
    example[
        example_numeric_columns
    ]
    .round(3)
)


print(
    example
    .to_string(
        index=False
    )
)


# ============================================================
# 27. RANGE CHECK
# ============================================================

print("\n" + "=" * 100)
print("FORWARD SCENARIO RANGE CHECK")
print("=" * 100)


print(
    "Overall minimum MILD adjustment:",
    round(
        forward_df[
            "mild_scenario_adjustment_pct"
        ]
        .min(),
        3
    ),
    "%"
)


print(
    "Overall maximum SEVERE adjustment:",
    round(
        forward_df[
            "severe_scenario_adjustment_pct"
        ]
        .max(),
        3
    ),
    "%"
)


print(
    "Average scenario width:",
    round(
        forward_df[
            "scenario_width_pp"
        ]
        .mean(),
        3
    ),
    "percentage points"
)


# ============================================================
# 28. SAVE
# ============================================================

if overall_pass:

    output = (
        forward_df.copy()
    )


    output[
        "forecast_origin"
    ] = (
        output[
            "forecast_origin"
        ]
        .dt.strftime(
            "%Y-%m-%d"
        )
    )


    output[
        "forecast_week_start"
    ] = (
        output[
            "forecast_week_start"
        ]
        .dt.strftime(
            "%Y-%m-%d"
        )
    )


    output.to_csv(
        OUTPUT_FILE,
        index=False
    )


    print("\n" + "=" * 100)
    print("STEP 4C.4 COMPLETE")
    print("=" * 100)


    print(
        "OVERALL STATUS: PASS"
    )


    print(
        "\nCreated:"
    )


    print(
        OUTPUT_FILE
    )


else:

    print("\n" + "=" * 100)
    print("STEP 4C.4 FAILED QA")
    print("=" * 100)


    print(
        "OVERALL STATUS: FAIL"
    )


    print(
        "Output was NOT saved."
    )


    raise RuntimeError(
        "Step 4C.4 corrected scenario calibration failed QA."
    )


# ============================================================
# END STEP 4C.4
# ============================================================