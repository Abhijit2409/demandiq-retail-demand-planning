import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# DEMANDIQ — STEP 2B
# WEATHER FEATURE ENGINEERING
#
# Purpose:
# Convert raw weekly regional weather into the governed
# Region × Week feature table used by DemandIQ.
#
# Governed modelling calendar:
#     2021-07-05 through 2026-06-22
#
# Expected final structure:
#     260 weeks × 9 regions = 2,340 rows
#
# IMPORTANT:
# Weather features are PUBLIC/DERIVED.
# Synthetic threshold rules are explicitly labelled.
# ============================================================


# ------------------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------------------

PROJECT_DIR = Path(r"D:\Downloads\DemandIQ")

WEATHER_ROOT = (
    PROJECT_DIR
    / "02_data"
    / "weather"
)

DATA_FOLDER = (
    WEATHER_ROOT
    / "data"
)

INPUT_FILE = (
    DATA_FOLDER
    / "weather_weekly.csv"
)

OUTPUT_FOLDER = DATA_FOLDER

OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

CSV_OUTPUT = (
    OUTPUT_FOLDER
    / "weather_features_weekly.csv"
)

EXCEL_OUTPUT = (
    OUTPUT_FOLDER
    / "weather_features_weekly.xlsx"
)


# ------------------------------------------------------------
# 2. GOVERNED STRUCTURE
# ------------------------------------------------------------

EXPECTED_REGIONS = 9
EXPECTED_WEEKS = 260
EXPECTED_FINAL_ROWS = 2340

GOVERNED_START = pd.Timestamp("2021-07-05")
GOVERNED_END = pd.Timestamp("2026-06-22")

EXPECTED_REGION_SET = {
    "CA_PNW",
    "CA_PRAIRIE",
    "CA_ON",
    "CA_QC",
    "US_PNW",
    "US_NE",
    "US_MIDWEST",
    "US_MTN",
    "US_WEST"
}


# ============================================================
# 3. INPUT FILE QA
# ============================================================

print("\n" + "=" * 88)
print("DEMANDIQ STEP 2B — WEATHER FEATURE ENGINEERING")
print("=" * 88)

print(
    "Input file:",
    INPUT_FILE
)

if not INPUT_FILE.exists():

    raise FileNotFoundError(
        f"\nWeather weekly input was not found:\n"
        f"{INPUT_FILE}"
    )

print(
    "Input file status: FOUND"
)


# ============================================================
# 4. LOAD DATA
# ============================================================

df = pd.read_csv(
    INPUT_FILE
)


required_input_columns = {
    "week_start",
    "region_id",
    "proxy_city",
    "avg_temp_c",
    "min_temp_c",
    "max_temp_c",
    "rain_mm",
    "rain_days",
    "snow_cm",
    "snow_days",
    "precipitation_mm",
    "precipitation_hours",
    "max_wind_kmh",
    "max_gust_kmh",
    "high_wind_days",
    "cold_days_lt5c",
    "wet_cold_days",
    "days_in_week",
    "source",
    "model"
}


missing_input_columns = (
    required_input_columns
    - set(df.columns)
)


if missing_input_columns:

    raise ValueError(
        "Missing required weather columns: "
        f"{sorted(missing_input_columns)}"
    )


print("\nRaw weekly dataset")
print("-" * 88)

print(
    "Rows:",
    len(df)
)

print(
    "Regions:",
    df["region_id"].nunique()
)


# ============================================================
# 5. ROBUST DATE PARSING
#
# Supports:
#     YYYY-MM-DD
#     DD-MM-YYYY
#
# The rebuilt historical weather pull writes ISO dates,
# but this also remains backward compatible with your
# earlier DD-MM-YYYY file.
# ============================================================

