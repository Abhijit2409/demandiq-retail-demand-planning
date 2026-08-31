import pandas as pd
from pathlib import Path


# ============================================================
# DEMANDIQ
# STEP 4B.6 — FINAL CHAMPION MODEL SELECTION
#
# Purpose:
# Consolidate full 12-fold forecasting evidence and select
# one governed champion model for each SKU × Channel series.
#
# Eligible evidence:
#   1. Baselines — full 12 folds
#   2. ETS       — full 12 folds
#   3. SARIMA    — full 12 folds ONLY for targeted series
#
# IMPORTANT:
# The 4-fold SARIMA screen is NOT eligible for final
# champion selection.
#
# Champion philosophy:
# Accuracy + Bias + Stability + Robustness + Simplicity
#
# Raw WAPE winner is preserved separately from the final
# governed champion so overrides remain transparent.
# ============================================================


# ------------------------------------------------------------
# 1. PROJECT ROOT
# ------------------------------------------------------------

PROJECT_DIR = Path(r"D:\Downloads\DemandIQ")


# ------------------------------------------------------------
# 2. ORGANIZED MODEL-EVIDENCE PATHS
# ------------------------------------------------------------

BASELINE_FILE = (
    PROJECT_DIR
    / "03_model_evidence"
    / "step4b_forecasting"
    / "baseline"
    / "DemandIQ_Step4B_Baseline_Summary.csv"
)


ETS_FILE = (
    PROJECT_DIR
    / "03_model_evidence"
    / "step4b_forecasting"
    / "ets"
    / "DemandIQ_Step4B_ETS_Summary.csv"
)


SARIMA_FILE = (
    PROJECT_DIR
    / "03_model_evidence"
    / "step4b_forecasting"
    / "sarima"
    / "targeted"
    / "DemandIQ_Step4B_SARIMA_Targeted_Summary.csv"
)


# ------------------------------------------------------------
# 3. FINAL OUTPUT DIRECTORY
# ------------------------------------------------------------

OUTPUT_DIR = (
    PROJECT_DIR
    / "05_outputs"
    / "champion_selection"
)


OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


CHAMPION_OUTPUT_FILE = (
    OUTPUT_DIR
    / "DemandIQ_Step4B_Champion_Selection.csv"
)


CANDIDATE_OUTPUT_FILE = (
    OUTPUT_DIR
    / "DemandIQ_Step4B_Full12Fold_Candidate_Evidence.csv"
)


# ------------------------------------------------------------
# 4. FILE PATH QA
#
# Check paths BEFORE attempting pd.read_csv().
# ------------------------------------------------------------

print("\n" + "=" * 88)
print("FILE PATH QA")
print("=" * 88)


source_files = {
    "Baseline summary": BASELINE_FILE,
    "ETS summary": ETS_FILE,
    "Targeted SARIMA summary": SARIMA_FILE
}


all_source_files_found = True


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
        all_source_files_found = False


if not all_source_files_found:

    raise FileNotFoundError(
        "\nOne or more model-summary files were not found.\n"
        "Check the paths printed above before continuing."
    )


# ------------------------------------------------------------
# 5. GOVERNANCE CONSTANTS
# ------------------------------------------------------------

EXPECTED_SERIES = 9

EXPECTED_FOLDS = 12

FORECAST_HORIZON_WEEKS = 13


# ------------------------------------------------------------
# Model-family complexity hierarchy
#
# Descriptive only.
# We are NOT generating a weighted complexity score.
# ------------------------------------------------------------

COMPLEXITY_RANK = {

    "BASELINE": 1,

    "ETS": 2,

    "SARIMA": 3

}


# ------------------------------------------------------------
# 6. EXPLICIT GOVERNANCE OVERRIDE
#
# IMH-001 / ECOM:
#
# Full 12-fold results:
#
# SARIMA WAPE        ≈ 8.62%
# HW_Damped_Mul WAPE ≈ 8.68%
#
# Difference ≈ 0.06 percentage points.
#
# The statistical improvement is operationally negligible.
# ETS is retained because it is simpler, faster and easier
# to maintain while providing essentially equivalent accuracy.
#
# This override is explicit rather than hidden in a score.
# ------------------------------------------------------------

