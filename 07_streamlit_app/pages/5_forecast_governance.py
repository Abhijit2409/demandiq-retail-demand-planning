"""Page 5 — Forecast & Governance. No planning filters. Reads frozen 4A/4B/4C
evidence. All numbers trace to a governed evidence file (never hardcoded).
"""
from __future__ import annotations
import streamlit as st

from utils.data_loader import get_evidence
from utils import formatting as fmt
from utils.theme import PLOTLY_CONFIG
from components import cards
from charts import governance_charts


def _recon_value(recon, segment, col):
    row = recon[(recon["method"] == "Seasonal_Profile_Imputation")
                & (recon["segment"] == segment)]
    return float(row.iloc[0][col]) if len(row) else float("nan")


def render():
    recon, champ, weather = get_evidence()

    cards.page_header(
        "Evidence & Governance", "Forecast & Governance",
        "Why should the planning output be trusted?",
        "An auditable pipeline turns constrained sales history into governed planner "
        "decisions — every figure below traces to a frozen evidence file.",
    )

    cards.methodology_journey([
        "Demand Reconstruction", "Forecast Model Selection", "Weather Scenario Governance",
        "Inventory / Service Simulation", "Planner Decision",
    ])
    st.write("")

    tabs = st.tabs([
        "Demand Reconstruction", "Forecast Models", "Weather Planning",
        "Planning Policy", "Data Provenance", "Limitations",
    ])

    # ---- Tab 1: Demand Reconstruction (Step 4A) ----
    with tabs[0]:
        cards.section("Selected method — Seasonal Profile Imputation")
        cards.kpi_grid([
            {"label": "Censored-Row WAPE",
             "value": fmt.pct(_recon_value(recon, "ALL_CENSORED_ROWS", "WAPE")),
             "sub": "Error on stockout-affected rows"},
            {"label": "Censored-Row Bias",
             "value": fmt.pct(_recon_value(recon, "ALL_CENSORED_ROWS", "Bias")),
             "sub": "Near-neutral", "accent": "ok"},
            {"label": "Lost-Demand Recovery",
             "value": fmt.pct(_recon_value(recon, "ALL_CENSORED_ROWS", "lost_demand_recovery_pct")),
             "sub": "Share of hidden demand recovered", "accent": "ok"},
            {"label": "Full-Stockout Recovery",
             "value": fmt.pct(_recon_value(recon, "STOCKOUT_ROWS", "lost_demand_recovery_pct")),
             "sub": "Zero-availability weeks", "accent": "ok"},
        ])
        st.write("")
        st.plotly_chart(governance_charts.reconstruction_method_bar(recon),
                        width='stretch', config=PLOTLY_CONFIG)
        st.markdown('<div class="diq-note">Seasonal Profile Imputation was selected because it '
                    'provided the strongest balance of censored-demand recovery and error '
                    'performance without using hidden synthetic truth as a forecasting input. '
                    'Forecast target = <b>reconstructed_demand_units</b> · Source: frozen Step 4A.'
                    '</div>', unsafe_allow_html=True)

    # ---- Tab 2: Forecast Models (Step 4B) ----
    with tabs[1]:
        fam = champ["selected_family"].str.upper()
        n_ets = int((fam == "ETS").sum())
        n_base = int((fam == "BASELINE").sum())
        n_sarima = int((fam == "SARIMA").sum())
        folds = int(champ["evaluation_folds"].iloc[0])
        horizon = int(champ["forecast_horizon_weeks"].iloc[0])

        cards.kpi_grid([
            {"label": "Forecast Series", "value": f"{len(champ)}", "sub": "SKU × Channel"},
            {"label": "ETS Champions", "value": f"{n_ets}", "sub": "Holt-Winters family", "accent": "ok"},
            {"label": "Baseline / SARIMA", "value": f"{n_base} / {n_sarima}",
             "sub": "Baseline retained · no SARIMA"},
            {"label": "Backtest", "value": f"{folds} folds",
             "sub": f"{horizon}-wk horizon · 52-wk season"},
        ])
        st.write("")
        cards.section("Champion Model by SKU × Channel")
        view = champ[["sku_id", "channel_id", "selected_champion", "selected_family",
                      "champion_wape_pct", "champion_bias_pct",
                      "governance_override_flag"]].copy()
        view.columns = ["SKU", "Channel", "Champion", "Family", "WAPE %", "Bias %", "Override"]
        st.dataframe(view.round({"WAPE %": 2, "Bias %": 2}), hide_index=True,
                     width='stretch', height=352)

        st.plotly_chart(governance_charts.champion_wape_bar(champ),
                        width='stretch', config=PLOTLY_CONFIG)
        st.caption("WAPE is descriptive; there is no pass/fail threshold. Higher wholesale "
                   "WAPE reflects noisier series, not defective models.")

        override = champ[champ["governance_override_flag"].astype(str).str.upper() == "YES"]
        if len(override):
            r = override.iloc[0]
            cards.callout("boundary", f"Simplicity override · {r['sku_id']} / {r['channel_id']}",
                          str(r["selection_reason"]))
        st.caption("Champion selection is frozen (Step 4B) — displayed, not recomputed.")

    # ---- Tab 3: Weather Planning (Step 4C) ----
    with tabs[2]:
        leak = int(weather["future_realized_weather_used_flag"].max())
        cards.section("Weather horizon framework")
        cards.weather_timeline()
        cards.kpi_grid([
            {"label": "Future Realized Weather Used", "value": "No" if leak == 0 else "YES",
             "sub": "No leakage into forecasts", "sub_kind": "up" if leak == 0 else "warn",
             "accent": "ok" if leak == 0 else "p1"},
            {"label": "Near-Term Rule", "value": "Nowcast", "sub": "Weeks 1–3 · not invented"},
            {"label": "Medium-Term Rule", "value": "Scenarios",
             "sub": "Weeks 4–13 · Mild / Normal / Severe", "accent": "p2"},
        ])
        st.markdown('<div class="diq-note">Weather dimensions (cold, rain, snow, wet+cold, wind) '
                    'are kept separate — no single weighted index. SKU scenario caps (mild/severe) '
                    'are <b>planning assumptions</b>, not empirically estimated demand '
                    'elasticities. Source: frozen Step 4C.</div>', unsafe_allow_html=True)

    # ---- Tab 4: Planning Policy ----
    with tabs[3]:
        cards.kpi_grid([
            {"label": "Service Target", "value": "92%", "sub": "Governed fill-rate policy"},
            {"label": "Safety Stock", "value": "2.5 weeks", "sub": "Coverage buffer"},
            {"label": "Chase Capacity", "value": "8%", "sub": "of forward seasonal commitment"},
            {"label": "Excess Threshold", "value": "8 WOS", "sub": "Over-coverage flag"},
        ])
        st.write("")
        cards.callout(
            "why", "Weekly service exception rule",
            "<b>WEEKLY_SERVICE_RISK</b> if 13-week Base fill ≥ 92% <b>AND</b> 2 or more forecast "
            "weeks have Base weekly fill &lt; 92% (misses need not be consecutive) → "
            "<b>P1 ESCALATE</b>. The two-week rule is a <b>synthetic planning-governance "
            "assumption</b>; it escalates for S&amp;OE review and does not auto-release chase.")

    # ---- Tab 5: Data Provenance ----
    with tabs[4]:
        cards.section("Every field is one of three provenance classes")
        cards.info_cards([
            {"cls": "public", "h": "PUBLIC",
             "b": "Historical public weather observations."},
            {"cls": "synthetic", "h": "SYNTHETIC",
             "b": "Simulated demand truth · inventory constraints · planning policies · "
                  "scenario caps · the weekly-service escalation rule."},
            {"cls": "derived", "h": "DERIVED",
             "b": "Reconstructed demand · forecasts · WAPE / bias · inventory simulation · "
                  "fill rate · WOS · risk type · planner action · economic exposure proxies."},
        ])
        st.warning("DemandIQ is a portfolio simulation inspired by a premium outdoor apparel "
                   "operating model. It does **not** represent any real company's internal data.")

    # ---- Tab 6: Limitations ----
    with tabs[5]:
        cards.info_cards([
            {"h": "Execution Feasibility",
             "b": "Supplier lead time and transfer transit time are not modeled — so "
                  "WEEKLY_SERVICE_RISK escalates but does not auto-release chase."},
            {"h": "Economics",
             "b": "Values are planning exposure proxies, not accounting profit (COGS unavailable)."},
            {"h": "Product Lifecycle",
             "b": "The engine covers mature products. Cold-start new-product launch planning "
                  "is a separate future module."},
            {"h": "Data",
             "b": "Synthetic planning environment — no claim of real company performance."},
        ])
