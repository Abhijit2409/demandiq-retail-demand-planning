# DemandIQ · Step 8 · Peak-Season Decisions

> **Simulation notice.** Portfolio simulation; no real company data. Reproduce every number with `python 04_scripts/step8/step8_peak_diagnosis.py`.
>
> **Two kinds of evidence, kept apart.** The recommendation, the decision table and the series tables use only what a planner can observe: sales, in-stock days, receipts, inventory, buys and reconstructed demand. *Simulation truth* (true and lost demand, which no planner sees) appears only in **Why**, to size the problem, and in **Validation**, to score the recommendation.

## The decision

**Plan the Dec–Feb peak on reconstructed demand, not last year's sales, and act now.** For the next peak, the indicative scenario is **+10,339 units (+21% on last season's Dec–Feb sales)**:

- **4,574 moved forward:** spring replenishment shipped before the peak instead of after it.
- **5,613 new.**
- **152 accepted as a gap,** in CTS-001 ECOM, where the excess guardrail blocks new units.

**The scenario is indicative, and the window is closing.** Those units must land before last season's first stockout week, one year on: Nov 30 or Dec 14, 2026. On the 22-week overseas lane, that means committing them by **Jun 29, 2026 for six series and Jul 13 for three**, the first two weeks of the current 13-week plan. The regular October-drop order date (Apr 27) has already passed, so the moved units need suppliers to ship early. DemandIQ does not model that, so it stays open. If neither early shipping nor a new overseas order is possible, chase alone can still land about **4,355 units** within last season's unused chase capacity.

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

| # | Decision | Quantity | Decide by · owner | Guardrail | Confidence |
| --- | --- | --- | --- | --- | --- |
| 1 | Plan the peak on reconstructed demand, moving stock before buying | Indicative +10,339 units: 4,574 moved, 5,613 new, 152 accepted gap | Supplier commitment by Jun 29 (6 series) or Jul 13, 2026 (3 series) · planner proposes, Manager of Merchandise Planning approves, supply planning confirms early shipping and capacity | No new units where over-buy exposure ≥ 50% of estimated lost revenue (a policy assumption to set with finance); season-end cover ≤ 8 weeks | Direction: high (calls and priority match the simulation 9 of 9). Size: indicative; early shipping and supplier capacity are unconfirmed |
| 2 | Size chase from the peak gap, not from early shipments | Fallback floor of about 4,355 units within last season's unused capacity; above that, needs supplier capacity | Chase order by Sep 21 (6 series) or Oct 5, 2026 (3 series), so it lands before the first stockout · planner with supply planning | Chase ≤ 8% of commitment | Medium: last season's headroom is only an indicator |
| 3 | Rank exceptions by stockout days, by SKU × region × channel | Top 20 of 81 cells | Each monthly S&OP · Demand Planner | – | High: the stockout-days ranking matches lost revenue (rank correlation 0.90; 15 of the top 20 shared) |
| 4 | Replace the summer escalation list | 0 ESCALATE, 1 WATCH (APS-001 Wholesale, short only if demand runs 18% above forecast), 5 PROTECT, 3 no action; the published list had 3 ESCALATE | Weekly S&OE · planner decides, supply confirms in-transit replenishment | Re-check weekly as replenishment confirms | Medium: assumes last year's replenishment pattern repeats |
| 5 | Launch reserve-release rule | Hold the 991-unit reserve (12% of the 8,259-unit buy) centrally; release it to any channel running 5+ pp above planned mix at W1–W2 | Launch checkpoints W1–W2 · planner with merchants | Total launch inventory unchanged | Medium: one seeded launch. The rule fires at W1 (ECOM +5.4 pp) |

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

## Receipt-date and supply check

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

**Moved units:** last season, half of the spring replenishment had arrived by Apr 13–27. Moving it before the peak means landing it 17–21 weeks earlier, so suppliers must ship part of the season commitment ahead of schedule. **Open:** order-change windows are not modelled.

**New units:** a 22-week order is still possible on the plan date, but supplier capacity is not modelled (**open**). On the chase lane, they fit last season's unused capacity in 3 of 8 series.

**Floor:** if neither early shipping nor a new overseas order is possible, chase alone lands about 4,355 units.

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
- **Size is conservative.** Reconstruction finds 75% of the true Dec–Feb gap, so +21% understates the need (truth: +28%).
- **The new/moved split leans to buying.** The planner view needs 54% new units against a 41% quantity share in truth. That is mostly CTS-001 Retail and IMH-001 ECOM, whose leftover stock sat in regions that didn't run out. A real planner learns this only after the season, so treat new units above the chase floor as the first item to cut if capacity is tight.

## What this does not settle

- **The data is simulated, and the failure modes were designed in.** The assumptions register says so for the peak throttle and the shipment-based chase. The test is that this diagnosis finds them from observable data. The size of every effect is still a property of the simulation.
- **Supply is only partly modelled.** Early shipping, order-change windows, supplier capacity, MOQs and DC space are missing, so +10,339 is indicative until supply planning confirms them.
- **The excess threshold is a policy choice.** The 50% guardrail ratio should be set with finance.
- **Lost revenue is an upper bound.** It assumes no substitution to other styles, channels or weeks.

## Files

- Script: `04_scripts/step8/step8_peak_diagnosis.py` (reads committed files only; about 3 seconds; identical outputs on every run)
- Recommendation: `05_outputs/peak_season_diagnosis/DemandIQ_Step8_Peak_Buy_Recommendation.csv`, `…_Peak_Buy_by_Region.csv`, `…_Peak_Move_Feasibility.csv`
- Validation: `…_Peak_Buy_Validation.csv`
- Every headline number, with its basis and role (diagnosis, recommendation, validation): `…_Headline_Metrics.csv`
- Charts: `08_assets/charts/step8_*.png`

![81% of lost demand falls in Dec–Feb; the S&OE window holds 1.1%](../08_assets/charts/step8_lost_demand_by_month.png)

![The 13-week queue moves with supply, not forecasting technique](../08_assets/charts/step8_forward_plan_sensitivity.png)
