# DemandIQ — Step 7B — Analog Selection & Launch Assumption Decision Record

**Launch product:** HIS-001 — Hybrid Insulated Shell
**Step status:** COMPLETE / FROZEN. Design (Step 7A) and the mature engine (Steps 4A–6F) remain frozen; no mature output was modified. The 18-month forecast (Step 7C) has **not** been started.

> **Simulation notice.** HIS-001 and every launch value in this record are **SYNTHETIC PLANNING ASSUMPTIONS**. They do not represent a real Arc'teryx product, price, or plan. Mature analog attributes are **DERIVED from frozen synthetic project data**. Economic values elsewhere in DemandIQ are planning exposure proxies, not profit.

---

## 1. Decision Summary

HIS-001 will be forecast from a **two-analog blend: 0.60 × APS-001 (Alpine Performance Shell) + 0.40 × IMH-001 (Insulated Midlayer Hoody)**. CTS-001 is **not** used.

This is the decision's central insight: **the highest total similarity score does not, by itself, choose the analog set.** APS-001 is the clear top-ranked single analog (0.679, stable across all sensitivity scenarios), but it is weak on exactly one defining HIS-001 capability — **insulation** (0.20 vs HIS-001's 0.90). The candidate that ranks **#2 by score, CTS-001, does not fix that gap** (insulation 0.15 — a second weatherproof shell). The candidate that ranks **#3, IMH-001, is the only one that supplies insulation** (0.95) and it shares APS-001's Fall/Winter seasonal shape (correlation 0.99). An *insulated shell* therefore needs APS-001's shell + IMH-001's insulation. The blend rule, not the raw ranking, produces the defensible answer.

| Decision | Value |
|---|---|
| Primary analog | **APS-001**, weight **0.60** |
| Secondary analog | **IMH-001**, weight **0.40** |
| Excluded | CTS-001 (redundant shell; no complementary insulation) |
| Sensitivity | **STABLE** — APS-001 stays top in all 5 weight scenarios |
| Analytical channel mix | ECOM 0.408 / RETAIL 0.324 / WHOLESALE 0.268 |
| Final planned channel mix | ECOM 0.45 / RETAIL 0.35 / WHOLESALE 0.20 (DTC-led override) |
| Base launch-scale factor | 0.60 × blended analog comparable demand |
| Adoption band | LOW 0.75 · BASE 1.00 · HIGH 1.25 (symmetric ±25%) |

## 2. HIS-001 Launch Brief *(all SYNTHETIC PLANNING ASSUMPTIONS)*

| Attribute | Value |
|---|---|
| SKU / product | HIS-001 / Hybrid Insulated Shell |
| Positioning | Premium technical outerwear — insulation + weather protection |
| Launch (on-sale) date | **2026-08-31** (a valid Monday `week_start`) |
| Season | Fall/Winter (FW26) |
| MSRP | CAD **750** (mid-premium, between IMH 400 and APS 800) |
| Weather sensitivity | **0.255** (deliberately between APS 0.292 and CTS/IMH 0.215) |
| Launch channels | ECOM, RETAIL, WHOLESALE (DTC-led weighting) |

**Launch-date rationale:** an end-of-August on-sale starts the fall build, so the 13-week execution window runs into the early-December cold-season peak (analog peak ISO wk49), and the 18-month strategic horizon (Sep 2026 → Feb 2028) spans **two Fall/Winter seasons** — enabling lifecycle and second-season planning. Frozen.

## 3. Candidate Analog Pool

| Candidate | Product | Eligibility | Verdict |
|---|---|---|---|
| APS-001 | Alpine Performance Shell | Premium technical shell, FW-peaking (wk49), overlapping channels | **QUALIFIES (strong)** |
| IMH-001 | Insulated Midlayer Hoody | Insulation, FW-peaking (wk49), overlapping channels | **QUALIFIES (strong on insulation)** |
| CTS-001 | Core Technical Shell | Core shell, but different seasonal profile (peak wk45; corr 0.36–0.47) | **QUALIFIES but WEAKER (seasonality)** |

