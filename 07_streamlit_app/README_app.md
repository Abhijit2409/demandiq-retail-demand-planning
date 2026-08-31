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
around one governed story: aggregate 13-week service is healthy, yet three
SKU-channel series suffer repeated weekly service failures while the portfolio
finishes with thin safety-stock coverage — so the response is split between
**P1 ESCALATE** and **P2 PROTECT**, with **no automatic chase release**.

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
