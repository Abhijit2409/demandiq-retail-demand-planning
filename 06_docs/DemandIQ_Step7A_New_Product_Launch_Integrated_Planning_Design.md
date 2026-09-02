# DemandIQ — Step 7A — New Product Launch & Integrated Planning Design

**Document type:** Business & analytical planning design / case-study specification.
**Status:** DESIGN ONLY. No launch forecast, launch data, initial-buy calculation, or synthetic actuals are produced in this step. This document defines the planning framework that later steps (7B onward) will implement.

**Relationship to the mature product:** The mature-product DemandIQ engine — demand reconstruction, nine-series forecast selection, weather scenarios, inventory/supply simulation, the IBP/S&OE decision layer, the Streamlit control tower, and the executive findings — is complete and frozen. The New Product Launch & Integrated Planning extension is a **separate planning capability**. It reads the existing portfolio for context only and does not alter any frozen logic, output, or page.

> **Simulation notice.** Every launch product, date, price band, assumption, and scenario in this document is a **SYNTHETIC PLANNING ASSUMPTION**. HIS-001 does not represent an actual Arc'teryx product or launch plan, and nothing here reflects any company's internal data. Economic measures are **planning exposure proxies, not accounting profit, savings, or realized financial impact.**

> **Provenance discipline.** The mature project labels every field as **PUBLIC**, **SYNTHETIC**, or **DERIVED**. This extension keeps that discipline. Launch information that is not drawn from existing frozen project data is labelled a **SYNTHETIC PLANNING ASSUMPTION** at the point it is introduced.

---

## Table of contents

1. Executive Purpose
2. Launch Product Definition
3. Planning Challenges of a New Product
4. Dual-Horizon Planning Architecture
5. Planning Hierarchy
6. Cold-Start Forecasting Framework
7. Analog Selection Framework
8. 18-Month Product Lifecycle Forecast
9. Bottom-Up Forecast
10. Top-Down Plan
11. Forecast Reconciliation
12. Forecast Versions
13. Consensus Forecast / IBP
14. Monthly IBP Cycle
15. Weekly S&OE Cycle
16. Scenario Planning
17. Initial Buy
18. Channel Allocation
19. Early Sell-Through
20. Reforecast & Lifecycle Transition
21. Exception Management
22. Planner Decisions
23. Forecast Governance / FVA
24. KPI Framework
25. Enterprise Planning Workflow Concepts
26. Economic Exposure
27. Cannibalization
28. Evaluation Design
29. Future Planning Workspace
30. Limitations
31. Implementation Roadmap

---

## 1. Executive Purpose

The mature DemandIQ project answers a single, powerful question well: *given products with years of sales history, how much will they sell, and what should the planner do about supply and service risk?* That is the demand planner's core in-season problem, and it is solved.

But it is only half of a demand planner's real remit. The other half is harder and more strategic: **planning a product that has never sold.** A new product launch has no SKU history to forecast, yet it demands a full planning response — a strategic outlook, an inventory commitment, a channel split, and a governance process to defend those decisions to merchandising, sales, supply, and finance.

This extension builds that second capability. It positions DemandIQ as an **integrated planning** case study — not only a forecasting exercise — by demonstrating how a planner would run a launch through the same lifecycle a mature enterprise planning organization uses:

- a **pre-launch** cold-start demand estimate built from comparable products;
- a **strategic / IBP** rolling 12–18 month outlook that places the launch inside category and portfolio expectations;
- a **tactical** inventory and channel commitment;
- an **operational / S&OE** weekly execution loop that turns early actuals into a governed planner decision.

The extension is deliberately built around the planning capabilities a senior demand-planning role emphasises: new-product forecasting, rolling forecasts, IBP / consensus, top-down vs bottom-up reconciliation, scenario planning, exception management, and forecast governance with an audit trail. The design demonstrates these capabilities **honestly** — as transferable planning concepts (see Section 25), not as claimed hands-on experience in any commercial platform.

The four planning questions this system is built to answer are:

| Horizon / layer | Planning question |
|---|---|
| **Pre-launch** | How much demand should we expect for a product with no SKU history? |
| **Strategic / IBP** | What should the rolling 12–18 month demand outlook be, and how does the launch fit within category and portfolio expectations? |
| **Tactical** | How much inventory should we commit, and by which channel? |
| **Operational / S&OE** | Once launch actuals arrive, should the planner **CHASE, HOLD, REALLOCATE, CUT, or ESCALATE**? |

The guiding principle from the mature project carries directly into the launch: **a forecast is not a decision.** A launch forecast becomes useful only when it is connected to a rolling strategic outlook, an inventory commitment, uncertainty scenarios, a consensus process, and an explicit planner action.

---

## 2. Launch Product Definition

### The launch SKU

| Attribute | Value |
|---|---|
| **SKU** | **HIS-001** *(SYNTHETIC PLANNING ASSUMPTION)* |
| **Product** | **Hybrid Insulated Shell** |
| **Positioning** | Premium technical outerwear launch combining **insulation** and **weather protection** in a single hybrid construction |
| **Portfolio family** | Technical outerwear (shell / insulation) |
| **Customer / use case** | The layering-forward premium buyer who wants one piece that is both warm and weatherproof for cold, transitional alpine conditions |
| **Commercial intent** | A premium price position, consistent with a technical launch, sitting inside the existing premium outdoor portfolio |

Every attribute above is a **SYNTHETIC PLANNING ASSUMPTION**. HIS-001 is a case-study construct used to demonstrate launch-planning methodology.

### Analog candidate pool

Because HIS-001 blends insulation and shell characteristics, the natural comparable ("analog") products already exist in the frozen mature portfolio:

| Candidate | Product | Relevance to HIS-001 |
|---|---|---|
| **APS-001** | Alpine Performance Shell | Premium technical shell; weather-protection and price relevance |
| **CTS-001** | Core Technical Shell | Core shell construction; channel breadth relevance |
| **IMH-001** | Insulated Midlayer Hoody | Insulation, layering and fall/winter seasonal-build relevance |

