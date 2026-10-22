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


def _count(exec_row, key, fallback):
    """Exec count with a fallback for decision layers written before the split counts."""
    return int(exec_row[key]) if key in exec_row.index else int(fallback)


def status_banner(exec_row):
    """Portfolio status banner (Page 1), worded from the data."""
    weekly_risk = int(exec_row["p1_weekly_service_risk_series"])
    escalate = _count(exec_row, "escalate_series", weekly_risk)
    protect = _count(exec_row, "protect_series", exec_row["p2_low_coverage_risk_series"])
    hold = _count(exec_row, "hold_series", 0)
    base_fill = fmt.pct(exec_row["base_13w_fill_rate"])
    target = fmt.pct(exec_row["service_target_fill_rate"])
    ss_gap = fmt.units_k(exec_row["base_safety_stock_protection_gap_units"])
    estimate = float(exec_row.get("estimated_replenishment_13w_units", 0.0) or 0.0)
    conditional = estimate > 0

    # committed_receipt_units is a legacy v1 name: the seasonal drops are projected
    # from last year's receipts, not confirmed supplier orders.
    supply = "Projected seasonal drops (not confirmed orders)"
    if conditional:
        supply = (f"Projected seasonal drops + {fmt.units_k(estimate)} estimated "
                  "replenishment (unconfirmed)")
    response = f"{escalate} ESCALATE · {protect} PROTECT · {hold} HOLD · 0 auto chase"
    cells = [
        ("Portfolio health", f"Base fill {base_fill} vs {target} target"),
        ("Weekly execution risk", f"{weekly_risk} series miss weekly service 2+ times"),
        ("Supply counted", supply),
        ("If the estimate arrives as modelled" if conditional else "Planner response", response),
    ]
    if conditional:
        zero = (f"{_count(exec_row, 'zero_replenishment_escalate_series', 0)} ESCALATE · "
                f"{_count(exec_row, 'zero_replenishment_protect_series', 0)} PROTECT · "
                f"{_count(exec_row, 'zero_replenishment_hold_series', 0)} HOLD (published list)")
        cells.append(("With zero replenishment", zero))
    if escalate:
        flag = "▲ Action Required"
        headline = (f"Aggregate service is healthy, but {escalate} series "
                    f"{'has' if escalate == 1 else 'have'} repeated weekly service misses")
    else:
        flag = "● No Escalation" + (" if the estimate arrives" if conditional else "")
        low_cover = int(exec_row["p2_low_coverage_risk_series"])
        severe = _count(exec_row, "p2_severe_scenario_risk_series", 0)
        headline = (("If the estimated replenishment arrives as modelled, service holds"
                     if conditional else "Service holds")
                    + f" in every week; {low_cover} series finish below the "
                    f"2.5-week safety-stock policy (gap {ss_gap})"
                    + (f" and {severe} more under severe weather" if severe else "")
                    + f", so {protect} are protected")
    if conditional:
        headline += (". Both supply streams are projected from last year, not confirmed "
                     "supplier orders: a planner must confirm open-order quantities and "
                     "receipt dates before this replaces the published escalation list")
    grid = "".join(
        f'<div class="diq-banner-cell"><div class="k">{_esc(k)}</div>'
        f'<div class="v">{_esc(v)}</div></div>' for k, v in cells
    )
    st.markdown(
        f'<div class="diq-banner"><div class="flag">{_esc(flag)}</div>'
        f'<div class="headline">{_esc(headline)}</div>'
        f'<div class="diq-banner-grid">{grid}</div></div>',
        unsafe_allow_html=True,
    )


def _weekly_miss(r) -> bool:
    return int(r.weeks_below_service_target) > 0


def priority_cards(series_df, limit: int = 3):
    """Page 1 action cards: P1 escalations if any, otherwise the thinnest PROTECT series."""
    p1 = series_df[series_df["priority_tier"] == "P1"].sort_values("min_weekly_base_fill_rate")
    rows = p1 if len(p1) else (
        series_df[series_df["planner_action"] == "PROTECT"].sort_values("base_final_wos")
    )
    cards = []
    for r in rows.head(limit if not len(p1) else len(p1)).itertuples():
        tier_cls = "p1" if r.priority_tier == "P1" else "p2"
        risk = fmt.RISK_LABELS.get(r.risk_type, r.risk_type)
        worst_week = fmt.date_short(r.worst_base_service_week) if _weekly_miss(r) else "—"
        cards.append(
            f'<div class="diq-decision">'
            f'<div class="top"><span class="diq-chip {tier_cls}">{_esc(r.priority_tier)}</span>'
            f'<span class="name">{_esc(r.sku_id)} · {_esc(r.channel_id)}</span></div>'
            f'<div class="risk">{_esc(risk)}</div>'
            f'<div class="row"><span>Worst weekly fill</span><b>{fmt.pct(r.min_weekly_base_fill_rate)}</b></div>'
            f'<div class="row"><span>Worst week</span><b>{_esc(worst_week)}</b></div>'
            f'<div class="row"><span>Ending cover</span><b>{fmt.wos(r.base_final_wos)}</b></div>'
            f'<div class="row"><span>Planner action</span><b>{_esc(r.planner_action)}</b></div>'
            f'</div>'
        )
    st.markdown(f'<div class="diq-decision-grid">{"".join(cards)}</div>',
                unsafe_allow_html=True)


def p1_decision_cards(series_df):
    """Backward-compatible alias."""
    priority_cards(series_df)


def series_header(row):
    """Selected-series header card (Page 4)."""
    tier_cls = {"P1": "p1", "P2": "p2"}.get(row["priority_tier"], "ok")
    chip = tier_cls
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
