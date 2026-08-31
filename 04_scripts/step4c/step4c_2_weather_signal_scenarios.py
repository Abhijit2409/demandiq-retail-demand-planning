import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# DEMANDIQ
# STEP 4C.2 — REGIONAL WEATHER SIGNAL & SCENARIO CONSTRUCTION
#
# Purpose:
# Convert governed historical Region × Week weather features
# into a transparent regional weather scenario classification.
#
# Scenario classes:
#
#   MILD
#   NORMAL
#   SEVERE
#   REFERENCE_UNAVAILABLE
#
# IMPORTANT:
#   - No demand data is used here.
#   - No true_demand / lost_demand fields are used.
#   - No hidden synthetic weather-effect fields are used.
#   - No arbitrary weighted weather score is created.
#
# Instead, weather severity is based on transparent
# weather dimensions and explicit project thresholds.
#
# Final grain:
#   Week × Region
#
# Expected rows:
#   260 weeks × 9 regions = 2,340
# ============================================================


# ------------------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------------------

PROJECT_DIR = Path(
    r"D:\Downloads\DemandIQ"
)


WEATHER_FILE = (
    PROJECT_DIR
    / "02_data"
    / "weather"
    / "data"
    / "weather_features_weekly.csv"
)


OUTPUT_DIR = (
    PROJECT_DIR
    / "05_outputs"
    / "weather_scenarios"
)


OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


OUTPUT_FILE = (
    OUTPUT_DIR
    / "DemandIQ_Step4C_Regional_Weather_Scenarios.csv"
)


# ------------------------------------------------------------
# 2. GOVERNED STRUCTURE
# ------------------------------------------------------------

EXPECTED_WEEKS = 260

EXPECTED_REGIONS = 9

EXPECTED_ROWS = (
    EXPECTED_WEEKS
    * EXPECTED_REGIONS
)


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


GOVERNED_START = pd.Timestamp(
    "2021-07-05"
)

GOVERNED_END = pd.Timestamp(
    "2026-06-22"
)


# ============================================================
# 3. WEATHER SCENARIO GOVERNANCE THRESHOLDS
#
# These are PROJECT ASSUMPTIONS.
#
# They are NOT statistically estimated demand elasticities
# and are NOT claims about Arc'teryx internal planning rules.
#
# They define weather scenario severity only.
# ============================================================


# ------------------------------------------------------------
# Temperature anomaly:
#
# <= -2C versus seasonal reference = meaningfully colder
# >= +2C versus seasonal reference = meaningfully milder
# ------------------------------------------------------------

COLD_TEMP_ANOMALY_C = -2.0

MILD_TEMP_ANOMALY_C = 2.0


# ------------------------------------------------------------
# Rain anomaly:
#
# +20 mm above prior seasonal reference contributes one
# adverse weather dimension.
# ------------------------------------------------------------

RAIN_ANOMALY_SEVERE_MM = 20.0


# ------------------------------------------------------------
# Snow anomaly:
#
# +5 cm above prior seasonal reference contributes one
# adverse weather dimension.
# ------------------------------------------------------------

SNOW_ANOMALY_SEVERE_CM = 5.0


# ------------------------------------------------------------
# Number of distinct adverse weather dimensions required
# to classify the week as SEVERE.
#
# This is an unweighted rule count, NOT a score.
# ------------------------------------------------------------

SEVERE_DIMENSION_THRESHOLD = 2


# ============================================================
# 4. FILE QA
# ============================================================

print(
    "\n"
    + "=" * 96
)

print(
    "STEP 4C.2 — REGIONAL WEATHER SIGNAL & SCENARIO CONSTRUCTION"
)

print(
    "=" * 96
)


print(
    "Weather input:",
    WEATHER_FILE
)


if not WEATHER_FILE.exists():

    raise FileNotFoundError(

        "\nWeather feature file not found:\n"
        f"{WEATHER_FILE}"

    )


print(
    "Input file status: FOUND"
)


# ============================================================
# 5. LOAD WEATHER DATA
# ============================================================

df = pd.read_csv(
    WEATHER_FILE
)


print(
    "\nInput shape:",
    df.shape
)


# ============================================================
# 6. REQUIRED COLUMN QA
# ============================================================

