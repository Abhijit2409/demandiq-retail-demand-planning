# DemandIQ — Step 7C — Cold-Start & 18-Month Lifecycle Forecast Decision Record

**Launch product:** HIS-001 — Hybrid Insulated Shell
**Forecast version:** **V0 — ANALYTICAL BASELINE** (unconstrained demand)
**Step status:** COMPLETE. Steps 7A/7B and the mature engine (4A–6F) remain frozen and untouched. No V1–V3, reconciliation, consensus, or supply constraint is produced here (that is Step 7D).

> **Simulation notice.** HIS-001 and all launch values are **SYNTHETIC PLANNING ASSUMPTIONS**; analog attributes are **DERIVED from frozen synthetic project data**. This is an **unconstrained demand** forecast — no inventory/supply limits are applied. Figures are planning quantities, not real performance.

---

## 1. Executive Forecast Summary

Using the frozen Step 7B analog blend (0.60 APS-001 + 0.40 IMH-001) and launch assumptions, the V0 analytical baseline for HIS-001 is:

| Diagnostic (V0, BASE / NORMAL unless noted) | Value |
|---|---:|
| **18-month BASE demand** (Sep 2026 – Feb 2028) | **44,919 units** |
| First 12-month BASE demand | 27,480 units |
| Second-season visible BASE demand (Sep 2027–Feb 2028) | 17,439 units |
| **13-week BASE launch demand** | **6,888 units** |
| Adoption band LOW / BASE / HIGH (18M) | 33,689 / 44,919 / 56,149 (spread 22,459) |
| Weather band around BASE — MILD / NORMAL / SEVERE (18M) | 43,158 / 44,919 / 47,384 |
| Peak month | **Dec 2026 (4,284 units)**; second peak Dec 2027 (4,091) |
| Channel split (planned) | ECOM 45% · RETAIL 35% · WHOLESALE 20% |

The forecast tells a clean lifecycle story: a September launch ramps through the fall, peaks in December, normalizes through spring/summer 2027, and rebuilds into a second Fall/Winter season — all borrowed from the analogs' cold-season shape and scaled by the governed launch assumptions.

## 2. Forecast Version & Governance

Everything here is **V0_ANALYTICAL_BASELINE** — the demand-planning starting position **before** merchandising/sales overrides, top-down targets, reconciliation, consensus, supply constraints, or approved-plan changes. It is **unconstrained demand**: if supply later proves insufficient, that becomes service risk / lost opportunity in a later step — it does **not** reduce this forecast. Every row is labelled with the version, provenance, and its adoption × weather scenario.

## 3. Analog Foundation

Demand **shape** and demand **scale** are kept strictly separate:

- **Shape** — the normalized 52-week seasonal profile of each analog (`sku_seasonality_factor`, frozen Step 3D economics), each normalized to sum 1.00 **before** blending so analog volume never leaks into shape, then combined 0.60 APS / 0.40 IMH.
- **Scale** — the analogs' annual planning demand (`weekly_plan_units`), giving the comparable-demand anchor.

Source: `02_data/processed/DemandIQ_Step3D_v4_Retail_Economics.csv`. Validation: the file's `week_of_year` equals ISO week for all 21,060 rows (0 mismatches), so future launch weeks map onto the profile correctly. CTS-001 contributes nothing (excluded in Step 7B).

## 4. Demand-Scale Construction

Recomputed precisely from the frozen source (not typed by hand):

| | Units/yr |
|---|---:|
| APS-001 comparable | 28,270.96 |
| IMH-001 comparable | 72,092.78 |
| Blended (0.60·APS + 0.40·IMH) | **45,799.69** |
| **HIS Base annual = blended × 0.60 launch-scale** | **27,479.81** |

## 5. 52-Week Blended Seasonal Profile

`blended[w] = 0.60·p_APS[w] + 0.40·p_IMH[w]`, sums to **1.000000**. Peak in ISO weeks 49–52 (December, ≈0.030 share each); trough ISO week 28 (summer, 0.0105). Because APS and IMH share a near-identical Fall/Winter shape (Step 7B correlation 0.99), the blend has a clean, single-peaked cold-season curve — the insulation analog does not distort the seasonality.

