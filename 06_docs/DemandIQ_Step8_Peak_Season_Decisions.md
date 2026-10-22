# DemandIQ · Step 8 · Peak-Season Decisions

> **Simulation notice.** Portfolio simulation; no real company data. Rebuild every number with `python 04_scripts/run_pipeline.py --check` (see [Reproducibility](./DemandIQ_Reproducibility.md)).
>
> **Retrospective decision case.** The recommendation is evaluated at the published plan's as-of date, **June 29, 2026**. Every order and chase deadline below (Jun 29 – Oct 5, 2026) had passed by the time of writing (October 21, 2026). The page shows what the planner should have decided on June 29, not actions still open.
>
> **Two kinds of evidence, kept apart.** The recommendation, the decision table and the series tables use only what a planner can observe: sales, in-stock days, receipts, inventory, buys and reconstructed demand. *Simulation truth* (true and lost demand, which no planner sees) appears only in **Why**, to size the problem, and in **Validation**, to score the recommendation.

## The decision

**On June 29, 2026, the planner should have planned the Dec–Feb peak on reconstructed demand, not last year's sales.** Evaluated at that date, the indicative scenario for the coming peak is **+10,339 units (+22% on last season's Dec–Feb sales)**:

- **4,574 moved forward:** spring replenishment shipped before the peak instead of after it.
- **5,613 new.**
- **152 accepted as a gap,** in CTS-001 ECOM, where the excess guardrail blocks new units.

**The scenario is indicative, and its deadlines were tight even at the planning date.**

- **Arrival:** the units had to land before last season's first stockout week, one year on: Nov 30 or Dec 14, 2026.
- **Orders:** on the 22-week overseas lane, that meant committing them by **Jun 29, 2026 for six series and Jul 13 for three**. Those were the first two weeks of the 13-week plan, which the published version spent on summer exceptions.
- **Moved units:** the regular October-drop order date (Apr 27) had already passed, so the moved units needed suppliers to ship early. DemandIQ does not model that, so it stays an open assumption.
- **Fallback:** if neither early shipping nor a new overseas order had been possible, chase alone could have landed about **4,355 units**, ordered by Sep 21 or Oct 5, 2026, within last season's unused chase capacity.

All of these dates have now passed.

![Peak-season fill fell from 86% to 78% in four plan years](../08_assets/charts/step8_fill_trend.png)

## Why

| Finding | Value | Evidence |
| --- | --- | --- |
| Dec–Feb fill, PY2022 → PY2026 | 85.9% → 78.1% | Simulation truth |
| The same, as a planner measures it (sales ÷ reconstructed demand), PY2026 | 82.6% | Observable |
| Lost revenue, PY2026 | CAD 6.65M, 9.1% of net revenue (an upper bound: no substitution assumed) | Simulation truth |
| Share of lost units in Dec–Feb, PY2026 | 83% | Simulation truth |
| Buy basis vs last year's reconstructed demand, PY2026 | −9.0%: each buy starts from last year's sales | Observable |
| Reconstructed vs sold demand: last summer's S&OE window / Dec–Feb | +0.4% / +21.0% | Observable |
| Chase: median first trigger | Plan week 11.5 (mid-September), before any peak stockout | Observable |
| Chase trigger rate, lowest- vs highest-loss quartile | 75% vs 77%; early shipments 0.97 vs 1.02 of plan, so the signal can't tell the cells apart | Observable (quartiles set by truth) |
| Unused chase capacity, PY2026 | 5,403 units | Observable |

## Decision table

Deadlines are as evaluated at the June 29, 2026 planning date; all have passed.