REQUIRED_COLUMNS = {

    "week_start",
    "region_id",
    "proxy_city",

    "avg_temp_c",
    "rain_mm",
    "snow_cm",
    "max_wind_kmh",
    "wet_cold_days",

    "temp_anomaly_c",
    "rain_anomaly_mm",
    "snow_anomaly_cm",

    "heavy_rain_week_flag",
    "heavy_snow_week_flag",
    "cold_week_flag",
    "very_cold_week_flag",
    "wet_cold_week_flag",
    "high_wind_week_flag",

    "weather_reference_available"

}


missing_columns = (

    REQUIRED_COLUMNS
    - set(
        df.columns
    )

)


schema_pass = (
    len(
        missing_columns
    )
    == 0
)


print(
    "\nRequired weather schema:",
    "PASS"
    if schema_pass
    else "FAIL"
)


if not schema_pass:

    print(
        "Missing columns:",
        sorted(
            missing_columns
        )
    )

    raise ValueError(
        "Required Step 4C.2 weather columns are missing."
    )


# ============================================================
# 7. DATE PARSING
# ============================================================

df[
    "week_start"
] = pd.to_datetime(

    df[
        "week_start"
    ],

    format="%Y-%m-%d",

    errors="raise"

)


# ============================================================
# 8. STRUCTURAL INPUT QA
# ============================================================

row_count_pass = (
    len(df)
    == EXPECTED_ROWS
)


week_count_pass = (
    df[
        "week_start"
    ]
    .nunique()
    == EXPECTED_WEEKS
)


region_count_pass = (
    df[
        "region_id"
    ]
    .nunique()
    == EXPECTED_REGIONS
)


region_set = set(

    df[
        "region_id"
    ]
    .unique()

)


region_set_pass = (
    region_set
    == EXPECTED_REGION_SET
)


date_start_pass = (
    df[
        "week_start"
    ]
    .min()
    == GOVERNED_START
)


date_end_pass = (
    df[
        "week_start"
    ]
    .max()
    == GOVERNED_END
)


monday_pass = (

    df[
        "week_start"
    ]
    .dt.dayofweek
    .eq(0)
    .all()

)


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


grain_pass = (
    duplicate_count == 0
)


weeks_per_region = (

    df
    .groupby(
        "region_id"
    )[
        "week_start"
    ]
    .nunique()

)