GOVERNANCE_OVERRIDES = {

    ("IMH-001", "ECOM"): {

        "selected_model":
            "HW_Damped_Mul",

        "reason":
            (
                "SARIMA was the raw WAPE winner, but its "
                "full 12-fold improvement versus "
                "HW_Damped_Mul was only about 0.06 percentage "
                "points. HW_Damped_Mul was retained because "
                "the accuracy difference was operationally "
                "negligible while ETS is simpler, faster, "
                "and easier to maintain."
            )

    }

}


# ------------------------------------------------------------
# 7. LOAD MODEL SUMMARIES
# ------------------------------------------------------------

baseline_df = pd.read_csv(
    BASELINE_FILE
)

ets_df = pd.read_csv(
    ETS_FILE
)

sarima_df = pd.read_csv(
    SARIMA_FILE
)


print("\n" + "=" * 88)
print("STEP 4B.6 — FINAL CHAMPION MODEL SELECTION")
print("=" * 88)


print(
    "Baseline summary shape:",
    baseline_df.shape
)

print(
    "ETS summary shape:",
    ets_df.shape
)

print(
    "Targeted SARIMA summary shape:",
    sarima_df.shape
)


# ------------------------------------------------------------
# 8. REQUIRED MODEL-SUMMARY COLUMNS
# ------------------------------------------------------------

REQUIRED_COLUMNS = {

    "sku_id",
    "channel_id",
    "model",

    "pooled_wape_pct",
    "pooled_bias_pct",
    "pooled_mae_units",

    "mean_fold_wape_pct",
    "median_fold_wape_pct",
    "std_fold_wape_pct",
    "worst_fold_wape_pct",

    "folds_evaluated"

}


def validate_summary_schema(
    dataframe,
    name
):

    missing_columns = (
        REQUIRED_COLUMNS
        - set(dataframe.columns)
    )


    schema_pass = (
        len(missing_columns)
        == 0
    )


    print(
        f"{name} required columns:",
        "PASS" if schema_pass else "FAIL"
    )


    if not schema_pass:

        print(
            f"Missing columns in {name}:",
            sorted(
                missing_columns
            )
        )


        raise ValueError(
            f"{name} summary schema is incomplete."
        )


# ------------------------------------------------------------
# 9. SOURCE SCHEMA QA
# ------------------------------------------------------------

print("\n" + "=" * 88)
print("SOURCE SCHEMA QA")
print("=" * 88)


validate_summary_schema(
    baseline_df,
    "BASELINE"
)


validate_summary_schema(
    ets_df,
    "ETS"
)


validate_summary_schema(
    sarima_df,
    "SARIMA"
)


# ------------------------------------------------------------
# 10. STANDARDIZE MODEL EVIDENCE
# ------------------------------------------------------------

KEEP_COLUMNS = [

    "sku_id",
    "channel_id",
    "model",

    "pooled_wape_pct",
    "pooled_bias_pct",
    "pooled_mae_units",

    "mean_fold_wape_pct",
    "median_fold_wape_pct",
    "std_fold_wape_pct",
    "worst_fold_wape_pct",

    "folds_evaluated"

]


baseline_candidates = (
    baseline_df[
        KEEP_COLUMNS
    ]
    .copy()
)


baseline_candidates[
    "model_family"
] = "BASELINE"


ets_candidates = (
    ets_df[
        KEEP_COLUMNS
    ]
    .copy()
)


ets_candidates[
    "model_family"
] = "ETS"


sarima_candidates = (
    sarima_df[
        KEEP_COLUMNS
    ]
    .copy()
)


sarima_candidates[
    "model_family"
] = "SARIMA"


# ------------------------------------------------------------
# 11. COMBINE ALL FULL-12-FOLD EVIDENCE
# ------------------------------------------------------------

candidate_df = pd.concat(

    [
        baseline_candidates,
        ets_candidates,
        sarima_candidates
    ],

    ignore_index=True

)


candidate_df[
    "evaluation_scope"
] = "FULL_12_FOLD"


candidate_df[
    "forecast_horizon_weeks"
] = FORECAST_HORIZON_WEEKS


candidate_df[
    "complexity_rank"
] = (
    candidate_df[
        "model_family"
    ]
    .map(
        COMPLEXITY_RANK
    )
)


# ------------------------------------------------------------
# 12. ELIGIBILITY QA
#
# Every final candidate must have full 12-fold evidence.
# ------------------------------------------------------------

