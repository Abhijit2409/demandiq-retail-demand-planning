import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# DEMANDIQ
# STEP 4B.3 — BASELINE FORECASTING MODELS
#
# Models:
# 1. Seasonal Naive:
#       forecast(t) = actual(t - 52 weeks)
#
# 2. 2-Year Seasonal Moving Average:
#       forecast(t) =
#       mean(actual(t - 52 weeks),
#            actual(t - 104 weeks))
#
# Evaluation:
# - WAPE
# - Bias
# - MAE
# - Fold stability
#
# IMPORTANT:
# Forecast references must come ONLY from the training window.
# No weather.
# No hidden true demand.
# No test-period leakage.
# ============================================================


# ------------------------------------------------------------
# 1. FILE PATHS
# ------------------------------------------------------------

PROJECT_DIR = Path(r"D:\Downloads\DemandIQ")

FORECAST_INPUT_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_Forecasting_Input.csv"
)

FOLD_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_Backtest_Folds.csv"
)

PREDICTIONS_OUTPUT_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_Baseline_Predictions.csv"
)

FOLD_METRICS_OUTPUT_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_Baseline_Fold_Metrics.csv"
)

SUMMARY_OUTPUT_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_Baseline_Summary.csv"
)


# ------------------------------------------------------------
# 2. DESIGN CONSTANTS
# ------------------------------------------------------------

SEASONAL_PERIOD = 52
SECOND_SEASONAL_LAG = 104

EXPECTED_SERIES = 9
EXPECTED_FOLDS = 12
FORECAST_HORIZON = 13

EXPECTED_PREDICTIONS_PER_MODEL = (
    EXPECTED_SERIES
    * EXPECTED_FOLDS
    * FORECAST_HORIZON
)

EXPECTED_TOTAL_PREDICTIONS = (
    EXPECTED_PREDICTIONS_PER_MODEL
    * 2
)


# ------------------------------------------------------------
# 3. LOAD DATA
# ------------------------------------------------------------

df = pd.read_csv(
    FORECAST_INPUT_FILE
)

fold_df = pd.read_csv(
    FOLD_FILE
)


df["week_start"] = pd.to_datetime(
    df["week_start"]
)


for column in [
    "train_start",
    "train_end",
    "test_start",
    "test_end"
]:

    fold_df[column] = pd.to_datetime(
        fold_df[column]
    )


print("\n" + "=" * 75)
print("STEP 4B.3 — BASELINE FORECASTING")
print("=" * 75)

print(
    "Forecast input shape:",
    df.shape
)

print(
    "Fold table shape:",
    fold_df.shape
)


# ------------------------------------------------------------
# 4. BASIC INPUT QA
# ------------------------------------------------------------

expected_columns = {
    "week_start",
    "sku_id",
    "channel_id",
    "reconstructed_demand_units"
}


input_schema_pass = (
    set(df.columns)
    == expected_columns
)

fold_count_pass = (
    len(fold_df)
    == EXPECTED_FOLDS
)

series_count = (
    df[
        ["sku_id", "channel_id"]
    ]
    .drop_duplicates()
    .shape[0]
)

series_count_pass = (
    series_count
    == EXPECTED_SERIES
)


print("\n" + "=" * 75)
print("INPUT QA")
print("=" * 75)

print(
    "Forecast input schema:",
    "PASS"
    if input_schema_pass
    else "FAIL"
)

print(
    "12 folds loaded:",
    "PASS"
    if fold_count_pass
    else "FAIL"
)

print(
    "9 forecast series:",
    "PASS"
    if series_count_pass
    else "FAIL"
)


if not all(
    [
        input_schema_pass,
        fold_count_pass,
        series_count_pass
    ]
):

    raise ValueError(
        "Input QA failed. "
        "Do not continue to baseline modelling."
    )


# ------------------------------------------------------------
# 5. METRIC FUNCTIONS
# ------------------------------------------------------------

def calculate_wape(actual, forecast):

    denominator = actual.sum()

    if denominator == 0:
        return np.nan

    return (
        np.abs(
            actual - forecast
        ).sum()
        / denominator
        * 100
    )


def calculate_bias(actual, forecast):

    denominator = actual.sum()

    if denominator == 0:
        return np.nan

    # Positive = overforecast
    # Negative = underforecast

    return (
        (
            forecast - actual
        ).sum()
        / denominator
        * 100
    )


