# DemandIQ — Step 7F Decision Record
## Forecast Value Add, Rolling Forecast Cycle 02 & Lifecycle Handoff — HIS-001 (Hybrid Insulated Shell)

**Status:** COMPLETE / FROZEN
**Planning cycles covered:** CYCLE_01_2026-08 (frozen) → CYCLE_02_2026-09 (new)
**Decision date basis:** post-13-week launch window (as-of 2026-11-30)
**Script:** `04_scripts/step7f/step7f_fva_rolling_handoff.py`
**Outputs:** `05_outputs/launch_step7f/` (FVA_Analysis, Cycle02_Rolling_Forecast, Lifecycle_Handoff, Policy_Sensitivity)

> **Provenance:** All figures are **DERIVED** from frozen Steps 7C/7D/7E and the frozen mature analog source (Step 3D economics), combined with **SYNTHETIC** planning-governance assumptions. HIS-001 is a synthetic launch. Nothing here is real Arc'teryx data. Economic figures are **planning exposure proxies**, not accounting profit.

---

## 1. Executive Learning Summary

Step 7F is the final substantive analytical/governance step of the HIS-001 launch. It answers three questions and reaches three governed conclusions:

1. **Did each forecast/planning intervention add or subtract statistical accuracy?**
   On this seeded synthetic launch path, the **V0 analytical baseline was the most accurate** version (WAPE 5.66%). The commercial (V1) and consensus (V2/V3) uplifts **reduced** statistical accuracy (V3 WAPE 11.81%; cumulative V0→V3 FVA **−6.15pp**). **This is not independent proof that merchandising harmed the forecast** — the Step 7E demand generator was centered on V0 (see §8). By contrast, the **early-launch reforecasts consistently added accuracy** (W1 +1.20pp → W8 +6.16pp) because they learned from below-plan actuals.

2. **How should the 18-month forecast roll after the first month of launch evidence?**
   The first true rolling update (Cycle 02, as-of 2026-09-28) carries the **W4 forward evidence signal (−6.13%)** into the horizon using **Method B lifecycle attenuation** (1.00 / 0.50 / 0.25). Like-for-like (17 overlapping months) the outlook falls **−3.05%**; the near term absorbs the full signal while the second season is only lightly revised.

3. **Is HIS-001 ready for the mature forecasting engine?**
   **No.** With 13 observed launch weeks it is **EARLY_LAUNCH**; it has not met the 52-week own-season milestone or the 104-week mature-engine milestone. No ETS/SARIMA is fitted; the recommended method remains the analog + actual-evidence blend.

A secondary **counterfactual policy learning**: the reallocation trigger would have fired only under a 5.0pp threshold (not the frozen 8.0pp), flagged for next-cycle review — **not** a retroactive change and **not** an optimality claim.

---

## 2. Frozen Inputs & Governance

| Input | Source (frozen) | Value used |
|---|---|---|
| V0 analytical 13-week (BASE/NORMAL) | Step 7C `13W_Launch_Forecast` | 6,888.30 |
| V0 weekly shape | Step 7C `analytical_baseline_units` | 13-week profile, reused unchanged |
| V1/V0, V2/V0, V3/V0 level factors | Step 7D `Reconciliation_Summary` (TOTAL_18M) | 1.10903 / 1.10000 / 1.10000 |
| V3 approved 13-week | Step 7E `planned_units_approved` | 7,577.13 |
| Cycle-01 V3 monthly plan (Month×Channel) | Step 7D `Forecast_Versions` (V3_APPROVED_PLAN) | 49,410.88 (18-mo) |
| Realized latent demand (EVAL-ONLY) | Step 7E `Launch_Weekly_Actuals` | 6,809.2 |
| Observed sales (censored) | Step 7E `Launch_Weekly_Actuals` | 6,650.4 |
| ECOM lost demand | Step 7E weekly actuals (`lost_demand_units`) | 158.8 |
| Idle flex reserve | Step 7E `Initial_Buy_Plan` (BALANCED, `reserve_units`) | 991.1 |
| Cold-start seasonal foundation | Step 3D economics (`sku_seasonality_factor`, `weekly_plan_units`) | 0.60 APS + 0.40 IMH, HIS Base annual 27,479.8 |