candidate_df[
    "champion_eligible"
] = (
    candidate_df[
        "folds_evaluated"
    ]
    .eq(
        EXPECTED_FOLDS
    )
)


ineligible_rows = (
    ~candidate_df[
        "champion_eligible"
    ]
).sum()


eligibility_pass = (
    ineligible_rows == 0
)


print("\n" + "=" * 88)
print("ELIGIBILITY QA")
print("=" * 88)


print(
    "Total candidate evidence rows:",
    len(candidate_df)
)


print(
    "Candidates with fewer than 12 folds:",
    ineligible_rows
)


print(
    "All candidates full-12-fold eligible:",
    "PASS"
    if eligibility_pass
    else "FAIL"
)


if not eligibility_pass:

    print(
        "\nIneligible rows:"
    )

    print(
        candidate_df[
            ~candidate_df[
                "champion_eligible"
            ]
        ]
        .to_string(
            index=False
        )
    )


    raise ValueError(
        "Ineligible model evidence detected."
    )


# ------------------------------------------------------------
# 13. METRIC QA
# ------------------------------------------------------------

METRIC_COLUMNS = [

    "pooled_wape_pct",
    "pooled_bias_pct",
    "pooled_mae_units",

    "mean_fold_wape_pct",
    "median_fold_wape_pct",
    "std_fold_wape_pct",
    "worst_fold_wape_pct"

]


null_metric_count = (

    candidate_df[
        METRIC_COLUMNS
    ]

    .isna()

    .sum()

    .sum()

)


null_metric_pass = (
    null_metric_count == 0
)


negative_wape_count = (
    candidate_df[
        "pooled_wape_pct"
    ]
    .lt(0)
    .sum()
)


wape_pass = (
    negative_wape_count == 0
)


duplicate_candidate_rows = (

    candidate_df

    .duplicated(

        subset=[
            "sku_id",
            "channel_id",
            "model"
        ]

    )

    .sum()

)


candidate_grain_pass = (
    duplicate_candidate_rows == 0
)


print("\n" + "=" * 88)
print("MODEL METRIC QA")
print("=" * 88)


print(
    "Missing metric values:",
    null_metric_count
)


print(
    "Metric completeness:",
    "PASS"
    if null_metric_pass
    else "FAIL"
)


print(
    "Negative WAPE values:",
    negative_wape_count
)


print(
    "WAPE validity:",
    "PASS"
    if wape_pass
    else "FAIL"
)


print(
    "Duplicate candidate model rows:",
    duplicate_candidate_rows
)


print(
    "Candidate model grain:",
    "PASS"
    if candidate_grain_pass
    else "FAIL"
)


# ------------------------------------------------------------
# 14. RAW MODEL RANKING
#
# First rank models statistically by pooled WAPE.
#
# If two models have identical WAPE, lower complexity wins
# the secondary sort.
# ------------------------------------------------------------

candidate_df = (

    candidate_df

    .sort_values(

        [
            "sku_id",
            "channel_id",
            "pooled_wape_pct",
            "complexity_rank"
        ]

    )

    .reset_index(
        drop=True
    )

)


candidate_df[
    "wape_rank"
] = (

    candidate_df

    .groupby(
        [
            "sku_id",
            "channel_id"
        ]
    )

    .cumcount()

    + 1

)


candidate_df[
    "absolute_bias_pct"
] = (

    candidate_df[
        "pooled_bias_pct"
    ]

    .abs()

)


# ------------------------------------------------------------
# 15. BUILD FINAL 9-ROW CHAMPION TABLE
# ------------------------------------------------------------

champion_rows = []