## 6. Lifecycle Treatment (interpretable; no double-discount)

The lifecycle governs **when** demand occurs, never a second cut to **how much**:

- **First-season ramp:** a gentle multiplier climbing 0.60 → 1.00 across the first 13 weeks (LAUNCH + RAMP), then flat. It is applied to the seasonal shape and then **renormalized so the first 52 weeks sum exactly to the governed Base annual (27,479.81)**. This is the anti-double-discount guarantee: the 0.60 launch-scale factor sets the scale once; the ramp only redistributes timing. **QA verified:** year-1 total = 27,479.81 to the unit.
- **Second-season maturation:** factor **1.00** (owner decision — flat run-rate, most conservative, no growth claim). Year-2 weeks use the pure seasonal profile at the Base run-rate.
- A small, expected level step exists at the year boundary: the first-season peak (Dec 2026, 4,284) is modestly above the second (Dec 2027, 4,091) because the launch ramp redistributes suppressed early-launch demand into the first peak. This is a documented artifact of a conservative flat second season, not a decline assumption.

Ramp start (0.60) and maturation (1.00) are **SYNTHETIC PLANNING ASSUMPTIONS**.

## 7. 18-Month Analytical Baseline

`DemandIQ_Step7C_18M_Analytical_Forecast.csv` — grain Month × HIS-001 × Channel × Adoption × Weather. BASE / NORMAL monthly trajectory:

| Month | Phase | Units | Month | Phase | Units |
|---|---|---:|---|---|---:|
| 2026-09 | LAUNCH | 1,226 | 2027-06 | NORMALIZATION | 1,308 |
| 2026-10 | RAMP | 2,601 | 2027-07 | SECOND-SEASON | 1,512 |
| 2026-11 | RAMP | 3,062 | 2027-08 | SECOND-SEASON | 1,345 |
| 2026-12 | SEASONAL PEAK | **4,284** | 2027-09 | SECOND-SEASON | 2,154 |
| 2027-01 | NORMALIZATION | 3,097 | 2027-10 | SECOND-SEASON | 2,470 |
| 2027-02 | NORMALIZATION | 2,824 | 2027-11 | SECOND-SEASON | 3,001 |
| 2027-03 | NORMALIZATION | 2,353 | 2027-12 | SECOND-SEASON | 4,091 |
| 2027-04 | NORMALIZATION | 2,363 | 2028-01 | SECOND-SEASON | 2,993 |
| 2027-05 | NORMALIZATION | 1,506 | 2028-02 | SECOND-SEASON | 2,730 |

## 8. LOW / BASE / HIGH Adoption Scenarios

Frozen Step 7B multipliers (launch-adoption uncertainty — **not** confidence intervals, **not** weather): LOW ×0.75, BASE ×1.00, HIGH ×1.25. Produced for every month/week and channel. 18-month totals: **LOW 33,689 · BASE 44,919 · HIGH 56,149**. QA confirms LOW < BASE < HIGH in every non-zero cell.

## 9. 13-Week Launch Forecast

`DemandIQ_Step7C_13W_Launch_Forecast.csv` — same engine, weeks 1–13 from on-sale 2026-08-31. BASE / NORMAL weekly demand ramps **283 (W1) → 806 (W13)** as adoption builds into the December peak. Checkpoints flagged W1/W2/W4/W8/W13 (283 / 299 / 330 / 548 / 806 units) for the Step 7F sell-through comparison. 13-week BASE total: **6,888 units**.

## 10. Channel Outlook

Planned DTC-led launch mix (Step 7B) applied to unconstrained demand: **ECOM 45% · RETAIL 35% · WHOLESALE 20%**. The analytical analog prior (40.8 / 32.4 / 26.8) is preserved in Step 7B provenance and not overwritten; Step 7C uses the *approved* planned mix. Channel values reconcile exactly to the SKU total in every period/scenario.

## 11. Peak Demand Timing

First-season peak: **December 2026 (4,284 units/month)**; peak launch-execution week is W13 (week of 2026-11-23), as the 13-week window closes right as demand ramps into December. Second-season peak: December 2027 (4,091). This matches the analogs' ISO-week-49–52 cold-season peak.

## 12. Weather Scenario Treatment

