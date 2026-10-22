# DemandIQ — Streamlit Decision Product (Step 6C)

An interactive IBP / S&OE decision product over the **frozen** DemandIQ planning
engine. It turns the 13-week demand outlook, inventory/supply simulation, and
governed risk classifications into a five-page planner experience.

> **Simulation disclaimer.** DemandIQ is a portfolio simulation inspired by a
> premium outdoor apparel operating model. It does **not** represent any real
> company's internal data. Economic values are **planning exposure proxies, not
> accounting profit**.

## Purpose

Move a planner / IBP leader / reviewer through:
`Portfolio → Demand Outlook → Service / Inventory Risk → SKU × Channel Decision → Governance`,
around one governed story. Supply is the **projected** seasonal drops plus an
**estimate** of replenishment receipts (last year's replenishment shifted 52
weeks, plus SKU growth; 6,512 units). The estimate is **not confirmed open
orders**. If it arrives as modelled, 13-week service holds in every week, most
series finish with thin safety-stock coverage, and the plan is
**0 ESCALATE, 7 PROTECT, 2 HOLD**, with **no automatic chase release**. With
zero replenishment the plan is the published list, **3 ESCALATE, 6 PROTECT**
(kept in `05_outputs/v1_published_plan/`); the Portfolio banner shows both.
The seasonal drops are projected the same way, from last year's seasonal
receipts shifted 52 weeks; they sit in `committed_receipt_units`, a v1 column
name kept for compatibility, and are not confirmed supplier orders
(`seasonal_receipt_projection_status = PROJECTED_NOT_CONFIRMED`). A
planner must confirm open-order quantities and receipt dates before the
conditional calls replace the published escalation list. The pages word their
headlines from the data, so they also render the v1 plan on its own.

## Structure

```
07_streamlit_app/
  app.py                     # entry: st.navigation, PAGES registry, sidebar filters, CSS
  pages/                     # one render() per page (loaded as callables)
    1_command_center.py      # Executive (full portfolio, no filters)
    2_demand_outlook.py      # filtered
    3_service_inventory_risk.py  # filtered (flagship)
    4_decision_queue.py      # filtered, interactive select -> detail
    5_forecast_governance.py # evidence tabs (no filters)
  components/                # kpi_cards, tables, detail_panel (UI rendering)
  charts/                    # demand_charts, risk_charts, governance_charts (pure Plotly builders)
  utils/                     # data_loader, filters, formatting, validation, theme
  assets/style.css           # premium/minimal theme
  .streamlit/config.toml     # theme + headless
  requirements.txt
```

## Data sources (read-only)

Pages 1–4 read **only** the frozen Step 6A semantic layer:
- `05_outputs/decision_layer/DemandIQ_Step6A_Executive_KPI_Summary.csv` (1 row)
- `05_outputs/decision_layer/DemandIQ_Step6A_Series_Decision_Summary.csv` (9 rows)
- `05_outputs/decision_layer/DemandIQ_Step6A_Weekly_Planning_Trajectory.csv` (117 rows)

Page 5 reads frozen evidence: Step 4A method comparison, Step 4B champion
selection, Step 4C forward weather framework.

The loader (`utils/data_loader.py`) resolves the project root relative to this
folder, validates shapes/columns, guards against forbidden hidden-truth fields,
and caches with `@st.cache_data`. Missing/malformed files raise a clear error
and stop the page — the app never rebuilds an upstream step.

## Launch (local, PowerShell)

```powershell
cd D:\Downloads\DemandIQ\07_streamlit_app
C:\Users\abhij\AppData\Local\Programs\Python\Python311\python.exe -m streamlit run app.py
```

Then open http://localhost:8501.

## Governance notes

- No hidden analytical logic in the UI layer — it displays frozen values.
- Filtering (Pages 2–4) only **subsets** frozen rows; it never recomputes
  `risk_type`, `priority_tier`, or `planner_action`. Page 1 is always
  full-portfolio so its KPIs equal the governed Step 6A numbers exactly.
- WEEKLY_SERVICE_RISK is shown as **ESCALATE**; it is never auto-converted to
  CHASE (execution lead-time feasibility is outside modeled scope).

## Future extension (not built)

A separate **New Product Launch Planning** workflow (analog / cold-start) can be
added by appending one entry to the `PAGES` list in `app.py` (see the `FUTURE`
marker). Mature-product time-series forecasting and new-product launch
forecasting remain analytically separate.
```
