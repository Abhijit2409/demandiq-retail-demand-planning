# v1 published plan (superseded)

These four files are the Step 5 and Step 6A outputs as first published, byte-for-byte as they were in draft PR #1 (commit `7fce826`). They are kept for audit and because Step 8's 13-week counterfactuals analyse this plan.

| File | Step |
| --- | --- |
| `DemandIQ_Step5_IBP_Decision_Plan.csv` | Step 5 IBP decision engine |
| `DemandIQ_Step6A_Executive_KPI_Summary.csv` | Step 6A KPI layer |
| `DemandIQ_Step6A_Series_Decision_Summary.csv` | Step 6A KPI layer |
| `DemandIQ_Step6A_Weekly_Planning_Trajectory.csv` | Step 6A KPI layer |

## Why it was superseded

v1 counted only the seasonal drops as forward supply. It left out the replenishment already in transit at the forecast origin, which lands in the first three weeks of the window (6,512 units by July 13, 2026). Without it, three series showed repeated weekly misses in August and September and were escalated.

The corrected plan in `05_outputs/ibp_decisions/` and `05_outputs/decision_layer/` counts that replenishment. It escalates no series: 7 PROTECT and 2 HOLD. `05_outputs/peak_season_diagnosis/DemandIQ_Step8B_Step5_Reconciliation.csv` explains every series-level difference.

| Call | v1 (seasonal drops only) | Corrected (plus in-transit replenishment) |
| --- | --- | --- |
| ESCALATE | 3 | 0 |
| PROTECT | 6 | 7 |
| HOLD | 0 | 2 |

## Reproducing it

The current Step 5 code reproduces v1 when run with the old supply view:

```bash
python 04_scripts/step5/step5_ibp_decision_engine.py --supply-view seasonal_only --output-dir <folder>
```

Every one of v1's 157 columns comes out identical. The run adds three columns: the seasonal/replenishment split and the supply-view label. `tests/test_supply_view.py` checks this on every CI run.

The executive summary here still carries its original `generated_at` wall-clock stamp. Current Step 6A runs write `plan_as_of_date` instead, so rebuilds are byte-identical.
