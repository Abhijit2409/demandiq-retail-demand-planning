# DemandIQ: Peak-Season Demand Planning for Premium Outerwear

**Bottom line.** Peak-season (Dec–Feb) fill fell from 86% to 78% in four plan years. The cause is that every buy starts from last year's sales, and stockouts suppress exactly the peak weeks. Evaluated at the published plan's as-of date, **June 29, 2026**, planning the coming peak on reconstructed demand meant an indicative **10,339 more units (+22% on last peak's Dec–Feb sales)**: 4,574 shipped before the peak instead of in spring, plus 5,613 new. The orders were due by **Jun 29 – Jul 13**, the first two weeks of the 13-week plan, which the published version spent on summer exceptions.

> **Retrospective decision case.** Every order and chase deadline in this README (Jun 29 – Oct 5, 2026) is evaluated at the June 29 planning date, and all have since passed. They show what the planner should have decided then, not actions still open.

> **Simulation notice.** Weather is public data; demand, inventory and launch actuals are synthetic. No company's internal data is used, and economics are planning-exposure proxies, not accounting profit.
>
> Every number is labelled by evidence. **Observable** numbers use only what a planner can see: sales, in-stock days, receipts, inventory and reconstructed demand. **Simulation truth** numbers use hidden generator fields, and appear only to size the problem and to validate the recommendation.

**Start here:** [Decision page](./06_docs/DemandIQ_Step8_Peak_Season_Decisions.md) · [Two-page brief (PDF)](./06_docs/DemandIQ_Peak_Season_Brief.pdf) · [Diagnosis script](./04_scripts/step8/step8_peak_diagnosis.py) · [Reproducibility](./06_docs/DemandIQ_Reproducibility.md) · [Technical appendix](./06_docs/DemandIQ_Technical_Appendix.md)

---

## The decision and who makes it

> Peak-season fill has fallen from 86% to 78% in four years. Why, and what should the Demand Planner change in the next fall/winter buy, chase plan and launch allocation to recover lost sales without building excess?

| Role | Part in the decision |
| --- | --- |
| Demand Planner, outerwear portfolio | Owns the demand plan; proposes buys, chase and allocation |
| Manager, Merchandise Planning | Approves at the monthly S&OP review |
| Merchants and commercial teams | Supply growth targets and launch input |
| Supply planning | Confirms lead times, early shipping and supplier capacity |
| Finance | Sets the revenue plan and the excess guardrail |

**The planning year:**

1. **Post-season review (Mar–Apr):** reconstruct last season's demand and measure peak fill against target.
2. **Seasonal buy review (22+ weeks before the October drop):** size the peak on reconstructed demand.
3. **Chase gate (late September):** commit chase early enough to land before December.
4. **Weekly S&OE (October to February):** exceptions ranked by lost revenue.
5. **Log every action** and feed the results into next season's review.

---

## Recommendations

**1. Plan the peak on reconstructed demand, and move stock before buying.**
- **I found:** Dec–Feb fill fell from 85.9% to 78.1% *(simulation truth)*. Each buy starts from last year's sales, which sat 9.0% below last year's reconstructed demand *(observable)*. Reconstructed Dec–Feb demand is 21% above sales *(observable)*.
- **This means:** the plan shrinks itself every year in the season that matters most.
- **Therefore:** at the June 29 planning date, plan the coming peak on the indicative scenario of **+10,339 units**: 4,574 moved forward from spring replenishment, 5,613 new, and 152 accepted as a gap where the excess guardrail blocks new units. Suppliers needed to commit by **Jun 29 (6 series) or Jul 13, 2026 (3 series)**.
- **Owner:** planner proposes, S&OP approves, supply planning confirms. **Confidence:** high on direction; indicative on size until early shipping and supplier capacity are confirmed.

**2. Size chase from the peak gap, not from early shipments.**
- **I found:** chase fires in mid-September in 75–77% of cell-years whatever their eventual loss. Early shipments can't tell high-loss cells from low-loss ones (0.97 vs 1.02 of plan), and 5,403 units of chase capacity went unused *(observable)*.
- **Therefore:** at the planning date, chase orders for the priority series were due by **Sep 21 or Oct 5, 2026**. As a fallback if the buy couldn't move, about **4,355 units** fit within last season's unused chase capacity. Both dates have passed.

**3. Rank exceptions by stockout days, by SKU × region × channel.**
- **I found:** the observable stockout-days ranking tracks lost revenue (rank correlation 0.90). The top 20 cells by stockout days capture **53.4%** of true lost revenue, against **60.2%** for the true top 20; 15 of the 20 cells are shared.
- **Therefore:** start each S&OP with the top 20 of 81 cells by stockout days.

**4. Escalate only shortfalls that survive forecast error.**
- **I found:** the published 13-week plan counted only the seasonal drops as supply, so it assumed zero replenishment, and escalated 3 series (APS-001 Wholesale, CTS-001 Retail, IMH-001 Wholesale). Repeating last year's replenishment pattern adds an **estimated** 6,512 units, projected to land by Jul 13 *(observable history; estimated, not confirmed open orders)*.
- **Therefore, conditionally:** if the estimated replenishment arrives as modelled, the Step 5 engine escalates none: **0 ESCALATE, 7 PROTECT, 2 HOLD**. With zero replenishment it gives the published list: **3 ESCALATE, 6 PROTECT**. Both are in the outputs. **A planner must confirm open-order quantities and receipt dates before the conditional calls replace the published escalation list.** The Jul 13 check only shows the projected dates fit the 3-week replenishment lead time; it says nothing about supplier commitments.
- **Check:** Step 8's error-band queue (0 ESCALATE, 1 WATCH, 5 PROTECT, 3 no action) agrees with the conditional calls on 7 of 9 series. The two differences come from tests only one of them runs: the forecast-error band (APS-001 Wholesale on watch) and the severe-weather case (IMH-001 Retail protected).
- **Sensitivity, not assurance:** cutting every series' estimate by 29.5% (the worst backtest series error) brings back no escalation, nor does landing it all in the last week of the window. That is one scenario, not a bound. The estimate's week-by-week error by series was 57–71% in the backtests, and the series-level shortfall reached 46% (APS-001 Wholesale received 54% of its estimate in PY2024). APS-001 Wholesale escalates again if less than 30% of its 183 estimated units arrive; CTS-001 Retail below 10% and IMH-001 Wholesale below 6.5%. No backtest year fell that low, but there are only three years per series.

**5. Release launch reserve on a channel-mix rule.**
- **I found:** the launch bought 21% more than latent demand, yet ECOM lost 159 units while a 991-unit reserve sat idle.
- **Therefore:** release reserve to any channel running 5+ pp above planned mix at W1–W2. On the seeded launch, that rule fires at W1.

Full table with quantities, dates, owners and guardrails: [decision page](./06_docs/DemandIQ_Step8_Peak_Season_Decisions.md).

---

## Evidence

### The planning process that creates the problem

- **The buy:** set from last year's sales (censored by stockouts), grown by a planner assumption, on a 22-week overseas lead time.
- **Supply arrives in four seasonal drops, July to October.** Replenishment is throttled from October to mid-January because of the lead time.
- **Chase:** fires when trailing shipments run 15% above plan. It has a 10-week lead time and is capped at 8% of the season commitment.

### The metric

| Tier | Metric | PY2026 |
| --- | --- | --- |
| Primary | Peak fill on reconstructed demand (Dec–Feb units sold ÷ reconstructed demand), target 92% | 82.6% *(observable)*; 78.1% *(truth)* |
| Currency | Lost revenue on unserved demand | CAD 6.65M, 9.1% of net revenue *(truth, upper bound)* |
| Secondary | Buy basis vs reconstructed demand; chase capacity used; forecast value add vs seasonal naive | −9.0%; 4.8% of an 8% cap; WAPE 11.7% vs 14.3% |
| Guardrail | Over-buy exposure (markdown, liquidation, obsolescence); season-end cover ≤ 8 weeks; chase ≤ 8% of commitment | CAD 1.09M |

### The drivers

- **Lost units** = weekly demand above available stock.
- **Available stock** = opening stock + four seasonal drops + replenishment + chase + restocked returns.

Demand is what it is. The losses come from three supply rules: the sales-based buy, the peak throttle and the shipment-based chase.

### The bottleneck

![Peak-season fill fell from 86% to 78% in four plan years](./08_assets/charts/step8_fill_trend.png)

![81% of lost demand falls in Dec–Feb; the S&OE window holds 1.1%](./08_assets/charts/step8_lost_demand_by_month.png)

| Finding | Value | Evidence |
| --- | --- | --- |
| Share of PY2026 lost units in Dec–Feb | 83% | Truth |
| Stock that arrived within the plan year, but after the stockouts | 59% of lost units | Truth |
| Chase trigger rate, lowest- vs highest-loss cells | 75% vs 77% | Observable |
| Top 20 cells by true lost revenue, share of lost revenue | 60.2% | Truth |
| Top 20 cells by stockout days, share of true lost revenue | 53.4% | Observable selection, truth value |

### What the forecasting work changes, and what it doesn't

![The 13-week queue moves with supply, not forecasting technique](./08_assets/charts/step8_forward_plan_sensitivity.png)

In the original summer window, weather scenarios and stockout correction change none of the 9 planner decisions. Swapping the model changes 3, and only through growth. Swapping the supply assumption changes 6. In the peak, stockout correction changes demand by +21%, which is why it belongs in the buy.

---

## How the forecast supports the decision

- **Demand reconstruction.** Seasonal-profile imputation on stockout-censored weeks:
    - censored-row bias −2.6%, against −21.0% for a naive gross-up;
    - recovers 75% of the true Dec–Feb gap, so the +21% uplift, and the buy change built on it, is conservative;
    - recovery varies by year (104%, 101% and 79% for PY2024–PY2026), because method selection used simulation truth. With real data, select by masking known in-stock weeks.
- **Backtest.** 12 expanding folds (104-week minimum, 13-week horizon) across 9 SKU × channel series:
    - ETS wins 8 of 9; no SARIMA model was selected;
    - champion WAPE is 11.7% against 14.3% for seasonal naive.
- **Weather.** Used as a scenario, never as a future-known input. It is untested in the peak, where the generator moves demand 12–13%.
- **Leakage governance.** True demand, lost demand and generator variables are excluded from every model and decision input.

## The launch: the same decision without history

HIS-001 has no sales history, so it is planned from analogs: 60% APS-001, 40% IMH-001. The plan runs through analytical, commercial, consensus and approved versions to an initial buy of 8,259 units, including a 991-unit central reserve.

The buy was large enough in total (21% above latent demand). ECOM still lost 159 units because the reserve wasn't released. Placement, not quantity, was the problem: hence recommendation 5.

The forecast-value-add result, where commercial input looks worse, is true by construction (launch truth was centred on the analytical forecast) and is not used as evidence.

## Validation against simulation truth

The recommendation uses observable data only; truth is used here to score it.

- **Direction holds.** The series priority ranking is identical to true lost revenue (9 of 9), and every call survives recomputation with true demand (9 of 9).
- **The observable cell selection is good, not perfect.** The top 20 cells by stockout days capture 53.4% of true lost revenue, against 60.2% for the truth-selected top 20.
- **Size is conservative.** The planner-view gap is 75% of the true gap.
- **The new/moved split leans to buying:** 54% new units in the planner view, against a 41% quantity share in truth.

## Assumptions and limitations

| Assumption | Basis | Changes a decision? |
| --- | --- | --- |
| Peak throttle and shipment-based chase | Designed into the generator; the assumptions register says so | Yes. Diagnosis must find them from observable data, and it does |
| 92% service target; 2.5-week safety stock; 8-week excess threshold | Policy assumptions, not derived from economics | Yes, for which series are flagged |
| 50% over-buy guardrail | Policy assumption, to set with finance | Yes, for CTS-001 ECOM |
| Early shipping, order-change windows, supplier capacity, MOQ | Not modelled | Yes: the +10,339 scenario is indicative until confirmed |
| Replenishment repeats last year's pattern (an estimate, not confirmed open orders) | Backtest series error 15–30%, series-week error 57–71%; projected arrivals all in weeks 1–3 | Yes, until confirmed: zero replenishment gives 3 escalations. A 29.5% cut gives none, but that is one scenario, not a bound. Protect vs hold changes in 3 series |
| Lost demand is fully lost (no substitution) | Simplification | Lost revenue is an upper bound |
| Wholesale modelled as weekly demand | Simplification; real wholesale is largely pre-booked | Wholesale numbers are the least reliable |
| Style level only; no sizes or colours | Scope | Buys are set by style, not style-colour-size |

---

## Run it

```bash
python -m pip install -r requirements-dev.txt     # pinned, Python 3.13
python -m playwright install chromium             # for the PDF brief
python 04_scripts/run_pipeline.py --check         # rebuilds weather, Steps 4B–8 and the brief, and fails if any committed output changes
python -m pytest -q                               # supply view, Step 8 numbers, brief, app, source data
python -m streamlit run 07_streamlit_app/app.py   # planning app: 13-week plan with estimated replenishment, zero-replenishment comparison
```

Every script uses paths relative to the repository. Two pieces were never committed:

- the Step 3 data generator, whose CSVs are the frozen source data;
- the Step 4A reconstruction code.

Step 4B.0 recovers the reconstructed-demand series exactly from committed backtest evidence, so Steps 4B–8 rebuild from the repository. ETS, SARIMA and Step 4D refits can be re-run, but they drift slightly across library versions; `run_pipeline.py --refit` reports by how much. Run order, inputs and the recovery path are in [Reproducibility](./06_docs/DemandIQ_Reproducibility.md).

## Repository map

| Folder | Contents |
| --- | --- |
| `01_assumptions/` | Assumption register and generator parameters |
| `02_data/` | Simulated history and public weather |
| `03_model_evidence/` | Reconstruction and backtest evidence |
| `04_scripts/` | Pipeline, Steps 4–8, and `run_pipeline.py` (rebuild in dependency order) |
| `05_outputs/` | Forecasts, decision layer, launch, `peak_season_diagnosis/` (Step 8), and `v1_published_plan/` (the superseded seasonal-only plan, kept for audit) |
| `06_docs/` | Decision page, brief, reproducibility, portfolio copy, technical appendix, step decision records |
| `07_streamlit_app/` | Six-page planning app |
| `08_assets/` | Charts, bundled fonts (OFL) and app screenshots |
| `tests/`, `.github/workflows/` | Focused checks and CI: clean rebuild, then tests |

## Technical appendix

Method detail, model results, launch steps and the app screenshots are in the [technical appendix](./06_docs/DemandIQ_Technical_Appendix.md), the original README. The step-by-step decision records are in `06_docs/`.
