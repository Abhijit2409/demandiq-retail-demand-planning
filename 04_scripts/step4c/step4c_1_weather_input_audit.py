import pandas as pd
from pathlib import Path


# ============================================================
# DEMANDIQ
# STEP 4C.1 — WEATHER INPUT AUDIT & GOVERNANCE
#
# Purpose:
# Validate weather and reconstructed-demand inputs before
# constructing any weather adjustment or scenario framework.
#
# This step DOES NOT:
#   - fit a weather model
#   - adjust forecasts
#   - generate future weather
#   - create weather-adjusted demand
#
# It checks:
#   1. File availability
#   2. Date parsing
#   3. Monday weekly calendar
#   4. Date/calendar reconciliation
#   5. Regional coverage
#   6. Grain uniqueness
#   7. Leakage-sensitive columns
#   8. Whether Step 4C.1 is ready to freeze
# ============================================================


# ------------------------------------------------------------
# 1. PROJECT ROOT
# ------------------------------------------------------------

PROJECT_DIR = Path(r"D:\Downloads\DemandIQ")


# ------------------------------------------------------------
# 2. INPUT PATHS
#
# These are the actual locations currently in your project.
# ------------------------------------------------------------

WEATHER_FILE = (
    PROJECT_DIR
    / "02_data"
    / "weather"
    / "data"
    / "weather_features_weekly.csv"
)


DEMAND_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4A_Demand_Reconstruction.csv"
)


# ------------------------------------------------------------
# 3. EXPECTED GOVERNED STRUCTURE
# ------------------------------------------------------------

EXPECTED_WEEKS = 260

EXPECTED_REGIONS = 9

EXPECTED_SKUS = 3

EXPECTED_CHANNELS = 3


EXPECTED_WEATHER_ROWS = (
    EXPECTED_WEEKS
    * EXPECTED_REGIONS
)


EXPECTED_DEMAND_ROWS = (
    EXPECTED_WEEKS
    * EXPECTED_REGIONS
    * EXPECTED_SKUS
    * EXPECTED_CHANNELS
)


EXPECTED_REGION_SET = {
    "CA_ON",
    "CA_PNW",
    "CA_PRAIRIE",
    "CA_QC",
    "US_MIDWEST",
    "US_MTN",
    "US_NE",
    "US_PNW",
    "US_WEST"
}


# ============================================================
# 4. FILE PATH QA
# ============================================================

print("\n" + "=" * 94)
print("STEP 4C.1 — WEATHER INPUT AUDIT & GOVERNANCE")
print("=" * 94)


source_files = {
    "Weekly weather features": WEATHER_FILE,
    "Demand reconstruction": DEMAND_FILE
}


all_files_found = True


for name, path in source_files.items():

    exists = path.exists()

    print(
        f"{name}:",
        "FOUND" if exists else "MISSING"
    )

    print(
        " ",
        path
    )

    if not exists:
        all_files_found = False


if not all_files_found:

    raise FileNotFoundError(
        "\nOne or more Step 4C source files are missing."
    )


# ============================================================
# 5. LOAD FILES
# ============================================================

weather_df = pd.read_csv(
    WEATHER_FILE
)


demand_df = pd.read_csv(
    DEMAND_FILE
)


print("\n" + "=" * 94)
print("FILE SHAPES")
print("=" * 94)


print(
    "Weather shape:",
    weather_df.shape
)


print(
    "Expected weather rows:",
    EXPECTED_WEATHER_ROWS
)


print(
    "Demand shape:",
    demand_df.shape
)


print(
    "Expected demand rows:",
    EXPECTED_DEMAND_ROWS
)


# ============================================================
# 6. ROBUST WEEK-START PARSER
#
# Why this exists:
#
# Weather and demand files may use different text formats:
#
#   DD-MM-YYYY
#   MM-DD-YYYY
#   YYYY-MM-DD
#
# Since DemandIQ uses weekly Monday dates, we can use the
# Monday-calendar rule to resolve ambiguous DD/MM ordering.
# ============================================================

