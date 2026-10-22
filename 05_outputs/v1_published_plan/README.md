# v1 published plan: the zero-replenishment view

These four files are the Step 5 and Step 6A outputs as first published, byte-for-byte as they were in draft PR #1 (commit `7fce826`). They are kept for audit, because Step 8's 13-week counterfactuals analyse this plan, and because they stay the published escalation list until open orders are confirmed (below). Step 6A reads this plan as its zero-replenishment comparison.

| File | Step |
| --- | --- |
| `DemandIQ_Step5_IBP_Decision_Plan.csv` | Step 5 IBP decision engine |
| `DemandIQ_Step6A_Executive_KPI_Summary.csv` | Step 6A KPI layer |
| `DemandIQ_Step6A_Series_Decision_Summary.csv` | Step 6A KPI layer |
| `DemandIQ_Step6A_Weekly_Planning_Trajectory.csv` | Step 6A KPI layer |

## How it relates to the current plan

v1 counted only the seasonal drops as forward supply, so it assumed zero replenishment. Its seasonal drops were themselves a projection: last year's seasonal receipts shifted 52 weeks and grown by SKU, not confirmed supplier orders. v1 named that column `committed_receipt_units`; the name is kept so this plan reproduces column for column, and current runs add `seasonal_receipt_projection_status = PROJECTED_NOT_CONFIRMED` beside it. Three series then showed repeated weekly misses in August and September and were escalated (3 ESCALATE, 6 PROTECT): APS-001 Wholesale, CTS-001 Retail and IMH-001 Wholesale.

The plan in `05_outputs/ibp_decisions/` and `05_outputs/decision_layer/` adds an **estimate** of replenishment receipts: last year's replenishment receipts shifted 52 weeks, plus SKU growth, 6,512 units projected to land by July 13, 2026. These are **not confirmed open orders**. The July 13 check validates the projected dates against the 3-week replenishment lead time, not supplier commitments. If the estimate arrives as modelled, no series escalates: 0 ESCALATE, 7 PROTECT, 2 HOLD. `05_outputs/peak_season_diagnosis/DemandIQ_Step8B_Step5_Reconciliation.csv` explains every series-level difference.

| Call | Zero replenishment (v1, published) | If the estimated replenishment arrives as modelled |
| --- | --- | --- |
| ESCALATE | 3 | 0 |
| PROTECT | 6 | 7 |
| HOLD | 0 | 2 |

A planner must confirm open-order quantities and receipt dates before the right-hand calls replace this published escalation list. Until then, both views stand side by side.

## Reproducing it

The current Step 5 code reproduces v1 when run with the old supply view:

```bash
python 04_scripts/step5/step5_ibp_decision_engine.py --supply-view seasonal_only --output-dir <folder>
```

Every one of v1's 157 columns comes out identical. The run adds eight columns: the estimated and planned receipts (zero replenishment, so planned equals the projected seasonal drops), the supply-view label, the seasonal-drop projection status and provenance, and the replenishment provenance, confirmation-status and call-condition labels. `tests/test_supply_view.py` checks this on every CI run.

The executive summary here still carries its original `generated_at` wall-clock stamp. Current Step 6A runs write `plan_as_of_date` instead, so rebuilds are byte-identical.