**Leakage contract enforced in code:** the retrospective FVA branch and the operational Cycle-02 branch are separate functions with separate inputs. Latent synthetic demand is used **only** to score forecasts after the fact; it never feeds any reforecast, the Cycle-02 forecast, or any decision. Steps 7A–7E and mature Steps 4A–6F were read-only.

---

## 3. Forecast Value Add Methodology

- **Truth for retrospective scoring:** Step 7E seeded **latent synthetic demand** (not observed sales, which are censored by the W13 ECOM stockout). Evaluation-only.
- **Metrics:** WAPE = Σ|F−A|/ΣA×100; **Bias = Σ(F−A)/ΣA×100** (governed sign); MAE; total error units.
- **Version FVA:** `FVA_WAPE_pp = WAPE(prior) − WAPE(new)` → **positive = accuracy improved**, negative = worsened.
- **Fair horizon:** all four pre-launch versions (V0/V1/V2/V3) evaluated on the **identical W1–W13** window. V1/V2/V3 are the frozen V0 weekly shape scaled by frozen Step 7D level factors — no reshaping.
- **Checkpoint FVA (strict temporal fairness):** each reforecast scored **only on weeks that were future at its creation**; the baseline is the original V3 plan for those same future weeks.

---

## 4. V0 vs V1 vs V2 vs V3

Evaluation horizon **W1–W13**, truth = latent synthetic demand.

| Version | Level factor | WAPE | Bias | MAE | Error units | FVA vs prior |
|---|---|---|---|---|---|---|
| V0 Analytical Baseline | 1.00000 | **5.66%** | +1.16% | 29.6 | +79.1 | — (anchor) |
| V1 Commercial Plan | 1.10903 | 12.58% | +12.19% | 65.9 | +830.1 | **−6.92pp** (worsened) |
| V2 Consensus | 1.10000 | 11.81% | +11.28% | 61.8 | +767.9 | **+0.77pp** (improved) |
| V3 Approved | 1.10000 | 11.81% | +11.28% | 61.8 | +767.9 | **0.00pp** (V3 = V2) |
| **V3 vs V0 (cumulative)** | | | | | | **−6.15pp** |

V0 is the most accurate on this path; the +10.9% commercial uplift added the most positive bias and error; the −0.9% consensus pullback from V1 to V2 recovered a small amount; V3 = V2 exactly, so their FVA is correctly zero.

---

## 5. Commercial / Consensus FVA

- **V0 → V1 (commercial, +10.9%): −6.92pp.** The commercial merchandising uplift moved the plan away from the (V0-centered) realized path, inflating both bias (+1.16% → +12.19%) and WAPE.
- **V1 → V2 (consensus, capped to +10% over V0): +0.77pp.** The consensus step pulled the level slightly back toward V0 and recovered a small amount of accuracy.
- **V2 → V3 (approved = consensus): 0.00pp.** No numerical change; no manufactured difference.

**Interpretation must remain conditional (see §8): this ranks statistical accuracy on one seeded path centered on V0 — it does not establish that the commercial process is wrong.**

---

## 6. Checkpoint Reforecast FVA

Each reforecast's forward-only quantity = `reforecast_total − cumulative_observed` (the Step 7E checkpoint file stores observed-to-date + forecast-of-remaining), distributed across still-future weeks by the **original V3 weekly shape**, scored against latent demand for those weeks only.

| Reforecast | Evaluated weeks | Reforecast WAPE | Original-V3 WAPE (same weeks) | **FVA** |
|---|---|---|---|---|
| W1 | W2–W13 (12) | 10.84% | 12.03% | **+1.20pp** |
| W2 | W3–W13 (11) | 9.18% | 11.98% | **+2.80pp** |
| W4 | W5–W13 (9) | 6.34% | 11.36% | **+5.01pp** |
| W8 | W9–W13 (5) | 5.09% | 11.25% | **+6.16pp** |
| W13 | — | — | — | **NOT_MEASURABLE_NO_REMAINING_HORIZON** |

Every reforecast **added accuracy** and value grew as more evidence accrued — because the reforecasts learned from the below-plan actuals and pulled toward the (V0-centered) realized level. No already-observed week was ever scored; W13 correctly receives no forward FVA.

---

## 7. Forecast Quality vs Planning Quality

Statistical accuracy and business decision quality are **separate**:

- **Accuracy consequence:** V0 had the lowest WAPE; the commercial/consensus uplift raised it (on this path).
- **Planning consequence:** the launch nonetheless delivered **97.7% service**, carried a launch-appropriate buffer, and produced HOLD at every checkpoint. The higher plan level is a defensible risk-management posture for a cold-start launch even though it scored worse against a V0-centered realized path.

**Do not conclude "V0 was the best business decision" from its WAPE alone.** A forecast intervention can subtract statistical accuracy while still being a reasonable planning choice; a high-service buy can carry excess inventory. Both consequences are reported.

---

## 8. Simulation-Design Caveat (must not be omitted)

**The Step 7E synthetic actual generator was centered on the pre-commercial V0 analytical baseline, not on the +10% V3 consensus plan.** The simulation's expected demand is therefore structurally closer to V0.

Correct reading of the FVA result:

> *"On this seeded synthetic launch path, the commercial/consensus uplift reduced forecast accuracy relative to V0. Because the synthetic demand generator was centered on the V0 analytical baseline, this FVA comparison is an illustrative governance demonstration, not independent empirical validation that the commercial override was harmful."*

Step 7E was **not** rerun with a different seed to change the result. This caveat is embedded in the FVA output and governs every accuracy statement in this record.

---

## 9. Cycle-02 Timing & Evidence Cutoff

- **planning_cycle = CYCLE_02_2026-09**, **forecast_as_of_date = 2026-09-28** (end of W4).
- Under the Step 7C Monday-week / Thursday-month rule, **W1–W4 (Aug 31, Sep 7, Sep 14, Sep 21) are exactly September**; W5's Thursday is Oct 1, so W5 belongs to October. September is complete at W4, letting Cycle 02 roll cleanly into October.
- **Evidence cutoff = W4.** Cycle 02 uses only W1–W4 information (observed, W4 reforecast, availability through W4, frozen priors). It **excludes** W5–W13 actuals, the W8/W13 reforecasts, the final latent truth, final observed sales, final service, the retrospective FVA, and the policy-sensitivity result. This is enforced by code architecture (separate branch).

---

## 10. September 2026 Actualization

September is no longer a forward month. It is stored as **ACTUALIZED_PERIOD** using **observed** W1–W4 sales only (no hidden truth):

| Channel | Cycle-01 V3 (Sep) | Actualized (obs W1–W4) | Revision |
|---|---|---|---|
| ECOM | 606.65 | 595.8 | −1.79% |
| RETAIL | 471.86 | 402.9 | −14.62% |
| WHOLESALE | 269.63 | 184.2 | −31.68% |
| **Total** | **1,348.1** | **1,182.9** | **−12.3%** |

Actualized September total (1,182.9) reconciles to the Step 7E cumulative observed at W4 (1,183.0). No stockout occurred within W1–W4, so observed equals demand there. This demonstrates the forecast → actual → roll-forward transition.

---

## 11. Cycle-02 18-Month Rolling Forecast

Cycle 02 genuinely rolls:

- **DROP** September 2026 (→ actualized history).
- **SHIFT** October 2026 → February 2028 one horizon position closer.
- **ADD** March 2028 as the new Month 18.

Grain = Planning Cycle × Month × SKU × Channel. **18 forward months (Oct 2026 → Mar 2028)**, all at the frozen **45/35/20** channel mix. Continuing months = Cycle-01 V3 approved × Method-B evidence factor:

| Lifecycle phase | Months | Attenuation weight | Applied revision |
|---|---|---|---|
| RAMP / SEASONAL PEAK (remaining first-season peak) | Oct–Dec 2026 | 1.00 | −6.13% |
| NORMALIZATION | Jan–Jun 2027 | 0.50 | −3.07% |
| SECOND-SEASON / MATURATION | Jul 2027 – Mar 2028 | 0.25 | −1.53% |

**Method B weights (1.00 / 0.50 / 0.25) are SYNTHETIC ROLLING-FORECAST GOVERNANCE ASSUMPTIONS** — the lifecycle phases provide the attenuation structure, but the exact weights are not statistically estimated. Rationale: W4 evidence is most informative for the immediate launch season, confidence should decay with forecast distance, and four observed weeks cannot fully determine the next Fall/Winter.

Versions preserved: `CYCLE_01_V3_APPROVED_PLAN` (previous) and `CYCLE_02_ANALYTICAL_UPDATE` (new); no new synthetic commercial override was invented.

