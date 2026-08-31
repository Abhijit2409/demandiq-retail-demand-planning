# DemandIQ — Step 6B — Streamlit Dashboard Architecture & UX Specification

**Status:** DESIGN ONLY. No Streamlit code is built in Step 6B. Implementation is Step 6C.
**Scope:** Information architecture, page/UX design, chart specs, source-column mappings, navigation, interactions, acceptance criteria, and the proposed Step 6C file structure.
**Governance:** Steps 4A–5 and Step 6A are FROZEN. This dashboard READS the frozen Step 6A semantic layer and frozen Step 4A/4B/4C evidence. It introduces **no new analytics**, no region-level forecasting, no recomputed risk logic, and no invented recommendations.

---

## 1. Dashboard objective

Turn the frozen DemandIQ planning engine into a **decision product** that a demand planner can read in ~30 seconds at the top and drill into for defensible, governed action. The dashboard must make one core tension legible:

> 13-week aggregate portfolio service looks healthy (Base fill ≈ 98.77% ≥ 92% target), **yet** three SKU-channel series suffer repeated weekly service failures, and the whole portfolio finishes below its 2.5-week safety-stock buffer — so the planner response is deliberately **split** (P1 ESCALATE vs P2 PROTECT) with **no automatic chase release**.

The dashboard is a governed presentation layer over Step 6A. It never re-derives forecasts, fills, risk types, or actions.

---

## 2. Target users / personas

| Persona | Role | What they need | Primary pages |
|---|---|---|---|
| **Primary** | Demand Planner / Senior Demand Planner | Which series to act on now; why; what the governed action is | 1 → 3 → 4 |
| **Secondary** | IBP / Supply Planning Manager | Portfolio outlook, service vs target, buffer health, exposure proxies | 1 → 2 → 3 |
| **Portfolio reviewer** | Hiring Manager / Analytics Lead | Credibility: methodology, governance, provenance, limitations | 1 → 5 |

Design intent: **premium, minimal, analytical, outdoor-inspired** — a purpose-built planning tool, not a default Streamlit demo. No specific brand trade dress.

---

## 3. Core business questions (page ownership)

| # | Question | Owned by |
|---|---|---|
| 1 | What is the 13-week demand outlook? | Page 2 (surfaced on Page 1) |
| 2 | Is current inventory + committed supply enough to protect service? | Page 1 + Page 3 |
| 3 | Which SKU-channel combos need immediate attention? | Page 3 + Page 4 |
| 4 | Why can portfolio service look healthy while weekly failures occur? | Page 3 (the flagship page) |
| 5 | What should the planner do? | Page 4 |
| 6 | What analytical governance supports these decisions? | Page 5 |

---

## 4. User journey

```
                       ┌─────────────────────────────────────────┐
                       │  PAGE 1 — EXECUTIVE COMMAND CENTER        │
                       │  "State of the business in 30 seconds"    │
                       │  Status banner + 6 KPI cards + demand trend│
                       └───────────────┬──────────────────────────┘
                                       │ "What needs attention?"
              ┌────────────────────────┼───────────────────────────┐
              ▼                        ▼                            ▼
   ┌───────────────────┐   ┌────────────────────────┐   ┌────────────────────┐
   │ PAGE 2 — DEMAND   │   │ PAGE 3 — SERVICE &     │   │ PAGE 4 — PLANNER   │
   │ OUTLOOK           │   │ INVENTORY RISK          │   │ DECISION QUEUE     │
   │ where/when demand │   │ heatmap + receipts gap  │   │ 9-series table →   │
   │ rises             │   │ + WOS vs 2.5wk          │   │ select → detail    │
   └───────────────────┘   └───────────┬────────────┘   └─────────┬──────────┘
                                        │ "prove it"                │ "act on one series"
                                        ▼                           ▼
                            ┌──────────────────────────────────────────────┐
                            │ PAGE 5 — FORECAST & GOVERNANCE                 │
                            │ reconstruction · champions · weather · policy │
                            │ · provenance · limitations                     │
                            └──────────────────────────────────────────────┘

Drill path (context preserved by global SKU/Channel filter on pages 2–4):
   Portfolio  →  Risk  →  SKU × Channel  →  Week
```

---

## 5. Navigation strategy

**Recommendation for Step 6C: programmatic navigation via `st.navigation` + `st.Page` defined in `app.py`** (Streamlit ≥ 1.36), **not** the legacy auto-discovered `pages/` folder.