**No analog is selected in this step.** All three are carried forward as an open candidate pool. Choosing the analog — or a governed blend of analogs — is the explicit purpose of **Step 7B** and is done through the interpretable framework described in Section 7. Naming a "winner" here would pre-empt that governed selection and remove the very transparency the framework exists to provide.

### What HIS-001 legitimately inherits vs. what a planner sets

A launch planner may only use what is genuinely knowable **before** the product sells. The frozen data already carries a set of planner-legitimate, non-leaking fields that describe the analog candidates:

| Knowable pre-launch (from analogs / assumptions) | Frozen source fields (illustrative) | Role |
|---|---|---|
| Category / family / product name | `sku_id`, `product_name` | analog shortlist |
| Seasonal shape | `season`, `sku_seasonality_factor`, `week_of_year` | borrowed seasonality |
| Price band | `msrp_cad`, `net_asp_cad`, `full_price_net_asp_cad` | price similarity, economics |
| Channel mix | `channel_mix_share` | analog mix / allocation prior |
| Weather sensitivity (governed assumption) | `weather_sensitivity`, `weather_cap_type`, `weather_cap_value` | scenario overlay |
| Demand scale | `planning_basis_annual_units`, `base_weekly_units_py2022`, `structural_growth_rate` | launch-scale prior |
| Region affinity (context only) | `base_portfolio_region_share`, `product_region_affinity`, `regional_season_modifier` | allocation / weather context |
| Public weather | `weather_features_weekly.csv` | seasonal weather context |

The planner **sets** HIS-001's category, season, price band, launch channels, and intended scale (all synthetic assumptions). The analog products then **supply** the demand shape, channel mix, and weather sensitivity. Region remains a downstream allocation and weather-context dimension — never a production forecasting grain (Section 5).

---

## 3. Planning Challenges of a New Product

A mature product can be forecast from its own history. A new product cannot, and that single fact changes the entire discipline.

| Mature-product engine (frozen) | New-product launch (this extension) |
|---|---|
| ≥ 100+ weeks of the product's own history per series | Zero weeks of the product's own history at launch |
| ETS / seasonal models fit to the SKU | No SKU series exists to fit a model to |
| Error measured over a 12-fold expanding backtest | No folds are possible on a product that has not sold |
| Seasonality **learned** from the series | Seasonality **borrowed** from analog products |
| Uncertainty ≈ backtest error | Uncertainty dominated by *whether the analog is right* and *how large the launch will be* |
| A steady safety-stock coverage policy | A front-loaded launch buffer for structurally different risk (Section 17) |

Three challenges follow directly:

1. **No signal to fit.** The forecast must be constructed from comparable products and commercial assumptions, not estimated from the product's own past.
2. **The dominant uncertainty is not model form — it is analog choice and launch scale.** A better statistical model cannot rescue a wrong analog. This is why the framework foregrounds interpretable analog selection and explicit scenario bands rather than model sophistication.
3. **The forecast must serve two very different clocks at once.** A launch needs a *strategic* multi-quarter outlook for category, financial, and lifecycle planning **and** a *near-term execution* view for the launch weeks. These are two horizons, not one — the subject of Section 4.

Forcing the mature time-series engine onto a launch would be indefensible: there is nothing to train on. The launch method is therefore **analog-based, planner-governed, lifecycle-aware, and kept in its own analytical and data paths** so it can never contaminate the frozen mature engine.

---

## 4. Dual-Horizon Planning Architecture

The launch is planned across **two connected horizons**, because a demand planner is answering two different questions simultaneously:

- **18-month rolling IBP forecast — "Where is demand heading?"** — the strategic outlook for category, portfolio, financial, and lifecycle planning.
- **13-week S&OE / launch-execution forecast — "What do we need to do now?"** — the operational loop for the launch weeks.

The two horizons share the same demand truth but serve different decisions and cadences. They are connected: the 13-week execution actuals feed back into and re-anchor the 18-month outlook at each planning cycle.

### A. The 18-month rolling IBP forecast

| Property | Design |
|---|---|
| **Purpose** | Strategic demand outlook; category planning; product-lifecycle planning; financial / inventory planning; consensus forecasting; scenario management |
| **Grain** | **Month × SKU × Channel** |
| **Horizon** | **18 rolling months** |
| **Cadence** | Refreshed every monthly IBP cycle (Section 14) |

**Rolling mechanics — this is a cycle, not a one-time 18-month chart.** The forecast horizon is a *moving window*. At each monthly planning cycle:

```
Cycle N          covers  Month 1  … Month 18
                 (Month 1 is the current near month; Month 18 is the far outlook)

At the next cycle (N+1):
   • Month 1 drops out            (it has now become actual / history)
   • every remaining month shifts one position closer
   • Month 19 enters the far end  (a newly visible outlook month)
   • the horizon remains exactly 18 months

Cycle N+1        covers  Month 2  … Month 19
Cycle N+2        covers  Month 3  … Month 20
```

This demonstrates genuine rolling-forecast thinking: the plan is never "finished," it is continuously rolled forward. Each roll incorporates the latest actuals, the latest commercial assumptions, and a fresh far-horizon month, and each roll is versioned so the planner can see how the outlook evolved (Section 12).

### B. The 13-week S&OE / launch-execution forecast

| Property | Design |
|---|---|
| **Purpose** | Launch execution; weekly demand; initial inventory; early sell-through; service monitoring; reforecast; planner action |
| **Grain** | **Week × SKU × Channel** |
| **Horizon** | **13 weeks** from on-sale |
| **Operational checkpoints** | **Week 1, Week 2, Week 4, Week 8, Week 13** |

For a launch, the *checkpoints matter more than the aggregate*. Week 1–2 velocity is the first read on whether the launch-scale assumption was right; Week 4 is the classic "trust the trend" reforecast point; Week 8 confirms the shape; Week 13 closes the initial-buy assessment.

