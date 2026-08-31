"""Service & inventory risk visuals (Page 3) + selected-series trajectory (Page 4).
Pure builders returning Plotly figures.
"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

from utils import theme
from utils.formatting import series_label


def _series_order(series_df: pd.DataFrame) -> list[str]:
    """P1 first, then P2, then by worst weekly fill ascending."""
    s = series_df.copy()
    s["_tier"] = s["priority_tier"].map({"P1": 0, "P2": 1, "P3": 2, "P4": 3}).fillna(9)
    s = s.sort_values(["_tier", "min_weekly_base_fill_rate"])
    return [series_label(r.sku_id, r.channel_id) for r in s.itertuples()]


def fill_rate_heatmap(weekly: pd.DataFrame, series_df: pd.DataFrame, title: str | None = None):
    """9 series x 13 weeks Base weekly fill-rate heatmap, threshold 92%.

    Below-target cells carry a text label; worst values come from data.
    """
    w = weekly.copy()
    w["series"] = w.apply(lambda r: series_label(r["sku_id"], r["channel_id"]), axis=1)
    w["gap"] = (w["base_forecast_units"] - w["base_shipped_units"]).clip(lower=0)

    weeks = sorted(w["forecast_week_start"].unique())
    week_labels = [pd.Timestamp(d).strftime("%b %d") for d in weeks]
    order = [s for s in _series_order(series_df) if s in set(w["series"])]

    z, text, custom = [], [], []
    for s in order:
        row = w[w["series"] == s].set_index("forecast_week_start")
        z.append([float(row.loc[d, "base_fill_rate"]) for d in weeks])
        text.append([
            f"{row.loc[d, 'base_fill_rate'] * 100:.0f}%"
            if row.loc[d, "base_fill_rate"] < 0.92 else ""
            for d in weeks
        ])
        custom.append([[float(row.loc[d, "gap"])] for d in weeks])

    fig = go.Figure(go.Heatmap(
        z=z, x=week_labels, y=order, customdata=custom,
        colorscale=theme.FILL_COLORSCALE, zmin=0.0, zmax=1.0, zmid=0.92,
        text=text, texttemplate="%{text}", textfont=dict(size=11, color="white"),
        xgap=2, ygap=3,
        colorbar=dict(title="Base fill", tickformat=".0%", thickness=12, len=0.8),
        hovertemplate=("%{y}<br>%{x}<br>Base fill: %{z:.1%}"
                       "<br>Service gap: %{customdata[0]:,.0f} units<extra></extra>"),
    ))
    if title:
        fig.update_layout(title=title)
    fig.update_xaxes(tickfont=dict(size=13), side="bottom")
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=14))
    fig = theme.apply_theme(fig, height=540, legend=False, ygrid=False)
    if not title:
        fig.update_layout(title_text="", margin_t=20)
    return fig


def demand_vs_receipts(weekly: pd.DataFrame, highlight_week=None):
    """Portfolio Base demand (line) vs committed receipts (bars).

    Receipts arrive in lumpy batches; `highlight_week` (the shared worst-service
    week, from frozen data) is annotated once. Diagnostic alignment, not a
    proven-cause claim.
    """
    d = (weekly.groupby("forecast_week_start", as_index=False)[
        ["base_forecast_units", "committed_receipt_units"]].sum()
        .sort_values("forecast_week_start").reset_index(drop=True))
    xlab = [pd.Timestamp(x).strftime("%b %d") for x in d["forecast_week_start"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=xlab, y=d["committed_receipt_units"], name="Committed receipts",
        marker_color=theme.P2, opacity=0.85,
        hovertemplate="%{x}<br>Receipts: %{y:,.0f} units<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=xlab, y=d["base_forecast_units"], name="Base demand",
        mode="lines+markers", line=dict(color=theme.BASE_LINE, width=3),
        hovertemplate="%{x}<br>Base demand: %{y:,.0f} units<extra></extra>",
    ))

    # Mark the shared worst-service week (a zero-receipt week between batches).
    if highlight_week is not None:
        hw = pd.Timestamp(highlight_week)
        match = d.index[d["forecast_week_start"] == hw]
        if len(match):
            i = int(match[0])
            fig.add_vrect(x0=i - 0.5, x1=i + 0.5, fillcolor=theme.P1, opacity=0.12,
                          line_width=0, layer="below")
            fig.add_annotation(
                x=xlab[i], y=1.0, yref="paper", showarrow=False, xanchor="center",
                text=f"⬤ {hw:%b %d} · worst service week · 0 receipts",
                font=dict(color=theme.P1, size=13),
            )

    fig.update_layout(title="Demand vs Committed Receipts (lumpy replenishment)",
                      barmode="overlay")
    fig.update_yaxes(title_text="units / week")
    return theme.apply_theme(fig, height=390)


def ending_wos(series_df: pd.DataFrame):
    """Ending WOS per series vs 2.5-week safety-stock policy line."""
    s = series_df.copy()
    s["series"] = s.apply(lambda r: series_label(r["sku_id"], r["channel_id"]), axis=1)
    s["_tier"] = s["priority_tier"].map({"P1": 0, "P2": 1}).fillna(9)
    s = s.sort_values(["_tier", "base_final_wos"], ascending=[True, True])
    colors = [theme.TIER_COLORS.get(t, theme.NEUTRAL) for t in s["priority_tier"]]

    fig = go.Figure(go.Bar(
        x=s["base_final_wos"], y=s["series"], orientation="h",
        marker_color=colors, text=s["base_final_wos"],
        texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False,
        textfont=dict(size=14),
        customdata=s[["priority_tier", "risk_type"]].values,
        hovertemplate=("%{y}<br>Ending WOS: %{x:.2f} weeks"
                       "<br>%{customdata[0]} · %{customdata[1]}<extra></extra>"),
    ))
    fig.add_vline(x=2.5, line=dict(color=theme.INK, dash="dash", width=2),
                  annotation_text="2.5-week safety-stock policy", annotation_position="top",
                  annotation_font=dict(size=13, color=theme.INK))
    fig.update_layout(title="Ending Weeks of Supply vs 2.5-Week Policy", showlegend=False)
    fig.update_xaxes(title_text="weeks of supply", range=[0, 2.9])
    fig.update_yaxes(title_text="", autorange="reversed", tickfont=dict(size=14))
    return theme.apply_theme(fig, height=420, legend=False)


def series_trajectory(weekly_one: pd.DataFrame, label: str, show_title: bool = True):
    """Selected-series weekly Base fill (bars) with 92% target + receipts overlay.

    Answers: when does this series miss, and how does it ALIGN with receipt
    timing? (Diagnostic alignment — not a proven causal claim.)
    """
    d = weekly_one.sort_values("forecast_week_start")
    xlab = [pd.Timestamp(x).strftime("%b %d") for x in d["forecast_week_start"]]
    bar_colors = [theme.P1 if f < 0.92 else theme.P2 for f in d["base_fill_rate"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=xlab, y=d["base_fill_rate"], name="Base weekly fill",
        marker_color=bar_colors, yaxis="y",
        customdata=d[["base_forecast_units", "base_shipped_units",
                      "committed_receipt_units"]].values,
        hovertemplate=("%{x}<br>Base fill: %{y:.1%}"
                       "<br>Demand: %{customdata[0]:,.0f} · Shipped: %{customdata[1]:,.0f}"
                       "<br>Receipts: %{customdata[2]:,.0f}<extra></extra>"),
    ))
    fig.add_trace(go.Scatter(
        x=xlab, y=d["committed_receipt_units"], name="Committed receipts",
        mode="lines+markers", line=dict(color=theme.SUBTLE, width=2, dash="dot"),
        yaxis="y2", hovertemplate="%{x}<br>Receipts: %{y:,.0f} units<extra></extra>",
    ))
    fig.add_hline(y=0.92, line=dict(color=theme.INK, dash="dash", width=1.5),
                  annotation_text="92% target", annotation_position="bottom right")

    fig.update_layout(
        yaxis=dict(title="Base fill", tickformat=".0%", range=[0, 1.05]),
        yaxis2=dict(title="receipts (units)", overlaying="y", side="right",
                    showgrid=False),
    )
    if show_title:
        fig.update_layout(title=f"Selected Series — Weekly Base Fill & Receipts · {label}")
    fig = theme.apply_theme(fig, height=430, ygrid=False)
    if not show_title:
        fig.update_layout(title_text="", margin_t=24)
    return fig
