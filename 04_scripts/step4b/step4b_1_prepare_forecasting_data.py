import pandas as pd
from pathlib import Path


# ============================================================
# DEMANDIQ
# STEP 4B.1 — PREPARE FORECASTING INPUT
#
# Purpose:
# Convert Step 4A reconstructed demand from:
#     week × SKU × region × channel
#
# into the primary forecasting grain:
#     week × SKU × channel
#
# Forecasting target:
#     reconstructed_demand_units
#
# IMPORTANT:
# Hidden synthetic truth and generator-only fields must never
# enter the forecasting dataset.
# ============================================================


# ------------------------------------------------------------
# 1. FILE PATHS
# ------------------------------------------------------------

PROJECT_DIR = Path(r"D:\Downloads\DemandIQ")

INPUT_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4A_Demand_Reconstruction.csv"
)

OUTPUT_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4B_Forecasting_Input.csv"
)


# ------------------------------------------------------------
# 2. EXPECTED PROJECT STRUCTURE
# ------------------------------------------------------------

EXPECTED_ROWS = 2340
EXPECTED_WEEKS = 260
EXPECTED_SKUS = 3
EXPECTED_CHANNELS = 3
EXPECTED_SERIES = 9
EXPECTED_WEEKS_PER_SERIES = 260


# ------------------------------------------------------------
# 3. LOAD STEP 4A DATA
# ------------------------------------------------------------

df = pd.read_csv(INPUT_FILE)

df["week_start"] = pd.to_datetime(
    df["week_start"]
)


print("\n" + "=" * 70)
print("STEP 4A INPUT")
print("=" * 70)

print("Input file:", INPUT_FILE)
print("Shape:", df.shape)
print("Rows:", len(df))
print("Columns:", len(df.columns))


# ------------------------------------------------------------
# 4. VERIFY REQUIRED SOURCE COLUMNS EXIST
# ------------------------------------------------------------

required_source_columns = {
    "week_start",
    "sku_id",
    "channel_id",
    "reconstructed_demand_units"
}

missing_source_columns = (
    required_source_columns
    - set(df.columns)
)

source_schema_pass = (
    len(missing_source_columns) == 0
)


print("\n" + "=" * 70)
print("SOURCE COLUMN QA")
print("=" * 70)

print(
    "Required source columns:",
    "PASS" if source_schema_pass else "FAIL"
)

if not source_schema_pass:
    print(
        "Missing columns:",
        missing_source_columns
    )

    raise ValueError(
        "Required Step 4A source columns are missing."
    )


# ------------------------------------------------------------
# 5. AGGREGATE REGION → SKU × CHANNEL
# ------------------------------------------------------------

forecast_df = (
    df.groupby(
        [
            "week_start",
            "sku_id",
            "channel_id"
        ],
        as_index=False
    )
    ["reconstructed_demand_units"]
    .sum()
)


# ------------------------------------------------------------
# 6. SORT FORECASTING DATA
# ------------------------------------------------------------

forecast_df = (
    forecast_df
    .sort_values(
        [
            "sku_id",
            "channel_id",
            "week_start"
        ]
    )
    .reset_index(drop=True)
)


# ------------------------------------------------------------
# 7. BASIC STRUCTURE QA
# ------------------------------------------------------------

rows = len(forecast_df)

weeks = (
    forecast_df["week_start"]
    .nunique()
)

skus = (
    forecast_df["sku_id"]
    .nunique()
)

channels = (
    forecast_df["channel_id"]
    .nunique()
)

series_count = (
    forecast_df[
        [
            "sku_id",
            "channel_id"
        ]
    ]
    .drop_duplicates()
    .shape[0]
)


structure_pass = (
    rows == EXPECTED_ROWS
    and weeks == EXPECTED_WEEKS
    and skus == EXPECTED_SKUS
    and channels == EXPECTED_CHANNELS
    and series_count == EXPECTED_SERIES
)


print("\n" + "=" * 70)
print("FORECASTING GRAIN QA")
print("=" * 70)

print("Rows:", rows)
print("Weeks:", weeks)
print("SKUs:", skus)
print("Channels:", channels)
print("Forecast series:", series_count)

print(
    "\nStructure check:",
    "PASS" if structure_pass else "FAIL"
)


# ------------------------------------------------------------
# 8. WEEKS PER FORECAST SERIES
# ------------------------------------------------------------

weeks_per_series = (
    forecast_df
    .groupby(
        [
            "sku_id",
            "channel_id"
        ]
    )
    ["week_start"]
    .nunique()
)


weeks_per_series_pass = (
    weeks_per_series
    == EXPECTED_WEEKS_PER_SERIES
).all()


print("\n" + "=" * 70)
print("WEEKS PER SKU × CHANNEL SERIES")
print("=" * 70)

print(weeks_per_series)

