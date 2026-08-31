import pandas as pd
import numpy as np
from pathlib import Path
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings


# ============================================================
# DEMANDIQ
# STEP 4D — FINAL 13-WEEK DEMAND FORECAST
#
# COMPLETE STEP 4D IN ONE SCRIPT
#
# 1. Load frozen forecasting target
# 2. Validate frozen champions
# 3. Fit each champion on all 260 historical weeks
# 4. Forecast next 13 weeks
# 5. Join frozen Step 4C weather scenarios
# 6. Produce Mild / Normal / Severe planning outlook
# 7. Run final QA
# 8. Save one final planner-ready forecast file
#
# Forecast grain:
#     Week × SKU × Channel
#
# 13 weeks × 9 series = 117 rows
# ============================================================


# ============================================================
# 1. PATHS
# ============================================================

PROJECT_DIR = Path(
    r"D:\Downloads\DemandIQ"
)


# Search automatically because the Step 4B input may have
# been moved during folder cleanup.
FORECAST_INPUT_NAME = (
    "DemandIQ_Step4B_Forecasting_Input.csv"
)


WEATHER_FILE = (
    PROJECT_DIR
    / "05_outputs"
    / "weather_forward"
    / "DemandIQ_Step4C_Forward_Weather_Framework.csv"
)


OUTPUT_DIR = (
    PROJECT_DIR
    / "05_outputs"
    / "forecasts"
)


OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


OUTPUT_FILE = (
    OUTPUT_DIR
    / "DemandIQ_Step4D_Final_13Week_Forecast.csv"
)


# ============================================================
# 2. GOVERNED FORECAST STRUCTURE
# ============================================================

HISTORY_WEEKS = 260

FORECAST_HORIZON = 13

EXPECTED_SERIES = 9

EXPECTED_HISTORY_ROWS = (
    HISTORY_WEEKS
    * EXPECTED_SERIES
)

EXPECTED_FORECAST_ROWS = (
    FORECAST_HORIZON
    * EXPECTED_SERIES
)


HISTORY_START = pd.Timestamp(
    "2021-07-05"
)

FORECAST_ORIGIN = pd.Timestamp(
    "2026-06-22"
)

FORECAST_START = pd.Timestamp(
    "2026-06-29"
)

