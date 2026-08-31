import pandas as pd
from pathlib import Path


# ============================================================
# DEMANDIQ
# STEP 4B.2 — BACKTEST FOLD GENERATOR
#
# Purpose:
# Create expanding-window rolling-origin backtest folds
# for the 9 SKU × Channel weekly forecasting series.
#
# No forecasting models are fitted in this script.
# ============================================================


# ------------------------------------------------------------
# 1. FILE PATHS
# ------------------------------------------------------------

PROJECT_DIR = Path(r"D:\Downloads\DemandIQ")

INPUT_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_Forecasting_Input.csv"
)


# ------------------------------------------------------------
# 2. BACKTEST DESIGN
# ------------------------------------------------------------

SEASONAL_PERIOD = 52

INITIAL_TRAIN_WEEKS = 104

FORECAST_HORIZON = 13

STEP_SIZE = 13


# ------------------------------------------------------------
# 3. LOAD FORECASTING INPUT
# ------------------------------------------------------------

df = pd.read_csv(
    INPUT_FILE
)

df["week_start"] = pd.to_datetime(
    df["week_start"]
)


print("\n" + "=" * 72)
print("STEP 4B.2 — BACKTEST DESIGN")
print("=" * 72)

print("Input file:", INPUT_FILE)
print("Rows:", len(df))
print("Columns:", df.columns.tolist())


# ------------------------------------------------------------
# 4. GET MASTER WEEKLY CALENDAR
#
# The 4B.1 QA already confirmed that all 9 series share
# the same weekly calendar.
# ------------------------------------------------------------

calendar = (
    df["week_start"]
    .drop_duplicates()
    .sort_values()
    .reset_index(drop=True)
)


TOTAL_WEEKS = len(
    calendar
)


print("\n" + "=" * 72)
print("CALENDAR SUMMARY")
print("=" * 72)

print("Total weeks:", TOTAL_WEEKS)
print("First week:", calendar.iloc[0].date())
print("Last week:", calendar.iloc[-1].date())


# ------------------------------------------------------------
# 5. VALIDATE BASIC BACKTEST FEASIBILITY
# ------------------------------------------------------------

minimum_required_weeks = (
    INITIAL_TRAIN_WEEKS
    + FORECAST_HORIZON
)


if TOTAL_WEEKS < minimum_required_weeks:

    raise ValueError(
        "Not enough history to create even one backtest fold."
    )


# ------------------------------------------------------------
# 6. CALCULATE NUMBER OF FOLDS
#
# Formula:
#
# floor(
#     (TOTAL_WEEKS
#      - INITIAL_TRAIN_WEEKS
#      - FORECAST_HORIZON)
#     / STEP_SIZE
# ) + 1
#
# For DemandIQ:
#
# (260 - 104 - 13) / 13 + 1
# = 12 folds
# ------------------------------------------------------------

N_FOLDS = (
    (
        TOTAL_WEEKS
        - INITIAL_TRAIN_WEEKS
        - FORECAST_HORIZON
    )
    // STEP_SIZE
) + 1


print("\n" + "=" * 72)
print("BACKTEST PARAMETERS")
print("=" * 72)

print("Seasonal period:", SEASONAL_PERIOD)
print("Initial training weeks:", INITIAL_TRAIN_WEEKS)
print("Forecast horizon:", FORECAST_HORIZON)
print("Step size:", STEP_SIZE)
print("Expected folds:", N_FOLDS)


# ------------------------------------------------------------
# 7. GENERATE EXPANDING-WINDOW FOLDS
# ------------------------------------------------------------

folds = []


for fold_number in range(
    1,
    N_FOLDS + 1
):

    # Expanding training window:
    # Fold 1 ends after 104 weeks
    # Fold 2 ends after 117 weeks
    # Fold 3 ends after 130 weeks
    # etc.

    train_end_idx = (
        INITIAL_TRAIN_WEEKS
        + (fold_number - 1) * STEP_SIZE
    )

    test_start_idx = train_end_idx

    test_end_idx = (
        test_start_idx
        + FORECAST_HORIZON
    )


    # --------------------------------------------
    # Slice calendar
    # --------------------------------------------

    train_dates = calendar.iloc[
        :train_end_idx
    ]

    test_dates = calendar.iloc[
        test_start_idx:test_end_idx
    ]


    # --------------------------------------------
    # Store fold metadata
    # --------------------------------------------

    fold_info = {
        "fold": fold_number,

        "train_start": train_dates.iloc[0],

        "train_end": train_dates.iloc[-1],

        "test_start": test_dates.iloc[0],

        "test_end": test_dates.iloc[-1],

        "train_weeks": len(train_dates),

        "test_weeks": len(test_dates)
    }


    folds.append(
        fold_info
    )


# ------------------------------------------------------------
# 8. CREATE FOLD TABLE
# ------------------------------------------------------------

fold_df = pd.DataFrame(
    folds
)


# ------------------------------------------------------------
# 9. PRINT EACH FOLD
# ------------------------------------------------------------

print("\n" + "=" * 72)
print("ROLLING-ORIGIN FOLDS")
print("=" * 72)


