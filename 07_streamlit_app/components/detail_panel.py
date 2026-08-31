"""Selected-series decision detail (Page 4). UI rendering only.

Header card → wide KPI grid → full-width trajectory → governed reason + the
execution boundary. Shows frozen values verbatim; never invents a recommendation.
"""
from __future__ import annotations
import streamlit as st

from utils import formatting as fmt
from utils.data_loader import apply_series_filter
from utils.theme import PLOTLY_CONFIG
from components import cards
from charts import risk_charts


def render_detail_panel(row, weekly_df):
    sku, chan = row["sku_id"], row["channel_id"]
    label = fmt.series_label(sku, chan)
    is_p1 = row["risk_type"] == "WEEKLY_SERVICE_RISK"

    cards.series_header(row)

    if is_p1:
        st.markdown(
            f'<div class="diq-note">Aggregate 13-week fill remains above target at '
            f'<b>{fmt.pct(row["base_13w_fill_rate"])}</b>, but this series misses weekly '
            f'service <b>{int(row["weeks_below_service_target"])} times</b> and reaches '
            f'<b>{fmt.pct(row["min_weekly_base_fill_rate"])}</b> fill in its worst week '
            f'({fmt.date_long(row["worst_base_service_week"])}).</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="diq-note">Weekly service holds, but ending coverage is '
            f'<b>{fmt.wos(row["base_final_wos"])}</b> — below the 2.5-week safety-stock '
            f'policy, so the series is protected rather than escalated.</div>',
            unsafe_allow_html=True)

    # ---- Wide responsive KPI grid (no narrow stacking) ----
    cards.kpi_grid([
        {"label": "13W Base Fill", "value": fmt.pct(row["base_13w_fill_rate"])},
        {"label": "Worst Weekly Fill", "value": fmt.pct(row["min_weekly_base_fill_rate"]),
         "accent": "p1" if is_p1 else ""},
        {"label": "Worst Week", "value": fmt.date_short(row["worst_base_service_week"])},
        {"label": "Weekly Misses", "value": int(row["weeks_below_service_target"])},
        {"label": "Ending WOS", "value": fmt.wos(row["base_final_wos"])},
        {"label": "Safety-Stock Gap", "value": fmt.units(row.get("base_safety_gap_units"))},
        {"label": "Chase Capacity", "value": fmt.units(row["chase_capacity_units"]),
         "accent": "p2"},
        {"label": "Recommended Chase Release",
         "value": fmt.units(row.get("recommended_chase_release_units", 0)),
         "sub": "Held — not released"},
    ])
    st.write("")

    # ---- Full-width trajectory ----
    cards.section("Weekly Trajectory", "Base fill vs 92% target, with receipt timing")
    one = apply_series_filter(weekly_df, [sku], [chan])
    st.plotly_chart(risk_charts.series_trajectory(one, label, show_title=False),
                    width='stretch', config=PLOTLY_CONFIG)

    st.write("")
    left, right = st.columns(2, gap="large")
    with left:
        cards.callout("why", f"Why this series is {row['priority_tier']}",
                      str(row["action_reason"]))
    with right:
        if is_p1:
            cards.callout(
                "boundary", "Execution boundary",
                "P1 means urgent S&amp;OE review. Automatic chase is <b>not</b> released "
                "because supplier / transfer lead-time feasibility is outside the current "
                "model.")
        else:
            cards.callout(
                "boundary", "Protection stance",
                "Protect ending inventory and retain the contingency chase option. It is "
                "<b>not</b> released simply to restore the safety-stock buffer.")
