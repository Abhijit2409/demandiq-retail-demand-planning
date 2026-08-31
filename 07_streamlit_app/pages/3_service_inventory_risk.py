"""Page 3 — Service & Inventory Risk (flagship). Shared SKU/Channel filters."""
from __future__ import annotations
import streamlit as st

from utils.data_loader import get_step6a, apply_series_filter
from utils import filters, formatting as fmt
from utils.theme import PLOTLY_CONFIG
from components import cards
from charts import risk_charts


def render():
    exec_df, series_df, weekly_df = get_step6a()
    e = exec_df.iloc[0]
    skus, chans = filters.get_selected()

    cards.page_header(
        "Planning · Flagship", "Service & Inventory Risk",
        "How can healthy aggregate service coexist with execution risk?",
        "Portfolio fill is <b>98.8%</b>, but three series miss the weekly 92% target twice "
        "each, while all nine finish below safety-stock policy — healthy aggregates can hide "
        "localized weekly execution failures.",
    )

    series_f = apply_series_filter(series_df, skus, chans)
    weekly_f = apply_series_filter(weekly_df, skus, chans)
    if weekly_f.empty:
        st.warning("No series match the current filters. Use **Reset filters** in the sidebar.")
        st.stop()

    # ---- Risk snapshot (frozen/derived) ----
    p1 = series_f[series_f["risk_type"] == "WEEKLY_SERVICE_RISK"]
    worst_fill = series_f["min_weekly_base_fill_rate"].min()
    # Shared worst-service week: the week the P1 series stock out (frozen).
    if len(p1):
        worst_week = p1["worst_base_service_week"].mode().iloc[0]
        worst_lbl = fmt.date_short(worst_week)
    else:
        worst_week, worst_lbl = None, "—"
    cards.kpi_grid([
        {"label": "Aggregate Base Fill", "value": fmt.pct(e["base_13w_fill_rate"]),
         "sub": "≥ 92% target", "sub_kind": "up", "accent": "ok"},
        {"label": "P1 Weekly Risks", "value": f"{len(p1)} series",
         "sub": "Repeated weekly miss", "sub_kind": "warn", "accent": "p1"},
        {"label": "Worst Weekly Fill", "value": fmt.pct(worst_fill),
         "sub": "Single-week low", "accent": "p1"},
        {"label": "Shared Worst-Service Week", "value": worst_lbl,
         "sub": "Zero-receipt week between batches", "accent": "p2"},
    ])
    st.write("")

    cards.section("Weekly Base Fill Rate", "9 series × 13 weeks · below-target weeks in warm tones")
    st.plotly_chart(risk_charts.fill_rate_heatmap(weekly_f, series_f),
                    width='stretch', config=PLOTLY_CONFIG)

    st.write("")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.plotly_chart(risk_charts.demand_vs_receipts(weekly_f, highlight_week=worst_week),
                        width='stretch', config=PLOTLY_CONFIG)
        st.markdown('<div class="diq-note">Receipts arrive in lumpy batches. The shared '
                    'worst-service week is a zero-receipt week between replenishments; '
                    'thin-buffer series miss service there while better-buffered series hold. '
                    'Diagnostic alignment, not proven causality.</div>',
                    unsafe_allow_html=True)
    with c2:
        st.plotly_chart(risk_charts.ending_wos(series_f),
                        width='stretch', config=PLOTLY_CONFIG)
        st.markdown('<div class="diq-note">All nine series finish below policy coverage; only '
                    'three also experience repeated weekly service misses (P1). The rest are '
                    'P2 PROTECT.</div>', unsafe_allow_html=True)
