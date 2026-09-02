<!-- ============================ PAGE 1 - COVER ============================ -->

# ABHIJIT MISHRA

## DemandIQ

### Demand Planning, IBP & New Product Launch Decision System for Premium Outdoor Apparel

*From stockout-adjusted forecasting and weekly S&OE decisions to cold-start launch planning, rolling forecasts, and lifecycle handoff.*

<br><br>

**Demand Planning · Forecasting · IBP · S&OE · New Product Planning**

<br><br>

> *Portfolio simulation built using public, synthetic, and derived data. No real company internal planning data was used.*

<div style="page-break-after: always;"></div>

<!-- ============================ PAGE 2 - DEMANDIQ AT A GLANCE ============================ -->

# DemandIQ at a Glance

*Everything you need to read the rest of this document.*

### A · Products

| Mature products (own demand history) | | New product (no own history) |
|---|---|---|
| **APS-001** · Alpine Performance Shell | | **HIS-001** · Hybrid Insulated Shell |
| **CTS-001** · Core Technical Shell | | |
| **IMH-001** · Insulated Midlayer Hoody | | |

HIS-001 has no demand history of its own at launch. It follows a cold-start, analog-led process instead of the mature forecasting engine.

### B · Channels

- **ECOM**: e-commerce and direct online. **RETAIL**: company-operated stores. **WHOLESALE**: partner channel.

### C · Essential planning terms

| Term | What it means |
|---|---|
| **WAPE** | Weighted Absolute Percentage Error, a forecast-accuracy measure. Lower is better. |
| **Bias** | Whether forecasts run above or below actual demand. |
| **IBP** | Integrated Business Planning, the cross-functional consensus plan. |
| **S&OE** | Sales and Operations Execution, the weekly execution decisions. |
| **FVA** | Forecast Value Add. Did a forecasting step improve accuracy? |
| **V0 / V1 / V2 / V3** | Analytical, Commercial, Consensus, and Approved forecast versions. |
| **WOS** | Weeks of Supply. How long inventory lasts at expected demand. |
| **Fill Rate** | The share of demand that available inventory can serve. |
| **Cold Start** | Forecasting a product with little or no history of its own. |

### D · What is DemandIQ?

DemandIQ is a synthetic premium outdoor apparel demand-planning simulation. It shows how a planner moves from retail demand signals to real decisions: demand reconstruction, forecasting, scenario planning, inventory and service risk, and governed planner actions. It then applies the same environment to a new-product launch, covering analog selection, an 18-month cold-start forecast, IBP consensus, the initial buy, sell-through, reforecasting, Forecast Value Add, and rolling forecast updates. Every figure comes from public, synthetic, or derived data. None of it is real company data, and every economic figure is a planning exposure proxy rather than accounting profit.

<div style="page-break-after: always;"></div>

<!-- ============================ PAGE 3 - BUSINESS PROBLEM + EXECUTIVE SUMMARY ============================ -->

# Why Planning Is More Than Predicting Sales

### The planning challenge

Good demand planning is not simply predicting sales. Six realities make it harder:

- Sales can be censored by stockouts, so observed sales understate real demand.
- Weather adds demand uncertainty, but future weather is not known at forecast time.
- Aggregate fill can hide weekly service failures.
- A forecast has to become an inventory decision. A number on its own is not an action.
- New products have no history of their own.
- The plan has to learn as evidence arrives, through governed reforecasting rather than ad-hoc overrides.

### What I found

| # | Finding | Value |
|---|---|---|
| 1 | Mature 13-week Base demand | **36,434.66 units** |
| 2 | Portfolio Base fill against target | **98.77% vs 92%** |
| 3 | Mature series at weekly-service P1 (escalate) | **3 of 9** |
| 4 | HIS-001 V3 approved 13-week demand | **~7,577 units** |
| 5 | HIS-001 initial buy and launch fill | **~8,259 units · ~97.7%** |
| 6 | Cycle-02 like-for-like revision | **~ −3.05%** |

> **The point of the project.** Aggregate accuracy and aggregate fill are necessary but not sufficient. The value sits in the decision: which weeks and channels are at risk, what to buy for a product with no history, and how the plan should learn after launch.

<div style="page-break-after: always;"></div>

<!-- ============================ PAGE 4 - ARCHITECTURE ============================ -->

# How DemandIQ Fits Together

*Two governed engines share one planning environment. One handles mature products. One handles a new-product launch.*