region_week_coverage_pass = (

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


print(
    "\n"
    + "=" * 96
)

print(
    "INPUT STRUCTURAL QA"
)

print(
    "=" * 96
)


input_checks = {

    "Rows = 2,340":
        row_count_pass,

    "Unique weeks = 260":
        week_count_pass,

    "Regions = 9":
        region_count_pass,

    "Exact governed region set":
        region_set_pass,

    "Start date correct":
        date_start_pass,

    "End date correct":
        date_end_pass,

    "All weeks Monday":
        monday_pass,

    "Region × Week grain unique":
        grain_pass,

    "Every region has 260 weeks":
        region_week_coverage_pass

}


for name, passed in input_checks.items():

    print(
        f"{name}:",
        "PASS"
        if passed
        else "FAIL"
    )


if not all(
    input_checks.values()
):

    raise ValueError(
        "Step 4C.2 structural input QA failed."
    )


# ============================================================
# 9. LEAKAGE / GOVERNANCE AUDIT
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


forbidden_columns = []


for column in df.columns:

    lower_column = (
        column.lower()
    )

    for pattern in FORBIDDEN_PATTERNS:

        if pattern in lower_column:

            forbidden_columns.append(
                column
            )

            break


forbidden_columns = sorted(
    set(
        forbidden_columns
    )
)


leakage_pass = (
    len(
        forbidden_columns
    )
    == 0
)


print(
    "\n"
    + "=" * 96
)

print(
    "LEAKAGE / GOVERNANCE QA"
)

print(
    "=" * 96
)


print(
    "Forbidden fields detected:",
    forbidden_columns
)


print(
    "Weather input leakage check:",
    "PASS"
    if leakage_pass
    else "FAIL"
)


if not leakage_pass:

    raise ValueError(
        "Forbidden leakage fields detected."
    )


# ============================================================
# 10. REFERENCE AVAILABILITY QA
# ============================================================

reference_available = (

    df[
        "weather_reference_available"
    ]
    .eq(1)

)


reference_unavailable = (
    ~reference_available
)


# ------------------------------------------------------------
# When reference_available == 1,
# anomaly fields must be present.
# ------------------------------------------------------------

ANOMALY_COLUMNS = [

    "temp_anomaly_c",
    "rain_anomaly_mm",
    "snow_anomaly_cm"

]


eligible_anomaly_nulls = (

    df
    .loc[
        reference_available,
        ANOMALY_COLUMNS
    ]
    .isna()
    .sum()
    .sum()

)


anomaly_complete_pass = (
    eligible_anomaly_nulls == 0
)


print(
    "\n"
    + "=" * 96
)

print(
    "WEATHER REFERENCE QA"
)

print(
    "=" * 96
)


print(
    "Rows with seasonal reference:",
    int(
        reference_available.sum()
    )
)


print(
    "Rows without seasonal reference:",
    int(
        reference_unavailable.sum()
    )
)


print(
    "Missing anomaly values where reference exists:",
    int(
        eligible_anomaly_nulls
    )
)


print(
    "Eligible anomaly completeness:",
    "PASS"
    if anomaly_complete_pass
    else "FAIL"
)


if not anomaly_complete_pass:

    raise ValueError(
        "Weather anomaly fields are incomplete."
    )


# ============================================================
# 11. CONSTRUCT DISTINCT WEATHER DIMENSIONS
#
# IMPORTANT:
#
# We do NOT add raw weather variables together.
#
# Instead, each distinct weather dimension becomes a simple
# binary indicator.
#
# This reduces double-counting and makes the classification
# explainable.
# ============================================================


# ------------------------------------------------------------
# A. Temperature severity dimension
#
# Trigger:
#   colder than seasonal reference by >= 2C
#   OR very-cold absolute week
# ------------------------------------------------------------

df[
    "cold_severity_dimension"
] = (

    (
        df[
            "temp_anomaly_c"
        ]
        <= COLD_TEMP_ANOMALY_C
    )

    |

    (
        df[
            "very_cold_week_flag"
        ]
        == 1
    )

).astype(int)


# ------------------------------------------------------------
# B. Rain severity dimension
#
# Trigger:
#   rain >= 20 mm above seasonal reference
#   OR existing heavy-rain project flag
# ------------------------------------------------------------

df[
    "rain_severity_dimension"
] = (

    (
        df[
            "rain_anomaly_mm"
        ]
        >= RAIN_ANOMALY_SEVERE_MM
    )

    |

    (
        df[
            "heavy_rain_week_flag"
        ]
        == 1
    )

).astype(int)


# ------------------------------------------------------------
# C. Snow severity dimension
# ------------------------------------------------------------

df[
    "snow_severity_dimension"
] = (

    (
        df[
            "snow_anomaly_cm"
        ]
        >= SNOW_ANOMALY_SEVERE_CM
    )

    |

    (
        df[
            "heavy_snow_week_flag"
        ]
        == 1
    )

).astype(int)


# ------------------------------------------------------------
# D. Wet + cold compound dimension
# ------------------------------------------------------------

df[
    "wet_cold_severity_dimension"
] = (

    df[
        "wet_cold_week_flag"
    ]
    .eq(1)

    .astype(int)

)


# ------------------------------------------------------------
# E. Wind severity dimension
# ------------------------------------------------------------

df[
    "wind_severity_dimension"
] = (

    df[
        "high_wind_week_flag"
    ]
    .eq(1)

    .astype(int)

)


# ============================================================
# 12. ADVERSE DIMENSION COUNT
#
# This is NOT a weighted severity score.
#
# It simply counts the number of distinct weather dimensions
# showing unusual adverse conditions.
# ============================================================

SEVERITY_DIMENSION_COLUMNS = [

    "cold_severity_dimension",
    "rain_severity_dimension",
    "snow_severity_dimension",
    "wet_cold_severity_dimension",
    "wind_severity_dimension"

]


df[
    "adverse_dimension_count"
] = (

    df[
        SEVERITY_DIMENSION_COLUMNS
    ]
    .sum(
        axis=1
    )

)


# ============================================================
# 13. EXTREME EVENT FLAG
#
# A single genuinely extreme event may classify a week as
# SEVERE even without two separate dimensions.
#
# We use:
#
#   very cold week
#   heavy snow week
#   compound heavy rain + high wind
#
# Again, this is transparent rule logic rather than weights.
# ============================================================

df[
    "extreme_weather_event_flag"
] = (

    (
        df[
            "very_cold_week_flag"
        ]
        == 1
    )

    |

    (
        df[
            "heavy_snow_week_flag"
        ]
        == 1
    )

    |

    (
        (
            df[
                "heavy_rain_week_flag"
            ]
            == 1
        )

        &

        (
            df[
                "high_wind_week_flag"
            ]
            == 1
        )
    )

).astype(int)


# ============================================================
# 14. MILD-WEATHER CONDITION
#
# Conservative definition:
#
#   meaningfully warmer than seasonal normal
#   AND
#   zero adverse dimensions
#
# We deliberately do not label every non-severe week MILD.
# Most weeks should remain NORMAL.
# ============================================================

df[
    "mild_weather_candidate_flag"
] = (

    (
        df[
            "temp_anomaly_c"
        ]
        >= MILD_TEMP_ANOMALY_C
    )

    &

    (
        df[
            "adverse_dimension_count"
        ]
        == 0
    )

).astype(int)


# ============================================================
# 15. SCENARIO CLASSIFICATION
# ============================================================

def classify_weather_scenario(row):

    # --------------------------------------------------------
    # No prior seasonal reference available.
    # --------------------------------------------------------

    if (
        row[
            "weather_reference_available"
        ]
        != 1
    ):

        return "REFERENCE_UNAVAILABLE"


    # --------------------------------------------------------
    # Severe:
    #
    # two or more adverse dimensions
    # OR one explicit extreme event.
    # --------------------------------------------------------

    if (

        row[
            "adverse_dimension_count"
        ]
        >= SEVERE_DIMENSION_THRESHOLD

        or

        row[
            "extreme_weather_event_flag"
        ]
        == 1

    ):

        return "SEVERE"


    # --------------------------------------------------------
    # Mild:
    #
    # materially warmer than seasonal reference
    # with no adverse dimensions.
    # --------------------------------------------------------

    if (
        row[
            "mild_weather_candidate_flag"
        ]
        == 1
    ):

        return "MILD"


    # --------------------------------------------------------
    # Everything else stays NORMAL.
    # --------------------------------------------------------

    return "NORMAL"


df[
    "weather_scenario"
] = (

    df.apply(
        classify_weather_scenario,
        axis=1
    )

)


# ============================================================
# 16. HUMAN-READABLE SCENARIO REASON
# ============================================================

def build_scenario_reason(row):

    scenario = (
        row[
            "weather_scenario"
        ]
    )


    if scenario == "REFERENCE_UNAVAILABLE":

        return (
            "No prior-year seasonal weather reference available"
        )


    triggered_dimensions = []


    if (
        row[
            "cold_severity_dimension"
        ]
        == 1
    ):

        triggered_dimensions.append(
            "colder_than_normal"
        )


    if (
        row[
            "rain_severity_dimension"
        ]
        == 1
    ):

        triggered_dimensions.append(
            "wetter_than_normal"
        )


    if (
        row[
            "snow_severity_dimension"
        ]
        == 1
    ):

        triggered_dimensions.append(
            "snowier_than_normal"
        )


    if (
        row[
            "wet_cold_severity_dimension"
        ]
        == 1
    ):

        triggered_dimensions.append(
            "wet_cold_compound"
        )


    if (
        row[
            "wind_severity_dimension"
        ]
        == 1
    ):

        triggered_dimensions.append(
            "high_wind"
        )


    if scenario == "SEVERE":

        reason = (
            "SEVERE: "
            + ", ".join(
                triggered_dimensions
            )
        )


        if (
            row[
                "extreme_weather_event_flag"
            ]
            == 1
        ):

            reason += (
                " | extreme_event_trigger"
            )


        return reason


    if scenario == "MILD":

        return (
            "MILD: warmer_than_seasonal_reference "
            "with no adverse weather dimensions"
        )


    if triggered_dimensions:

        return (
            "NORMAL: isolated adverse dimension "
            "without severe compound conditions | "
            + ", ".join(
                triggered_dimensions
            )
        )


    return (
        "NORMAL: no material adverse or mild scenario trigger"
    )


df[
    "scenario_reason"
] = (

    df.apply(
        build_scenario_reason,
        axis=1
    )

)


# ============================================================
# 17. SCENARIO ELIGIBILITY
# ============================================================

df[
    "scenario_eligible_flag"
] = (

    df[
        "weather_reference_available"
    ]
    .eq(1)

    .astype(int)

)


# ============================================================
# 18. PROVENANCE / GOVERNANCE FIELDS
# ============================================================

df[
    "scenario_method"
] = (
    "RULE_BASED_UNWEIGHTED_WEATHER_DIMENSIONS"
)


df[
    "scenario_provenance"
] = (
    "DERIVED_FROM_PUBLIC_WEATHER"
)


df[
    "scenario_threshold_provenance"
] = (
    "PROJECT_ASSUMPTION"
)


# ============================================================
# 19. SCENARIO QA
# ============================================================

VALID_SCENARIOS = {

    "MILD",
    "NORMAL",
    "SEVERE",
    "REFERENCE_UNAVAILABLE"

}


scenario_values = set(

    df[
        "weather_scenario"
    ]
    .unique()

)


scenario_value_pass = (
    scenario_values
    .issubset(
        VALID_SCENARIOS
    )
)


# ------------------------------------------------------------
# Every no-reference row must be REFERENCE_UNAVAILABLE.
# ------------------------------------------------------------

reference_logic_pass = (

    df
    .loc[
        df[
            "weather_reference_available"
        ]
        == 0,
        "weather_scenario"
    ]
    .eq(
        "REFERENCE_UNAVAILABLE"
    )
    .all()

)


# ------------------------------------------------------------
# Every MILD/NORMAL/SEVERE row must have reference available.
# ------------------------------------------------------------

eligible_logic_pass = (

    df
    .loc[
        df[
            "weather_scenario"
        ]
        != "REFERENCE_UNAVAILABLE",
        "weather_reference_available"
    ]
    .eq(1)
    .all()

)


# ------------------------------------------------------------
# Severe rule reconciliation.
# ------------------------------------------------------------

expected_severe = (

    (
        df[
            "weather_reference_available"
        ]
        == 1
    )

    &

    (
        (
            df[
                "adverse_dimension_count"
            ]
            >= SEVERE_DIMENSION_THRESHOLD
        )

        |

        (
            df[
                "extreme_weather_event_flag"
            ]
            == 1
        )
    )

)


actual_severe = (

    df[
        "weather_scenario"
    ]
    .eq(
        "SEVERE"
    )

)


severe_rule_pass = (
    expected_severe
    .eq(
        actual_severe
    )
    .all()
)


# ------------------------------------------------------------
# Mild reconciliation.
# ------------------------------------------------------------

expected_mild = (

    (
        df[
            "weather_reference_available"
        ]
        == 1
    )

    &

    (
        ~expected_severe
    )

    &

    (
        df[
            "mild_weather_candidate_flag"
        ]
        == 1
    )

)


actual_mild = (

    df[
        "weather_scenario"
    ]
    .eq(
        "MILD"
    )

)


mild_rule_pass = (
    expected_mild
    .eq(
        actual_mild
    )
    .all()
)


scenario_reason_pass = (

    df[
        "scenario_reason"
    ]
    .notna()
    .all()

    and

    df[
        "scenario_reason"
    ]
    .astype(str)
    .str.len()
    .gt(0)
    .all()

)


# ============================================================
# 20. OUTPUT TABLE
#
# Keep the components that explain the decision.
#
# We do NOT need all 62 weather-feature columns in this
# business-facing scenario table.
# ============================================================

OUTPUT_COLUMNS = [

    "week_start",
    "region_id",
    "proxy_city",

    "avg_temp_c",
    "rain_mm",
    "snow_cm",
    "max_wind_kmh",
    "wet_cold_days",

    "temp_reference_c",
    "rain_reference_mm",
    "snow_reference_cm",

    "temp_anomaly_c",
    "rain_anomaly_mm",
    "snow_anomaly_cm",

    "heavy_rain_week_flag",
    "heavy_snow_week_flag",
    "cold_week_flag",
    "very_cold_week_flag",
    "wet_cold_week_flag",
    "high_wind_week_flag",

    "cold_severity_dimension",
    "rain_severity_dimension",
    "snow_severity_dimension",
    "wet_cold_severity_dimension",
    "wind_severity_dimension",

    "adverse_dimension_count",
    "extreme_weather_event_flag",
    "mild_weather_candidate_flag",

    "weather_reference_available",
    "scenario_eligible_flag",

    "weather_scenario",
    "scenario_reason",

    "scenario_method",
    "scenario_provenance",
    "scenario_threshold_provenance"

]


output_df = (

    df[
        OUTPUT_COLUMNS
    ]
    .copy()

)


# ============================================================
# 21. FINAL OUTPUT STRUCTURAL QA
# ============================================================

output_row_pass = (
    len(
        output_df
    )
    == EXPECTED_ROWS
)


output_duplicate_count = (

    output_df
    .duplicated(

        subset=[
            "week_start",
            "region_id"
        ]

    )
    .sum()

)


output_grain_pass = (
    output_duplicate_count == 0
)


output_region_pass = (

    set(
        output_df[
            "region_id"
        ]
        .unique()
    )

    == EXPECTED_REGION_SET

)


output_week_pass = (
    output_df[
        "week_start"
    ]
    .nunique()
    == EXPECTED_WEEKS
)


# ============================================================
# 22. FINAL QA
# ============================================================

qa_checks = {

    "Input structural QA":
        all(
            input_checks.values()
        ),

    "Weather input leakage check":
        leakage_pass,

    "Anomalies complete where reference exists":
        anomaly_complete_pass,

    "Scenario values valid":
        scenario_value_pass,

    "Reference-unavailable logic valid":
        reference_logic_pass,

    "Scenario eligibility logic valid":
        eligible_logic_pass,

    "SEVERE classification rule reconciles":
        severe_rule_pass,

    "MILD classification rule reconciles":
        mild_rule_pass,

    "Scenario reasons populated":
        scenario_reason_pass,

    "Output rows = 2,340":
        output_row_pass,

    "Output Region × Week grain unique":
        output_grain_pass,

    "Output exact 9-region set":
        output_region_pass,

    "Output unique weeks = 260":
        output_week_pass

}


overall_pass = all(
    qa_checks.values()
)


print(
    "\n"
    + "=" * 96
)

print(
    "FINAL STEP 4C.2 QA"
)

print(
    "=" * 96
)


for name, passed in qa_checks.items():

    print(
        f"{name}:",
        "PASS"
        if passed
        else "FAIL"
    )


# ============================================================
# 23. SCENARIO DISTRIBUTION
# ============================================================

print(
    "\n"
    + "=" * 96
)

print(
    "OVERALL SCENARIO DISTRIBUTION"
)

print(
    "=" * 96
)


scenario_distribution = (

    output_df[
        "weather_scenario"
    ]
    .value_counts()
    .rename_axis(
        "weather_scenario"
    )
    .reset_index(
        name="weeks"
    )

)


scenario_distribution[
    "pct"
] = (

    scenario_distribution[
        "weeks"
    ]

    / len(
        output_df
    )

    * 100

)


scenario_distribution[
    "pct"
] = (

    scenario_distribution[
        "pct"
    ]
    .round(2)

)


print(
    scenario_distribution
    .to_string(
        index=False
    )
)


# ============================================================
# 24. SCENARIO DISTRIBUTION BY REGION
# ============================================================

print(
    "\n"
    + "=" * 96
)

print(
    "SCENARIO DISTRIBUTION BY REGION"
)

print(
    "=" * 96
)


region_scenario_distribution = (

    output_df

    .groupby(
        [
            "region_id",
            "weather_scenario"
        ]
    )

    .size()

    .unstack(
        fill_value=0
    )

)


print(
    region_scenario_distribution
    .to_string()
)


# ============================================================
# 25. ADVERSE DIMENSION DISTRIBUTION
# ============================================================

print(
    "\n"
    + "=" * 96
)

print(
    "ADVERSE WEATHER DIMENSION COUNT"
)

print(
    "=" * 96
)


print(

    output_df[
        "adverse_dimension_count"
    ]

    .value_counts()

    .sort_index()

    .to_string()

)


# ============================================================
# 26. EXAMPLE SEVERE WEEKS
# ============================================================

print(
    "\n"
    + "=" * 96
)

print(
    "EXAMPLE SEVERE WEEKS"
)

print(
    "=" * 96
)


severe_examples = (

    output_df[
        output_df[
            "weather_scenario"
        ]
        == "SEVERE"
    ]

    [
        [
            "week_start",
            "region_id",
            "temp_anomaly_c",
            "rain_anomaly_mm",
            "snow_anomaly_cm",
            "adverse_dimension_count",
            "scenario_reason"
        ]
    ]

    .head(
        15
    )

)


if len(
    severe_examples
) > 0:

    print(
        severe_examples
        .to_string(
            index=False
        )
    )

else:

    print(
        "No SEVERE weeks classified."
    )


# ============================================================
# 27. SAVE OUTPUT
# ============================================================

if overall_pass:

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
        OUTPUT_FILE,
        index=False
    )


    print(
        "\n"
        + "=" * 96
    )

    print(
        "STEP 4C.2 COMPLETE"
    )

    print(
        "=" * 96
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
        + "=" * 96
    )

    print(
        "STEP 4C.2 FAILED QA"
    )

    print(
        "=" * 96
    )


    print(
        "OVERALL STATUS: FAIL"
    )


    print(
        "Output was NOT saved."
    )


    raise RuntimeError(
        "Step 4C.2 scenario QA failed."
    )


# ============================================================
# END STEP 4C.2
# ============================================================