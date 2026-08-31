# DemandIQ — Portfolio Case Study

### A 13-week demand-planning & S&OE decision system for a premium outdoor apparel portfolio

*A deeper narrative companion to the root `README.md`. Where the README is the recruiter landing page, this document is written for an interview conversation — it explains the reasoning, the trade-offs, and why each design choice is defensible.*

> **Simulation notice.** DemandIQ is a portfolio simulation inspired by a premium outdoor apparel operating model. It does not use or represent real Arc'teryx internal data. All economic figures are **planning exposure proxies, not accounting profit** (COGS is unavailable). Every number below reconciles to the frozen Step 6A decision layer.

---

## 1. Business context

Premium outdoor apparel is a seasonal, high-consideration category: technical shells and insulated layers sell hardest into cold, wet, transitional weather, across three very different channels (own e-commerce, own retail, and wholesale partners). A demand planner in this business is judged on **service** — is the right product available in the right channel when demand arrives — while carrying inventory efficiently across a portfolio.

DemandIQ models a focused slice of that world: three mature products (Alpine Performance Shell, Core Technical Shell, Insulated Midlayer Hoody) across three channels, planned over a 13-week window (**2026-06-29 → 2026-09-21**) that runs into the autumn demand build. The forecasting grain is **SKU × Channel — nine series** — with ~260 weeks of history behind it.

## 2. The planning problem

The project exists because two realities break the naive "forecast the sales history" approach:

**Sales are censored by inventory.** When a product stocks out, observed sales stop reflecting true demand. If you forecast raw sales, you teach the model that constrained weeks were genuinely low-demand weeks and you systematically under-plan the very products that were selling best.

**A forecast is not a decision.** Even a perfect forecast leaves the planner's real questions unanswered: is there enough inventory, when does committed supply land, which SKU-channel series will miss service, and what should be done — chase, protect, or escalate?

DemandIQ is built to answer the *decision*, not just the forecast — connecting demand → forecast → inventory → supply → service → risk → action in one governed pipeline.

## 3. Analytical design

I designed the engine as a sequence of governed, individually-frozen steps, so every later decision traces back to an auditable source:

| Step | What it produces |
|---|---|
| 4A | Reconstructed demand (removes stockout censoring) |
| 4B | Champion forecast model per series (common backtest) |
| 4C | Weather scenario framework (Mild / Normal / Severe) |
| 4D | Final 13-week forecast (9 series × 13 weeks = 117 rows) |
| 5 | Inventory + committed-supply simulation → risk classification + planner action |
| 6A | Presentation-ready decision layer (executive / series / weekly) |
| 6B–6C | Streamlit S&OE control tower |

A design principle throughout: **defensible over sophisticated.** I preferred the simplest model or rule that survived a fair test, and I documented every override rather than hiding it.

## 4. Demand reconstruction

I compared three reconstruction approaches under one evaluation — naive in-stock-days gross-up, regression imputation, and seasonal-profile imputation — and selected **seasonal-profile imputation**:

| Metric (censored rows) | Value |
|---|---:|
| WAPE | ≈ 26.08% |
| Bias | ≈ −2.61% |
| Lost-demand recovery | ≈ 95.68% |
| Full-stockout recovery | ≈ 98.43% |

The naive gross-up over-corrected on partially-constrained weeks; seasonal-profile imputation gave the best balance of recovery and error with near-neutral bias. The reconstructed series (`reconstructed_demand_units`) becomes the forecast target.

**Governance point I'd raise in an interview:** the simulation carries a hidden "true demand" series, but I use it **only to score the reconstruction** — never as a forecast feature. Reconstructed demand is a *modeled estimate*, and I don't claim it equals real-world truth.

## 5. Forecasting & backtesting

Every series ran through an identical, honest backtest: weekly data, 52-week seasonal period, 104-week initial train, **13-week horizon, 12 expanding-window folds**, WAPE as the primary metric with bias tracked separately.

**Final champions (frozen):**