---

## 12. Like-for-Like Cycle01 vs Cycle02 Revision

Over the **17 overlapping months (Oct 2026 → Feb 2028)** — the only fair comparison, since Sep drops and Mar enters:

| | Units |
|---|---|
| Cycle-01 V3 approved (overlap) | 48,062.7 |
| Cycle-02 analytical update (overlap) | 46,596.6 |
| **Revision** | **−1,466.1 (−3.05%)** |

This is **pure forecast revision**: the same months re-forecast on W4 evidence, attenuated by lifecycle phase. The near term carries the full −6.13%; the far horizon only −1.53%.

---

## 13. Full Rolling-Window Outlook Change

The full-window totals cover **different windows** and must not be read as pure revision:

| Window | Total |
|---|---|
| Cycle-01 (Sep 2026 → Feb 2028) | 49,410.9 |
| Cycle-02 (Oct 2026 → Mar 2028) | 49,642.2 |

Labelled **ROLLING-WINDOW OUTLOOK CHANGE**, not forecast revision: the +231 difference is a **composition effect** — September (~1,348 at V3) drops out and the new March 2028 (3,045.6) enters. The governed like-for-like number is §12's −3.05%.

---

## 14. Near-Term vs Far-Horizon Learning

The attenuation deliberately concentrates learning near term: Oct–Dec 2026 revised −6.13%, Jan–Jun 2027 −3.07%, and Jul 2027 onward only −1.53%. Four weeks of launch evidence strongly informs the immediate ramp/peak but is weak evidence about next winter's own-season demand, so the second season is only lightly revised. This is the core rolling-forecast discipline of Cycle 02.

---

## 15. March-2028 New Horizon Month

March 2028 was **generated from frozen methodology**, not copied from February 2028 or March 2027:

- Frozen **0.60 APS + 0.40 IMH** normalized 52-week seasonal profile (Step 7C engine, Step 3D source);
- ISO weeks assigned to March 2028 by the **Monday-week / Thursday-month** rule (5 Thursday-weeks fall in March 2028 — a genuine calendar effect);
- HIS **Base annual scale**, **second-season factor 1.00**;
- **× frozen V3/V0 = 1.10000** so the new month sits on the **approved-plan basis, consistent with the continuing Cycle-02 months** (corrected in the final governance patch);
- **× 0.25 × W4 forward revision** (second-season attenuation);
- **× 45/35/20** channel mix.

Result: ECOM 1,370.51 / RETAIL 1,065.95 / WHOLESALE 609.11 = **3,045.6**. The construction was validated by reproducing existing frozen second-season months (e.g., Dec 2027, Feb 2028) from the same engine before generating March 2028. March has no literal Cycle-01 predecessor (it did not exist in Cycle 01), so `previous_cycle_units` is blank by design.

---

## 16. Reallocation-Threshold Policy Learning

On the frozen realized path, ECOM's channel-mix deviation peaked at **+5.4pp** (W1–W8), below the frozen **8.0pp** REALLOCATE trigger, so the 991.1-unit reserve stayed idle and the W13 ECOM stockout (158.8 units lost) occurred. A **COUNTERFACTUAL POLICY SENSITIVITY** diagnostic (frozen values read from Step 7E, not hard-coded):

| Threshold | Would trigger? | First trigger | Reserve available | Indicative deployable | Arrives before W13 (~2-wk lead)? |
|---|---|---|---|---|---|
| **5.0pp** | YES | W1 | 991.1 | ~158.8 | YES (arrive ~W3) |
| **6.5pp** | NO | — | 991.1 | — | — |
| **8.0pp** (frozen rule) | NO | — | 991.1 | — | — |

Only a 5.0pp trigger would have fired. **Classified as POLICY LEARNING / NEXT-CYCLE REVIEW** — not causal proof, not an optimality claim, and not a change to the frozen Step 7E 8pp rule or the historical decision. One seeded path cannot establish an optimal threshold.

---

## 17. Lifecycle Status

| Field | Value |
|---|---|
| as_of_date | 2026-11-30 (after the 13-week launch window completes) |
| observed_weeks | 13 |
| current_lifecycle_status | **EARLY_LAUNCH** |
| calendar quality | PASS (13/13 weekly calendar complete) |
| availability quality | CENSORED_W13_ECOM_STOCKOUT — demand reconstruction required before handoff |
| channel coverage | PASS (all 3 channels) |
| recommended method | ANALOG (0.60 APS + 0.40 IMH) + actual-evidence blend; **no ETS/SARIMA** |