### Why a demand planner needs both

| 18-month rolling IBP | 13-week S&OE |
|---|---|
| "Where is demand heading?" | "What do we need to do now?" |
| Monthly grain, strategic | Weekly grain, operational |
| Category / portfolio / financial planning | Launch execution and service |
| Consensus, scenarios, versions | Actuals, variance, exceptions, actions |
| Re-anchored by execution actuals | Bounded by the strategic outlook |

Separating strategy from execution — and connecting them through a disciplined feedback loop — is the core of integrated planning. The two horizons are never merged into a single confusing view.

---

## 5. Planning Hierarchy

Integrated planning requires an explicit hierarchy, because consensus forecasting and reconciliation both operate *across levels*. The design uses:

```
PORTFOLIO
    ↓
PRODUCT FAMILY / CATEGORY   (technical outerwear)
    ↓
SKU                          (HIS-001, and the mature SKUs)
    ↓
CHANNEL                      (ECOM · RETAIL · WHOLESALE)
```

**Region** remains available for allocation and weather context (it is central to the mature weather and inventory work), but it is deliberately **not** the production forecasting grain — consistent with the frozen mature engine, which forecasts at SKU × Channel and uses region only for downstream context.

### Why hierarchy matters

- **For consensus forecasting:** different stakeholders naturally speak at different levels. Finance and merchandising think in **category / portfolio** terms; sales and channel partners think in **channel** terms; demand planning builds from **SKU × Channel**. A shared hierarchy lets every input attach to the correct level and roll up or down to a common language.
- **For reconciliation:** the entire top-down vs bottom-up exercise (Section 11) is only meaningful *because* the same demand can be viewed from the top (category target) and from the bottom (SKU × Channel build). The hierarchy is the backbone that lets the two views be compared and reconciled at a defined level.
- **For governance:** exceptions, overrides, and approvals each attach to a level of the hierarchy, which is what makes them auditable.

---

## 6. Cold-Start Forecasting Framework

At launch, HIS-001 has no reliable own history, so the baseline forecast is **constructed**, not estimated. Conceptually:

```
analog demand shape            (normalized seasonal profile from the selected analog(s))
   ×  launch-scale assumption  (planner's expected first-season scale vs the analog)
   ×  seasonal alignment       (align the analog's week/month-of-year to HIS-001's calendar)
   ×  planned channel mix       (from analog channel mix, planner-adjustable)
   ×  approved commercial assumptions
      ─────────────────────────────────────────────
   =  ANALYTICAL / STATISTICAL BASELINE FORECAST     (Forecast Version V0 — Section 12)
```

The output is the **analytical baseline** — the demand-planning starting position, before any commercial input, reconciliation, or consensus. It is the launch equivalent of the mature engine's model output: the disciplined, defensible number the rest of the planning process then debates and governs.

On top of the baseline, the framework produces **three launch-adoption scenarios — LOW / BASE / HIGH** — representing uncertainty in customer adoption, analog fit, and launch scale (Section 16).

**No numerical multipliers are chosen in this step.** The launch-scale factor, the channel mix, and the LOW/BASE/HIGH multipliers are all governed **SYNTHETIC PLANNING ASSUMPTIONS** set and documented in later steps, each with a stated rationale — never fit to future actuals, and never presented as magic numbers.

---

## 7. Analog Selection Framework

*(Designed here; executed in Step 7B.)*

**Principle:** a demand planner must be able to answer *"Why did we use this product as an analog?"* Therefore the selection process must be interpretable — **not a black-box similarity score.**

The framework has three transparent stages:

**Stage 1 — Rules-based shortlist (hard filters).**
Keep only candidates that match on the non-negotiables — broadly the same category and season, with overlapping channels. This removes obviously unsuitable comparables before any scoring and gives the planner a defensible starting set.

**Stage 2 — Transparent weighted similarity score.**
Score each shortlisted candidate on a small set of **named, defensible dimensions**, each normalised to a common scale and combined with **weights the planner can see and change.** The candidate dimensions are drawn from fields that already exist in the frozen data:

| Analog dimension | Frozen source (illustrative) |
|---|---|
| Product family / category match | `product_name` / family |
| Use case | product positioning (assumption) |
| Insulation characteristics | product attributes (assumption) |
| Weather protection | product attributes (assumption) |
| Price positioning | `net_asp_cad`, `msrp_cad` |
| Seasonality profile | `sku_seasonality_factor` by `week_of_year` |
| Weather sensitivity | `weather_sensitivity`, `weather_cap_value` |
| Demand scale | `planning_basis_annual_units` |
| Channel mix | `channel_mix_share` |
| Launch season | `season` |

The **weights are SYNTHETIC PLANNING ASSUMPTIONS**, surfaced to the planner and adjustable — they are not fitted to any outcome. No weights or scores are set in Step 7A.

**Stage 3 — Planner judgment / override.**
The planner confirms, adjusts, or overrides the ranked result, and may blend more than one analog (for HIS-001, a shell analog and an insulation analog may be blended because the product is a hybrid). The blend and the rationale are recorded for audit.

**Why this combination:**

| Approach | Pro | Con |
|---|---|---|
| Rules only | Fully transparent | Brittle; cannot rank close candidates |
| Score only | Ranks candidates | Risks an unexplained "black-box" number |
| **Rules + weighted score + planner override** | Interpretable, governed, planner owns the final call | Requires the planner to engage — which is the point |

The third approach is chosen because it produces a selection a planner can **explain and defend**, which is the whole requirement.

---

## 8. 18-Month Product Lifecycle Forecast

A new product does not behave like a mature SKU on day one, so the long-range outlook must be **lifecycle-aware** rather than assuming immediate maturity. The conceptual lifecycle:

```
PRE-LAUNCH  →  LAUNCH  →  RAMP  →  PEAK / SEASONAL BUILD  →  NORMALIZATION  →  MATURE PRODUCT
```

