# DemandIQ — Step 7D — Top-Down / Bottom-Up Reconciliation & Consensus Decision Record

**Launch product:** HIS-001 — Hybrid Insulated Shell
**Scope:** 18-month strategic / IBP demand plan (BASE adoption, NORMAL weather). The frozen Step 7C 13-week S&OE forecast is unchanged.
**Step status:** COMPLETE. Steps 7A–7C and the mature engine (4A–6F) remain frozen. No initial-buy, safety-stock, or supply-constrained work is done here (that is Step 7E).

> **Simulation notice.** The top-down plan rests on **SYNTHETIC COMMERCIAL PLANNING ASSUMPTIONS**; V0 is DERIVED from the frozen Step 7C baseline; category context is DERIVED from frozen mature planning data. All versions are **unconstrained demand** — supply is never used to lower demand.

---

## 1. Executive IBP Summary

The bottom-up analytical baseline (V0) and the top-down commercial plan (V1) disagreed by **+10.9%**. Rather than average them, the demand planner applied a governed consensus rule: because the gap fell in the **PLANNER_REVIEW** band, a **bounded** commercial adjustment (capped at +10% from V0) was accepted, and the small residual was flagged to IBP. Management approved the consensus unchanged.

| Version | 12-month | 18-month | vs prior |
|---|---:|---:|---|
| **V0** Analytical baseline | 27,480 | 44,919 | — |
| **V1** Commercial / top-down | 30,476 | 49,816 | +10.9% vs V0 |
| **V2** Consensus | 30,228 | 49,411 | −0.8% vs V1 (bounded to +10% vs V0) |
| **V3** Approved IBP plan | 30,228 | 49,411 | = V2 (approved unchanged) |

Result: **V3 approved unconstrained demand = 49,411 units (18-month), 30,228 (first 12-month)** — a governed +10.0% above the pure analytical baseline, and **within** the frozen LOW/HIGH scenario envelope.

## 2. V0 Analytical Baseline

Loaded from `DemandIQ_Step7C_18M_Analytical_Forecast.csv` (BASE / NORMAL only; LOW/HIGH and MILD/SEVERE remain scenario outputs, not mixed into consensus). Recomputed, not typed: **V0 first-12-month = 27,479.80**, **18-month = 44,918.94**. V0 is the **anchor** and is never overwritten.

## 3. Planning Hierarchy

```
PORTFOLIO
  → TECHNICAL OUTERWEAR CATEGORY
      → HIS-001
          → CHANNEL (ECOM · RETAIL · WHOLESALE)
```

**Bottom-up** builds from SKU × Channel upward (V0). **Top-down** starts from the category/commercial outlook and allocates downward (V1). The two directions are kept explicit and separate.

## 4. Top-Down Category Context

Mature Technical Outerwear annual comparable demand (frozen `weekly_plan_units`, read-only): APS-001 28,270.96 + CTS-001 52,397.39 + IMH-001 72,092.78 = **152,761.14 units/yr**.

**Implied category share of the bottom-up V0 = 27,479.81 ÷ 152,761.14 = 17.99%.** This is a key context point: the analytical baseline already implies HIS would be ~18% of the entire existing mature category in year one — essentially APS-001's full annual volume. The analytical baseline is therefore *already ambitious*, which frames how much additional commercial ambition is reasonable.

## 5. Commercial Planning Assumptions *(SYNTHETIC COMMERCIAL PLANNING ASSUMPTIONS)*

Approved top-down option: **Option B — Planned.**

| Assumption | Value |
|---|---|
| Technical Outerwear category growth | **+5%** |
| Planned HIS-001 category share | **19%** |
| Merchandising ambition | Flagship premium launch, modestly above analytical |
| Channel strategy | Preserve the Step 7B DTC-led 45/35/20 mix (no channel override) |

`V1 12-month target = 152,761.14 × 1.05 × 0.19 = 30,475.85 units.`

Three options were evaluated before selection: A Conservative (+3% growth / 17.5% share → 27,535, +0.2%), **B Planned (30,476, +10.9%)**, C Stretch (+8% / 21% → 34,646, +26.1%, which exceeds the V0 HIGH bound and would escalate). Option B was chosen as commercially plausible while exercising the bounded-override path.