| MATURE PRODUCT ENGINE | | NEW PRODUCT ENGINE (HIS-001) |
|---|---|---|
| Observed retail sales | | Analog products (APS + IMH) |
| Demand reconstruction | | Cold-start forecast (V0) |
| Forecast backtesting | | 18-month lifecycle forecast |
| Weather scenarios | | Commercial plan (V1) |
| 13-week demand plan | | Consensus and Approved (V2, V3) |
| Inventory and receipts | | Initial buy and allocation |
| Service-risk detection | | Launch sell-through |
| **Planner decisions** | | Reforecast and Forecast Value Add |
| | | Cycle-02 rolling forecast |
| | | **Lifecycle handoff** |

**Mature grain:** Week × SKU × Channel. Three SKUs across three channels give nine series, with about 260 weeks of history.
**New-product grain:** HIS-001 by channel, on a dual horizon of 18 months monthly and 13 weeks weekly.

> I kept the two engines separate on purpose. A product with 13 weeks of history should not be forced through a model process built for 104 weeks.

<div style="page-break-after: always;"></div>

<!-- ============================ PAGE 5 - RECONSTRUCTION + MATURE FORECASTING ============================ -->

# Recover the Demand Signal, Then Forecast It Honestly

### A · Why sales are not always demand

When inventory runs short, sales are censored. If I forecast those sales directly, the model learns that stockout weeks were genuinely low-demand weeks, and it plans down the very products that were selling best. So I reconstructed demand before forecasting. I compared three methods under one evaluation and chose Seasonal Profile Imputation.

| Reconstruction metric (censored rows) | Value |
|---|---:|
| WAPE | **26.08%** |
| Bias | **−2.61%** |
| Lost-demand recovery | **95.68%** |
| Full-stockout recovery | **98.43%** |

The forecast target is reconstructed demand. The simulation carries a hidden true-demand series, but I only use it to score the reconstruction. It is never a forecast input.

### B · The mature forecast engine

Every one of the nine series runs the same honest backtest: 52-week seasonality, 104 weeks of initial training, a 13-week horizon, and 12 expanding-window folds. WAPE is the primary metric, with bias tracked alongside.

| Champion mix | Result |
|---|---|
| **8 ETS, 1 Seasonal-MA baseline, 0 SARIMA** | Champion WAPE 8.4% to 21.7%, bias between −3.1% and +2.4% |

> I chose the defensible model, not the most complex one. Where SARIMA beat ETS by about 0.06 points of WAPE, I kept the simpler ETS. Where a moving-average baseline won outright, I kept it. Repeated out-of-sample performance, bias, and simplicity drove the choice.

<div style="page-break-after: always;"></div>

<!-- ============================ PAGE 6 - OUTLOOK → INVENTORY → DECISIONS ============================ -->

# From 13-Week Outlook to Planner Decisions

### A · Weather and demand outlook

| Scenario | 13-week demand |
|---|---:|
| Mild | ~36,036 |
| **Base** | **36,434.66** |
| Severe | ~36,677 |

Weeks 1 to 3 need a real nowcast. None was supplied, so I made no near-term weather adjustment rather than inventing one. Weeks 4 to 13 use Mild, Normal, and Severe scenarios. No realized future weather enters any forecast. The band is narrow, about 1.8% of Base, which is itself a finding: weather is not the dominant near-term risk here.

### B · Service and inventory risk

Portfolio Base fill is 98.77% against a 92% target. Yet three of the nine series miss the weekly target twice each.

| SKU · Channel | 13W fill | Worst weekly fill | Action |
|---|---:|---:|---|
| APS-001 · WHOLESALE | 93.5% | **33.2%** | Escalate |
| CTS-001 · RETAIL | 95.6% | **65.4%** | Escalate |
| IMH-001 · WHOLESALE | 96.1% | **74.1%** | Escalate |

All three share a worst week of 2026-08-24, when committed receipts are zero across all nine series. I read that carefully: the receipt gap lines up with failures in the thin-buffer channels, but it is not proven cause. All nine share the gap, and only three break.

### C · Planner action

Three series escalate. Six protect. All nine finish below the 2.5-week coverage policy, a portfolio gap of about 7,000 units.

> **Risk detection is not execution authorization.** The engine releases zero automatic chase and zero reallocation, because it does not model supplier lead time, expedite, or transfer feasibility. Base lost-revenue exposure is about CAD 192K (a planning exposure proxy, not profit), roughly 64% of it in CTS-001 / RETAIL. I use it only to rank the review queue.

<div style="page-break-after: always;"></div>

<!-- ============================ PAGE 7 - HIS COLD START ============================ -->

