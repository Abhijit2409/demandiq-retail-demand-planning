"""Decision-queue tables (Page 1 mini + Page 4 interactive). UI rendering only.

Tables DISPLAY frozen rows with business-friendly labels. They never
recompute risk_type, priority_tier, or planner_action.
"""
from __future__ import annotations
import streamlit as st
import pandas as pd

from utils import formatting as fmt


TIER_ORDER = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}


def _sorted(series_df: pd.DataFrame) -> pd.DataFrame:
    s = series_df.copy()
    s["_tier"] = s["priority_tier"].map(TIER_ORDER).fillna(9)
    return (s.sort_values(["_tier", "weeks_below_service_target", "min_weekly_base_fill_rate"],
                          ascending=[True, False, True])
             .drop(columns="_tier").reset_index(drop=True))


def mini_decision_queue(series_df: pd.DataFrame):
    """Concise executive queue for Page 1 — 5 columns, P1 first, read-only."""
    s = _sorted(series_df)
    view = pd.DataFrame({
        "Priority": s["priority_tier"],
        "SKU": s["sku_id"],
        "Channel": s["channel_id"],
        "Risk": s["risk_type"].map(fmt.RISK_LABELS).fillna(s["risk_type"]),
        "Action": s["planner_action"],
    })
    st.dataframe(view, hide_index=True, width='stretch',
                 column_config={"Priority": st.column_config.TextColumn(width="small")})


def decision_queue_table(series_df: pd.DataFrame):
    """Interactive Page-4 queue with single-row selection.

    Returns the selected frozen series row (pd.Series) or None.
    Default selection = first P1 row when nothing is chosen.
    """
    s = _sorted(series_df)
    view = pd.DataFrame({
        "Priority": s["priority_tier"],
        "SKU": s["sku_id"],
        "Channel": s["channel_id"],
        "Risk": s["risk_type"].map(fmt.RISK_LABELS).fillna(s["risk_type"]),
        "Action": s["planner_action"],
        "13W Fill": s["base_13w_fill_rate"].map(lambda v: fmt.pct(v)),
        "Worst Weekly Fill": s["min_weekly_base_fill_rate"].map(lambda v: fmt.pct(v)),
        "Worst Week": s["worst_base_service_week"].map(fmt.date_short),
        "Weeks Below": s["weeks_below_service_target"].astype(int),
        "Ending WOS": s["base_final_wos"].map(lambda v: fmt.wos(v)),
    })

    event = st.dataframe(
        view, hide_index=True, width='stretch', height=388,
        on_select="rerun", selection_mode="single-row",
        column_config={
            "Priority": st.column_config.TextColumn(width="small"),
            "SKU": st.column_config.TextColumn(width="small"),
            "Channel": st.column_config.TextColumn(width="small"),
            "Risk": st.column_config.TextColumn(width="medium"),
            "Action": st.column_config.TextColumn(width="small"),
        },
    )

    rows = []
    sel = getattr(event, "selection", None)
    if sel is not None:
        rows = getattr(sel, "rows", None)
        if rows is None and isinstance(sel, dict):
            rows = sel.get("rows", [])
    if rows:
        return s.iloc[rows[0]]
    if len(s):
        return s.iloc[0]  # default: first P1
    return None
