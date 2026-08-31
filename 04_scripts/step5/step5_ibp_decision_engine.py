import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# DEMANDIQ
# STEP 5 — FINAL INVENTORY, SUPPLY & IBP DECISION ENGINE
#
# FINAL GOVERNED VERSION
#
# INPUTS
# ------------------------------------------------------------
# 1. Step 4D final 13-week demand forecast
# 2. Step 3C v5 frozen inventory / supply history
# 3. Step 3D v4 frozen retail economics
#
# OUTPUT
# ------------------------------------------------------------
# One planner-ready weekly file:
#
#     Week × SKU × Channel
#
# 13 weeks × 9 series = 117 rows
#
#
# STEP 5 BUSINESS LOGIC
# ------------------------------------------------------------
#
# BASE_SERVICE_RISK
#     Base fill rate < 92%
#     Immediate action required.
#
# WEEKLY_SERVICE_RISK
#     13-week base fill meets target, but base weekly fill
#     misses the governed 92% service target in 2+ forecast
#     weeks across the 13-week horizon. The misses do not need
#     to be consecutive. Escalate for S&OE review; do not
#     automatically release chase without timing feasibility.
#
# LOW_COVERAGE_RISK
#     Base fill rate meets target, but base ending inventory
#     falls below governed 2.5-week safety-stock coverage.
#     Protect inventory. Do not automatically release chase.
#
# SEVERE_SCENARIO_RISK
#     Base case is healthy, but severe-weather scenario causes
#     service or safety-stock risk.
#     Preserve contingency options.
#
# EXCESS_INVENTORY_RISK
#     Mild scenario leaves > 8 weeks of supply.
#
# BALANCED
#     No governed service, coverage, severe-scenario or excess
#     risk.
#
#
# GOVERNANCE
# ------------------------------------------------------------
# - No true_demand_units
# - No historical lost_demand_units as planning inputs
# - No realized future weather
# - No automatic chase for severe-only risk
# - No automatic chase merely to restore safety stock
# - Reallocation donor inventory cannot be double-counted
# - Financial values are exposure proxies, not accounting profit
# ============================================================


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(
    r"D:\Downloads\DemandIQ"
)


FORECAST_FILE = (
    PROJECT_DIR
    / "05_outputs"
    / "forecasts"
    / "DemandIQ_Step4D_Final_13Week_Forecast.csv"
)


STEP3C_FILENAME = (
    "DemandIQ_Step3C_v5_Seasonal_Buy_Inventory.csv"
)


STEP3D_FILENAME = (
    "DemandIQ_Step3D_v4_Retail_Economics.csv"
)


OUTPUT_DIR = (
    PROJECT_DIR
    / "05_outputs"
    / "ibp_decisions"
)


OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


OUTPUT_FILE = (
    OUTPUT_DIR
    / "DemandIQ_Step5_IBP_Decision_Plan.csv"
)


# ============================================================
# 2. GOVERNED STRUCTURE
# ============================================================

FORECAST_ORIGIN = pd.Timestamp(
    "2026-06-22"
)


FORECAST_START = pd.Timestamp(
    "2026-06-29"
)


FORECAST_END = pd.Timestamp(
    "2026-09-21"
)


FORECAST_HORIZON = 13


EXPECTED_SERIES = 9


EXPECTED_ROWS = (
    FORECAST_HORIZON
    * EXPECTED_SERIES
)


EXPECTED_SKUS = {
    "APS-001",
    "CTS-001",
    "IMH-001"
}


EXPECTED_CHANNELS = {
    "ECOM",
    "RETAIL",
    "WHOLESALE"
}


# ============================================================
# 3. FROZEN PLANNING ASSUMPTIONS
# ============================================================

TARGET_FILL_RATE = 0.92


SAFETY_STOCK_WEEKS = 2.5


CHASE_CAPACITY_SHARE = 0.08


ANNUAL_CARRYING_COST_RATE = 0.18


EXCESS_WOS_THRESHOLD = 8.0


# Synthetic planning-governance assumption:
# escalate a weekly execution exception when the governed
# 92% service target is missed in 2+ forecast weeks across
# the 13-week planning horizon. The misses do not need to be
# consecutive.
WEEKLY_SERVICE_EXCEPTION_WEEKS = 2


SKU_GROWTH = {

    "APS-001": 0.040,

    "CTS-001": 0.055,

    "IMH-001": 0.065

}


CHANNEL_RETURN_RATE = {

    "ECOM": 0.070,

    "RETAIL": 0.055,

    "WHOLESALE": 0.020

}


CHANNEL_RESTOCK_SHARE = {

    "ECOM": 0.85,

    "RETAIL": 0.90,

    "WHOLESALE": 0.50

}


VALID_ACTIONS = {

    "HOLD",

    "PROTECT",

    "REALLOCATE",

    "CHASE",

    "REALLOCATE + CHASE",

    "REDUCE",

    "ESCALATE"

}


# ============================================================
# 4. HELPER — FIND FILE
# ============================================================

def find_project_file(filename):

    preferred = [

        PROJECT_DIR / filename,

        PROJECT_DIR
        / "02_data"
        / "processed"
        / filename,

        PROJECT_DIR
        / "03_model_evidence"
        / filename

    ]


    for path in preferred:

        if path.exists():

            return path


    matches = list(
        PROJECT_DIR.rglob(
            filename
        )
    )


    clean_matches = [

        path

        for path in matches

        if "archive" not in str(path).lower()

        and "backup" not in str(path).lower()

    ]


    if len(clean_matches) == 1:

        return clean_matches[0]


    if len(clean_matches) == 0:

        raise FileNotFoundError(

            f"\nRequired file not found:\n"
            f"{filename}\n\n"
            f"Expected somewhere inside:\n"
            f"{PROJECT_DIR}"

        )


    print(
        f"\nMultiple active copies found for {filename}:"
    )


    for path in clean_matches:

        print(
            " -",
            path
        )


    raise RuntimeError(
        f"Multiple active copies of {filename} found."
    )


# ============================================================
# 5. HELPER — DATE PARSER
# ============================================================

def parse_date_column(
    series,
    label
):

    formats = [

        "%Y-%m-%d",

        "%d-%m-%Y",

        "%m-%d-%Y"

    ]


    candidates = []


    for fmt in formats:

        parsed = pd.to_datetime(

            series,

            format=fmt,

            errors="coerce"

        )


        success_rate = (
            parsed.notna().mean()
        )


        if parsed.notna().any():

            monday_rate = (

                parsed[
                    parsed.notna()
                ]

                .dt.dayofweek

                .eq(0)

                .mean()

            )

        else:

            monday_rate = 0.0


        candidates.append(

            (
                fmt,
                success_rate,
                monday_rate,
                parsed
            )

        )


    candidates.sort(

        key=lambda x: (
            x[1],
            x[2]
        ),

        reverse=True

    )


    best_format, success, monday, parsed = (
        candidates[0]
    )


    if success < 1.0:

        raise ValueError(
            f"{label} date parsing failed."
        )


    print(
        f"{label} date format:",
        best_format
    )


    return parsed


# ============================================================
# 6. HELPER — SELECT COLUMN
# ============================================================

def choose_column(
    df,
    candidates,
    required=True,
    label="field"
):

    for column in candidates:

        if column in df.columns:

            print(
                f"{label}: {column}"
            )

            return column


    if required:

        raise ValueError(

            f"No supported column found for {label}.\n"
            f"Tried:\n{candidates}"

        )


    print(
        f"{label}: NOT AVAILABLE"
    )

    return None


# ============================================================
# 7. LOCATE INPUT FILES
# ============================================================

STEP3C_FILE = find_project_file(
    STEP3C_FILENAME
)


STEP3D_FILE = find_project_file(
    STEP3D_FILENAME
)


print(
    "\n"
    + "=" * 100
)

print(
    "STEP 5 — FINAL INVENTORY, SUPPLY & IBP DECISION ENGINE"
)

print(
    "=" * 100
)


print(
    "\nStep 4D forecast:"
)

print(
    FORECAST_FILE
)


print(
    "\nStep 3C inventory:"
)

print(
    STEP3C_FILE
)


print(
    "\nStep 3D economics:"
)

print(
    STEP3D_FILE
)


if not FORECAST_FILE.exists():

    raise FileNotFoundError(
        FORECAST_FILE
    )


# ============================================================
# 8. LOAD INPUTS
# ============================================================

forecast = pd.read_csv(
    FORECAST_FILE
)


inventory = pd.read_csv(
    STEP3C_FILE
)


economics = pd.read_csv(
    STEP3D_FILE
)


print(
    "\nForecast shape:",
    forecast.shape
)


print(
    "Inventory shape:",
    inventory.shape
)


print(
    "Economics shape:",
    economics.shape
)


# ============================================================
# 9. FORECAST SCHEMA
# ============================================================

FORECAST_REQUIRED = {

    "forecast_week_start",

    "horizon_week",

    "sku_id",

    "channel_id",

    "base_forecast_units",

    "mild_scenario_forecast_units",

    "severe_scenario_forecast_units",

    "champion_model",

    "champion_family"

}


forecast_missing = (

    FORECAST_REQUIRED

    - set(
        forecast.columns
    )

)


if forecast_missing:

    raise ValueError(

        f"Step 4D forecast missing columns:\n"
        f"{sorted(forecast_missing)}"

    )


forecast[
    "forecast_week_start"
] = pd.to_datetime(

    forecast[
        "forecast_week_start"
    ],

    format="%Y-%m-%d",

    errors="raise"

)


for column in [

    "base_forecast_units",

    "mild_scenario_forecast_units",

    "severe_scenario_forecast_units"

]:

    forecast[
        column
    ] = pd.to_numeric(

        forecast[
            column
        ],

        errors="raise"

    )


# ============================================================
# 10. IDENTIFY INVENTORY COLUMNS
# ============================================================

inventory_date_col = choose_column(

    inventory,

    [
        "week_start",
        "date"
    ],

    label="Inventory date"

)


ending_inventory_col = choose_column(

    inventory,

    [
        "ending_inventory_units",

        "ending_inventory",

        "end_inventory_units"
    ],

    label="Ending inventory"

)


seasonal_receipt_col = choose_column(

    inventory,

    [
        "seasonal_receipt_units",

        "planned_receipt_units",

        "base_receipt_units",

        "committed_receipt_units",

        "receipt_units"
    ],

    label="Seasonal receipt"

)