def calculate_mae(actual, forecast):

    return np.abs(
        actual - forecast
    ).mean()


# ------------------------------------------------------------
# 6. GENERATE BASELINE PREDICTIONS
# ------------------------------------------------------------

prediction_rows = []

reference_failures = []


series_groups = df.groupby(
    [
        "sku_id",
        "channel_id"
    ]
)


for (sku, channel), series_df in series_groups:

    series_df = (
        series_df
        .sort_values(
            "week_start"
        )
        .reset_index(drop=True)
    )


    for _, fold in fold_df.iterrows():

        fold_number = int(
            fold["fold"]
        )

        train_start = (
            fold["train_start"]
        )

        train_end = (
            fold["train_end"]
        )

        test_start = (
            fold["test_start"]
        )

        test_end = (
            fold["test_end"]
        )


        # ----------------------------------------------------
        # Training and test slices
        # ----------------------------------------------------

        train_df = (
            series_df[
                (
                    series_df["week_start"]
                    >= train_start
                )
                &
                (
                    series_df["week_start"]
                    <= train_end
                )
            ]
            .copy()
        )

        test_df = (
            series_df[
                (
                    series_df["week_start"]
                    >= test_start
                )
                &
                (
                    series_df["week_start"]
                    <= test_end
                )
            ]
            .copy()
        )


        # ----------------------------------------------------
        # Training lookup
        #
        # Only training data enters this dictionary.
        # Therefore test-period observations cannot be used
        # as forecast references.
        # ----------------------------------------------------

        train_lookup = (
            train_df
            .set_index(
                "week_start"
            )
            [
                "reconstructed_demand_units"
            ]
            .to_dict()
        )


        # ----------------------------------------------------
        # Forecast every week in the 13-week test horizon
        # ----------------------------------------------------

        for _, test_row in test_df.iterrows():

            forecast_date = (
                test_row["week_start"]
            )

            actual = (
                test_row[
                    "reconstructed_demand_units"
                ]
            )


            # -----------------------------------------------
            # Seasonal reference dates
            # -----------------------------------------------

            lag52_date = (
                forecast_date
                - pd.Timedelta(
                    weeks=SEASONAL_PERIOD
                )
            )

            lag104_date = (
                forecast_date
                - pd.Timedelta(
                    weeks=SECOND_SEASONAL_LAG
                )
            )


            # -----------------------------------------------
            # Hard leakage / availability checks
            # -----------------------------------------------

            lag52_available = (
                lag52_date
                in train_lookup
            )

            lag104_available = (
                lag104_date
                in train_lookup
            )


            if not (
                lag52_available
                and lag104_available
            ):

                reference_failures.append(
                    {
                        "fold": fold_number,
                        "sku_id": sku,
                        "channel_id": channel,
                        "forecast_date": forecast_date,
                        "lag52_date": lag52_date,
                        "lag104_date": lag104_date,
                        "lag52_available": lag52_available,
                        "lag104_available": lag104_available
                    }
                )

                continue


            # -----------------------------------------------
            # Retrieve seasonal training values
            # -----------------------------------------------

            lag52_value = (
                train_lookup[
                    lag52_date
                ]
            )

            lag104_value = (
                train_lookup[
                    lag104_date
                ]
            )


            # -----------------------------------------------
            # MODEL 1 — SEASONAL NAIVE
            # -----------------------------------------------

            seasonal_naive_forecast = (
                lag52_value
            )


            prediction_rows.append(
                {
                    "fold": fold_number,
                    "sku_id": sku,
                    "channel_id": channel,
                    "forecast_date": forecast_date,
                    "actual_units": actual,
                    "model": "Seasonal_Naive",
                    "forecast_units": seasonal_naive_forecast,
                    "reference_1_date": lag52_date,
                    "reference_2_date": pd.NaT
                }
            )


            # -----------------------------------------------
            # MODEL 2 — 2-YEAR SEASONAL MOVING AVERAGE
            # -----------------------------------------------

            seasonal_ma_forecast = (
                lag52_value
                + lag104_value
            ) / 2


            prediction_rows.append(
                {
                    "fold": fold_number,
                    "sku_id": sku,
                    "channel_id": channel,
                    "forecast_date": forecast_date,
                    "actual_units": actual,
                    "model": "Seasonal_MA_2Y",
                    "forecast_units": seasonal_ma_forecast,
                    "reference_1_date": lag52_date,
                    "reference_2_date": lag104_date
                }
            )