No candidate was removed before scoring (per governance: a candidate is not dropped for "looking unlikely to win"). CTS-001 was flagged weaker on evidence, then evaluated fully.

## 4. Scoring Framework

`final_score = Σ_d ( weight_d × similarity_d )`, each similarity ∈ [0,1] (1 = strong).

| Dimension | Weight | Type | Normalization |
|---|---:|---|---|
| Functional | 0.30 | SYNTHETIC attribute matrix | `1 − mean|Δattr|` over 5 attributes |
| Seasonal fit | 0.25 | DATA-DERIVED | cold-season concentration (ISO wk 40–52 + 1–9), rescaled vs uniform baseline |
| Price | 0.15 | DATA-DERIVED | `1 − min(1, |ΔMSRP|/400)` |
| Weather | 0.15 | DATA-DERIVED | `1 − min(1, |Δsensitivity|/0.10)` |
| Demand scale | 0.10 | MIXED | `1 − min(1, |Δln(scale)|/ln 3)` vs a wide independent HIS band |
| Channel mix | 0.05 | DATA-DERIVED (non-discriminating) | `1 − ½Σ|Δshare|` |

Weights are **GOVERNANCE ASSUMPTIONS** — principle-based, summing to 1.00, and **not tuned to any HIS-001 outcome** (which does not exist). **0.55 of the weight is discriminating data-derived** (seasonal + price + weather), so the conclusion does not rest on the synthetic functional matrix.

**Seasonal-dimension note (governed relabel):** this dimension is **SEASONAL / COLD-SEASON FIT** — how strongly each mature product matches HIS-001's *known* Fall/Winter positioning — **not** similarity to an HIS-001 history (there is none). The pairwise seasonal correlation matrix is retained as **corroborating evidence only**, not as a second score.

**Functional attribute matrix** *(SYNTHETIC PRODUCT-ATTRIBUTE ASSUMPTION; frozen before scoring)*:

| Attribute | HIS-001 | APS-001 | CTS-001 | IMH-001 |
|---|---|---|---|---|
| Insulation | 0.90 | 0.20 | 0.15 | **0.95** |
| Weather protection | 0.90 | **0.95** | 0.80 | 0.35 |
| Shell construction | 0.85 | **0.95** | 0.90 | 0.25 |
| Technical/premium | 0.90 | 0.90 | 0.65 | 0.60 |
| Cold/transitional use | 0.90 | 0.75 | 0.55 | 0.85 |

## 5. Corrected Similarity Results

*(HIS-001 weather sensitivity corrected to 0.255; MSRP 750. Source: `DemandIQ_Step7B_Analog_Scorecard.csv`.)*

| Rank | Candidate | Functional | Seasonal fit | Price | Weather | Scale | Channel | **Final** |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | **APS-001** | 0.80 | 0.299 | 0.875 | 0.63 | 0.898 | 0.968 | **0.679** |
| 2 | CTS-001 | 0.70 | 0.064 | 0.750 | 0.60 | 0.540 | 0.968 | **0.531** |
| 3 | IMH-001 | 0.69 | 0.234 | 0.125 | 0.60 | 0.250 | 0.968 | **0.448** |

## 6. Weighted Contribution Analysis

Each contribution = `score × weight`; contributions reconcile to the final score (verified in code).

| Candidate | Func | Seas | Price | Weather | Scale | Channel | **Σ = Final** |
|---|---:|---:|---:|---:|---:|---:|---:|
| APS-001 | 0.240 | 0.075 | 0.131 | 0.095 | 0.090 | 0.048 | **0.679** |
| CTS-001 | 0.210 | 0.016 | 0.113 | 0.090 | 0.054 | 0.048 | **0.531** |
| IMH-001 | 0.207 | 0.058 | 0.019 | 0.090 | 0.025 | 0.048 | **0.448** |