Rationale:
- **Explicit order, labels, and icons** — the five pages must appear in decision order (1→5), which folder auto-discovery cannot guarantee cleanly.
- **Shared, cached data load once** in `app.py` before dispatching to a page — all pages read the same three Step 6A CSVs; load + `@st.cache_data` once, pass down. Avoids reloading per page.
- **Global sidebar filters** rendered once in `app.py` and shared, with per-page opt-in (see §11).
- **Grouping** — pages 1–4 under a "Planning" group, page 5 under "Evidence & Governance", visually separating the operational product from the credibility appendix.
- Future-proof: easy to add auth/landing later without restructuring.

Sidebar layout: brand lockup (text wordmark "DemandIQ" + subtitle "Premium Outdoor Apparel · IBP / S&OE Simulation") → nav → global filters → provenance footer ("SYNTHETIC + PUBLIC → DERIVED · portfolio simulation, not any real company's data").

---

## 6. Five-page information architecture (overview)

| Page | Title | Primary question | Main visuals | Main source |
|---|---|---|---|---|
| 1 | Executive Command Center | Outlook + what needs attention now | Status banner, 6 KPI cards, portfolio demand trend, P1-first decision queue | Executive + Weekly + Series |
| 2 | Demand Outlook | Where/when does demand rise | Weekly Mild/Base/Severe forecast (peak marker), demand by SKU, demand by Channel | Weekly + Series |
| 3 | Service & Inventory Risk | Healthy aggregate vs weekly P1 failures | Weekly fill-rate heatmap (9×13), demand vs committed receipts, ending WOS vs 2.5wk | Weekly + Series |
| 4 | Planner Decision Queue | What to investigate first | Interactive 9-series table → selected-series detail panel + trajectory | Series + Weekly |
| 5 | Forecast & Governance | Why trust this | Reconstruction card, champion table + WAPE bar, weather governance, policy, provenance, limitations | Frozen 4A/4B/4C evidence |

---

## 7–15. Page-by-page design

Each chart carries a full 10-field spec:
**(1) title · (2) business question · (3) chart type · (4) x-axis · (5) y-axis · (6) color/group · (7) reference line · (8) source file · (9) source columns · (10) interaction.**

Source file shorthand:
- **EXEC** = `05_outputs/decision_layer/DemandIQ_Step6A_Executive_KPI_Summary.csv` (1 row × 33)
- **SERIES** = `05_outputs/decision_layer/DemandIQ_Step6A_Series_Decision_Summary.csv` (9 rows × 31)
- **WEEKLY** = `05_outputs/decision_layer/DemandIQ_Step6A_Weekly_Planning_Trajectory.csv` (117 rows × 25)

---

### PAGE 1 — EXECUTIVE COMMAND CENTER

**Business question:** *What is the 13-week outlook and what requires attention now?*
**Filter behavior:** Page 1 is **always full portfolio** (governed truth). Global SKU/Channel filters do **not** apply here, to prevent a filtered fill-rate being misread as the governed 98.77%. (See §11.)

#### Wireframe
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ DemandIQ — Executive Command Center            13-week horizon: 2026-06-29 → 09-21│
├──────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────────────────────┐ │
│ │ ▲ ACTION REQUIRED                                            [amber band]  │ │
│ │ 3 P1 WEEKLY_SERVICE_RISK series → ESCALATE (S&OE review)                   │ │
│ │ 6 P2 LOW_COVERAGE_RISK series → PROTECT (retain buffer/chase option)       │ │
│ │ Aggregate Base fill 98.8% ≥ 92% target · 0 automatic chase/realloc released│ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐            │
│ │13W Base│ │Base    │ │Service │ │P1      │ │Safety- │ │Immed.  │            │
│ │Demand  │ │Fill    │ │Target  │ │Excep-  │ │Stock   │ │Chase   │            │
│ │36,435  │ │98.8%   │ │92.0%   │ │tions 3 │ │Gap     │ │Release │            │
│ │units   │ │▲ +6.8pp│ │(policy)│ │of 9    │ │7,000 u │ │0 units │            │
│ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘            │
│                                                                                │
│ ┌──────────────────────────────────────────┐  ┌───────────────────────────┐  │
│ │ C1.1  Portfolio 13-week demand (Base line, │  │ Decision queue (P1 first) │  │
│ │       Mild/Severe band)                    │  │ ─────────────────────────  │  │
│ │   units                                    │  │ P1 APS WHOLESALE ESCALATE │  │
│ │    3.6k ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈● peak 09-07       │  │ P1 CTS RETAIL    ESCALATE │  │
│ │    ▁▂▃▃▄▅▆▆▇▇█▇▆                            │  │ P1 IMH WHOLESALE ESCALATE │  │
│ │         weeks 1..13                        │  │ P2 (6) …         PROTECT  │  │
│ └──────────────────────────────────────────┘  └───────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

