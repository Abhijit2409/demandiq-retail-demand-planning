"""Reusable HTML card primitives for the DemandIQ overhaul.

Custom cards replace narrow st.metric rows so KPI labels/values wrap and never
truncate. Rendering only — all values come from frozen data passed in.
"""
from __future__ import annotations
import html
import streamlit as st

from utils import formatting as fmt


def _esc(x) -> str:
    return html.escape(str(x))


def page_header(eyebrow: str, title: str, question: str, insight: str):
    st.markdown(
        f'<div class="diq-eyebrow">{_esc(eyebrow)}</div>'
        f'<div class="diq-h1">{_esc(title)}</div>'
        f'<div class="diq-question">{_esc(question)}</div>'
        f'<div class="diq-insight">{insight}</div>'
        f'<hr class="diq-rule"/>',
        unsafe_allow_html=True,
    )


def section(title: str, sub: str | None = None):
    html_str = f'<div class="diq-section">{_esc(title)}</div>'
    if sub:
        html_str += f'<div class="diq-section-sub">{_esc(sub)}</div>'
    st.markdown(html_str, unsafe_allow_html=True)


def kpi_grid(cards: list[dict]):
    """cards: [{label, value, sub?, sub_kind?('up'|'warn'), accent?('p1'|'p2'|'ok')}]."""
    cells = []
    for c in cards:
        accent = c.get("accent", "")
        sub = ""
        if c.get("sub"):
            sk = c.get("sub_kind", "")
            sub = f'<div class="diq-kpi-sub {sk}">{_esc(c["sub"])}</div>'
        cells.append(
            f'<div class="diq-kpi {accent}">'
            f'<div class="diq-kpi-label">{_esc(c["label"])}</div>'
            f'<div class="diq-kpi-value">{_esc(c["value"])}</div>'
            f'{sub}</div>'
        )
    st.markdown(f'<div class="diq-kpi-grid">{"".join(cells)}</div>',
                unsafe_allow_html=True)


def status_banner(exec_row):
    """Structured ACTION REQUIRED banner (Page 1)."""
    p1 = int(exec_row["p1_weekly_service_risk_series"])
    p2 = int(exec_row["p2_low_coverage_risk_series"])
    base_fill = fmt.pct(exec_row["base_13w_fill_rate"])
    target = fmt.pct(exec_row["service_target_fill_rate"])
    ss_gap = fmt.units_k(exec_row["base_safety_stock_protection_gap_units"])

    cells = [
        ("Portfolio health", f"Base fill {base_fill} ≥ {target} target"),
        ("Weekly execution risk", f"{p1} series miss weekly service 2+ times"),
        ("Inventory coverage", f"Safety-stock gap {ss_gap}"),
        ("Planner response", f"{p1} ESCALATE · {p2} PROTECT · 0 auto chase"),
    ]
    grid = "".join(
        f'<div class="diq-banner-cell"><div class="k">{_esc(k)}</div>'
        f'<div class="v">{_esc(v)}</div></div>' for k, v in cells
    )
    st.markdown(
        f'<div class="diq-banner"><div class="flag">▲ Action Required</div>'
        f'<div class="headline">Aggregate service is healthy, but three series '
        f'have repeated weekly service misses</div>'
        f'<div class="diq-banner-grid">{grid}</div></div>',
        unsafe_allow_html=True,
    )


def p1_decision_cards(series_df):
    """Three readable P1 decision cards (Page 1)."""
    p1 = series_df[series_df["risk_type"] == "WEEKLY_SERVICE_RISK"].copy()
    p1 = p1.sort_values("min_weekly_base_fill_rate")
    cards = []
    for r in p1.itertuples():
        cards.append(
            f'<div class="diq-decision">'
            f'<div class="top"><span class="diq-chip p1">P1</span>'
            f'<span class="name">{_esc(r.sku_id)} · {_esc(r.channel_id)}</span></div>'
            f'<div class="risk">Weekly Service Risk</div>'
            f'<div class="row"><span>Worst weekly fill</span><b>{fmt.pct(r.min_weekly_base_fill_rate)}</b></div>'
            f'<div class="row"><span>Worst week</span><b>{fmt.date_short(r.worst_base_service_week)}</b></div>'
            f'<div class="row"><span>Weeks below target</span><b>{int(r.weeks_below_service_target)}</b></div>'
            f'<div class="row"><span>Planner action</span><b>{_esc(r.planner_action)}</b></div>'
            f'</div>'
        )
    st.markdown(f'<div class="diq-decision-grid">{"".join(cards)}</div>',
                unsafe_allow_html=True)


def series_header(row):
    """Selected-series header card (Page 4)."""
    tier_cls = "p1" if row["priority_tier"] == "P1" else "p2"
    chip = "p1" if row["priority_tier"] == "P1" else "p2"
    risk_label = fmt.RISK_LABELS.get(row["risk_type"], row["risk_type"]).upper()
    st.markdown(
        f'<div class="diq-series-header {tier_cls}">'
        f'<div class="name">{_esc(row["sku_id"])} · {_esc(row["channel_id"])}</div>'
        f'<div class="tags"><span class="diq-chip {chip}">{_esc(row["priority_tier"])} · '
        f'{_esc(risk_label)}</span> &nbsp; Planner Action: '
        f'<b>{_esc(row["planner_action"])}</b></div></div>',
        unsafe_allow_html=True,
    )


def callout(kind: str, title: str, body: str):
    """kind: 'why' | 'boundary'."""
    st.markdown(
        f'<div class="diq-callout {kind}"><div class="t">{_esc(title)}</div>'
        f'<div class="b">{body}</div></div>',
        unsafe_allow_html=True,
    )


def methodology_journey(steps: list[str]):
    parts = []
    for i, s in enumerate(steps):
        parts.append(
            f'<div class="diq-journey-step"><div class="n">{i + 1}</div>'
            f'<div class="t">{_esc(s)}</div></div>'
        )
        if i < len(steps) - 1:
            parts.append('<div class="diq-journey-arrow">→</div>')
    st.markdown(f'<div class="diq-journey">{"".join(parts)}</div>',
                unsafe_allow_html=True)


def weather_timeline():
    st.markdown(
        '<div class="diq-timeline">'
        '<div class="diq-tl-seg diq-tl-nowcast"><div class="lab">Weeks 1–3</div>'
        '<div class="val">NOWCAST REQUIRED</div></div>'
        '<div class="diq-tl-seg diq-tl-scenario"><div class="lab">Weeks 4–13</div>'
        '<div class="val">Scenario Planning · Mild / Normal / Severe</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )


def info_cards(cards: list[dict]):
    """cards: [{cls, h, b}] for provenance/limitations."""
    cells = "".join(
        f'<div class="diq-info-card {c.get("cls", "")}">'
        f'<div class="h">{_esc(c["h"])}</div><div class="b">{c["b"]}</div></div>'
        for c in cards
    )
    st.markdown(f'<div class="diq-info-grid">{cells}</div>', unsafe_allow_html=True)
