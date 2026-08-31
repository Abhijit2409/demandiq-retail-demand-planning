import pandas as pd
import numpy as np
import warnings
from pathlib import Path

from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tools.sm_exceptions import ConvergenceWarning


# ============================================================
# DEMANDIQ
# STEP 4B.4 — HOLT-WINTERS / ETS BACKTEST
#
# Primary forecasting grain:
#     SKU × Channel
#
# Target:
#     reconstructed_demand_units
#
# Frozen backtest:
#     Seasonal period        = 52 weeks
#     Initial training       = 104 weeks
#     Forecast horizon       = 13 weeks
#     Step size              = 13 weeks
#     Folds                  = 12
#     Window                 = expanding
#
# Models:
#     1. HW_Add_Add
#     2. HW_Damped_Add
#     3. HW_Damped_Mul
#
# Metrics:
#     WAPE
#     Bias
#     MAE
#     Fold stability
#
# IMPORTANT:
# - No weather
# - No true_demand_units
# - No hidden generator variables
# - No test-period information enters model fitting
# ============================================================


# ------------------------------------------------------------
# 1. PATHS
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
    / "DemandIQ_Step4B_ETS_Predictions.csv"
)

FOLD_METRICS_OUTPUT_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_ETS_Fold_Metrics.csv"
)

SUMMARY_OUTPUT_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_ETS_Summary.csv"
)

FIT_QA_OUTPUT_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_ETS_Fit_QA.csv"
)


# ------------------------------------------------------------
# 2. FROZEN DESIGN CONSTANTS
# ------------------------------------------------------------

SEASONAL_PERIOD = 52
FORECAST_HORIZON = 13

EXPECTED_SERIES = 9
EXPECTED_FOLDS = 12


# ------------------------------------------------------------
# 3. GOVERNED MODEL FAMILY
#
# We deliberately test only a small interpretable family.
# No automated hyperparameter sweep.
# ------------------------------------------------------------

MODEL_CONFIGS = {

    "HW_Add_Add": {
        "trend": "add",
        "seasonal": "add",
        "damped_trend": False
    },

    "HW_Damped_Add": {
        "trend": "add",
        "seasonal": "add",
        "damped_trend": True
    },

    "HW_Damped_Mul": {
        "trend": "add",
        "seasonal": "mul",
        "damped_trend": True
    }
}


EXPECTED_MODELS = len(
    MODEL_CONFIGS
)

EXPECTED_FITS = (
    EXPECTED_SERIES
    * EXPECTED_FOLDS
    * EXPECTED_MODELS
)

EXPECTED_PREDICTIONS = (
    EXPECTED_FITS
    * FORECAST_HORIZON
)

EXPECTED_FOLD_METRICS = (
    EXPECTED_FITS
)

EXPECTED_SUMMARY_ROWS = (
    EXPECTED_SERIES
    * EXPECTED_MODELS
)


# ------------------------------------------------------------
# 4. LOAD DATA
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


print("\n" + "=" * 78)
print("STEP 4B.4 — HOLT-WINTERS / ETS BACKTEST")
print("=" * 78)

print(
    "Forecast input shape:",
    df.shape
)

print(
    "Fold file shape:",
    fold_df.shape
)

print(
    "Models:",
    list(
        MODEL_CONFIGS.keys()
    )
)


# ------------------------------------------------------------
# 5. INPUT QA
# ------------------------------------------------------------

EXPECTED_INPUT_COLUMNS = [
    "week_start",
    "sku_id",
    "channel_id",
    "reconstructed_demand_units"
]


