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

    n_weekly = int((series_df["risk_type"] == "WEEKLY_SERVICE_RISK").sum())
    n_below = int((series_df["base_final_wos"] < 2.5).sum())
    if n_weekly:
        insight = (f"Portfolio fill is <b>{fmt.pct(e['base_13w_fill_rate'])}</b>, but {n_weekly} "
                   f"series miss the weekly 92% target in 2+ weeks, and {n_below} of 9 finish "
                   "below safety-stock policy. Healthy aggregates can hide weekly failures.")
    else:
        insight = (f"Portfolio fill is <b>{fmt.pct(e['base_13w_fill_rate'])}</b> and no series "
                   "misses the weekly 92% target once in-transit replenishment is counted. "
                   f"The risk is coverage: {n_below} of 9 finish below the 2.5-week policy.")
    cards.page_header(
        "Planning · Flagship", "Service & Inventory Risk",
        "Where does weekly execution or ending coverage fall short?",
        insight,
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
         "sub": "Repeated weekly miss", "sub_kind": "warn" if len(p1) else "up",
         "accent": "p1" if len(p1) else "ok"},
        {"label": "Worst Weekly Fill", "value": fmt.pct(worst_fill),
         "sub": "Single-week low", "accent": "p1"},
        {"label": "Shared Worst-Service Week", "value": worst_lbl,
         "sub": "Zero-receipt week between batches" if len(p1) else "No week below target",
         "accent": "p2"},
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
        if len(p1):
            receipts_note = ('Receipts arrive in lumpy batches. The shared worst-service week '
                             'is a zero-receipt week between batches; thin-buffer series miss '
                             'service there. Diagnostic alignment, not proven causality.')
        else:
            receipts_note = ('Receipts arrive in batches: in-transit replenishment in the first '
                             'three weeks, then the seasonal drops. Every week is covered; the '
                             'gaps between drops show up as thin ending cover, not missed sales.')
        st.markdown(f'<div class="diq-note">{receipts_note}</div>', unsafe_allow_html=True)
    with c2:
        st.plotly_chart(risk_charts.ending_wos(series_f),
                        width='stretch', config=PLOTLY_CONFIG)
        n_p2 = int((series_f["priority_tier"] == "P2").sum())
        st.markdown(f'<div class="diq-note">{n_below} of 9 series finish below policy cover; '
                    f'{len(p1)} also miss weekly service repeatedly (P1). {n_p2} are P2 PROTECT '
                    'in this view.</div>', unsafe_allow_html=True)