chase_receipt_col = choose_column(

    inventory,

    [
        "chase_receipt_units",

        "chase_received_units",

        "chase_units_received"
    ],

    required=False,

    label="Historical chase receipt"

)


historical_ship_col = choose_column(

    inventory,

    [
        "shipped_units",

        "observed_sales_units"
    ],

    required=False,

    label="Historical shipped units"

)


# ============================================================
# 11. IDENTIFY ECONOMIC COLUMNS
# ============================================================

economic_date_col = choose_column(

    economics,

    [
        "week_start",
        "date"
    ],

    label="Economics date"

)


asp_col = choose_column(

    economics,

    [
        "net_asp_cad",

        "full_price_net_asp_cad",

        "promo_adjusted_price_cad"
    ],

    label="Net ASP"

)


economic_ship_col = choose_column(

    economics,

    [
        "shipped_units",

        "observed_sales_units"
    ],

    required=False,

    label="Economics shipment weight"

)


current_excess_exposure_col = choose_column(

    economics,

    [
        "ending_inventory_value_proxy_cad",

        "total_excess_inventory_exposure_cad"
    ],

    required=False,

    label="Current inventory economic exposure"

)


# ============================================================
# 12. PARSE DATES
# ============================================================

inventory[
    inventory_date_col
] = parse_date_column(

    inventory[
        inventory_date_col
    ],

    "Inventory"

)


economics[
    economic_date_col
] = parse_date_column(

    economics[
        economic_date_col
    ],

    "Economics"

)


# ============================================================
# 13. NORMALIZE NUMERIC INPUTS
# ============================================================

inventory[
    ending_inventory_col
] = pd.to_numeric(

    inventory[
        ending_inventory_col
    ],

    errors="raise"

)


inventory[
    seasonal_receipt_col
] = pd.to_numeric(

    inventory[
        seasonal_receipt_col
    ],

    errors="coerce"

).fillna(0.0)


if chase_receipt_col is not None:

    inventory[
        chase_receipt_col
    ] = pd.to_numeric(

        inventory[
            chase_receipt_col
        ],

        errors="coerce"

    ).fillna(0.0)


if historical_ship_col is not None:

    inventory[
        historical_ship_col
    ] = pd.to_numeric(

        inventory[
            historical_ship_col
        ],

        errors="coerce"

    ).fillna(0.0)


economics[
    asp_col
] = pd.to_numeric(

    economics[
        asp_col
    ],

    errors="coerce"

)


if economic_ship_col is not None:

    economics[
        economic_ship_col
    ] = pd.to_numeric(

        economics[
            economic_ship_col
        ],

        errors="coerce"

    ).fillna(0.0)


if current_excess_exposure_col is not None:

    economics[
        current_excess_exposure_col
    ] = pd.to_numeric(

        economics[
            current_excess_exposure_col
        ],

        errors="coerce"

    )


# ============================================================
# 14. GOVERNANCE QA
# ============================================================

for required in [

    "sku_id",

    "channel_id"

]:

    if required not in inventory.columns:

        raise ValueError(
            f"Inventory missing {required}"
        )


    if required not in economics.columns:

        raise ValueError(
            f"Economics missing {required}"
        )


INVENTORY_FIELDS_USED = {

    inventory_date_col,

    "sku_id",

    "channel_id",

    ending_inventory_col,

    seasonal_receipt_col

}


if chase_receipt_col:

    INVENTORY_FIELDS_USED.add(
        chase_receipt_col
    )


if historical_ship_col:

    INVENTORY_FIELDS_USED.add(
        historical_ship_col
    )


FORBIDDEN_FIELDS = {

    "true_demand_units",

    "lost_demand_units",

    "weather_effect_pct",

    "weather_factor",

    "audit_hidden_demand"

}


forbidden_used = (

    INVENTORY_FIELDS_USED

    & FORBIDDEN_FIELDS

)


leakage_pass = (
    len(forbidden_used) == 0
)


print(
    "\n"
    + "=" * 100
)

print(
    "GOVERNANCE QA"
)

print(
    "=" * 100
)


print(
    "Forbidden historical truth fields used:",
    sorted(
        forbidden_used
    )
)


print(
    "Leakage check:",
    "PASS"
    if leakage_pass
    else "FAIL"
)


if not leakage_pass:

    raise RuntimeError(
        "Forbidden Step 5 field used."
    )


# ============================================================
# 15. STEP 4D FORECAST QA
# ============================================================

forecast_checks = {

    "Rows = 117":
        len(forecast)
        == EXPECTED_ROWS,

    "13 forecast weeks":
        forecast[
            "forecast_week_start"
        ]
        .nunique()
        == FORECAST_HORIZON,

    "Forecast starts 2026-06-29":
        forecast[
            "forecast_week_start"
        ]
        .min()
        == FORECAST_START,

    "Forecast ends 2026-09-21":
        forecast[
            "forecast_week_start"
        ]
        .max()
        == FORECAST_END,

    "Forecast grain unique":
        forecast
        .duplicated(
            subset=[
                "forecast_week_start",
                "sku_id",
                "channel_id"
            ]
        )
        .sum()
        == 0,

    "Exactly 9 series":
        forecast[
            [
                "sku_id",
                "channel_id"
            ]
        ]
        .drop_duplicates()
        .shape[0]
        == EXPECTED_SERIES,

    "Mild <= Base":
        (
            forecast[
                "mild_scenario_forecast_units"
            ]
            <=
            forecast[
                "base_forecast_units"
            ]
            + 1e-10
        )
        .all(),

    "Base <= Severe":
        (
            forecast[
                "base_forecast_units"
            ]
            <=
            forecast[
                "severe_scenario_forecast_units"
            ]
            + 1e-10
        )
        .all()

}


print(
    "\n"
    + "=" * 100
)

print(
    "STEP 4D FORECAST QA"
)

print(
    "=" * 100
)


for name, passed in forecast_checks.items():

    print(
        f"{name}:",
        "PASS"
        if passed
        else "FAIL"
    )


if not all(
    forecast_checks.values()
):

    raise RuntimeError(
        "Step 4D forecast QA failed."
    )


# ============================================================
# 16. BASE RECEIPT FIELD
# ============================================================

inventory[
    "_base_receipt_units"
] = (

    inventory[
        seasonal_receipt_col
    ]

    .copy()

)


if (

    seasonal_receipt_col
    == "receipt_units"

    and

    chase_receipt_col is not None

):

    inventory[
        "_base_receipt_units"
    ] = (

        inventory[
            "_base_receipt_units"
        ]

        -

        inventory[
            chase_receipt_col
        ]

    ).clip(
        lower=0
    )


    receipt_method = (
        "TOTAL_RECEIPT_MINUS_EXPLICIT_CHASE"
    )


elif seasonal_receipt_col == "receipt_units":

    receipt_method = (
        "GENERIC_RECEIPT_USED_AS_SEASONAL_PROXY"
    )


else:

    receipt_method = (
        "EXPLICIT_SEASONAL_RECEIPT"
    )


print(
    "\nReceipt construction method:",
    receipt_method
)


# ============================================================
# 17. CURRENT OPENING INVENTORY
# ============================================================

inventory_origin = (

    inventory[
        inventory[
            inventory_date_col
        ]
        == FORECAST_ORIGIN
    ]

    .copy()

)


if len(inventory_origin) == 0:

    raise RuntimeError(
        "No inventory position found at 2026-06-22."
    )


opening_inventory = (

    inventory_origin

    .groupby(
        [
            "sku_id",
            "channel_id"
        ],

        as_index=False

    )

    .agg(

        opening_inventory_units=(
            ending_inventory_col,
            "sum"
        )

    )

)


opening_series_pass = (
    len(opening_inventory)
    == EXPECTED_SERIES
)


print(
    "\n"
    + "=" * 100
)

print(
    "CURRENT INVENTORY POSITION"
)

print(
    "=" * 100
)


print(
    opening_inventory
    .round(2)
    .to_string(
        index=False
    )
)


print(
    "\nOpening inventory total:",
    round(

        opening_inventory[
            "opening_inventory_units"
        ]
        .sum(),

        2

    )
)


print(
    "Exactly 9 SKU × Channel positions:",
    "PASS"
    if opening_series_pass
    else "FAIL"
)


if not opening_series_pass:

    raise RuntimeError(
        "Opening inventory coverage failed."
    )


# ============================================================
# 18. PRIOR-WEEK SHIPMENTS
# ============================================================

if historical_ship_col is not None:

    prior_shipments = (

        inventory_origin

        .groupby(
            [
                "sku_id",
                "channel_id"
            ],

            as_index=False

        )

        .agg(

            prior_week_shipped_units=(
                historical_ship_col,
                "sum"
            )

        )

    )


else:

    prior_shipments = (

        opening_inventory[
            [
                "sku_id",
                "channel_id"
            ]
        ]

        .copy()

    )


    prior_shipments[
        "prior_week_shipped_units"
    ] = 0.0


# ============================================================
# 19. FORWARD COMMITTED RECEIPT PROXY
#
# Prior-year seasonal receipt pattern shifted 52 weeks
# + frozen structural SKU growth.
# ============================================================

prior_receipts = (

    inventory

    .groupby(
        [
            inventory_date_col,
            "sku_id",
            "channel_id"
        ],

        as_index=False

    )

    .agg(

        prior_year_receipt_units=(
            "_base_receipt_units",
            "sum"
        )

    )

)


prior_receipts[
    "forecast_week_start"
] = (

    prior_receipts[
        inventory_date_col
    ]

    + pd.Timedelta(
        weeks=52
    )

)


prior_receipts = (

    prior_receipts[
        prior_receipts[
            "forecast_week_start"
        ]
        .between(
            FORECAST_START,
            FORECAST_END
        )
    ]

    .copy()

)


prior_receipts[
    "sku_growth_rate"
] = (

    prior_receipts[
        "sku_id"
    ]

    .map(
        SKU_GROWTH
    )

)


if prior_receipts[
    "sku_growth_rate"
].isna().any():

    raise RuntimeError(
        "Missing SKU growth assumption."
    )


prior_receipts[
    "committed_receipt_units"
] = (

    prior_receipts[
        "prior_year_receipt_units"
    ]

    *

    (
        1

        +

        prior_receipts[
            "sku_growth_rate"
        ]
    )

)


forward_receipts = (

    prior_receipts

    .groupby(
        [
            "forecast_week_start",
            "sku_id",
            "channel_id"
        ],

        as_index=False

    )

    .agg(

        committed_receipt_units=(
            "committed_receipt_units",
            "sum"
        )

    )

)