def parse_week_start(
    series,
    file_name
):

    raw = (
        series
        .astype(str)
        .str.strip()
    )


    candidate_formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m-%d-%Y"
    ]


    candidate_results = []


    for date_format in candidate_formats:

        parsed = pd.to_datetime(
            raw,
            format=date_format,
            errors="coerce"
        )


        parse_success_rate = (
            parsed.notna().mean()
        )


        if parsed.notna().sum() > 0:

            monday_rate = (
                parsed
                .dropna()
                .dt.dayofweek
                .eq(0)
                .mean()
            )

        else:

            monday_rate = 0.0


        unique_dates = (
            parsed
            .dropna()
            .nunique()
        )


        candidate_results.append(
            {
                "format": date_format,
                "parsed": parsed,
                "parse_success_rate":
                    parse_success_rate,
                "monday_rate":
                    monday_rate,
                "unique_dates":
                    unique_dates
            }
        )


    # --------------------------------------------------------
    # Select format:
    #
    # Priority:
    # 1. highest parse success
    # 2. highest Monday consistency
    # 3. closest to expected 260 unique weeks
    # --------------------------------------------------------

    candidate_results = sorted(

        candidate_results,

        key=lambda x: (
            x["parse_success_rate"],
            x["monday_rate"],
            -abs(
                x["unique_dates"]
                - EXPECTED_WEEKS
            )
        ),

        reverse=True

    )


    best = candidate_results[0]


    print("\n" + "-" * 94)

    print(
        f"{file_name} DATE FORMAT DETECTION"
    )

    print("-" * 94)


    for result in candidate_results:

        print(
            f"Format {result['format']} | "
            f"Parse success="
            f"{result['parse_success_rate']:.2%} | "
            f"Monday rate="
            f"{result['monday_rate']:.2%} | "
            f"Unique dates="
            f"{result['unique_dates']}"
        )


    print(
        f"\nSelected {file_name} format:",
        best["format"]
    )


    # --------------------------------------------------------
    # Hard validation
    # --------------------------------------------------------

    if best[
        "parse_success_rate"
    ] < 1.0:

        raise ValueError(
            f"{file_name}: selected date format does not "
            f"parse 100% of rows."
        )


    if best[
        "monday_rate"
    ] < 1.0:

        raise ValueError(
            f"{file_name}: selected date format does not "
            f"produce an all-Monday weekly calendar."
        )


    return (
        best["parsed"],
        best["format"]
    )


# ============================================================
# 7. PARSE WEATHER + DEMAND DATES
# ============================================================

weather_df[
    "week_start"
], weather_date_format = parse_week_start(

    weather_df[
        "week_start"
    ],

    "WEATHER"

)


demand_df[
    "week_start"
], demand_date_format = parse_week_start(

    demand_df[
        "week_start"
    ],

    "DEMAND"

)


# ============================================================
# 8. DATE COVERAGE
# ============================================================

print("\n" + "=" * 94)
print("WEATHER DATE COVERAGE")
print("=" * 94)


print(
    "Detected date format:",
    weather_date_format
)


print(
    "Min date:",
    weather_df[
        "week_start"
    ].min()
)


print(
    "Max date:",
    weather_df[
        "week_start"
    ].max()
)


print(
    "Unique weeks:",
    weather_df[
        "week_start"
    ].nunique()
)


weather_monday_pass = (

    weather_df[
        "week_start"
    ]

    .dt.dayofweek

    .eq(0)

    .all()

)


print(
    "All week_start values are Monday:",
    "PASS"
    if weather_monday_pass
    else "FAIL"
)


print("\n" + "=" * 94)
print("DEMAND DATE COVERAGE")
print("=" * 94)


print(
    "Detected date format:",
    demand_date_format
)


print(
    "Min date:",
    demand_df[
        "week_start"
    ].min()
)


print(
    "Max date:",
    demand_df[
        "week_start"
    ].max()
)


print(
    "Unique weeks:",
    demand_df[
        "week_start"
    ].nunique()
)


demand_monday_pass = (

    demand_df[
        "week_start"
    ]

    .dt.dayofweek

    .eq(0)

    .all()

)


print(
    "All week_start values are Monday:",
    "PASS"
    if demand_monday_pass
    else "FAIL"
)


# ============================================================
# 9. WEEK COUNT QA
# ============================================================

weather_week_count = (
    weather_df[
        "week_start"
    ]
    .nunique()
)


demand_week_count = (
    demand_df[
        "week_start"
    ]
    .nunique()
)


weather_week_count_pass = (
    weather_week_count
    == EXPECTED_WEEKS
)


demand_week_count_pass = (
    demand_week_count
    == EXPECTED_WEEKS
)


print("\n" + "=" * 94)
print("WEEK COUNT QA")
print("=" * 94)


print(
    "Weather unique weeks:",
    weather_week_count,
    "|",
    "PASS"
    if weather_week_count_pass
    else "FAIL"
)