**Reading it:** APS-001's lead comes from functional (0.240), price (0.131) and scale (0.090). IMH-001 is dragged down almost entirely by **price** (0.019 — MSRP 400 vs HIS 750) and **scale** (0.025 — a high-volume midlayer) — dimensions on which it is a *poor scale/price anchor* but which say nothing about its unique **insulation** value. Channel contributes an identical 0.048 to all three (non-discriminating), confirming it cannot separate candidates.

## 7. Seasonal Correlation Evidence

52-week `sku_seasonality_factor` profile correlations (`DemandIQ_Step7B_Seasonal_Correlation.csv`):

| | APS-001 | CTS-001 | IMH-001 |
|---|---:|---:|---:|
| APS-001 | 1.000 | 0.361 | **0.992** |
| CTS-001 | 0.361 | 1.000 | 0.471 |
| IMH-001 | 0.992 | 0.471 | 1.000 |

- **APS vs IMH — 0.99:** nearly identical Fall/Winter shape (both peak ISO wk49). This is critical: **blending APS with IMH does not distort seasonality** — the two carry the same cold-season curve, so IMH adds insulation without corrupting the shape.
- **APS vs CTS — 0.36** and **IMH vs CTS — 0.47:** CTS has a materially different, flatter profile (peak wk45), which is why its cold-season-fit score is low (0.064) despite being a shell.

## 8. Sensitivity Analysis

Five governed scenarios; non-target weights rebalanced proportionally to keep the sum at 1.00 (`DemandIQ_Step7B_Analog_Sensitivity.csv`).

| Scenario | Rank order | Top | Changed? |
|---|---|---|:--:|
| A — Base | APS (0.679) > CTS (0.531) > IMH (0.448) | APS-001 | — |
| B — +0.10 functional | APS (0.696) > CTS (0.555) > IMH (0.482) | APS-001 | No |
| C — −0.10 functional | APS (0.661) > CTS (0.507) > IMH (0.413) | APS-001 | No |
| D — +0.10 seasonal | APS (0.628) > CTS (0.469) > IMH (0.419) | APS-001 | No |
| E — +0.10 price | APS (0.702) > CTS (0.557) > IMH (0.410) | APS-001 | No |

**Stability: STABLE.** APS-001 is the top analog in every scenario, and the full order APS > CTS > IMH never changes. A reasonable planner with modestly different priorities reaches the same primary-analog conclusion. The blend decision (below) is even more robust because it rests on a *structural* attribute gap, not on marginal weight settings.

## 9. Planner Review

Quantitative ranking is documented **separately** from planner judgment. Reviewing the top candidates against HIS-001:

