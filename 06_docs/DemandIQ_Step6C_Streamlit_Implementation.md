# DemandIQ — Step 6C — Streamlit Implementation Notes & QA

**Status:** COMPLETE. Application built, imported, chart-instantiated, validated, and boot-smoke-tested.
**Scope:** Presentation/application layer only. Frozen Steps 4A–6B untouched.

---

## 1. What was built

A 5-page Streamlit decision product under `D:\Downloads\DemandIQ\07_streamlit_app\`, implementing the approved Step 6B architecture with the Step 6C locked decisions.

| Area | Files |
|---|---|
| Entry / nav | `app.py` (st.navigation, `PAGES` registry, conditional sidebar filters, CSS) |
| Pages (render fns) | `pages/1_command_center.py` … `pages/5_forecast_governance.py` |
| Components | `components/kpi_cards.py`, `tables.py`, `detail_panel.py` |
| Charts (pure Plotly builders) | `charts/demand_charts.py`, `risk_charts.py`, `governance_charts.py` |
| Utilities | `utils/data_loader.py`, `filters.py`, `formatting.py`, `validation.py`, `theme.py` |
| Assets / config | `assets/style.css`, `.streamlit/config.toml`, `requirements.txt`, `README_app.md` |

## 2. Key implementation decisions

- **Navigation:** programmatic `st.navigation` + `st.Page` from a `PAGES` list (the Page-6 plug point). Page modules are loaded as **callables** (via `importlib`, keeping the digit-prefixed 6B filenames) — chart builders return figures, so pages can be exercised with no server.
- **Filter persistence (two-key mirror):** canonical `selected_skus` / `selected_channels` keys are never used as widget keys; sidebar widgets use `w_skus` / `w_channels` with an `on_change` sync callback. This survives the Page 1 ↔ Page 2 navigation round-trip (Streamlit GCs a widget's session key when the widget isn't rendered). Empty selection = "All".
- **Page 1 always full portfolio:** KPI cards read the **Executive row verbatim** — guarantees exact reconciliation to Step 6A. Filters render only for Pages 2–4 (by page title).
- **Loader:** root resolved via `Path(__file__).resolve().parents[2]` (no hardcoded drive path), `@st.cache_data`, column + shape validation, forbidden-field leakage guard, and load-or-stop UI wrappers.
- **Governance in UI:** filtering only subsets frozen rows; `risk_type` / `priority_tier` / `planner_action` / `action_reason` are displayed verbatim; WEEKLY_SERVICE_RISK shown as ESCALATE, never auto-CHASE; economics labeled exposure proxies; simulation disclaimer on Page 5 + sidebar.

## 3. QA results

### 3.1 No-server harness (imports + charts + validation) — PASS (15/15)
- Import all utils/components/charts — PASS
- All 5 pages import + expose `render()` — PASS
- Load Step 6A (1 / 9 / 117 rows) — PASS
- Load Page 5 evidence (recon / champion 9 / weather 117) — PASS
- **Reconciliation & governance validation — 21 / 21 PASS** (structure; P1=3; P2=6; exact P1 set = APS-001/WHOLESALE, CTS-001/RETAIL, IMH-001/WHOLESALE; all P1 ESCALATE; all P2 PROTECT; all P1 weekly-exception flag=1 and weeks_below≥2; no P1→CHASE; service target 92%; immediate chase=0; immediate realloc=0; Base demand 36,434.66; exec↔weekly demand tie; exec↔series P1/P2 counts).
- All 8 charts instantiate as `go.Figure` — PASS
- Filter subset works + empty=all + no reclassification — PASS

### 3.2 Streamlit boot smoke test — PASS
- Launched headless on port 8501.
- `/_stcore/health` → `ok` within 1s.
- Root page → HTTP 200.
- Log scan → no Traceback / Error / Exception / ImportError.
- Clean shutdown (port released).

### 3.3 AppTest render-body execution (`streamlit.testing.v1.AppTest`) — PASS (12/12)
This executes the actual `render()` body of every page headlessly (via per-page
runner files that preserve module globals), covering §35 items that the boot
check alone cannot:
- Page 1–5 render bodies — **no exception** (5/5).
- Page 4 — detail panel metrics render with default P1 selected; selectable dataframe present.
- Page 5 — reconstruction metric renders governed **26.1%** censored WAPE.
- **Filter two-key mirror survives a simulated nav round-trip** (widget-key GC): after `w_skus` is dropped and `render_sidebar_filters` re-runs, both the widget and canonical `selected_skus` re-seed to `APS-001` (§35.12).
- Full app boots on default page; **Page 1 has zero sidebar planning filters** (§35.13); Page 1 KPI shows governed **98.8%** Base fill.

**Coverage note:** boot proves process/nav/import; AppTest proves every page's
render logic + the filter round-trip. Together these cover §35.1–15. Live
mouse click-through in a browser is the only thing not automated.

### 3.4 Deprecation migration
Real renders surfaced the `use_container_width` deprecation (removed after
2025-12-31). Migrated all 13 call sites to `width='stretch'` (supported in
1.62). Post-migration AppTest runs are warning-clean.

## 4. Dependencies installed
`streamlit 1.62.0`, `plotly 7.0.0` (via pip). Already present: `pandas 3.0.5`, `numpy 2.4.6`. No frozen analytical package versions altered.

## 5. Deviations from Step 6B
- Added `utils/filters.py` (not in the 6B skeleton) to centralize the two-key filter-state pattern and avoid duplicating filter logic across pages — consistent with 6B intent and the §4 "no duplicated filter-state" instruction.
- Sidebar global filters are rendered centrally in `app.py` (conditional per page) rather than inside each page module — same behavior, less duplication.
- No functional deviation from the page/chart/source-column mappings in 6B.

## 6. Frozen-engine confirmation
Steps 4A–6B were **not** modified. Step 6A CSVs and the Step 5 script/output retain their pre-6C timestamps. Step 6C only created files under `07_streamlit_app/` and this notes file under `06_docs/`.

## 7. Future extensibility
`app.py` builds navigation from the `PAGES` list; a `# FUTURE` entry marks where **"6 — New Product Launch Planning"** plugs in (one list entry, own group, `filters` flag). Launch data would load through its own loader, keeping mature-product time-series forecasting and new-product cold-start forecasting analytically separate. No restructuring of Pages 1–5 required.