print(
    "Demand unique weeks:",
    demand_week_count,
    "|",
    "PASS"
    if demand_week_count_pass
    else "FAIL"
)


# ============================================================
# 10. CALENDAR RECONCILIATION
#
# The weather and demand files should represent the exact
# same 260 weekly Mondays.
# ============================================================

weather_calendar = set(

    weather_df[
        "week_start"
    ]
    .drop_duplicates()

)


demand_calendar = set(

    demand_df[
        "week_start"
    ]
    .drop_duplicates()

)


weeks_missing_from_weather = sorted(

    demand_calendar
    - weather_calendar

)


weeks_missing_from_demand = sorted(

    weather_calendar
    - demand_calendar

)


calendar_match_pass = (

    weather_calendar
    == demand_calendar

)


print("\n" + "=" * 94)
print("CALENDAR RECONCILIATION")
print("=" * 94)


print(
    "Demand weeks missing from weather:",
    len(
        weeks_missing_from_weather
    )
)


if weeks_missing_from_weather:

    print(
        "First few:",
        weeks_missing_from_weather[:10]
    )


print(
    "Weather weeks missing from demand:",
    len(
        weeks_missing_from_demand
    )
)


if weeks_missing_from_demand:

    print(
        "First few:",
        weeks_missing_from_demand[:10]
    )


print(
    "Weather and demand use identical weekly calendar:",
    "PASS"
    if calendar_match_pass
    else "FAIL"
)


# ============================================================
# 11. REGION AUDIT
# ============================================================

weather_regions = sorted(

    weather_df[
        "region_id"
    ]

    .dropna()

    .astype(str)

    .unique()

)


demand_regions = sorted(

    demand_df[
        "region_id"
    ]

    .dropna()

    .astype(str)

    .unique()

)


print("\n" + "=" * 94)
print("REGION AUDIT")
print("=" * 94)


print(
    "Weather region count:",
    len(
        weather_regions
    )
)


print(
    "Weather regions:"
)


for region in weather_regions:

    print(
        " -",
        region
    )


print(
    "\nDemand region count:",
    len(
        demand_regions
    )
)


print(
    "Demand regions:"
)


for region in demand_regions:

    print(
        " -",
        region
    )


# ============================================================
# 12. REGION RECONCILIATION
# ============================================================

weather_region_set = set(
    weather_regions
)


demand_region_set = set(
    demand_regions
)


missing_from_weather = sorted(

    demand_region_set
    - weather_region_set

)


extra_in_weather = sorted(

    weather_region_set
    - demand_region_set

)


weather_expected_regions_missing = sorted(

    EXPECTED_REGION_SET
    - weather_region_set

)


demand_expected_regions_missing = sorted(

    EXPECTED_REGION_SET
    - demand_region_set

)


region_match_pass = (

    weather_region_set
    == demand_region_set
    == EXPECTED_REGION_SET

)


print("\n" + "=" * 94)
print("REGION RECONCILIATION")
print("=" * 94)


print(
    "Demand regions missing from weather:",
    missing_from_weather
)


print(
    "Extra regions in weather:",
    extra_in_weather
)


print(
    "Expected regions missing from weather:",
    weather_expected_regions_missing
)


print(
    "Expected regions missing from demand:",
    demand_expected_regions_missing
)


print(
    "Exact governed 9-region coverage:",
    "PASS"
    if region_match_pass
    else "FAIL"
)


# ============================================================
# 13. WEATHER ROW COUNT QA
# ============================================================

weather_row_count_pass = (

    len(
        weather_df
    )

    ==

    EXPECTED_WEATHER_ROWS

)


demand_row_count_pass = (

    len(
        demand_df
    )

    ==

    EXPECTED_DEMAND_ROWS

)


print("\n" + "=" * 94)
print("ROW COUNT QA")
print("=" * 94)


print(
    "Weather rows:",
    len(
        weather_df
    ),
    "| Expected:",
    EXPECTED_WEATHER_ROWS,
    "|",
    "PASS"
    if weather_row_count_pass
    else "FAIL"
)


print(
    "Demand rows:",
    len(
        demand_df
    ),
    "| Expected:",
    EXPECTED_DEMAND_ROWS,
    "|",
    "PASS"
    if demand_row_count_pass
    else "FAIL"
)


# ============================================================
# 14. LEAKAGE / HIDDEN FIELD AUDIT
#
# Presence in an audit/source file is not itself a failure.
# These fields simply must NOT enter Step 4C model inputs.
# ============================================================

