import pandas as pd
import numpy as np
import warnings
import time
from pathlib import Path

from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tools.sm_exceptions import ConvergenceWarning


# ============================================================
# DEMANDIQ
# STEP 4B.5 — SARIMA CHALLENGER SCREEN
#
# Purpose:
# Screen one canonical SARIMA challenger against the existing
# ETS / baseline results without running an expensive
# 324-model search.
#
# IMPORTANT:
# This is a SCREENING evaluation using folds 9–12.
# It is not presented as the full 12-fold SARIMA backtest.
# ============================================================


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
    / "DemandIQ_Step4B_SARIMA_Screen_Predictions.csv"
)

FOLD_METRICS_OUTPUT_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_SARIMA_Screen_Fold_Metrics.csv"
)

SUMMARY_OUTPUT_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_SARIMA_Screen_Summary.csv"
)

FIT_QA_OUTPUT_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_SARIMA_Screen_Fit_QA.csv"
)


# ============================================================
# FROZEN / SCREENING DESIGN
# ============================================================

SEASONAL_PERIOD = 52
FORECAST_HORIZON = 13

# Recent four folds cover approximately one annual cycle.
SCREEN_FOLDS = [9, 10, 11, 12]

MODEL_NAME = "SARIMA_011_011"

ORDER = (0, 1, 1)

SEASONAL_ORDER = (
    0,
    1,
    1,
    52
)

EXPECTED_SERIES = 9
EXPECTED_SCREEN_FOLDS = 4

EXPECTED_FITS = (
    EXPECTED_SERIES
    * EXPECTED_SCREEN_FOLDS
)

EXPECTED_PREDICTIONS = (
    EXPECTED_FITS
    * FORECAST_HORIZON
)


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(
    FORECAST_INPUT_FILE
)

fold_df = pd.read_csv(
    FOLD_FILE
)


df["week_start"] = pd.to_datetime(
    df["week_start"]
)


for col in [
    "train_start",
    "train_end",
    "test_start",
    "test_end"
]:

    fold_df[col] = pd.to_datetime(
        fold_df[col]
    )


# Keep only screen folds
screen_fold_df = (
    fold_df[
        fold_df["fold"].isin(
            SCREEN_FOLDS
        )
    ]
    .copy()
    .sort_values("fold")
)


print("\n" + "=" * 80)
print("STEP 4B.5 — SARIMA CHALLENGER SCREEN")
print("=" * 80)

print("Input shape:", df.shape)

print(
    "Screen folds:",
    screen_fold_df["fold"].tolist()
)

print(
    "SARIMA order:",
    ORDER
)

print(
    "Seasonal order:",
    SEASONAL_ORDER
)

print(
    "Expected fits:",
    EXPECTED_FITS
)


# ============================================================
# METRICS
# ============================================================

def wape(actual, forecast):

    actual = np.asarray(
        actual,
        dtype=float
    )

    forecast = np.asarray(
        forecast,
        dtype=float
    )

    return (
        np.abs(
            actual - forecast
        ).sum()
        / actual.sum()
        * 100
    )


def bias(actual, forecast):

    actual = np.asarray(
        actual,
        dtype=float
    )

    forecast = np.asarray(
        forecast,
        dtype=float
    )

    return (
        (
            forecast - actual
        ).sum()
        / actual.sum()
        * 100
    )


def mae(actual, forecast):

    return np.mean(
        np.abs(
            np.asarray(actual)
            - np.asarray(forecast)
        )
    )


# ============================================================
# STORAGE
# ============================================================

prediction_rows = []

fit_qa_rows = []

fit_counter = 0


# ============================================================
# MODEL LOOP
# ============================================================

