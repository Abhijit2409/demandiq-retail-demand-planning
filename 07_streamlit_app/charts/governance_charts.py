"""Forecast governance visual (Page 5). Pure builder returning a Plotly figure."""
from __future__ import annotations
import plotly.graph_objects as go

from utils import theme
from utils.formatting import series_label


def champion_wape_bar(champion_df):
    """Descriptive backtest WAPE per champion series, colored by model family.

    WAPE is descriptive only — NO pass/fail threshold. Higher wholesale WAPE
    is not framed as a defect.
    """
    d = champion_df.copy()
    d["series"] = d.apply(lambda r: series_label(r["sku_id"], r["channel_id"]), axis=1)
    d = d.sort_values("champion_wape_pct")

    families = list(d["selected_family"].unique())
    fam_color = {fam: theme.CATEGORICAL[i % len(theme.CATEGORICAL)]
                 for i, fam in enumerate(families)}
    colors = [fam_color[f] for f in d["selected_family"]]

    fig = go.Figure(go.Bar(
        x=d["champion_wape_pct"], y=d["series"], orientation="h", marker_color=colors,
        text=d["champion_wape_pct"], texttemplate="%{text:.1f}%", textposition="outside",
        cliponaxis=False,
        customdata=d[["selected_champion", "selected_family", "champion_bias_pct"]].values,
        hovertemplate=("%{y}<br>%{customdata[0]} (%{customdata[1]})"
                       "<br>WAPE %{x:.2f}% · Bias %{customdata[2]:.2f}%<extra></extra>"),
    ))
    fig.update_traces(textfont=dict(size=14))
    fig.update_layout(title="Backtest WAPE by Champion (9 series)", showlegend=False)
    fig.update_xaxes(title_text="WAPE % (lower is better · descriptive)",
                     range=[0, float(d["champion_wape_pct"].max()) * 1.18])
    fig.update_yaxes(title_text="", autorange="reversed", tickfont=dict(size=14))
    return theme.apply_theme(fig, height=400, legend=False)


def reconstruction_method_bar(recon_df):
    """Censored-row WAPE by candidate reconstruction method (frozen Step 4A).

    Descriptive comparison of the three methods on ALL_CENSORED_ROWS; the
    selected method (Seasonal Profile Imputation) is emphasized.
    """
    d = recon_df[recon_df["segment"] == "ALL_CENSORED_ROWS"].copy()
    name_map = {
        "Naive_InStock_GrossUp": "Naive in-stock gross-up",
        "Regression_Imputation": "Regression imputation",
        "Seasonal_Profile_Imputation": "Seasonal profile imputation (selected)",
    }
    d["label"] = d["method"].map(name_map).fillna(d["method"])
    d["wape_pct"] = d["WAPE"] * 100
    d = d.sort_values("wape_pct", ascending=False)
    colors = [theme.P1 if m == "Seasonal_Profile_Imputation" else theme.NEUTRAL
              for m in d["method"]]

    fig = go.Figure(go.Bar(
        x=d["wape_pct"], y=d["label"], orientation="h", marker_color=colors,
        text=d["wape_pct"], texttemplate="%{text:.1f}%", textposition="outside",
        cliponaxis=False, textfont=dict(size=14),
        customdata=(d["Bias"] * 100).values,
        hovertemplate="%{y}<br>Censored WAPE %{x:.1f}% · Bias %{customdata:.1f}%<extra></extra>",
    ))
    fig.update_layout(title="Censored-Row WAPE by Reconstruction Method",
                      showlegend=False)
    fig.update_xaxes(title_text="WAPE % on censored rows (lower is better)",
                     range=[0, float(d["wape_pct"].max()) * 1.25])
    fig.update_yaxes(title_text="", tickfont=dict(size=14))
    return theme.apply_theme(fig, height=320, legend=False)