# ------------------------------------------------------------
# 7. CREATE PREDICTIONS DATAFRAME
# ------------------------------------------------------------

predictions_df = pd.DataFrame(
    prediction_rows
)


print("\n" + "=" * 75)
print("PREDICTION GENERATION QA")
print("=" * 75)


# ------------------------------------------------------------
# QA — Seasonal references available
# ------------------------------------------------------------

reference_pass = (
    len(reference_failures)
    == 0
)


print(
    "All seasonal references found in training:",
    "PASS"
    if reference_pass
    else "FAIL"
)


if not reference_pass:

    print(
        "\nReference failures:"
    )

    print(
        pd.DataFrame(
            reference_failures
        )
    )


# ------------------------------------------------------------
# QA — Prediction count
# ------------------------------------------------------------

prediction_count = (
    len(predictions_df)
)

prediction_count_pass = (
    prediction_count
    == EXPECTED_TOTAL_PREDICTIONS
)


print(
    "Prediction rows:",
    prediction_count
)

print(
    "Expected prediction rows:",
    EXPECTED_TOTAL_PREDICTIONS
)

print(
    "Prediction count:",
    "PASS"
    if prediction_count_pass
    else "FAIL"
)


# ------------------------------------------------------------
# QA — Predictions per model
# ------------------------------------------------------------

predictions_per_model = (
    predictions_df[
        "model"
    ]
    .value_counts()
)


print(
    "\nPredictions per model:"
)

print(
    predictions_per_model
)


model_count_pass = (
    predictions_per_model
    .eq(
        EXPECTED_PREDICTIONS_PER_MODEL
    )
    .all()
    and
    len(
        predictions_per_model
    ) == 2
)


print(
    "\nExpected rows per model:",
    EXPECTED_PREDICTIONS_PER_MODEL
)

print(
    "Rows per model:",
    "PASS"
    if model_count_pass
    else "FAIL"
)


# ------------------------------------------------------------
# QA — Null forecasts
# ------------------------------------------------------------

null_forecasts = (
    predictions_df[
        "forecast_units"
    ]
    .isna()
    .sum()
)

null_forecast_pass = (
    null_forecasts == 0
)


print(
    "Null forecasts:",
    null_forecasts
)

print(
    "Null forecast check:",
    "PASS"
    if null_forecast_pass
    else "FAIL"
)


# ------------------------------------------------------------
# QA — Negative forecasts
# ------------------------------------------------------------

negative_forecasts = (
    predictions_df[
        "forecast_units"
    ] < 0
).sum()

negative_forecast_pass = (
    negative_forecasts == 0
)


print(
    "Negative forecasts:",
    negative_forecasts
)

print(
    "Negative forecast check:",
    "PASS"
    if negative_forecast_pass
    else "FAIL"
)


# ------------------------------------------------------------
# QA — Duplicate forecast rows
# ------------------------------------------------------------

duplicate_predictions = (
    predictions_df
    .duplicated(
        subset=[
            "fold",
            "sku_id",
            "channel_id",
            "forecast_date",
            "model"
        ]
    )
    .sum()
)

duplicate_prediction_pass = (
    duplicate_predictions == 0
)


print(
    "Duplicate prediction rows:",
    duplicate_predictions
)

print(
    "Prediction-grain uniqueness:",
    "PASS"
    if duplicate_prediction_pass
    else "FAIL"
)


# ------------------------------------------------------------
# QA — References are not future/test observations
# ------------------------------------------------------------

reference_1_leakage = (
    predictions_df[
        "reference_1_date"
    ]
    >=
    predictions_df[
        "forecast_date"
    ]
).sum()


reference_2_non_null = (
    predictions_df[
        "reference_2_date"
    ]
    .notna()
)


reference_2_leakage = (
    predictions_df.loc[
        reference_2_non_null,
        "reference_2_date"
    ]
    >=
    predictions_df.loc[
        reference_2_non_null,
        "forecast_date"
    ]
).sum()