| SKU | Channel | Champion | WAPE | Bias |
|---|---|---|---:|---:|
| APS-001 | ECOM | HW_Damped_Mul | 10.55% | −3.09% |
| APS-001 | RETAIL | HW_Damped_Mul | 8.83% | −0.97% |
| APS-001 | WHOLESALE | HW_Damped_Add | 18.26% | −0.35% |
| CTS-001 | ECOM | HW_Damped_Mul | 8.37% | −1.12% |
| CTS-001 | RETAIL | HW_Damped_Mul | 9.18% | +0.80% |
| CTS-001 | WHOLESALE | Seasonal_MA_2Y | 21.73% | +2.41% |
| IMH-001 | ECOM | HW_Damped_Mul | 8.68% | −1.32% |
| IMH-001 | RETAIL | HW_Damped_Mul | 8.48% | −1.21% |
| IMH-001 | WHOLESALE | HW_Add_Add | 18.55% | +1.41% |

**Mix: 8 ETS · 1 baseline · 0 SARIMA.** Two decisions worth defending:

- **Wholesale WAPE is higher (18–22%) and that's fine.** Wholesale ordering is lumpier than DTC; I did not tune models to flatter those numbers, because the honest backtest is more valuable than a prettier scorecard.
- **A moving-average baseline won CTS-001/WHOLESALE outright**, and I kept it. Where SARIMA beat ETS by only ~0.06 pp WAPE (IMH-001/ECOM), I retained the simpler ETS. The objective was the most defensible model *per series*, not one sophisticated model everywhere.

## 6. Weather scenario planning

Weather is real signal in this category, but it is dangerous to over-use:

- **Weeks 1–3 — `NOWCAST_REQUIRED`.** Near-term weather is only applied if a genuine point-in-time nowcast exists. None was supplied, so I did **not** adjust the near-term forecast — inventing a nowcast would be leakage dressed up as insight.
- **Weeks 4–13 — Mild / Normal / Severe scenarios** from seasonal analogs, keeping cold, rain, snow, wet+cold, and wind as separate dimensions rather than a single weighted index.

The scenario band is deliberately bounded: the SKU caps are **planning assumptions, not empirically estimated elasticities**, and **no realized future weather** enters any forecast. In this horizon the resulting Mild–Severe spread is narrow (±~1% of Base), which is itself a finding: weather uncertainty is *not* the dominant near-term risk here.

## 7. Inventory / supply decision engine

Step 5 simulates each series forward: opening inventory + committed receipts + returns-restock, against Base/Mild/Severe demand, producing weekly fill, ending inventory, and weeks of supply — then classifying risk and assigning a planner action.

**Portfolio supply position:**

| | |
|---|---:|
| Opening inventory | 9,562.84 units |
| 13-week committed receipts | 26,597.06 units |
| Available chase capacity | 4,461.84 units |
| Base projected shipments | 35,987.27 units |

The risk hierarchy (highest first): BASE_SERVICE_RISK → **WEEKLY_SERVICE_RISK (P1)** → **LOW_COVERAGE_RISK (P2)** → SEVERE_SCENARIO_RISK → EXCESS_INVENTORY_RISK → BALANCED. The critical piece is the **weekly-service diagnostic**, added because a 13-week aggregate fill can hide acute single-week stockouts.

## 8. Key findings

**Finding 1 — Aggregate health hides weekly risk.** Portfolio Base fill is **98.77%** against a 92% target, but three series miss the *weekly* target twice each:

| SKU | Channel | 13W Fill | Worst Weekly Fill | Worst Week | Gap (units) | Weeks Below | Ending WOS | Action |
|---|---|---:|---:|---|---:|:--:|---:|---|
| APS-001 | WHOLESALE | 93.5% | 33.2% | 2026-08-24 | 62.5 | 2 | 0.00 | ESCALATE |
| CTS-001 | RETAIL | 95.6% | 65.4% | 2026-08-24 | 122.8 | 2 | 0.00 | ESCALATE |
| IMH-001 | WHOLESALE | 96.1% | 74.1% | 2026-08-24 | 78.4 | 2 | 0.00 | ESCALATE |

**Finding 2 — A shared supply-timing signal.** Committed receipts are lumpy (three batches across 13 weeks). **2026-08-24 has zero committed receipts across all nine series**, and it is the shared worst-service week for all three P1 series. Disciplined reading: the zero-receipt week *coincides with* localized failures in thin-buffer series while better-buffered series hold — a structural planning signal, **not proven causality** (all nine share the gap; only three break).