for _, row in fold_df.iterrows():

    print(
        f"\nFold {int(row['fold'])}"
    )

    print(
        "Train:",
        row["train_start"].date(),
        "→",
        row["train_end"].date()
    )

    print(
        "Test: ",
        row["test_start"].date(),
        "→",
        row["test_end"].date()
    )

    print(
        "Train weeks:",
        int(row["train_weeks"])
    )

    print(
        "Test weeks:",
        int(row["test_weeks"])
    )


# ------------------------------------------------------------
# 10. BACKTEST DESIGN QA
# ------------------------------------------------------------

print("\n" + "=" * 72)
print("BACKTEST DESIGN QA")
print("=" * 72)


# --------------------------------------------
# QA 1 — Expected number of folds
# --------------------------------------------

fold_count_pass = (
    len(fold_df) == 12
)


print(
    "12 folds created:",
    "PASS" if fold_count_pass else "FAIL"
)


# --------------------------------------------
# QA 2 — First fold has 104 training weeks
# --------------------------------------------

initial_train_pass = (
    fold_df.iloc[0]["train_weeks"]
    == INITIAL_TRAIN_WEEKS
)


print(
    "Initial training window = 104 weeks:",
    "PASS" if initial_train_pass else "FAIL"
)


# --------------------------------------------
# QA 3 — Every test window has 13 weeks
# --------------------------------------------

test_horizon_pass = (
    fold_df["test_weeks"]
    .eq(
        FORECAST_HORIZON
    )
    .all()
)


print(
    "Every test horizon = 13 weeks:",
    "PASS" if test_horizon_pass else "FAIL"
)


# --------------------------------------------
# QA 4 — Training window expands by 13 weeks
# --------------------------------------------

train_growth = (
    fold_df[
        "train_weeks"
    ]
    .diff()
    .dropna()
)


expanding_window_pass = (
    train_growth
    .eq(
        STEP_SIZE
    )
    .all()
)


print(
    "Training window expands by 13 weeks:",
    "PASS" if expanding_window_pass else "FAIL"
)


# --------------------------------------------
# QA 5 — Test begins immediately after train
# --------------------------------------------

boundary_pass = True


for _, row in fold_df.iterrows():

    expected_test_start = (
        row["train_end"]
        + pd.Timedelta(
            days=7
        )
    )

    if (
        row["test_start"]
        != expected_test_start
    ):

        boundary_pass = False
        break


print(
    "Test starts immediately after training:",
    "PASS" if boundary_pass else "FAIL"
)


# --------------------------------------------
# QA 6 — No train/test overlap
# --------------------------------------------

no_overlap_pass = (
    fold_df[
        "train_end"
    ]
    <
    fold_df[
        "test_start"
    ]
).all()


print(
    "No train/test overlap:",
    "PASS" if no_overlap_pass else "FAIL"
)


# --------------------------------------------
# QA 7 — Final fold reaches final dataset week
# --------------------------------------------

final_week_pass = (
    fold_df.iloc[-1][
        "test_end"
    ]
    == calendar.iloc[-1]
)


print(
    "Final fold reaches final historical week:",
    "PASS" if final_week_pass else "FAIL"
)


# --------------------------------------------
# QA 8 — Seasonal-history requirement
# --------------------------------------------

seasonal_history_pass = (
    fold_df[
        "train_weeks"
    ]
    .min()
    >=
    2 * SEASONAL_PERIOD
)


print(
    "Minimum 2 full seasonal cycles in training:",
    "PASS" if seasonal_history_pass else "FAIL"
)


# ------------------------------------------------------------
# 11. OVERALL QA STATUS
# ------------------------------------------------------------

all_checks_pass = all(
    [
        fold_count_pass,
        initial_train_pass,
        test_horizon_pass,
        expanding_window_pass,
        boundary_pass,
        no_overlap_pass,
        final_week_pass,
        seasonal_history_pass
    ]
)


print("\n" + "-" * 72)


if all_checks_pass:

    print(
        "OVERALL STATUS: PASS — "
        "Rolling-origin backtest design is valid."
    )

else:

    print(
        "OVERALL STATUS: FAIL — "
        "Review backtest design before modelling."
    )


print("-" * 72)


# ------------------------------------------------------------
# 12. DISPLAY FINAL FOLD TABLE
# ------------------------------------------------------------

print("\n" + "=" * 72)
print("FINAL FOLD TABLE")
print("=" * 72)


display_fold_df = (
    fold_df.copy()
)


for column in [
    "train_start",
    "train_end",
    "test_start",
    "test_end"
]:

    display_fold_df[column] = (
        display_fold_df[column]
        .dt.strftime(
            "%Y-%m-%d"
        )
    )


print(
    display_fold_df
    .to_string(
        index=False
    )
)
FOLD_OUTPUT_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_Backtest_Folds.csv"
)

if all_checks_pass:

    fold_df.to_csv(
        FOLD_OUTPUT_FILE,
        index=False
    )

    print(
        "\nBacktest fold definition saved:"
    )

    print(
        FOLD_OUTPUT_FILE
    )

# ============================================================
# END OF STEP 4B.2 FOLD GENERATOR
#
# NO FORECASTING MODEL HAS BEEN FIT.
# ============================================================