reference_date_pass = (
    reference_1_leakage == 0
    and
    reference_2_leakage == 0
)


print(
    "Future/reference-date leakage rows:",
    (
        reference_1_leakage
        + reference_2_leakage
    )
)

print(
    "Reference date leakage check:",
    "PASS"
    if reference_date_pass
    else "FAIL"
)


# ------------------------------------------------------------
# 8. CALCULATE FOLD-LEVEL METRICS
# ------------------------------------------------------------

fold_metric_rows = []


for (
    fold_number,
    sku,
    channel,
    model
), group in predictions_df.groupby(
    [
        "fold",
        "sku_id",
        "channel_id",
        "model"
    ]
):

    actual = (
        group[
            "actual_units"
        ]
    )

    forecast = (
        group[
            "forecast_units"
        ]
    )


    wape = calculate_wape(
        actual,
        forecast
    )

    bias = calculate_bias(
        actual,
        forecast
    )

    mae = calculate_mae(
        actual,
        forecast
    )


    fold_metric_rows.append(
        {
            "fold": fold_number,
            "sku_id": sku,
            "channel_id": channel,
            "model": model,
            "wape_pct": wape,
            "bias_pct": bias,
            "mae_units": mae,
            "actual_units_total": actual.sum(),
            "forecast_units_total": forecast.sum(),
            "test_observations": len(group)
        }
    )


fold_metrics_df = pd.DataFrame(
    fold_metric_rows
)


# ------------------------------------------------------------
# 9. FOLD METRIC QA
# ------------------------------------------------------------

expected_fold_metric_rows = (
    EXPECTED_SERIES
    * EXPECTED_FOLDS
    * 2
)


fold_metric_count_pass = (
    len(
        fold_metrics_df
    )
    == expected_fold_metric_rows
)


test_observation_pass = (
    fold_metrics_df[
        "test_observations"
    ]
    .eq(
        FORECAST_HORIZON
    )
    .all()
)


print("\n" + "=" * 75)
print("FOLD METRIC QA")
print("=" * 75)

print(
    "Fold metric rows:",
    len(
        fold_metrics_df
    )
)

print(
    "Expected fold metric rows:",
    expected_fold_metric_rows
)

print(
    "Fold metric count:",
    "PASS"
    if fold_metric_count_pass
    else "FAIL"
)

print(
    "13 observations per fold/model/series:",
    "PASS"
    if test_observation_pass
    else "FAIL"
)


# ------------------------------------------------------------
# 10. CREATE MODEL SUMMARY BY SKU × CHANNEL
# ------------------------------------------------------------

summary_rows = []


for (
    sku,
    channel,
    model
), prediction_group in predictions_df.groupby(
    [
        "sku_id",
        "channel_id",
        "model"
    ]
):

    actual = (
        prediction_group[
            "actual_units"
        ]
    )

    forecast = (
        prediction_group[
            "forecast_units"
        ]
    )


    # --------------------------------------------------------
    # Pooled metrics across all 12 folds
    # --------------------------------------------------------

    pooled_wape = calculate_wape(
        actual,
        forecast
    )

    pooled_bias = calculate_bias(
        actual,
        forecast
    )

    pooled_mae = calculate_mae(
        actual,
        forecast
    )


    # --------------------------------------------------------
    # Fold stability
    # --------------------------------------------------------

    model_fold_metrics = (
        fold_metrics_df[
            (
                fold_metrics_df[
                    "sku_id"
                ] == sku
            )
            &
            (
                fold_metrics_df[
                    "channel_id"
                ] == channel
            )
            &
            (
                fold_metrics_df[
                    "model"
                ] == model
            )
        ]
    )


    mean_fold_wape = (
        model_fold_metrics[
            "wape_pct"
        ]
        .mean()
    )

    median_fold_wape = (
        model_fold_metrics[
            "wape_pct"
        ]
        .median()
    )

    std_fold_wape = (
        model_fold_metrics[
            "wape_pct"
        ]
        .std()
    )

    worst_fold_wape = (
        model_fold_metrics[
            "wape_pct"
        ]
        .max()
    )


    summary_rows.append(
        {
            "sku_id": sku,
            "channel_id": channel,
            "model": model,
            "pooled_wape_pct": pooled_wape,
            "pooled_bias_pct": pooled_bias,
            "pooled_mae_units": pooled_mae,
            "mean_fold_wape_pct": mean_fold_wape,
            "median_fold_wape_pct": median_fold_wape,
            "std_fold_wape_pct": std_fold_wape,
            "worst_fold_wape_pct": worst_fold_wape,
            "folds_evaluated": len(
                model_fold_metrics
            ),
            "backtest_observations": len(
                prediction_group
            )
        }
    )