Lifecycle ladder: COLD_START (0w) → **EARLY_LAUNCH (1–13w, current)** → MATURING_LAUNCH (14–51w) → SEASONAL_HISTORY_AVAILABLE (≥52w) → MATURE_MODEL_ELIGIBLE (≥104 clean weeks + gates).

---

## 18. Mature-Engine Eligibility

- **52-week own-season milestone: NOT MET** (need ≥52 clean weeks to observe one own-season cycle).
- **104-week mature-engine milestone: NOT MET** (need ≥104 clean weekly observations **and** all data-quality gates).
- Aligns with the frozen Step 4B backtest (initial training = 104 weeks, seasonal period = 52). Thirteen weeks is not "mature history." **No ETS/SARIMA is fitted to HIS-001 now**, and the existing APS/IMH champion models are **not** auto-assigned.

Next review scheduled at the 52-week milestone.

---

## 19. Future Mature-Engine Handoff

When HIS-001 eventually becomes eligible:
1. Build governed HIS weekly historical demand at **Week × HIS-001 × Channel**.
2. Apply stockout / demand-reconstruction governance (observed sales ≠ uncensored demand).
3. Create the forecasting input.
4. Run the frozen model-selection philosophy (seasonal baselines, ETS, selective challengers where justified).
5. Use expanding-window validation.
6. Select champions on WAPE + bias + simplicity.
7. Only then add HIS-001 into the mature planning engine.

Do not automatically assign the existing APS/IMH model to HIS-001.

---

## 20. Governance / Leakage Controls

- Steps 7A–7E and mature Steps 4A–6F untouched (read-only).
- Hidden latent demand is evaluation-only; it never entered a reforecast, Cycle 02, or any decision.
- No retrospective FVA and no policy-sensitivity result entered Cycle 02 (separate code branches; W4 evidence cutoff enforced).
- No mature model fitted to HIS-001.
- All Step 7F outputs are reproducible from frozen inputs and internally reconciled (18 forward months; Sep dropped / Mar added; channels reconcile to SKU at 45/35/20; overlap and full-window computed separately).
- Reserve and ECOM-lost figures read from frozen Step 7E outputs, not hard-coded constants.

---

## 21. Limitations

- **Single seeded launch path** (seed = 7); one path cannot establish an optimal override or reallocation threshold.
- **Synthetic actual generator centered on V0** — commercial FVA is conditional on simulation design, not independent empirical evidence (see §8).
- **Short 13-week evaluation**; reforecast FVA horizon shrinks at later checkpoints; W13 has no forward FVA.
- **ECOM observed sales are stockout-censored** — observed ≠ full demand; latent truth is evaluation-only.
- **FVA accuracy ≠ business value** — a low-WAPE forecast can still be the wrong risk-management choice.
- Method-B attenuation weights and the counterfactual thresholds are **synthetic governance assumptions**, not estimated parameters.
- Economics are **planning exposure proxies**, not profit/margin.

---

## 22. Step 7F Conclusion

Step 7F delivered the launch program's first genuine forecast-value-add audit, its first true rolling-forecast update, and an explicit lifecycle-handoff decision — all under strict leakage governance. On this seeded path the **analytical baseline was most accurate and the early reforecasts added value**, while the commercial/consensus uplift subtracted statistical accuracy (with the mandatory V0-centering caveat). Cycle 02 rolls cleanly into Oct 2026 → Mar 2028 with **lifecycle-attenuated W4 learning (−3.05% like-for-like)** and a **methodology-generated March 2028 (3,045.6, approved-plan basis)**. HIS-001 remains **EARLY_LAUNCH** and is **not** eligible for the mature engine. All QA passed; no computational defect remains.

**STEP 7F — COMPLETE / FROZEN.**

---

## 23. Exact Next Step

**STEP 7G — NEW PRODUCT LAUNCH PLANNING WORKSPACE + CASE-STUDY INTEGRATION.**

Do not start Step 7G until directed. Do not modify Steps 7A–7E, mature Steps 4A–6F, or the frozen Step 7F outputs unless a genuine computational defect is later discovered.