# ============================================================
# 20. FULL SEASON COMMITMENT / CHASE CAPACITY
# ============================================================

prior_season = (

    inventory[
        (
            inventory[
                inventory_date_col
            ]
            .dt.year
            == 2025
        )

        &

        (
            inventory[
                inventory_date_col
            ]
            .dt.month
            .isin(
                [
                    8,
                    9,
                    10
                ]
            )
        )
    ]

    .copy()

)


seasonal_commitment = (

    prior_season

    .groupby(
        [
            "sku_id",
            "channel_id"
        ],

        as_index=False

    )

    .agg(

        prior_year_seasonal_receipt_units=(
            "_base_receipt_units",
            "sum"
        )

    )

)


seasonal_commitment[
    "sku_growth_rate"
] = (

    seasonal_commitment[
        "sku_id"
    ]

    .map(
        SKU_GROWTH
    )

)


seasonal_commitment[
    "forward_seasonal_commitment_units"
] = (

    seasonal_commitment[
        "prior_year_seasonal_receipt_units"
    ]

    *

    (
        1

        +

        seasonal_commitment[
            "sku_growth_rate"
        ]
    )

)


seasonal_commitment[
    "chase_capacity_units"
] = (

    seasonal_commitment[
        "forward_seasonal_commitment_units"
    ]

    *

    CHASE_CAPACITY_SHARE

)


if len(
    seasonal_commitment
) != EXPECTED_SERIES:

    raise RuntimeError(
        "Seasonal commitment does not cover 9 series."
    )


# ============================================================
# 21. TRAILING 52-WEEK ECONOMIC ASSUMPTIONS
# ============================================================

economics_start = (

    FORECAST_ORIGIN

    - pd.Timedelta(
        weeks=51
    )

)


economics_window = (

    economics[
        economics[
            economic_date_col
        ]
        .between(
            economics_start,
            FORECAST_ORIGIN
        )
    ]

    .copy()

)


economic_rows = []


for (
    sku_id,
    channel_id
), group in economics_window.groupby(
    [
        "sku_id",
        "channel_id"
    ]
):

    values = (

        group[
            asp_col
        ]

        .astype(float)

    )


    valid = (
        values.notna()
    )


    if valid.sum() == 0:

        planning_asp = np.nan


    elif economic_ship_col is not None:

        weights = (

            group[
                economic_ship_col
            ]

            .astype(float)

            .fillna(0.0)

            .clip(
                lower=0
            )

        )


        if weights[
            valid
        ].sum() > 0:

            planning_asp = float(

                np.average(

                    values[
                        valid
                    ],

                    weights=weights[
                        valid
                    ]

                )

            )


        else:

            planning_asp = float(

                values[
                    valid
                ]
                .mean()

            )


    else:

        planning_asp = float(

            values[
                valid
            ]
            .mean()

        )


    economic_rows.append({

        "sku_id":
            sku_id,

        "channel_id":
            channel_id,

        "planning_net_asp_cad":
            planning_asp

    })


economic_assumptions = pd.DataFrame(
    economic_rows
)


if (

    len(economic_assumptions)
    != EXPECTED_SERIES

    or

    economic_assumptions[
        "planning_net_asp_cad"
    ]
    .isna()
    .any()

):

    raise RuntimeError(
        "Planning ASP assumptions incomplete."
    )


# ============================================================
# 22. CURRENT ECONOMIC EXPOSURE
# ============================================================

if current_excess_exposure_col is not None:

    economic_origin = (

        economics[
            economics[
                economic_date_col
            ]
            == FORECAST_ORIGIN
        ]

        .copy()

    )


    current_exposure = (

        economic_origin

        .groupby(
            [
                "sku_id",
                "channel_id"
            ],

            as_index=False

        )

        .agg(

            current_inventory_economic_exposure_cad=(
                current_excess_exposure_col,
                "sum"
            )

        )

    )


else:

    current_exposure = (

        economic_assumptions[
            [
                "sku_id",
                "channel_id"
            ]
        ]

        .copy()

    )


    current_exposure[
        "current_inventory_economic_exposure_cad"
    ] = np.nan


# ============================================================
# 23. PREPARE FORWARD PLAN
# ============================================================

plan = (

    forecast

    .merge(

        opening_inventory,

        on=[
            "sku_id",
            "channel_id"
        ],

        how="left",

        validate="many_to_one"

    )

    .merge(

        prior_shipments,

        on=[
            "sku_id",
            "channel_id"
        ],

        how="left",

        validate="many_to_one"

    )

    .merge(

        forward_receipts,

        on=[
            "forecast_week_start",
            "sku_id",
            "channel_id"
        ],

        how="left",

        validate="one_to_one"

    )

    .merge(

        seasonal_commitment[
            [
                "sku_id",

                "channel_id",

                "forward_seasonal_commitment_units",

                "chase_capacity_units"
            ]
        ],

        on=[
            "sku_id",
            "channel_id"
        ],

        how="left",

        validate="many_to_one"

    )

    .merge(

        economic_assumptions,

        on=[
            "sku_id",
            "channel_id"
        ],

        how="left",

        validate="many_to_one"

    )

    .merge(

        current_exposure,

        on=[
            "sku_id",
            "channel_id"
        ],

        how="left",

        validate="many_to_one"

    )

)


plan[
    "committed_receipt_units"
] = (

    plan[
        "committed_receipt_units"
    ]

    .fillna(0.0)

)


plan[
    "prior_week_shipped_units"
] = (

    plan[
        "prior_week_shipped_units"
    ]

    .fillna(0.0)

)


plan[
    "returns_rate"
] = (

    plan[
        "channel_id"
    ]

    .map(
        CHANNEL_RETURN_RATE
    )

)


plan[
    "sellable_restock_share"
] = (

    plan[
        "channel_id"
    ]

    .map(
        CHANNEL_RESTOCK_SHARE
    )

)


if (

    plan[
        [
            "opening_inventory_units",

            "forward_seasonal_commitment_units",

            "chase_capacity_units",

            "planning_net_asp_cad",

            "returns_rate",

            "sellable_restock_share"
        ]
    ]

    .isna()

    .any()

    .any()

):

    raise RuntimeError(
        "Missing planning input after joins."
    )


# ============================================================
# 24. FORWARD RUN RATE / SAFETY STOCK
# ============================================================

plan = (

    plan

    .sort_values(
        [
            "sku_id",
            "channel_id",
            "forecast_week_start"
        ]
    )

    .reset_index(
        drop=True
    )

)


plan[
    "forecast_run_rate_units"
] = np.nan


for (
    sku_id,
    channel_id
), group in plan.groupby(
    [
        "sku_id",
        "channel_id"
    ]
):

    idx = (
        group.index.to_list()
    )


    values = (

        group[
            "base_forecast_units"
        ]

        .to_numpy(
            dtype=float
        )

    )


    final_four_avg = (
        values[-4:].mean()
    )


    run_rates = []


    for i in range(
        len(values)
    ):

        if i <= len(values) - 4:

            run_rate = (

                values[
                    i:i + 4
                ]

                .mean()

            )


        else:

            run_rate = (
                final_four_avg
            )


        run_rates.append(
            run_rate
        )


    plan.loc[
        idx,
        "forecast_run_rate_units"
    ] = run_rates


plan[
    "safety_stock_units"
] = (

    plan[
        "forecast_run_rate_units"
    ]

    *

    SAFETY_STOCK_WEEKS

)


# ============================================================
# 25. INVENTORY SIMULATION FUNCTION
# ============================================================

def simulate_scenario(
    frame,
    demand_column,
    prefix
):

    rows = []


    for (
        sku_id,
        channel_id
    ), group in frame.groupby(
        [
            "sku_id",
            "channel_id"
        ]
    ):

        group = (

            group

            .sort_values(
                "forecast_week_start"
            )

            .copy()

        )


        beginning_inventory = float(

            group[
                "opening_inventory_units"
            ]

            .iloc[0]

        )


        prior_ship = float(

            group[
                "prior_week_shipped_units"
            ]

            .iloc[0]

        )


        return_rate = float(

            group[
                "returns_rate"
            ]

            .iloc[0]

        )


        restock_share = float(

            group[
                "sellable_restock_share"
            ]

            .iloc[0]

        )


        for idx, row in group.iterrows():

            demand = max(

                0.0,

                float(
                    row[
                        demand_column
                    ]
                )

            )


            receipt = max(

                0.0,

                float(
                    row[
                        "committed_receipt_units"
                    ]
                )

            )


            return_restock = (

                prior_ship

                *

                return_rate

                *

                restock_share

            )


            available = (

                beginning_inventory

                +

                receipt

                +

                return_restock

            )


            shipped = min(
                available,
                demand
            )


            lost = max(
                0.0,
                demand - shipped
            )


            ending = max(
                0.0,
                available - shipped
            )


            fill_rate = (

                shipped / demand

                if demand > 0

                else 1.0

            )


            run_rate = float(

                row[
                    "forecast_run_rate_units"
                ]

            )


            wos = (

                ending / run_rate

                if run_rate > 0

                else np.nan

            )


            rows.append({

                "row_index":
                    idx,

                f"{prefix}_beginning_inventory_units":
                    beginning_inventory,

                f"{prefix}_return_restock_units":
                    return_restock,

                f"{prefix}_available_units":
                    available,

                f"{prefix}_shipped_units":
                    shipped,

                f"{prefix}_lost_demand_units":
                    lost,

                f"{prefix}_ending_inventory_units":
                    ending,

                f"{prefix}_fill_rate":
                    fill_rate,

                f"{prefix}_weeks_of_supply":
                    wos

            })


            beginning_inventory = (
                ending
            )


            prior_ship = (
                shipped
            )


    return (

        pd.DataFrame(
            rows
        )

        .set_index(
            "row_index"
        )

        .sort_index()

    )


# ============================================================
# 26. RUN THREE SCENARIOS
# ============================================================

mild_sim = simulate_scenario(

    plan,

    "mild_scenario_forecast_units",

    "mild"

)


base_sim = simulate_scenario(

    plan,

    "base_forecast_units",

    "base"

)


severe_sim = simulate_scenario(

    plan,

    "severe_scenario_forecast_units",

    "severe"

)


plan = pd.concat(

    [
        plan,

        mild_sim,

        base_sim,

        severe_sim
    ],

    axis=1

)