Adoption and weather stay separate, composable layers (no 3×3 clutter — 5 governed combos: LOW/BASE/HIGH at NORMAL, plus BASE at MILD and SEVERE). HIS weather caps are the 60/40 blend of the frozen analog caps (SKILL §11): **Severe +5.6% · Mild −4% · Normal 0%**. Weeks 1–3 are `NOWCAST_REQUIRED` → no weather adjustment (matching frozen Step 4C governance); weeks 4+ and all months use the seasonal-analog scenario (a governed extension beyond the Step 4C horizon — **not** realized future weather). 18-month BASE weather band: MILD 43,158 · NORMAL 44,919 · SEVERE 47,384.

## 13. 18M / 13W Reconciliation

Both views derive from one weekly engine, so they reconcile by construction. Weekly demand is aggregated to months by the ISO "Thursday rule" (each Monday-week belongs to the month of its Thursday), which places the 2026-08-31 launch week in September and keeps August as pre-launch context (zero forecast units). **QA:** BASE/NORMAL weekly roll-up vs the 18-month monthly value — **max difference 0.0000** (rounding only). The only expected boundary effect is the partial month at the 13-week tail (late Nov 2026), documented and not a discrepancy.

## 14. Rolling-Forecast Readiness

The 18-month file carries `planning_cycle` (CYCLE_01_2026-08), `forecast_as_of_date` (2026-08-24, synthetic pre-launch), `planning_month`, and `horizon_month_number` (1–18). The structure supports rolling forward monthly — the next cycle would shift to Oct 2026 → Mar 2028 without changing the methodology. No future cycles are generated here.

## 15. Forecast Plan Diagnostics

These are **plan diagnostics, not accuracy KPIs** (HIS-001 has no actuals yet): 18-month BASE 44,919; first-12-month 27,480 (= governed Base annual, confirming the ramp preserves scale); second-season visible 17,439; 13-week BASE 6,888; adoption spread (HIGH−LOW) 22,459; peak Dec 2026 (4,284); channel shares 0.45/0.35/0.20.

## 16. Governance / Leakage Controls

No `true_demand_units`, `lost_demand_units`, `audit_hidden_*`, `weather_effect_pct`, `weather_factor`, spike/shock/noise generator factors, future realized weather, or future HIS actuals/sell-through were used. Inputs are the frozen analog seasonality + planning-demand fields plus the labelled Step 7B synthetic assumptions. Mature Steps 4A–6F outputs untouched; launch outputs isolated in `05_outputs/launch_step7c/`.

## 17. Limitations

- Seasonality is **borrowed** from analogs (unavoidable cold-start), not HIS's own history.
- Ramp shape and second-season maturation are **synthetic assumptions**; the ramp is scale-neutral by renormalization, the maturation is deliberately flat (1.00).
- The modest first-vs-second peak step is a documented artifact of the conservative flat second season.
- Weather caps are a governed analog-blend **extension** beyond the Step 4C horizon — seasonal-planning, not realized weather.
- Channel mix is held constant at 45/35/20 (wholesale scale-in timing not separately modelled in 7C).
- This is **V0 unconstrained demand** — commercial and supply realities are applied only from Step 7D onward.

## 18. Step 7C Conclusion

The HIS-001 cold-start V0 analytical baseline is complete, internally reconciled, and fully governed: an 18-month rolling IBP view (44,919 BASE units, Dec peak, two seasons) and a 13-week launch-execution view (6,888 BASE units, ramp 283→806) built from the *same* demand logic, with adoption and weather held as separate composable layers. All QA passed (18-month grain, 13-week grain, analog blend, LOW<BASE<HIGH, channel reconciliation, weekly↔monthly reconciliation, leakage).

## 19. Exact Next Step

**STEP 7D — Top-Down / Bottom-Up Reconciliation & Consensus Forecast.** Not started. It will introduce the synthetic top-down category plan, reconcile it against this bottom-up V0 baseline, and progress the forecast through V1 (commercial) → V2 (consensus) → V3 (approved).

---

*Step 7C decision record. V0 analytical baseline only; unconstrained demand; mature Steps 4A–6F frozen and untouched. Every launch value is a labelled synthetic planning assumption.*
