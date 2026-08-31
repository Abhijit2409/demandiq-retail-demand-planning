# DemandIQ — Step 6D — Executive Findings & Business Recommendations

**Scope:** Business interpretation of the frozen DemandIQ decision engine. Read-only — no analytical file, forecast, classification, or economic value was modified. Every figure below reconciles to the frozen Step 6A decision layer.

**What this is:** a portfolio simulation of a premium outdoor apparel demand-planning problem. Economic figures are **planning exposure proxies, not accounting profit**, and this is **not any real company's internal data**.

**Planning horizon:** 2026-06-29 → 2026-09-21 (13 weeks) · grain: SKU × Channel (9 series).

---

## 1. Executive Summary

Over the next 13 weeks the portfolio is expected to demand ~36,435 units (Base), and aggregate committed supply protects a healthy **98.8% Base fill against a 92% service target** — so at the top line the plan looks comfortable. That headline is misleading: **three of nine SKU-channel series miss the weekly 92% service target twice each**, bottoming at **33.2% fill in a single week (APS-001/WHOLESALE)**, and **all nine series finish the horizon below the 2.5-week safety-stock policy**. The three weekly-risk series alone account for **100% of the ~CAD 192K Base lost-revenue exposure proxy**, concentrated on a shared worst week of **2026-08-24** where every series has zero committed receipts. Because DemandIQ does not model supplier/transfer lead-time feasibility, the engine **releases zero automatic chase and zero reallocation** — the correct response is targeted **S&OE escalation** on the three P1 series and **inventory protection** on the six P2 series, not indiscriminate chasing. The single most important takeaway: **aggregate forecast accuracy and aggregate fill rate are not sufficient for demand planning — weekly execution and forward coverage must be read alongside them.**

---

## 2. 13-Week Portfolio Outlook

| Metric | Value |
|---|---|
| Base demand | **36,434.66 units** |
| Mild demand | 36,036.10 units (−1.09% vs Base) |
| Severe demand | 36,677.25 units (+0.67% vs Base) |
| Scenario width (Severe − Mild) | 641.15 units (~1.8% of Base) |
| Peak Base week | **2026-09-07** (~3,640 units) |

**Business meaning.** Demand rises materially into late August / September, peaking the week of 2026-09-07. The weather-scenario band is **narrow** — roughly ±1% around Base — so scenario uncertainty is *not* the dominant near-term planning problem.

**Planner implication.** Do not over-invest attention in weather-scenario swings. The build-up toward the September peak, combined with **when supply actually arrives**, is the more consequential issue for this horizon. (Governance reminder: Weeks 1–3 are `NOWCAST_REQUIRED` and no live nowcast was supplied, so near-term demand was **not** adjusted with realized future weather; Weeks 4–13 use Mild/Normal/Severe scenario planning.)

---

## 3. Service & Supply Position

| Metric | Value |
|---|---|
| Base projected shipments | 35,987.27 units |
| Base fill rate | **98.77%** (+6.77 pp vs target) |
| Severe fill rate | 98.61% |
| Service target | 92.00% |
| Opening inventory | 9,562.84 units |
| Committed receipts (13W) | 26,597.07 units |
| Available chase capacity | 4,461.84 units (contingency option ~3,229 units) |

**Finding.** On aggregate, opening inventory plus committed receipts comfortably clears the 92% target in both Base and Severe cases.

**Business meaning.** A ~98.8% aggregate fill *looks* like a solved problem — and this is exactly the trap. Aggregate fill is a portfolio-level 13-week service ratio; it can mask acute weekly shortfalls in individual SKU-channel series.

**Planner implication.** Aggregate fill is necessary but **not sufficient** to declare the portfolio healthy. It must be evaluated together with (a) weekly execution service and (b) ending inventory coverage — the next two sections.

---

## 4. Critical Weekly Service Risks (P1 — ESCALATE)

Three series carry `risk_type = WEEKLY_SERVICE_RISK`, `priority_tier = P1`, `planner_action = ESCALATE`:

| SKU | Channel | 13W Fill | Worst Weekly Fill | Worst Week | Gap Units | Weeks Below Target | Ending WOS | Planner Action |
|---|---|---:|---:|---|---:|---:|---:|---|
| APS-001 | WHOLESALE | 93.5% | **33.2%** | 2026-08-24 | 62.5 | 2 | 0.00 | ESCALATE |
| CTS-001 | RETAIL | 95.6% | **65.4%** | 2026-08-24 | 122.8 | 2 | 0.00 | ESCALATE |
| IMH-001 | WHOLESALE | 96.1% | **74.1%** | 2026-08-24 | 78.4 | 2 | 0.00 | ESCALATE |

**Finding.** Each of these series clears the 92% target *on aggregate* (93.5–96.1%), yet each **misses the weekly target in two separate weeks**, with a worst week that shares the same date — **2026-08-24** — and drops as low as one-third fill (APS-001/WHOLESALE).