input_schema_pass = (
    list(df.columns)
    == EXPECTED_INPUT_COLUMNS
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


null_target_pass = (
    df[
        "reconstructed_demand_units"
    ]
    .isna()
    .sum()
    == 0
)


positive_target_pass = (
    df[
        "reconstructed_demand_units"
    ]
    .gt(0)
    .all()
)


print("\n" + "=" * 78)
print("INPUT QA")
print("=" * 78)

print(
    "Exact forecasting-input schema:",
    "PASS"
    if input_schema_pass
    else "FAIL"
)

print(
    "12 frozen folds loaded:",
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

print(
    "No null targets:",
    "PASS"
    if null_target_pass
    else "FAIL"
)

print(
    "Strictly positive target:",
    "PASS"
    if positive_target_pass
    else "FAIL"
)


input_qa_pass = all(
    [
        input_schema_pass,
        fold_count_pass,
        series_count_pass,
        null_target_pass,
        positive_target_pass
    ]
)


if not input_qa_pass:

    raise ValueError(
        "Input QA failed. "
        "Do not fit ETS models."
    )


# ------------------------------------------------------------
# 6. METRIC FUNCTIONS
# ------------------------------------------------------------

def calculate_wape(actual, forecast):

    actual = np.asarray(
        actual,
        dtype=float
    )

    forecast = np.asarray(
        forecast,
        dtype=float
    )

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

    actual = np.asarray(
        actual,
        dtype=float
    )

    forecast = np.asarray(
        forecast,
        dtype=float
    )

    denominator = actual.sum()

    if denominator == 0:
        return np.nan

    # Positive bias = overforecast
    # Negative bias = underforecast

    return (
        (
            forecast - actual
        ).sum()
        / denominator
        * 100
    )


def calculate_mae(actual, forecast):

    actual = np.asarray(
        actual,
        dtype=float
    )

    forecast = np.asarray(
        forecast,
        dtype=float
    )

    return np.abs(
        actual - forecast
    ).mean()


# ------------------------------------------------------------
# 7. PREPARE SERIES
# ------------------------------------------------------------

series_groups = df.groupby(
    [
        "sku_id",
        "channel_id"
    ]
)


prediction_rows = []

fit_qa_rows = []


# ------------------------------------------------------------
# 8. BACKTEST ALL ETS CONFIGURATIONS
# ------------------------------------------------------------

for (
    sku,
    channel
), series_df in series_groups:


    series_df = (
        series_df
        .sort_values(
            "week_start"
        )
        .reset_index(
            drop=True
        )
    )


    # --------------------------------------------------------
    # Loop through frozen folds
    # --------------------------------------------------------

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
        # Training data
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


        # ----------------------------------------------------
        # Test data
        # ----------------------------------------------------

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


        train_weeks = len(
            train_df
        )

        test_weeks = len(
            test_df
        )


        # ----------------------------------------------------
        # Hard chronological QA
        # ----------------------------------------------------

        train_test_boundary_pass = (
            train_df[
                "week_start"
            ].max()
            <
            test_df[
                "week_start"
            ].min()
        )


        test_horizon_pass = (
            test_weeks
            == FORECAST_HORIZON
        )


        seasonal_history_pass = (
            train_weeks
            >=
            2 * SEASONAL_PERIOD
        )


        if not all(
            [
                train_test_boundary_pass,
                test_horizon_pass,
                seasonal_history_pass
            ]
        ):

            raise ValueError(
                f"Fold QA failure: "
                f"{sku} | {channel} | Fold {fold_number}"
            )


        train_y = (
            train_df[
                "reconstructed_demand_units"
            ]
            .astype(float)
            .reset_index(drop=True)
        )


        actual = (
            test_df[
                "reconstructed_demand_units"
            ]
            .astype(float)
            .to_numpy()
        )


        test_dates = (
            test_df[
                "week_start"
            ]
            .reset_index(drop=True)
        )


        # ----------------------------------------------------
        # Fit each governed ETS model
        # ----------------------------------------------------

        for (
            model_name,
            config
        ) in MODEL_CONFIGS.items():


            fit_status = "SUCCESS"

            convergence_warning = False

            warning_messages = []

            error_message = None


            try:


                # --------------------------------------------
                # Multiplicative seasonality requires
                # strictly positive training data.
                # --------------------------------------------

                if (
                    config["seasonal"]
                    == "mul"
                    and
                    (
                        train_y <= 0
                    ).any()
                ):

                    raise ValueError(
                        "Multiplicative seasonality requires "
                        "strictly positive training values."
                    )


                # --------------------------------------------
                # Capture convergence warnings
                # --------------------------------------------

                with warnings.catch_warnings(
                    record=True
                ) as caught_warnings:


                    warnings.simplefilter(
                        "always"
                    )


                    model = (
                        ExponentialSmoothing(
                            train_y,

                            trend=(
                                config[
                                    "trend"
                                ]
                            ),

                            damped_trend=(
                                config[
                                    "damped_trend"
                                ]
                            ),

                            seasonal=(
                                config[
                                    "seasonal"
                                ]
                            ),

                            seasonal_periods=(
                                SEASONAL_PERIOD
                            ),

                            initialization_method=(
                                "estimated"
                            )
                        )
                    )


                    fitted_model = (
                        model.fit(
                            optimized=True,
                            remove_bias=False
                        )
                    )


                    forecast = np.asarray(
                        fitted_model.forecast(
                            FORECAST_HORIZON
                        ),
                        dtype=float
                    )


                    # ----------------------------------------
                    # Record warnings
                    # ----------------------------------------

                    for warning in caught_warnings:

                        warning_messages.append(
                            str(
                                warning.message
                            )
                        )

                        if issubclass(
                            warning.category,
                            ConvergenceWarning
                        ):

                            convergence_warning = True


                # --------------------------------------------
                # Forecast length QA
                # --------------------------------------------

                if (
                    len(forecast)
                    != FORECAST_HORIZON
                ):

                    raise ValueError(
                        "Forecast length does not equal "
                        "13-week horizon."
                    )


                # --------------------------------------------
                # Null forecast QA
                # --------------------------------------------

                if np.isnan(
                    forecast
                ).any():

                    raise ValueError(
                        "Model produced null forecast."
                    )


                # --------------------------------------------
                # Do NOT clip negative forecasts.
                #
                # If ETS produces negatives, we want QA
                # to expose that rather than hide it.
                # --------------------------------------------


                for i in range(
                    FORECAST_HORIZON
                ):


                    prediction_rows.append(
                        {
                            "fold": fold_number,

                            "sku_id": sku,

                            "channel_id": channel,

                            "forecast_date":
                                test_dates.iloc[i],

                            "actual_units":
                                actual[i],

                            "model":
                                model_name,

                            "forecast_units":
                                forecast[i],

                            "train_start":
                                train_start,

                            "train_end":
                                train_end,

                            "test_start":
                                test_start,

                            "test_end":
                                test_end,

                            "train_weeks":
                                train_weeks
                        }
                    )


            except Exception as error:


                fit_status = "FAIL"

                error_message = str(
                    error
                )


            # ------------------------------------------------
            # Fit QA row
            # ------------------------------------------------

            fit_qa_rows.append(
                {
                    "fold": fold_number,

                    "sku_id": sku,

                    "channel_id": channel,

                    "model": model_name,

                    "train_weeks":
                        train_weeks,

                    "test_weeks":
                        test_weeks,

                    "fit_status":
                        fit_status,

                    "convergence_warning":
                        convergence_warning,

                    "warning_count":
                        len(
                            warning_messages
                        ),

                    "warning_message":
                        " | ".join(
                            warning_messages
                        ),

                    "error_message":
                        error_message
                }
            )


# ------------------------------------------------------------
# 9. CREATE DATAFRAMES
# ------------------------------------------------------------

predictions_df = pd.DataFrame(
    prediction_rows
)

fit_qa_df = pd.DataFrame(
    fit_qa_rows
)


# ------------------------------------------------------------
# 10. FIT QA
# ------------------------------------------------------------

fit_attempts = len(
    fit_qa_df
)

successful_fits = (
    fit_qa_df[
        "fit_status"
    ]
    .eq(
        "SUCCESS"
    )
    .sum()
)

failed_fits = (
    fit_qa_df[
        "fit_status"
    ]
    .eq(
        "FAIL"
    )
    .sum()
)

convergence_warnings = (
    fit_qa_df[
        "convergence_warning"
    ]
    .sum()
)


fit_attempt_count_pass = (
    fit_attempts
    == EXPECTED_FITS
)

all_fits_successful = (
    failed_fits == 0
)


print("\n" + "=" * 78)
print("MODEL FIT QA")
print("=" * 78)

print(
    "Expected fits:",
    EXPECTED_FITS
)

print(
    "Fit attempts:",
    fit_attempts
)

print(
    "Successful fits:",
    successful_fits
)

print(
    "Failed fits:",
    failed_fits
)

print(
    "Convergence warnings:",
    convergence_warnings
)

print(
    "Expected fit count:",
    "PASS"
    if fit_attempt_count_pass
    else "FAIL"
)

print(
    "All fits successful:",
    "PASS"
    if all_fits_successful
    else "FAIL"
)


# ------------------------------------------------------------
# 11. PREDICTION QA
# ------------------------------------------------------------

prediction_count = len(
    predictions_df
)

prediction_count_pass = (
    prediction_count
    == EXPECTED_PREDICTIONS
)


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


negative_forecasts = (
    predictions_df[
        "forecast_units"
    ]
    .lt(0)
    .sum()
)


negative_forecast_pass = (
    negative_forecasts == 0
)


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


prediction_grain_pass = (
    duplicate_predictions == 0
)


# ------------------------------------------------------------
# Test date vs train date leakage check
# ------------------------------------------------------------

date_leakage_rows = (
    predictions_df[
        "forecast_date"
    ]
    .le(
        predictions_df[
            "train_end"
        ]
    )
    .sum()
)


date_leakage_pass = (
    date_leakage_rows == 0
)


print("\n" + "=" * 78)
print("PREDICTION QA")
print("=" * 78)

print(
    "Prediction rows:",
    prediction_count
)

print(
    "Expected prediction rows:",
    EXPECTED_PREDICTIONS
)

print(
    "Prediction count:",
    "PASS"
    if prediction_count_pass
    else "FAIL"
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

print(
    "Duplicate prediction rows:",
    duplicate_predictions
)

print(
    "Prediction grain:",
    "PASS"
    if prediction_grain_pass
    else "FAIL"
)

print(
    "Train/test date leakage rows:",
    date_leakage_rows
)

print(
    "Chronological leakage check:",
    "PASS"
    if date_leakage_pass
    else "FAIL"
)


# ------------------------------------------------------------
# 12. CALCULATE FOLD METRICS
# ------------------------------------------------------------

fold_metric_rows = []


for (
    fold_number,
    sku,
    channel,
    model_name
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
        .to_numpy()
    )

    forecast = (
        group[
            "forecast_units"
        ]
        .to_numpy()
    )


    fold_metric_rows.append(
        {
            "fold":
                fold_number,

            "sku_id":
                sku,

            "channel_id":
                channel,

            "model":
                model_name,

            "wape_pct":
                calculate_wape(
                    actual,
                    forecast
                ),

            "bias_pct":
                calculate_bias(
                    actual,
                    forecast
                ),

            "mae_units":
                calculate_mae(
                    actual,
                    forecast
                ),

            "actual_units_total":
                actual.sum(),

            "forecast_units_total":
                forecast.sum(),

            "test_observations":
                len(
                    actual
                )
        }
    )


fold_metrics_df = pd.DataFrame(
    fold_metric_rows
)


# ------------------------------------------------------------
# 13. FOLD METRIC QA
# ------------------------------------------------------------

fold_metric_count_pass = (
    len(
        fold_metrics_df
    )
    == EXPECTED_FOLD_METRICS
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


print("\n" + "=" * 78)
print("FOLD METRIC QA")
print("=" * 78)

print(
    "Fold metric rows:",
    len(
        fold_metrics_df
    )
)

print(
    "Expected fold metric rows:",
    EXPECTED_FOLD_METRICS
)

print(
    "Fold metric count:",
    "PASS"
    if fold_metric_count_pass
    else "FAIL"
)

print(
    "13 observations per fold:",
    "PASS"
    if test_observation_pass
    else "FAIL"
)


# ------------------------------------------------------------
# 14. CREATE SKU × CHANNEL MODEL SUMMARY
# ------------------------------------------------------------

summary_rows = []


for (
    sku,
    channel,
    model_name
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
        .to_numpy()
    )

    forecast = (
        prediction_group[
            "forecast_units"
        ]
        .to_numpy()
    )


    relevant_fold_metrics = (
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
                ] == model_name
            )
        ]
    )


    relevant_fit_qa = (
        fit_qa_df[
            (
                fit_qa_df[
                    "sku_id"
                ] == sku
            )
            &
            (
                fit_qa_df[
                    "channel_id"
                ] == channel
            )
            &
            (
                fit_qa_df[
                    "model"
                ] == model_name
            )
        ]
    )


    summary_rows.append(
        {
            "sku_id":
                sku,

            "channel_id":
                channel,

            "model":
                model_name,

            "pooled_wape_pct":
                calculate_wape(
                    actual,
                    forecast
                ),

            "pooled_bias_pct":
                calculate_bias(
                    actual,
                    forecast
                ),

            "pooled_mae_units":
                calculate_mae(
                    actual,
                    forecast
                ),

            "mean_fold_wape_pct":
                relevant_fold_metrics[
                    "wape_pct"
                ].mean(),

            "median_fold_wape_pct":
                relevant_fold_metrics[
                    "wape_pct"
                ].median(),

            "std_fold_wape_pct":
                relevant_fold_metrics[
                    "wape_pct"
                ].std(),

            "worst_fold_wape_pct":
                relevant_fold_metrics[
                    "wape_pct"
                ].max(),

            "folds_evaluated":
                len(
                    relevant_fold_metrics
                ),

            "convergence_warning_folds":
                relevant_fit_qa[
                    "convergence_warning"
                ].sum(),

            "backtest_observations":
                len(
                    prediction_group
                )
        }
    )


summary_df = pd.DataFrame(
    summary_rows
)


# ------------------------------------------------------------
# 15. SUMMARY QA
# ------------------------------------------------------------

summary_count_pass = (
    len(
        summary_df
    )
    == EXPECTED_SUMMARY_ROWS
)


folds_per_summary_pass = (
    summary_df[
        "folds_evaluated"
    ]
    .eq(
        EXPECTED_FOLDS
    )
    .all()
)


print("\n" + "=" * 78)
print("SUMMARY QA")
print("=" * 78)

print(
    "Summary rows:",
    len(
        summary_df
    )
)

print(
    "Expected summary rows:",
    EXPECTED_SUMMARY_ROWS
)

print(
    "Summary row count:",
    "PASS"
    if summary_count_pass
    else "FAIL"
)

print(
    "12 folds per model/series:",
    "PASS"
    if folds_per_summary_pass
    else "FAIL"
)


# ------------------------------------------------------------
# 16. FINAL STEP 4B.4 QA
#
# Convergence warnings are reported but are NOT automatically
# treated as a hard failure if forecasts were successfully
# generated. We will review them before champion selection.
# ------------------------------------------------------------

all_checks_pass = all(
    [
        input_qa_pass,
        fit_attempt_count_pass,
        all_fits_successful,
        prediction_count_pass,
        null_forecast_pass,
        negative_forecast_pass,
        prediction_grain_pass,
        date_leakage_pass,
        fold_metric_count_pass,
        test_observation_pass,
        summary_count_pass,
        folds_per_summary_pass
    ]
)


print("\n" + "=" * 78)
print("FINAL STEP 4B.4 QA")
print("=" * 78)


qa_results = {

    "Input QA":
        input_qa_pass,

    "Expected fit attempts":
        fit_attempt_count_pass,

    "All model fits successful":
        all_fits_successful,

    "Expected prediction rows":
        prediction_count_pass,

    "No null forecasts":
        null_forecast_pass,

    "No negative forecasts":
        negative_forecast_pass,

    "Prediction grain unique":
        prediction_grain_pass,

    "No chronological leakage":
        date_leakage_pass,

    "Expected fold metric rows":
        fold_metric_count_pass,

    "13 observations per fold":
        test_observation_pass,

    "Expected summary rows":
        summary_count_pass,

    "12 folds per summary":
        folds_per_summary_pass
}


for (
    check_name,
    status
) in qa_results.items():

    print(
        f"{check_name}:",
        "PASS"
        if status
        else "FAIL"
    )


print("\nConvergence warnings:", convergence_warnings)


print("\n" + "-" * 78)


if all_checks_pass:

    print(
        "OVERALL STATUS: PASS — "
        "ETS backtest outputs are structurally valid."
    )

else:

    print(
        "OVERALL STATUS: FAIL — "
        "Do not interpret ETS performance yet."
    )


print("-" * 78)


# ------------------------------------------------------------
# 17. DISPLAY MODEL SUMMARY
# ------------------------------------------------------------

summary_display = (
    summary_df
    .copy()
)


numeric_columns = [
    "pooled_wape_pct",
    "pooled_bias_pct",
    "pooled_mae_units",
    "mean_fold_wape_pct",
    "median_fold_wape_pct",
    "std_fold_wape_pct",
    "worst_fold_wape_pct"
]


summary_display[
    numeric_columns
] = (
    summary_display[
        numeric_columns
    ]
    .round(2)
)


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


print("\n" + "=" * 78)
print("ETS MODEL SUMMARY")
print("=" * 78)


print(
    summary_display
    .to_string(
        index=False
    )
)


# ------------------------------------------------------------
# 18. SAVE FIT QA
#
# Fit QA is useful even when another QA fails because it tells
# us exactly which model/fold failed.
# ------------------------------------------------------------

fit_qa_df.to_csv(
    FIT_QA_OUTPUT_FILE,
    index=False
)


# ------------------------------------------------------------
# 19. SAVE MODEL OUTPUTS ONLY IF QA PASSES
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


    print("\n" + "=" * 78)
    print("OUTPUT FILES SAVED")
    print("=" * 78)

    print(
        PREDICTIONS_OUTPUT_FILE
    )

    print(
        FOLD_METRICS_OUTPUT_FILE
    )

    print(
        SUMMARY_OUTPUT_FILE
    )

    print(
        FIT_QA_OUTPUT_FILE
    )


else:

    print(
        "\nMain ETS outputs NOT saved because QA failed."
    )

    print(
        "Fit QA was still saved for debugging:"
    )

    print(
        FIT_QA_OUTPUT_FILE
    )


# ============================================================
# END STEP 4B.4
# ============================================================