FORBIDDEN_PATTERNS = [

    "true_demand",
    "lost_demand",
    "weather_effect",
    "weather_factor",
    "audit_hidden",
    "positive_spike",
    "negative_shock",
    "noise_factor"

]


def find_forbidden_columns(
    dataframe
):

    matches = []


    for column in dataframe.columns:

        lower_column = (
            column.lower()
        )


        for pattern in FORBIDDEN_PATTERNS:

            if pattern in lower_column:

                matches.append(
                    column
                )

                break


    return sorted(
        set(matches)
    )


weather_forbidden = (
    find_forbidden_columns(
        weather_df
    )
)


demand_forbidden = (
    find_forbidden_columns(
        demand_df
    )
)


print("\n" + "=" * 94)
print("LEAKAGE / HIDDEN FIELD AUDIT")
print("=" * 94)


print(
    "Forbidden-style columns present in WEATHER file:"
)


if weather_forbidden:

    for column in weather_forbidden:

        print(
            " -",
            column
        )

else:

    print(
        " None"
    )


print(
    "\nForbidden-style columns present in DEMAND file:"
)


if demand_forbidden:

    for column in demand_forbidden:

        print(
            " -",
            column
        )

else:

    print(
        " None"
    )


weather_leakage_pass = (
    len(
        weather_forbidden
    )
    == 0
)


print(
    "\nWeather feature file leakage-sensitive field check:",
    "PASS"
    if weather_leakage_pass
    else "FAIL"
)


print(
    "\nNOTE:"
)

print(
    "true_demand_units and lost_demand_units may remain in "
    "the Step 4A audit dataset, but they are prohibited from "
    "Step 4C analytical inputs."
)


# ============================================================
# 15. WEATHER SAMPLE
# ============================================================

print("\n" + "=" * 94)
print("WEATHER SAMPLE — FIRST 5 ROWS")
print("=" * 94)


weather_sample_columns = [

    column

    for column in [

        "week_start",
        "region_id",
        "proxy_city",
        "avg_temp_c",
        "rain_mm",
        "snow_cm",
        "max_wind_kmh",
        "cold_days_lt5c",
        "wet_cold_days",
        "temp_anomaly_c",
        "rain_anomaly_mm",
        "snow_anomaly_cm",
        "weather_reference_available"

    ]

    if column in weather_df.columns

]


print(

    weather_df[
        weather_sample_columns
    ]

    .head()

    .to_string(
        index=False
    )

)


# ============================================================
# 16. DEMAND SAMPLE
# ============================================================

print("\n" + "=" * 94)
print("DEMAND SAMPLE — FIRST 5 ROWS")
print("=" * 94)


demand_sample_columns = [

    column

    for column in [

        "week_start",
        "sku_id",
        "region_id",
        "channel_id",
        "reconstructed_demand_units"

    ]

    if column in demand_df.columns

]


print(

    demand_df[
        demand_sample_columns
    ]

    .head()

    .to_string(
        index=False
    )

)


# ============================================================
# 17. WEATHER GRAIN QA
#
# Expected grain:
# Region × Week
# ============================================================

weather_duplicates = (

    weather_df

    .duplicated(

        subset=[
            "week_start",
            "region_id"
        ]

    )

    .sum()

)


weather_grain_pass = (
    weather_duplicates == 0
)


print("\n" + "=" * 94)
print("WEATHER GRAIN QA")
print("=" * 94)


print(
    "Duplicate Region × Week rows:",
    weather_duplicates
)


print(
    "Region × Week grain unique:",
    "PASS"
    if weather_grain_pass
    else "FAIL"
)


weather_weeks_per_region = (

    weather_df

    .groupby(
        "region_id"
    )

    [
        "week_start"
    ]

    .nunique()

    .sort_index()

)


print(
    "\nUnique weather weeks per region:"
)


print(
    weather_weeks_per_region
    .to_string()
)


weather_complete_each_region_pass = (

    len(
        weather_weeks_per_region
    )
    == EXPECTED_REGIONS

    and

    weather_weeks_per_region
    .eq(
        EXPECTED_WEEKS
    )
    .all()

)


print(
    "\nEvery governed region has exactly 260 weeks:",
    "PASS"
    if weather_complete_each_region_pass
    else "FAIL"
)


# ============================================================
# 18. DEMAND GRAIN QA
#
# Expected detailed grain:
# Week × SKU × Region × Channel
# ============================================================