# ============================================================
# 27. INVENTORY SIMULATION QA
# ============================================================

flow_checks = {}


for scenario in [

    "mild",

    "base",

    "severe"

]:

    expected_end = (

        plan[
            f"{scenario}_beginning_inventory_units"
        ]

        +

        plan[
            "committed_receipt_units"
        ]

        +

        plan[
            f"{scenario}_return_restock_units"
        ]

        -

        plan[
            f"{scenario}_shipped_units"
        ]

    )


    flow_checks[
        f"{scenario.upper()} inventory equation reconciles"
    ] = (

        np.allclose(

            expected_end,

            plan[
                f"{scenario}_ending_inventory_units"
            ],

            atol=1e-8

        )

    )


    flow_checks[
        f"{scenario.upper()} ending inventory non-negative"
    ] = (

        plan[
            f"{scenario}_ending_inventory_units"
        ]

        .ge(0)

        .all()

    )


    flow_checks[
        f"{scenario.upper()} lost demand non-negative"
    ] = (

        plan[
            f"{scenario}_lost_demand_units"
        ]

        .ge(0)

        .all()

    )


    flow_checks[
        f"{scenario.upper()} fill rate within 0-1"
    ] = (

        plan[
            f"{scenario}_fill_rate"
        ]

        .between(
            0,
            1
        )

        .all()

    )


print(
    "\n"
    + "=" * 100
)

print(
    "FORWARD INVENTORY SIMULATION QA"
)

print(
    "=" * 100
)


for name, passed in flow_checks.items():

    print(
        f"{name}:",
        "PASS"
        if passed
        else "FAIL"
    )


if not all(
    flow_checks.values()
):

    raise RuntimeError(
        "Forward inventory simulation failed."
    )


# ============================================================
# 28. WEEKLY ECONOMIC EXPOSURE
# ============================================================

for scenario in [

    "mild",

    "base",

    "severe"

]:

    plan[
        f"{scenario}_lost_revenue_opportunity_cad"
    ] = (

        plan[
            f"{scenario}_lost_demand_units"
        ]

        *

        plan[
            "planning_net_asp_cad"
        ]

    )


    plan[
        f"{scenario}_ending_inventory_value_proxy_cad"
    ] = (

        plan[
            f"{scenario}_ending_inventory_units"
        ]

        *

        plan[
            "planning_net_asp_cad"
        ]

    )


    plan[
        f"{scenario}_weekly_carrying_cost_proxy_cad"
    ] = (

        plan[
            f"{scenario}_ending_inventory_value_proxy_cad"
        ]

        *

        (
            ANNUAL_CARRYING_COST_RATE
            / 52
        )

    )


# ============================================================
# HELPER — MAX CONSECUTIVE TRUE VALUES
# ============================================================

def max_consecutive_true(values):

    max_run = 0
    current_run = 0

    for value in values:

        if bool(value):

            current_run += 1
            max_run = max(
                max_run,
                current_run
            )

        else:

            current_run = 0

    return max_run


# ============================================================
# 29. SERIES-LEVEL IBP METRICS
# ============================================================

series_rows = []


for (
    sku_id,
    channel_id
), group in plan.groupby(
    [
        "sku_id",
        "channel_id"
    ]
):

    group = (

        group

        .sort_values(
            "forecast_week_start"
        )

    )
    # ========================================================
    # WEEKLY SERVICE EXECUTION DIAGNOSTICS
    #
    # Purpose:
    # 13-week aggregate fill is an IBP KPI, but it can hide
    # acute week-level service failures.
    #
    # DIAGNOSTIC ONLY:
    # These fields do NOT change risk_type, priority_tier,
    # planner_action, reallocation, or chase logic yet.
    # ========================================================

    group = group.copy()


    group[
        "_base_weekly_fill_rate"
    ] = np.where(

        group[
            "base_forecast_units"
        ] > 0,

        group[
            "base_shipped_units"
        ]

        /

        group[
            "base_forecast_units"
        ],

        1.0

    )


    group[
        "_base_weekly_fill_rate"
    ] = (

        group[
            "_base_weekly_fill_rate"
        ]

        .clip(
            lower=0.0,
            upper=1.0
        )

    )


    group[
        "_weekly_below_target_flag"
    ] = (

        group[
            "_base_weekly_fill_rate"
        ]

        <

        TARGET_FILL_RATE

    ).astype(int)


    group[
        "_weekly_service_gap_units"
    ] = (

        group[
            "base_forecast_units"
        ]

        -

        group[
            "base_shipped_units"
        ]

    ).clip(
        lower=0.0
    )


    min_weekly_base_fill_rate = float(

        group[
            "_base_weekly_fill_rate"
        ]

        .min()

    )


    worst_week_idx = (

        group[
            "_base_weekly_fill_rate"
        ]

        .idxmin()

    )


    worst_week = (

        group.loc[
            worst_week_idx,
            "forecast_week_start"
        ]

    )


    worst_week_service_gap_units = float(

        group.loc[
            worst_week_idx,
            "_weekly_service_gap_units"
        ]

    )


    weeks_below_service_target = int(

        group[
            "_weekly_below_target_flag"
        ]

        .sum()

    )


    max_consecutive_weeks_below_target = int(

        max_consecutive_true(

            group[
                "_weekly_below_target_flag"
            ]

            .tolist()

        )

    )


    # --------------------------------------------------------
    # Governed weekly execution exception
    # --------------------------------------------------------
    # Synthetic planning-governance rule:
    # escalate when the existing 92% service target is missed
    # in 2+ forecast weeks across the 13-week horizon. The
    # misses do not need to be consecutive. This flags the
    # series for S&OE review but does NOT automatically release
    # chase.

    weekly_service_exception_flag = int(
        weeks_below_service_target
        >= WEEKLY_SERVICE_EXCEPTION_WEEKS
    )


    # --------------------------------------------------------
    # Demand and shipments
    # --------------------------------------------------------

    base_demand = (
        group[
            "base_forecast_units"
        ]
        .sum()
    )


    base_ship = (
        group[
            "base_shipped_units"
        ]
        .sum()
    )


    mild_demand = (
        group[
            "mild_scenario_forecast_units"
        ]
        .sum()
    )


    mild_ship = (
        group[
            "mild_shipped_units"
        ]
        .sum()
    )


    severe_demand = (
        group[
            "severe_scenario_forecast_units"
        ]
        .sum()
    )


    severe_ship = (
        group[
            "severe_shipped_units"
        ]
        .sum()
    )


    # --------------------------------------------------------
    # Fill rate
    # --------------------------------------------------------

    base_fill = (

        base_ship / base_demand

        if base_demand > 0

        else 1.0

    )


    mild_fill = (

        mild_ship / mild_demand

        if mild_demand > 0

        else 1.0

    )


    severe_fill = (

        severe_ship / severe_demand

        if severe_demand > 0

        else 1.0

    )


    # --------------------------------------------------------
    # Final inventory
    # --------------------------------------------------------

    last = (
        group.iloc[-1]
    )


    base_end = float(

        last[
            "base_ending_inventory_units"
        ]

    )


    mild_end = float(

        last[
            "mild_ending_inventory_units"
        ]

    )


    severe_end = float(

        last[
            "severe_ending_inventory_units"
        ]

    )


    safety_end = float(

        last[
            "safety_stock_units"
        ]

    )


    final_run_rate = float(

        last[
            "forecast_run_rate_units"
        ]

    )


    # --------------------------------------------------------
    # Final WOS
    # --------------------------------------------------------

    base_end_wos = (

        base_end / final_run_rate

        if final_run_rate > 0

        else np.nan

    )


    mild_end_wos = (

        mild_end / final_run_rate

        if final_run_rate > 0

        else np.nan

    )


    severe_end_wos = (

        severe_end / final_run_rate

        if final_run_rate > 0

        else np.nan

    )


    # --------------------------------------------------------
    # Lost demand
    # --------------------------------------------------------

    base_lost = (
        group[
            "base_lost_demand_units"
        ]
        .sum()
    )


    mild_lost = (
        group[
            "mild_lost_demand_units"
        ]
        .sum()
    )


    severe_lost = (
        group[
            "severe_lost_demand_units"
        ]
        .sum()
    )


    base_lost_pct = (

        base_lost / base_demand

        if base_demand > 0

        else 0.0

    )


    severe_lost_pct = (

        severe_lost / severe_demand

        if severe_demand > 0

        else 0.0

    )


    # --------------------------------------------------------
    # Excess
    # --------------------------------------------------------

    base_excess = max(
        0.0,
        base_end - safety_end
    )


    mild_excess = max(
        0.0,
        mild_end - safety_end
    )


    severe_excess = max(
        0.0,
        severe_end - safety_end
    )


    # --------------------------------------------------------
    # Safety-stock gaps
    # --------------------------------------------------------

    base_safety_gap = max(
        0.0,
        safety_end - base_end
    )


    severe_safety_gap = max(
        0.0,
        safety_end - severe_end
    )


    # --------------------------------------------------------
    # Immediate base service gap
    #
    # IMPORTANT:
    #
    # This is an ACT-NOW gap only when base fill rate fails
    # the governed service target.
    #
    # Low safety stock alone does not release chase.
    # --------------------------------------------------------

    if base_fill < TARGET_FILL_RATE:

        immediate_base_gap = (

            base_lost

            +

            base_safety_gap

        )


    else:

        immediate_base_gap = 0.0


    # --------------------------------------------------------
    # Base protection gap
    #
    # This captures thin buffer even when service is okay.
    #
    # It is NOT an immediate procurement requirement.
    # --------------------------------------------------------

    base_protection_gap = (

        base_safety_gap

        if base_fill >= TARGET_FILL_RATE

        else 0.0

    )


    # --------------------------------------------------------
    # Severe contingency gap
    # --------------------------------------------------------

    severe_contingency_gap = (

        severe_lost

        +

        severe_safety_gap

    )


    # ========================================================
    # FINAL CORRECTED RISK HIERARCHY
    # ========================================================
    #
    # 1. Aggregate base service failure
    # 2. Persistent weekly execution service failure
    # 3. Base low coverage
    # 4. Severe-only scenario risk
    # 5. Excess risk
    # 6. Balanced
    #
    # IMPORTANT:
    # WEEKLY_SERVICE_RISK is escalated for review, but it does
    # not automatically release chase because supply-response
    # lead-time feasibility is not modeled in Step 5.
    # ========================================================

    if base_fill < TARGET_FILL_RATE:

        risk_type = (
            "BASE_SERVICE_RISK"
        )


    elif weekly_service_exception_flag == 1:

        risk_type = (
            "WEEKLY_SERVICE_RISK"
        )


    elif base_end < safety_end:

        risk_type = (
            "LOW_COVERAGE_RISK"
        )


    elif (

        severe_fill < TARGET_FILL_RATE

        or

        severe_end < safety_end

    ):

        risk_type = (
            "SEVERE_SCENARIO_RISK"
        )


    elif mild_end_wos > EXCESS_WOS_THRESHOLD:

        risk_type = (
            "EXCESS_INVENTORY_RISK"
        )


    else:

        risk_type = (
            "BALANCED"
        )


    asp = float(

        last[
            "planning_net_asp_cad"
        ]

    )


    series_rows.append({

        "min_weekly_base_fill_rate":
            min_weekly_base_fill_rate,

        "worst_base_service_week":
            worst_week,

        "worst_week_service_gap_units":
            worst_week_service_gap_units,

        "weeks_below_service_target":
            weeks_below_service_target,

        "max_consecutive_weeks_below_target":
             max_consecutive_weeks_below_target,

        "weekly_service_exception_flag":
            weekly_service_exception_flag,

        "sku_id":
            sku_id,

        "channel_id":
            channel_id,


        # -----------------------------------
        # Demand
        # -----------------------------------

        "base_13w_demand_units":
            base_demand,

        "mild_13w_demand_units":
            mild_demand,

        "severe_13w_demand_units":
            severe_demand,


        # -----------------------------------
        # Service
        # -----------------------------------

        "base_13w_fill_rate":
            base_fill,

        "mild_13w_fill_rate":
            mild_fill,

        "severe_13w_fill_rate":
            severe_fill,


        "base_service_target_met_flag":
            int(
                base_fill
                >= TARGET_FILL_RATE
            ),


        "severe_service_target_met_flag":
            int(
                severe_fill
                >= TARGET_FILL_RATE
            ),


        # -----------------------------------
        # Lost demand
        # -----------------------------------

        "base_13w_lost_demand_units":
            base_lost,

        "mild_13w_lost_demand_units":
            mild_lost,

        "severe_13w_lost_demand_units":
            severe_lost,


        "base_lost_demand_pct":
            base_lost_pct,

        "severe_lost_demand_pct":
            severe_lost_pct,


        "base_lost_demand_observed_flag":
            int(
                base_lost > 0
            ),


        "severe_lost_demand_observed_flag":
            int(
                severe_lost > 0
            ),


        # -----------------------------------
        # Final inventory
        # -----------------------------------

        "base_final_inventory_units":
            base_end,

        "mild_final_inventory_units":
            mild_end,

        "severe_final_inventory_units":
            severe_end,


        "ending_safety_stock_units":
            safety_end,


        # -----------------------------------
        # Final weeks of supply
        # -----------------------------------

        "base_final_wos":
            base_end_wos,

        "mild_final_wos":
            mild_end_wos,

        "severe_final_wos":
            severe_end_wos,


        # -----------------------------------
        # Excess
        # -----------------------------------

        "base_excess_units":
            base_excess,

        "mild_excess_units":
            mild_excess,

        "severe_excess_units":
            severe_excess,


        # -----------------------------------
        # Gaps
        # -----------------------------------

        "base_safety_gap_units":
            base_safety_gap,

        "severe_safety_gap_units":
            severe_safety_gap,


        "immediate_base_gap_units":
            immediate_base_gap,


        "base_protection_gap_units":
            base_protection_gap,


        "severe_contingency_gap_units":
            severe_contingency_gap,


        # -----------------------------------
        # Risk
        # -----------------------------------

        "risk_type":
            risk_type,


        # -----------------------------------
        # Economics
        # -----------------------------------

        "planning_net_asp_cad":
            asp,


        "base_13w_lost_revenue_opportunity_cad":
            group[
                "base_lost_revenue_opportunity_cad"
            ]
            .sum(),


        "severe_13w_lost_revenue_opportunity_cad":
            group[
                "severe_lost_revenue_opportunity_cad"
            ]
            .sum(),


        "base_13w_carrying_cost_proxy_cad":
            group[
                "base_weekly_carrying_cost_proxy_cad"
            ]
            .sum(),


        "mild_13w_carrying_cost_proxy_cad":
            group[
                "mild_weekly_carrying_cost_proxy_cad"
            ]
            .sum(),


        "base_ending_excess_value_proxy_cad":
            (
                base_excess
                * asp
            ),


        "mild_ending_excess_value_proxy_cad":
            (
                mild_excess
                * asp
            ),


        # -----------------------------------
        # Supply
        # -----------------------------------

        "forward_committed_receipts_13w":
            group[
                "committed_receipt_units"
            ]
            .sum(),


        "forward_seasonal_commitment_units":
            float(

                last[
                    "forward_seasonal_commitment_units"
                ]

            ),


        "chase_capacity_units":
            float(

                last[
                    "chase_capacity_units"
                ]

            ),


        "current_inventory_economic_exposure_cad":
            float(

                last[
                    "current_inventory_economic_exposure_cad"
                ]

            )

            if pd.notna(

                last[
                    "current_inventory_economic_exposure_cad"
                ]

            )

            else np.nan

    })


