# DemandIQ: portfolio copy

Paste-ready text for the portfolio home-page card and project page. Every number matches the Step 8 outputs in this repository. This is a retrospective decision case: deadlines are evaluated at the published plan's as-of date, June 29, 2026, and all have since passed.

---

## Home-page card

**Retail · Demand planning**

### DemandIQ: Peak-Season Demand Planning

Completed · Simulated data · Retrospective decision case

Every outerwear buy starts from last year's sales, so stockouts in the peak quietly shrink next year's peak, and fill falls every season.

- **86% → 78%**: Dec–Feb fill over four plan years, traced to a sales-based buy
- **+10,339 units (+22%)**: indicative peak change on reconstructed demand, evaluated at the June 29, 2026 planning date (4,574 moved, 5,613 new)
- **9 / 9 series**: priority and call confirmed against simulation truth

Python · pandas · statsmodels · matplotlib · Streamlit · pytest · GitHub Actions

[Explore project] [GitHub]

---

## Project page

**Hero line:** Every outerwear buy starts from last year's sales, so stockouts in the peak quietly shrink next year's peak, and fill falls every season.

**Metrics:** use the same three as the card.

### Overview

A demand-planning case study for a premium outerwear range. It asks why peak-season (Dec–Feb) availability has fallen four years running, and what the Demand Planner should have decided at the June 29, 2026 planning date for the coming fall/winter buy, chase plan and launch allocation. Every recommendation uses only data a planner can observe; hidden simulation truth is used only to size the problem and to validate the answer.

### Business problem

Peak-season fill fell from 85.9% to 78.1% between PY2022 and PY2026, while annual fill still looked close to the 92% target. Each buy starts from last year's sales, and stockouts suppress exactly the peak weeks. So the plan understates the peak every year, and the in-season chase can't tell which cells will run out.

### How the project runs (six steps)

1. **Process.** Map the planning loop: a sales-based buy on a 22-week lead time, four drops from July to October, replenishment throttled in the peak, and chase triggered on shipments.
2. **Metric.** Peak fill on reconstructed demand is the primary metric. Lost revenue is the currency; over-buy exposure and season-end cover are the guardrails.
3. **Drivers.** Lost units are weekly demand above available stock. Available stock is drops + replenishment + chase + restocked returns.
4. **Bottleneck.**
    - The buy basis sits 9.0% below last year's reconstructed demand.
    - 59% of lost units had stock that arrived too late.
    - Chase fires in mid-September on a signal that can't tell high-loss cells from low-loss ones.
5. **Solution.** Plan the peak on reconstructed demand: an indicative +10,339 units (4,574 moved forward, 5,613 new), evaluated at the planning date. Chase is sized from the peak gap, and launch reserve is released on a 5-pp channel-mix rule.
6. **Plan.**
    - At the June 29, 2026 planning date, suppliers needed to commit by Jun 29 to Jul 13.
    - Chase orders were due by Sep 21 to Oct 5. All of these deadlines have passed.
    - Weekly S&OE works from exceptions ranked by stockout days.
    - A post-season review feeds the next buy.

### Key findings

- 83% of lost units fall in Dec–Feb. The original 13-week summer window held 1.1% of lost demand.
- In that summer window, weather scenarios and stockout correction change none of the nine planner decisions. The supply assumption changes six, which is why the decision belongs in the peak.
- The published 13-week plan assumed zero replenishment and escalated three series. Adding an estimate of replenishment (6,512 units, last year's pattern shifted 52 weeks, not confirmed open orders), the planning engine escalates none if the estimate arrives as modelled: 0 escalate, 7 protect, 2 hold. A planner must confirm open orders and receipt dates before that replaces the published list. An independent error-band check agrees on 7 of 9 series.
- Stockout correction lifts Dec–Feb demand by 21% (the true gap is 28%), so the recommended change is conservative.
- The top 20 of 81 SKU × region × channel cells by true lost revenue hold 60.2% of it. The observable selection, the top 20 by stockout days, captures 53.4% (rank correlation 0.90).
- At the June 29 planning date the decision was already urgent. 22-week orders had to be committed by Jun 29 to Jul 13 to land before the first stockouts; otherwise chase alone could have landed about 4,355 units.

### Business recommendation

At the June 29, 2026 planning date, plan the peak on reconstructed demand and move stock before buying more. Commit suppliers by Jun 29 to Jul 13, order chase by Sep 21 to Oct 5, and rank weekly exceptions by stockout days. The +10,339-unit scenario is indicative: early shipping and supplier capacity were never confirmed, and every deadline has now passed.

### Reproducibility

One command rebuilds every output from the repository, and CI fails if any committed number changes. Two pieces were never committed: the data generator, whose CSVs are the frozen source data, and the original demand-reconstruction code. The reconstructed series is recovered exactly from committed backtest evidence. Every number in the two-page brief is generated from the outputs and checked.

### Limitations

- All data is simulated, and the peak throttle and shipment-based chase are designed into the generator. The test is that the diagnosis finds them from observable data.
- Early shipping, order-change windows, supplier capacity and MOQs are not modelled.
- Lost revenue assumes no substitution, so it is an upper bound.
- The 50% over-buy guardrail and the 92% service target are policy assumptions.

### Images

Replace the app screenshots with the three Step 8 charts in `08_assets/charts/`. The app screenshots show the zero-replenishment summer escalation list (3 escalate), without the conditional comparison.

- `step8_fill_trend.png`: Dec–Feb fill fell from 86% to 78%
- `step8_lost_demand_by_month.png`: 81% of lost demand falls in Dec–Feb
- `step8_forward_plan_sensitivity.png`: the 13-week queue moves with supply, not forecasting technique

### Replace on the current page

- "95.68% of demand lost to stockouts recovered": a five-year net figure; the latest year recovered 79%
- "3 / 9 series flagged as weekly service risks": these disappear if the estimated replenishment arrives as modelled
- "3 ESCALATE, 6 PROTECT": this is the zero-replenishment view. Show it next to the conditional result (0 escalate, 7 protect, 2 hold, if the estimated replenishment arrives) and say open orders are not yet confirmed.
- "a work list with owners": now true only in the Step 8 decision table, so link there
