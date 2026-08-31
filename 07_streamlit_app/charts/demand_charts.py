"""Demand visuals (Pages 1 & 2). Pure builders returning Plotly figures."""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from utils import theme
from utils.formatting import SKU_NAMES


def _weekly_portfolio(weekly: pd.DataFrame) -> pd.DataFrame:
    """Aggregate weekly rows to portfolio totals per week (sum of frozen values)."""
    return (
        weekly.groupby("forecast_week_start", as_index=False)[
            ["base_forecast_units", "mild_scenario_forecast_units",
             "severe_scenario_forecast_units"]
        ].sum().sort_values("forecast_week_start")
    )


def portfolio_demand_trend(weekly: pd.DataFrame, title: str | None = None):
    """Base line + Mild–Severe scenario band + peak marker.

    Peak is DERIVED from the (filtered) data, never hardcoded.
    """
    d = _weekly_portfolio(weekly)
    fig = go.Figure()

    # Scenario band: Severe (upper) then Mild (lower) filled to it.
    fig.add_trace(go.Scatter(
        x=d["forecast_week_start"], y=d["severe_scenario_forecast_units"],
        mode="lines", line=dict(width=0), name="Severe",
        hovertemplate="Severe: %{y:,.0f}<extra></extra>", showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=d["forecast_week_start"], y=d["mild_scenario_forecast_units"],
        mode="lines", line=dict(width=0), fill="tonexty", fillcolor=theme.BAND_FILL,
        name="Mild", hovertemplate="Mild: %{y:,.0f}<extra></extra>", showlegend=True,
    ))
    # Base line (primary)
    fig.add_trace(go.Scatter(
        x=d["forecast_week_start"], y=d["base_forecast_units"],
        mode="lines+markers", line=dict(color=theme.BASE_LINE, width=3),
        marker=dict(size=5), name="Base",
        hovertemplate="%{x|%b %d, %Y}<br>Base: %{y:,.0f} units<extra></extra>",
    ))

    # Peak base week marker (derived)
    if len(d):
        pk = d.loc[d["base_forecast_units"].idxmax()]
        fig.add_trace(go.Scatter(
            x=[pk["forecast_week_start"]], y=[pk["base_forecast_units"]],
            mode="markers", marker=dict(size=11, color=theme.P1, symbol="circle"),
            name="Peak Base week",
            hovertemplate="Peak Base<br>%{x|%b %d, %Y}<br>%{y:,.0f} units<extra></extra>",
        ))
        fig.add_annotation(
            x=pk["forecast_week_start"], y=pk["base_forecast_units"],
            text=f"Peak · {pk['forecast_week_start']:%b %d}", showarrow=True,
            arrowhead=0, ax=0, ay=-34, font=dict(color=theme.P1, size=12),
        )

    fig.update_layout(hovermode="x unified")
    if title:
        fig.update_layout(title=title)
    fig.update_yaxes(title_text="units / week")
    fig = theme.apply_theme(fig, height=450)
    if not title:
        fig.update_layout(title_text="", margin_t=28)
    return fig


def demand_by_dimension(series: pd.DataFrame, dimension: str, scenario: str = "base"):
    """Horizontal bar of 13-week demand by 'sku_id' or 'channel_id'."""
    col = {
        "base": "base_13w_demand_units",
        "mild": "mild_13w_demand_units",
        "severe": "severe_13w_demand_units",
    }[scenario]
    agg = series.groupby(dimension, as_index=False)[col].sum().sort_values(col)

    if dimension == "sku_id":
        agg["label"] = agg[dimension].map(lambda s: f"{s} · {SKU_NAMES.get(s, s)}")
        title = f"13-Week {scenario.title()} Demand by SKU"
    else:
        agg["label"] = agg[dimension]
        title = f"13-Week {scenario.title()} Demand by Channel"

    fig = px.bar(agg, x=col, y="label", orientation="h",
                 color="label", color_discrete_sequence=theme.CATEGORICAL, text=col)
    fig.update_traces(
        texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False,
        textfont=dict(size=15),
        hovertemplate="%{y}<br>%{x:,.0f} units<extra></extra>",
    )
    fig.update_layout(title=title, showlegend=False)
    # Headroom so outside bar labels (e.g. 16,504) are never clipped.
    fig.update_xaxes(title_text="units (13 weeks)",
                     range=[0, float(agg[col].max()) * 1.18])
    fig.update_yaxes(title_text="", tickfont=dict(size=15))
    return theme.apply_theme(fig, height=380, legend=False)