#### KPI cards (`st.metric` ×6, in `st.columns(6)`) — max 6, no model metrics on Page 1
| Card | Value source | Notes / delta |
|---|---|---|
| 13W Base Demand | EXEC `base_13w_demand_units` | 36,434.66 → "36,435 units" |
| Base Fill Rate | EXEC `base_13w_fill_rate` | delta vs target = `base_13w_fill_rate − service_target_fill_rate` (+6.8pp), delta green |
| Service Target | EXEC `service_target_fill_rate` | 92.0%, neutral (policy, not a KPI to beat visually) |
| P1 Exception Count | EXEC `p1_weekly_service_risk_series` | "3 of 9" (`/total_series`); amber |
| Safety-Stock Protection Gap | EXEC `base_safety_stock_protection_gap_units` | 7,000.21 u; framed as buffer shortfall, **not** procurement order (neutral/slate) |
| Immediate Chase Release | EXEC `immediate_chase_release_units` | 0 units; neutral (intentional, not a failure) |

#### Status banner
- Text driven by EXEC `portfolio_decision_status` + counts `p1_weekly_service_risk_series`, `p2_low_coverage_risk_series`.
- Color = amber (P1 present) per §14. Rendered via `st.container(border=True)` + colored left rule / `st.warning`-style but custom-styled.

#### Charts
**C1.1 — Portfolio 13-week demand (Base with Mild/Severe context)**
1. "Portfolio 13-Week Demand Outlook" · 2. When does portfolio demand rise? · 3. Line + shaded band (Plotly GO) · 4. `forecast_week_start` (13 weeks) · 5. units · 6. Base = graphite solid line; Mild/Severe = filled band (light clay) · 7. Peak marker annotation at `2026-09-07` · 8. WEEKLY (aggregated to portfolio) · 9. `forecast_week_start`, `base_forecast_units`, `mild_scenario_forecast_units`, `severe_scenario_forecast_units` (summed across 9 series per week); peak from EXEC `peak_base_demand_week`, `peak_base_weekly_demand_units` · 10. hover shows week + Mild/Base/Severe units; static (no filter).

**Decision queue (mini)** — `st.dataframe`, P1 first: SERIES columns `priority_tier, sku_id, channel_id, risk_type, planner_action` sorted `priority_tier` asc then `weeks_below_service_target` desc. Executive-level columns only (no gap units here). Row click optional → deep-link to Page 4 (nice-to-have; default read-only).

**Page-1 acceptance:** banner reflects 3 P1 / 6 P2; exactly 6 KPI cards; demand trend shows Base + scenario band + peak at 2026-09-07; queue lists 3 P1 rows before any P2; no forecast WAPE/bias anywhere on this page.

---

### PAGE 2 — DEMAND OUTLOOK

**Business question:** *Where and when is demand expected to rise?*
**Filters:** global SKU + Channel apply (subset which series aggregate into the visuals). Optional scenario `st.segmented_control` {Mild, Base, Severe} affecting only C2.2/C2.3 emphasis.