---

# Step 6C — UI/UX Overhaul (presentation-layer only)

The first Step 6C build was analytically correct but visually weak. This overhaul fixes readability/layout with **no analytical changes** — all 21 reconciliation checks still pass and frozen Steps 4A–6B were not touched.

## O1. Root causes found and fixed
- **Narrow content / whitespace:** `assets/style.css` had `.block-container { max-width: 1280px }`, which re-centered the app into a narrow column despite `layout="wide"`. → raised to **1520px** with tighter side padding; app now uses the desktop width.
- **KPI truncation (`36.4...`, `7.0K...`, `Immediate...`):** six `st.metric` in `st.columns(6)` — Streamlit's metric label uses `white-space:nowrap; text-overflow:ellipsis`. → replaced with **custom HTML KPI cards** (`components/cards.py::kpi_grid`) in a responsive `grid(auto-fit, minmax(230px,1fr))` → 3×2 on Page 1, labels/values wrap, **zero ellipsis**. Also added a CSS safety-net so any remaining `st.metric` label wraps.
- **Small text:** base font 16px; type scale — page title 2.25rem, hero 2.7rem, section 1.25rem, KPI value 2.1rem, body 1rem, chart title 20px, axis 13–15px.
- **Undersized charts:** `utils/theme.py` default height 360→420, fonts 13→15, title 15→20; per-chart heights raised (heatmap **540**, demand **450**, WOS **420**, trajectory **430**).

## O2. Layout & storytelling
- Every page opens with **eyebrow → title → business question → one-sentence insight** (`cards.page_header`).
- **Page 1:** hero (what DemandIQ is) + horizon chip; structured 4-part ACTION-REQUIRED banner; 6 custom KPI cards; large demand chart; **3 P1 decision cards** + P2 callout + link to Page 4 (replacing the cramped 9-row table).
- **Page 3 (flagship):** risk-snapshot cards; **dominant 540px heatmap**; receipts chart reworked to show **lumpy replenishment** with a single **Aug 24** worst-service-week highlight; WOS chart with value labels + 2.5-week line.
- **Page 4:** full-width readable queue (trimmed to key columns, row height set); selected-series **header card** → wide 8-card KPI grid → **full-width trajectory** → **Why P1 / Execution boundary** callouts.
- **Page 5:** 5-step **methodology journey**; card-based tabs; new **reconstruction method-comparison** chart; weather **horizon timeline**; provenance/limitations as cards.
- Sidebar: SVG wordmark logo (`assets/logo.svg`) via `st.logo`, numbered nav (`01 · …`), workflow descriptor, subtle provenance footer. Streamlit toolbar/footer chrome hidden.

## O3. Data-story correction (presentation only)
The first build's Page 3 card labeled the *first* zero-receipt week (Jul 06). Investigation showed **10 of 13 weeks have zero portfolio receipts** (receipts arrive in only 3 batches: Jun 29 / Jul 27 / Aug 31). The governed anchor is the shared **worst-service week = 2026-08-24** (from the P1 series' frozen `worst_base_service_week`). The card and the receipts-chart highlight now use that week. No frozen value changed — only which frozen value is surfaced.

## O4. Bugs found via screenshot QA and fixed
- **"Page not found" toast** when the default page's own `url_path` is hit → default page now has no `url_path` (serves at `/`).
- **Chart title rendering "undefined"** for suppressed-title charts (`apply_theme` set `title=dict(font=…)` with no `text`) → set `title_text=""` in the no-title branches.
- Duplicate section-header + in-chart title on Pages 1/2/3/4 → in-chart titles suppressed where a section header precedes.

## O5. New/changed files
- New: `components/cards.py`, `assets/logo.svg`.
- Rewritten: `assets/style.css`, `pages/1–5`, `components/detail_panel.py`, `charts/governance_charts.py` (+`reconstruction_method_bar`).
- Updated: `utils/theme.py` (scale + `PLOTLY_CONFIG`), `charts/demand_charts.py`, `charts/risk_charts.py`, `components/tables.py`, `components/kpi_cards.py` (now a shim), `app.py` (logo/nav/routing).
- Brand names: all prior brand-name references removed (style.css, page 5, README) → "any real company's data".

## O6. Redesign QA
- Reconciliation validation **21/21 PASS** (unchanged).
- AppTest render-body **PASS** for all 5 pages + full app boot; Page 1 shows governed **98.8%** and has **no** sidebar filters.
- Boot smoke test **PASS** (health `ok`, HTTP 200, no tracebacks).
- **Visual QA via Playwright + system Edge** (no heavyweight stack): captured all pages at 1440-wide and inspected — **zero KPI truncation**, wide content, readable charts/tables, dominant heatmap, substantial Page 5. Screenshots were temporary and removed after inspection.
- Deprecation-clean (`width='stretch'`). Playwright installed as a dev-only tool for screenshots; **not** added to `requirements.txt`.