def parse_weather_week_start(series):

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

    candidates = []


    for date_format in candidate_formats:

        parsed = pd.to_datetime(
            raw,
            format=date_format,
            errors="coerce"
        )

        success_rate = (
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


        candidates.append(
            {
                "format":
                    date_format,

                "parsed":
                    parsed,

                "success_rate":
                    success_rate,

                "monday_rate":
                    monday_rate
            }
        )


    candidates = sorted(
        candidates,
        key=lambda x: (
            x["success_rate"],
            x["monday_rate"]
        ),
        reverse=True
    )


    best = candidates[0]


    print("\nDate format detection")
    print("-" * 88)


    for candidate in candidates:

        print(
            f"{candidate['format']} | "
            f"Parse success="
            f"{candidate['success_rate']:.2%} | "
            f"Monday rate="
            f"{candidate['monday_rate']:.2%}"
        )


    print(
        "\nSelected format:",
        best["format"]
    )


    if best["success_rate"] != 1.0:

        raise ValueError(
            "Unable to parse 100% of weather week_start "
            "values."
        )


    return best["parsed"]


df["week_start"] = (
    parse_weather_week_start(
        df["week_start"]
    )
)


print(
    "\nRaw minimum week:",
    df["week_start"].min()
)

print(
    "Raw maximum week:",
    df["week_start"].max()
)


# ============================================================
# 6. RAW REGION QA
# ============================================================

raw_regions = set(
    df["region_id"]
    .dropna()
    .astype(str)
    .unique()
)


print("\n" + "=" * 88)
print("RAW REGION QA")
print("=" * 88)


print(
    "Raw region count:",
    len(raw_regions)
)


print(
    "Regions:"
)

for region in sorted(raw_regions):

    print(
        " -",
        region
    )


missing_regions = sorted(
    EXPECTED_REGION_SET
    - raw_regions
)


extra_regions = sorted(
    raw_regions
    - EXPECTED_REGION_SET
)


raw_region_pass = (
    raw_regions
    == EXPECTED_REGION_SET
)


print(
    "\nMissing governed regions:",
    missing_regions
)

print(
    "Unexpected regions:",
    extra_regions
)

print(
    "Exact governed 9-region set:",
    "PASS"
    if raw_region_pass
    else "FAIL"
)


if not raw_region_pass:

    raise ValueError(
        "Raw weekly weather does not contain the "
        "complete governed 9-region set."
    )


# ============================================================
# 7. REMOVE PARTIAL BOUNDARY WEEKS
#
# Historical pull includes partial weeks:
#
#   2021-06-28
#   2026-06-29
#
# Only full 7-day weeks are eligible.
# ============================================================

partial_week_count = (
    df[
        "days_in_week"
    ]
    .ne(7)
    .sum()
)


print("\n" + "=" * 88)
print("PARTIAL-WEEK FILTER")
print("=" * 88)


print(
    "Partial Region × Week rows before filter:",
    partial_week_count
)


df = (
    df[
        df["days_in_week"] == 7
    ]
    .copy()
)


# ------------------------------------------------------------
# Also enforce the exact governed forecast-history window.
# ------------------------------------------------------------

df = (
    df[
        df["week_start"].between(
            GOVERNED_START,
            GOVERNED_END
        )
    ]
    .copy()
)


print(
    "Rows after complete-week + governed-date filter:",
    len(df)
)

print(
    "Expected final rows:",
    EXPECTED_FINAL_ROWS
)


# ============================================================
# 8. SORT DATA
# ============================================================

df = (
    df
    .sort_values(
        [
            "region_id",
            "week_start"
        ]
    )
    .reset_index(
        drop=True
    )
)


# ============================================================
# 9. BASE CALENDAR QA
# ============================================================

week_count = (
    df["week_start"].nunique()
)

region_count = (
    df["region_id"].nunique()
)


all_mondays_pass = (
    df["week_start"]
    .dt.dayofweek
    .eq(0)
    .all()
)


row_count_pass = (
    len(df)
    == EXPECTED_FINAL_ROWS
)


week_count_pass = (
    week_count
    == EXPECTED_WEEKS
)


region_count_pass = (
    region_count
    == EXPECTED_REGIONS
)


print("\n" + "=" * 88)
print("GOVERNED CALENDAR QA")
print("=" * 88)


print(
    "Rows:",
    len(df),
    "| Expected:",
    EXPECTED_FINAL_ROWS,
    "|",
    "PASS" if row_count_pass else "FAIL"
)


print(
    "Unique weeks:",
    week_count,
    "| Expected:",
    EXPECTED_WEEKS,
    "|",
    "PASS" if week_count_pass else "FAIL"
)


print(
    "Regions:",
    region_count,
    "| Expected:",
    EXPECTED_REGIONS,
    "|",
    "PASS" if region_count_pass else "FAIL"
)


print(
    "Minimum date:",
    df["week_start"].min()
)


print(
    "Maximum date:",
    df["week_start"].max()
)


print(
    "All week_start values Monday:",
    "PASS"
    if all_mondays_pass
    else "FAIL"
)


if not all(
    [
        row_count_pass,
        week_count_pass,
        region_count_pass,
        all_mondays_pass
    ]
):

    raise ValueError(
        "Governed weather calendar QA failed."
    )


# ============================================================
# 10. CALENDAR FEATURES
# ============================================================

iso_calendar = (
    df["week_start"]
    .dt
    .isocalendar()
)


df["year"] = (
    df["week_start"]
    .dt
    .year
)


df["month"] = (
    df["week_start"]
    .dt
    .month
)


df["quarter"] = (
    df["week_start"]
    .dt
    .quarter
)


df["week_of_year"] = (
    iso_calendar[
        "week"
    ]
    .astype(int)
)


def assign_season(month):

    if month in [
        12,
        1,
        2
    ]:

        return "WINTER"

    elif month in [
        3,
        4,
        5
    ]:

        return "SPRING"

    elif month in [
        6,
        7,
        8
    ]:

        return "SUMMER"

    else:

        return "FALL"


df["season"] = (
    df["month"]
    .apply(
        assign_season
    )
)


# ============================================================
# 11. PRIOR-YEAR WEATHER REFERENCES
#
# IMPORTANT:
# Current-year values are not used in their own reference.
#
# Example:
#
# 2022 reference → 2021
# 2023 reference → mean(2021, 2022)
# 2024 reference → mean(2021, 2022, 2023)
#
# This preserves the original methodology from your file.
# ============================================================

def prior_year_reference(series):

    return (
        series
        .shift(1)
        .expanding(
            min_periods=1
        )
        .mean()
    )


df["temp_reference_c"] = (

    df.groupby(
        [
            "region_id",
            "week_of_year"
        ]
    )[
        "avg_temp_c"
    ]

    .transform(
        prior_year_reference
    )

)


df["rain_reference_mm"] = (

    df.groupby(
        [
            "region_id",
            "week_of_year"
        ]
    )[
        "rain_mm"
    ]

    .transform(
        prior_year_reference
    )

)


df["snow_reference_cm"] = (

    df.groupby(
        [
            "region_id",
            "week_of_year"
        ]
    )[
        "snow_cm"
    ]

    .transform(
        prior_year_reference
    )

)


# ============================================================
# 12. WEATHER ANOMALIES
# ============================================================

df["temp_anomaly_c"] = (
    df["avg_temp_c"]
    -
    df["temp_reference_c"]
)


df["rain_anomaly_mm"] = (
    df["rain_mm"]
    -
    df["rain_reference_mm"]
)


df["snow_anomaly_cm"] = (
    df["snow_cm"]
    -
    df["snow_reference_cm"]
)


# ------------------------------------------------------------
# Rain percentage anomaly
#
# Minimum historical denominator = 1 mm to prevent
# unstable percentage values near zero.
# ------------------------------------------------------------

rain_denominator = (
    df["rain_reference_mm"]
    .clip(
        lower=1
    )
)


df["rain_anomaly_pct"] = (
    df["rain_anomaly_mm"]
    /
    rain_denominator
)


# ============================================================
# 13. WEATHER INTERACTION FEATURES
# ============================================================

# ------------------------------------------------------------
# Wet + Cold Index
# ------------------------------------------------------------

cold_anomaly_strength = np.maximum(
    0,
    -df["temp_anomaly_c"]
)


df["wet_cold_index"] = (
    df["rain_mm"]
    *
    cold_anomaly_strength
)


# ------------------------------------------------------------
# Snow + Cold Index
# ------------------------------------------------------------

df["snow_cold_index"] = (
    df["snow_cm"]
    *
    cold_anomaly_strength
)


# ------------------------------------------------------------
# Rain + Wind Index
# ------------------------------------------------------------

df["rain_wind_index"] = (
    df["rain_mm"]
    *
    df["max_wind_kmh"]
)


# ============================================================
# 14. WEATHER INTENSITY FLAGS
#
# These thresholds remain explicit PROJECT ASSUMPTIONS.
# ============================================================

df["heavy_rain_week_flag"] = (
    df["rain_mm"]
    >= 50
).astype(int)


df["heavy_snow_week_flag"] = (
    df["snow_cm"]
    >= 15
).astype(int)


df["cold_week_flag"] = (
    df["avg_temp_c"]
    <= 0
).astype(int)


df["very_cold_week_flag"] = (
    df["avg_temp_c"]
    <= -10
).astype(int)


df["wet_cold_week_flag"] = (
    df["wet_cold_days"]
    >= 2
).astype(int)


df["high_wind_week_flag"] = (
    df["high_wind_days"]
    >= 2
).astype(int)


# ============================================================
# 15. LAG FEATURES
# ============================================================

LAG_COLUMNS = [

    "avg_temp_c",

    "temp_anomaly_c",

    "rain_mm",

    "rain_anomaly_mm",

    "snow_cm",

    "max_wind_kmh",

    "wet_cold_days",

    "wet_cold_index"

]


for column in LAG_COLUMNS:

    df[
        f"{column}_lag1"
    ] = (

        df.groupby(
            "region_id"
        )[
            column
        ]

        .shift(1)

    )


    df[
        f"{column}_lag2"
    ] = (

        df.groupby(
            "region_id"
        )[
            column
        ]

        .shift(2)

    )


# ============================================================
# 16. ROLLING WEATHER FEATURES
# ============================================================

df["rain_mm_4wk"] = (

    df.groupby(
        "region_id"
    )[
        "rain_mm"
    ]

    .transform(

        lambda x:

        x.rolling(
            4,
            min_periods=1
        )
        .sum()

    )

)


df["snow_cm_4wk"] = (

    df.groupby(
        "region_id"
    )[
        "snow_cm"
    ]

    .transform(

        lambda x:

        x.rolling(
            4,
            min_periods=1
        )
        .sum()

    )

)


df["avg_temp_4wk"] = (

    df.groupby(
        "region_id"
    )[
        "avg_temp_c"
    ]

    .transform(

        lambda x:

        x.rolling(
            4,
            min_periods=1
        )
        .mean()

    )

)


df["wet_cold_days_4wk"] = (

    df.groupby(
        "region_id"
    )[
        "wet_cold_days"
    ]

    .transform(

        lambda x:

        x.rolling(
            4,
            min_periods=1
        )
        .sum()

    )

)


# ============================================================
# 17. WEATHER REFERENCE AVAILABILITY
#
# First available seasonal cycle has no prior-year
# historical reference and intentionally remains NaN.
# ============================================================

df["weather_reference_available"] = (

    df[
        "temp_reference_c"
    ]

    .notna()

    .astype(int)

)


# ============================================================
# 18. ROUND NUMERIC FEATURES
# ============================================================

numeric_columns = (

    df.select_dtypes(

        include=[
            "float64",
            "float32"
        ]

    )

    .columns

)


df[
    numeric_columns
] = (

    df[
        numeric_columns
    ]

    .round(3)

)


# ============================================================
# 19. FINAL STRUCTURAL QA
# ============================================================

duplicate_count = (

    df

    .duplicated(

        subset=[
            "week_start",
            "region_id"
        ]

    )

    .sum()

)


weeks_per_region = (

    df.groupby(
        "region_id"
    )[
        "week_start"
    ]

    .nunique()

    .sort_index()

)


each_region_260_pass = (

    len(
        weeks_per_region
    )
    == EXPECTED_REGIONS

    and

    weeks_per_region
    .eq(
        EXPECTED_WEEKS
    )
    .all()

)


duplicate_pass = (
    duplicate_count == 0
)


final_region_set = set(

    df[
        "region_id"
    ]

    .unique()

)


final_region_set_pass = (
    final_region_set
    == EXPECTED_REGION_SET
)


# ------------------------------------------------------------
# Missing core weather checks
# ------------------------------------------------------------

CORE_WEATHER_COLUMNS = [

    "avg_temp_c",
    "rain_mm",
    "snow_cm",
    "max_wind_kmh",
    "wet_cold_days"

]


core_weather_null_count = (

    df[
        CORE_WEATHER_COLUMNS
    ]

    .isna()

    .sum()

    .sum()

)


core_weather_complete_pass = (
    core_weather_null_count == 0
)


# ------------------------------------------------------------
# Expected first-cycle reference absence
# ------------------------------------------------------------

reference_available_count = int(

    df[
        "weather_reference_available"
    ]
    .sum()

)


reference_unavailable_count = int(

    (
        df[
            "weather_reference_available"
        ]
        == 0
    )
    .sum()

)


# ============================================================
# 20. QA SUMMARY TABLE
# ============================================================

qa_summary = pd.DataFrame(

    {

        "metric": [

            "Total modelling rows",

            "Number of regions",

            "Unique weeks",

            "Minimum weeks per region",

            "Maximum weeks per region",

            "Minimum date",

            "Maximum date",

            "Duplicate region-week records",

            "Rows with 7 complete days",

            "Core weather null values",

            "Rows with weather reference",

            "Rows without weather reference"

        ],


        "value": [

            len(df),

            df[
                "region_id"
            ].nunique(),

            df[
                "week_start"
            ].nunique(),

            int(
                weeks_per_region.min()
            ),

            int(
                weeks_per_region.max()
            ),

            str(
                df[
                    "week_start"
                ]
                .min()
                .date()
            ),

            str(
                df[
                    "week_start"
                ]
                .max()
                .date()
            ),

            duplicate_count,

            int(
                (
                    df[
                        "days_in_week"
                    ]
                    == 7
                )
                .sum()
            ),

            int(
                core_weather_null_count
            ),

            reference_available_count,

            reference_unavailable_count

        ]

    }

)


# ============================================================
# 21. FEATURE DICTIONARY
#
# Original feature definitions are preserved.
# ============================================================

feature_dictionary = pd.DataFrame(

    [

        [
            "year",
            "Calendar year",
            "DERIVED"
        ],

        [
            "month",
            "Calendar month",
            "DERIVED"
        ],

        [
            "quarter",
            "Calendar quarter",
            "DERIVED"
        ],

        [
            "week_of_year",
            "ISO week number",
            "DERIVED"
        ],

        [
            "season",
            "WINTER / SPRING / SUMMER / FALL",
            "DERIVED"
        ],

        [
            "temp_reference_c",
            (
                "Mean temperature for the same "
                "region/week using prior years only"
            ),
            "DERIVED"
        ],

        [
            "temp_anomaly_c",
            (
                "Actual temperature minus "
                "prior-year seasonal reference"
            ),
            "DERIVED"
        ],

        [
            "rain_reference_mm",
            (
                "Historical rainfall reference "
                "using prior years only"
            ),
            "DERIVED"
        ],

        [
            "rain_anomaly_mm",
            (
                "Actual rainfall minus "
                "historical reference"
            ),
            "DERIVED"
        ],

        [
            "rain_anomaly_pct",
            (
                "Rainfall anomaly divided by "
                "historical reference"
            ),
            "DERIVED"
        ],

        [
            "snow_reference_cm",
            (
                "Historical snowfall reference "
                "using prior years only"
            ),
            "DERIVED"
        ],

        [
            "snow_anomaly_cm",
            (
                "Actual snowfall minus "
                "historical reference"
            ),
            "DERIVED"
        ],

        [
            "wet_cold_index",
            (
                "Rainfall multiplied by "
                "unusual-cold intensity"
            ),
            "DERIVED"
        ],

        [
            "snow_cold_index",
            (
                "Snowfall multiplied by "
                "unusual-cold intensity"
            ),
            "DERIVED"
        ],

        [
            "rain_wind_index",
            (
                "Rainfall multiplied by "
                "maximum wind speed"
            ),
            "DERIVED"
        ],

        [
            "heavy_rain_week_flag",
            "1 when weekly rainfall >= 50 mm",
            "SYNTHETIC RULE"
        ],

        [
            "heavy_snow_week_flag",
            "1 when weekly snowfall >= 15 cm",
            "SYNTHETIC RULE"
        ],

        [
            "cold_week_flag",
            (
                "1 when average weekly "
                "temperature <= 0C"
            ),
            "SYNTHETIC RULE"
        ],

        [
            "very_cold_week_flag",
            (
                "1 when average weekly "
                "temperature <= -10C"
            ),
            "SYNTHETIC RULE"
        ],

        [
            "wet_cold_week_flag",
            (
                "1 when >=2 days during week "
                "are both wet and cold"
            ),
            "SYNTHETIC RULE"
        ],

        [
            "high_wind_week_flag",
            (
                "1 when >=2 high-wind days "
                "occur during the week"
            ),
            "SYNTHETIC RULE"
        ],

        [
            "*_lag1",
            (
                "Previous week's value "
                "for the same region"
            ),
            "DERIVED"
        ],

        [
            "*_lag2",
            (
                "Value two weeks earlier "
                "for the same region"
            ),
            "DERIVED"
        ],

        [
            "rain_mm_4wk",
            "Rolling four-week rainfall total",
            "DERIVED"
        ],

        [
            "snow_cm_4wk",
            "Rolling four-week snowfall total",
            "DERIVED"
        ],

        [
            "avg_temp_4wk",
            (
                "Rolling four-week "
                "average temperature"
            ),
            "DERIVED"
        ],

        [
            "wet_cold_days_4wk",
            (
                "Rolling four-week number "
                "of wet+cold days"
            ),
            "DERIVED"
        ],

        [
            "weather_reference_available",
            (
                "1 if prior-year weather "
                "reference exists"
            ),
            "DERIVED"
        ]

    ],

    columns=[
        "feature",
        "description",
        "provenance"
    ]

)


# ============================================================
# 22. FINAL QA
# ============================================================

qa_checks = {

    "Final rows = 2,340":
        len(df)
        == EXPECTED_FINAL_ROWS,

    "Regions = 9":
        df["region_id"].nunique()
        == EXPECTED_REGIONS,

    "Exact governed region set":
        final_region_set_pass,

    "Unique weeks = 260":
        df["week_start"].nunique()
        == EXPECTED_WEEKS,

    "Every region has exactly 260 weeks":
        each_region_260_pass,

    "Region × Week grain unique":
        duplicate_pass,

    "All rows are complete 7-day weeks":
        (
            df["days_in_week"]
            == 7
        ).all(),

    "Minimum date is governed start":
        (
            df["week_start"].min()
            == GOVERNED_START
        ),

    "Maximum date is governed end":
        (
            df["week_start"].max()
            == GOVERNED_END
        ),

    "All week_start values are Monday":
        (
            df["week_start"]
            .dt.dayofweek
            .eq(0)
            .all()
        ),

    "Core weather fields have no nulls":
        core_weather_complete_pass

}


overall_pass = all(
    qa_checks.values()
)


print("\n" + "=" * 88)
print("FINAL WEATHER FEATURE QA")
print("=" * 88)


for name, passed in qa_checks.items():

    print(
        f"{name}:",
        "PASS"
        if passed
        else "FAIL"
    )


print(
    "\nWeeks per region:"
)

print(
    weeks_per_region
    .to_string()
)


print(
    "\nRows with prior-year weather reference:",
    reference_available_count
)


print(
    "Rows without prior-year weather reference:",
    reference_unavailable_count
)


# ============================================================
# 23. SAVE ONLY IF QA PASSES
# ============================================================

if overall_pass:

    # --------------------------------------------------------
    # CSV
    #
    # Save ISO dates so all downstream scripts use one
    # unambiguous standard.
    # --------------------------------------------------------

    output_df = df.copy()

    output_df[
        "week_start"
    ] = (

        output_df[
            "week_start"
        ]

        .dt.strftime(
            "%Y-%m-%d"
        )

    )


    output_df.to_csv(
        CSV_OUTPUT,
        index=False
    )


    # --------------------------------------------------------
    # Excel
    # --------------------------------------------------------

    with pd.ExcelWriter(
        EXCEL_OUTPUT,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            sheet_name="weather_features",
            index=False
        )

        feature_dictionary.to_excel(
            writer,
            sheet_name="feature_dictionary",
            index=False
        )

        qa_summary.to_excel(
            writer,
            sheet_name="qa_summary",
            index=False
        )


    print("\n" + "=" * 88)
    print("DEMANDIQ STEP 2B COMPLETE")
    print("=" * 88)


    print(
        "OVERALL STATUS: PASS"
    )


    print(
        "\nFinal rows:",
        len(df)
    )


    print(
        "Regions:",
        df["region_id"].nunique()
    )


    print(
        "Unique weeks:",
        df["week_start"].nunique()
    )


    print(
        "\nCreated:"
    )


    print(
        CSV_OUTPUT
    )


    print(
        EXCEL_OUTPUT
    )


else:

    print("\n" + "=" * 88)
    print("DEMANDIQ STEP 2B FAILED QA")
    print("=" * 88)


    print(
        "OVERALL STATUS: FAIL"
    )


    print(
        "\nOutputs were NOT overwritten."
    )


    raise RuntimeError(
        "Weather feature engineering QA failed."
    )


# ============================================================
# END
# ============================================================