print(
    "\n260 weeks per series:",
    "PASS"
    if weeks_per_series_pass
    else "FAIL"
)


# ------------------------------------------------------------
# 9. DUPLICATE FORECAST-GRAIN CHECK
# ------------------------------------------------------------

duplicate_rows = (
    forecast_df
    .duplicated(
        subset=[
            "week_start",
            "sku_id",
            "channel_id"
        ]
    )
    .sum()
)

duplicates_pass = (
    duplicate_rows == 0
)


print("\n" + "=" * 70)
print("DUPLICATE QA")
print("=" * 70)

print(
    "Duplicate forecast-grain rows:",
    duplicate_rows
)

print(
    "Duplicate check:",
    "PASS" if duplicates_pass else "FAIL"
)


# ------------------------------------------------------------
# 10. MISSING TARGET CHECK
# ------------------------------------------------------------

missing_target = (
    forecast_df[
        "reconstructed_demand_units"
    ]
    .isna()
    .sum()
)

missing_target_pass = (
    missing_target == 0
)


print("\n" + "=" * 70)
print("MISSING TARGET QA")
print("=" * 70)

print(
    "Missing reconstructed demand:",
    missing_target
)

print(
    "Missing target check:",
    "PASS"
    if missing_target_pass
    else "FAIL"
)


# ------------------------------------------------------------
# 11. NEGATIVE DEMAND CHECK
# ------------------------------------------------------------

negative_target = (
    forecast_df[
        "reconstructed_demand_units"
    ] < 0
).sum()

negative_target_pass = (
    negative_target == 0
)


print("\n" + "=" * 70)
print("NEGATIVE DEMAND QA")
print("=" * 70)

print(
    "Negative reconstructed demand rows:",
    negative_target
)

print(
    "Negative demand check:",
    "PASS"
    if negative_target_pass
    else "FAIL"
)


# ------------------------------------------------------------
# 12. ZERO DEMAND SANITY CHECK
#
# Zero demand is not automatically invalid.
# We report it so we know whether the series is intermittent.
# ------------------------------------------------------------

zero_target = (
    forecast_df[
        "reconstructed_demand_units"
    ] == 0
).sum()


print("\n" + "=" * 70)
print("ZERO DEMAND SANITY CHECK")
print("=" * 70)

print(
    "Zero-demand rows:",
    zero_target
)


# ------------------------------------------------------------
# 13. SAME CALENDAR ACROSS ALL SERIES
#
# Having 260 observations in every series does NOT guarantee
# that all series contain the exact same 260 dates.
# ------------------------------------------------------------

calendar_sets = {}

for (sku, channel), group in forecast_df.groupby(
    [
        "sku_id",
        "channel_id"
    ]
):

    calendar_sets[
        (sku, channel)
    ] = set(
        group["week_start"]
    )


reference_key = next(
    iter(calendar_sets)
)

reference_calendar = (
    calendar_sets[
        reference_key
    ]
)

same_calendar_pass = all(
    dates == reference_calendar
    for dates in calendar_sets.values()
)


print("\n" + "=" * 70)
print("SAME CALENDAR QA")
print("=" * 70)

print(
    "Reference series:",
    reference_key
)

print(
    "Identical calendar across all 9 series:",
    "PASS"
    if same_calendar_pass
    else "FAIL"
)


if not same_calendar_pass:

    for key, dates in calendar_sets.items():

        if dates != reference_calendar:

            missing_vs_reference = (
                reference_calendar
                - dates
            )

            extra_vs_reference = (
                dates
                - reference_calendar
            )

            print(
                "\nCalendar mismatch:",
                key
            )

            print(
                "Missing vs reference:",
                sorted(
                    missing_vs_reference
                )
            )

            print(
                "Extra vs reference:",
                sorted(
                    extra_vs_reference
                )
            )


# ------------------------------------------------------------
# 14. MONDAY WEEK-START CHECK
# ------------------------------------------------------------

monday_pass = (
    forecast_df[
        "week_start"
    ]
    .dt.dayofweek
    .eq(0)
    .all()
)


print("\n" + "=" * 70)
print("WEEK-START DAY QA")
print("=" * 70)

print(
    "All week_start values are Monday:",
    "PASS" if monday_pass else "FAIL"
)


# ------------------------------------------------------------
# 15. EXACT 7-DAY SPACING CHECK
# ------------------------------------------------------------

spacing_failures = []

for (sku, channel), group in forecast_df.groupby(
    [
        "sku_id",
        "channel_id"
    ]
):

    group = (
        group
        .sort_values(
            "week_start"
        )
    )

    day_differences = (
        group[
            "week_start"
        ]
        .diff()
        .dropna()
        .dt.days
    )

    invalid_spacing = (
        day_differences != 7
    )

    if invalid_spacing.any():

        spacing_failures.append(
            (
                sku,
                channel
            )
        )