## 6. V1 Commercial Plan

`V1 = V0 × level_factor` with `level_factor = 30,475.85 / 27,479.80 = 1.1090`, applied uniformly to every month and channel. This keeps the disagreement about **level/ambition, not timing** (V0's seasonality and the 45/35/20 mix are preserved). **V1 18-month = 49,816 units** (ECOM 22,417 / RETAIL 17,436 / WHOLESALE 9,963). Owner role: Merchandising / Commercial Planning; approval status: PROPOSED.

## 7. V0 vs V1 Reconciliation

| Level | V0 | V1 | Abs variance | % variance | Direction |
|---|---:|---:|---:|---:|---|
| First 12-month | 27,480 | 30,476 | +2,996 | +10.9% | COMMERCIAL_ABOVE_ANALYTICAL |
| 18-month | 44,919 | 49,816 | +4,897 | +10.9% | COMMERCIAL_ABOVE_ANALYTICAL |

Because V1 is a uniform level scaling, every month carries the same +10.9% → the disagreement is a clean, explainable commercial-ambition gap, not a timing artifact. Channel detail is preserved in the version file.

## 8. Variance / Exception Analysis

Tolerance policy *(governance assumption; set before seeing results)*: **≤±5% WITHIN_TOLERANCE · ±5–15% PLANNER_REVIEW · >±15% IBP_EXCEPTION.** The wider outer band reflects launch uncertainty (V0's own adoption band is ±25%, so a ≤15% commercial disagreement is still inside the plausible demand envelope and merits review, not automatic escalation).

- **All 18 months → PLANNER_REVIEW** (each +10.9%); **0 IBP_EXCEPTION**.
- **Largest monthly disagreement: December 2026, +467 units** (the peak month carries the largest absolute gap).
- Exception content — *WHAT changed:* commercial plan +10.9% above analytical. *WHY it matters:* a ~+2,996-unit first-year demand difference driving category contribution and downstream buy. *WHAT decision:* accept a bounded documented override (per the consensus rule), not escalate.

## 9. Consensus Decision Rules

Consensus is **not** `(V0 + V1)/2`. The governed rule:

1. **V0 is the anchor.**
2. **WITHIN_TOLERANCE (≤5%):** retain V0; commercial view noted without change absent documented evidence.
3. **PLANNER_REVIEW (5–15%):** accept a documented commercial adjustment, **bounded to a maximum ±10% move from V0** without executive sign-off; any excess is escalated.
4. **IBP_EXCEPTION (>15%):** escalate; no automatic move; V0 retained pending explicit approval.
5. **V3** = management approval of V2 (may equal V2).

## 10. V2 Consensus Forecast

The V0→V1 gap (+10.9%) is PLANNER_REVIEW, so the consensus accepts a bounded move capped at **+10%** from V0. **Consensus factor = 1.10.**

| | 12-month | 18-month |
|---|---:|---:|
| V2 consensus | **30,228** | **49,411** |
| vs V0 | +2,748 (+10.0%) | +4,492 (+10.0%) |
| vs V1 | −248 (−0.8%) | −405 (−0.8%) |

The −0.8% pullback from the commercial ask is the visible effect of the governed cap: the planner accepted almost all of merchandising's ambition but held the line at the +10% governance limit, documenting the residual for IBP. Owner role: Demand Planning (consensus facilitator); approval status: CONSENSUS. QA confirms V2 ≠ (V0+V1)/2 (which would be 28,978).

## 11. V3 Approved IBP Plan

Management approved the consensus unchanged, so **V3 = V2 = 30,228 (12-mo) / 49,411 (18-mo)** — no manufactured change. V3 remains an **unconstrained demand plan**; it is not reduced for any anticipated supply limitation (that is evaluated separately in Step 7E). Owner role: Management / IBP; approval status: APPROVED.

## 12. Channel Reconciliation

The 45/35/20 mix is preserved through every version (no channel override proposed). Channel totals reconcile exactly to the SKU total in every month and version. 18-month V3: ECOM 22,235 (45%) · RETAIL 17,294 (35%) · WHOLESALE 9,882 (20%).

## 13. Forecast Version Audit Trail

`DemandIQ_Step7D_Forecast_Versions.csv` (216 rows = 4 versions × 18 months × 3 channels) preserves for every row: version, name, cycle, as-of date, month, channel, units, previous-version units, change units, change %, reason, owner role, approval status, provenance. Any V0→V1→V2→V3 path is traceable — e.g., **Dec 2026 ECOM: 1,927.65 (V0) → 2,137.82 (V1, +10.9%) → 2,120.42 (V2, −0.8% to cap) → 2,120.42 (V3, approved).**

## 14. Scenario-Band Position

Governance diagnostic against the frozen Step 7C envelope: **V3 within V0 LOW/HIGH band = YES** (V3 first-12 30,228 inside 20,610–34,350; V3 18-month 49,411 inside 33,689–56,149). The approved plan is ambitious but stays inside the analytically supported demand range — unlike Option C, which would have breached the HIGH bound.

## 15. IBP Monthly Workflow (synthetic simulation)

| Week | Stage | Input → Decision |
|---|---|---|
| 1 | Demand Review | V0 analytical → Demand Planning recommendation |
| 2 | Commercial / Merchandising Review | V1 top-down → document assumptions & differences |
| 3 | Reconciliation / Supply Review | Demand reconciliation (V0 vs V1); supply kept separate — demand not censored |
| 4 | Executive / Consensus IBP | V2 consensus → V3 approved demand plan |

This is a simulated IBP rhythm for the case study, not a claim about any real company's exact process.

## 16. Forecast Value Add Readiness

The version table carries `actual_demand_units`, `forecast_error_vs_actual`, and `fva_status` fields so V0/V1/V2/V3 errors can later be compared against launch actuals. For now every row is labelled **`NOT YET MEASURABLE - NO LAUNCH ACTUALS`**. No FVA is fabricated.

## 17. Governance / Leakage Controls

No future HIS actuals, no hidden truth (`true_demand_units`, etc.), no realized future weather, and no supply constraint were used. Top-down inputs are explicitly synthetic commercial assumptions. V0 is preserved unchanged from Step 7C; no version overwrites another; every change carries a reason and an owner role. Mature Steps 4A–6F and all Step 7C outputs untouched; Step 7D writes only to `05_outputs/launch_step7d/`.

## 18. Limitations

- Top-down rests on **synthetic commercial assumptions** and a category context of only 3 mature SKUs.
- V0's implied ~18% share is high (analog blend included high-volume IMH) — "ambition" is read in that light.
- V1 uses **uniform level scaling** (no month-specific merchandising phasing applied, though the framework allows it).
- Tolerance bands and the +10% consensus cap are **governance assumptions**, not estimates.
- Uniform scaling makes every month's variance identical; a real merchandising plan might differ by phase.
- **No supply feasibility and no FVA** (no actuals) — both deferred.

## 19. Step 7D Conclusion

HIS-001 now has a governed four-version strategic demand plan: analytical baseline (V0), commercial top-down (V1), a consensus reached by rule rather than by averaging (V2), and an approved unconstrained IBP plan (V3 = 49,411 units, 18-month). The reconciliation demonstrates hierarchy, top-down vs bottom-up variance, a governed tolerance/exception framework, a bounded documented override, a full audit trail, and a scenario-band governance check — all with demand never reduced for supply. QA passed on versions, reconciliation, hierarchy, and governance.

## 20. Exact Next Step

**STEP 7E — Initial Buy & Channel Allocation.** Not started. It will take the approved V3 unconstrained demand and, using a launch-specific buffer (not the mature 2.5-week policy) and supply feasibility, produce the initial buy and its channel allocation — the first point at which supply constraints enter.

---

*Step 7D decision record. V0 preserved; consensus by governed rule, not averaging; V3 is unconstrained demand. Mature Steps 4A–6F and Step 7C remain frozen and untouched. Top-down inputs are labelled synthetic commercial planning assumptions.*