#### Wireframe
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Demand Outlook            [SKU ▾ all] [Channel ▾ all]     scenario: (Mild|Base|Severe)│
├──────────────────────────────────────────────────────────────────────────────┤
│ C2.1  Weekly demand forecast — Mild / Base / Severe                            │
│   units                                        ● peak Base 09-07 ≈ 3,640       │
│   3.6k                          ┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈●                                │
│        ░░░ severe band ░░░  ▂▃▄▅▆▇█▇▆   (Base bold line)                        │
│        weeks 2026-06-29 ................................ 2026-09-21             │
├───────────────────────────────────────┬──────────────────────────────────────┤
│ C2.2  13-week demand by SKU            │ C2.3  13-week demand by Channel       │
│   APS ████ 5,234                       │   ECOM     ████████ 16,231            │
│   CTS ██████████ 14,697                │   RETAIL   █████ 11,199               │
│   IMH ████████████ 16,504              │   WHOLESALE████ 9,004                 │
└───────────────────────────────────────┴──────────────────────────────────────┘
(illustrative magnitudes; values come from data)
```

**C2.1 — Weekly demand forecast (Mild/Base/Severe)**
1. "Weekly Demand Forecast — Scenario Range" · 2. When does demand rise and how wide is scenario uncertainty? · 3. Line (Base) + shaded Mild–Severe band (Plotly GO) · 4. `forecast_week_start` · 5. units · 6. Base graphite line; band clay fill · 7. peak Base marker `2026-09-07` · 8. WEEKLY · 9. `forecast_week_start`, `base_forecast_units`, `mild_scenario_forecast_units`, `severe_scenario_forecast_units` (summed over filtered series) · 10. hover Mild/Base/Severe; filter-reactive.

**C2.2 — 13-week demand by SKU**
1. "13-Week Demand by SKU" · 2. Which SKU drives volume? · 3. Horizontal bar · 4. units · 5. `sku_id` (APS/CTS/IMH) · 6. one hue per SKU (categorical, non-alarming) · 7. none · 8. SERIES (or WEEKLY summed) · 9. `sku_id`, `base_13w_demand_units` (+ `mild/severe` if scenario toggled) · 10. hover exact units; filter-reactive; click optional cross-filter.

**C2.3 — 13-week demand by Channel**
1. "13-Week Demand by Channel" · 2. Which channel drives volume? · 3. Horizontal bar · 4. units · 5. `channel_id` (ECOM/RETAIL/WHOLESALE) · 6. one hue per channel · 7. none · 8. SERIES · 9. `channel_id`, `base_13w_demand_units` · 10. hover; filter-reactive.

**Governance guard:** **No Region filter** anywhere (governed grain = SKU × Channel). Scenario toggle changes displayed series, never recomputes forecasts.

**Page-2 acceptance:** C2.1 shows all three scenarios and the 2026-09-07 peak; SKU and Channel breakdowns sum to the portfolio Base total (36,434.66) when no filter applied; region absent.

---

### PAGE 3 — SERVICE & INVENTORY RISK  *(flagship page)*

**Business question:** *How can healthy 13-week aggregate service coexist with P1 execution risk?*
**Filters:** global SKU + Channel apply. This page must visually resolve the central tension.

#### Wireframe
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Service & Inventory Risk       [SKU ▾ all] [Channel ▾ all]                     │
│ Insight: aggregate Base fill 98.8% ≥ 92%, but 3 series miss weekly service ≥2× │
├──────────────────────────────────────────────────────────────────────────────┤
│ C3.1  Weekly Base fill-rate heatmap (9 series × 13 weeks)   [<92% = warm]      │
│                w1 w2 w3 w4 w5 w6 w7 w8 w9 w10 w11 w12 w13                       │
│ APS WHOLESALE  ██ ██ ██ ██ ██ ██ ██ ▓33%██ ██  ██  ██  ██   ◄ P1               │
│ CTS RETAIL     ██ ██ ██ ██ ██ ██ ██ ▓65%██ ██  ██  ██  ██   ◄ P1               │
│ IMH WHOLESALE  ██ ██ ██ ██ ██ ██ ██ ▓74%██ ██  ██  ██  ██   ◄ P1               │
│ APS ECOM …     ██ ██ ██ … (all ≥92%)                                          │
│                                       ▲ week 2026-08-24                        │
├───────────────────────────────────────┬──────────────────────────────────────┤
│ C3.2 Demand vs committed receipts      │ C3.3 Ending WOS vs 2.5-wk policy      │
│  (portfolio; receipts=0 on 08-24)      │  9 series bars, ref line 2.5          │
│   units  ▉demand  ▏receipts            │  APS ECOM ▍1.25                       │
│   ▉▉▉▉▉▉▉ ▉0◄08-24 ▉▉▉▉▉               │  CTS WHOLE ▍0.91  ──── 2.5 policy ─── │
│                                        │  P1 series ▏0.00                      │
└───────────────────────────────────────┴──────────────────────────────────────┘
```

**C3.1 — Weekly fill-rate heatmap** *(the single most important visual)*
1. "Weekly Base Fill Rate — 9 Series × 13 Weeks" · 2. Where and when does weekly service fail despite healthy aggregate? · 3. Heatmap (Plotly GO Heatmap or `px.imshow`) · 4. `horizon_week` / `forecast_week_start` (13 cols) · 5. series label `sku_id / channel_id` (9 rows, sorted P1 first) · 6. sequential-through-threshold color: cells ≥92% cool/neutral, <92% warm (amber→clay), diverging at the 0.92 break · 7. threshold encoded in colorscale midpoint at 0.92; annotate worst cells · 8. WEEKLY · 9. `sku_id`, `channel_id`, `horizon_week`, `base_fill_rate`, `weekly_base_fill_below_target_flag`; row order by SERIES `priority_tier` · 10. hover shows week, fill %, and gap units; clicking a row can set the global series selection for Page 4. **Do not hardcode** the 33.2/65.4/74.1 worst values — they render from `base_fill_rate`.