| Phase | What the 18-month outlook must reflect (conceptually) |
|---|---|
| **Pre-launch** | No own history; forecast is fully analog-based |
| **Launch** | On-sale; first real demand signal begins |
| **Ramp** | Adoption builds; velocity is still climbing toward the analog's seasonal shape |
| **Peak / seasonal build** | The seasonal high point, inherited from the analog's seasonality |
| **Normalization** | Post-peak settling; possible second-season behaviour as the product enters its next annual cycle |
| **Mature product** | Enough clean own-history exists to hand the SKU off to the mature DemandIQ time-series engine |

The 18-month horizon is chosen precisely because it is long enough to see a launch through **more than one season** — the ramp, the first seasonal peak, the post-launch normalization, and the beginning of a second-season pattern — which a 13-week window cannot show. That multi-season view is what makes the outlook useful for category and financial planning.

**No numerical lifecycle factors are invented in this step.** The lifecycle is a conceptual structure here; the ramp, peak, and normalization shapes become governed assumptions in later steps.

---

## 9. Bottom-Up Forecast

The **bottom-up forecast** is the analytical / operational view of demand, generated at the finest planning grain and aggregated upward.

**Grain:** `SKU × Channel`.

For HIS-001, the bottom-up build will eventually combine (in later steps): the selected analog(s), the launch-scale assumption, borrowed seasonality, the planned channel mix, and the approved launch assumptions — i.e., the cold-start construction of Section 6, produced per channel.

**Aggregation path:**

```
SKU × Channel
   →  SKU
   →  Product Family / Category
   →  Portfolio
```

This is the demand planner's "build from the parts" view: it is detailed, operationally grounded, and it is what the initial buy and channel allocation ultimately depend on. It is deliberately kept **separate** from the top-down plan (Section 10) so the two can be compared honestly.

---

## 10. Top-Down Plan

The **top-down plan** is a separate view built from commercial and category expectations rather than from SKU-level construction. Candidate inputs:

- category growth expectation;
- the commercial / merchandising plan;
- portfolio target;
- merchandising expectation for the launch;
- seasonal category outlook.

Top-down planning answers questions of the form:

> *"If the outerwear category is expected to deliver a certain volume or growth, what share should HIS-001 contribute?"*

Because this is a synthetic case study, all top-down inputs are later documented as **SYNTHETIC COMMERCIAL / PLANNING ASSUMPTIONS**. **No category targets, growth rates, or share numbers are created in Step 7A** — inventing them here would produce arbitrary figures with no governance behind them. The purpose of this section is to establish that a top-down view *exists as an independent input* to be reconciled against the bottom-up build, not to populate it.

---

## 11. Forecast Reconciliation

This is a core integrated-planning capability and is designed explicitly. The system compares the **bottom-up forecast** (analog + SKU/channel logic) against the **top-down plan** (category / portfolio commercial expectations) and produces a **reconciled planning forecast**.

```
Top-down plan
        ↘
         RECONCILIATION
        ↗
Bottom-up forecast
        ↓
Reconciled Planning Forecast
```

### What the system displays

| Field | Meaning |
|---|---|
| Top-down forecast | Category / portfolio-derived expectation for HIS-001 |
| Bottom-up forecast | Aggregated SKU × Channel analog build |
| Absolute variance | Bottom-up − top-down, in units |
| Percentage variance | Variance as a % of the top-down (or agreed base) |
| Reconciled forecast | The agreed number after the process below |
| Reconciliation rationale | The documented reason for the reconciled position |

### Recommended reconciliation method (interpretable, tolerance-based)

The recommendation for this portfolio project is a **transparent, tolerance-based reconciliation** rather than a sophisticated hierarchical-optimisation algorithm. With a small synthetic portfolio, an elaborate algorithm would add the *appearance* of rigour without improving the decision, and it would be harder for a planner to explain. The governed flow:

1. **Generate** the bottom-up analytical forecast (Section 9).
2. **Compare** it with the category-level top-down target (Section 10).
3. **Define** an acceptable tolerance band (a governed **SYNTHETIC PLANNING ASSUMPTION**; no value set here).
4. **If within tolerance** → retain the bottom-up forecast; record that it reconciled cleanly.
5. **If outside tolerance** → flag for **planner review** — the variance is an exception, not an automatic override.
6. **Planner action** → apply a governed **proportional adjustment** or a documented **override**, with a stated rationale.
7. **Reaggregate** and confirm the hierarchy reconciles (the parts still sum to the agreed whole).

**Every adjustment is auditable:** the original bottom-up value, the top-down target, the variance, the adjustment made, the reason, and the owner-role are all preserved (this ties directly to the versioning fields in Section 12 and the FVA fields in Section 23). The reconciled forecast is not a silent overwrite — it is a recorded, explainable decision.

---

## 12. Forecast Versions

Enterprise planning treats the forecast as a **versioned object** that evolves through the planning cycle, not a single number that gets overwritten. The launch forecast is designed the same way:

| Version | Name | Owner-role concept | What it represents |
|---|---|---|---|
| **V0** | Analytical Baseline | Demand Planning | Cold-start analog forecast (Section 6) |
| **V1** | Commercial / Merchandising Input | Merchandising | Positioning and launch expectations layered on |
| **V2** | Consensus Forecast | Demand Planning (facilitates) | The agreed cross-functional position (Section 13) |
| **V3** | Approved Plan | Management / IBP | The signed-off official plan |

**Workflow:**

```
Analytical Baseline (V0)
        ↓
Commercial Input (V1)
        ↓
Planner Review
        ↓
Reconciliation (Section 11)
        ↓
Consensus Forecast (V2)
        ↓
Approved Plan (V3)
```

**Every version preserves, for audit:**

- forecast value;
- date / version identifier;
- source (which stage / stakeholder produced it);
- reason for change;
- owner / role concept;
- override delta (the signed change from the prior version).

This is what makes the forecast **governed**: at any later point the planner, the manager, or a hiring reviewer can see exactly how the number moved from the analytical baseline to the approved plan, who moved it, and why. It is also the substrate that makes Forecast Value Add (Section 23) possible — you can only measure whether an override helped if the pre-override and post-override values were both preserved.