FORECAST_END = pd.Timestamp(
    "2026-09-21"
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
# 3. FROZEN STEP 4B CHAMPIONS
#
# NO NEW MODEL SELECTION OR TUNING OCCURS IN STEP 4D.
# ============================================================

CHAMPIONS = {

    ("APS-001", "ECOM"): {
        "model": "HW_Damped_Mul",
        "family": "ETS",
        "wape": 10.55,
        "bias": -3.09
    },

    ("APS-001", "RETAIL"): {
        "model": "HW_Damped_Mul",
        "family": "ETS",
        "wape": 8.83,
        "bias": -0.97
    },

    ("APS-001", "WHOLESALE"): {
        "model": "HW_Damped_Add",
        "family": "ETS",
        "wape": 18.26,
        "bias": -0.35
    },

    ("CTS-001", "ECOM"): {
        "model": "HW_Damped_Mul",
        "family": "ETS",
        "wape": 8.37,
        "bias": -1.12
    },

    ("CTS-001", "RETAIL"): {
        "model": "HW_Damped_Mul",
        "family": "ETS",
        "wape": 9.18,
        "bias": 0.80
    },

    ("CTS-001", "WHOLESALE"): {
        "model": "Seasonal_MA_2Y",
        "family": "BASELINE",
        "wape": 21.73,
        "bias": 2.41
    },

    ("IMH-001", "ECOM"): {
        "model": "HW_Damped_Mul",
        "family": "ETS",
        "wape": 8.68,
        "bias": -1.32
    },

    ("IMH-001", "RETAIL"): {
        "model": "HW_Damped_Mul",
        "family": "ETS",
        "wape": 8.48,
        "bias": -1.21
    },

    ("IMH-001", "WHOLESALE"): {
        "model": "HW_Add_Add",
        "family": "ETS",
        "wape": 18.55,
        "bias": 1.41
    }

}


# ============================================================
# 4. FIND STEP 4B FORECASTING INPUT
# ============================================================

def find_forecast_input():

    matches = list(
        PROJECT_DIR.rglob(
            FORECAST_INPUT_NAME
        )
    )

    matches = [
        x
        for x in matches
        if "archive" not in str(x).lower()
        and "backup" not in str(x).lower()
    ]

    if len(matches) == 0:

        raise FileNotFoundError(
            f"{FORECAST_INPUT_NAME} not found."
        )

    if len(matches) > 1:

        print(
            "\nMultiple Step 4B forecasting inputs found:"
        )

        for path in matches:
            print(
                " -",
                path
            )

        raise RuntimeError(
            "Keep only one active Step 4B forecasting input."
        )

    return matches[0]


FORECAST_INPUT_FILE = (
    find_forecast_input()
)


# ============================================================
# 5. START
# ============================================================

print(
    "\n"
    + "=" * 100
)

print(
    "STEP 4D — FINAL 13-WEEK DEMAND FORECAST"
)

print(
    "=" * 100
)


print(
    "\nForecasting input:"
)

print(
    FORECAST_INPUT_FILE
)


print(
    "\nForward weather framework:"
)

print(
    WEATHER_FILE
)


if not WEATHER_FILE.exists():

    raise FileNotFoundError(
        WEATHER_FILE
    )


# ============================================================
# 6. LOAD INPUTS
# ============================================================

history = pd.read_csv(
    FORECAST_INPUT_FILE
)


weather = pd.read_csv(
    WEATHER_FILE
)


print(
    "\nHistory shape:",
    history.shape
)


print(
    "Weather framework shape:",
    weather.shape
)


# ============================================================
# 7. SCHEMA QA
# ============================================================

HISTORY_REQUIRED = {

    "week_start",
    "sku_id",
    "channel_id",
    "reconstructed_demand_units"

}


WEATHER_REQUIRED = {

    "forecast_origin",
    "forecast_week_start",
    "horizon_week",

    "sku_id",
    "channel_id",

    "weather_horizon_mode",

    "mild_scenario_adjustment_pct",
    "normal_scenario_adjustment_pct",
    "severe_scenario_adjustment_pct",

    "recommended_base_adjustment_pct",

    "future_realized_weather_used_flag"

}


missing_history = (
    HISTORY_REQUIRED
    - set(history.columns)
)


missing_weather = (
    WEATHER_REQUIRED
    - set(weather.columns)
)


if missing_history:

    raise ValueError(
        f"Missing history columns: "
        f"{sorted(missing_history)}"
    )


if missing_weather:

    raise ValueError(
        f"Missing weather columns: "
        f"{sorted(missing_weather)}"
    )


print(
    "\nInput schemas: PASS"
)


# ============================================================
# 8. DATE PARSING
# ============================================================

history["week_start"] = pd.to_datetime(
    history["week_start"],
    format="%Y-%m-%d",
    errors="raise"
)


weather["forecast_origin"] = pd.to_datetime(
    weather["forecast_origin"],
    format="%Y-%m-%d",
    errors="raise"
)


weather["forecast_week_start"] = pd.to_datetime(
    weather["forecast_week_start"],
    format="%Y-%m-%d",
    errors="raise"
)


# ============================================================
# 9. HISTORICAL INPUT QA
# ============================================================

history_checks = {

    "Rows = 2,340":
        len(history)
        == EXPECTED_HISTORY_ROWS,

    "260 historical weeks":
        history["week_start"].nunique()
        == HISTORY_WEEKS,

    "History begins 2021-07-05":
        history["week_start"].min()
        == HISTORY_START,

    "History ends 2026-06-22":
        history["week_start"].max()
        == FORECAST_ORIGIN,

    "All history dates Monday":
        history["week_start"]
        .dt.dayofweek
        .eq(0)
        .all(),

    "Historical grain unique":
        history
        .duplicated(
            subset=[
                "week_start",
                "sku_id",
                "channel_id"
            ]
        )
        .sum()
        == 0,

    "3 SKUs":
        set(
            history["sku_id"].unique()
        )
        == EXPECTED_SKUS,

    "3 channels":
        set(
            history["channel_id"].unique()
        )
        == EXPECTED_CHANNELS,

    "Target contains no nulls":
        history[
            "reconstructed_demand_units"
        ]
        .notna()
        .all(),

    "Target non-negative":
        history[
            "reconstructed_demand_units"
        ]
        .ge(0)
        .all()

}


series_count = (
    history[
        [
            "sku_id",
            "channel_id"
        ]
    ]
    .drop_duplicates()
    .shape[0]
)


history_checks[
    "Exactly 9 forecasting series"
] = (
    series_count
    == EXPECTED_SERIES
)


weeks_per_series = (
    history
    .groupby(
        [
            "sku_id",
            "channel_id"
        ]
    )
    ["week_start"]
    .nunique()
)


history_checks[
    "Every series has 260 weeks"
] = (
    weeks_per_series
    .eq(HISTORY_WEEKS)
    .all()
)


print(
    "\n"
    + "=" * 100
)

print(
    "HISTORICAL INPUT QA"
)

print(
    "=" * 100
)


for name, passed in history_checks.items():

    print(
        f"{name}:",
        "PASS"
        if passed
        else "FAIL"
    )


if not all(
    history_checks.values()
):

    raise RuntimeError(
        "Historical input QA failed."
    )


# ============================================================
# 10. CHAMPION REGISTRY QA
# ============================================================

actual_series = set(

    history[
        [
            "sku_id",
            "channel_id"
        ]
    ]

    .itertuples(
        index=False,
        name=None
    )

)


champion_series = set(
    CHAMPIONS.keys()
)


champion_coverage_pass = (
    actual_series
    == champion_series
)


ets_count = sum(

    config["family"]
    == "ETS"

    for config
    in CHAMPIONS.values()

)


baseline_count = sum(

    config["family"]
    == "BASELINE"

    for config
    in CHAMPIONS.values()

)


champion_family_pass = (
    ets_count == 8
    and
    baseline_count == 1
)


print(
    "\n"
    + "=" * 100
)

print(
    "FROZEN CHAMPION QA"
)

print(
    "=" * 100
)


print(
    "Exact 9-series champion coverage:",
    "PASS"
    if champion_coverage_pass
    else "FAIL"
)


print(
    "ETS champions:",
    ets_count
)


print(
    "Baseline champions:",
    baseline_count
)


print(
    "Expected family mix 8 ETS + 1 baseline:",
    "PASS"
    if champion_family_pass
    else "FAIL"
)


if not all([
    champion_coverage_pass,
    champion_family_pass
]):

    raise RuntimeError(
        "Frozen champion registry QA failed."
    )


# ============================================================
# 11. WEATHER FRAMEWORK QA
# ============================================================

weather_checks = {

    "Rows = 117":
        len(weather)
        == EXPECTED_FORECAST_ROWS,

    "13 forecast weeks":
        weather[
            "forecast_week_start"
        ]
        .nunique()
        == FORECAST_HORIZON,

    "Forecast origin correct":
        weather[
            "forecast_origin"
        ]
        .eq(FORECAST_ORIGIN)
        .all(),

    "Forecast begins 2026-06-29":
        weather[
            "forecast_week_start"
        ]
        .min()
        == FORECAST_START,

    "Forecast ends 2026-09-21":
        weather[
            "forecast_week_start"
        ]
        .max()
        == FORECAST_END,

    "Weather grain unique":
        weather
        .duplicated(
            subset=[
                "forecast_week_start",
                "sku_id",
                "channel_id"
            ]
        )
        .sum()
        == 0,

    "No realized future weather":
        weather[
            "future_realized_weather_used_flag"
        ]
        .eq(0)
        .all()

}


print(
    "\n"
    + "=" * 100
)

print(
    "FORWARD WEATHER QA"
)

print(
    "=" * 100
)


for name, passed in weather_checks.items():

    print(
        f"{name}:",
        "PASS"
        if passed
        else "FAIL"
    )


if not all(
    weather_checks.values()
):

    raise RuntimeError(
        "Forward weather framework QA failed."
    )


# ============================================================
# 12. FUTURE CALENDAR
# ============================================================

future_dates = pd.date_range(

    start=FORECAST_START,

    periods=FORECAST_HORIZON,

    freq="W-MON"

)


# ============================================================
# 13. ETS FUNCTION
# ============================================================

def ets_forecast(
    y,
    model_name,
    horizon
):

    if model_name == "HW_Damped_Mul":

        trend = "add"
        damped_trend = True
        seasonal = "mul"


    elif model_name == "HW_Damped_Add":

        trend = "add"
        damped_trend = True
        seasonal = "add"


    elif model_name == "HW_Add_Add":

        trend = "add"
        damped_trend = False
        seasonal = "add"


    else:

        raise ValueError(
            f"Unknown ETS model: {model_name}"
        )


    values = np.asarray(
        y,
        dtype=float
    )


    if (
        seasonal == "mul"
        and
        np.any(values <= 0)
    ):

        raise ValueError(
            f"{model_name} requires "
            f"strictly positive observations."
        )


    model = ExponentialSmoothing(

        values,

        trend=trend,

        damped_trend=damped_trend,

        seasonal=seasonal,

        seasonal_periods=52,

        initialization_method="estimated"

    )


    captured_warnings = []


    with warnings.catch_warnings(
        record=True
    ) as warning_list:

        warnings.simplefilter(
            "always"
        )


        fitted = model.fit(

            optimized=True,

            use_brute=True,

            remove_bias=False

        )


        predictions = fitted.forecast(
            horizon
        )


        for item in warning_list:

            captured_warnings.append(
                str(item.message)
            )


    return (
        np.asarray(
            predictions,
            dtype=float
        ),
        captured_warnings
    )


# ============================================================
# 14. SEASONAL 2-YEAR MA FUNCTION
# ============================================================

def seasonal_ma_2y(
    dated_series,
    future_dates
):

    predictions = []


    for forecast_date in future_dates:

        date_1y = (
            forecast_date
            - pd.Timedelta(
                weeks=52
            )
        )

        date_2y = (
            forecast_date
            - pd.Timedelta(
                weeks=104
            )
        )


        if date_1y not in dated_series.index:

            raise KeyError(
                f"Missing t-52 value: "
                f"{date_1y.date()}"
            )


        if date_2y not in dated_series.index:

            raise KeyError(
                f"Missing t-104 value: "
                f"{date_2y.date()}"
            )


        value = (

            dated_series.loc[
                date_1y
            ]

            +

            dated_series.loc[
                date_2y
            ]

        ) / 2


        predictions.append(
            float(value)
        )


    return np.asarray(
        predictions
    )


# ============================================================
# 15. FIT ALL CHAMPIONS
# ============================================================

forecast_rows = []

fit_audit = []


print(
    "\n"
    + "=" * 100
)

print(
    "FIT FROZEN CHAMPIONS ON ALL 260 WEEKS"
)

print(
    "=" * 100
)


for (
    sku_id,
    channel_id
), config in sorted(
    CHAMPIONS.items()
):


    series = (

        history[
            (
                history["sku_id"]
                == sku_id
            )

            &

            (
                history["channel_id"]
                == channel_id
            )
        ]

        .sort_values(
            "week_start"
        )

        .copy()

    )


    y = (
        series[
            "reconstructed_demand_units"
        ]
        .astype(float)
    )


    dated_series = pd.Series(

        y.values,

        index=series[
            "week_start"
        ]

    )


    model_name = (
        config["model"]
    )


    family = (
        config["family"]
    )


    if family == "ETS":

        forecast_values, model_warnings = (

            ets_forecast(

                y=y,

                model_name=model_name,

                horizon=FORECAST_HORIZON

            )

        )


    elif (
        family == "BASELINE"
        and
        model_name
        == "Seasonal_MA_2Y"
    ):

        forecast_values = (

            seasonal_ma_2y(

                dated_series,

                future_dates

            )

        )

        model_warnings = []


    else:

        raise ValueError(
            f"Unsupported champion "
            f"{sku_id} {channel_id}"
        )


    # --------------------------------------------------------
    # Model output QA
    # --------------------------------------------------------

    if len(
        forecast_values
    ) != FORECAST_HORIZON:

        raise RuntimeError(
            "Wrong forecast horizon."
        )


    if not np.isfinite(
        forecast_values
    ).all():

        raise RuntimeError(
            f"Invalid forecast values for "
            f"{sku_id} {channel_id}"
        )


    if (
        forecast_values < 0
    ).any():

        raise RuntimeError(
            f"Negative forecast generated for "
            f"{sku_id} {channel_id}"
        )


    print(
        f"{sku_id:<8} | "
        f"{channel_id:<10} | "
        f"{model_name:<16} | "
        f"13W total = "
        f"{forecast_values.sum():,.2f}"
    )


    if model_warnings:

        print(
            f"   warnings captured: "
            f"{len(model_warnings)}"
        )


    fit_audit.append({

        "sku_id":
            sku_id,

        "channel_id":
            channel_id,

        "champion_model":
            model_name,

        "champion_family":
            family,

        "warning_count":
            len(model_warnings),

        "forecast_13w_units":
            forecast_values.sum()

    })


    for horizon_week, (
        date,
        value
    ) in enumerate(

        zip(
            future_dates,
            forecast_values
        ),

        start=1

    ):

        forecast_rows.append({

            "forecast_origin":
                FORECAST_ORIGIN,

            "forecast_week_start":
                date,

            "horizon_week":
                horizon_week,

            "sku_id":
                sku_id,

            "channel_id":
                channel_id,

            "champion_model":
                model_name,

            "champion_family":
                family,

            "training_weeks":
                HISTORY_WEEKS,

            "champion_backtest_wape_pct":
                config["wape"],

            "champion_backtest_bias_pct":
                config["bias"],

            "base_forecast_units":
                float(value)

        })


base = pd.DataFrame(
    forecast_rows
)


fit_audit = pd.DataFrame(
    fit_audit
)


# ============================================================
# 16. BASE FORECAST QA
# ============================================================

base_checks = {

    "117 base forecast rows":
        len(base)
        == EXPECTED_FORECAST_ROWS,

    "Base forecast grain unique":
        base
        .duplicated(
            subset=[
                "forecast_week_start",
                "sku_id",
                "channel_id"
            ]
        )
        .sum()
        == 0,

    "9 forecasting series":
        base[
            [
                "sku_id",
                "channel_id"
            ]
        ]
        .drop_duplicates()
        .shape[0]
        == EXPECTED_SERIES,

    "13 forecast weeks":
        base[
            "forecast_week_start"
        ]
        .nunique()
        == FORECAST_HORIZON,

    "No missing forecasts":
        base[
            "base_forecast_units"
        ]
        .notna()
        .all(),

    "No negative forecasts":
        base[
            "base_forecast_units"
        ]
        .ge(0)
        .all()

}


print(
    "\n"
    + "=" * 100
)

print(
    "BASE FORECAST QA"
)

print(
    "=" * 100
)


for name, passed in base_checks.items():

    print(
        f"{name}:",
        "PASS"
        if passed
        else "FAIL"
    )


if not all(
    base_checks.values()
):

    raise RuntimeError(
        "Base forecast QA failed."
    )


# ============================================================
# 17. MERGE WEATHER FRAMEWORK
# ============================================================

final = base.merge(

    weather,

    on=[
        "forecast_week_start",
        "horizon_week",
        "sku_id",
        "channel_id"
    ],

    how="left",

    validate="one_to_one",

    suffixes=(
        "",
        "_weather"
    )

)


weather_merge_pass = (
    final[
        "weather_horizon_mode"
    ]
    .notna()
    .all()
)


if not weather_merge_pass:

    raise RuntimeError(
        "Weather framework merge failed."
    )


# ============================================================
# 18. CREATE FINAL WEATHER SCENARIO FORECASTS
# ============================================================

final[
    "mild_scenario_forecast_units"
] = (

    final[
        "base_forecast_units"
    ]

    *

    (
        1

        +

        final[
            "mild_scenario_adjustment_pct"
        ]
        / 100
    )

)


final[
    "normal_scenario_forecast_units"
] = (

    final[
        "base_forecast_units"
    ]

    *

    (
        1

        +

        final[
            "normal_scenario_adjustment_pct"
        ]
        / 100
    )

)


final[
    "severe_scenario_forecast_units"
] = (

    final[
        "base_forecast_units"
    ]

    *

    (
        1

        +

        final[
            "severe_scenario_adjustment_pct"
        ]
        / 100
    )

)


# ============================================================
# 19. CURRENT OPERATIONAL FORECAST
#
# No archived point-in-time nowcast has been supplied.
#
# Therefore:
#
# recommended_base_adjustment_pct = 0
#
# Operational forecast currently remains champion base.
# ============================================================

final[
    "operational_forecast_units"
] = (

    final[
        "base_forecast_units"
    ]

    *

    (
        1

        +

        final[
            "recommended_base_adjustment_pct"
        ]
        / 100
    )

)


# ============================================================
# 20. SCENARIO RANGE
# ============================================================

final[
    "scenario_range_units"
] = (

    final[
        "severe_scenario_forecast_units"
    ]

    -

    final[
        "mild_scenario_forecast_units"
    ]

)


final[
    "scenario_range_pct"
] = (

    final[
        "scenario_range_units"
    ]

    /

    final[
        "base_forecast_units"
    ]

    * 100

)


# ============================================================
# 21. PLANNER STATUS
# ============================================================

final[
    "planner_status"
] = np.where(

    final[
        "weather_horizon_mode"
    ]
    == "NOWCAST_REQUIRED",

    "BASE_FORECAST_PENDING_NOWCAST",

    "BASE_WITH_MILD_NORMAL_SEVERE_SCENARIOS"

)


# ============================================================
# 22. GOVERNANCE / PROVENANCE
# ============================================================

final[
    "forecast_target"
] = (
    "RECONSTRUCTED_DEMAND_UNITS"
)


final[
    "model_selection_status"
] = (
    "FROZEN_STEP4B_CHAMPION"
)


final[
    "weather_framework_status"
] = (
    "FROZEN_STEP4C"
)


final[
    "forecast_provenance"
] = (
    "DERIVED_FROM_SYNTHETIC_CASE_STUDY_DEMAND"
)


# ============================================================
# 23. FINAL QA
# ============================================================

final_checks = {

    "Final rows = 117":
        len(final)
        == EXPECTED_FORECAST_ROWS,

    "Final grain unique":
        final
        .duplicated(
            subset=[
                "forecast_week_start",
                "sku_id",
                "channel_id"
            ]
        )
        .sum()
        == 0,

    "Forecast begins 2026-06-29":
        final[
            "forecast_week_start"
        ]
        .min()
        == FORECAST_START,

    "Forecast ends 2026-09-21":
        final[
            "forecast_week_start"
        ]
        .max()
        == FORECAST_END,

    "All forecast dates Monday":
        final[
            "forecast_week_start"
        ]
        .dt.dayofweek
        .eq(0)
        .all(),

    "No scenario forecast nulls":
        final[
            [
                "mild_scenario_forecast_units",
                "normal_scenario_forecast_units",
                "severe_scenario_forecast_units"
            ]
        ]
        .notna()
        .all()
        .all(),

    "All scenario forecasts non-negative":
        final[
            [
                "mild_scenario_forecast_units",
                "normal_scenario_forecast_units",
                "severe_scenario_forecast_units"
            ]
        ]
        .ge(0)
        .all()
        .all(),

    "MILD <= NORMAL":
        (
            final[
                "mild_scenario_forecast_units"
            ]
            <=
            final[
                "normal_scenario_forecast_units"
            ]
            + 1e-10
        )
        .all(),

    "NORMAL <= SEVERE":
        (
            final[
                "normal_scenario_forecast_units"
            ]
            <=
            final[
                "severe_scenario_forecast_units"
            ]
            + 1e-10
        )
        .all(),

    "NORMAL equals base forecast":
        np.allclose(

            final[
                "normal_scenario_forecast_units"
            ],

            final[
                "base_forecast_units"
            ],

            atol=1e-10

        ),

    "No realized future weather":
        final[
            "future_realized_weather_used_flag"
        ]
        .eq(0)
        .all(),

    "Weeks 1-3 are NOWCAST_REQUIRED":
        final[
            final[
                "horizon_week"
            ]
            <= 3
        ]
        [
            "weather_horizon_mode"
        ]
        .eq(
            "NOWCAST_REQUIRED"
        )
        .all(),

    "Weeks 4-13 use SCENARIO_ANALOG":
        final[
            final[
                "horizon_week"
            ]
            >= 4
        ]
        [
            "weather_horizon_mode"
        ]
        .eq(
            "SCENARIO_ANALOG"
        )
        .all()

}


overall_pass = (

    all(
        history_checks.values()
    )

    and

    champion_coverage_pass

    and

    champion_family_pass

    and

    all(
        weather_checks.values()
    )

    and

    all(
        base_checks.values()
    )

    and

    weather_merge_pass

    and

    all(
        final_checks.values()
    )

)


print(
    "\n"
    + "=" * 100
)

print(
    "FINAL STEP 4D QA"
)

print(
    "=" * 100
)


for name, passed in final_checks.items():

    print(
        f"{name}:",
        "PASS"
        if passed
        else "FAIL"
    )


# ============================================================
# 24. MODEL FIT AUDIT
# ============================================================

print(
    "\n"
    + "=" * 100
)

print(
    "FINAL MODEL FIT AUDIT"
)

print(
    "=" * 100
)


print(
    fit_audit
    .round(
        {
            "forecast_13w_units": 2
        }
    )
    .to_string(
        index=False
    )
)


# ============================================================
# 25. SERIES-LEVEL FINAL OUTLOOK
# ============================================================

series_summary = (

    final

    .groupby(
        [
            "sku_id",
            "channel_id",
            "champion_model"
        ],

        as_index=False

    )

    .agg(

        base_13w_units=(
            "base_forecast_units",
            "sum"
        ),

        mild_13w_units=(
            "mild_scenario_forecast_units",
            "sum"
        ),

        severe_13w_units=(
            "severe_scenario_forecast_units",
            "sum"
        ),

        avg_mild_adjustment_pct=(
            "mild_scenario_adjustment_pct",
            "mean"
        ),

        avg_severe_adjustment_pct=(
            "severe_scenario_adjustment_pct",
            "mean"
        )

    )

)


series_summary[
    "mild_vs_base_pct"
] = (

    (
        series_summary[
            "mild_13w_units"
        ]

        /

        series_summary[
            "base_13w_units"
        ]

        - 1
    )

    * 100

)


series_summary[
    "severe_vs_base_pct"
] = (

    (
        series_summary[
            "severe_13w_units"
        ]

        /

        series_summary[
            "base_13w_units"
        ]

        - 1
    )

    * 100

)


print(
    "\n"
    + "=" * 100
)

print(
    "13-WEEK FORECAST SUMMARY BY SERIES"
)

print(
    "=" * 100
)


print(
    series_summary
    .round(2)
    .to_string(
        index=False
    )
)


# ============================================================
# 26. PORTFOLIO OUTLOOK
# ============================================================

portfolio_base = (
    final[
        "base_forecast_units"
    ]
    .sum()
)


portfolio_mild = (
    final[
        "mild_scenario_forecast_units"
    ]
    .sum()
)


portfolio_severe = (
    final[
        "severe_scenario_forecast_units"
    ]
    .sum()
)


mild_pct = (

    (
        portfolio_mild
        / portfolio_base
    )

    - 1

) * 100


severe_pct = (

    (
        portfolio_severe
        / portfolio_base
    )

    - 1

) * 100


print(
    "\n"
    + "=" * 100
)

print(
    "PORTFOLIO 13-WEEK DEMAND OUTLOOK"
)

print(
    "=" * 100
)


print(
    f"MILD:          "
    f"{portfolio_mild:,.2f} units "
    f"({mild_pct:+.2f}% vs base)"
)


print(
    f"NORMAL / BASE: "
    f"{portfolio_base:,.2f} units"
)


print(
    f"SEVERE:        "
    f"{portfolio_severe:,.2f} units "
    f"({severe_pct:+.2f}% vs base)"
)


print(
    f"Scenario width: "
    f"{portfolio_severe - portfolio_mild:,.2f} units"
)


# ============================================================
# 27. WEEKLY PORTFOLIO OUTLOOK
# ============================================================

weekly = (

    final

    .groupby(
        [
            "horizon_week",
            "forecast_week_start"
        ],

        as_index=False

    )

    .agg(

        mild_units=(
            "mild_scenario_forecast_units",
            "sum"
        ),

        base_units=(
            "base_forecast_units",
            "sum"
        ),

        severe_units=(
            "severe_scenario_forecast_units",
            "sum"
        )

    )

)


print(
    "\n"
    + "=" * 100
)

print(
    "WEEKLY PORTFOLIO FORECAST"
)

print(
    "=" * 100
)


weekly_display = (
    weekly.copy()
)


for column in [
    "mild_units",
    "base_units",
    "severe_units"
]:

    weekly_display[
        column
    ] = (
        weekly_display[
            column
        ]
        .round(2)
    )


print(
    weekly_display
    .to_string(
        index=False
    )
)


# ============================================================
# 28. SAVE ONE FINAL FILE
# ============================================================

if overall_pass:

    output = (

        final

        .sort_values(
            [
                "forecast_week_start",
                "sku_id",
                "channel_id"
            ]
        )

        .copy()

    )


    numeric_columns = [

        "base_forecast_units",

        "mild_scenario_forecast_units",

        "normal_scenario_forecast_units",

        "severe_scenario_forecast_units",

        "operational_forecast_units",

        "scenario_range_units",

        "scenario_range_pct"

    ]


    for column in numeric_columns:

        output[
            column
        ] = (

            output[
                column
            ]
            .round(3)

        )


    # --------------------------------------------------------
    # Drop duplicate forecast_origin from weather merge if
    # pandas created one.
    # --------------------------------------------------------

    if (
        "forecast_origin_weather"
        in output.columns
    ):

        output = output.drop(
            columns=[
                "forecast_origin_weather"
            ]
        )


    output[
        "forecast_origin"
    ] = (

        pd.to_datetime(
            output[
                "forecast_origin"
            ]
        )

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


    print(
        "\n"
        + "=" * 100
    )

    print(
        "STEP 4D COMPLETE"
    )

    print(
        "=" * 100
    )


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

    print(
        "\n"
        + "=" * 100
    )

    print(
        "STEP 4D FAILED QA"
    )

    print(
        "=" * 100
    )


    print(
        "OVERALL STATUS: FAIL"
    )


    print(
        "Final forecast was NOT saved."
    )


    raise RuntimeError(
        "Step 4D final forecast QA failed."
    )


# ============================================================
# END STEP 4D
# ============================================================