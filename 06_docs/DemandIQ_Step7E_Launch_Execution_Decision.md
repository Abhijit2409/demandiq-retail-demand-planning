# DemandIQ — Step 7E — Launch Buy, Sell-Through & Reforecast Decision Record

**Launch product:** HIS-001 — Hybrid Insulated Shell
**Step status:** COMPLETE. Two-stage, order-enforced: the pre-launch buy was frozen **before** any launch actuals existed. Steps 7A–7D and the mature engine (4A–6F) remain frozen.

> **Simulation notice.** Supply assumptions and launch actuals are **SYNTHETIC** (seeded, reproducible). Hidden latent demand is **evaluation-only** and never used by the reforecast. Economics are **PLANNING EXPOSURE PROXIES**, not profit. Demand is kept separate from supply.

---

## 1. Executive Launch Decision

The pre-launch buy was frozen at the **BALANCED** position — **8,259 units** (covered demand 7,577 + 9% launch buffer), with a **991-unit flex reserve** and channel pre-allocation ECOM 3,271 / RETAIL 2,544 / WHOLESALE 1,454. After launch, the seeded actuals came in **below the commercially-lifted plan** (realized 6,809 vs plan 7,577; the plan carried the +10% consensus lift). The reforecast correctly pulled demand down to **6,650** by W13, and the planner **HELD** at every checkpoint — no chase, no cut. Fill was **97.7%**. The one blemish: ECOM ran hot and lost **159 units** to a W13 stockout while the reserve sat idle, because the mix deviation (+5.4pp) stayed below the governed 8pp reallocation trigger — a documented threshold-calibration learning.

## 2. Approved Demand Basis

The buy begins from **V3_APPROVED_PLAN** (Step 7D), not V0. Approved weekly plan = Step 7C BASE/NORMAL weekly × the governed **V3/V0 = 1.10**, giving **7,577 units over 13 weeks** (ECOM 3,410 / RETAIL 2,652 / WHOLESALE 1,515), ramping 311 (W1) → 886 (W13). The genuine demand-uncertainty band (Step 7C adoption) is LOW 5,166 / BASE 6,888 / HIGH 8,610.

## 3. Supply Planning Assumptions *(SYNTHETIC — Setup B: Balanced)*

Effective replenishment lead time **~8 weeks** (6 production + 2 transit); PO-change window closes ~4 weeks pre-receipt; chase **≤15%** of the buy; expedite limited; reserve/transfer lead ~2 weeks. A chase is feasible for the launch window **only if ordered by ~W5** (5 + 8 = W13).

## 4. Protected Buy Horizon

Derived, not assumed: with an 8-week effective lead time and the first reforecast at W4, a reactive replenishment cannot arrive until **~W12**. The pre-launch buy must therefore protect the **full 13-week launch window** — lead time, not preference, forces it.

## 5. Launch Buffer

A **launch uncertainty buffer** (9% of covered demand), explicitly **not** the mature 2.5-week safety-stock policy. It is inventory protection sized off the adoption band and service ambition, kept separate from the demand forecast (demand is never inflated to represent buffer).

## 6. Buy Scenario Comparison

| Position | Buffer | Initial buy | Short vs HIGH | Excess vs LOW | Under-buy exp. (CAD) | Over-buy markdown exp. (CAD) | **Two-sided exp.** |
|---|---:|---:|---:|---:|---:|---:|---:|
| LEAN | +4% | 7,880 | −730 | +2,714 | 445,261 | 331,000 | 776,261 |
| **BALANCED** ✔ | +9% | 8,259 | −351 | +3,093 | 214,234 | 377,205 | **591,439** |
| PROTECTIVE | +14% | 8,638 | 0 | +3,472 | 0 | 423,411 | 423,411 |

*(Exposure proxies: under-buy at full net-ASP 610; over-buy at net-ASP × 20% synthetic clearance markdown.)*

## 7. Recommended Initial Buy

**BALANCED (frozen).** Honest reading of the table: because the proxy prices under-buy at full ASP but over-buy at only a 20% markdown, the raw two-sided figure actually favours **PROTECTIVE**. BALANCED was chosen as the governed position because (a) the proxy overstates under-buy cost — a premium launch stockout is partly *deferred* (a second season exists), not fully lost; (b) PROTECTIVE ties up the most capital and carrying cost for only a +13.6% upside; and (c) BALANCED still covers realistic demand while limiting excess. This is a genuine judgment under uncertainty, documented rather than asserted as "optimal."

## 8. Channel Allocation & Reserve