spacing_pass = (
    len(
        spacing_failures
    ) == 0
)


print("\n" + "=" * 70)
print("WEEKLY SPACING QA")
print("=" * 70)

print(
    "Exact 7-day spacing across all series:",
    "PASS"
    if spacing_pass
    else "FAIL"
)

if not spacing_pass:

    print(
        "Series with spacing problems:",
        spacing_failures
    )


# ------------------------------------------------------------
# 16. MISSING-WEEK CHECK
# ------------------------------------------------------------

total_missing_weeks = 0

missing_week_detail = {}


print("\n" + "=" * 70)
print("TIME SERIES CONTINUITY QA")
print("=" * 70)


for (sku, channel), group in forecast_df.groupby(
    [
        "sku_id",
        "channel_id"
    ]
):

    group = (
        group
        .sort_values(
            "week_start"
        )
    )

    expected_dates = (
        pd.date_range(
            start=group[
                "week_start"
            ].min(),
            end=group[
                "week_start"
            ].max(),
            freq="7D"
        )
    )

    actual_dates = (
        pd.DatetimeIndex(
            group[
                "week_start"
            ]
        )
    )

    missing_dates = (
        expected_dates
        .difference(
            actual_dates
        )
    )

    missing_count = (
        len(
            missing_dates
        )
    )

    total_missing_weeks += (
        missing_count
    )

    missing_week_detail[
        (sku, channel)
    ] = missing_count

    print(
        f"{sku} | {channel} | "
        f"missing weeks: {missing_count}"
    )


continuity_pass = (
    total_missing_weeks == 0
)


print(
    "\nWeekly continuity:",
    "PASS"
    if continuity_pass
    else "FAIL"
)


# ------------------------------------------------------------
# 17. DEMAND RECONCILIATION
#
# Aggregating region must not create or destroy demand.
# ------------------------------------------------------------

source_total = (
    df[
        "reconstructed_demand_units"
    ]
    .sum()
)

forecast_total = (
    forecast_df[
        "reconstructed_demand_units"
    ]
    .sum()
)

difference = (
    forecast_total
    - source_total
)

reconciliation_pass = (
    abs(
        difference
    ) < 0.0001
)


print("\n" + "=" * 70)
print("DEMAND RECONCILIATION QA")
print("=" * 70)

print(
    "Step 4A total:",
    round(
        source_total,
        4
    )
)

print(
    "Forecasting dataset total:",
    round(
        forecast_total,
        4
    )
)

print(
    "Difference:",
    round(
        difference,
        10
    )
)

print(
    "Demand reconciliation:",
    "PASS"
    if reconciliation_pass
    else "FAIL"
)


# ------------------------------------------------------------
# 18. SERIES-LEVEL DEMAND SUMMARY
#
# Diagnostic only.
# We are NOT removing or modifying outliers here.
# ------------------------------------------------------------

series_summary = (
    forecast_df
    .groupby(
        [
            "sku_id",
            "channel_id"
        ]
    )
    ["reconstructed_demand_units"]
    .agg(
        weeks="count",
        mean="mean",
        std="std",
        minimum="min",
        maximum="max",
        total="sum"
    )
)


series_summary[
    "cv"
] = (
    series_summary[
        "std"
    ]
    / series_summary[
        "mean"
    ]
)


series_summary = (
    series_summary
    .round(2)
)


print("\n" + "=" * 70)
print("SERIES DEMAND SUMMARY")
print("=" * 70)

print(
    series_summary
)


# ------------------------------------------------------------
# 19. EXTREME-VALUE SANITY SCAN
#
# This does NOT prove whether an outlier is valid or invalid.
# It simply checks whether series minima/maxima appear repeatedly,
# which can sometimes indicate clipping/capping artifacts.
# ------------------------------------------------------------

extreme_summary_rows = []


for (sku, channel), group in forecast_df.groupby(
    [
        "sku_id",
        "channel_id"
    ]
):

    target = (
        group[
            "reconstructed_demand_units"
        ]
    )

    minimum_value = (
        target.min()
    )

    maximum_value = (
        target.max()
    )

    minimum_count = (
        target
        .eq(
            minimum_value
        )
        .sum()
    )

    maximum_count = (
        target
        .eq(
            maximum_value
        )
        .sum()
    )

    extreme_summary_rows.append(
        {
            "sku_id": sku,
            "channel_id": channel,
            "minimum": minimum_value,
            "minimum_count": minimum_count,
            "maximum": maximum_value,
            "maximum_count": maximum_count
        }
    )


extreme_summary = (
    pd.DataFrame(
        extreme_summary_rows
    )
)


print("\n" + "=" * 70)
print("EXTREME-VALUE SANITY SCAN")
print("=" * 70)

