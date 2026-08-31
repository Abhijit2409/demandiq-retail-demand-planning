import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# DEMANDIQ
# STEP 4C.3 — WEATHER PLANNING OVERLAY
#
# Combines:
#
#   4C.3A — Regional demand weights
#   4C.3B — SKU weather sensitivity policy
#   4C.3C — Weighted SKU × Channel weather overlay
#
# Purpose:
#
# Translate Region × Week weather scenarios into the
# SKU × Channel forecasting grain used by DemandIQ.
#
# IMPORTANT:
#
# This script DOES NOT:
#   - fit another forecasting model
#   - use true_demand_units
#   - use lost_demand_units
#   - use hidden weather effects
#   - use generator elasticities
#   - modify the final forecast yet
#
# It produces a planning-policy overlay that Step 4D
# can later apply to the champion base forecasts.
# ============================================================


# ------------------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------------------

PROJECT_DIR = Path(
    r"D:\Downloads\DemandIQ"
)


DEMAND_FILE = (
    PROJECT_DIR
    / "DemandIQ_Step4A_Demand_Reconstruction.csv"
)


WEATHER_SCENARIO_FILE = (
    PROJECT_DIR
    / "05_outputs"
    / "weather_scenarios"
    / "DemandIQ_Step4C_Regional_Weather_Scenarios.csv"
)


OUTPUT_DIR = (
    PROJECT_DIR
    / "05_outputs"
    / "weather_overlay"
)


OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


OUTPUT_FILE = (
    OUTPUT_DIR
    / "DemandIQ_Step4C_Weather_Planning_Overlay.csv"
)


# ============================================================
# 2. GOVERNED STRUCTURE
# ============================================================

EXPECTED_WEEKS = 260

EXPECTED_REGIONS = 9

EXPECTED_SKUS = 3

EXPECTED_CHANNELS = 3

EXPECTED_SERIES = (
    EXPECTED_SKUS
    * EXPECTED_CHANNELS
)

EXPECTED_WEIGHT_ROWS = (
    EXPECTED_SKUS
    * EXPECTED_CHANNELS
    * EXPECTED_REGIONS
)