Total buy 8,259 → **flex reserve 991 (12%)** held unallocated; the remaining **7,268 pre-allocated** by the approved 45/35/20: ECOM 3,271 / RETAIL 2,544 / WHOLESALE 1,454. The reserve exists to respond to early channel-mix uncertainty (deploy toward whichever channel runs ahead) — a REALLOCATE lever that avoids a chase. Allocation + reserve reconcile exactly to the buy.

## 9. Pre-Launch Freeze

`prelaunch_buy_frozen = 1` · `buy_freeze_date = 2026-08-24` · `planning_cycle = CYCLE_01_2026-08` · `demand_version_used = V3_APPROVED_PLAN`. Stage B (actuals) runs only after this record exists — enforced by code order.

## 10. Synthetic Launch Realization

Deterministic **seed = 7**. Latent weekly demand = analytical-BASE weekly × a single adoption draw (N(1.0, 0.08) → **1.000**) × weekly noise (N(1, 0.10)) × a channel skew (ECOM hotter, WHOLESALE softer), renormalized so the mix shifts but the SKU total is preserved. **Actuals are centered on the analytical baseline — DemandIQ's unbiased demand expectation — not the commercially-lifted plan**, so the simulation neither assumes the +10% lift was right nor engineers it to look wrong. Observed sales = min(latent, available inventory); hidden latent is evaluation-only. Realized: **truth 6,809 · observed 6,650**; realized mix ECOM 50.4% / RETAIL 34.1% / WHOLESALE 15.6%.

## 11. Sell-Through Performance

Fill rate (observed ÷ latent truth) = **97.7%**. Channel outcome: ECOM sold its full 3,271 allocation and lost **159** more to a W13 stockout; RETAIL 2,319 (excess 225) and WHOLESALE 1,060 (excess 394) finished under-sold. So ~1,610 units (reserve 991 + other-channel excess 619) sat unsold while ECOM lost sales — a channel-mix mismatch the reserve was designed to solve.

## 12. Checkpoint Variance

| Checkpoint | Attainment | Demand var vs plan | Reforecast total | WOS | Exception | Action |
|---|---:|---:|---:|---:|---|---|
| W1 | 93.6% | −6.4% | 7,465 | 27.4 | WATCH | HOLD |
| W2 | 91.0% | −9.0% | 7,310 | 26.4 | WATCH | HOLD |
| W4 | 87.7% | −12.3% | 7,030 | 23.9 | WATCH | HOLD |
| W8 | 89.8% | −10.2% | 6,943 | 10.1 | WATCH | HOLD |
| W13 | 87.8% | −12.2% | 6,650 | 2.2 | WATCH | HOLD |

Demand tracked **~10–12% below the lifted plan** throughout — consistent with the +10% consensus lift being optimistic relative to the analytical baseline.

## 13. Channel Mix Performance

ECOM ran **+5.4pp** above its 45% plan (peaking the mix deviation) with WHOLESALE **−4.4pp** below. Per the pre-registered thresholds (<5pp ON_PLAN · 5–8pp WATCH · ≥8pp REALLOCATE), +5.4pp sat in the **WATCH** band — a monitored REALLOCATE *candidate* below the action trigger. The reserve therefore stayed idle, and ECOM's 159-unit W13 stockout went uncovered. **Learning:** an 8pp reallocation trigger was too coarse for this launch; a lower threshold (or a WATCH-band partial pre-position) would have captured ~159 units. Recorded for the next cycle — not edited retroactively.

## 14. Reforecast Methodology

Interpretable shrinkage from analog prior to observed evidence: `w_actual = n/(n+k)`, **k = 4**. Remaining demand = original remaining plan × [w_actual × attainment + (1−w_actual)]. `w_actual` rises 0.20 (W1) → 0.50 (W4) → 0.77 (W13), so actuals increasingly dominate — no time-series model fit to 1–13 weeks. The original V3 plan and every checkpoint reforecast are preserved.

## 15. W1/W2/W4/W8/W13 Reforecasts

| Version | Remaining/total | Δ vs original | Evidence |
|---|---:|---:|---|
| ORIGINAL_V3_PLAN | 7,577 | 0.0% | none (pre-launch) |
| W1_REFORECAST | 7,465 | −1.5% | 1 obs week |
| W2_REFORECAST | 7,310 | −3.5% | 2 obs weeks |
| W4_REFORECAST | 7,030 | −7.2% | 4 obs weeks |
| W8_REFORECAST | 6,943 | −8.4% | 8 obs weeks |
| W13_REFORECAST | 6,650 | −12.2% | 13 obs weeks |

The long-range signal moved from **MAINTAIN** (W1–W2) to **DECREASE second-season outlook** (W4 onward) — the early evidence that will seed the Cycle-02 rolling forecast in Step 7F.