summary_df = pd.DataFrame(
    summary_rows
)


# ------------------------------------------------------------
# 11. ROUND DISPLAY COPIES
# ------------------------------------------------------------

fold_metrics_display = (
    fold_metrics_df.copy()
)

summary_display = (
    summary_df.copy()
)


numeric_fold_columns = [
    "wape_pct",
    "bias_pct",
    "mae_units",
    "actual_units_total",
    "forecast_units_total"
]


numeric_summary_columns = [
    "pooled_wape_pct",
    "pooled_bias_pct",
    "pooled_mae_units",
    "mean_fold_wape_pct",
    "median_fold_wape_pct",
    "std_fold_wape_pct",
    "worst_fold_wape_pct"
]


fold_metrics_display[
    numeric_fold_columns
] = (
    fold_metrics_display[
        numeric_fold_columns
    ]
    .round(2)
)


summary_display[
    numeric_summary_columns
] = (
    summary_display[
        numeric_summary_columns
    ]
    .round(2)
)


# ------------------------------------------------------------
# 12. FINAL QA
# ------------------------------------------------------------

all_checks_pass = all(
    [
        reference_pass,
        prediction_count_pass,
        model_count_pass,
        null_forecast_pass,
        negative_forecast_pass,
        duplicate_prediction_pass,
        reference_date_pass,
        fold_metric_count_pass,
        test_observation_pass
    ]
)


print("\n" + "=" * 75)
print("FINAL STEP 4B.3 QA")
print("=" * 75)


qa_results = {
    "Seasonal references available in training":
        reference_pass,

    "Expected total prediction count":
        prediction_count_pass,

    "Expected prediction count per model":
        model_count_pass,

    "No null forecasts":
        null_forecast_pass,

    "No negative forecasts":
        negative_forecast_pass,

    "Prediction grain unique":
        duplicate_prediction_pass,

    "No seasonal-reference leakage":
        reference_date_pass,

    "Expected fold metric count":
        fold_metric_count_pass,

    "13 observations per test fold":
        test_observation_pass
}


for check_name, status in qa_results.items():

    print(
        f"{check_name}:",
        "PASS" if status else "FAIL"
    )


print("\n" + "-" * 75)


if all_checks_pass:

    print(
        "OVERALL STATUS: PASS — "
        "Baseline forecasts and backtest metrics are valid."
    )

else:

    print(
        "OVERALL STATUS: FAIL — "
        "Do not interpret baseline results."
    )


print("-" * 75)


# ------------------------------------------------------------
# 13. DISPLAY BASELINE SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 75)
print("BASELINE MODEL SUMMARY")
print("=" * 75)


summary_display = (
    summary_display
    .sort_values(
        [
            "sku_id",
            "channel_id",
            "pooled_wape_pct"
        ]
    )
)


print(
    summary_display
    .to_string(
        index=False
    )
)


# ------------------------------------------------------------
# 14. SAVE OUTPUTS ONLY IF QA PASSES
# ------------------------------------------------------------

if all_checks_pass:

    predictions_df.to_csv(
    PREDICTIONS_OUTPUT_FILE,
    index=False,
    date_format="%Y-%m-%d"
    )

    fold_metrics_df.to_csv(
        FOLD_METRICS_OUTPUT_FILE,
        index=False
    )

    summary_df.to_csv(
        SUMMARY_OUTPUT_FILE,
        index=False
    )


    print("\n" + "=" * 75)
    print("OUTPUT FILES SAVED")
    print("=" * 75)

    print(
        PREDICTIONS_OUTPUT_FILE
    )

    print(
        FOLD_METRICS_OUTPUT_FILE
    )

    print(
        SUMMARY_OUTPUT_FILE
    )

else:

    print(
        "\nOutputs NOT saved because QA failed."
    )


# ============================================================
# END STEP 4B.3
# ============================================================