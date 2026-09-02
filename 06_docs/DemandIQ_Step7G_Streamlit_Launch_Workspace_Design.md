# DemandIQ — Step 7G · Streamlit Launch Workspace (Page 6) — Architecture

**Scope:** Streamlit-only. Adds one page — **06 · New Product Launch Planning** — to the
existing DemandIQ app, telling the HIS-001 cold-start planner story from **frozen Step
7B–7F outputs only**. No new analytics; Pages 1–5 unchanged. This is architecture
documentation, **not** a case study.

**Status:** Implemented + QA-passed. Awaiting owner visual review before freeze.

---

## 1. Files

| Action | File |
|---|---|
| **MODIFY** | `07_streamlit_app/app.py` — one entry added to `PAGES` (the pre-existing FUTURE marker) |
| **CREATE** | `07_streamlit_app/pages/6_launch_planning.py` — `render()` |
| **CREATE** | `07_streamlit_app/charts/launch_charts.py` — Plotly builders |
| **CREATE** | `07_streamlit_app/utils/launch_data.py` — cached Step 7B–7F loaders + latent quarantine |
| **CREATE** | `06_docs/DemandIQ_Step7G_Streamlit_Launch_Workspace_Design.md` — this doc |
| **UNCHANGED** | Pages 1–5, existing charts/components, `theme.py`, `formatting.py`, `filters.py`, `data_loader.py` (import-only), `style.css`, `config.toml`, README, case study, presentation |

## 2. Integration

- **Navigation:** registered in the `app.py` `PAGES` list (`st.navigation`/`st.Page`), group **"Launch Planning"**, `filters=False` (HIS-only page uses its own in-page Channel control, not the shared SKU/Channel sidebar filters).
- **Data layer:** `utils/launch_data.py` reuses the frozen primitives `_read`, `DataLoadError`, `PROJECT_ROOT`, `_cache` from `data_loader.py` (no edit to it). One `st.cache_data` loader per frozen file; paths resolved from `PROJECT_ROOT` (deployment-safe, no drive letters). Missing/malformed → `st.stop()` with a clear message.
- **Visual system:** reuses `page_header / section / kpi_grid / callout / info_cards`, `theme.apply_theme` + `PLOTLY_CONFIG`, `width="stretch"`. Light theme only. Widget keys namespaced `p6_*`.

## 3. Page-6 sections & data sources

| Section | Content | Frozen source |
|---|---|---|
| 1 · Launch Command Center | 8 KPI cards | 7B assumptions, 7E buy, derived fill/mix, 7F handoff & cycle02 |
| 2 · Cold Start → Consensus | Analog scorecard · V0 18-mo baseline · V0→V1→V2→V3 | 7B Scorecard/Assumptions, 7C 18M, 7D Versions |
| 3 · Initial Buy & Allocation | Buy bridge · allocation+reserve · supply context | 7E Buy_Plan, 7F Policy (transfer lead), `STEP7E_SUPPLY_CONTEXT` (text) |
| 4 · Launch Execution & Reforecast | Plan vs observed (+latent toggle) · reforecast waterfall · checkpoint table | 7E Weekly/Checkpoint/Planner_Decisions |
| 5 · Channel / Inventory Learning | ECOM mix learning · counterfactual policy sensitivity | 7E Weekly/Planner_Decisions, 7F Policy |
| 6 · FVA + Rolling + Lifecycle | FVA WAPE + caveat · checkpoint FVA · Cycle 01→02 · lifecycle handoff | 7F FVA/Cycle02/Handoff |

## 4. Channel filter contract

In-page `st.segmented_control` (radio fallback), values **ALL / ECOM / RETAIL / WHOLESALE**, key `p6_channel`.
- **Responds:** V0 baseline, version evolution, allocation (highlight), plan-vs-observed, rolling overlap.
- **SKU-level / global (not filtered):** analog scorecard, buy bridge, reforecast waterfall + checkpoint table, all of Section 5, FVA + checkpoint FVA, lifecycle. Marked with a "SKU-level governance evidence — not changed by the Channel filter" note so the filter never distorts governance evidence.

