import pandas as pd
import numpy as np
import warnings
import time
from pathlib import Path

from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tools.sm_exceptions import ConvergenceWarning


# ============================================================
# DEMANDIQ
# STEP 4B.5C — TARGETED FULL SARIMA CONFIRMATION
#
# Purpose:
# Full 12-fold confirmation of SARIMA only for the two
# SKU × Channel series that showed potential in the
# 4-fold challenger screen.
#
# Target series:
#   CTS-001 | RETAIL
#   IMH-001 | ECOM
#
# SARIMA:
#   (0,1,1)(0,1,1,52)
#
# IMPORTANT:
# The earlier folds 9–12 exercise was only screening.
# Final SARIMA eligibility is evaluated here over all
# frozen 12 folds.
# ============================================================


# ------------------------------------------------------------
# 1. PATHS
# ------------------------------------------------------------

PROJECT_DIR = Path(r"D:\Downloads\DemandIQ")

FORECAST_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_Forecasting_Input.csv"
)

FOLD_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_Backtest_Folds.csv"
)

BASELINE_SUMMARY_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_Baseline_Summary.csv"
)

ETS_SUMMARY_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_ETS_Summary.csv"
)

PREDICTIONS_OUTPUT = (
    PROJECT_DIR
    / "DemandIQ_Step4B_SARIMA_Targeted_Predictions.csv"
)

FOLD_METRICS_OUTPUT = (
    PROJECT_DIR
    / "DemandIQ_Step4B_SARIMA_Targeted_Fold_Metrics.csv"
)

SUMMARY_OUTPUT = (
    PROJECT_DIR
    / "DemandIQ_Step4B_SARIMA_Targeted_Summary.csv"
)

FIT_QA_OUTPUT = (
    PROJECT_DIR
    / "DemandIQ_Step4B_SARIMA_Targeted_Fit_QA.csv"
)

COMPARISON_OUTPUT = (
    PROJECT_DIR
    / "DemandIQ_Step4B_Targeted_Model_Comparison.csv"
)


# ------------------------------------------------------------
# 2. FROZEN DESIGN
# ------------------------------------------------------------

SEASONAL_PERIOD = 52
FORECAST_HORIZON = 13

MODEL_NAME = "SARIMA_011_011"

ORDER = (
    0,
    1,
    1
)

SEASONAL_ORDER = (
    0,
    1,
    1,
    52
)


TARGET_SERIES = [
    ("CTS-001", "RETAIL"),
    ("IMH-001", "ECOM")
]


EXPECTED_FOLDS = 12

EXPECTED_SERIES = len(
    TARGET_SERIES
)

EXPECTED_FITS = (
    EXPECTED_SERIES
    * EXPECTED_FOLDS
)

EXPECTED_PREDICTIONS = (
    EXPECTED_FITS
    * FORECAST_HORIZON
)


# ------------------------------------------------------------
# 3. LOAD DATA
# ------------------------------------------------------------

df = pd.read_csv(
    FORECAST_FILE
)

fold_df = pd.read_csv(
    FOLD_FILE
)

baseline_summary = pd.read_csv(
    BASELINE_SUMMARY_FILE
)