---

## 13. Consensus Forecast / IBP

Consensus forecasting is a mandatory part of this extension, and it is designed as a **process, not an average.** Simply averaging every stakeholder's number would discard the very information the process exists to surface — *where* and *why* views differ.

### Participants and what each brings

| Function | Contribution |
|---|---|
| **Demand Planning** | The analytical baseline / analog forecast (V0) |
| **Merchandising** | Product positioning and launch expectations |
| **Sales / Channel** | Channel-specific commercial expectations |
| **Supply Planning** | Capacity and receipt feasibility |
| **Finance / Management** | Portfolio / category outlook and targets |

### The consensus process

1. The **analytical baseline** is generated (demand planning).
2. **Commercial assumptions** are added *separately*, as their own layer — not blended silently into the baseline.
3. **Differences are surfaced** — the process makes disagreement visible rather than averaging it away.
4. **Material variances require a rationale** — a large gap must be explained, not just split.
5. The **demand planner recommends a consensus position**, informed by the reconciliation (Section 11).
6. **Supply feasibility is reviewed separately** (see the critical boundary below).
7. The **approved consensus** becomes the official plan (V3).

### Critical governance: demand vs. supply-constrained plan

> **The UNCONSTRAINED DEMAND FORECAST is kept conceptually separate from the SUPPLY-CONSTRAINED PLAN.**

Demand is **not reduced simply because supply is unavailable.** If the team can only receive part of the demand, that gap is recorded as a supply constraint and a service risk — it does not get hidden by quietly lowering the demand number. This mirrors the mature engine's discipline (demand reconstruction recovers demand hidden by stockouts rather than accepting censored sales as truth), and it keeps the planning honest: the organisation always knows the true size of the opportunity it is choosing not to fully serve.

---

## 14. Monthly IBP Cycle

The 18-month rolling forecast is refreshed on a monthly **Integrated Business Planning** rhythm. The illustrative cadence, and what HIS-001 contributes at each stage:

| Week | IBP stage | HIS-001 contribution |
|---|---|---|
| **Week 1** | **Demand Review** | Refreshed 18-month baseline + launch assumptions; updated LOW/BASE/HIGH adoption scenarios |
| **Week 2** | **Commercial / Merchandising Review** | Launch positioning and channel-specific commercial inputs; V1 commercial layer |
| **Week 3** | **Supply Review** | Initial buy, receipt timing, and feasibility for the launch quantity |
| **Week 4** | **Consensus / Executive IBP** | Approve the consensus scenario for HIS-001 and log the associated launch risks |

This is a **simulation of an IBP rhythm** for demonstration — it is not a claim about any real company's exact process. Its purpose in the case study is to show that the launch forecast is not a static artefact: it is refreshed, challenged, and re-approved on a governed monthly cadence, and each cycle rolls the 18-month horizon forward (Section 4).

---

## 15. Weekly S&OE Cycle

Strategic IBP is deliberately separated from short-term **Sales & Operations Execution**. During the first 13 launch weeks, HIS-001 runs a weekly S&OE loop:

```
Actual sell-through
        ↓
Forecast variance (actual vs launch plan)
        ↓
Inventory / Weeks-of-Supply position
        ↓
Supply feasibility (can we respond in time?)
        ↓
Exception (is a threshold breached?)
        ↓
Planner decision
```

This weekly loop is where the operational decisions live: **CHASE / HOLD / REALLOCATE / CUT / ESCALATE** (Section 22). The distinction from IBP is deliberate — IBP asks *"where is demand heading over 18 months?"* on a monthly cadence; S&OE asks *"what must we do this week?"* on a weekly cadence during the critical launch window. Conflating them would blunt both.

---

## 16. Scenario Planning

Scenario planning is explicit and **multi-dimensional**, and it keeps **two distinct uncertainties separate** so the planner is never confused about which risk is being examined.

### Launch-adoption scenarios (cold-start uncertainty)

| Scenario | Represents |
|---|---|
| **LOW** | Weak adoption; analog scale over-estimated; soft channel response |
| **BASE** | Expected adoption |
| **HIGH** | Strong adoption; analog scale under-estimated; strong channel response |

These capture uncertainty in **customer adoption, analog fit, launch scale, and channel response** — the dominant risks of a launch.

### Weather scenarios (condition uncertainty)

| Scenario | Represents |
|---|---|
| **MILD / NORMAL / SEVERE** | Weather-condition uncertainty, reusing the frozen DemandIQ weather framework |

These are the existing mature-engine weather scenarios and are **not rebuilt** — they are reused as a composable overlay.

### Keeping them separate and composable

The two uncertainties are **never merged into a single confusing label.** A launch has *both* an adoption risk and a weather risk, and they are different in kind. The scenario architecture keeps them as separate, composable layers:

```
Launch base demand (cold-start: LOW / BASE / HIGH)
   → then apply the governed weather overlay (MILD / NORMAL / SEVERE)
     using the analog's weather sensitivity (reused from the frozen weather framework)
```

Future scenario evaluation can look at meaningful combinations — for example **LOW adoption + NORMAL weather**, **BASE adoption + NORMAL weather**, **HIGH adoption + NORMAL weather**, plus selected weather sensitivities where they change the decision. The design deliberately **avoids full 3 × 3 scenario clutter** unless a specific combination improves a decision; more scenarios are only worth showing if they change what the planner does.

---

## 17. Scenario Impact

Scenario planning must answer *"what changes in the decision?"* — not merely *"what changes in the forecast?"* For every material scenario, the future outputs are designed to include:

| Output | Decision relevance |
|---|---|
| Demand units | The scenario's demand level |
| Inventory requirement | What the scenario implies we must hold |
| Weeks of supply | Coverage under the scenario |
| Service risk | Likelihood of missing service |
| Under-buy exposure | Cost of buying too little if this scenario is true |
| Over-buy exposure | Cost of buying too much if this scenario is true |
| Potential planner action | What the planner would do under the scenario |