| # | Decision | Quantity | Deadline at the planning date · owner | Guardrail | Confidence |
| --- | --- | --- | --- | --- | --- |
| 1 | Plan the peak on reconstructed demand, moving stock before buying | Indicative +10,339 units: 4,574 moved, 5,613 new, 152 accepted gap | Supplier commitment by Jun 29 (6 series) or Jul 13, 2026 (3 series) · planner proposes, Manager of Merchandise Planning approves, supply planning confirms early shipping and capacity | No new units where over-buy exposure ≥ 50% of estimated lost revenue (a policy assumption to set with finance); season-end cover ≤ 8 weeks | Direction: high (calls and priority match the simulation 9 of 9). Size: indicative; early shipping and supplier capacity are unconfirmed |
| 2 | Size chase from the peak gap, not from early shipments | Fallback floor of about 4,355 units within last season's unused capacity; above that, needs supplier capacity | Chase order by Sep 21 (6 series) or Oct 5, 2026 (3 series), so it lands before the first stockout · planner with supply planning | Chase ≤ 8% of commitment | Medium: last season's headroom is only an indicator |
| 3 | Rank exceptions by stockout days, by SKU × region × channel | Top 20 of 81 cells by stockout days (ties broken by sales) | Each monthly S&OP · Demand Planner | – | Good: those 20 cells capture 53.4% of true lost revenue, against 60.2% for the true top 20 (rank correlation 0.90; 15 of 20 cells shared) |
| 4 | Replace the summer escalation list | Corrected Step 5, counting 6,512 in-transit units: 0 ESCALATE, 7 PROTECT, 2 HOLD. The error-band check adds 1 WATCH (APS-001 Wholesale, short only if demand runs 18% above forecast). The published list had 3 ESCALATE | Weekly S&OE · planner decides, supply confirms the in-transit orders | Re-check weekly as replenishment confirms | Medium: the in-transit estimate repeats last year's pattern. No escalation returns within its backtest error; the protect/hold call for 3 series does |
| 5 | Launch reserve-release rule | Hold the 991-unit reserve (12% of the 8,259-unit buy) centrally; release it to any channel running 5+ pp above planned mix at W1–W2 | Launch checkpoints W1–W2 · planner with merchants | Total launch inventory unchanged | Medium: one seeded launch. The rule fires at W1 (ECOM +5.4 pp) |

## The 13-week queue after the supply fix

The published 13-week plan (v1) counted only the seasonal drops as supply, and it escalated three series for August–September misses. Step 5 now also counts replenishment already in transit at the forecast origin.

- **Estimate.** Last year's replenishment in the same weeks, shifted 52 weeks and grown.
- **Timing.** Under the replenishment policy, nothing can be ordered inside the window, so all **6,512 units** arrive by **Jul 13, 2026**, ahead of the weeks they serve.
- **Result.** Service then holds in every week and no series is escalated.

Step 8B (`DemandIQ_Step8B_Step5_Reconciliation.csv`) compares that corrected engine with Step 8's error-band queue, series by series:

| Series | Published (v1) | Step 5, corrected | Step 8, error band | Why they differ |
| --- | --- | --- | --- | --- |
| APS-001 ECOM | PROTECT | PROTECT (cover 2.24 wk) | PROTECT | – |
| APS-001 Retail | PROTECT | PROTECT (1.64 wk) | PROTECT | – |
| APS-001 Wholesale | ESCALATE | PROTECT (0.74 wk) | WATCH | Step 8 tests the forecast-error band. At +18% demand this series misses 92% in 2+ weeks (worst week 32%). Step 5 plans on the point forecast. Both protect stock and neither escalates |
| CTS-001 ECOM | PROTECT | HOLD (2.77 wk) | No action | – |
| CTS-001 Retail | ESCALATE | PROTECT (1.80 wk) | PROTECT | – |
| CTS-001 Wholesale | PROTECT | HOLD (3.18 wk) | No action | – |
| IMH-001 ECOM | PROTECT | PROTECT (2.06 wk) | PROTECT | – |
| IMH-001 Retail | PROTECT | PROTECT, severe-weather test (2.55 wk base, 2.48 severe) | No action | Only Step 5 runs a weather scenario, and it takes cover under the 2.5-week policy |
| IMH-001 Wholesale | ESCALATE | PROTECT (1.75 wk) | PROTECT | – |
| **Total** | **3 escalate, 6 protect** | **0 escalate, 7 protect, 2 hold** | **0 escalate, 1 watch, 5 protect, 3 no action** | **7 of 9 agree** |

Step 8 holds restocked returns at the v1 values. Step 5 recomputes them from the higher shipments, so ending cover differs by at most 0.015 weeks. In S&OE, run the stricter of the two calls: 1 WATCH (APS-001 Wholesale, also below cover policy), 6 PROTECT, 2 no action.

**How firm is it?**

- **Backtest.** The in-transit estimate was backtested on three earlier plan years. Its series-level error was 15–30%, and 100% of the replenishment landed in weeks 1–3 each year.
- **Volume stress.** At ±29.5% (the worst series error), no series escalates, but the protect/hold call flips for CTS-001 ECOM, CTS-001 Wholesale and IMH-001 Retail.
- **Timing stress.** Moving every in-transit unit to the last possible week changes nothing.
- **Margin on the escalations.** The three v1 escalations clear with 6%, 10% and 30% of the estimated in-transit units.