**C3.2 — Demand vs committed receipts**
1. "Demand vs Committed Receipts — the 2026-08-24 gap" · 2. Why does a shared week create localized failure? · 3. Combo: bars (`committed_receipt_units`) + line (`base_forecast_units`), Plotly GO · 4. `forecast_week_start` · 5. units · 6. receipts = slate bars, demand = graphite line · 7. vertical marker/annotation at `2026-08-24` (all-series `committed_receipt_units = 0`) · 8. WEEKLY (portfolio sum, or per selected series) · 9. `forecast_week_start`, `committed_receipt_units`, `base_forecast_units` · 10. hover; filter-reactive. **Caption (governed, no over-claim):** "Shared zero-receipt week + thin channel buffers → localized weekly service failure. Only thin-buffer series stock out; causality limited to what the simulation supports."

**C3.3 — Ending WOS vs safety-stock policy**
1. "Ending Weeks-of-Supply vs 2.5-Week Policy" · 2. Why are the other six series still P2 PROTECT? · 3. Horizontal bar with reference line · 4. weeks of supply · 5. series `sku_id / channel_id` · 6. bar hue by `priority_tier` (P1 amber, P2 slate) · 7. **reference line at 2.5 weeks** (safety-stock policy); optional 8.0 excess line (context only) · 8. SERIES · 9. `sku_id`, `channel_id`, `base_final_wos`, `ending_safety_stock_units`, `priority_tier` · 10. hover shows ending inventory, safety stock, gap (`base_safety_gap_units`). Shows all 9 finishing **below** 2.5 → explains portfolio-wide thin coverage; the 3 P1 sit at ~0 WOS.

**Page-3 acceptance:** heatmap renders 9×13 with a visible 0.92 threshold and the three P1 rows highlighted; the three worst cells align to 2026-08-24; receipts chart makes the zero-receipt week obvious; WOS chart draws the 2.5 reference and shows all series below it. No causal claim beyond "shared gap + thin buffer".

---

### PAGE 4 — PLANNER DECISION QUEUE

**Business question:** *What should the planner investigate first?*
**Filters:** global SKU + Channel apply. Default selection = first P1 row (APS-001 / WHOLESALE).