The point is that a scenario is only worth presenting if it **moves a decision** — a different buy, a different allocation, an escalation. A scenario that changes the forecast but not the action is noise. This keeps the scenario layer disciplined and decision-oriented, consistent with the mature project's philosophy.

---

## 18. Initial Buy

*(Designed here; calculated in a later step.)*

The launch initial-buy recommendation is built conceptually as:

```
Reconciled launch forecast
   +  launch-uncertainty buffer
   +  service ambition
   −  available opening inventory / committed supply   (typically ~0 for a true launch)
   subject to  supply / buy-window constraints
      ─────────────────────────────────────────────
   =  Initial Buy Recommendation
```

**The mature 2.5-week safety-stock policy is deliberately NOT reused by default.** New-product uncertainty is *structurally different* from mature-product variability:

- it is **front-loaded** — largest at Week 0, before any actuals exist;
- it is driven by **analog-choice risk and scale risk**, not by backtest error;
- it is **asymmetric** — an initial under-buy on a hit cannot be recovered within lead time, while an over-buy becomes markdown risk.

Reusing the mature 2.5-week buffer "for convenience" would understate launch risk. The **launch-specific buffer is governed independently** as a later step — for example, covering to a launch quantile derived from the LOW/BASE/HIGH band, or a larger initial coverage that *decays* as actuals arrive, with the service target treated as a **launch service ambition** that may differ from the mature policy. **No buffer size, service level, or buy quantity is set in Step 7A**; all launch policy values will be documented **SYNTHETIC PLANNING ASSUMPTIONS**, separate from mature policy.

---

## 19. Channel Allocation

The initial buy is allocated across the launch channels:

```
Initial Buy
        ↓
Channel Allocation
        ↓
ECOM  ·  RETAIL  ·  WHOLESALE
```

Candidate inputs to the allocation:

- analog channel mix;
- launch strategy (e.g., a DTC-led launch weights ECOM/RETAIL first);
- channel demand expectations;
- commercial priorities;
- channel uncertainty;
- ability to rebalance inventory after launch.

**Design intent:** the allocation should **hold back rebalancing flexibility** rather than committing every unit up front, because early sell-through will reveal channel skew that the pre-launch mix could not. The system is designed to later **track whether the actual channel mix differs from the planned mix** (a monitored KPI, Section 24), which is what triggers a REALLOCATE decision (Section 22). **No allocation percentages are invented in Step 7A.**

---

## 20. Early Sell-Through

Once launch actuals exist, the system monitors the launch at each checkpoint (**Week 1, 2, 4, 8, 13**). The launch-monitoring KPIs:

| KPI | Why it matters |
|---|---|
| Actual units vs plan | First read on scale error |
| Cumulative sell-through % | Inventory depletion pace |
| Weekly demand velocity | Trend vs the analog curve |
| Remaining inventory | Coverage position |
| Weeks of supply (WOS) | Forward coverage risk |
| Availability | Whether a stockout is censoring the launch signal |
| Channel-mix variance | Whether the allocation was right |
| Launch forecast bias | Directional error in the launch forecast |
| Cumulative forecast error | Overall analog-quality read |

**Why early-launch monitoring matters:** the first weeks are the *highest-information, highest-stakes* window of the entire launch. They are the first evidence of whether the analog and scale assumptions were right, and they arrive while there is still time to act — to chase more units on a hit, or to cut exposure on a miss. Availability is watched closely because a launch stockout **censors the very demand signal the planner is trying to learn from** — exactly the problem the mature engine's demand reconstruction was built to handle.

---

## 21. Reforecast & Lifecycle Transition

The launch forecast is designed to **evolve from analog-based to actual-based** as the product accumulates its own history:

```
PRE-LAUNCH   →  Analog forecast (100% analog)
     ↓
EARLY LAUNCH →  Analog forecast + actual demand (actuals up-weighted as they accrue)
     ↓
MATURING     →  Actual demand increasingly drives the forecast
     ↓
ESTABLISHED  →  Transition into the mature DemandIQ forecasting engine
```

The transition is **interpretable and planner-tunable**, not a black box: as observed weeks accumulate, the forecast shifts weight from the analog prior toward the actual trend, governed by an **analog-confidence assumption** (larger = trust the analog longer). The **handoff rule** — enough weeks of clean, uncensored own-history to graduate HIS-001 into the mature time-series engine — closes the lifecycle loop and connects this extension back to the frozen project.

Throughout, **forecast versions are preserved** (Section 12), so the planner can always see:

- the **original launch forecast**;
- the **current reforecast**;
- the **variance** between them;
- the **reason for change**.

---

## 22. Planner Decisions

The weekly S&OE loop resolves to one of five governed planner states, each defined by an explicit business condition:

| Action | Business condition (conceptual) |
|---|---|
| **CHASE** | Actual demand materially **>** plan **AND** coverage is insufficient **AND** execution is feasible |
| **HOLD** | Actuals broadly tracking the plan within tolerance |
| **REALLOCATE** | Total portfolio demand acceptable, but the **channel mix** differs materially from plan |
| **CUT** | Actual demand materially **<** plan **AND** over-buy / markdown risk is increasing |
| **ESCALATE** | A material risk is detected but execution feasibility is unresolved |

**Governance boundary — the most important rule:**

> **RISK SIGNAL ≠ EXECUTION AUTHORIZATION.**

Detecting that demand is running hot does not, by itself, authorise a chase. A CHASE is only valid when demand materially exceeds plan **and** coverage is short **and** the chase is genuinely feasible within lead time. When a strong signal exists but feasibility is unknown or unmodeled — supplier lead time, expedite capacity, transfer transit, PO-change windows — the correct state is **ESCALATE into an S&OE review**, not an automatic execution. This is the direct launch analogue of the frozen mature engine's P1-ESCALATE boundary, and it keeps the system from producing false-precision recommendations it cannot stand behind.