**Business meaning.** These are the SKU-channel series where the simulation projects service shortfalls, even though their 13-week aggregate fill remains above target (93–96%). The trigger is a governed **synthetic planning rule**: 13-week Base fill ≥ 92% *and* ≥ 2 forecast weeks below 92% (the misses need not be consecutive).

**Planner implication.** These three are the urgent S&OE queue. `ESCALATE` means **escalate for human review and validate a feasible response** — it is deliberately **not** an automatic chase order (see §10). Note the largest single-week gap sits with **CTS-001/RETAIL (122.8 units)**, which also carries the largest exposure (§7) — it should lead the review.

---

## 5. Inventory Coverage Risk (P2 — PROTECT)

The remaining six series carry `risk_type = LOW_COVERAGE_RISK`, `priority_tier = P2`, `planner_action = PROTECT`:

`APS-001/ECOM`, `APS-001/RETAIL`, `CTS-001/ECOM`, `CTS-001/WHOLESALE`, `IMH-001/ECOM`, `IMH-001/RETAIL`.

| Fact | Value |
|---|---|
| Weekly service failures in these six | **None** (100% min weekly fill, 0 weeks below target) |
| Ending WOS range (these six) | 0.28 – 1.25 weeks |
| Safety-stock policy | 2.5 weeks |
| Series finishing below policy (all nine) | **9 of 9** |
| Base safety-stock protection gap (portfolio) | **7,000.21 units** |

**Finding.** These six series are **not** experiencing repeated weekly service failure — their concern is **forward coverage**. Every series (all nine, P1 and P2) ends the horizon under the 2.5-week buffer, and the portfolio-wide shortfall to policy is ~7,000 units.

**Business meaning.** Healthy *current* service and thin *forward* coverage are two different things. A series can be serving customers today while running its buffer down to a level that leaves it fragile to the next demand surprise or receipt slip.

**Planner implication.** The distinction is the core of the plan:
- **P1 = weekly execution / service concern** (customers missed now → escalate).
- **P2 = forward coverage / buffer concern** (buffer too thin → protect).

Do **not** read the six P2 series as stockout failures, and do **not** read their healthy current service as evidence of excess inventory — the opposite is true (they are below policy).

---

## 6. Supply-Timing Observation (2026-08-24)

**Verified from the weekly output:** on **2026-08-24, `committed_receipt_units = 0` for all 9 of 9 series.**

Context (also from the weekly data): committed receipts are **lumpy** — they arrive in only three batches across the 13 weeks (weeks of Jun 29, Jul 27, Aug 31), so many weeks carry zero receipts. What makes 2026-08-24 notable is that it is the **shared worst-service week** for all three P1 series, falling in the gap just before the Aug 31 replenishment.

**Interpretation (disciplined causality).** A shared zero-receipt week **coincides with** localized weekly service failures in the thinner-buffer P1 series, while better-buffered series remain protected through the same week. This is a **structural planning observation**, consistent with the simulation:

> Shared replenishment-timing gap **+** thin channel-specific buffers **→ aligns with** localized weekly service failure.

This is **not** a proven causal claim. Only three of nine series fail on 2026-08-24 despite all nine sharing the zero-receipt week — the differentiator is channel-specific buffer thinness, not the receipt gap alone.

**Planner implication.** The most actionable structural question for the review is whether receipt timing can be pulled earlier (or buffer positioned ahead) for the three thin-buffer channels around that week.

---

## 7. Economic Exposure (planning proxies)

| Measure | Value |
|---|---|
| Base lost-revenue opportunity | **≈ CAD 192,468** |
| Severe lost-revenue opportunity | ≈ CAD 217,867 |
| 13-week Base carrying-cost proxy | ≈ CAD 171,876 |

**What these are.** Directional **planning exposure proxies** used to *prioritize* attention — lost-revenue opportunity = unmet Base/Severe demand valued at planning ASP; carrying-cost proxy = ending inventory value × the 18% annual carrying assumption, pro-rated.

**What these are NOT.** Not accounting profit, not gross margin, not actual realized revenue, not audited financial impact, and not any real company's results. **COGS is unavailable**, so no profit statement is possible.

**Finding that sharpens the priority.** The entire **CAD 192,468 Base lost-revenue exposure sits in the three P1 series** — the six P2 series contribute ~0 at Base (they have no Base lost demand). Within the P1 group the exposure is highly concentrated:

| P1 series | Base lost-revenue proxy | Share |
|---|---:|---:|
| CTS-001 / RETAIL | ≈ CAD 123,856 | **~64%** |
| APS-001 / WHOLESALE | ≈ CAD 35,175 | ~18% |
| IMH-001 / WHOLESALE | ≈ CAD 33,437 | ~17% |

**Planner implication.** Exposure prioritization and service prioritization point to the same place — the P1 queue — and specifically nominate **CTS-001/RETAIL** as the single highest-value review, even though APS-001/WHOLESALE has the lower fill rate.