demand_duplicates = (

    demand_df

    .duplicated(

        subset=[
            "week_start",
            "sku_id",
            "region_id",
            "channel_id"
        ]

    )

    .sum()

)


demand_grain_pass = (
    demand_duplicates == 0
)


print("\n" + "=" * 94)
print("DEMAND GRAIN QA")
print("=" * 94)


print(
    "Duplicate Week × SKU × Region × Channel rows:",
    demand_duplicates
)


print(
    "Detailed demand grain unique:",
    "PASS"
    if demand_grain_pass
    else "FAIL"
)


# ============================================================
# 19. DEMAND DIMENSION QA
# ============================================================

sku_count = (
    demand_df[
        "sku_id"
    ]
    .nunique()
)


channel_count = (
    demand_df[
        "channel_id"
    ]
    .nunique()
)


region_count = (
    demand_df[
        "region_id"
    ]
    .nunique()
)


sku_count_pass = (
    sku_count == EXPECTED_SKUS
)


channel_count_pass = (
    channel_count == EXPECTED_CHANNELS
)


demand_region_count_pass = (
    region_count == EXPECTED_REGIONS
)


print("\n" + "=" * 94)
print("DEMAND DIMENSION QA")
print("=" * 94)


print(
    "SKUs:",
    sku_count,
    "|",
    "PASS"
    if sku_count_pass
    else "FAIL"
)


print(
    "Channels:",
    channel_count,
    "|",
    "PASS"
    if channel_count_pass
    else "FAIL"
)


print(
    "Regions:",
    region_count,
    "|",
    "PASS"
    if demand_region_count_pass
    else "FAIL"
)


# ============================================================
# 20. FINAL STEP 4C.1 READINESS QA
# ============================================================

qa_checks = {

    "Weather file found":
        WEATHER_FILE.exists(),

    "Demand file found":
        DEMAND_FILE.exists(),

    "Weather has 260 unique weeks":
        weather_week_count_pass,

    "Demand has 260 unique weeks":
        demand_week_count_pass,

    "Weather dates are Mondays":
        weather_monday_pass,

    "Demand dates are Mondays":
        demand_monday_pass,

    "Weather and demand calendars match exactly":
        calendar_match_pass,

    "Exact 9-region coverage":
        region_match_pass,

    "Weather row count = 2,340":
        weather_row_count_pass,

    "Demand row count = 21,060":
        demand_row_count_pass,

    "Weather Region × Week grain unique":
        weather_grain_pass,

    "Each weather region has 260 weeks":
        weather_complete_each_region_pass,

    "Demand detailed grain unique":
        demand_grain_pass,

    "Demand contains 3 SKUs":
        sku_count_pass,

    "Demand contains 3 channels":
        channel_count_pass,

    "Demand contains 9 regions":
        demand_region_count_pass,

    "Weather feature file contains no hidden leakage fields":
        weather_leakage_pass

}


overall_ready = all(
    qa_checks.values()
)


print("\n" + "=" * 94)
print("FINAL STEP 4C.1 READINESS QA")
print("=" * 94)


for check_name, passed in qa_checks.items():

    print(
        f"{check_name}:",
        "PASS"
        if passed
        else "FAIL"
    )


print("\n" + "-" * 94)


if overall_ready:

    print(
        "OVERALL STATUS: PASS — "
        "Step 4C.1 weather inputs are ready to freeze."
    )

    print(
        "Next step: Step 4C.2 — Regional Weather Signal "
        "and Scenario Construction."
    )

else:

    print(
        "OVERALL STATUS: NOT READY — "
        "Do not build Step 4C.2 yet."
    )


    if not region_match_pass:

        print(
            "\nBLOCKER:"
        )

        print(
            "Weather regional coverage is incomplete."
        )

        print(
            "Regions missing from weather:",
            missing_from_weather
        )


    if not calendar_match_pass:

        print(
            "\nBLOCKER:"
        )

        print(
            "Weather and demand calendars do not match."
        )


    if not weather_row_count_pass:

        print(
            "\nBLOCKER:"
        )

        print(
            f"Weather has {len(weather_df):,} rows, "
            f"but {EXPECTED_WEATHER_ROWS:,} are required "
            f"for 9 regions × 260 weeks."
        )


print("-" * 94)


# ============================================================
# END STEP 4C.1
#
# No CSV is intentionally generated by this audit.
# ============================================================