## Peak scenario by series (observable inputs only)

| Priority | Series | Dec–Feb sales | Reconstructed demand | Gap | Change, units | Moved | New | Accepted gap | Call | Estimated lost revenue | Over-buy ÷ estimated lost revenue |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| 1 | IMH-001 ECOM | 10,815 | 13,026 | +20.4% | 2,355 | 1,308 | 1,047 | 0 | Buy and re-time | CAD 977K | 0.16 |
| 2 | APS-001 ECOM | 4,298 | 5,221 | +21.5% | 960 | 593 | 367 | 0 | Buy and re-time | CAD 918K | 0.15 |
| 3 | APS-001 Retail | 2,899 | 3,820 | +31.8% | 958 | 343 | 615 | 0 | Buy and re-time | CAD 900K | 0.10 |
| 4 | IMH-001 Retail | 8,274 | 9,775 | +18.1% | 1,599 | 674 | 925 | 0 | Buy and re-time | CAD 755K | 0.18 |
| 5 | IMH-001 Wholesale | 5,105 | 7,445 | +45.8% | 2,492 | 927 | 1,565 | 0 | Buy and re-time | CAD 568K | 0.08 |
| 6 | CTS-001 Retail | 3,815 | 4,406 | +15.5% | 625 | 161 | 464 | 0 | Buy and re-time | CAD 416K | 0.35 |
| 7 | APS-001 Wholesale | 2,447 | 3,111 | +27.2% | 690 | 212 | 478 | 0 | Buy and re-time | CAD 390K | 0.11 |
| 8 | CTS-001 Wholesale | 2,870 | 3,192 | +11.2% | 341 | 189 | 152 | 0 | Buy and re-time | CAD 284K | 0.25 |
| 9 | CTS-001 ECOM | 5,946 | 6,248 | +5.1% | 319 | 167 | 0 | 152 | Re-time only | CAD 240K | 1.10 |
| | **Total** | | | | **10,339** | **4,574** | **5,613** | **152** | | | |

**How the numbers are built (all observable):**

1. **Change** = (reconstructed − sold) Dec–Feb units last season × (1 + SKU growth).
2. **Regions** receive the change in proportion to their Dec–Feb stockout days. The by-region file is `DemandIQ_Step8_Peak_Buy_by_Region.csv`.
3. **Moved:** in each region, stock that was still unsold at season end *and* arrived as spring replenishment can ship before the peak instead.
4. **New:** whatever the moved stock doesn't cover.
5. **Guardrail:** no new units where inventory-based over-buy exposure is already ≥ 50% of estimated lost revenue (reconstructed minus sold units for the year, at net price). The remainder there is an accepted gap.
6. **Call:** named from the quantities, so a label can't contradict its numbers.

## Receipt-date and supply check, at the June 29, 2026 planning date

| Series | Must land by | Last 22-week order date (days left on Jun 29) | Last chase order date | New units vs last season's unused chase | Chase-only floor |
| --- | --- | --- | --- | --- | ---: |
| IMH-001 ECOM | Dec 14, 2026 | Jul 13 (14) | Oct 5 | 1,047 vs 1,302: fits | 1,301 |
| APS-001 ECOM | Dec 14, 2026 | Jul 13 (14) | Oct 5 | 367 vs 722: fits | 721 |
| APS-001 Retail | Nov 30, 2026 | Jun 29 (0) | Sep 21 | 615 vs 200: exceeds | 199 |
| IMH-001 Retail | Nov 30, 2026 | Jun 29 (0) | Sep 21 | 925 vs 911: exceeds | 910 |
| IMH-001 Wholesale | Nov 30, 2026 | Jun 29 (0) | Sep 21 | 1,565 vs 390: exceeds | 390 |
| CTS-001 Retail | Nov 30, 2026 | Jun 29 (0) | Sep 21 | 464 vs 826: fits | 625 |
| APS-001 Wholesale | Nov 30, 2026 | Jun 29 (0) | Sep 21 | 478 vs 170: exceeds | 169 |
| CTS-001 Wholesale | Nov 30, 2026 | Jun 29 (0) | Sep 21 | 152 vs 41: exceeds | 40 |
| CTS-001 ECOM | Dec 14, 2026 | Jul 13 (14) | Oct 5 | no new units | 0 |

