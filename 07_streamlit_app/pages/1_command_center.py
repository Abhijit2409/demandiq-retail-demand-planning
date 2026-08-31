"""Page 1 — Executive Command Center. Always full portfolio (no filters).

KPI values read the frozen Executive row VERBATIM (exact reconciliation).
"""
from __future__ import annotations
import streamlit as st

from utils.data_loader import get_step6a
from utils import formatting as fmt
from utils.theme import PLOTLY_CONFIG
from components import cards
from charts import demand_charts


def render():
    exec_df, series_df, weekly_df = get_step6a()
    e = exec_df.iloc[0]

    horizon = (f"{weekly_df['forecast_week_start'].min():%b %d} → "
               f"{weekly_df['forecast_week_start'].max():%b %d, %Y}")

    # ---- Hero ----
    st.markdown(
        '<div class="diq-hero-title">DemandIQ</div>'
        '<div class="diq-hero-sub">13-Week Demand Planning &amp; S&amp;OE Control Tower</div>'
        '<div class="diq-hero-desc">Forecast mature-product demand, test supply and '
        'inventory coverage, detect service risk, and prioritize planner action across '
        'SKU × Channel.</div>'
        f'<div class="diq-hero-horizon">Planning horizon &nbsp;<b>{horizon}</b></div>'
        '<hr class="diq-rule"/>',
        unsafe_allow_html=True,
    )

    # ---- Status story ----
    cards.status_banner(e)
    st.write("")

    # ---- Six KPI cards (custom grid: 3 x 2, no truncation) ----
    base_fill = e["base_13w_fill_rate"]
    target = e["service_target_fill_rate"]
    p1 = int(e["p1_weekly_service_risk_series"])
    p2 = int(e["p2_low_coverage_risk_series"])
    total = int(e.get("total_series", 9))
    cards.kpi_grid([
        {"label": "13-Week Base Demand", "value": fmt.units(e["base_13w_demand_units"]),
         "sub": "Mature-product portfolio"},
        {"label": "Base Fill Rate", "value": fmt.pct(base_fill),
         "sub": f"{fmt.pct_points(base_fill - target)} vs target", "sub_kind": "up",
         "accent": "ok"},
        {"label": "Service Target", "value": fmt.pct(target),
         "sub": "Governed policy (92%)"},
        {"label": "P1 Weekly Exceptions", "value": f"{p1} of {total} series",
         "sub": "Require ESCALATE", "sub_kind": "warn", "accent": "p1"},
        {"label": "Safety-Stock Gap",
         "value": fmt.units(e["base_safety_stock_protection_gap_units"]),
         "sub": "Buffer shortfall vs 2.5-week policy", "accent": "p2"},
        {"label": "Immediate Chase Release",
         "value": fmt.units(e["immediate_chase_release_units"]),
         "sub": "Held — execution feasibility not modeled"},
    ])
    st.write("")

    # ---- Primary chart + urgent actions ----
    big, side = st.columns([1.7, 1], gap="large")
    with big:
        cards.section("Portfolio 13-Week Demand Outlook",
                      "Base forecast with Mild–Severe scenario band")
        st.plotly_chart(demand_charts.portfolio_demand_trend(weekly_df),
                        width='stretch', config=PLOTLY_CONFIG)
    with side:
        cards.section("Urgent Planner Actions", "P1 series requiring escalation")
        cards.p1_decision_cards(series_df)
        st.markdown(
            f'<div class="diq-note">+ {p2} series require <b>PROTECT</b> because ending '
            'coverage remains below the 2.5-week policy.</div>'
            '<a href="/decision-queue" target="_self" '
            'style="font-weight:650;color:#3F6C8E;text-decoration:none;">'
            'Review full decision queue →</a>',
            unsafe_allow_html=True,
        )