---

## 8. Recommended Planner Actions

### A. IMMEDIATE — Escalate (the three P1 series)
- Escalate `APS-001/WHOLESALE`, `CTS-001/RETAIL`, `IMH-001/WHOLESALE` into the next S&OE review; lead with **CTS-001/RETAIL** (largest gap and ~64% of exposure).
- Validate **receipt timing** around 2026-08-24 — can any committed receipt be pulled earlier into the pre-Aug-31 gap?
- Validate **feasibility** of supplier expedite / inter-channel transfer for the affected weeks (lead times are outside the model — this must be checked with the supply team).
- Inspect the actual available buffer entering the risk weeks before authorizing any supply action.
- **Do not auto-release chase.** Chase capacity of ~1,177 units is allocated across the three P1 series (their frozen contingency chase option is 0), but it is intentionally **held** pending feasibility (see §10).

### B. PROTECT — Coverage (the six P2 series)
- Preserve existing inventory buffers; avoid unnecessary depletion of the six `LOW_COVERAGE_RISK` series.
- Retain contingency chase capacity rather than releasing it merely to top up the safety-stock buffer.
- Monitor ending WOS against the 2.5-week policy; treat below-policy coverage as a watch item, **not** as excess.
- Do not reallocate away from these series on the basis of their currently healthy weekly service.

### C. MONITOR — Demand & Weather
- Refresh the Weeks 1–3 outlook **once a genuine point-in-time nowcast is available** — none exists today, so no near-term weather adjustment is claimed.
- Continue Mild/Normal/Severe scenario planning for Weeks 4–13; the band is narrow, so watch for *deviation from Base around the 2026-09-07 peak* more than for scenario spread.
- Re-check whether any scenario movement materially changes forward coverage for the thin-buffer channels.

---

## 9. S&OE / IBP Discussion Agenda

A concise agenda a planner can take into the review:

1. **Receipt timing vs peak:** Is committed-receipt timing aligned with the 2026-09-07 demand peak, or does supply land too late?
2. **The Aug 24 gap:** Why is 2026-08-24 uncovered by committed receipts, and can any receipt be pulled forward for the three P1 channels?
3. **Channel buffers:** Which channels (WHOLESALE on APS/IMH, RETAIL on CTS) carry insufficient incoming buffer, and why are those the thin ones?
4. **Contingency chase:** Should the ~3,229-unit contingency chase option remain reserved, and under what trigger would it be released?
5. **Feasible interventions:** For each P1 series, is there a *feasible* expedite or transfer path within lead-time — or is protection the only realistic lever?
6. **Safety-stock policy fit:** Is the 2.5-week policy appropriate per channel, given that all nine series finish below it?
7. **Commercial prioritization:** If capacity is constrained, which P1 series wins — service-led (APS-001/WHOLESALE at 33.2%) or exposure-led (CTS-001/RETAIL at ~CAD 124K)?

*(No supplier facts, capacities, or operational constraints are asserted here — these are questions for the people who hold that data.)*

---

## 10. Decision Boundaries & Limitations

DemandIQ **models**: demand, forecast uncertainty, inventory, committed receipts, service/fill, weeks of supply, risk classification, planner priority, and planner action.

DemandIQ **does not model**: supplier lead time, expedite lead time, transfer transit time, PO-modification windows, vendor capacity, or execution cost by intervention type.

Therefore:
- **`P1 ESCALATE` = urgent human S&OE review, not an automatic chase order.** Risk detection and execution authorization are **intentionally separated** — a governance strength, not a gap. The engine will not "fix" a weekly miss by releasing supply it cannot prove is feasible.
- Weeks 1–3 require an **actual nowcast**; none was supplied, so no near-term weather adjustment is made.
- No hidden synthetic truth (`true_demand_units`, generator-only variables) and no realized future weather are used anywhere in this interpretation.
- Economic figures are **planning exposure proxies**, not accounting profit (COGS unavailable).
- This is a **portfolio simulation**, not real company data or performance.

---

## 11. Executive Takeaway

DemandIQ shows why aggregate forecast and fill-rate performance are **not enough** for demand planning. At the top line the portfolio looks healthy — ~36.4K units of demand and 98.8% fill against a 92% target — yet the weekly service diagnostics and ending-coverage view expose **three urgent execution risks** (all failing weekly service around 2026-08-24, and carrying 100% of the ~CAD 192K exposure proxy) and **six additional protection risks** (all finishing below the 2.5-week buffer). The right response is **targeted S&OE escalation and disciplined inventory protection — not indiscriminate chasing** — and, critically, the model **detects** these risks but leaves **execution authorization to the planner**, because supplier and transfer feasibility live outside the model.

---

*Step 6D deliverable — executive interpretation only. Frozen Steps 4A–6C untouched. New Product Launch Planning remains a future, separate analog/cold-start extension and is not part of this step.*