**Moved units:** last season, half of the spring replenishment had arrived by Apr 13–27. Moving it before the peak meant landing it 17–21 weeks earlier, so suppliers had to ship part of the season commitment ahead of schedule. **Open:** order-change windows are not modelled.

**New units:** on the plan date, a 22-week order was still possible (0–14 days left), but supplier capacity is not modelled (**open**). On the chase lane, they fit last season's unused capacity in 3 of 8 series.

**Floor:** if neither early shipping nor a new overseas order had been possible, chase alone could have landed about 4,355 units, with orders due by Sep 21 or Oct 5, 2026.

## Validation against simulation truth

Truth is used here only to score the recommendation above; nothing in it feeds back.

| Series | Planner gap ÷ true gap | Priority: planner / truth | New units in the change: planner / truth quantity share | Same call with true demand |
| --- | ---: | ---: | ---: | --- |
| IMH-001 ECOM | 74% | 1 / 1 | 44% / 24% | Yes |
| APS-001 ECOM | 81% | 2 / 2 | 38% / 35% | Yes |
| APS-001 Retail | 87% | 3 / 3 | 64% / 66% | Yes |
| IMH-001 Retail | 90% | 4 / 4 | 58% / 44% | Yes |
| IMH-001 Wholesale | 69% | 5 / 5 | 63% / 48% | Yes |
| CTS-001 Retail | 71% | 6 / 6 | 74% / 10% | Yes |
| APS-001 Wholesale | 68% | 7 / 7 | 69% / 73% | Yes |
| CTS-001 Wholesale | 50% | 8 / 8 | 45% / 27% | Yes |
| CTS-001 ECOM | 85% | 9 / 9 | 0% / 54% | Yes |
| **Total** | **75%** | **9 of 9 match** | **54% / 41%** | **9 of 9** |

**What validation says:**

- **Direction is right.** The planner view ranks the series exactly as the true lost revenue does, and every call survives recomputation with true demand.
- **The observable cell selection is good, not perfect.** The top 20 cells by stockout days capture 53.4% of true lost revenue; the truth-selected top 20 capture 60.2%.
- **Size is conservative.** Reconstruction finds 75% of the true Dec–Feb gap, so +21% understates the need (truth: +28%).
- **The new/moved split leans to buying.** The planner view needs 54% new units against a 41% quantity share in truth. That is mostly CTS-001 Retail and IMH-001 ECOM, whose leftover stock sat in regions that didn't run out. A real planner learns this only after the season, so treat new units above the chase floor as the first item to cut if capacity is tight.

## What this does not settle

- **The data is simulated, and the failure modes were designed in.** The assumptions register says so for the peak throttle and the shipment-based chase. The test is that this diagnosis finds them from observable data. The size of every effect is still a property of the simulation.
- **Supply is only partly modelled.** Early shipping, order-change windows, supplier capacity, MOQs and DC space are missing, so +10,339 is indicative until supply planning confirms them.
- **The excess threshold is a policy choice.** The 50% guardrail ratio should be set with finance.
- **Lost revenue is an upper bound.** It assumes no substitution to other styles, channels or weeks.

## Files

- Script: `04_scripts/step8/step8_peak_diagnosis.py` (reads committed files only; about 3 seconds; identical outputs on every run). The whole chain: `python 04_scripts/run_pipeline.py --check`
- Step 5 reconciliation: `04_scripts/step8/step8b_step5_reconciliation.py` → `…_Step8B_Step5_Reconciliation.csv`, `…_Step8B_Replenishment_Proxy_Backtest.csv`, `…_Step8B_Summary_Metrics.csv`
- Brief: `04_scripts/step8/step8c_build_brief.py` builds `06_docs/DemandIQ_Peak_Season_Brief.pdf` and checks every number in it against these CSVs
- Recommendation: `05_outputs/peak_season_diagnosis/DemandIQ_Step8_Peak_Buy_Recommendation.csv`, `…_Peak_Buy_by_Region.csv`, `…_Peak_Move_Feasibility.csv`
- Validation: `…_Peak_Buy_Validation.csv`
- Every headline number, with its basis and role (diagnosis, recommendation, validation): `…_Headline_Metrics.csv`
- Charts: `08_assets/charts/step8_*.png`

![81% of lost demand falls in Dec–Feb; the S&OE window holds 1.1%](../08_assets/charts/step8_lost_demand_by_month.png)

![The 13-week queue moves with supply, not forecasting technique](../08_assets/charts/step8_forward_plan_sensitivity.png)
