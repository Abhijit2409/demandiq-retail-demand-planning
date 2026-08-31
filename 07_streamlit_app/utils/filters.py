"""Shared SKU/Channel filter state for Pages 2-4.

Two-key mirror so selections survive navigation round-trips (Streamlit
garbage-collects a widget's session key when the widget is not rendered,
e.g. on Page 1). Canonical keys are never used as widget keys:

    canonical (persist)     widget (may be GC'd)
    selected_skus       <-  w_skus     (on_change sync)
    selected_channels   <-  w_channels (on_change sync)

Empty selection == "All" (avoids clutter; any non-empty selection over the
9 existing SKU×Channel series always yields rows).
"""
from __future__ import annotations
import streamlit as st

from utils.data_loader import ALL_SKUS, ALL_CHANNELS

SEL_SKUS = "selected_skus"
SEL_CHANS = "selected_channels"
SEL_SERIES = "selected_series"  # reserved for cross-page series selection


def init_filter_state():
    st.session_state.setdefault(SEL_SKUS, [])
    st.session_state.setdefault(SEL_CHANS, [])
    st.session_state.setdefault(SEL_SERIES, None)


def _sync():
    st.session_state[SEL_SKUS] = st.session_state.get("w_skus", [])
    st.session_state[SEL_CHANS] = st.session_state.get("w_channels", [])


def _reset():
    st.session_state[SEL_SKUS] = []
    st.session_state[SEL_CHANS] = []
    st.session_state["w_skus"] = []
    st.session_state["w_channels"] = []


def render_sidebar_filters():
    """Render the shared planning filters in the sidebar (Pages 2-4 only)."""
    # Re-seed widget keys from canonical values (widget keys may be GC'd
    # after visiting a page without filters).
    if "w_skus" not in st.session_state:
        st.session_state["w_skus"] = st.session_state.get(SEL_SKUS, [])
    if "w_channels" not in st.session_state:
        st.session_state["w_channels"] = st.session_state.get(SEL_CHANS, [])

    st.sidebar.markdown("#### Planning filters")
    st.sidebar.multiselect("SKU", ALL_SKUS, key="w_skus",
                           placeholder="All SKUs", on_change=_sync)
    st.sidebar.multiselect("Channel", ALL_CHANNELS, key="w_channels",
                           placeholder="All channels", on_change=_sync)
    st.sidebar.button("Reset filters", on_click=_reset, width='stretch')
    st.sidebar.caption("Filters apply to Demand, Risk and Decision Queue. "
                       "Executive and Governance pages stay full-portfolio.")


def get_selected():
    return st.session_state.get(SEL_SKUS, []), st.session_state.get(SEL_CHANS, [])


def is_filtered() -> bool:
    skus, chans = get_selected()
    return bool(skus) or bool(chans)


def filtered_caption() -> str | None:
    """Human-readable 'Filtered View' note, or None when full portfolio."""
    if not is_filtered():
        return None
    skus, chans = get_selected()
    parts = []
    if skus:
        parts.append("SKU: " + ", ".join(skus))
    if chans:
        parts.append("Channel: " + ", ".join(chans))
    return "Filtered View — " + " · ".join(parts)