ets_summary = pd.read_csv(
    ETS_SUMMARY_FILE
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


print("\n" + "=" * 82)
print("STEP 4B.5C — TARGETED FULL SARIMA CONFIRMATION")
print("=" * 82)

print(
    "Target series:"
)

for sku, channel in TARGET_SERIES:

    print(
        f" - {sku} | {channel}"
    )

print(
    "\nExpected fits:",
    EXPECTED_FITS
)

print(
    "Expected predictions:",
    EXPECTED_PREDICTIONS
)


# ------------------------------------------------------------
# 4. METRICS
# ------------------------------------------------------------

def calculate_wape(
    actual,
    forecast
):

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


def calculate_bias(
    actual,
    forecast
):

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


def calculate_mae(
    actual,
    forecast
):

    return np.mean(
        np.abs(
            np.asarray(actual)
            - np.asarray(forecast)
        )
    )


# ------------------------------------------------------------
# 5. STORAGE
# ------------------------------------------------------------

prediction_rows = []

fit_qa_rows = []

fit_counter = 0


# ------------------------------------------------------------
# 6. TARGETED MODEL LOOP
# ------------------------------------------------------------

for sku, channel in TARGET_SERIES:


    series_df = (
        df[
            (
                df["sku_id"] == sku
            )
            &
            (
                df["channel_id"] == channel
            )
        ]
        .sort_values(
            "week_start"
        )
        .reset_index(
            drop=True
        )
    )


    if len(
        series_df
    ) != 260:

        raise ValueError(
            f"Unexpected history length: "
            f"{sku} | {channel}"
        )


    print(
        "\n"
        + "#" * 82
    )

    print(
        f"SERIES: {sku} | {channel}"
    )

    print(
        "#" * 82
    )


    for _, fold in fold_df.iterrows():


        fold_number = int(
            fold["fold"]
        )


        train_df = (
            series_df[
                (
                    series_df[
                        "week_start"
                    ]
                    >=
                    fold[
                        "train_start"
                    ]
                )
                &
                (
                    series_df[
                        "week_start"
                    ]
                    <=
                    fold[
                        "train_end"
                    ]
                )
            ]
            .copy()
        )


        test_df = (
            series_df[
                (
                    series_df[
                        "week_start"
                    ]
                    >=
                    fold[
                        "test_start"
                    ]
                )
                &
                (
                    series_df[
                        "week_start"
                    ]
                    <=
                    fold[
                        "test_end"
                    ]
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


        # --------------------------------------------
        # Frozen-fold QA
        # --------------------------------------------

        chronology_pass = (
            train_df[
                "week_start"
            ].max()
            <
            test_df[
                "week_start"
            ].min()
        )


        horizon_pass = (
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
                chronology_pass,
                horizon_pass,
                seasonal_history_pass
            ]
        ):

            raise ValueError(
                f"Fold QA failure: "
                f"{sku} | {channel} | "
                f"Fold {fold_number}"
            )


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
            .reset_index(
                drop=True
            )
        )


        # --------------------------------------------
        # FIT
        # --------------------------------------------

        fit_counter += 1

        print(
            f"\n[{fit_counter}/{EXPECTED_FITS}] "
            f"FITTING | "
            f"{sku} | {channel} | "
            f"Fold {fold_number} | "
            f"Train={train_weeks}",
            flush=True
        )


        start_time = (
            time.perf_counter()
        )


        fit_status = "SUCCESS"

        optimizer_converged = False

        optimizer_iterations = np.nan

        convergence_warning = False

        warning_messages = []

        warning_categories = []

        error_message = None

        aic = np.nan

        bic = np.nan


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

                    enforce_stationarity=True,

                    enforce_invertibility=True,

                    simple_differencing=False,

                    # Same computational specification
                    # used in the challenger screen.
                    concentrate_scale=True
                )


                fitted = model.fit(

                    disp=False,

                    maxiter=75,

                    method="lbfgs"
                )


                for warning in caught_warnings:


                    warning_messages.append(
                        str(
                            warning.message
                        )
                    )


                    warning_categories.append(
                        warning.category.__name__
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


            bic = float(
                fitted.bic
            )


            forecast = np.asarray(

                fitted.forecast(
                    steps=FORECAST_HORIZON
                ),

                dtype=float
            )


            if (
                len(forecast)
                !=
                FORECAST_HORIZON
            ):

                raise ValueError(
                    "Forecast length != 13."
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

                        "train_start":
                            fold[
                                "train_start"
                            ],

                        "train_end":
                            fold[
                                "train_end"
                            ],

                        "test_start":
                            fold[
                                "test_start"
                            ],

                        "test_end":
                            fold[
                                "test_end"
                            ],

                        "train_weeks":
                            train_weeks
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

                "optimizer_iterations":
                    optimizer_iterations,

                "convergence_warning":
                    convergence_warning,

                "warning_count":
                    len(
                        warning_messages
                    ),

                # IMPORTANT ADDITION:
                "warning_categories":
                    " | ".join(
                        warning_categories
                    ),

                "warning_message":
                    " | ".join(
                        warning_messages
                    ),

                "aic":
                    aic,

                "bic":
                    bic,

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


# ------------------------------------------------------------
# 7. CREATE DATAFRAMES
# ------------------------------------------------------------

predictions_df = pd.DataFrame(
    prediction_rows
)

fit_qa_df = pd.DataFrame(
    fit_qa_rows
)


# ------------------------------------------------------------
# 8. STRUCTURAL QA
# ------------------------------------------------------------

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


fit_count_pass = (
    len(fit_qa_df)
    == EXPECTED_FITS
)


all_fits_pass = (
    failed_fits == 0
)


prediction_count_pass = (
    len(predictions_df)
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


finite_pass = (
    np.isfinite(
        predictions_df[
            "forecast_units"
        ]
    )
    .all()
)


negative_pass = (
    predictions_df[
        "forecast_units"
    ]
    .lt(0)
    .sum()
    == 0
)


duplicate_count = (
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


duplicate_pass = (
    duplicate_count == 0
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


print("\n" + "=" * 82)
print("TARGETED SARIMA QA")
print("=" * 82)

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
    len(
        predictions_df
    )
)

print(
    "Expected predictions:",
    EXPECTED_PREDICTIONS
)

print(
    "Fit count:",
    "PASS" if fit_count_pass else "FAIL"
)

print(
    "All fits successful:",
    "PASS" if all_fits_pass else "FAIL"
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
    "Finite forecasts:",
    "PASS" if finite_pass else "FAIL"
)

print(
    "No negative forecasts:",
    "PASS" if negative_pass else "FAIL"
)

print(
    "Prediction grain unique:",
    "PASS" if duplicate_pass else "FAIL"
)

print(
    "No chronological leakage:",
    "PASS" if leakage_pass else "FAIL"
)


# ------------------------------------------------------------
# 9. WARNING REVIEW
# ------------------------------------------------------------

print("\n" + "=" * 82)
print("WARNING REVIEW")
print("=" * 82)


warning_summary = (
    fit_qa_df[
        fit_qa_df[
            "warning_count"
        ] > 0
    ]
    .groupby(
        [
            "warning_categories",
            "warning_message"
        ]
    )
    .size()
    .reset_index(
        name="fit_count"
    )
)


if len(
    warning_summary
) > 0:

    print(
        warning_summary
        .to_string(
            index=False
        )
    )

else:

    print(
        "No warnings captured."
    )


# ------------------------------------------------------------
# 10. FOLD METRICS
# ------------------------------------------------------------

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

            "test_observations":
                len(actual)
        }
    )


fold_metrics_df = pd.DataFrame(
    fold_metric_rows
)


# ------------------------------------------------------------
# 11. FULL 12-FOLD SARIMA SUMMARY
# ------------------------------------------------------------

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
                fm[
                    "wape_pct"
                ].mean(),

            "median_fold_wape_pct":
                fm[
                    "wape_pct"
                ].median(),

            "std_fold_wape_pct":
                fm[
                    "wape_pct"
                ].std(),

            "worst_fold_wape_pct":
                fm[
                    "wape_pct"
                ].max(),

            "folds_evaluated":
                len(fm),

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
                .sum(),

            "backtest_observations":
                len(group)
        }
    )


summary_df = pd.DataFrame(
    summary_rows
)


# ------------------------------------------------------------
# 12. COMPARE AGAINST FULL 12-FOLD BASELINES + ETS
# ------------------------------------------------------------

comparison_rows = []


for sku, channel in TARGET_SERIES:


    baseline_candidates = (
        baseline_summary[
            (
                baseline_summary[
                    "sku_id"
                ] == sku
            )
            &
            (
                baseline_summary[
                    "channel_id"
                ] == channel
            )
        ]
        .sort_values(
            "pooled_wape_pct"
        )
    )


    ets_candidates = (
        ets_summary[
            (
                ets_summary[
                    "sku_id"
                ] == sku
            )
            &
            (
                ets_summary[
                    "channel_id"
                ] == channel
            )
        ]
        .sort_values(
            "pooled_wape_pct"
        )
    )


    sarima_row = (
        summary_df[
            (
                summary_df[
                    "sku_id"
                ] == sku
            )
            &
            (
                summary_df[
                    "channel_id"
                ] == channel
            )
        ]
        .iloc[0]
    )


    best_baseline = (
        baseline_candidates
        .iloc[0]
    )


    best_ets = (
        ets_candidates
        .iloc[0]
    )


    candidates = pd.DataFrame(
        [
            {
                "model":
                    best_baseline[
                        "model"
                    ],

                "family":
                    "BASELINE",

                "wape":
                    best_baseline[
                        "pooled_wape_pct"
                    ],

                "bias":
                    best_baseline[
                        "pooled_bias_pct"
                    ],

                "std":
                    best_baseline[
                        "std_fold_wape_pct"
                    ],

                "worst":
                    best_baseline[
                        "worst_fold_wape_pct"
                    ]
            },

            {
                "model":
                    best_ets[
                        "model"
                    ],

                "family":
                    "ETS",

                "wape":
                    best_ets[
                        "pooled_wape_pct"
                    ],

                "bias":
                    best_ets[
                        "pooled_bias_pct"
                    ],

                "std":
                    best_ets[
                        "std_fold_wape_pct"
                    ],

                "worst":
                    best_ets[
                        "worst_fold_wape_pct"
                    ]
            },

            {
                "model":
                    MODEL_NAME,

                "family":
                    "SARIMA",

                "wape":
                    sarima_row[
                        "pooled_wape_pct"
                    ],

                "bias":
                    sarima_row[
                        "pooled_bias_pct"
                    ],

                "std":
                    sarima_row[
                        "std_fold_wape_pct"
                    ],

                "worst":
                    sarima_row[
                        "worst_fold_wape_pct"
                    ]
            }
        ]
    )


    candidates = (
        candidates
        .sort_values(
            "wape"
        )
        .reset_index(
            drop=True
        )
    )


    best = candidates.iloc[0]


    second = candidates.iloc[1]


    comparison_rows.append(
        {
            "sku_id":
                sku,

            "channel_id":
                channel,

            "best_model_by_wape":
                best[
                    "model"
                ],

            "best_family":
                best[
                    "family"
                ],

            "best_wape_pct":
                best[
                    "wape"
                ],

            "best_bias_pct":
                best[
                    "bias"
                ],

            "best_std_fold_wape":
                best[
                    "std"
                ],

            "best_worst_fold_wape":
                best[
                    "worst"
                ],

            "second_model":
                second[
                    "model"
                ],

            "second_family":
                second[
                    "family"
                ],

            "second_wape_pct":
                second[
                    "wape"
                ],

            "wape_advantage_pp":
                (
                    second[
                        "wape"
                    ]
                    -
                    best[
                        "wape"
                    ]
                ),

            "sarima_wape_pct":
                sarima_row[
                    "pooled_wape_pct"
                ],

            "sarima_bias_pct":
                sarima_row[
                    "pooled_bias_pct"
                ]
        }
    )


comparison_df = pd.DataFrame(
    comparison_rows
)


# ------------------------------------------------------------
# 13. DISPLAY RESULTS
# ------------------------------------------------------------

print("\n" + "=" * 82)
print("FULL 12-FOLD SARIMA SUMMARY")
print("=" * 82)


summary_display = (
    summary_df.copy()
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


print(
    summary_display
    .to_string(
        index=False
    )
)


print("\n" + "=" * 82)
print("FULL 12-FOLD MODEL COMPARISON")
print("=" * 82)


comparison_display = (
    comparison_df.copy()
)


comparison_numeric = [
    "best_wape_pct",
    "best_bias_pct",
    "best_std_fold_wape",
    "best_worst_fold_wape",
    "second_wape_pct",
    "wape_advantage_pp",
    "sarima_wape_pct",
    "sarima_bias_pct"
]


comparison_display[
    comparison_numeric
] = (
    comparison_display[
        comparison_numeric
    ]
    .round(2)
)


print(
    comparison_display
    .to_string(
        index=False
    )
)


# ------------------------------------------------------------
# 14. FINAL QA
# ------------------------------------------------------------

overall_pass = all(
    [
        fit_count_pass,
        all_fits_pass,
        prediction_count_pass,
        null_pass,
        finite_pass,
        negative_pass,
        duplicate_pass,
        leakage_pass
    ]
)


print("\n" + "=" * 82)
print("FINAL STEP 4B.5C QA")
print("=" * 82)


print(
    "24 expected fits:",
    "PASS"
    if fit_count_pass
    else "FAIL"
)

print(
    "All fits successful:",
    "PASS"
    if all_fits_pass
    else "FAIL"
)

print(
    "312 expected predictions:",
    "PASS"
    if prediction_count_pass
    else "FAIL"
)

print(
    "No null forecasts:",
    "PASS"
    if null_pass
    else "FAIL"
)

print(
    "Finite forecasts:",
    "PASS"
    if finite_pass
    else "FAIL"
)

print(
    "No negative forecasts:",
    "PASS"
    if negative_pass
    else "FAIL"
)

print(
    "Prediction grain unique:",
    "PASS"
    if duplicate_pass
    else "FAIL"
)

print(
    "No chronological leakage:",
    "PASS"
    if leakage_pass
    else "FAIL"
)


# ------------------------------------------------------------
# 15. SAVE
# ------------------------------------------------------------

fit_qa_df.to_csv(
    FIT_QA_OUTPUT,
    index=False
)


if overall_pass:


    predictions_df.to_csv(
        PREDICTIONS_OUTPUT,
        index=False,
        date_format="%Y-%m-%d"
    )


    fold_metrics_df.to_csv(
        FOLD_METRICS_OUTPUT,
        index=False
    )


    summary_df.to_csv(
        SUMMARY_OUTPUT,
        index=False
    )


    comparison_df.to_csv(
        COMPARISON_OUTPUT,
        index=False
    )


    print(
        "\nOVERALL STATUS: PASS — "
        "Targeted full SARIMA confirmation complete."
    )


else:


    print(
        "\nOVERALL STATUS: FAIL — "
        "Do not use SARIMA results for champion selection."
    )