series_summary = pd.DataFrame(
    series_rows
)


# ============================================================
# 30. INFORMATIONAL SAME-SKU DONOR CAPACITY
# ============================================================

series_summary[
    "same_sku_other_channel_base_excess_units"
] = 0.0


series_summary[
    "same_sku_other_channel_severe_excess_units"
] = 0.0


for idx, row in series_summary.iterrows():

    peers = (

        series_summary[
            (
                series_summary[
                    "sku_id"
                ]
                == row[
                    "sku_id"
                ]
            )

            &

            (
                series_summary[
                    "channel_id"
                ]
                != row[
                    "channel_id"
                ]
            )
        ]

    )


    series_summary.loc[
        idx,
        "same_sku_other_channel_base_excess_units"
    ] = (

        peers[
            "base_excess_units"
        ]
        .sum()

    )


    series_summary.loc[
        idx,
        "same_sku_other_channel_severe_excess_units"
    ] = (

        peers[
            "severe_excess_units"
        ]
        .sum()

    )


# ============================================================
# 31. FINITE SAME-SKU REALLOCATION FUNCTION
#
# Donor units cannot be promised twice.
# ============================================================

def allocate_same_sku_reallocation(
    summary_df,
    gap_column,
    donor_excess_column,
    eligible_risks,
    output_column
):

    summary_df[
        output_column
    ] = 0.0


    for sku_id in sorted(
        summary_df[
            "sku_id"
        ]
        .unique()
    ):

        sku_indices = (

            summary_df[
                summary_df[
                    "sku_id"
                ]
                == sku_id
            ]

            .index

            .tolist()

        )


        donor_remaining = {

            idx:
                max(

                    0.0,

                    float(
                        summary_df.loc[
                            idx,
                            donor_excess_column
                        ]
                    )

                )

            for idx in sku_indices

        }


        receivers = (

            summary_df.loc[
                sku_indices
            ]

            [
                summary_df.loc[
                    sku_indices,
                    "risk_type"
                ]
                .isin(
                    eligible_risks
                )
            ]

            .sort_values(
                gap_column,
                ascending=False
            )

        )


        for receiver_idx, receiver in receivers.iterrows():

            remaining_gap = max(

                0.0,

                float(
                    receiver[
                        gap_column
                    ]
                )

            )


            if remaining_gap <= 0:

                continue


            donor_order = sorted(

                [

                    idx

                    for idx in sku_indices

                    if (

                        idx
                        != receiver_idx

                        and

                        donor_remaining[
                            idx
                        ]
                        > 0

                    )

                ],

                key=lambda idx:
                    donor_remaining[
                        idx
                    ],

                reverse=True

            )


            allocated = 0.0


            for donor_idx in donor_order:

                if remaining_gap <= 0:

                    break


                transfer = min(

                    remaining_gap,

                    donor_remaining[
                        donor_idx
                    ]

                )


                allocated += (
                    transfer
                )


                remaining_gap -= (
                    transfer
                )


                donor_remaining[
                    donor_idx
                ] -= (
                    transfer
                )


            summary_df.loc[
                receiver_idx,
                output_column
            ] = allocated


    return summary_df


# ============================================================
# 32. IMMEDIATE BASE-SERVICE REALLOCATION
#
# ACT NOW only for BASE_SERVICE_RISK.
# ============================================================

series_summary = allocate_same_sku_reallocation(

    summary_df=series_summary,

    gap_column="immediate_base_gap_units",

    donor_excess_column="base_excess_units",

    eligible_risks={
        "BASE_SERVICE_RISK"
    },

    output_column="recommended_reallocation_units"

)


series_summary[
    "base_gap_after_reallocation_units"
] = (

    (

        series_summary[
            "immediate_base_gap_units"
        ]

        -

        series_summary[
            "recommended_reallocation_units"
        ]

    )

    .clip(
        lower=0
    )

)


# ============================================================
# 33. IMMEDIATE CHASE RELEASE
#
# ACT NOW only for BASE_SERVICE_RISK.
#
# LOW_COVERAGE_RISK does NOT automatically release chase.
# ============================================================

series_summary[
    "recommended_chase_release_units"
] = (

    np.where(

        series_summary[
            "risk_type"
        ]
        == "BASE_SERVICE_RISK",

        np.minimum(

            series_summary[
                "base_gap_after_reallocation_units"
            ],

            series_summary[
                "chase_capacity_units"
            ]

        ),

        0.0

    )

)


series_summary[
    "base_uncovered_gap_after_action_units"
] = (

    (

        series_summary[
            "base_gap_after_reallocation_units"
        ]

        -

        series_summary[
            "recommended_chase_release_units"
        ]

    )

    .clip(
        lower=0
    )

)


# ============================================================
# 34. PROTECTION / CONTINGENCY REALLOCATION
#
# Applies to:
#
# LOW_COVERAGE_RISK
# SEVERE_SCENARIO_RISK
#
# These are planning OPTIONS, not immediate moves.
# ============================================================

series_summary = allocate_same_sku_reallocation(

    summary_df=series_summary,

    gap_column="severe_contingency_gap_units",

    donor_excess_column="severe_excess_units",

    eligible_risks={
        "LOW_COVERAGE_RISK",
        "SEVERE_SCENARIO_RISK"
    },

    output_column="contingency_reallocation_option_units"

)