for (
    sku,
    channel
), group in candidate_df.groupby(
    [
        "sku_id",
        "channel_id"
    ]
):


    group = (

        group

        .sort_values(

            [
                "pooled_wape_pct",
                "complexity_rank"
            ]

        )

        .reset_index(
            drop=True
        )

    )


    # --------------------------------------------------------
    # Raw statistical WAPE winner
    # --------------------------------------------------------

    raw_winner = (
        group.iloc[0]
    )


    # --------------------------------------------------------
    # Statistical runner-up
    # --------------------------------------------------------

    runner_up = (
        group.iloc[1]
    )


    raw_winner_advantage_pp = (

        runner_up[
            "pooled_wape_pct"
        ]

        -

        raw_winner[
            "pooled_wape_pct"
        ]

    )


    # --------------------------------------------------------
    # Default:
    # final champion = raw statistical winner
    # --------------------------------------------------------

    selected_model = (
        raw_winner[
            "model"
        ]
    )


    governance_override_flag = "NO"


    selection_reason = (

        "Selected as the strongest eligible full 12-fold "
        "candidate based on pooled WAPE, with acceptable "
        "bias and fold stability."

    )


    # --------------------------------------------------------
    # Apply explicit governance override
    # --------------------------------------------------------

    override_key = (
        sku,
        channel
    )


    if (
        override_key
        in GOVERNANCE_OVERRIDES
    ):


        override = (
            GOVERNANCE_OVERRIDES[
                override_key
            ]
        )


        selected_model = (
            override[
                "selected_model"
            ]
        )


        governance_override_flag = "YES"


        selection_reason = (
            override[
                "reason"
            ]
        )


    # --------------------------------------------------------
    # Retrieve selected model evidence
    # --------------------------------------------------------

    selected_rows = (

        group[

            group[
                "model"
            ]

            ==

            selected_model

        ]

    )


    if len(
        selected_rows
    ) != 1:

        raise ValueError(

            f"Selected champion model not uniquely found: "
            f"{sku} | "
            f"{channel} | "
            f"{selected_model}"

        )


    selected = (
        selected_rows.iloc[0]
    )


    # --------------------------------------------------------
    # WAPE cost of governance override
    #
    # 0 if raw winner is retained.
    # Positive if we knowingly selected a slightly worse
    # statistical model for governance reasons.
    # --------------------------------------------------------

    selected_minus_raw_winner_pp = (

        selected[
            "pooled_wape_pct"
        ]

        -

        raw_winner[
            "pooled_wape_pct"
        ]

    )


    # --------------------------------------------------------
    # Bias review flag
    #
    # Frozen governance threshold:
    # |Bias| > 10% requires review.
    # --------------------------------------------------------

    bias_review_flag = (

        "YES"

        if abs(
            selected[
                "pooled_bias_pct"
            ]
        ) > 10

        else "NO"

    )


    # --------------------------------------------------------
    # Final champion row
    # --------------------------------------------------------

    champion_rows.append(

        {

            "sku_id":
                sku,

            "channel_id":
                channel,


            # -----------------------------
            # Raw statistical winner
            # -----------------------------

            "raw_wape_winner":
                raw_winner[
                    "model"
                ],

            "raw_winner_family":
                raw_winner[
                    "model_family"
                ],

            "raw_winner_wape_pct":
                raw_winner[
                    "pooled_wape_pct"
                ],

            "raw_winner_bias_pct":
                raw_winner[
                    "pooled_bias_pct"
                ],


            # -----------------------------
            # Final governed champion
            # -----------------------------

            "selected_champion":
                selected[
                    "model"
                ],

            "selected_family":
                selected[
                    "model_family"
                ],

            "champion_wape_pct":
                selected[
                    "pooled_wape_pct"
                ],

            "champion_bias_pct":
                selected[
                    "pooled_bias_pct"
                ],

            "champion_mae_units":
                selected[
                    "pooled_mae_units"
                ],

            "champion_mean_fold_wape_pct":
                selected[
                    "mean_fold_wape_pct"
                ],

            "champion_median_fold_wape_pct":
                selected[
                    "median_fold_wape_pct"
                ],

            "champion_std_fold_wape_pct":
                selected[
                    "std_fold_wape_pct"
                ],

            "champion_worst_fold_wape_pct":
                selected[
                    "worst_fold_wape_pct"
                ],


            # -----------------------------
            # Runner-up
            # -----------------------------

            "runner_up_model":
                runner_up[
                    "model"
                ],

            "runner_up_family":
                runner_up[
                    "model_family"
                ],

            "runner_up_wape_pct":
                runner_up[
                    "pooled_wape_pct"
                ],

            "raw_winner_advantage_pp":
                raw_winner_advantage_pp,


            # -----------------------------
            # Governance
            # -----------------------------

            "governance_override_flag":
                governance_override_flag,

            "selected_minus_raw_winner_pp":
                selected_minus_raw_winner_pp,

            "bias_review_flag":
                bias_review_flag,

            "selection_reason":
                selection_reason,


            # -----------------------------
            # Evaluation design
            # -----------------------------

            "evaluation_folds":
                EXPECTED_FOLDS,

            "forecast_horizon_weeks":
                FORECAST_HORIZON_WEEKS,

            "evaluation_scope":
                "FULL_12_FOLD"

        }

    )


