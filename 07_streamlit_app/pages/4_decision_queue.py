"""Page 4 — Planner Decision Queue. Shared SKU/Channel filters.

Full-width interactive 9-series table -> selected-series detail. Shows frozen
planner_action + action_reason verbatim; never invents a recommendation.
"""
from __future__ import annotations
import streamlit as st

from utils.data_loader import get_step6a, apply_series_filter
from utils import filters
from components import cards, tables, detail_panel


def render():
    _, series_df, weekly_df = get_step6a()
    skus, chans = filters.get_selected()

    cards.page_header(
        "Planning", "Planner Decision Queue",
        "What should the planner investigate first?",
        "Series are ranked P1 → P2. Select any row to open its governed decision detail, "
        "including the frozen action reason and the execution boundary.",
    )

    series_f = apply_series_filter(series_df, skus, chans)
    if series_f.empty:
        st.warning("No series match the current filters. Use **Reset filters** in the sidebar.")
        st.stop()

    active = filters.filtered_caption()
    st.markdown(
        f'<span class="diq-chip p2">{"Filtered · " + active[15:] if active else "All 9 series"}'
        '</span> &nbsp; <span style="color:#5B6B73;">Select a row to open its decision detail.</span>',
        unsafe_allow_html=True)
    st.write("")

    selected = tables.decision_queue_table(series_f)

    st.markdown('<hr class="diq-rule"/>', unsafe_allow_html=True)
    if selected is not None:
        detail_panel.render_detail_panel(selected, weekly_df)
    else:
        st.info("Select a series in the table above to see its decision detail.")