series_summary[
    "contingency_gap_after_reallocation_units"
] = (

    (

        series_summary[
            "severe_contingency_gap_units"
        ]

        -

        series_summary[
            "contingency_reallocation_option_units"
        ]

    )

    .clip(
        lower=0
    )

)


# ============================================================
# 35. CONTINGENCY CHASE OPTION
#
# DO NOT RELEASE YET.
#
# This capacity is retained for:
#
# LOW_COVERAGE_RISK
# SEVERE_SCENARIO_RISK
# ============================================================

series_summary[
    "contingency_chase_option_units"
] = (

    np.where(

        series_summary[
            "risk_type"
        ]
        .isin(
            [
                "LOW_COVERAGE_RISK",
                "SEVERE_SCENARIO_RISK"
            ]
        ),

        np.minimum(

            series_summary[
                "contingency_gap_after_reallocation_units"
            ],

            series_summary[
                "chase_capacity_units"
            ]

        ),

        0.0

    )

)


series_summary[
    "contingency_uncovered_gap_units"
] = (

    np.where(

        series_summary[
            "risk_type"
        ]
        .isin(
            [
                "LOW_COVERAGE_RISK",
                "SEVERE_SCENARIO_RISK"
            ]
        ),

        (

            series_summary[
                "contingency_gap_after_reallocation_units"
            ]

            -

            series_summary[
                "contingency_chase_option_units"
            ]

        )

        .clip(
            lower=0
        ),

        0.0

    )

)


# ============================================================
# 36. FINAL PLANNER ACTION
# ============================================================

def choose_action(row):

    risk = (
        row[
            "risk_type"
        ]
    )


    immediate_reallocation = (
        row[
            "recommended_reallocation_units"
        ]
    )


    immediate_chase = (
        row[
            "recommended_chase_release_units"
        ]
    )


    if risk == "BASE_SERVICE_RISK":

        if (

            immediate_reallocation > 0

            and

            immediate_chase > 0

        ):

            return (
                "REALLOCATE + CHASE"
            )


        if immediate_reallocation > 0:

            return (
                "REALLOCATE"
            )


        if immediate_chase > 0:

            return (
                "CHASE"
            )


        return (
            "PROTECT"
        )


    if risk == "WEEKLY_SERVICE_RISK":

        return (
            "ESCALATE"
        )


    if risk == "LOW_COVERAGE_RISK":

        return (
            "PROTECT"
        )


    if risk == "SEVERE_SCENARIO_RISK":

        return (
            "PROTECT"
        )


    if risk == "EXCESS_INVENTORY_RISK":

        return (
            "REDUCE"
        )


    return (
        "HOLD"
    )


series_summary[
    "planner_action"
] = (

    series_summary.apply(
        choose_action,
        axis=1
    )

)


# ============================================================
# 37. ACTION REASON
# ============================================================

def action_reason(row):

    action = (
        row[
            "planner_action"
        ]
    )


    risk = (
        row[
            "risk_type"
        ]
    )


    if action == "CHASE":

        return (

            "Base-case fill rate is below the governed "
            "service target; release chase capacity now."

        )


    if action == "REALLOCATE":

        return (

            "Base-case service is below target and another "
            "channel for the same SKU has transferable excess."

        )


    if action == "REALLOCATE + CHASE":

        return (

            "Base-case service is below target; reallocate "
            "available same-SKU excess first, then release "
            "chase for the remaining immediate gap."

        )


    if (

        action == "ESCALATE"

        and

        risk == "WEEKLY_SERVICE_RISK"

    ):

        worst_week = pd.to_datetime(
            row["worst_base_service_week"]
        ).strftime("%Y-%m-%d")

        return (

            f"Base 13-week service meets target, but the series "
            f"misses the {TARGET_FILL_RATE:.0%} service target in "
            f"{int(row['weeks_below_service_target'])} forecast weeks. "
            f"Worst week {worst_week} falls to "
            f"{row['min_weekly_base_fill_rate']:.1%} fill with a "
            f"{row['worst_week_service_gap_units']:.1f}-unit gap. "
            f"Escalate for S&OE review and validate receipt timing, "
            f"reallocation and chase feasibility before any release."

        )


    if (

        action == "PROTECT"

        and

        risk == "LOW_COVERAGE_RISK"

    ):

        return (

            "Base-case fill rate meets the governed service "
            "target, but ending inventory is below the 2.5-week "
            "safety-stock policy. Protect inventory and retain "
            "contingency chase capacity; do not release it yet."

        )


    if (

        action == "PROTECT"

        and

        risk == "SEVERE_SCENARIO_RISK"

    ):

        return (

            "Base-case service and coverage are healthy, but "
            "the severe-demand scenario creates service or "
            "coverage risk. Retain contingency options."

        )


    if action == "REDUCE":

        return (

            "Mild-demand scenario leaves more than "
            f"{EXCESS_WOS_THRESHOLD:.0f} weeks of supply; "
            "review commitment, transfer or markdown."

        )


    return (

        "Base service, coverage and scenario exposure remain "
        "within governed planning thresholds."

    )


series_summary[
    "action_reason"
] = (

    series_summary.apply(
        action_reason,
        axis=1
    )

)


# ============================================================
# 38. ACTION FLAGS
# ============================================================

series_summary[
    "chase_release_flag"
] = (

    series_summary[
        "recommended_chase_release_units"
    ]

    .gt(0)

    .astype(int)

)


series_summary[
    "contingency_chase_option_flag"
] = (

    series_summary[
        "contingency_chase_option_units"
    ]

    .gt(0)

    .astype(int)

)


# ============================================================
# 39. PRIORITY TIER
# ============================================================

def priority_tier(row):

    risk = (
        row[
            "risk_type"
        ]
    )


    if risk == "BASE_SERVICE_RISK":

        return "P1"


    if risk == "WEEKLY_SERVICE_RISK":

        return "P1"


    if risk == "LOW_COVERAGE_RISK":

        return "P2"


    if risk == "SEVERE_SCENARIO_RISK":

        return "P2"


    if risk == "EXCESS_INVENTORY_RISK":

        return "P3"


    return "P4"


series_summary[
    "priority_tier"
] = (

    series_summary.apply(
        priority_tier,
        axis=1
    )

)


# ============================================================
# 39A. WEEKLY SERVICE EXCEPTION DIAGNOSTICS
#
# GOVERNED INPUT — persistent weekly misses now feed risk_type.
# ============================================================

weekly_service_diagnostics = (

    series_summary[
        [
            "sku_id",
            "channel_id",
            "base_13w_fill_rate",
            "min_weekly_base_fill_rate",
            "worst_base_service_week",
            "weeks_below_service_target",
            "max_consecutive_weeks_below_target",
            "weekly_service_exception_flag",
            "worst_week_service_gap_units",
            "base_13w_lost_demand_units",
            "risk_type",
            "priority_tier",
            "planner_action"
        ]
    ]

    .sort_values(
        [
            "min_weekly_base_fill_rate",
            "weeks_below_service_target"
        ],
        ascending=[
            True,
            False
        ]
    )

    .copy()

)


for column in [
    "base_13w_fill_rate",
    "min_weekly_base_fill_rate",
    "worst_week_service_gap_units",
    "base_13w_lost_demand_units"
]:

    weekly_service_diagnostics[
        column
    ] = (

        weekly_service_diagnostics[
            column
        ]

        .round(4)

    )


weekly_service_diagnostics[
    "worst_base_service_week"
] = (

    pd.to_datetime(
        weekly_service_diagnostics[
            "worst_base_service_week"
        ]
    )

    .dt.strftime(
        "%Y-%m-%d"
    )

)


print(
    "\n"
    + "=" * 100
)

print(
    "WEEKLY SERVICE EXCEPTION DIAGNOSTICS"
)

print(
    "=" * 100
)

print(
    weekly_service_diagnostics
    .to_string(
        index=False
    )
)


# ============================================================
# 40. DECISION QA
# ============================================================

base_reallocation_capacity_pass = True


contingency_reallocation_capacity_pass = True


for sku_id, group in series_summary.groupby(
    "sku_id"
):

    if (

        group[
            "recommended_reallocation_units"
        ]
        .sum()

        >

        group[
            "base_excess_units"
        ]
        .sum()

        + 1e-8

    ):

        base_reallocation_capacity_pass = False


    if (

        group[
            "contingency_reallocation_option_units"
        ]
        .sum()

        >

        group[
            "severe_excess_units"
        ]
        .sum()

        + 1e-8

    ):

        contingency_reallocation_capacity_pass = False


