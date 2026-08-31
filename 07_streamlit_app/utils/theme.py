"""DemandIQ visual identity + Plotly theming.

Premium, minimal, outdoor-inspired. Consistent risk semantics:
    P1 / ESCALATE  -> clay (urgent attention)
    P2 / PROTECT   -> slate (preserve / watch)
    healthy/neutral -> moss / grey (NOT alarming)
"""
from __future__ import annotations

# Core palette
INK = "#1F2A30"
SUBTLE = "#5B6B73"
STONE = "#F5F3EF"
LINE = "#E4E0D8"
LINE_2 = "#EDEAE3"

P1 = "#C0603A"        # clay — urgent (WEEKLY_SERVICE_RISK / ESCALATE)
P2 = "#3F6C8E"        # slate — protect (LOW_COVERAGE_RISK / PROTECT)
HEALTHY = "#4F7A5B"   # moss — healthy aggregate
NEUTRAL = "#9AA7AE"   # grey — neutral metric

BASE_LINE = "#243B53"                 # deep slate — Base forecast line
BAND_FILL = "rgba(192,96,58,0.12)"    # light clay — scenario band

# Categorical hues for SKU / Channel breakdowns (non-alarming)
CATEGORICAL = ["#3F6C8E", "#4F7A5B", "#B08A3E"]

# Risk / tier semantic maps
RISK_COLORS = {
    "WEEKLY_SERVICE_RISK": P1,
    "LOW_COVERAGE_RISK": P2,
    "BASE_SERVICE_RISK": "#8C3B1E",
    "SEVERE_SCENARIO_RISK": "#B08A3E",
    "EXCESS_INVENTORY_RISK": NEUTRAL,
    "BALANCED": HEALTHY,
}
TIER_COLORS = {"P1": P1, "P2": P2, "P3": NEUTRAL, "P4": HEALTHY}

# Heatmap colorscale: warm (low fill) -> pale -> cool (healthy fill).
# Colorblind-safe warm/cool split; below-target cells also carry text.
FILL_COLORSCALE = [
    [0.00, "#8C3B1E"],   # deep clay — severe miss
    [0.55, "#C0603A"],   # clay
    [0.85, "#E5D4C1"],   # pale sand (just below target)
    [0.92, "#DCE6EC"],   # pale cool (target boundary)
    [0.97, "#9DBBC9"],   # cool slate
    [1.00, "#3F6C8E"],   # slate — healthy
]


# Shared st.plotly_chart config: clean, no modebar, responsive.
PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}


def apply_theme(fig, *, height: int = 420, legend: bool = True, ygrid: bool = True):
    """Apply the DemandIQ look to a Plotly figure. Pure; returns the figure.

    Larger, readable type; generous margins; clean gridlines.
    """
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=12, r=20, t=64, b=16),
        font=dict(family="Inter, Segoe UI, sans-serif", size=15, color=INK),
        title=dict(font=dict(size=20, color=INK), x=0, xanchor="left", y=0.97),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=CATEGORICAL,
        hoverlabel=dict(bgcolor="white", font_size=14, bordercolor=LINE),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(size=13)),
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=LINE, ticks="outside",
                     tickcolor=LINE, color=SUBTLE, tickfont=dict(size=13),
                     title_font=dict(size=14))
    fig.update_yaxes(showgrid=ygrid, gridcolor=LINE_2, zeroline=False, color=SUBTLE,
                     tickfont=dict(size=13), title_font=dict(size=14))
    return fig