## 16. Supply Feasibility

No chase was warranted (demand ran below, not above, plan). Had demand run hot, a chase would have been **feasible only if ordered by ~W5** (8-week lead into a 13-week window); a hot signal at W8+ would have produced **ESCALATE**, not an auto-chase — the launch analogue of the frozen P1-ESCALATE boundary: **risk signal ≠ execution authorization**.

## 17. Planner Actions

All five states were implemented (CHASE / HOLD / REALLOCATE / CUT / ESCALATE) with explicit conditions; the realized path produced **HOLD at every checkpoint** (demand modestly soft, coverage ample, mix deviation below the action threshold). No action was forced for storytelling. The honest takeaways are the *non-actions*: the disciplined HOLD avoided over-reacting to a soft-but-stable launch, while the un-triggered REALLOCATE exposed a threshold-calibration gap.

## 18. Initial-Buy Performance

Against the realized launch: initial buy 8,259 · observed sales 6,650 · **ending unsold 1,609** (channel 618 + idle reserve 991) · **lost/under-buy 159** (ECOM stockout) · fill **97.7%**. Both an over-buy (1,609) and a small under-buy (159) coexist — the signature of a mix mismatch, not a level error. The buy is **not** retroactively changed.

## 19. Forecast vs Planning Quality

Deliberately separated:
- **Forecast quality** — the approved plan over-forecast: **WAPE 11.8%, Bias +11.3%** vs the hidden truth. The bias ≈ the +10% commercial lift, i.e., the consensus optimism *added* error over the analytical baseline (a preview of the Step 7F FVA finding).
- **Planning quality** — despite the biased forecast, the buy delivered **97.7% service**; the cost was ~1,600 units of excess (≈19% of the buy) driven by that same optimism, plus 159 lost to the mix gap.

A forecast can be imperfect while the inventory decision still performs acceptably — and vice versa. Here the plan was biased high, service held, and excess was the price of the commercial lift.

## 20. Economic Exposure *(PLANNING EXPOSURE PROXIES)*

Realized proxies at net-ASP 610: under-buy exposure ≈ 159 × 610 ≈ **CAD 97K**; over-buy markdown exposure ≈ 1,609 × 610 × 20% ≈ **CAD 196K**; two-sided ≈ **CAD 293K**. Carrying-cost proxy applies to the ending inventory at 18%/yr. No profit or savings is claimed.

## 21. Governance / Leakage Controls

Buy frozen before actuals; hidden latent demand never used by the reforecast (only observed sales, inventory, availability, elapsed weeks); simulation deterministic (seed 7); observed sales never exceed available inventory; inventory never negative (shortfalls appear as lost demand); channels reconcile to SKU; V0–V3 untouched; economics labelled proxies; mature engine untouched. All Stage-A/Stage-B ordering is visible in code and outputs.

## 22. Limitations

- Single seeded realized path — one draw, not a distribution; a Monte-Carlo sweep would quantify buy-position risk better.
- Supplier and actuals are synthetic; 13-week signal is short.
- The +20% markdown and full-ASP under-buy proxies are governance assumptions that materially shape the exposure ranking (they favour PROTECTIVE).
- The 8pp REALLOCATE threshold proved too coarse for a +5.4pp mix gap — a calibration learning, not a hindsight edit.
- Reserve deployment and chase are modelled simply (single injection points).

## 23. Step 7E Conclusion

HIS-001 now has a complete, governed launch-execution loop: a frozen pre-launch buy (BALANCED 8,259 + 991 reserve), a seeded launch realization centered on the unbiased baseline, interpretable checkpoint reforecasts that pulled demand down from 7,577 to 6,650, and governed planner decisions (HOLD throughout, honestly). It demonstrates the separation of forecast quality (biased high by the consensus lift) from planning quality (97.7% service at the cost of ~19% excess), and surfaces a real reallocation-threshold learning — the kind of honest finding that distinguishes a planning system from a demo.

## 24. Exact Next Step

**STEP 7F — Forecast Value Add, Rolling Forecast Cycle 02 & Lifecycle Handoff.** Not started. It will quantify FVA (comparing V0/V1/V2/V3 and the reforecasts against the realized launch — the +11.3% bias suggests the commercial lift subtracted value), open the next rolling cycle (Oct 2026 → Mar 2028) seeded by the DECREASE second-season signal, and define the handoff into the mature engine.

---

*Step 7E decision record. Buy frozen before actuals; hidden truth evaluation-only; all launch data synthetic; economics are planning exposure proxies. Steps 7A–7D and the mature engine remain frozen and untouched.*