**Finding 3 — Coverage is thin everywhere.** **All nine series finish below the 2.5-week safety-stock policy** (~7,000-unit portfolio gap). The six non-P1 series are `LOW_COVERAGE_RISK / P2 / PROTECT`: `APS-001/ECOM`, `APS-001/RETAIL`, `CTS-001/ECOM`, `CTS-001/WHOLESALE`, `IMH-001/ECOM`, `IMH-001/RETAIL`. Their concern is **forward coverage**, not current repeated failure — a genuinely different risk from P1.

**Finding 4 — Exposure concentrates.** The entire Base lost-revenue exposure proxy sits in the three P1 series, and it is lopsided:

| P1 series | Base lost-revenue proxy | Share |
|---|---:|---:|
| CTS-001 / RETAIL | ≈ CAD 123,856 | ~64% |
| APS-001 / WHOLESALE | ≈ CAD 35,175 | ~18% |
| IMH-001 / WHOLESALE | ≈ CAD 33,437 | ~17% |

Service priority and economic priority agree — and both nominate **CTS-001/RETAIL** as the single most important review, even though APS-001/WHOLESALE has the lower fill rate.

## 9. Planner recommendations

**ESCALATE (P1 — 3 series).** Take the three weekly-risk series into S&OE; validate receipt timing around 2026-08-24, supplier/expedite/transfer feasibility, and the buffer entering the risk week before any supply action. Lead with CTS-001/RETAIL.

**PROTECT (P2 — 6 series).** Preserve buffers and retain contingency chase; do not read healthy current service as excess. Monitor ending WOS against the 2.5-week policy.

**MONITOR (demand & weather).** Refresh Weeks 1–3 once a real nowcast exists; watch deviation from Base around the 2026-09-07 peak; the scenario band is narrow, so spread is a secondary concern.

## 10. Business impact / exposure

| Measure (planning proxy) | Value |
|---|---:|
| Base lost-revenue opportunity | ≈ CAD 192,468 |
| Severe lost-revenue opportunity | ≈ CAD 217,867 |
| 13-week carrying-cost proxy | ≈ CAD 171,876 |

These are **directional prioritization measures**, not profit, realized loss, or savings. Their value is in *ranking attention*: they quantify why the P1 queue — and CTS-001/RETAIL within it — deserves the planner's first hour. I would not present these as financial results, and I say so explicitly.

The engine's headline governance outcome: **immediate chase = 0 and immediate reallocation = 0.** The plan flags ~CAD 192K of exposure and still authorizes no automatic supply — because it can detect the risk but cannot prove the fix is feasible.

## 11. Governance & limitations

**Detection ≠ authorization.** `P1 ESCALATE` means *urgent human review*, not an auto-chase. Supplier lead time, expedite lead time, transfer transit time, PO-change windows, and vendor capacity are **not modeled**, so the engine deliberately stops at escalation. Separating risk detection from execution authorization is the governance idea I'm most proud of.

**Other limitations:** Weeks 1–3 need an actual nowcast; economics are exposure proxies (no COGS); mature products only; and the whole thing is a **simulation**, not real company data or performance. Hidden synthetic truth and realized future weather are never used as inputs.

## 12. What I would build next

1. **Execution-feasibility layer** — model supplier/expedite/transfer lead times so a P1 escalation can become a *validated* chase/transfer recommendation, closing the detection→authorization gap on purpose.
2. **Weather nowcast integration** — a genuine point-in-time nowcast for Weeks 1–3, replacing the deliberate near-term gap.
3. **New Product Launch Planning** — a separate analog / cold-start workflow (analog selection → initial buy → launch monitoring → reforecast → chase/hold/cut), kept analytically distinct from mature-product time-series forecasting.

---

*The single sentence I'd want a hiring manager to remember: DemandIQ shows why aggregate forecast and fill-rate performance are not enough for demand planning — the portfolio looks healthy at the top, but weekly service and forward coverage reveal three urgent execution risks and six protection risks, and the right response is targeted S&OE escalation and inventory protection rather than indiscriminate chase.*