---

## 23. Forecast Governance / FVA

The system is designed to eventually answer a question every serious planning organisation asks: **did planner and commercial overrides actually improve the forecast, or damage it?** This is the **Forecast Value Add (FVA)** concept.

Conceptually, once actuals arrive, the system compares:

```
Baseline Forecast Error      (the analytical V0 baseline)
        vs.
Consensus / Override Error   (after commercial input and planner overrides)
```

If overrides consistently make the error *worse*, that is a governance finding — the process is adding noise, not value. If they make it *better*, the overrides are earning their place.

**Fields designed to support this (computed later, not now):**

| Field | Meaning |
|---|---|
| `baseline_forecast` | The analytical baseline (V0) |
| `override_units` | Signed change applied by commercial / planner input |
| `override_pct` | Override as a % of baseline |
| `override_reason` | Documented rationale |
| `consensus_forecast` | The agreed consensus number (V2) |
| `actual_demand` | Realised demand (evaluation only) |
| `baseline_error` | Error of the baseline vs actual |
| `consensus_error` | Error of the consensus vs actual |

**No FVA is calculated in Step 7A** — this section defines the fields and the governance concept. Together with the version history (Section 12) and the reconciliation audit trail (Section 11), FVA completes the forecast-governance story: every number is versioned, every change is explained, and the value of every change can later be measured.

---

## 24. KPI Framework

The KPI framework is aligned to demand planning and deliberately spans **more than forecast accuracy** — because launch performance is a planning outcome, not just a forecasting one.

### Forecast KPIs

- WAPE
- Bias
- MAE
- Week-4 cumulative error
- Week-13 cumulative error

### New-product KPIs

- Launch forecast accuracy
- Sell-through
- Demand velocity
- Initial-buy accuracy
- Channel-mix variance

### Inventory / service KPIs

- Fill rate
- Weeks of supply (WOS)
- Under-buy units
- Over-buy units
- Inventory remaining

### IBP / governance KPIs

- Top-down vs bottom-up variance
- Consensus adjustment
- Override %
- Forecast Value Add (concept)
- Scenario variance
- Exception count
- Forecast version changes

**Framing:** the four groups are intentionally ordered from *forecast* → *product* → *inventory/service* → *governance*, because the case study's message is that **forecast accuracy is only one part of planning performance.** A launch can be forecast reasonably and still be planned badly (wrong buy, wrong channel split, ungoverned overrides) — or forecast imperfectly and still be planned well through disciplined buffers, reconciliation, and consensus. The KPI framework is built to show both.

---

## 25. Enterprise Planning Workflow Concepts

DemandIQ's launch extension is deliberately designed around concepts that are standard in enterprise planning organisations:

- planning hierarchies;
- rolling horizons;
- forecast version management;
- scenario planning;
- planner overrides;
- consensus workflows;
- top-down / bottom-up reconciliation;
- exception management;
- approval / governance;
- audit trail.

These are the same conceptual building blocks found in enterprise planning platforms such as **o9, Blue Yonder, Anaplan, and Oracle**. The design uses them because they are the right way to structure integrated planning — the concepts are transferable across platforms.

> **Honesty statement.** *This portfolio demonstrates planning concepts and workflow design; it does not claim hands-on implementation experience in these commercial platforms.*

The platform names above are referenced only to locate these concepts in the wider planning landscape. They are **not** part of a "tools used" or "skills" list, and no implementation experience in them is claimed. What DemandIQ demonstrates is fluency in the **planning concepts** those platforms operationalise — hierarchies, rolling forecasts, versions, scenarios, consensus, reconciliation, exceptions, governance, and auditability — implemented here transparently in an open analytical stack.

---

## 26. Economic Exposure

The launch continues DemandIQ's **planning-exposure** approach to economics. The candidate launch measures:

| Measure | Launch meaning |
|---|---|
| Revenue opportunity | Directional upside (price × forecast) |
| Under-buy exposure | Demand missed by committing too little inventory |
| Over-buy exposure | Units committed that will not sell at full price |
| Markdown exposure | End-of-season clearance risk |
| Carrying-cost proxy | Holding cost of launch inventory |

These reuse the existing frozen economic vocabulary (illustrative fields include `total_underbuy_exposure_cad`, `total_overbuy_event_exposure_cad`, `markdown_revenue_reduction_cad`, `weekly_carrying_cost_exposure_cad`, `total_two_sided_planning_exposure_cad`, `net_asp_cad`). The launch decision is inherently **two-sided** — the cost of buying too little vs. too much — which makes the two-sided planning-exposure measure the natural headline.

> **Boundary.** COGS is unavailable, so the extension does **not** claim profit, actual savings, or real financial impact. All figures are **planning exposure proxies**, used to prioritise decisions and review queues — never presented as accounting outcomes.

---

## 27. Cannibalization

HIS-001, as a hybrid shell/insulation product, may overlap commercially with existing portfolio products — **APS-001, CTS-001, IMH-001.**

With only three mature SKUs and synthetic data, a **causal cannibalization model is not defensible** — there is no basis to *estimate* how much demand HIS-001 draws from each existing product. Fabricating causal evidence would violate the project's governance.

**Recommendation:** treat cannibalization as **either**:

- an **optional, planner-set scenario overlay** — a documented, clearly-labelled **SYNTHETIC PLANNING ASSUMPTION** (e.g., "assume HIS-001 draws a stated share from the nearest analog"), used to explore sensitivity; **or**
- a **documented limitation** — explicitly stated as out of scope for causal modelling.

By default the extension **documents cannibalization as a limitation** and offers the scenario overlay only as an optional, assumption-based sensitivity — never as an estimated or causal result.

---

## 28. Evaluation Design

Because a cold-start launch cannot be validated the way a mature time-series model can, the evaluation strategy is designed honestly around what the data can support.