EXPECTED_OVERLAY_ROWS = (
    EXPECTED_WEEKS
    * EXPECTED_SERIES
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


EXPECTED_SKU_SET = {
    "APS-001",
    "CTS-001",
    "IMH-001"
}


EXPECTED_CHANNEL_SET = {
    "ECOM",
    "RETAIL",
    "WHOLESALE"
}


# ============================================================
# 3. REGIONAL WEIGHT GOVERNANCE
#
# Use the most recent complete 52 weeks of reconstructed
# demand to represent the CURRENT regional demand mix.
#
# Why 52 weeks?
#
#   - recent enough to represent current mix
#   - long enough to include one complete seasonal cycle
#   - avoids using a single seasonal quarter
#
# These are planning weights, not model coefficients.
# ============================================================

REGIONAL_WEIGHT_LOOKBACK_WEEKS = 52


# ============================================================
# 4. SKU WEATHER SENSITIVITY POLICY
#
# IMPORTANT:
#
# These are conservative PROJECT ASSUMPTIONS.
#
# They are NOT:
#   - empirically estimated elasticities
#   - Arc'teryx internal numbers
#   - synthetic generator coefficients
#
# Interpretation:
#
# If 100% of a SKU × Channel's regional demand exposure
# were classified SEVERE, the maximum overlay would be
# the severe uplift cap.
#
# If 100% were MILD, the maximum downside would be the
# mild adjustment cap.
#
# Actual adjustment is scaled by regional demand exposure.
# ============================================================

SKU_WEATHER_POLICY = {

    "APS-001": {

        "severe_adjustment_pct":
            6.0,

        "mild_adjustment_pct":
            -4.0,

        "policy_rationale":
            (
                "Higher assumed weather responsiveness "
                "for an alpine performance shell."
            )

    },


    "CTS-001": {

        "severe_adjustment_pct":
            4.0,

        "mild_adjustment_pct":
            -3.0,

        "policy_rationale":
            (
                "Moderate assumed weather responsiveness "
                "for a core technical shell."
            )

    },


    "IMH-001": {

        "severe_adjustment_pct":
            5.0,

        "mild_adjustment_pct":
            -4.0,

        "policy_rationale":
            (
                "Moderately high assumed responsiveness "
                "for an insulated midlayer."
            )

    }

}


# ============================================================
# 5. FILE QA
# ============================================================

print(
    "\n"
    + "=" * 100
)

print(
    "STEP 4C.3 — WEATHER PLANNING OVERLAY"
)

print(
    "=" * 100
)


source_files = {

    "Demand reconstruction":
        DEMAND_FILE,

    "Regional weather scenarios":
        WEATHER_SCENARIO_FILE

}


all_files_found = True


for name, path in source_files.items():

    exists = path.exists()

    print(
        f"{name}:",
        "FOUND"
        if exists
        else "MISSING"
    )

    print(
        " ",
        path
    )

    if not exists:

        all_files_found = False


if not all_files_found:

    raise FileNotFoundError(
        "One or more Step 4C.3 inputs are missing."
    )


# ============================================================
# 6. LOAD INPUTS
# ============================================================

demand_df = pd.read_csv(
    DEMAND_FILE
)


weather_df = pd.read_csv(
    WEATHER_SCENARIO_FILE
)


print(
    "\nDemand shape:",
    demand_df.shape
)


print(
    "Weather scenario shape:",
    weather_df.shape
)


# ============================================================
# 7. REQUIRED SCHEMA QA
# ============================================================

DEMAND_REQUIRED_COLUMNS = {

    "week_start",
    "sku_id",
    "region_id",
    "channel_id",
    "reconstructed_demand_units"

}


WEATHER_REQUIRED_COLUMNS = {

    "week_start",
    "region_id",

    "weather_scenario",

    "adverse_dimension_count",

    "weather_reference_available",

    "scenario_eligible_flag"

}


missing_demand_columns = (

    DEMAND_REQUIRED_COLUMNS
    - set(
        demand_df.columns
    )

)


missing_weather_columns = (

    WEATHER_REQUIRED_COLUMNS
    - set(
        weather_df.columns
    )

)


demand_schema_pass = (
    len(
        missing_demand_columns
    )
    == 0
)


weather_schema_pass = (
    len(
        missing_weather_columns
    )
    == 0
)


print(
    "\n"
    + "=" * 100
)

print(
    "INPUT SCHEMA QA"
)

print(
    "=" * 100
)


print(
    "Demand schema:",
    "PASS"
    if demand_schema_pass
    else "FAIL"
)


print(
    "Weather schema:",
    "PASS"
    if weather_schema_pass
    else "FAIL"
)


if not demand_schema_pass:

    print(
        "Missing demand columns:",
        sorted(
            missing_demand_columns
        )
    )


if not weather_schema_pass:

    print(
        "Missing weather columns:",
        sorted(
            missing_weather_columns
        )
    )


if not all(
    [
        demand_schema_pass,
        weather_schema_pass
    ]
):

    raise ValueError(
        "Step 4C.3 input schema QA failed."
    )


# ============================================================
# 8. PARSE DATES
# ============================================================

demand_df[
    "week_start"
] = pd.to_datetime(

    demand_df[
        "week_start"
    ],

    format="%Y-%m-%d",

    errors="raise"

)


weather_df[
    "week_start"
] = pd.to_datetime(

    weather_df[
        "week_start"
    ],

    format="%Y-%m-%d",

    errors="raise"

)


# ============================================================
# 9. FORBIDDEN FIELD GOVERNANCE
#
# We intentionally select only reconstructed demand.
#
# Hidden synthetic truth fields may exist in the source
# Step 4A audit table, but are NOT used below.
# ============================================================

FORBIDDEN_MODEL_FIELDS = {

    "true_demand_units",
    "lost_demand_units",
    "weather_effect_pct",
    "weather_factor",

    "positive_spike_factor",
    "negative_shock_factor",
    "noise_factor"

}


FIELDS_ACTUALLY_USED_FROM_DEMAND = {

    "week_start",
    "sku_id",
    "region_id",
    "channel_id",
    "reconstructed_demand_units"

}


forbidden_usage = (

    FIELDS_ACTUALLY_USED_FROM_DEMAND
    &
    FORBIDDEN_MODEL_FIELDS

)


leakage_pass = (
    len(
        forbidden_usage
    )
    == 0
)


print(
    "\n"
    + "=" * 100
)

print(
    "LEAKAGE / GOVERNANCE QA"
)

print(
    "=" * 100
)


print(
    "Forbidden fields used:",
    sorted(
        forbidden_usage
    )
)


print(
    "Hidden-field usage check:",
    "PASS"
    if leakage_pass
    else "FAIL"
)


if not leakage_pass:

    raise ValueError(
        "Forbidden demand field used."
    )


# ============================================================
# 10. DEMAND DIMENSION QA
# ============================================================

sku_set = set(
    demand_df[
        "sku_id"
    ]
    .unique()
)


channel_set = set(
    demand_df[
        "channel_id"
    ]
    .unique()
)


region_set = set(
    demand_df[
        "region_id"
    ]
    .unique()
)


dimension_pass = (

    sku_set
    == EXPECTED_SKU_SET

    and

    channel_set
    == EXPECTED_CHANNEL_SET

    and

    region_set
    == EXPECTED_REGION_SET

)


print(
    "\n"
    + "=" * 100
)

print(
    "DEMAND DIMENSION QA"
)

print(
    "=" * 100
)


print(
    "SKUs:",
    sorted(
        sku_set
    )
)


print(
    "Channels:",
    sorted(
        channel_set
    )
)


print(
    "Regions:",
    sorted(
        region_set
    )
)


print(
    "Expected governed dimensions:",
    "PASS"
    if dimension_pass
    else "FAIL"
)


if not dimension_pass:

    raise ValueError(
        "Unexpected demand dimensions."
    )


# ============================================================
# 11. DETERMINE CURRENT REGIONAL WEIGHT WINDOW
#
# Last 52 complete historical weeks.
# ============================================================

latest_demand_week = (
    demand_df[
        "week_start"
    ]
    .max()
)


regional_weight_start = (

    latest_demand_week

    - pd.Timedelta(
        weeks=(
            REGIONAL_WEIGHT_LOOKBACK_WEEKS
            - 1
        )
    )

)


weight_window_df = (

    demand_df[

        demand_df[
            "week_start"
        ]
        .between(
            regional_weight_start,
            latest_demand_week
        )

    ]

    .copy()

)


weight_window_unique_weeks = (

    weight_window_df[
        "week_start"
    ]
    .nunique()

)


weight_window_pass = (

    weight_window_unique_weeks
    == REGIONAL_WEIGHT_LOOKBACK_WEEKS

)


print(
    "\n"
    + "=" * 100
)

print(
    "REGIONAL WEIGHT WINDOW"
)

print(
    "=" * 100
)


print(
    "Weight basis start:",
    regional_weight_start.date()
)


print(
    "Weight basis end:",
    latest_demand_week.date()
)


print(
    "Unique weeks:",
    weight_window_unique_weeks
)


print(
    "Exactly 52 weeks:",
    "PASS"
    if weight_window_pass
    else "FAIL"
)


if not weight_window_pass:

    raise ValueError(
        "Regional weighting window is not 52 weeks."
    )


# ============================================================
# 12. CALCULATE REGIONAL DEMAND WEIGHTS
#
# Grain:
# SKU × Channel × Region
#
# Expected:
# 3 × 3 × 9 = 81 rows
# ============================================================

regional_weights = (

    weight_window_df

    .groupby(
        [
            "sku_id",
            "channel_id",
            "region_id"
        ],
        as_index=False
    )

    [
        "reconstructed_demand_units"
    ]

    .sum()

    .rename(
        columns={
            "reconstructed_demand_units":
                "regional_reconstructed_demand_units"
        }
    )

)


series_totals = (

    regional_weights

    .groupby(
        [
            "sku_id",
            "channel_id"
        ]
    )

    [
        "regional_reconstructed_demand_units"
    ]

    .transform(
        "sum"
    )

)


regional_weights[
    "series_reconstructed_demand_units"
] = series_totals


regional_weights[
    "regional_demand_weight"
] = (

    regional_weights[
        "regional_reconstructed_demand_units"
    ]

    /

    regional_weights[
        "series_reconstructed_demand_units"
    ]

)


# ============================================================
# 13. REGIONAL WEIGHT QA
# ============================================================

weight_row_pass = (

    len(
        regional_weights
    )

    == EXPECTED_WEIGHT_ROWS

)


negative_weight_count = (

    regional_weights[
        "regional_demand_weight"
    ]
    .lt(0)
    .sum()

)


negative_weight_pass = (
    negative_weight_count == 0
)


missing_weight_count = (

    regional_weights[
        "regional_demand_weight"
    ]
    .isna()
    .sum()

)


missing_weight_pass = (
    missing_weight_count == 0
)


weight_sums = (

    regional_weights

    .groupby(
        [
            "sku_id",
            "channel_id"
        ]
    )

    [
        "regional_demand_weight"
    ]

    .sum()

)


weight_sum_pass = (

    np.allclose(

        weight_sums.values,

        1.0,

        atol=1e-10

    )

)


regions_per_series = (

    regional_weights

    .groupby(
        [
            "sku_id",
            "channel_id"
        ]
    )

    [
        "region_id"
    ]

    .nunique()

)


regions_per_series_pass = (

    len(
        regions_per_series
    )
    == EXPECTED_SERIES

    and

    regions_per_series
    .eq(
        EXPECTED_REGIONS
    )
    .all()

)


print(
    "\n"
    + "=" * 100
)

print(
    "REGIONAL DEMAND WEIGHT QA"
)

print(
    "=" * 100
)


print(
    "Weight rows:",
    len(
        regional_weights
    ),
    "| Expected:",
    EXPECTED_WEIGHT_ROWS,
    "|",
    "PASS"
    if weight_row_pass
    else "FAIL"
)


print(
    "Missing weights:",
    missing_weight_count,
    "|",
    "PASS"
    if missing_weight_pass
    else "FAIL"
)


print(
    "Negative weights:",
    negative_weight_count,
    "|",
    "PASS"
    if negative_weight_pass
    else "FAIL"
)


print(
    "Weights sum to 1.0 within every SKU × Channel:",
    "PASS"
    if weight_sum_pass
    else "FAIL"
)


print(
    "Every series contains all 9 regions:",
    "PASS"
    if regions_per_series_pass
    else "FAIL"
)


if not all(
    [
        weight_row_pass,
        missing_weight_pass,
        negative_weight_pass,
        weight_sum_pass,
        regions_per_series_pass
    ]
):

    raise ValueError(
        "Regional demand weight QA failed."
    )


# ============================================================
# 14. DISPLAY REGIONAL WEIGHTS
# ============================================================

weight_display = (

    regional_weights

    .pivot_table(

        index="region_id",

        columns=[
            "sku_id",
            "channel_id"
        ],

        values="regional_demand_weight"

    )

    * 100

)


print(
    "\n"
    + "=" * 100
)

print(
    "REGIONAL DEMAND WEIGHTS (%)"
)

print(
    "=" * 100
)


print(
    weight_display
    .round(2)
    .to_string()
)


# ============================================================
# 15. ADD SKU SENSITIVITY POLICY
# ============================================================

policy_rows = []


for sku_id, policy in SKU_WEATHER_POLICY.items():

    policy_rows.append(

        {

            "sku_id":
                sku_id,

            "severe_adjustment_pct":
                policy[
                    "severe_adjustment_pct"
                ],

            "mild_adjustment_pct":
                policy[
                    "mild_adjustment_pct"
                ],

            "weather_policy_rationale":
                policy[
                    "policy_rationale"
                ]

        }

    )


policy_df = pd.DataFrame(
    policy_rows
)


policy_sku_pass = (

    set(
        policy_df[
            "sku_id"
        ]
    )

    == EXPECTED_SKU_SET

)


print(
    "\n"
    + "=" * 100
)

print(
    "SKU WEATHER POLICY"
)

print(
    "=" * 100
)


print(
    policy_df
    .to_string(
        index=False
    )
)


print(
    "\nPolicy covers all 3 SKUs:",
    "PASS"
    if policy_sku_pass
    else "FAIL"
)


if not policy_sku_pass:

    raise ValueError(
        "SKU weather policy is incomplete."
    )


# ============================================================
# 16. WEATHER SCENARIO INPUT QA
# ============================================================

scenario_row_pass = (

    len(
        weather_df
    )

    == EXPECTED_WEEKS
    * EXPECTED_REGIONS

)


scenario_region_pass = (

    set(
        weather_df[
            "region_id"
        ]
    )

    == EXPECTED_REGION_SET

)


scenario_week_pass = (

    weather_df[
        "week_start"
    ]
    .nunique()

    == EXPECTED_WEEKS

)


scenario_duplicate_count = (

    weather_df

    .duplicated(
        subset=[
            "week_start",
            "region_id"
        ]
    )

    .sum()

)


scenario_grain_pass = (
    scenario_duplicate_count == 0
)


print(
    "\n"
    + "=" * 100
)

print(
    "WEATHER SCENARIO INPUT QA"
)

print(
    "=" * 100
)


print(
    "Rows:",
    len(weather_df),
    "|",
    "PASS"
    if scenario_row_pass
    else "FAIL"
)


print(
    "9-region set:",
    "PASS"
    if scenario_region_pass
    else "FAIL"
)


print(
    "260 weeks:",
    "PASS"
    if scenario_week_pass
    else "FAIL"
)


print(
    "Region × Week grain unique:",
    "PASS"
    if scenario_grain_pass
    else "FAIL"
)


if not all(
    [
        scenario_row_pass,
        scenario_region_pass,
        scenario_week_pass,
        scenario_grain_pass
    ]
):

    raise ValueError(
        "Weather scenario input QA failed."
    )


# ============================================================
# 17. JOIN REGIONAL WEATHER TO REGIONAL DEMAND WEIGHTS
#
# Weather:
#     Week × Region
#
# Weights:
#     SKU × Channel × Region
#
# Result:
#     Week × SKU × Channel × Region
#
# Expected:
#     260 × 3 × 3 × 9 = 21,060
# ============================================================

joined = (

    weather_df

    .merge(

        regional_weights[
            [
                "sku_id",
                "channel_id",
                "region_id",
                "regional_demand_weight"
            ]
        ],

        on="region_id",

        how="left",

        validate="many_to_many"

    )

)


EXPECTED_JOINED_ROWS = (

    EXPECTED_WEEKS
    * EXPECTED_SKUS
    * EXPECTED_CHANNELS
    * EXPECTED_REGIONS

)


joined_row_pass = (

    len(
        joined
    )

    == EXPECTED_JOINED_ROWS

)


joined_weight_null_pass = (

    joined[
        "regional_demand_weight"
    ]
    .isna()
    .sum()

    == 0

)


print(
    "\n"
    + "=" * 100
)

print(
    "REGIONAL WEATHER × DEMAND WEIGHT JOIN QA"
)

print(
    "=" * 100
)


print(
    "Joined rows:",
    len(joined),
    "| Expected:",
    EXPECTED_JOINED_ROWS,
    "|",
    "PASS"
    if joined_row_pass
    else "FAIL"
)


print(
    "Missing regional weights after join:",
    "PASS"
    if joined_weight_null_pass
    else "FAIL"
)


if not all(
    [
        joined_row_pass,
        joined_weight_null_pass
    ]
):

    raise ValueError(
        "Weather-weight join QA failed."
    )


# ============================================================
# 18. CREATE WEIGHTED WEATHER CONTRIBUTIONS
# ============================================================

joined[
    "mild_weight_contribution"
] = (

    joined[
        "regional_demand_weight"
    ]

    *

    joined[
        "weather_scenario"
    ]
    .eq(
        "MILD"
    )
    .astype(int)

)


joined[
    "normal_weight_contribution"
] = (

    joined[
        "regional_demand_weight"
    ]

    *

    joined[
        "weather_scenario"
    ]
    .eq(
        "NORMAL"
    )
    .astype(int)

)


joined[
    "severe_weight_contribution"
] = (

    joined[
        "regional_demand_weight"
    ]

    *

    joined[
        "weather_scenario"
    ]
    .eq(
        "SEVERE"
    )
    .astype(int)

)


joined[
    "reference_unavailable_weight_contribution"
] = (

    joined[
        "regional_demand_weight"
    ]

    *

    joined[
        "weather_scenario"
    ]
    .eq(
        "REFERENCE_UNAVAILABLE"
    )
    .astype(int)

)


joined[
    "weighted_adverse_dimension_contribution"
] = (

    joined[
        "regional_demand_weight"
    ]

    *

    joined[
        "adverse_dimension_count"
    ]

)


# ============================================================
# 19. AGGREGATE TO FORECASTING GRAIN
#
# Week × SKU × Channel
# ============================================================

overlay_df = (

    joined

    .groupby(

        [
            "week_start",
            "sku_id",
            "channel_id"
        ],

        as_index=False

    )

    .agg(

        mild_exposure_share=(
            "mild_weight_contribution",
            "sum"
        ),

        normal_exposure_share=(
            "normal_weight_contribution",
            "sum"
        ),

        severe_exposure_share=(
            "severe_weight_contribution",
            "sum"
        ),

        reference_unavailable_share=(
            "reference_unavailable_weight_contribution",
            "sum"
        ),

        weighted_adverse_dimension_exposure=(
            "weighted_adverse_dimension_contribution",
            "sum"
        )

    )

)


# ============================================================
# 20. EXPOSURE SHARE QA
#
# Mild + Normal + Severe + Reference unavailable
# must sum to exactly the regional demand exposure = 1.
# ============================================================

overlay_df[
    "total_scenario_exposure_share"
] = (

    overlay_df[
        "mild_exposure_share"
    ]

    +

    overlay_df[
        "normal_exposure_share"
    ]

    +

    overlay_df[
        "severe_exposure_share"
    ]

    +

    overlay_df[
        "reference_unavailable_share"
    ]

)


scenario_share_sum_pass = (

    np.allclose(

        overlay_df[
            "total_scenario_exposure_share"
        ],

        1.0,

        atol=1e-10

    )

)


# ============================================================
# 21. WEATHER DATA ELIGIBILITY
# ============================================================

overlay_df[
    "eligible_weather_share"
] = (

    1.0

    -

    overlay_df[
        "reference_unavailable_share"
    ]

)


overlay_df[
    "overlay_eligible_flag"
] = (

    overlay_df[
        "eligible_weather_share"
    ]
    .ge(
        1.0 - 1e-10
    )

    .astype(int)

)


# ============================================================
# 22. ADD SKU WEATHER POLICY
# ============================================================

overlay_df = (

    overlay_df

    .merge(

        policy_df,

        on="sku_id",

        how="left",

        validate="many_to_one"

    )

)


policy_merge_pass = (

    overlay_df[
        "severe_adjustment_pct"
    ]
    .notna()
    .all()

    and

    overlay_df[
        "mild_adjustment_pct"
    ]
    .notna()
    .all()

)


if not policy_merge_pass:

    raise ValueError(
        "Missing SKU weather policy after merge."
    )


# ============================================================
# 23. CALCULATE WEATHER PLANNING ADJUSTMENT
#
# Example:
#
# APS Severe cap = +6%
#
# If 40% of APS ECOM regional demand exposure is SEVERE:
#
#     0.40 × 6% = +2.4%
#
# If 20% is simultaneously MILD:
#
#     0.20 × -4% = -0.8%
#
# Net overlay:
#
#     +2.4% - 0.8% = +1.6%
#
# No arbitrary weighted weather score is used.
# ============================================================

overlay_df[
    "severe_adjustment_contribution_pct"
] = (

    overlay_df[
        "severe_exposure_share"
    ]

    *

    overlay_df[
        "severe_adjustment_pct"
    ]

)


overlay_df[
    "mild_adjustment_contribution_pct"
] = (

    overlay_df[
        "mild_exposure_share"
    ]

    *

    overlay_df[
        "mild_adjustment_pct"
    ]

)


overlay_df[
    "weather_adjustment_pct"
] = (

    overlay_df[
        "severe_adjustment_contribution_pct"
    ]

    +

    overlay_df[
        "mild_adjustment_contribution_pct"
    ]

)


# ------------------------------------------------------------
# Reference-unavailable periods should not produce an
# operational weather adjustment.
# ------------------------------------------------------------

overlay_df.loc[

    overlay_df[
        "overlay_eligible_flag"
    ]
    == 0,

    "weather_adjustment_pct"

] = 0.0


overlay_df[
    "weather_adjustment_factor"
] = (

    1.0

    +

    (
        overlay_df[
            "weather_adjustment_pct"
        ]

        / 100.0
    )

)


# ============================================================
# 24. DOMINANT PLANNING WEATHER VIEW
# ============================================================

def determine_planning_weather_view(row):

    if (
        row[
            "overlay_eligible_flag"
        ]
        == 0
    ):

        return "REFERENCE_UNAVAILABLE"


    scenario_shares = {

        "MILD":
            row[
                "mild_exposure_share"
            ],

        "NORMAL":
            row[
                "normal_exposure_share"
            ],

        "SEVERE":
            row[
                "severe_exposure_share"
            ]

    }


    return max(

        scenario_shares,

        key=scenario_shares.get

    )


overlay_df[
    "planning_weather_view"
] = (

    overlay_df.apply(

        determine_planning_weather_view,

        axis=1

    )

)


# ============================================================
# 25. CURRENT REGION-WEIGHT METADATA
# ============================================================

overlay_df[
    "regional_weight_lookback_weeks"
] = REGIONAL_WEIGHT_LOOKBACK_WEEKS


overlay_df[
    "regional_weight_basis_start"
] = regional_weight_start


overlay_df[
    "regional_weight_basis_end"
] = latest_demand_week


overlay_df[
    "regional_weight_method"
] = (
    "TRAILING_52_WEEK_RECONSTRUCTED_DEMAND_SHARE"
)


# ============================================================
# 26. WEATHER POLICY PROVENANCE
# ============================================================

overlay_df[
    "weather_adjustment_method"
] = (
    "REGIONAL_EXPOSURE_WEIGHTED_SCENARIO_POLICY"
)


overlay_df[
    "weather_adjustment_provenance"
] = (
    "PROJECT_ASSUMPTION_NOT_EMPIRICAL_ELASTICITY"
)


overlay_df[
    "weather_input_provenance"
] = (
    "PUBLIC_WEATHER_DERIVED_SCENARIOS"
)


# ============================================================
# 27. DOMINANT REGIONAL EXPOSURE
#
# Useful context for planners.
# ============================================================

dominant_region = (

    regional_weights

    .sort_values(

        [
            "sku_id",
            "channel_id",
            "regional_demand_weight"
        ],

        ascending=[
            True,
            True,
            False
        ]

    )

    .groupby(
        [
            "sku_id",
            "channel_id"
        ],
        as_index=False
    )

    .first()

    [
        [
            "sku_id",
            "channel_id",
            "region_id",
            "regional_demand_weight"
        ]
    ]

    .rename(

        columns={

            "region_id":
                "largest_demand_region",

            "regional_demand_weight":
                "largest_region_demand_share"

        }

    )

)


overlay_df = (

    overlay_df

    .merge(

        dominant_region,

        on=[
            "sku_id",
            "channel_id"
        ],

        how="left",

        validate="many_to_one"

    )

)


# ============================================================
# 28. FINAL OUTPUT QA
# ============================================================

overlay_row_pass = (

    len(
        overlay_df
    )

    == EXPECTED_OVERLAY_ROWS

)


overlay_duplicate_count = (

    overlay_df

    .duplicated(

        subset=[
            "week_start",
            "sku_id",
            "channel_id"
        ]

    )

    .sum()

)


overlay_grain_pass = (
    overlay_duplicate_count == 0
)


series_count = (

    overlay_df[

        [
            "sku_id",
            "channel_id"
        ]

    ]

    .drop_duplicates()

    .shape[0]

)


series_count_pass = (
    series_count == EXPECTED_SERIES
)


weeks_per_series = (

    overlay_df

    .groupby(
        [
            "sku_id",
            "channel_id"
        ]
    )

    [
        "week_start"
    ]

    .nunique()

)


weeks_per_series_pass = (

    len(
        weeks_per_series
    )
    == EXPECTED_SERIES

    and

    weeks_per_series
    .eq(
        EXPECTED_WEEKS
    )
    .all()

)


adjustment_null_pass = (

    overlay_df[
        "weather_adjustment_pct"
    ]
    .notna()
    .all()

)


factor_positive_pass = (

    overlay_df[
        "weather_adjustment_factor"
    ]
    .gt(0)
    .all()

)


# ------------------------------------------------------------
# Adjustment must remain within each SKU's full-exposure caps.
# ------------------------------------------------------------

adjustment_bounds_pass = (

    (
        overlay_df[
            "weather_adjustment_pct"
        ]

        <=

        overlay_df[
            "severe_adjustment_pct"
        ]

        + 1e-10
    )

    &

    (
        overlay_df[
            "weather_adjustment_pct"
        ]

        >=

        overlay_df[
            "mild_adjustment_pct"
        ]

        - 1e-10
    )

).all()


reference_adjustment_pass = (

    overlay_df

    .loc[
        overlay_df[
            "overlay_eligible_flag"
        ]
        == 0,
        "weather_adjustment_pct"
    ]

    .eq(0)

    .all()

)


# ============================================================
# 29. FINAL QA OUTPUT
# ============================================================

qa_checks = {

    "Input schemas valid":
        (
            demand_schema_pass
            and
            weather_schema_pass
        ),

    "No forbidden hidden fields used":
        leakage_pass,

    "Demand governed dimensions valid":
        dimension_pass,

    "Regional weight window = 52 weeks":
        weight_window_pass,

    "Regional weight rows = 81":
        weight_row_pass,

    "Regional weights complete":
        missing_weight_pass,

    "Regional weights non-negative":
        negative_weight_pass,

    "Regional weights sum to 1":
        weight_sum_pass,

    "Every SKU × Channel has 9 regions":
        regions_per_series_pass,

    "Weather scenario input valid":
        all(
            [
                scenario_row_pass,
                scenario_region_pass,
                scenario_week_pass,
                scenario_grain_pass
            ]
        ),

    "Weather-weight join valid":
        (
            joined_row_pass
            and
            joined_weight_null_pass
        ),

    "Scenario exposure shares sum to 1":
        scenario_share_sum_pass,

    "SKU weather policy complete":
        policy_merge_pass,

    "Output rows = 2,340":
        overlay_row_pass,

    "Output Week × SKU × Channel grain unique":
        overlay_grain_pass,

    "Exactly 9 forecasting series":
        series_count_pass,

    "Each series has 260 weeks":
        weeks_per_series_pass,

    "No missing weather adjustments":
        adjustment_null_pass,

    "Weather adjustment factors positive":
        factor_positive_pass,

    "Weather adjustments remain within policy caps":
        adjustment_bounds_pass,

    "Reference-unavailable periods receive zero adjustment":
        reference_adjustment_pass

}


overall_pass = all(
    qa_checks.values()
)


print(
    "\n"
    + "=" * 100
)

print(
    "FINAL STEP 4C.3 QA"
)

print(
    "=" * 100
)


for name, passed in qa_checks.items():

    print(
        f"{name}:",
        "PASS"
        if passed
        else "FAIL"
    )


# ============================================================
# 30. WEATHER ADJUSTMENT SUMMARY BY SERIES
# ============================================================

series_summary = (

    overlay_df

    .groupby(
        [
            "sku_id",
            "channel_id"
        ],
        as_index=False
    )

    .agg(

        avg_weather_adjustment_pct=(
            "weather_adjustment_pct",
            "mean"
        ),

        min_weather_adjustment_pct=(
            "weather_adjustment_pct",
            "min"
        ),

        max_weather_adjustment_pct=(
            "weather_adjustment_pct",
            "max"
        ),

        avg_severe_exposure_share=(
            "severe_exposure_share",
            "mean"
        ),

        avg_mild_exposure_share=(
            "mild_exposure_share",
            "mean"
        ),

        eligible_weeks=(
            "overlay_eligible_flag",
            "sum"
        )

    )

)


summary_numeric_columns = [

    "avg_weather_adjustment_pct",
    "min_weather_adjustment_pct",
    "max_weather_adjustment_pct",
    "avg_severe_exposure_share",
    "avg_mild_exposure_share"

]


series_summary[
    summary_numeric_columns
] = (

    series_summary[
        summary_numeric_columns
    ]

    .round(3)

)


print(
    "\n"
    + "=" * 100
)

print(
    "WEATHER ADJUSTMENT SUMMARY BY SERIES"
)

print(
    "=" * 100
)


print(
    series_summary
    .to_string(
        index=False
    )
)


# ============================================================
# 31. PLANNING WEATHER VIEW DISTRIBUTION
# ============================================================

print(
    "\n"
    + "=" * 100
)

print(
    "PLANNING WEATHER VIEW DISTRIBUTION"
)

print(
    "=" * 100
)


planning_view_distribution = (

    overlay_df[
        "planning_weather_view"
    ]

    .value_counts()

    .rename_axis(
        "planning_weather_view"
    )

    .reset_index(
        name="weeks"
    )

)


planning_view_distribution[
    "pct"
] = (

    planning_view_distribution[
        "weeks"
    ]

    / len(
        overlay_df
    )

    * 100

)


planning_view_distribution[
    "pct"
] = (

    planning_view_distribution[
        "pct"
    ]

    .round(2)

)


print(
    planning_view_distribution
    .to_string(
        index=False
    )
)


# ============================================================
# 32. LARGEST POSITIVE WEATHER OVERLAYS
# ============================================================

print(
    "\n"
    + "=" * 100
)

print(
    "TOP 15 POSITIVE WEATHER OVERLAYS"
)

print(
    "=" * 100
)


positive_examples = (

    overlay_df

    .sort_values(
        "weather_adjustment_pct",
        ascending=False
    )

    [
        [
            "week_start",
            "sku_id",
            "channel_id",
            "severe_exposure_share",
            "mild_exposure_share",
            "planning_weather_view",
            "weather_adjustment_pct"
        ]
    ]

    .head(
        15
    )

    .copy()

)


print(
    positive_examples
    .round(
        {
            "severe_exposure_share":
                3,

            "mild_exposure_share":
                3,

            "weather_adjustment_pct":
                3
        }
    )
    .to_string(
        index=False
    )
)


# ============================================================
# 33. LARGEST NEGATIVE WEATHER OVERLAYS
# ============================================================

print(
    "\n"
    + "=" * 100
)

print(
    "TOP 15 NEGATIVE WEATHER OVERLAYS"
)

print(
    "=" * 100
)


negative_examples = (

    overlay_df

    .sort_values(
        "weather_adjustment_pct",
        ascending=True
    )

    [
        [
            "week_start",
            "sku_id",
            "channel_id",
            "severe_exposure_share",
            "mild_exposure_share",
            "planning_weather_view",
            "weather_adjustment_pct"
        ]
    ]

    .head(
        15
    )

    .copy()

)


print(
    negative_examples
    .round(
        {
            "severe_exposure_share":
                3,

            "mild_exposure_share":
                3,

            "weather_adjustment_pct":
                3
        }
    )
    .to_string(
        index=False
    )
)


# ============================================================
# 34. SAVE ONE MAIN OUTPUT
#
# No separate regional-weight CSV is created.
#
# Regional weights are reproducibly calculated inside this
# script to avoid unnecessary output-file clutter.
# ============================================================

if overall_pass:

    output_df = (
        overlay_df
        .copy()
    )


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


    output_df[
        "regional_weight_basis_start"
    ] = (

        pd.to_datetime(
            output_df[
                "regional_weight_basis_start"
            ]
        )
        .dt.strftime(
            "%Y-%m-%d"
        )

    )


    output_df[
        "regional_weight_basis_end"
    ] = (

        pd.to_datetime(
            output_df[
                "regional_weight_basis_end"
            ]
        )
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
        + "=" * 100
    )

    print(
        "STEP 4C.3 COMPLETE"
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
        "STEP 4C.3 FAILED QA"
    )

    print(
        "=" * 100
    )


    print(
        "OVERALL STATUS: FAIL"
    )


    print(
        "Output was NOT saved."
    )


    raise RuntimeError(
        "Step 4C.3 weather overlay QA failed."
    )


# ============================================================
# END STEP 4C.3
# ============================================================