for (
    sku,
    channel
), series_df in df.groupby(
    [
        "sku_id",
        "channel_id"
    ]
):

    series_df = (
        series_df
        .sort_values("week_start")
        .reset_index(drop=True)
    )


    for _, fold in screen_fold_df.iterrows():

        fold_number = int(
            fold["fold"]
        )

        train_df = series_df[
            (
                series_df["week_start"]
                >= fold["train_start"]
            )
            &
            (
                series_df["week_start"]
                <= fold["train_end"]
            )
        ].copy()


        test_df = series_df[
            (
                series_df["week_start"]
                >= fold["test_start"]
            )
            &
            (
                series_df["week_start"]
                <= fold["test_end"]
            )
        ].copy()


        train_y = (
            train_df[
                "reconstructed_demand_units"
            ]
            .astype(float)
            .to_numpy()
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


        fit_counter += 1

        print(
            f"\n[{fit_counter}/{EXPECTED_FITS}] "
            f"FITTING | "
            f"{sku} | {channel} | "
            f"Fold {fold_number}",
            flush=True
        )


        start_time = time.perf_counter()

        fit_status = "SUCCESS"

        convergence_warning = False

        warning_messages = []

        error_message = None

        optimizer_converged = False

        optimizer_iterations = np.nan

        aic = np.nan


        try:

            with warnings.catch_warnings(
                record=True
            ) as caught_warnings:

                warnings.simplefilter(
                    "always"
                )


                model = SARIMAX(

                    train_y,

                    order=ORDER,

                    seasonal_order=SEASONAL_ORDER,

                    trend=None,

                    # Keep original-level forecasts.
                    simple_differencing=False,

                    enforce_stationarity=True,

                    enforce_invertibility=True,

                    # Reduce one ML parameter.
                    concentrate_scale=True
                )


                fitted = model.fit(

                    disp=False,

                    # Lower than 200 because this is screening.
                    maxiter=75,

                    method="lbfgs"
                )


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


            mle_retvals = getattr(
                fitted,
                "mle_retvals",
                {}
            )


            optimizer_converged = bool(
                mle_retvals.get(
                    "converged",
                    True
                )
            )


            optimizer_iterations = (
                mle_retvals.get(
                    "iterations",
                    np.nan
                )
            )


            aic = float(
                fitted.aic
            )


            forecast = np.asarray(

                fitted.forecast(
                    steps=FORECAST_HORIZON
                ),

                dtype=float
            )


            if len(forecast) != 13:

                raise ValueError(
                    "Forecast horizon != 13."
                )


            if not np.isfinite(
                forecast
            ).all():

                raise ValueError(
                    "Non-finite forecast."
                )


            for i in range(
                FORECAST_HORIZON
            ):

                prediction_rows.append(
                    {
                        "fold":
                            fold_number,

                        "sku_id":
                            sku,

                        "channel_id":
                            channel,

                        "forecast_date":
                            test_dates.iloc[i],

                        "actual_units":
                            actual[i],

                        "model":
                            MODEL_NAME,

                        "forecast_units":
                            forecast[i],

                        "train_end":
                            fold["train_end"]
                    }
                )


        except Exception as error:

            fit_status = "FAIL"

            error_message = str(
                error
            )


        elapsed = (
            time.perf_counter()
            - start_time
        )


        fit_qa_rows.append(
            {
                "fold":
                    fold_number,

                "sku_id":
                    sku,

                "channel_id":
                    channel,

                "model":
                    MODEL_NAME,

                "fit_status":
                    fit_status,

                "optimizer_converged":
                    optimizer_converged,

                "convergence_warning":
                    convergence_warning,

                "warning_count":
                    len(
                        warning_messages
                    ),

                "optimizer_iterations":
                    optimizer_iterations,

                "aic":
                    aic,

                "fit_seconds":
                    elapsed,

                "error_message":
                    error_message
            }
        )


        print(
            f"[{fit_counter}/{EXPECTED_FITS}] "
            f"{fit_status} | "
            f"Converged={optimizer_converged} | "
            f"Warnings={len(warning_messages)} | "
            f"Seconds={elapsed:.2f}",
            flush=True
        )


# ============================================================
# CREATE DATAFRAMES
# ============================================================

predictions_df = pd.DataFrame(
    prediction_rows
)

fit_qa_df = pd.DataFrame(
    fit_qa_rows
)


# ============================================================
# STRUCTURAL QA
# ============================================================

successful_fits = (
    fit_qa_df[
        "fit_status"
    ]
    .eq("SUCCESS")
    .sum()
)


failed_fits = (
    fit_qa_df[
        "fit_status"
    ]
    .eq("FAIL")
    .sum()
)


prediction_count = len(
    predictions_df
)


expected_fit_pass = (
    len(fit_qa_df)
    == EXPECTED_FITS
)


all_fit_pass = (
    failed_fits == 0
)


prediction_count_pass = (
    prediction_count
    == EXPECTED_PREDICTIONS
)


null_pass = (
    predictions_df[
        "forecast_units"
    ]
    .isna()
    .sum()
    == 0
)


negative_pass = (
    predictions_df[
        "forecast_units"
    ]
    .lt(0)
    .sum()
    == 0
)


leakage_pass = (
    predictions_df[
        "forecast_date"
    ]
    .gt(
        predictions_df[
            "train_end"
        ]
    )
    .all()
)


print("\n" + "=" * 80)
print("SARIMA SCREEN QA")
print("=" * 80)

print(
    "Expected fits:",
    EXPECTED_FITS
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
    "Prediction rows:",
    prediction_count
)

print(
    "Expected prediction rows:",
    EXPECTED_PREDICTIONS
)

print(
    "Fit count:",
    "PASS" if expected_fit_pass else "FAIL"
)

print(
    "All fits successful:",
    "PASS" if all_fit_pass else "FAIL"
)

print(
    "Prediction count:",
    "PASS"
    if prediction_count_pass
    else "FAIL"
)

print(
    "No null forecasts:",
    "PASS" if null_pass else "FAIL"
)

print(
    "No negative forecasts:",
    "PASS" if negative_pass else "FAIL"
)

print(
    "No chronological leakage:",
    "PASS" if leakage_pass else "FAIL"
)


# ============================================================
# FOLD METRICS
# ============================================================

fold_metric_rows = []


for (
    fold,
    sku,
    channel
), group in predictions_df.groupby(
    [
        "fold",
        "sku_id",
        "channel_id"
    ]
):

    actual = group[
        "actual_units"
    ].to_numpy()

    forecast = group[
        "forecast_units"
    ].to_numpy()


    fold_metric_rows.append(
        {
            "fold":
                fold,

            "sku_id":
                sku,

            "channel_id":
                channel,

            "model":
                MODEL_NAME,

            "wape_pct":
                wape(
                    actual,
                    forecast
                ),

            "bias_pct":
                bias(
                    actual,
                    forecast
                ),

            "mae_units":
                mae(
                    actual,
                    forecast
                )
        }
    )


fold_metrics_df = pd.DataFrame(
    fold_metric_rows
)


# ============================================================
# SERIES SUMMARY
# ============================================================

summary_rows = []


for (
    sku,
    channel
), group in predictions_df.groupby(
    [
        "sku_id",
        "channel_id"
    ]
):

    actual = group[
        "actual_units"
    ].to_numpy()

    forecast = group[
        "forecast_units"
    ].to_numpy()


    fm = fold_metrics_df[
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
    ]


    qa = fit_qa_df[
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
    ]


    summary_rows.append(
        {
            "sku_id":
                sku,

            "channel_id":
                channel,

            "model":
                MODEL_NAME,

            "screen_folds":
                "9-12",

            "pooled_wape_pct":
                wape(
                    actual,
                    forecast
                ),

            "pooled_bias_pct":
                bias(
                    actual,
                    forecast
                ),

            "pooled_mae_units":
                mae(
                    actual,
                    forecast
                ),

            "mean_fold_wape_pct":
                fm[
                    "wape_pct"
                ].mean(),

            "std_fold_wape_pct":
                fm[
                    "wape_pct"
                ].std(),

            "worst_fold_wape_pct":
                fm[
                    "wape_pct"
                ].max(),

            "nonconverged_folds":
                (
                    ~qa[
                        "optimizer_converged"
                    ]
                ).sum(),

            "warning_folds":
                qa[
                    "warning_count"
                ]
                .gt(0)
                .sum()
        }
    )


summary_df = pd.DataFrame(
    summary_rows
)


print("\n" + "=" * 80)
print("SARIMA SCREEN SUMMARY")
print("=" * 80)

display_summary = (
    summary_df.copy()
)

numeric_cols = [
    "pooled_wape_pct",
    "pooled_bias_pct",
    "pooled_mae_units",
    "mean_fold_wape_pct",
    "std_fold_wape_pct",
    "worst_fold_wape_pct"
]

display_summary[
    numeric_cols
] = (
    display_summary[
        numeric_cols
    ]
    .round(2)
)

print(
    display_summary
    .to_string(
        index=False
    )
)


# ============================================================
# SAVE
# ============================================================

overall_pass = all(
    [
        expected_fit_pass,
        all_fit_pass,
        prediction_count_pass,
        null_pass,
        negative_pass,
        leakage_pass
    ]
)


fit_qa_df.to_csv(
    FIT_QA_OUTPUT_FILE,
    index=False
)


if overall_pass:

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

    print(
        "\nOVERALL STATUS: PASS — "
        "SARIMA challenger screen complete."
    )

else:

    print(
        "\nOVERALL STATUS: FAIL — "
        "Do not interpret SARIMA results."
    )