# HIS-001: Forecasting a Product With No History

HIS-001, the Hybrid Insulated Shell, launched on 31 Aug 2026. It had no demand history of its own, so the mature ETS and seasonal engine could not be applied.

### A · Analog selection

| Candidate | Similarity score | Role |
|---|---:|---|
| APS-001 | **0.679** | Primary analog, 60% |
| CTS-001 | 0.531 | Excluded from blend |
| IMH-001 | 0.448 | Secondary analog, 40% |

APS anchors shell construction, price, scale, and Fall/Winter seasonality. IMH supplies the insulation that APS lacks, and the two share the same Fall/Winter shape (correlation 0.99). CTS ranked second by raw score, but it is a redundant shell that fills no gap, so I left it out. The final blend is 60% APS and 40% IMH.

### B · The V0 cold-start forecast

| V0 analytical baseline | Value |
|---|---:|
| Launch-scale factor | 0.60 |
| First-year demand | **~27,480 units** |
| 18-month demand | ~44,919 units |
| 13-week demand | ~6,888 units |
| Second-season factor | 1.00 (flat, no growth assumed before evidence) |

### C · Why two horizons

- **Strategic (IBP): 18 months, monthly.** This supports commercial, category, and supply discussions.
- **Operational (S&OE): 13 weeks, weekly.** This supports near-term launch execution and the initial buy.

<div style="page-break-after: always;"></div>

<!-- ============================ PAGE 8 - CONSENSUS → V3 → BUY ============================ -->

# From Consensus to an Approved Plan and a Buy

### A · The forecast version journey

The plan moved through four versions: V0 Analytical, V1 Commercial, V2 Consensus, and V3 Approved. The commercial option applied 5% category growth and a 19% category share for HIS. Consensus then moderated the uplift with a cap of 10% over V0.

| Version | First 12 months | 18 months |
|---|---:|---:|
| V1 Commercial | ~30,476 | ~49,816 |
| **V3 Approved** | **~30,228** | **~49,411** |

> **V3 is approved, unconstrained demand** (V3 over V0 is about 1.10). It is a demand position, not a supply-constrained plan.

### B · The initial buy

| Buy build-up | Units |
|---|---:|
| Approved V3 13-week demand | ~7,577 |
| Plus launch uncertainty buffer (9%) | ~682 |
| **Frozen initial buy (BALANCED)** | **~8,259** |
| Flex reserve, held back | ~991 |

### C · Channel allocation

| Channel | Pre-allocation |
|---|---:|
| ECOM | ~3,271 |
| RETAIL | ~2,544 |
| WHOLESALE | ~1,454 |
| **FLEX RESERVE** | **~991** |

Supply setup (synthetic supply planning assumptions): about an 8-week replenishment lead and chase capacity of 15% of the buy or less.

> The 9% launch buffer is a one-time cold-start allowance for launch uncertainty. It is not the mature 2.5-week safety-stock rule.

<div style="page-break-after: always;"></div>

<!-- ============================ PAGE 9 - LAUNCH EXECUTION + REFORECAST ============================ -->

# What Happened After Launch

### A · The seeded launch result

*Synthetic seeded launch simulation (seed 7).*

| Launch outcome (13 weeks) | Value |
|---|---:|
| Observed sales | ~6,650 |
| Latent demand (evaluation only) | ~6,809 |
| Launch fill | ~97.7% |

> The latent demand is for evaluation only. The operational planner never saw hidden demand truth, and it never entered a reforecast or a decision.

### B · The reforecast journey

| Checkpoint | Reforecast (13-week demand) |
|---|---:|
| Original V3 | 7,577 |
| W1 | 7,465 |
| W2 | 7,310 |
| W4 | 7,030 |
| W8 | 6,943 |
| W13 | 6,650 |

As launch evidence built up, the plan leaned less on the pre-launch analog prior and more on what was actually selling. The weighting rises with observed weeks (w = n / (n + 4)). The planning point matters more than the formula: real evidence earns weight over time.

### C · A disciplined non-action

Every checkpoint resolved to hold. Attainment stayed within tolerance, channel-mix deviation stayed under the reallocation trigger, and coverage stayed adequate. I forced no chase, cut, or reallocation. That is disciplined governance, not a missing feature.

<div style="page-break-after: always;"></div>

<!-- ============================ PAGE 10 - FVA + CHANNEL LEARNING ============================ -->

# Did the Forecast Add Value, and What the Channels Taught Me

### A · Did each version improve accuracy?