champion_df = pd.DataFrame(
    champion_rows
)


# ------------------------------------------------------------
# 16. FINAL CHAMPION QA
# ------------------------------------------------------------

row_count_pass = (
    len(
        champion_df
    )
    == EXPECTED_SERIES
)


unique_series_count = (

    champion_df[

        [
            "sku_id",
            "channel_id"
        ]

    ]

    .drop_duplicates()

    .shape[0]

)


unique_series_pass = (
    unique_series_count
    == EXPECTED_SERIES
)


missing_champion_count = (

    champion_df[
        "selected_champion"
    ]

    .isna()

    .sum()

)


champion_complete_pass = (
    missing_champion_count == 0
)


fold_scope_pass = (

    champion_df[
        "evaluation_folds"
    ]

    .eq(
        EXPECTED_FOLDS
    )

    .all()

)


# ------------------------------------------------------------
# Verify every selected champion exists in full-12-fold
# candidate evidence.
# ------------------------------------------------------------

champion_evidence_pass = True


for _, row in champion_df.iterrows():


    matching_evidence = (

        candidate_df[

            (
                candidate_df[
                    "sku_id"
                ]
                ==
                row[
                    "sku_id"
                ]
            )

            &

            (
                candidate_df[
                    "channel_id"
                ]
                ==
                row[
                    "channel_id"
                ]
            )

            &

            (
                candidate_df[
                    "model"
                ]
                ==
                row[
                    "selected_champion"
                ]
            )

            &

            (
                candidate_df[
                    "champion_eligible"
                ]
            )

        ]

    )


    if len(
        matching_evidence
    ) != 1:


        champion_evidence_pass = False


        print(
            "Champion evidence problem:",
            row[
                "sku_id"
            ],
            row[
                "channel_id"
            ],
            row[
                "selected_champion"
            ]
        )


# ------------------------------------------------------------
# 17. CHAMPION FAMILY COUNTS
# ------------------------------------------------------------

family_counts = (

    champion_df[
        "selected_family"
    ]

    .value_counts()

)


override_count = (

    champion_df[
        "governance_override_flag"
    ]

    .eq(
        "YES"
    )

    .sum()

)


# ------------------------------------------------------------
# Expected validated result:
#
# ETS      = 8
# BASELINE = 1
# SARIMA   = 0
#
# This does NOT create the champions.
# It is only a final reconciliation check against our
# previously reviewed model decisions.
# ------------------------------------------------------------

expected_ets_count = (

    family_counts.get(
        "ETS",
        0
    )

    ==

    8

)


expected_baseline_count = (

    family_counts.get(
        "BASELINE",
        0
    )

    ==

    1

)


expected_sarima_count = (

    family_counts.get(
        "SARIMA",
        0
    )

    ==

    0

)


family_shape_pass = all(

    [
        expected_ets_count,
        expected_baseline_count,
        expected_sarima_count
    ]

)


# ------------------------------------------------------------
# 18. OVERALL QA
# ------------------------------------------------------------

all_checks_pass = all(

    [

        eligibility_pass,
        null_metric_pass,
        wape_pass,
        candidate_grain_pass,

        row_count_pass,
        unique_series_pass,
        champion_complete_pass,
        fold_scope_pass,
        champion_evidence_pass,

        family_shape_pass

    ]

)


print("\n" + "=" * 88)
print("FINAL STEP 4B.6 QA")
print("=" * 88)