#### Wireframe
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Planner Decision Queue           [SKU ▾ all] [Channel ▾ all]                   │
├──────────────────────────────────────────────────────────────────────────────┤
│ 9-series table (P1 → P2), single-row select                                    │
│ ┌─ tier sku      chan     risk               action  base% minwk% wksbelow wos│ │
│ │● P1  APS-001 WHOLESALE WEEKLY_SERVICE_RISK ESCALATE 93.5  33.2   2      0.00│ │
│ │  P1  CTS-001 RETAIL    WEEKLY_SERVICE_RISK ESCALATE 95.6  65.4   2      0.00│ │
│ │  P1  IMH-001 WHOLESALE WEEKLY_SERVICE_RISK ESCALATE 96.1  74.1   2      0.00│ │
│ │  P2  APS-001 ECOM      LOW_COVERAGE_RISK   PROTECT 100.0 100.0   0      1.25│ │
│ │  … 5 more P2 …                                                             │ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
├───────────────────────────────────────┬──────────────────────────────────────┤
│ SELECTED: APS-001 / WHOLESALE   [P1]   │ C4.1  Selected-series trajectory      │
│  Risk:  WEEKLY_SERVICE_RISK            │   fill%    ─── 92% target ───         │
│  Action:ESCALATE                       │   100 ██ ██ ██ ██ ██ ██ ██ ▂33 ██ ██  │
│  13W Base fill:      93.5%             │        base fill by week (bars)       │
│  Min weekly fill:    33.2%             │   + committed receipts overlay        │
│  Worst week:         2026-08-24        │                                       │
│  Service-gap units:  62.5             │                                       │
│  Weeks below target: 2                │                                       │
│  Ending WOS:         0.00             │                                       │
│  Chase capacity:     … units          │                                       │
│  ▸ Governed reason: "Base 13-week…    │                                       │
│    escalate for S&OE review…"         │                                       │
└───────────────────────────────────────┴──────────────────────────────────────┘
```

**Interactive table** — `st.dataframe(selection_mode="single-row", on_select="rerun")`.
Columns (SERIES): `priority_tier, sku_id, channel_id, risk_type, planner_action, base_13w_fill_rate, min_weekly_base_fill_rate, worst_base_service_week, worst_week_service_gap_units, weeks_below_service_target, base_final_wos, chase_capacity_units`. Sort: `priority_tier` asc, then `weeks_below_service_target` desc, then `min_weekly_base_fill_rate` asc. Conditional style: P1 rows amber tint, P2 slate tint.

**Detail panel (on select)** — `st.container`, two columns:
- Left: metrics from SERIES for the selected series — `base_13w_fill_rate`, `min_weekly_base_fill_rate`, `worst_base_service_week`, `worst_week_service_gap_units`, `weeks_below_service_target`, `base_final_wos`, `ending_safety_stock_units`, `base_safety_gap_units`, `risk_type`, `priority_tier`, `planner_action`, `chase_capacity_units`, `contingency_chase_option_units`. **Governed `action_reason` shown verbatim** (frozen text).
- Right: **C4.1 selected-series trajectory** — 1. "Selected Series — Weekly Base Fill & Receipts" · 2. When does this series fail and is receipt timing the cause? · 3. Bars (weekly `base_fill_rate`) + overlay bars/line (`committed_receipt_units`) · 4. `forecast_week_start` · 5. fill % (primary), units (secondary) · 6. fill bars amber when `<92%` · 7. **92% target reference line** · 8. WEEKLY filtered to selected series · 9. `forecast_week_start, base_fill_rate, committed_receipt_units, base_forecast_units, base_shipped_units` · 10. hover shows fill, demand, shipped, gap.

**Hard governance guard:** the panel **must not invent** actions. `WEEKLY_SERVICE_RISK → P1 → ESCALATE` is shown as-is; it is **never** upgraded to CHASE. Display only frozen `planner_action` + `action_reason`. `recommended_chase_release_units` (=0) and `contingency_chase_option_units` are shown as *options*, explicitly labeled "not released — execution lead time not modeled".

**Page-4 acceptance:** table sorts P1 first; selecting a row updates the panel and C4.1; `action_reason` is the frozen string; no CHASE recommendation appears for any WEEKLY_SERVICE_RISK series; empty selection falls back to default P1 row.

---

### PAGE 5 — FORECAST & GOVERNANCE

**Business question:** *Why should the user trust this planning output?* Uses frozen 4A/4B/4C evidence (see §20). No filters. Organized with `st.tabs`.

#### Wireframe
```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Forecast & Governance                                                          │
│ [ Reconstruction | Forecast | Weather | Planning Policy | Provenance | Limits ]│
├──────────────────────────────────────────────────────────────────────────────┤
│ Tab: Forecast                                                                  │
│  9 champion models · 12 folds · 13-wk horizon · 52-wk season · 8 ETS/1 base/0 SARIMA│
│  ┌ sku chan champion        wape%  bias%  override ┐   C5.1 WAPE by series (bar)│
│  │ APS ECOM HW_Damped_Mul   10.55  -3.09   NO     │    APS WHOLE ████ 18.3     │
│  │ …                                              │    ── target readability ──│
│  └────────────────────────────────────────────────┘                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Tab A — Demand Reconstruction** (`st.metric` row + short prose)
Source: `03_model_evidence/step4a_reconstruction/DemandIQ_Step4A_Method_Comparison.csv`, row `method = Seasonal_Profile_Imputation`.
- Selected method: Seasonal Profile Imputation.
- Censored-row WAPE 26.08% (`segment = ALL_CENSORED_ROWS`, `WAPE`), Bias −2.61% (`Bias`), Recovery 95.68% (`lost_demand_recovery_pct`), full-stockout recovery 98.43% (`segment = STOCKOUT_ROWS` recovery). Values from the file, not hardcoded.

**Tab B — Forecast Governance**
Source: `05_outputs/champion_selection/DemandIQ_Step4B_Champion_Selection.csv` (9 rows).
- Table: `sku_id, channel_id, selected_champion, selected_family, champion_wape_pct, champion_bias_pct, governance_override_flag, selection_reason, evaluation_folds (12), forecast_horizon_weeks (13)`.
- Summary chips: 8 ETS / 1 Baseline / 0 SARIMA; 52-week seasonal period; expanding window.
- Note the documented IMH-001/ECOM simplicity override (SARIMA beat ETS by ~0.06pp; ETS retained) surfaced from `selection_reason` / `governance_override_flag`.
- **C5.1 — Champion WAPE by series**: 1. "Backtest WAPE by Champion (9 series)" · 2. How accurate is each series model? · 3. Horizontal bar · 4. WAPE % · 5. `sku_id / channel_id` · 6. hue by `selected_family` · 7. none (WAPE is descriptive, no pass/fail line) · 8. Champion_Selection · 9. `sku_id, channel_id, champion_wape_pct, selected_family` · 10. hover shows bias, runner-up. **Do not recompute selection.**