| Version | WAPE | FVA vs prior |
|---|---:|---:|
| V0 Analytical | **5.66%** | n/a |
| V1 Commercial | 12.58% | **−6.92 pp** |
| V2 Consensus | 11.81% | +0.77 pp |
| V3 Approved | 11.81% | 0.00 pp (V3 equals V2) |

The checkpoint reforecasts, scored only on the weeks that were still ahead, added accuracy each time: W1 +1.20, W2 +2.80, W4 +5.01, W8 +6.16 points. W13 has no remaining horizon, so it cannot be measured.

> **A caveat I will not hide.** The synthetic launch generator was centered on the V0 analytical baseline. So V0 scoring better than V1, V2, and V3 on this seeded path is an illustrative governance demonstration. It is not independent proof that commercial input was harmful.

### B · What the channels taught me

Using observed, operational data:

| Signal | Value |
|---|---:|
| Observed ECOM mix (planned 45%) | **~49.2%** |
| ECOM lost demand (W13 stockout) | ~159 units |
| Idle flex reserve | ~991 units |
| Historical reallocation trigger | 8 pp |

> Total supply and channel allocation are two different problems. Inventory sat available in the reserve and in other channels while ECOM stocked out. That is a channel-allocation and policy-timing issue, and I recorded it as a next-cycle learning. I do not claim another threshold is optimal.

<div style="page-break-after: always;"></div>

<!-- ============================ PAGE 11 - ROLLING + LIFECYCLE ============================ -->

# Rolling the Forecast, and Where HIS-001 Sits

### A · A genuine rolling forecast

| | Window | As-of |
|---|---|---|
| **Cycle 01** | Sep 2026 to Feb 2028 | 2026-08-24 |
| **Cycle 02** | Oct 2026 to Mar 2028 | 2026-09-28 |

After the first four weeks of launch evidence, the horizon rolls. September becomes actual. March 2028 enters as a newly generated month 18, built from the same governed seasonal foundation rather than copied. Across the 17 overlapping months (Oct 2026 to Feb 2028), the outlook falls by about 3.05%.

I attenuated the learning by lifecycle phase, so early evidence moves the first season most and the second season least:

| Phase | Weight applied to W4 evidence |
|---|---:|
| Near-term and peak | 1.00 |
| Normalization | 0.50 |
| Second season | 0.25 |

*(These weights are synthetic rolling-forecast governance assumptions. The structure follows the lifecycle phases. The exact weights are not statistically estimated.)*

### B · Lifecycle handoff

| Stage | Weeks |
|---|---|
| COLD_START | 0 |
| **EARLY_LAUNCH (HIS-001 is here)** | **1 to 13** |
| MATURING_LAUNCH | 14 to 51 |
| SEASONAL_HISTORY_AVAILABLE | 52 or more |
| MATURE_MODEL_ELIGIBLE | 104 or more clean weeks, plus data-quality gates |

> HIS-001 has 13 observed weeks, so it is not eligible for the mature model. I fit no ETS or SARIMA on it. The current method stays an analog plus actual-evidence blend, because new products and mature products need different governance.

<div style="page-break-after: always;"></div>

<!-- ============================ PAGE 12 - CLOSE ============================ -->

# What This Project Shows

### Capabilities

- **Forecasting:** demand reconstruction, backtesting, accuracy and bias, weather scenarios.
- **Planning:** 13-week S&OE, initial buy, channel allocation, sell-through.
- **IBP:** 18-month rolling forecast, V0 to V3 versions, consensus, overrides.
- **New product:** cold start, analog planning, reforecasting, lifecycle handoff.
- **Governance:** Forecast Value Add, exception management, detection separated from authorization, provenance controls.

### Governance

- Public, synthetic, and derived data. No real company internal data.
- Hidden truth is used for evaluation only.
- Economics are planning exposure proxies, not profit.
- Enterprise planning concepts are demonstrated. I make no claim of hands-on experience with a specific commercial platform.

### Limitations

- A synthetic launch on a single seeded path.
- Simplified supplier constraints, and weather caps that are planning assumptions.
- FVA shaped by a simulation centered on V0.
- 13 launch weeks, too few to fit a mature model.

### The takeaway

DemandIQ moved the question from *"What is likely to sell?"* to something a planner can act on:

> *"What demand should we plan for, what inventory and service risk does that create, what action should the planner take, how should a new product be launched, and how should the plan learn as new evidence arrives?"*

The value is in planning decision quality and governance, not in predictive accuracy alone.

<br>

*DemandIQ. Portfolio simulation using public, synthetic, and derived data. Economic values are planning exposure proxies.*
