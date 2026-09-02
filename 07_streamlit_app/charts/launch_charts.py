"""Page 6 (New Product Launch Planning) Plotly builders. Pure functions that
return themed figures from FROZEN Step 7B–7F values. No analytics, no file I/O.
"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

from utils import theme

# Local (Page-6-only) accents drawn from the shared palette
PRIMARY = theme.P2          # slate — primary analog / approved
SECONDARY = theme.HEALTHY   # moss — secondary analog
EXCLUDED = theme.NEUTRAL    # grey — excluded
ACCENT = theme.P1           # clay — highlight / attention
BASE = theme.BASE_LINE

_VERSION_COLORS = {
    "V0_ANALYTICAL_BASELINE": theme.NEUTRAL,
    "V1_COMMERCIAL_PLAN": theme.P1,
    "V2_CONSENSUS_FORECAST": theme.P2,
    "V3_APPROVED_PLAN": theme.BASE_LINE,
}
_VERSION_LABEL = {
    "V0_ANALYTICAL_BASELINE": "V0 Analytical",
    "V1_COMMERCIAL_PLAN": "V1 Commercial",
    "V2_CONSENSUS_FORECAST": "V2 Consensus",
    "V3_APPROVED_PLAN": "V3 Approved",
}


# ------------------------------------------------------------------ S2
def analog_scorecard(scorecard: pd.DataFrame):
    """Horizontal analog-similarity score bars: APS primary, IMH secondary, CTS excluded."""
    role = {"APS-001": ("Primary analog · 60%", PRIMARY),
            "IMH-001": ("Secondary analog · 40%", SECONDARY),
            "CTS-001": ("Excluded from blend", EXCLUDED)}
    d = scorecard.sort_values("final_score")
    colors = [role.get(c, ("", theme.NEUTRAL))[1] for c in d["candidate"]]
    labels = [f"{c} · {role.get(c, ('', ''))[0]}" for c in d["candidate"]]
    fig = go.Figure(go.Bar(
        x=d["final_score"], y=labels, orientation="h", marker_color=colors,
        text=[f"{v:.3f}" for v in d["final_score"]], textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}<br>Similarity score: %{x:.3f}<extra></extra>",
    ))
    fig.update_layout(title="Analog Selection — Similarity Score", showlegend=False)
    fig.update_xaxes(title_text="composite similarity score",
                     range=[0, float(d["final_score"].max()) * 1.25])
    fig.update_yaxes(title_text="")
    return theme.apply_theme(fig, height=320, legend=False)


def v0_baseline_18m(v0_18m: pd.DataFrame, channel: str):
    """V0 analytical baseline over 18 months with light lifecycle-phase peak marker."""
    d = v0_18m
    if channel and channel != "ALL":
        d = d[d["channel_id"] == channel]
    g = (d.groupby("planning_month", as_index=False)
           .agg(units=("analytical_baseline_units", "sum"),
                phase=("lifecycle_phase", "first"))
           .sort_values("planning_month"))
    scope = channel if channel not in (None, "ALL") else "All channels"
    fig = go.Figure(go.Scatter(
        x=g["planning_month"], y=g["units"], mode="lines+markers",
        line=dict(color=BASE, width=3), marker=dict(size=6),
        customdata=g["phase"],
        hovertemplate="%{x}<br>%{y:,.0f} units<br>Phase: %{customdata}<extra></extra>",
        name="V0 analytical",
    ))
    if len(g):
        pk = g.loc[g["units"].idxmax()]
        fig.add_annotation(x=pk["planning_month"], y=pk["units"],
                           text=f"Peak · {pk['planning_month']}", showarrow=True,
                           arrowhead=0, ax=0, ay=-34,
                           font=dict(color=ACCENT, size=12))
    fig.update_layout(title=f"V0 Cold-Start 18-Month Analytical Baseline · {scope}",
                      showlegend=False)
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="units / month")
    return theme.apply_theme(fig, height=380, legend=False)


def version_evolution(versions: pd.DataFrame, channel: str):
    """V0 → V1 → V2 → V3 monthly forecast lines."""
    d = versions.copy()
    if channel and channel != "ALL":
        d = d[d["channel_id"] == channel]
    g = (d.groupby(["forecast_version", "planning_month"], as_index=False)
           .forecast_units.sum())
    scope = channel if channel not in (None, "ALL") else "All channels"
    fig = go.Figure()
    for ver in ["V0_ANALYTICAL_BASELINE", "V1_COMMERCIAL_PLAN",
                "V2_CONSENSUS_FORECAST", "V3_APPROVED_PLAN"]:
        s = g[g["forecast_version"] == ver].sort_values("planning_month")
        if not len(s):
            continue
        dash = "dot" if ver == "V3_APPROVED_PLAN" else "solid"
        fig.add_trace(go.Scatter(
            x=s["planning_month"], y=s["forecast_units"], mode="lines",
            line=dict(color=_VERSION_COLORS[ver], width=3, dash=dash),
            name=_VERSION_LABEL[ver],
            hovertemplate=(_VERSION_LABEL[ver] + "<br>%{x}<br>%{y:,.0f} units<extra></extra>"),
        ))
    fig.update_layout(title=f"Forecast Evolution · V0 → V1 → V2 → V3 · {scope}")
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="units / month")
    return theme.apply_theme(fig, height=380)


# ------------------------------------------------------------------ S3
def buy_bridge(buy):
    """Waterfall: V3 covered demand + launch uncertainty buffer = frozen initial buy."""
    covered = float(buy["covered_demand_units"])
    buffer = float(buy["buffer_units"])
    total = float(buy["initial_buy_units"])
    fig = go.Figure(go.Waterfall(
        orientation="v", measure=["absolute", "relative", "total"],
        x=["V3 Approved<br>13-Wk Demand", "Launch Uncertainty<br>Buffer",
           "Frozen Initial Buy"],
        y=[covered, buffer, total],
        text=[f"{covered:,.0f}", f"+{buffer:,.0f}", f"{total:,.0f}"],
        textposition="outside",
        connector=dict(line=dict(color=theme.LINE)),
        decreasing=dict(marker=dict(color=theme.NEUTRAL)),
        increasing=dict(marker=dict(color=SECONDARY)),
        totals=dict(marker=dict(color=BASE)),
        hovertemplate="%{x}<br>%{y:,.0f} units<extra></extra>",
    ))
    fig.update_layout(title="Initial-Buy Bridge (unconstrained demand → committed buy)",
                      showlegend=False)
    fig.update_yaxes(title_text="units")
    return theme.apply_theme(fig, height=360, legend=False)


def allocation_bar(buy, channel: str):
    """Pre-allocation by channel + flex reserve (reserve visually distinct)."""
    rows = [("ECOM", float(buy["alloc_ecom"]), PRIMARY),
            ("RETAIL", float(buy["alloc_retail"]), theme.HEALTHY),
            ("WHOLESALE", float(buy["alloc_wholesale"]), theme.CATEGORICAL[2]),
            ("FLEX RESERVE", float(buy["reserve_units"]), ACCENT)]
    ys = [r[0] for r in rows]
    xs = [r[1] for r in rows]
    colors = [r[2] for r in rows]
    if channel and channel != "ALL":  # dim non-selected channels (reserve stays highlighted)
        colors = [c if (lab == channel or lab == "FLEX RESERVE") else theme.LINE
                  for lab, c in zip(ys, colors)]
    fig = go.Figure(go.Bar(
        x=xs, y=ys, orientation="h", marker_color=colors,
        text=[f"{v:,.0f}" for v in xs], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>%{x:,.0f} units<extra></extra>",
    ))
    fig.update_layout(title="Initial Buy — Channel Pre-Allocation + Flex Reserve",
                      showlegend=False)
    fig.update_xaxes(title_text="units", range=[0, max(xs) * 1.2])
    fig.update_yaxes(title_text="")
    return theme.apply_theme(fig, height=320, legend=False)


# ------------------------------------------------------------------ S4
def plan_vs_observed(weekly: pd.DataFrame, channel: str,
                     latent: pd.DataFrame | None = None):
    """Weekly V3 plan vs observed sales (operational). Optional eval-only latent overlay."""
    d = weekly
    if channel and channel != "ALL":
        d = d[d["channel_id"] == channel]
    g = (d.groupby(["launch_week_number", "week_start"], as_index=False)
           .agg(plan=("planned_units_approved", "sum"),
                observed=("observed_sales_units", "sum"))
           .sort_values("launch_week_number"))
    scope = channel if channel not in (None, "ALL") else "All channels"
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=g["week_start"], y=g["plan"], name="V3 approved plan",
        marker_color=theme.NEUTRAL,
        hovertemplate="%{x|%b %d}<br>Plan: %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=g["week_start"], y=g["observed"], name="Observed sales",
        mode="lines+markers", line=dict(color=BASE, width=3), marker=dict(size=6),
        hovertemplate="%{x|%b %d}<br>Observed: %{y:,.0f}<extra></extra>"))
    if latent is not None:
        ld = latent
        if channel and channel != "ALL":
            ld = ld[ld["channel_id"] == channel]
        lg = (ld.groupby("week_start", as_index=False).latent_units.sum()
                .sort_values("week_start"))
        fig.add_trace(go.Scatter(
            x=lg["week_start"], y=lg["latent_units"], name="Latent (EVAL-ONLY)",
            mode="lines", line=dict(color=ACCENT, width=2, dash="dot"),
            hovertemplate="%{x|%b %d}<br>Latent (eval-only): %{y:,.0f}<extra></extra>"))
    fig.update_layout(title=f"Weekly Plan vs Observed Sales · W1–W13 · {scope}",
                      barmode="overlay", hovermode="x unified")
    fig.update_traces(opacity=0.85, selector=dict(type="bar"))
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="units / week")
    return theme.apply_theme(fig, height=400)


def reforecast_waterfall(checkpoints: pd.DataFrame):
    """13-week demand-view evolution: original V3 → W1/W2/W4/W8/W13 reforecasts (SKU-level)."""
    order = ["ORIGINAL_V3_PLAN", "W1_REFORECAST", "W2_REFORECAST",
             "W4_REFORECAST", "W8_REFORECAST", "W13_REFORECAST"]
    lab = {"ORIGINAL_V3_PLAN": "Original V3", "W1_REFORECAST": "W1",
           "W2_REFORECAST": "W2", "W4_REFORECAST": "W4", "W8_REFORECAST": "W8",
           "W13_REFORECAST": "W13 (final)"}
    d = checkpoints.set_index("forecast_version").reindex(order)
    xs = [lab[o] for o in order]
    ys = [float(d.loc[o, "remaining_horizon_units"]) for o in order]
    fig = go.Figure(go.Scatter(
        x=xs, y=ys, mode="lines+markers+text",
        line=dict(color=BASE, width=3), marker=dict(size=9, color=BASE),
        text=[f"{v:,.0f}" for v in ys], textposition="top center",
        hovertemplate="%{x}<br>%{y:,.0f} units<extra></extra>"))
    fig.update_layout(title="Reforecast Evolution — 13-Week Demand View", showlegend=False)
    fig.update_xaxes(title_text="checkpoint (analog prior → early evidence → closure)")
    fig.update_yaxes(title_text="13-week demand (units)")
    return theme.apply_theme(fig, height=340, legend=False)


# ------------------------------------------------------------------ S6
def fva_wape_bar(fva: pd.DataFrame):
    """WAPE by pre-launch version (lower = more accurate on this seeded path)."""
    order = ["V0_ANALYTICAL_BASELINE", "V1_COMMERCIAL_PLAN",
             "V2_CONSENSUS_FORECAST", "V3_APPROVED_PLAN"]
    d = fva[fva["forecast_stage"].isin(order)].copy()
    d["forecast_stage"] = pd.Categorical(d["forecast_stage"], order, ordered=True)
    d = d.sort_values("forecast_stage")
    xs = [_VERSION_LABEL[s] for s in d["forecast_stage"]]
    ys = [float(v) for v in d["WAPE"]]
    colors = [_VERSION_COLORS[s] for s in d["forecast_stage"]]
    fig = go.Figure(go.Bar(
        x=xs, y=ys, marker_color=colors,
        text=[f"{v:.2f}%" for v in ys], textposition="outside", cliponaxis=False,
        hovertemplate="%{x}<br>WAPE: %{y:.2f}%<extra></extra>"))
    fig.update_layout(title="Forecast Value Add — WAPE by Version", showlegend=False)
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="WAPE % (lower = more accurate)",
                     range=[0, max(ys) * 1.25])
    return theme.apply_theme(fig, height=340, legend=False)


def checkpoint_fva_bar(fva: pd.DataFrame):
    """Forward FVA (pp) at each reforecast checkpoint; W13 not measurable."""
    order = ["W1_REFORECAST", "W2_REFORECAST", "W4_REFORECAST", "W8_REFORECAST"]
    lab = {"W1_REFORECAST": "W1", "W2_REFORECAST": "W2",
           "W4_REFORECAST": "W4", "W8_REFORECAST": "W8"}
    d = fva[fva["forecast_stage"].isin(order)].copy()
    d["forecast_stage"] = pd.Categorical(d["forecast_stage"], order, ordered=True)
    d = d.sort_values("forecast_stage")
    xs = [lab[s] for s in d["forecast_stage"]]
    ys = [float(v) for v in d["FVA_WAPE_pp"]]
    fig = go.Figure(go.Bar(
        x=xs, y=ys, marker_color=SECONDARY,
        text=[f"+{v:.2f} pp" for v in ys], textposition="outside", cliponaxis=False,
        hovertemplate="%{x} reforecast<br>Forward FVA: +%{y:.2f} pp<extra></extra>"))
    fig.update_layout(title="Checkpoint Reforecast FVA (future-horizon only)",
                      showlegend=False)
    fig.update_xaxes(title_text="reforecast checkpoint · W13 = not measurable")
    fig.update_yaxes(title_text="FVA (pp, positive = improved)",
                     range=[0, max(ys) * 1.25])
    return theme.apply_theme(fig, height=320, legend=False)


def rolling_overlap(cycle02: pd.DataFrame, channel: str):
    """Cycle-01 V3 vs Cycle-02 over the 17 like-for-like months (Oct 2026 → Feb 2028)."""
    d = cycle02[cycle02["forecast_version"] == "CYCLE_02_ANALYTICAL_UPDATE"].copy()
    d["previous_cycle_units"] = pd.to_numeric(d["previous_cycle_units"], errors="coerce")
    d["cycle02_units"] = pd.to_numeric(d["cycle02_units"], errors="coerce")
    d = d.dropna(subset=["previous_cycle_units"])
    if channel and channel != "ALL":
        d = d[d["channel_id"] == channel]
    g = (d.groupby("planning_month", as_index=False)
           .agg(prev=("previous_cycle_units", "sum"), new=("cycle02_units", "sum"))
           .sort_values("planning_month"))
    scope = channel if channel not in (None, "ALL") else "All channels"
    fig = go.Figure()
    fig.add_trace(go.Bar(x=g["planning_month"], y=g["prev"], name="Cycle 01 · V3 approved",
                         marker_color=theme.NEUTRAL,
                         hovertemplate="%{x}<br>Cycle 01: %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(x=g["planning_month"], y=g["new"], name="Cycle 02 · updated",
                         marker_color=BASE,
                         hovertemplate="%{x}<br>Cycle 02: %{y:,.0f}<extra></extra>"))
    fig.update_layout(title=f"Cycle 01 → Cycle 02 · like-for-like Oct 2026–Feb 2028 · {scope}",
                      barmode="group")
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="units / month")
    return theme.apply_theme(fig, height=380)