**Tab C — Weather Governance** (prose + small table)
Source: `05_outputs/weather_forward/DemandIQ_Step4C_Forward_Weather_Framework.csv`.
- Weeks 1–3 `NOWCAST_REQUIRED` (`weather_horizon_mode`, `nowcast_available_flag`, `nowcast_governance`); Weeks 4–13 MILD/NORMAL/SEVERE analog scenarios (`scenario_method`, `scenario_provenance`).
- State explicitly: `future_realized_weather_used_flag = 0` (no future-weather leakage); scenario caps (`sku_mild_policy_cap_pct`, `sku_severe_policy_cap_pct`) are **planning assumptions, not empirical elasticities**.

**Tab D — Planning Governance** (`st.metric` + callouts)
- Service target 92% · Safety stock 2.5 weeks · Chase capacity 8% · Excess threshold 8 WOS (from EXEC `service_target_fill_rate` and documented constants).
- Weekly exception rule callout: **WEEKLY_SERVICE_RISK if 13-week Base fill ≥ 92% AND ≥ 2 forecast weeks have weekly Base fill < 92%** (misses need not be consecutive). Labeled a **SYNTHETIC PLANNING-GOVERNANCE ASSUMPTION**.

**Tab E — Provenance**
- PUBLIC (historical weather observations), SYNTHETIC (simulated demand truth, inventory constraints, policies, scenario caps, 2-week rule), DERIVED (reconstruction, forecasts, WAPE/bias, inventory sim, fill, WOS, risk type, planner action, exposure proxies).
- Explicit banner: **portfolio simulation inspired by a premium outdoor apparel operating model — NOT any real company's internal data.**

**Tab F — Limitations**
- No supplier lead-time execution model; no transfer-transit-time model; no automatic chase for WEEKLY_SERVICE_RISK; economic values are **planning exposure proxies, not accounting profit** (COGS unavailable); simulation, not real company performance.

**Page-5 acceptance:** every number traces to a frozen evidence file; champion mix reads 8/1/0; weather leakage flag shown as 0; the 2-week rule labeled synthetic; provenance + limitations present; no claim of real company performance.

---

## 16. Streamlit component recommendations

| Need | Component |
|---|---|
| KPI cards | `st.metric` inside `st.columns` (with `border=True` container) |
| Status banner | `st.container(border=True)` + custom CSS accent, or `st.warning`-style block |
| Tables (queue, evidence) | `st.dataframe` with `column_config`, `selection_mode="single-row"` on Page 4 |
| Page 5 sections | `st.tabs` |
| Grouping/detail panels | `st.container`, `st.columns` |
| Optional detail hiding | `st.expander` (governed `action_reason`, methodology detail) |
| Scenario switch | `st.segmented_control` (Mild/Base/Severe) on Page 2 |
| Interactive charts | **Plotly** — Plotly Express for bars/heatmap; Plotly Graph Objects for band + reference lines + combo charts |
| Caching | `@st.cache_data` on the three CSV loaders |
| Nav | `st.navigation` + `st.Page` |

Avoid: pie/donut/gauge charts, 15+ KPI cards, model metrics on Page 1, decorative charts, exposing the 157-column Step 5 file.

---

## 17. Proposed Step 6C file structure

