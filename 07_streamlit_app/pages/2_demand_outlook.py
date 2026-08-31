"""Page 2 — Demand Outlook. Uses shared SKU/Channel filters (Pages 2-4)."""
from __future__ import annotations
import streamlit as st

from utils.data_loader import get_step6a, apply_series_filter
from utils import filters, formatting as fmt
from utils.theme import PLOTLY_CONFIG
from components import cards
from charts import demand_charts


def render():
    exec_df, series_df, weekly_df = get_step6a()
    e = exec_df.iloc[0]
    skus, chans = filters.get_selected()

    cards.page_header(
        "Planning", "Demand Outlook",
        "Where and when is demand expected to rise?",
        "Portfolio Base demand totals <b>36.4K units</b> over 13 weeks and peaks in "
        "early September; the Mild–Severe band stays narrow (&lt;1% either side of Base).",
    )

    series_f = apply_series_filter(series_df, skus, chans)
    weekly_f = apply_series_filter(weekly_df, skus, chans)
    if weekly_f.empty:
        st.warning("No series match the current filters. Use **Reset filters** in the sidebar.")
        st.stop()

    active = filters.filtered_caption()
    top = st.columns([3, 1])
    with top[0]:
        st.markdown(
            f'<span class="diq-chip p2">{"Filtered · " + active[15:] if active else "All SKUs · All Channels"}</span>',
            unsafe_allow_html=True)
    with top[1]:
        scenario = st.segmented_control(
            "Scenario emphasis", options=["Mild", "Base", "Severe"], default="Base",
            help="Changes emphasis of the SKU/Channel breakdowns. Does not recompute forecasts.",
        ) or "Base"
    scen = scenario.lower()

    # ---- Top summary cards (frozen/derived presentation values) ----
    peak_week = str(e["peak_base_demand_week"])
    cards.kpi_grid([
        {"label": "13-Week Demand", "value": fmt.units_k(weekly_f["base_forecast_units"].sum()),
         "sub": "Filtered Base total" if active else "Portfolio Base total"},
        {"label": "Peak Week", "value": fmt.date_short(peak_week), "sub": "Highest Base week"},
        {"label": "Peak Weekly Demand", "value": fmt.units_k(e["peak_base_weekly_demand_units"]),
         "sub": "Portfolio Base"},
        {"label": "Severe vs Base", "value": f'+{e["severe_vs_base_pct"]:.2f}%',
         "sub": "Scenario upside", "accent": "p2"},
    ])
    st.write("")

    cards.section("Weekly Demand Forecast — Scenario Range")
    st.plotly_chart(demand_charts.portfolio_demand_trend(weekly_f),
                    width='stretch', config=PLOTLY_CONFIG)
    st.markdown('<div class="diq-note">Base is the primary line; the shaded band spans the '
                'Mild–Severe scenario range. Peak Base week is derived from the data.</div>',
                unsafe_allow_html=True)

    st.write("")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.plotly_chart(demand_charts.demand_by_dimension(series_f, "sku_id", scen),
                        width='stretch', config=PLOTLY_CONFIG)
    with c2:
        st.plotly_chart(demand_charts.demand_by_dimension(series_f, "channel_id", scen),
                        width='stretch', config=PLOTLY_CONFIG)
    st.caption("Governed forecasting grain is SKU × Channel. Region is intentionally not a "
               "forecasting dimension.")