print(
    extreme_summary
    .round(2)
    .to_string(
        index=False
    )
)


# ------------------------------------------------------------
# 20. CREATE FINAL FORECASTING DATAFRAME
#
# Exact 4-column schema.
# ------------------------------------------------------------

final_forecast_df = (
    forecast_df[
        [
            "week_start",
            "sku_id",
            "channel_id",
            "reconstructed_demand_units"
        ]
    ]
    .copy()
)


# ------------------------------------------------------------
# 21. EXACT OUTPUT SCHEMA CHECK
#
# This is stronger than only checking forbidden columns.
# Nothing except the approved 4 columns may enter Step 4B.
# ------------------------------------------------------------

EXPECTED_OUTPUT_COLUMNS = [
    "week_start",
    "sku_id",
    "channel_id",
    "reconstructed_demand_units"
]


schema_pass = (
    list(
        final_forecast_df.columns
    )
    == EXPECTED_OUTPUT_COLUMNS
)


print("\n" + "=" * 70)
print("FINAL OUTPUT SCHEMA QA")
print("=" * 70)

print(
    "Actual columns:",
    final_forecast_df.columns.tolist()
)

print(
    "Exact 4-column schema:",
    "PASS"
    if schema_pass
    else "FAIL"
)


# ------------------------------------------------------------
# 22. HARD LEAKAGE GUARD
# ------------------------------------------------------------

FORBIDDEN_EXACT_COLUMNS = {
    "true_demand_units",
    "lost_demand_units",
    "recon_naive_units",
    "recon_seasonal_units",
    "recon_regression_units",
    "weather_effect_pct",
    "weather_factor",
    "positive_spike_factor",
    "negative_shock_factor",
    "noise_factor"
}


forbidden_hits = (
    FORBIDDEN_EXACT_COLUMNS
    .intersection(
        final_forecast_df.columns
    )
)


audit_hidden_hits = [
    column
    for column
    in final_forecast_df.columns
    if column.startswith(
        "audit_hidden_"
    )
]


leakage_pass = (
    len(
        forbidden_hits
    ) == 0
    and
    len(
        audit_hidden_hits
    ) == 0
)


print("\n" + "=" * 70)
print("LEAKAGE GUARD QA")
print("=" * 70)

print(
    "Forbidden exact-column hits:",
    sorted(
        forbidden_hits
    )
)

print(
    "audit_hidden_* hits:",
    audit_hidden_hits
)

print(
    "Leakage guard:",
    "PASS"
    if leakage_pass
    else "FAIL"
)


# ------------------------------------------------------------
# 23. FINAL 4B.1 QA STATUS
# ------------------------------------------------------------

all_checks_pass = all(
    [
        source_schema_pass,
        structure_pass,
        weeks_per_series_pass,
        duplicates_pass,
        missing_target_pass,
        negative_target_pass,
        same_calendar_pass,
        monday_pass,
        spacing_pass,
        continuity_pass,
        reconciliation_pass,
        schema_pass,
        leakage_pass
    ]
)


print("\n" + "=" * 70)
print("FINAL STEP 4B.1 QA")
print("=" * 70)


qa_results = {
    "Required source columns": source_schema_pass,
    "Expected forecasting structure": structure_pass,
    "260 weeks per series": weeks_per_series_pass,
    "Duplicate forecast grain": duplicates_pass,
    "Missing target": missing_target_pass,
    "Negative demand": negative_target_pass,
    "Same calendar across series": same_calendar_pass,
    "Monday week_start": monday_pass,
    "Exact 7-day spacing": spacing_pass,
    "Missing-week continuity": continuity_pass,
    "Demand reconciliation": reconciliation_pass,
    "Exact output schema": schema_pass,
    "Leakage guard": leakage_pass
}


for check_name, status in qa_results.items():

    print(
        f"{check_name}:",
        "PASS" if status else "FAIL"
    )


print("\n" + "-" * 70)

if all_checks_pass:

    print(
        "OVERALL STATUS: PASS — "
        "Step 4B forecasting input is structurally ready."
    )

else:

    print(
        "OVERALL STATUS: FAIL — "
        "Do not continue to forecasting."
    )

print("-" * 70)


# ------------------------------------------------------------
# 24. SAVE OFFICIAL STEP 4B FORECASTING INPUT
#
# File is written ONLY when every critical QA check passes.
# ------------------------------------------------------------

if all_checks_pass:

    final_forecast_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        "\nForecasting input saved successfully:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nFinal output shape:",
        final_forecast_df.shape
    )

    print(
        "Final output columns:",
        final_forecast_df.columns.tolist()
    )

else:

    print(
        "\nForecasting input NOT saved "
        "because one or more QA checks failed."
    )


# ============================================================
# END OF STEP 4B.1
# ============================================================