decision_checks = {

    "Weekly min fill rates within 0-1":
        series_summary[
            "min_weekly_base_fill_rate"
        ]
        .between(
            0,
            1
        )
        .all(),


    "Weekly service gaps non-negative":
        series_summary[
            "worst_week_service_gap_units"
        ]
        .ge(0)
        .all(),


    "Weeks below target within 0-13":
        series_summary[
            "weeks_below_service_target"
        ]
        .between(
            0,
            FORECAST_HORIZON
        )
        .all(),


    "Consecutive miss count valid":
        (
            series_summary[
                "max_consecutive_weeks_below_target"
            ]

            <=

            series_summary[
                "weeks_below_service_target"
            ]
        )
        .all(),


    "Weekly exception flag matches repeated-miss rule":
        (
            series_summary[
                "weekly_service_exception_flag"
            ]
            ==
            (
                series_summary[
                    "weeks_below_service_target"
                ]
                >= WEEKLY_SERVICE_EXCEPTION_WEEKS
            ).astype(int)
        )
        .all(),


    "Exactly 9 series decisions":
        len(series_summary)
        == EXPECTED_SERIES,


    "All planner actions valid":
        set(
            series_summary[
                "planner_action"
            ]
            .unique()
        )
        .issubset(
            VALID_ACTIONS
        ),


    "Immediate reallocation non-negative":
        series_summary[
            "recommended_reallocation_units"
        ]
        .ge(0)
        .all(),


    "Immediate donor capacity not double-counted":
        base_reallocation_capacity_pass,


    "Immediate chase release non-negative":
        series_summary[
            "recommended_chase_release_units"
        ]
        .ge(0)
        .all(),


    "Immediate chase within capacity":
        (
            series_summary[
                "recommended_chase_release_units"
            ]

            <=

            series_summary[
                "chase_capacity_units"
            ]

            + 1e-8
        )
        .all(),


    "Only aggregate BASE_SERVICE_RISK can release immediate chase":
        series_summary.loc[
            series_summary[
                "risk_type"
            ]
            != "BASE_SERVICE_RISK",

            "recommended_chase_release_units"
        ]
        .eq(0)
        .all(),


    "Only aggregate BASE_SERVICE_RISK can trigger immediate reallocation":
        series_summary.loc[
            series_summary[
                "risk_type"
            ]
            != "BASE_SERVICE_RISK",

            "recommended_reallocation_units"
        ]
        .eq(0)
        .all(),


    "Base uncovered action gap non-negative":
        series_summary[
            "base_uncovered_gap_after_action_units"
        ]
        .ge(0)
        .all(),


    "Contingency reallocation non-negative":
        series_summary[
            "contingency_reallocation_option_units"
        ]
        .ge(0)
        .all(),


    "Contingency donor capacity not double-counted":
        contingency_reallocation_capacity_pass,


    "Contingency chase non-negative":
        series_summary[
            "contingency_chase_option_units"
        ]
        .ge(0)
        .all(),


    "Contingency chase within capacity":
        (
            series_summary[
                "contingency_chase_option_units"
            ]

            <=

            series_summary[
                "chase_capacity_units"
            ]

            + 1e-8
        )
        .all(),


    "Only P2 coverage/scenario rows carry contingency chase":
        series_summary.loc[
            ~series_summary[
                "risk_type"
            ]
            .isin(
                [
                    "LOW_COVERAGE_RISK",
                    "SEVERE_SCENARIO_RISK"
                ]
            ),

            "contingency_chase_option_units"
        ]
        .eq(0)
        .all(),


    "Contingency uncovered gap non-negative":
        series_summary[
            "contingency_uncovered_gap_units"
        ]
        .ge(0)
        .all(),


    "Base fill rates within 0-1":
        series_summary[
            "base_13w_fill_rate"
        ]
        .between(
            0,
            1
        )
        .all(),


    "Severe fill rates within 0-1":
        series_summary[
            "severe_13w_fill_rate"
        ]
        .between(
            0,
            1
        )
        .all(),


    "BASE_SERVICE_RISK only below 92%":
        series_summary.loc[
            series_summary[
                "risk_type"
            ]
            == "BASE_SERVICE_RISK",

            "base_13w_fill_rate"
        ]
        .lt(
            TARGET_FILL_RATE
        )
        .all(),


    "WEEKLY_SERVICE_RISK has aggregate base service >=92%":
        series_summary.loc[
            series_summary[
                "risk_type"
            ]
            == "WEEKLY_SERVICE_RISK",

            "base_13w_fill_rate"
        ]
        .ge(
            TARGET_FILL_RATE
        )
        .all(),


    "WEEKLY_SERVICE_RISK meets repeated-miss trigger":
        series_summary.loc[
            series_summary[
                "risk_type"
            ]
            == "WEEKLY_SERVICE_RISK",

            "weeks_below_service_target"
        ]
        .ge(
            WEEKLY_SERVICE_EXCEPTION_WEEKS
        )
        .all(),


    "WEEKLY_SERVICE_RISK has zero automatic chase":
        series_summary.loc[
            series_summary[
                "risk_type"
            ]
            == "WEEKLY_SERVICE_RISK",

            "recommended_chase_release_units"
        ]
        .eq(0)
        .all(),


    "LOW_COVERAGE_RISK has base service >=92%":
        series_summary.loc[
            series_summary[
                "risk_type"
            ]
            == "LOW_COVERAGE_RISK",

            "base_13w_fill_rate"
        ]
        .ge(
            TARGET_FILL_RATE
        )
        .all(),


    "LOW_COVERAGE_RISK is below safety stock":
        (
            series_summary.loc[
                series_summary[
                    "risk_type"
                ]
                == "LOW_COVERAGE_RISK",

                "base_final_inventory_units"
            ]

            <

            series_summary.loc[
                series_summary[
                    "risk_type"
                ]
                == "LOW_COVERAGE_RISK",

                "ending_safety_stock_units"
            ]
        )
        .all(),


    "SEVERE_SCENARIO_RISK has healthy base service":
        series_summary.loc[
            series_summary[
                "risk_type"
            ]
            == "SEVERE_SCENARIO_RISK",

            "base_13w_fill_rate"
        ]
        .ge(
            TARGET_FILL_RATE
        )
        .all(),


    "SEVERE_SCENARIO_RISK has healthy base coverage":
        (
            series_summary.loc[
                series_summary[
                    "risk_type"
                ]
                == "SEVERE_SCENARIO_RISK",

                "base_final_inventory_units"
            ]

            >=

            series_summary.loc[
                series_summary[
                    "risk_type"
                ]
                == "SEVERE_SCENARIO_RISK",

                "ending_safety_stock_units"
            ]
        )
        .all()

}


print(
    "\n"
    + "=" * 100
)

print(
    "IBP DECISION QA"
)

print(
    "=" * 100
)


for name, passed in decision_checks.items():

    print(
        f"{name}:",
        "PASS"
        if passed
        else "FAIL"
    )


if not all(
    decision_checks.values()
):

    raise RuntimeError(
        "Step 5 decision QA failed."
    )


# ============================================================
# 41. MERGE SERIES DECISIONS BACK TO WEEKLY PLAN
# ============================================================

decision_columns = [

    "sku_id",

    "channel_id",


    # Weekly service execution diagnostics
    "min_weekly_base_fill_rate",

    "worst_base_service_week",

    "worst_week_service_gap_units",

    "weeks_below_service_target",

    "max_consecutive_weeks_below_target",

    "weekly_service_exception_flag",


    "priority_tier",

    "risk_type",

    "planner_action",

    "action_reason",


    "base_service_target_met_flag",

    "severe_service_target_met_flag",


    "base_13w_fill_rate",

    "severe_13w_fill_rate",


    "base_13w_lost_demand_units",

    "severe_13w_lost_demand_units",


    "base_lost_demand_pct",

    "severe_lost_demand_pct",


    "base_lost_demand_observed_flag",

    "severe_lost_demand_observed_flag",


    "base_final_inventory_units",

    "mild_final_inventory_units",

    "severe_final_inventory_units",


    "base_final_wos",

    "mild_final_wos",

    "severe_final_wos",


    "base_excess_units",

    "mild_excess_units",

    "severe_excess_units",


    "base_safety_gap_units",

    "severe_safety_gap_units",


    "immediate_base_gap_units",

    "base_protection_gap_units",

    "severe_contingency_gap_units",


    "same_sku_other_channel_base_excess_units",

    "same_sku_other_channel_severe_excess_units",


    "recommended_reallocation_units",

    "recommended_chase_release_units",

    "chase_release_flag",


    "base_uncovered_gap_after_action_units",


    "contingency_reallocation_option_units",

    "contingency_chase_option_units",

    "contingency_chase_option_flag",

    "contingency_uncovered_gap_units",


    "base_13w_lost_revenue_opportunity_cad",

    "severe_13w_lost_revenue_opportunity_cad",


    "base_13w_carrying_cost_proxy_cad",

    "mild_13w_carrying_cost_proxy_cad",


    "base_ending_excess_value_proxy_cad",

    "mild_ending_excess_value_proxy_cad"

]


output = (

    plan

    .merge(

        series_summary[
            decision_columns
        ],

        on=[
            "sku_id",
            "channel_id"
        ],

        how="left",

        validate="many_to_one"

    )

)


# ============================================================
# 42. GOVERNANCE / PROVENANCE FIELDS
# ============================================================

output[
    "service_target_fill_rate"
] = TARGET_FILL_RATE


output[
    "safety_stock_policy_weeks"
] = SAFETY_STOCK_WEEKS


output[
    "chase_capacity_share"
] = CHASE_CAPACITY_SHARE


output[
    "annual_carrying_cost_rate"
] = ANNUAL_CARRYING_COST_RATE


output[
    "receipt_projection_method"
] = (
    "PRIOR_YEAR_SEASONAL_RECEIPTS_SHIFTED_52W_PLUS_FROZEN_SKU_GROWTH"
)


output[
    "receipt_source_method"
] = receipt_method


output[
    "inventory_decision_provenance"
] = (
    "DERIVED_IBP_DECISION_LAYER"
)


output[
    "economic_value_basis"
] = (
    "NET_REVENUE_INVENTORY_EXPOSURE_PROXY_NOT_ACCOUNTING_PROFIT"
)


output[
    "demand_forecast_status"
] = (
    "FROZEN_STEP4D"
)


output[
    "weather_framework_status"
] = (
    "FROZEN_STEP4C"
)


output[
    "risk_hierarchy_governance"
] = (
    "BASE_SERVICE_THEN_PERSISTENT_WEEKLY_SERVICE_THEN_BASE_COVERAGE_THEN_SEVERE_SCENARIO_THEN_EXCESS"
)


output[
    "chase_governance"
] = (
    "IMMEDIATE_RELEASE_ONLY_FOR_AGGREGATE_BASE_SERVICE_RISK_WEEKLY_SERVICE_RISK_REQUIRES_SOE_REVIEW"
)


output[
    "coverage_governance"
] = (
    "LOW_COVERAGE_PROTECTS_INVENTORY_WITHOUT_AUTOMATIC_CHASE_RELEASE"
)


output[
    "weekly_service_governance"
] = (
    "SYNTHETIC_PLANNING_GOVERNANCE_2PLUS_FORECAST_WEEKS_BELOW_92PCT_ESCALATES_TO_P1_NO_AUTOMATIC_CHASE"
)


output[
    "contingency_governance"
] = (
    "P2_CHASE_AND_REALLOCATION_OPTIONS_ARE_NOT_RELEASED"
)


# ============================================================
# 43. FINAL STRUCTURAL QA
# ============================================================

final_checks = {

    "Output rows = 117":
        len(output)
        == EXPECTED_ROWS,


    "Output grain unique":
        output
        .duplicated(
            subset=[
                "forecast_week_start",
                "sku_id",
                "channel_id"
            ]
        )
        .sum()
        == 0,


    "Exactly 9 forecasting series":
        output[
            [
                "sku_id",
                "channel_id"
            ]
        ]
        .drop_duplicates()
        .shape[0]
        == EXPECTED_SERIES,


    "13 forecast weeks":
        output[
            "forecast_week_start"
        ]
        .nunique()
        == FORECAST_HORIZON,


    "No missing planner actions":
        output[
            "planner_action"
        ]
        .notna()
        .all(),


    "No negative committed receipts":
        output[
            "committed_receipt_units"
        ]
        .ge(0)
        .all(),


    "No negative base ending inventory":
        output[
            "base_ending_inventory_units"
        ]
        .ge(0)
        .all(),


    "No negative mild ending inventory":
        output[
            "mild_ending_inventory_units"
        ]
        .ge(0)
        .all(),


    "No negative severe ending inventory":
        output[
            "severe_ending_inventory_units"
        ]
        .ge(0)
        .all(),


    "No forbidden historical truth fields used":
        leakage_pass

}