Repo uses numbered top-level folders (`01_…`–`06_docs`). A multipage app is more than a single script, so keep it self-contained at root as **`07_streamlit_app/`** (rationale: clean separation from analytical scripts, standard Streamlit deploy root, doesn't pollute `04_scripts`). Alternative if you prefer scripts-nesting: `04_scripts/step6/streamlit_app/`.

```
07_streamlit_app/
    app.py                     # entry point: st.navigation, global sidebar filters, shared cached load
    pages/
        1_command_center.py
        2_demand_outlook.py
        3_service_inventory_risk.py
        4_decision_queue.py
        5_forecast_governance.py
    components/
        kpi_cards.py           # render_metric_row(), status_banner()
        tables.py              # decision_queue_table(), evidence_table()
        detail_panel.py        # selected-series panel (Page 4)
    charts/
        demand_charts.py       # C1.1, C2.1, C2.2, C2.3
        risk_charts.py         # C3.1 heatmap, C3.2 receipts, C3.3 WOS, C4.1 trajectory
        governance_charts.py   # C5.1
    utils/
        data_loader.py         # cached loaders for EXEC/SERIES/WEEKLY + evidence files; path constants
        formatting.py          # units/%/CAD formatters, week formatting
        theme.py               # color tokens (risk semantics), Plotly template
    assets/
        style.css              # premium/minimal theme overrides
    .streamlit/
        config.toml            # theme (base colors, font)
    README_app.md              # run instructions (Step 6C)
```

Entry point: `app.py`. Data loader: `utils/data_loader.py` (single source of truth for paths + `@st.cache_data`). Formatting: `utils/formatting.py`. Reusable KPI/cards: `components/kpi_cards.py`. Chart utilities justified because charts are reused across pages (trajectory logic on Pages 3 & 4). **Do not create these files in Step 6B.**

---

## 18. Page-specific acceptance criteria
Consolidated from §7–15 (one block per page above). Each page's "acceptance" line is the contract for Step 6C.

## 19. Overall Streamlit acceptance criteria
- App launches from `07_streamlit_app/app.py`; 5 pages in decision order via `st.navigation`.
- All Page 1–4 numbers reconcile to Step 6A (Base demand 36,434.66; Base fill 98.77%; P1=3; P2=6; immediate chase/realloc = 0).
- Heatmap threshold at 0.92; three P1 series highlighted; worst cells at 2026-08-24.
- No Region dimension anywhere; grain = SKU × Channel.
- No invented recommendations; `action_reason` shown verbatim; no CHASE for WEEKLY_SERVICE_RISK.
- All economic figures labeled "planning exposure proxy (not accounting profit)".
- Provenance banner states simulation, not any real company's data.
- Risk color semantics consistent (P1 amber, P2 slate, neutral not alarming); not every KPI red.
- Data loaded once, cached; no per-page reload; no write-back to any CSV.

## 20. Additional frozen evidence required for Page 5
| Section | Frozen file | Key columns |
|---|---|---|
| Reconstruction | `03_model_evidence/step4a_reconstruction/DemandIQ_Step4A_Method_Comparison.csv` | `method, segment, WAPE, Bias, lost_demand_recovery_pct` |
| Forecast champions | `05_outputs/champion_selection/DemandIQ_Step4B_Champion_Selection.csv` | `sku_id, channel_id, selected_champion, selected_family, champion_wape_pct, champion_bias_pct, governance_override_flag, selection_reason, evaluation_folds, forecast_horizon_weeks` |
| Weather governance | `05_outputs/weather_forward/DemandIQ_Step4C_Forward_Weather_Framework.csv` | `weather_horizon_mode, nowcast_available_flag, future_realized_weather_used_flag, sku_mild_policy_cap_pct, sku_severe_policy_cap_pct, scenario_method, scenario_provenance, nowcast_governance` |
| Planning policy | EXEC (`service_target_fill_rate`) + documented constants (2.5wk / 8% / 8 WOS) | — |

(Optional richer evidence, not required: Step 4B fold-metric files under `03_model_evidence/step4b_forecasting/` for a fold-stability view — only if a later iteration wants it.)

## 21. Data limitations / gaps identified
- **`ending_safety_stock_units` / WOS**: Step 6A carries `ending_safety_stock_units` and `base_final_wos` per series — sufficient for C3.3. No gap.
- **Champion model not in Step 6A files**: Page 5 must read Step 4B/4D evidence directly (by design; Step 6A intentionally excludes model diagnostics from the operational layer). No gap — evidence files exist.
- **Region**: present in Step 3 data but **excluded by governance** from forecasting; dashboard must not add it as a forecasting filter. (Region could appear only as non-forecast context on a future weather/allocation page — out of scope for 6B.)
- **Filtered fill-rate risk**: re-aggregating weekly fill over a filtered subset is a valid derived aggregation but could be misread as the governed 98.77%. Mitigation: Page 1 is unfiltered; filtered pages label such values "filtered view".
- **Causality**: the 2026-08-24 shared zero-receipt insight is a structural interpretation, not proven cause; captions must not overstate.
- **No execution feasibility data** (lead times, transit) — the reason WEEKLY_SERVICE_RISK stays ESCALATE, never auto-CHASE. This is a designed limitation, surfaced on Page 5.

---

## Step 6B validation checklist
- [x] Pages 1–4 buildable **entirely** from frozen Step 6A EXEC/SERIES/WEEKLY outputs.
- [x] **No new analytics** required for Pages 1–4 (only read / aggregate / reshape frozen values).
- [x] Page 5 requires **only** existing frozen Step 4A/4B/4C evidence files (all confirmed present).
- [x] **No region-level forecasting** introduced anywhere.
- [x] **P1/P2 logic unchanged** — risk_type, priority_tier, planner_action displayed verbatim from Step 6A.
- [x] **No automatic chase invented** — WEEKLY_SERVICE_RISK shown as ESCALATE; chase/realloc shown as options, not released (both immediate values = 0).
- [x] All economic values labeled **planning exposure proxies, not accounting profit**.
- [x] **No synthetic data represented as any real company's data** — provenance banner + Page 5 provenance/limitations.

---
*Step 6B deliverable. Design only — Streamlit implementation is Step 6C, pending approval. Frozen Steps 4A–5 and Step 6A untouched.*