## 5. Governance controls

- **Hidden latent demand** (`latent_demand_units_HIDDEN_EVAL_ONLY`) is **quarantined**: `load_launch_actuals()` drops it; the only accessor is `load_launch_latent_eval_only()`, used solely behind the **default-OFF** toggle "Show evaluation-only latent synthetic demand", which shows a visible eval-only warning. No operational KPI reads latent.
  - *Note:* the realized **ECOM mix KPI is 49.2% (observed/operational)**, not the 50.4% figure from the 7E narrative — 50.4% is latent-derived, so the governed operational KPI uses observed sales.
- **FVA caveat** rendered visibly next to the FVA chart (not tooltip): *"illustrative governance demonstration … not independent empirical evidence that commercial input was harmful."*
- **Policy sensitivity** shown under an explicit **COUNTERFACTUAL POLICY SENSITIVITY** heading; no threshold labelled optimal/best/recommended; historical 8pp rule frozen.
- **Supply context:** `STEP7E_SUPPLY_CONTEXT` (~8-wk lead, ≤15% chase) is **display metadata only**, labelled **SYNTHETIC SUPPLY PLANNING ASSUMPTIONS**, sourced from the frozen Step 7E decision record (not a CSV), never used in a calculation. CSV-backed supply values (buffer 9%, reserve ~991, reserve/transfer ~2 wks) shown separately as data-derived.
- **Lifecycle:** HIS-001 = EARLY_LAUNCH, 13 weeks, 52-wk & 104-wk milestones distinguished, mature-model eligible = NO. No ETS/SARIMA anywhere on the page.
- V3 stated as **unconstrained demand**; launch buffer stated as **not** mature safety stock.

## 6. QA results (all passed)

- **Data:** all 16 Step 7B–7F files load; buy 8,259 = alloc+reserve; V3 13-wk 7,577; reserve 991; observed fill 97.7%; ECOM lost 158.8; like-for-like −3.05% over 17 months; Cycle02 = 18 forward months Oct26–Mar28; lifecycle EARLY_LAUNCH; mature = NO.
- **UI:** all 6 pages render without exception (AppTest); full `app.py` builds and default page renders.
- **Filter:** ALL/ECOM/RETAIL/WHOLESALE all render; return-to-ALL restores SKU totals.
- **Governance:** latent OFF by default (warning only when toggled on); FVA caveat + COUNTERFACTUAL labels visibly rendered; no frozen Step 7B–7F file modified; no README/case-study/presentation modified.

## 7. Launch command

```powershell
cd "D:\Downloads\DemandIQ\07_streamlit_app"
streamlit run app.py
```

## 8. Final channel-filter fix + freeze

A follow-up review found that the Channel selector updated the charts but not the
Command Center KPIs or the Section-5 learning block (those read global/SKU-level
sources and never used the selected channel; Section 5 was hard-wired to ECOM). This
was corrected: a single central `filter_channel()` plus channel-scoped helpers now
drive V3 demand, allocated buy, launch fill, Cycle-02 direction, observed/lost, the
cold-start and version charts, weekly plan-vs-observed, allocation, rolling forecast,
and channel learning. Every genuinely global block carries a `SKU-LEVEL · NOT
CHANNEL-FILTERED` marker; channel-responsive blocks carry a `CHANNEL VIEW · X` marker.
Verified with numeric reconciliation, Plotly figure-data filter tests, and AppTest
interaction tests (values change per channel; global evidence stays constant; Pages
1-5 unaffected). Owner visually approved ALL / ECOM / RETAIL / WHOLESALE behaviour.

**STEP 7G - COMPLETE / FROZEN.** Frozen files: `pages/6_launch_planning.py`,
`charts/launch_charts.py`, `utils/launch_data.py`, and the Page-6 registration in
`app.py`. Do not modify further unless a genuine computational or rendering defect is
found. Pages 1-5 are not redesigned.

## 9. Out of scope

Step 7H (case-study PDF) is the active follow-on. README / presentation / CV updates
remain separate future steps.