| Lens | APS-001 (score #1) | IMH-001 (score #3) | CTS-001 (score #2) |
|---|---|---|---|
| Functional fit | Strong shell/weather; **weak insulation** | **Strong insulation**; weak shell | Shell only; **no insulation** |
| Seasonal fit | Strong FW (wk49) | Strong FW (wk49) | Weak (wk45, flatter) |
| Commercial (price) | Close to HIS 750 | Far (400) | Close (650) |
| Weather fit | Most relevant | Relevant | Relevant |
| Scale anchor | Good (premium-tier volume) | Poor (high-volume midlayer) | Moderate |
| Complementarity | Needs insulation | **Supplies the missing insulation** | Redundant with APS |

**Judgment:** APS-001 is the right primary — it anchors shell, weather, price, scale, and the FW shape. But an *insulated* shell cannot be represented by shells alone. IMH-001 is the only candidate carrying the insulation attribute, and it does so without seasonal distortion (corr 0.99 with APS). CTS-001, despite the higher score, adds nothing APS does not already provide.

## 10. Single vs Blended Analog Decision

Applying the governed blend rule:

1. Top-ranked candidate **A1 = APS-001**.
2. Material weakness on a defining HIS-001 capability? **Yes — insulation (0.20 vs 0.90).**
3. Does another candidate uniquely fill it? **Yes — IMH-001 (0.95); CTS-001 (0.15) does not.**
4. → **Two-analog blend, APS-001 + IMH-001.**
5. Third analog? **No** — CTS-001 provides no complementary capability; max 2 analogs.

**Option A (single analog APS-001)** was rejected: it would omit insulation, the defining half of the product, and bias the borrowed demand shape toward a non-insulated shell. **Option B (APS + IMH blend)** is selected.

## 11. Final Analog Weights

| Role | Analog | Weight | Justification |
|---|---|---:|---|
| Primary | APS-001 | **0.60** | Higher total score (0.679); anchors shell/weather, price (MSRP closest to HIS), scale, premium positioning, and the FW seasonal shape |
| Secondary | IMH-001 | **0.40** | Uniquely supplies insulation — a co-equal, defining attribute of an *insulated* shell — so it earns substantial (not token) weight; shares APS's FW curve (corr 0.99) |
| — | **Sum** | **1.00** | |

Weights are kept **simple and explainable (0.60/0.40)**, reflecting that HIS-001 is a near-even hybrid while APS remains primary because it carries more of the total analog information (price, scale, seasonality, positioning). No false precision.

## 12. Channel-Mix Prior

Two layers are preserved, not overwritten (`DemandIQ_Step7B_Launch_Assumptions.csv`):

| Channel | A. Analytical analog mix | B. Commercial launch mix (planned) |
|---|---:|---:|
| ECOM | 0.408 | **0.45** |
| RETAIL | 0.324 | **0.35** |
| WHOLESALE | 0.268 | **0.20** |
| **Sum** | **1.00** | **1.00** |

**Analytical prior:** derived from the blended analogs' channel mix. Note the mature SKUs share an identical mix, so **channel mix has low discriminatory value for analog selection** — but it remains important as the allocation starting point.
**Commercial override:** a DTC-led premium-launch adjustment shifts ~7–8 points from WHOLESALE to ECOM/RETAIL, to control brand presentation, capture full-price ASP, and gather first-party sell-through signal early, deferring wholesale scale-up until launch proof. The analytical prior is retained in the register so the override is fully auditable.

## 13. Launch-Scale Assumption

`HIS-001 Base comparable demand = blended-analog comparable demand × base_launch_scale_factor`.

- Blended analog comparable demand (DERIVED context, **not** a HIS forecast) = 0.60 × 28,271 + 0.40 × 72,093 ≈ **45,800 units/yr**.
- **Base launch-scale factor = 0.60** *(SYNTHETIC PLANNING ASSUMPTION)*.

**Rationale:** a new, premium ($750), unproven product with meaningful overlap against existing shells and a DTC-led (initially narrower) distribution should be planned **conservatively** — it does not immediately reach a mature analog's volume. 0.60 is a simple, defensible first-season position. It is **not** fitted to any future HIS outcome, and **no HIS forecast units are produced in Step 7B** (that is Step 7C).

## 14. LOW / BASE / HIGH Adoption Assumptions

| Scenario | Multiplier (× Base) | Meaning |
|---|---:|---|
| LOW | **0.75** | Weak adoption / analog overstatement |
| BASE | **1.00** | Expected launch adoption |
| HIGH | **1.25** | Strong adoption / analog understatement |

**Symmetric ±25% band**, chosen for planner interpretability. Launch-demand uncertainty is genuinely two-sided at the demand level, so the band is symmetric; the **asymmetric *cost* of a miss** (an under-buy on a hit is unrecoverable within lead time, an over-buy becomes markdown) is deliberately handled later in the **initial-buy buffer (Step 7E)**, not by skewing the demand band. These are **SYNTHETIC PLANNING ASSUMPTIONS**, not statistical confidence intervals, and are kept distinct from the weather scenarios (MILD/NORMAL/SEVERE).

## 15. 18-Month Lifecycle Calendar

Anchored to on-sale 2026-08-31; strategic horizon **Sep 2026 → Feb 2028** (`DemandIQ_Step7B_Lifecycle_Calendar.csv`). Month 0 (Aug 2026) is pre-launch context outside the horizon.

| Months | Phase |
|---|---|
| Aug 2026 (idx 0) | PRE-LAUNCH (context) |
| Sep 2026 | LAUNCH |
| Oct–Nov 2026 | RAMP |
| Dec 2026 | SEASONAL PEAK |
| Jan–Jun 2027 | NORMALIZATION |
| Jul 2027–Feb 2028 | SECOND-SEASON / MATURATION |

No forecast units are attached — the calendar defines only the lifecycle structure Step 7C will populate.

## 16. Assumption Register Summary

A 33-row governed register (`DemandIQ_Step7B_Launch_Assumptions.csv`) captures every launch value with `provenance`, `rationale`, `owner_role`, `status`, and `effective_date`. Provenance classes: **DERIVED (frozen mature data)**, **SYNTHETIC PLANNING ASSUMPTION**, **GOVERNANCE ASSUMPTION**, and **NOT YET SET (Step 7D)**. Top-down inputs (category growth, HIS share, merchandising expectation, commercial target) are present as **NOT YET SET** placeholders — deliberately not fabricated in Step 7B.

## 17. Governance / Leakage Controls

- No future HIS launch data, no hidden truth (`true_demand_units`, `lost_demand_units`, `audit_hidden_*`), no generator-only factors, and no future realized weather were used.
- Analog attributes were read from governed planning fields in the frozen Step 3D economics file only.
- Weights and attribute ratings were frozen **before** scoring and are not tuned to any HIS outcome.
- HIS-001 has no history, so nothing about HIS-001 could leak — all HIS values are explicit synthetic assumptions.
- Mature Steps 4A–6F outputs were untouched; all launch outputs live in a separate `launch_step7b` path.

## 18. Limitations

- **Small candidate pool (3 SKUs)** — the selection is interpretable but not statistically powerful; stated plainly.
- **Functional attributes are synthetic** — mitigated by freezing them pre-scoring, by the 0.55 data-derived weight agreeing, and by putting functional first in the sensitivity test.
- **Channel mix is non-discriminating** in this dataset (identical across SKUs) — it informs the allocation prior, not the analog choice.
- **Demand-scale is partly synthetic and mildly circular** — mitigated by the lowest weight and a wide independent HIS band.
- **Launch-scale and adoption multipliers are governed assumptions**, not estimates — to be validated only against evaluation-only truth in later steps.

## 19. Step 7B Conclusion

HIS-001 is set up for cold-start forecasting with a **0.60 APS-001 / 0.40 IMH-001** analog blend — a choice driven by an auditable complementarity rule rather than the raw score, corroborated by a STABLE sensitivity result and near-identical FW seasonality between the two analogs. All governed launch assumptions (channel-mix prior + DTC-led override, 0.60 base scale factor, 0.75/1.00/1.25 adoption band, 18-month lifecycle calendar, and top-down placeholders) are recorded in the assumption register. Step 7B is complete and ready to freeze.

## 20. Exact Next Step

**STEP 7C — Cold-Start & 18-Month Lifecycle Forecast.** Not started. It will apply the blended analog shape × launch scale × seasonality × channel mix × LOW/BASE/HIGH across the frozen lifecycle calendar, with the weather overlay composed on top — producing the first HIS-001 forecast units.

---

*Step 7B decision record. Analog selection is interpretable, data-informed, planner-governed, and auditable. Mature Steps 4A–6F remain frozen and untouched. Every launch value is a labelled synthetic planning assumption.*
