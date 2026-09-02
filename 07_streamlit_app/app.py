"""DemandIQ — Streamlit decision product (Step 6C).

Entry point. Builds programmatic navigation (st.navigation / st.Page), loads the
shared cached data layer via the page modules, and renders shared sidebar filters
for Pages 2-4 only. Pages 1 and 5 stay full-portfolio.

Governance: this UI layer READS the frozen Step 6A semantic layer and frozen Step
4A/4B/4C evidence. It contains no forecasting, inventory, or risk logic and writes
no files.

Extensibility: to add "06 — New Product Launch Planning" later, append one entry to
PAGES (see the FUTURE marker) — no restructuring of Pages 1-5. Mature-product
forecasting and new-product cold-start forecasting stay analytically separate.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import streamlit as st

from utils import filters

APP_DIR = Path(__file__).resolve().parent
PAGES_DIR = APP_DIR / "pages"
ASSETS = APP_DIR / "assets"

# ------------------------------------------------------------------
# Page registry — single source of truth for navigation.
# `filters=True` => shared SKU/Channel sidebar filters apply.
# ------------------------------------------------------------------
PAGES = [
    # Default page: no url_path so it serves at "/" (avoids a "page not found"
    # toast when its own url_path is hit directly).
    {"module": "1_command_center.py", "title": "01 · Executive Command Center",
     "icon": "🧭", "group": "Planning", "url": None,
     "filters": False, "default": True},
    {"module": "2_demand_outlook.py", "title": "02 · Demand Outlook",
     "icon": "📈", "group": "Planning", "url": "demand-outlook", "filters": True},
    {"module": "3_service_inventory_risk.py", "title": "03 · Service & Inventory Risk",
     "icon": "🌡️", "group": "Planning", "url": "service-inventory-risk", "filters": True},
    {"module": "4_decision_queue.py", "title": "04 · Planner Decision Queue",
     "icon": "✅", "group": "Planning", "url": "decision-queue", "filters": True},
    {"module": "5_forecast_governance.py", "title": "05 · Forecast & Governance",
     "icon": "📚", "group": "Evidence", "url": "forecast-governance", "filters": False},
    # New-product launch planning (Step 7G). HIS-only page with its own in-page
    # Channel control, so it does not use the shared SKU/Channel sidebar filters.
    {"module": "6_launch_planning.py", "title": "06 · New Product Launch Planning",
     "icon": "🚀", "group": "Launch Planning", "url": "launch-planning", "filters": False},
]


def _load_render(module_file: str):
    """Import a digit-prefixed page module by path and return its render fn."""
    path = PAGES_DIR / module_file
    spec = importlib.util.spec_from_file_location(f"page_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.render


def _load_css():
    css = ASSETS / "style.css"
    if css.exists():
        st.markdown(f"<style>{css.read_text(encoding='utf-8')}</style>",
                    unsafe_allow_html=True)


def _sidebar_top():
    logo = ASSETS / "logo.svg"
    if logo.exists():
        try:
            st.logo(str(logo), size="large")
        except Exception:
            pass
    st.sidebar.markdown(
        '<div class="diq-brand-sub">Demand Planning &amp; S&amp;OE Control Tower</div>'
        '<div class="diq-workflow">Forecast → Supply → Risk → Action</div>',
        unsafe_allow_html=True,
    )


def _sidebar_footer():
    st.sidebar.divider()
    st.sidebar.markdown(
        '<div class="diq-footer">Provenance: PUBLIC + SYNTHETIC → DERIVED.<br>'
        'Portfolio simulation — not any real company\'s data.<br>'
        'Economics are planning exposure proxies, not accounting profit.</div>',
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(page_title="DemandIQ — IBP Decision Product",
                       page_icon="🧭", layout="wide",
                       initial_sidebar_state="expanded")
    _load_css()
    filters.init_filter_state()

    grouped: dict[str, list] = {}
    wants_filters: dict[str, bool] = {}
    for p in PAGES:
        page = st.Page(_load_render(p["module"]), title=p["title"], icon=p["icon"],
                       url_path=p["url"], default=p.get("default", False))
        grouped.setdefault(p["group"], []).append(page)
        wants_filters[p["title"]] = p["filters"]

    _sidebar_top()
    pg = st.navigation(grouped)

    if wants_filters.get(pg.title, False):
        filters.render_sidebar_filters()
    _sidebar_footer()

    pg.run()


if __name__ == "__main__":
    main()