overall_pass = (

    all(
        forecast_checks.values()
    )

    and

    all(
        flow_checks.values()
    )

    and

    all(
        decision_checks.values()
    )

    and

    all(
        final_checks.values()
    )

)


print(
    "\n"
    + "=" * 100
)

print(
    "FINAL STEP 5 QA"
)

print(
    "=" * 100
)


for name, passed in final_checks.items():

    print(
        f"{name}:",
        "PASS"
        if passed
        else "FAIL"
    )


# ============================================================
# 44. PLANNER DECISION QUEUE
# ============================================================

decision_queue = (

    series_summary

    .sort_values(

        [
            "priority_tier",

            "immediate_base_gap_units",

            "base_protection_gap_units",

            "severe_contingency_gap_units"
        ],

        ascending=[
            True,
            False,
            False,
            False
        ]

    )

    [
        [
            "priority_tier",

            "sku_id",

            "channel_id",

            "risk_type",

            "planner_action",


            "base_13w_fill_rate",

            "severe_13w_fill_rate",

            "base_service_target_met_flag",


            "base_final_wos",

            "severe_final_wos",


            "base_13w_lost_demand_units",


            "base_safety_gap_units",

            "immediate_base_gap_units",

            "base_protection_gap_units",


            "recommended_reallocation_units",

            "recommended_chase_release_units",

            "base_uncovered_gap_after_action_units",


            "severe_contingency_gap_units",

            "contingency_reallocation_option_units",

            "contingency_chase_option_units",

            "contingency_uncovered_gap_units",


            "base_13w_lost_revenue_opportunity_cad",

            "severe_13w_lost_revenue_opportunity_cad",


            "action_reason"
        ]
    ]

    .copy()

)


numeric_display = [

    "base_13w_fill_rate",

    "severe_13w_fill_rate",

    "base_final_wos",

    "severe_final_wos",

    "base_13w_lost_demand_units",

    "base_safety_gap_units",

    "immediate_base_gap_units",

    "base_protection_gap_units",

    "recommended_reallocation_units",

    "recommended_chase_release_units",

    "base_uncovered_gap_after_action_units",

    "severe_contingency_gap_units",

    "contingency_reallocation_option_units",

    "contingency_chase_option_units",

    "contingency_uncovered_gap_units",

    "base_13w_lost_revenue_opportunity_cad",

    "severe_13w_lost_revenue_opportunity_cad"

]


decision_queue[
    numeric_display
] = (

    decision_queue[
        numeric_display
    ]

    .round(2)

)


print(
    "\n"
    + "=" * 100
)

print(
    "PLANNER DECISION QUEUE"
)

print(
    "=" * 100
)


print(
    decision_queue
    .to_string(
        index=False
    )
)


# ============================================================
# 45. PORTFOLIO IBP OUTLOOK
# ============================================================

portfolio_base_demand = (

    plan[
        "base_forecast_units"
    ]
    .sum()

)


portfolio_base_ship = (

    plan[
        "base_shipped_units"
    ]
    .sum()

)


portfolio_severe_demand = (

    plan[
        "severe_scenario_forecast_units"
    ]
    .sum()

)


portfolio_severe_ship = (

    plan[
        "severe_shipped_units"
    ]
    .sum()

)


portfolio_base_fill = (

    portfolio_base_ship

    / portfolio_base_demand

)


portfolio_severe_fill = (

    portfolio_severe_ship

    / portfolio_severe_demand

)


actual_reallocation = (

    series_summary[
        "recommended_reallocation_units"
    ]
    .sum()

)


actual_chase_release = (

    series_summary[
        "recommended_chase_release_units"
    ]
    .sum()

)


base_uncovered_gap = (

    series_summary[
        "base_uncovered_gap_after_action_units"
    ]
    .sum()

)


base_protection_gap = (

    series_summary[
        "base_protection_gap_units"
    ]
    .sum()

)


contingency_reallocation = (

    series_summary[
        "contingency_reallocation_option_units"
    ]
    .sum()

)


contingency_chase = (

    series_summary[
        "contingency_chase_option_units"
    ]
    .sum()

)


contingency_uncovered = (

    series_summary[
        "contingency_uncovered_gap_units"
    ]
    .sum()

)


print(
    "\n"
    + "=" * 100
)

print(
    "PORTFOLIO 13-WEEK IBP OUTLOOK"
)

print(
    "=" * 100
)


print(
    f"Base demand:                     "
    f"{portfolio_base_demand:,.2f} units"
)


print(
    f"Base projected shipments:        "
    f"{portfolio_base_ship:,.2f} units"
)


print(
    f"Base projected fill rate:        "
    f"{portfolio_base_fill:.2%}"
)


print(
    f"Governed service target:         "
    f"{TARGET_FILL_RATE:.2%}"
)


print(
    f"Severe demand:                   "
    f"{portfolio_severe_demand:,.2f} units"
)


print(
    f"Severe projected fill rate:      "
    f"{portfolio_severe_fill:.2%}"
)


print(
    f"Committed receipts in 13W:       "
    f"{plan['committed_receipt_units'].sum():,.2f}"
)


print(
    f"Total available chase capacity:  "
    f"{series_summary['chase_capacity_units'].sum():,.2f}"
)


print(
    "\n--- ACT NOW / SERVICE FAILURE ---"
)


print(
    f"Recommended reallocation now:    "
    f"{actual_reallocation:,.2f} units"
)


print(
    f"Recommended chase RELEASE now:   "
    f"{actual_chase_release:,.2f} units"
)


print(
    f"Base uncovered service gap:      "
    f"{base_uncovered_gap:,.2f} units"
)


print(
    "\n--- PROTECT / BASE COVERAGE ---"
)


print(
    f"Base safety-stock protection gap:"
    f" {base_protection_gap:,.2f} units"
)


print(
    "This is a buffer shortfall, not an automatic "
    "procurement release."
)


print(
    "\n--- CONTINGENCY / DO NOT RELEASE YET ---"
)


print(
    f"Contingency reallocation option: "
    f"{contingency_reallocation:,.2f} units"
)


print(
    f"Contingency chase option:        "
    f"{contingency_chase:,.2f} units"
)


print(
    f"Contingency uncovered gap:       "
    f"{contingency_uncovered:,.2f} units"
)


print(
    "\n--- ECONOMIC EXPOSURE ---"
)


print(
    f"Base lost revenue exposure:      "
    f"${series_summary['base_13w_lost_revenue_opportunity_cad'].sum():,.2f}"
)


print(
    f"Severe lost revenue exposure:    "
    f"${series_summary['severe_13w_lost_revenue_opportunity_cad'].sum():,.2f}"
)


print(
    f"13W base carrying cost proxy:    "
    f"${series_summary['base_13w_carrying_cost_proxy_cad'].sum():,.2f}"
)


# ============================================================
# 46. ACTION / RISK COUNTS
# ============================================================

print(
    "\n"
    + "=" * 100
)

print(
    "PLANNER ACTION COUNTS"
)

print(
    "=" * 100
)


print(

    series_summary[
        "planner_action"
    ]

    .value_counts()

    .to_string()

)


print(
    "\n"
    + "=" * 100
)

print(
    "RISK TYPE COUNTS"
)

print(
    "=" * 100
)


print(

    series_summary[
        "risk_type"
    ]

    .value_counts()

    .to_string()

)


# ============================================================
# 47. RISK HIERARCHY VALIDATION TABLE
# ============================================================

validation_table = (

    series_summary[
        [
            "sku_id",

            "channel_id",

            "base_13w_fill_rate",

            "base_final_inventory_units",

            "ending_safety_stock_units",

            "base_final_wos",

            "severe_final_wos",

            "risk_type",

            "planner_action"
        ]
    ]

    .copy()

)


validation_table[
    "base_below_safety_stock_flag"
] = (

    validation_table[
        "base_final_inventory_units"
    ]

    <

    validation_table[
        "ending_safety_stock_units"
    ]

).astype(int)


print(
    "\n"
    + "=" * 100
)

print(
    "RISK HIERARCHY VALIDATION"
)

print(
    "=" * 100
)


validation_table[
    [
        "base_13w_fill_rate",

        "base_final_inventory_units",

        "ending_safety_stock_units",

        "base_final_wos",

        "severe_final_wos"
    ]
] = (

    validation_table[
        [
            "base_13w_fill_rate",

            "base_final_inventory_units",

            "ending_safety_stock_units",

            "base_final_wos",

            "severe_final_wos"
        ]
    ]

    .round(2)

)


print(
    validation_table
    .to_string(
        index=False
    )
)


# ============================================================
# 48. SAVE FINAL STEP 5 OUTPUT
# ============================================================

if overall_pass:

    output = (

        output

        .sort_values(
            [
                "forecast_week_start",

                "sku_id",

                "channel_id"
            ]
        )

        .copy()

    )


    round_columns = [

        column

        for column in output.columns

        if output[
            column
        ].dtype.kind in "fc"

    ]


    for column in round_columns:

        output[
            column
        ] = (

            output[
                column
            ]

            .round(3)

        )


    output[
        "forecast_week_start"
    ] = (

        pd.to_datetime(
            output[
                "forecast_week_start"
            ]
        )

        .dt.strftime(
            "%Y-%m-%d"
        )

    )


    if "forecast_origin" in output.columns:

        output[
            "forecast_origin"
        ] = (

            pd.to_datetime(
                output[
                    "forecast_origin"
                ]
            )

            .dt.strftime(
                "%Y-%m-%d"
            )

        )


    output.to_csv(

        OUTPUT_FILE,

        index=False

    )


    print(
        "\n"
        + "=" * 100
    )

    print(
        "STEP 5 COMPLETE"
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
        "STEP 5 FAILED QA"
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
        "Step 5 final IBP decision engine failed QA."
    )


# ============================================================
# END STEP 5
# ============================================================