qa_results = {

    "All candidate models have 12-fold evidence":
        eligibility_pass,

    "No missing model metrics":
        null_metric_pass,

    "No invalid WAPE values":
        wape_pass,

    "Candidate model grain unique":
        candidate_grain_pass,

    "Exactly 9 champion rows":
        row_count_pass,

    "Exactly 9 unique SKU × Channel series":
        unique_series_pass,

    "No missing champions":
        champion_complete_pass,

    "All champions use full 12-fold evidence":
        fold_scope_pass,

    "Every champion traceable to model evidence":
        champion_evidence_pass,

    "Expected champion-family mix":
        family_shape_pass

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


print(
    "\nGovernance overrides:",
    override_count
)


print(
    "\nChampion family counts:"
)


print(
    family_counts
)


print("\n" + "-" * 88)


if all_checks_pass:


    print(

        "OVERALL STATUS: PASS — "
        "Final champion-selection table is valid."

    )


else:


    print(

        "OVERALL STATUS: FAIL — "
        "Do not freeze champion selection."

    )


print("-" * 88)


# ------------------------------------------------------------
# 19. DISPLAY FINAL CHAMPION TABLE
# ------------------------------------------------------------

DISPLAY_COLUMNS = [

    "sku_id",
    "channel_id",

    "raw_wape_winner",
    "raw_winner_wape_pct",

    "selected_champion",
    "selected_family",

    "champion_wape_pct",
    "champion_bias_pct",
    "champion_std_fold_wape_pct",
    "champion_worst_fold_wape_pct",

    "runner_up_model",
    "runner_up_wape_pct",

    "governance_override_flag",
    "selected_minus_raw_winner_pp"

]


champion_display = (

    champion_df[
        DISPLAY_COLUMNS
    ]

    .copy()

)


NUMERIC_DISPLAY_COLUMNS = [

    "raw_winner_wape_pct",
    "champion_wape_pct",
    "champion_bias_pct",
    "champion_std_fold_wape_pct",
    "champion_worst_fold_wape_pct",
    "runner_up_wape_pct",
    "selected_minus_raw_winner_pp"

]


champion_display[
    NUMERIC_DISPLAY_COLUMNS
] = (

    champion_display[
        NUMERIC_DISPLAY_COLUMNS
    ]

    .round(
        2
    )

)


champion_display = (

    champion_display

    .sort_values(

        [
            "sku_id",
            "channel_id"
        ]

    )

)


print("\n" + "=" * 88)
print("FINAL CHAMPION SELECTION")
print("=" * 88)


print(

    champion_display

    .to_string(
        index=False
    )

)


# ------------------------------------------------------------
# 20. GOVERNANCE OVERRIDE REVIEW
# ------------------------------------------------------------

print("\n" + "=" * 88)
print("GOVERNANCE OVERRIDE REVIEW")
print("=" * 88)


override_rows = (

    champion_df[

        champion_df[
            "governance_override_flag"
        ]

        ==

        "YES"

    ]

)


if len(
    override_rows
) == 0:


    print(
        "No governance overrides."
    )


else:


    for _, row in override_rows.iterrows():


        print(
            f"\n{row['sku_id']} | "
            f"{row['channel_id']}"
        )


        print(
            "Raw WAPE winner:",
            row[
                "raw_wape_winner"
            ]
        )


        print(
            "Raw winner WAPE:",
            round(
                row[
                    "raw_winner_wape_pct"
                ],
                4
            ),
            "%"
        )


        print(
            "Final champion:",
            row[
                "selected_champion"
            ]
        )


        print(
            "Final champion WAPE:",
            round(
                row[
                    "champion_wape_pct"
                ],
                4
            ),
            "%"
        )


        print(
            "WAPE cost of override:",
            round(
                row[
                    "selected_minus_raw_winner_pp"
                ],
                4
            ),
            "percentage points"
        )


        print(
            "Reason:",
            row[
                "selection_reason"
            ]
        )


# ------------------------------------------------------------
# 21. SAVE OUTPUTS
# ------------------------------------------------------------

if all_checks_pass:


    candidate_df.to_csv(
        CANDIDATE_OUTPUT_FILE,
        index=False
    )


    champion_df.to_csv(
        CHAMPION_OUTPUT_FILE,
        index=False
    )


    print("\n" + "=" * 88)
    print("OUTPUT FILES SAVED")
    print("=" * 88)


    print(
        "\nModel evidence:"
    )


    print(
        CANDIDATE_OUTPUT_FILE
    )


    print(
        "\nFinal decision output:"
    )


    print(
        CHAMPION_OUTPUT_FILE
    )


else:


    print(
        "\nOutputs NOT saved because "
        "champion-selection QA failed."
    )


# ============================================================
# END STEP 4B.6
# ============================================================