| Option | Design | Honest read |
|---|---|---|
| **A. Leave-one-product-out pseudo-launch** | Hide a mature SKU's own history, treat it as a launch, pick analogs from the remaining SKUs using only pre-launch fields, and forecast its early weeks vs its actual reconstructed demand | Only **3 mature SKUs** exist → at most 3 pseudo-launches with ≤2 candidate analogs each. **Illustrative of the method, not statistically robust.** |
| **B. SKU × Channel pseudo-launch harness** | Treat individual historical SKU × Channel cells as pseudo-launches and use other cells as analogs | Provides real sample size to validate the *methodology*. Must be framed **evaluation-only** — it does **not** reintroduce region-level production forecasting. |
| **C. Controlled synthetic hidden launch truth** | Generate a controlled launch demand truth for HIS-001 to score the cold-start method against a known answer | Controlled and known, but must use independent noise/scale to avoid circularity, and is **evaluation truth only**. |

**Recommended combination:** use **(B)** as the primary methodology-validation harness (it has the sample size), support it with **(C)** synthetic hidden truth for controlled scoring of the forward launch, and present **(A)** leave-one-product-out as an illustrative sanity check with its small-sample caveat stated plainly.

**Transparency requirement:** only three mature SKUs exist, so historical analog validation is inherently limited — this is stated openly, not hidden behind a single accuracy number. Any **synthetic hidden truth, if used, is EVALUATION ONLY** — scored against, **never** fed into the forecast as an input — exactly mirroring the mature engine's rule that hidden true demand exists solely to evaluate reconstruction.

---

## 29. Future Planning Workspace

The launch capability is envisioned as a professional launch-planning workspace — a business product concept, presented here as sections rather than as build instructions. It is a **separate** workflow from the frozen mature control tower and reads launch-only data.

| # | Workspace section | Planning question it answers |
|---|---|---|
| 1 | **Launch Executive Outlook** | What is the launch outlook and what needs attention now? |
| 2 | **18-Month Rolling Forecast** | Where is demand heading over the strategic horizon? |
| 3 | **Analog Selection** | Which product(s) are we using as the analog, and why? |
| 4 | **Top-Down vs Bottom-Up** | Do the commercial and analytical views agree, and how were they reconciled? |
| 5 | **Consensus Forecast** | What did the cross-functional team agree, and where did views differ? |
| 6 | **Scenario Planning** | How do adoption and weather scenarios change the decision? |
| 7 | **Initial Buy & Channel Allocation** | How much to commit, and to which channels? |
| 8 | **Early Sell-Through** | Is the launch tracking plan at each checkpoint? |
| 9 | **Exceptions & Planner Actions** | What breached tolerance, and what is the decision? |
| 10 | **Forecast Governance / Version History** | How did the forecast evolve, who changed it, and did overrides add value? |

The workspace is designed to drill from the executive outlook down to SKU × Channel and week, and to make the *decision* — not the model mechanics — the centre of every view.

---

## 30. Limitations

Stated plainly, as the project's governance requires:

- **Everything about HIS-001 is synthetic** — no real product, plan, price, or performance; economics are planning exposure proxies, not profit.
- **The analog pool is small (3 SKUs)** → launch back-testing is illustrative, not statistically powerful.
- **Analog choice is the dominant risk**, larger than model form — the framework foregrounds it with interpretable scoring and planner override.
- **Top-down inputs are synthetic commercial assumptions**, not real category targets.
- **Cannibalization is an assumption / scenario, not a causal estimate.**
- **The launch weather overlay** beyond the mature framework's horizon requires extending the analog weather scenario, not rebuilding the frozen weather framework.
- **Execution feasibility is not fully modeled** — supplier lead time, expedite, transfer transit, PO-change windows — so risk detection escalates rather than auto-executes.
- **Enterprise-platform concepts are demonstrated, not implemented** — no hands-on o9 / Blue Yonder / Anaplan / Oracle experience is claimed.
- **The lifecycle handoff** from launch to mature engine is a governed rule, not an automatic switch.

---

## 31. Implementation Roadmap

Step 7A is design only. The subsequent steps implement the framework in dependency order, each producing governed outputs in launch-only data and code paths that leave the frozen mature engine untouched.

| Step | Deliverable | Notes |
|---|---|---|
| **7A** | **New Product Launch & Integrated Planning Design** *(this document)* | Design only — no analytics, no data, no numbers |
| **7B** | **Analog Product Selection & Launch Assumption Setup** | Rules shortlist + interpretable weighted score + planner override; select/blend the analog(s) for HIS-001 and set the governed launch assumptions. **Next approved step.** |
| 7C | Cold-Start & 18-Month Lifecycle Forecast | Analog shape × scale × seasonality × channel mix × LOW/BASE/HIGH; lifecycle-aware 18-month build + weather overlay |
| 7D | Top-Down / Bottom-Up Reconciliation & Consensus | Bottom-up build, synthetic top-down plan, tolerance-based reconciliation, V0→V3 versions, consensus position |
| 7E | Initial Buy & Channel Allocation | Launch-specific buffer (not the mature 2.5-week policy); channel allocation with rebalancing reserve |
| 7F | Early Sell-Through & Reforecast (needs synthetic launch actuals, evaluation-governed) | Checkpoint monitoring; analog→actual blend; CHASE / HOLD / REALLOCATE / CUT / ESCALATE |
| 7G | FVA, Exception Management & Launch Planning Workspace | Governance KPIs, exception surfacing, and the separate launch workspace + case-study update |

**Guardrails carried through every step:** launch work stays in separate data and code paths; no frozen mature output is altered; synthetic assumptions are labelled at the point of use; hidden truth (if generated) is evaluation-only; and no number is presented without a governed, documented rationale.

---

*Step 7A deliverable — design only. No launch forecast, launch data, initial-buy calculation, or synthetic actuals were produced. The mature-product DemandIQ engine remains complete and frozen. The launch methodology is analytically separate by construction, and every launch assumption is a SYNTHETIC PLANNING ASSUMPTION. Economic measures are planning exposure proxies, not accounting profit.*
