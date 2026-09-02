"""Page 6 — New Product Launch Planning (HIS-001). Step 7G.

Tells the cold-start planner decision story from FROZEN Step 7B–7F outputs only:
plan → forecast with no history → V0→V3 → buy → launch → reforecast → learning →
rolling forecast → lifecycle handoff. No forecasting/optimization here — only
presentation transformations (filter / sum / groupby / ratio / reshape).

Channel-filter contract:
  - IF the underlying frozen data has a channel dimension, the KPI/chart RESPONDS
    to the Channel selector (V3 demand, allocated buy, fill, observed/lost,
    cold-start & version charts, weekly plan-vs-observed, rolling forecast,
    channel-learning).
  - IF the concept is inherently SKU-level / global, it stays global and is
    clearly marked (launch date, lifecycle status, mature eligibility, analog
    scorecard, reforecast, checkpoint table, FVA, policy sensitivity, lifecycle).
"""
from __future__ import annotations
import pandas as pd
import streamlit as st

from utils import launch_data as ld
from utils import formatting as fmt
from utils.theme import PLOTLY_CONFIG
from components import cards
from charts import launch_charts as lc

CHANNEL_OPTIONS = ["ALL", "ECOM", "RETAIL", "WHOLESALE"]


def _channel_control() -> str:
    try:
        ch = st.segmented_control("Channel", CHANNEL_OPTIONS, default="ALL",
                                  key="p6_channel")
    except Exception:  # fallback for older Streamlit
        ch = st.radio("Channel", CHANNEL_OPTIONS, horizontal=True, key="p6_channel_radio")
    return ch or "ALL"


def _pct1(x) -> str:
    return f"{x * 100:.1f}%" if pd.notna(x) else "—"


def _scope(responsive: bool, channel: str = "ALL"):
    """Reusable scope marker so a global metric never looks like a broken filter."""
    if responsive:
        lab = "ALL CHANNELS" if channel == "ALL" else channel
        txt, color, bg, bd = f"CHANNEL VIEW · {lab}", "#3F6C8E", "#eef2f5", "#d5e0e8"
    else:
        txt, color, bg, bd = "SKU-LEVEL · NOT CHANNEL-FILTERED", "#8A969C", "#f4f2ee", "#e4e0d8"
    st.markdown(
        f'<div style="margin:-4px 0 8px;"><span style="font-size:10.5px;font-weight:700;'
        f'letter-spacing:.06em;color:{color};background:{bg};border:1px solid {bd};'
        f'border-radius:20px;padding:2px 10px;">{txt}</span></div>',
        unsafe_allow_html=True)


def render():
    d = ld.get_launch_data()
    buy = d["buy"]
    handoff = d["handoff"]
    weekly = d["weekly"]

    cards.page_header(
        "New Product Launch Planning · Step 7",
        "HIS-001 · Hybrid Insulated Shell",
        "How do you plan a premium product that has no sales history?",
        "Cold-start demand planning → consensus → initial buy → launch learning → "
        "rolling forecast → lifecycle handoff. Every figure traces to a frozen "
        "Step 7B–7F output.",
    )
    channel = _channel_control()
    is_all = (channel == "ALL")
    pfx = "" if is_all else f"{channel} · "
    st.caption("The Channel selector updates every metric and chart that has channel-level "
               "frozen data. Global / SKU-level evidence is marked and stays constant.")

    # ============================ SECTION 1 — COMMAND CENTER ============================
    cards.section("1 · Launch Command Center", "HIS-001 at a glance")
    _scope(True, channel)
    v3 = ld.v3_13w_demand(weekly, channel)
    fill = ld.launch_fill_rate(weekly, channel)
    rev = ld.cycle02_overlap_revision(d["cycle02"], channel)
    buy_val = ld.allocated_buy(buy, channel)
    buy_label = "Frozen Initial Buy" if is_all else f"{channel} · Allocated Buy"
    launch_date = str(d["assumptions"].get("launch_date", "2026-08-31"))
    cards.kpi_grid([
        {"label": "Launch Date", "value": fmt.date_long(launch_date), "sub": "Global"},
        {"label": "Lifecycle Status", "value": str(handoff["current_lifecycle_status"]),
         "sub": f"Global · {int(handoff['observed_weeks'])} weeks", "accent": "p2"},
        {"label": f"{pfx}V3 Approved 13-Wk Demand", "value": fmt.units(v3),
         "sub": "unconstrained demand" if is_all else f"{channel} channel demand"},
        {"label": buy_label, "value": fmt.units(buy_val),
         "sub": "BALANCED supply setup" if is_all else "channel pre-allocation"},
        {"label": "Flex Reserve", "value": fmt.units(buy["reserve_units"]),
         "sub": "Global pool — not preallocated", "accent": "p2"},
        {"label": f"{pfx}Launch Fill Rate", "value": _pct1(fill),
         "sub": "observed sell-through", "accent": "ok"},
        {"label": f"{pfx}Cycle-02 Direction", "value": _pct1(rev["revision_pct"]),
         "sub": "like-for-like revision", "sub_kind": "warn"},
        {"label": "Mature-Model Eligible?",
         "value": "No" if "NO" in str(handoff["mature_104w_eligible_flag"]).upper() else "Yes",
         "sub": "Global lifecycle"},
    ])
    st.write("")

    # ============================ SECTION 2 — COLD START → CONSENSUS ============================
    cards.section("2 · Cold Start → Consensus",
                  "How do you forecast a product with no history?")
    a = d["assumptions"]
    _scope(False)
    st.plotly_chart(lc.analog_scorecard(d["scorecard"]), width="stretch", config=PLOTLY_CONFIG)
    cards.callout(
        "why", "Final governed analog blend — 60% APS-001 + 40% IMH-001",
        f"<b>{a.get('selected_primary_analog', 'APS-001')}</b> is the primary analog "
        f"(top score, stable across sensitivity); <b>{a.get('selected_secondary_analog', 'IMH-001')}</b> "
        "uniquely supplies the insulation attribute APS lacks (FW-shape correlation 0.99). "
        f"<b>{a.get('excluded_candidate', 'CTS-001')}</b> ranked #2 by score but is a redundant "
        "shell that fills no gap, so it was excluded from the final blend.")
    st.write("")
    _scope(True, channel)
    st.plotly_chart(lc.v0_baseline_18m(d["v0_18m"], channel), width="stretch", config=PLOTLY_CONFIG)
    st.plotly_chart(lc.version_evolution(d["versions"], channel), width="stretch", config=PLOTLY_CONFIG)
    cards.callout(
        "why", "V0 → V1 → V2 → V3",
        "The commercial plan (V1) lifted the analytical baseline; consensus governance (V2) "
        "moderated the commercial uplift; V3 became the <b>approved unconstrained-demand</b> "
        "position. V3 is demand — it is <b>not</b> supply-constrained.")
    st.write("")

    # ============================ SECTION 3 — INITIAL BUY & ALLOCATION ============================
    cards.section("3 · Initial Buy & Channel Allocation",
                  "How did approved demand become an inventory commitment?")
    c1, c2 = st.columns(2)
    with c1:
        _scope(False)
        st.plotly_chart(lc.buy_bridge(buy), width="stretch", config=PLOTLY_CONFIG)
        st.caption("SKU-level buy decision — not channel-filtered.")
    with c2:
        _scope(True, channel)
        st.plotly_chart(lc.allocation_bar(buy, channel), width="stretch", config=PLOTLY_CONFIG)
    cards.callout(
        "boundary", "Launch uncertainty buffer — not mature safety stock",
        f"The <b>{_pct1(float(buy['buffer_pct']))}</b> buffer "
        f"(≈ {fmt.units(buy['buffer_units'])}) is a <b>launch uncertainty buffer</b>, a "
        "one-time cold-start allowance. It is <b>not</b> the mature 2.5-week safety-stock rule.")
    cards.info_cards([
        {"cls": "synthetic", "h": "Supply setup · BALANCED",
         "b": "Data-derived (frozen Step 7E buy): launch buffer "
              f"<b>{_pct1(float(buy['buffer_pct']))}</b> · flex reserve "
              f"<b>{fmt.units(buy['reserve_units'])}</b> · reserve/transfer lead "
              f"<b>~{int(d['policy']['reserve_transfer_lead_weeks'].iloc[0])} weeks</b>."},
        {"cls": "synthetic", "h": "SYNTHETIC SUPPLY PLANNING ASSUMPTIONS",
         "b": f"Display context from the {ld.STEP7E_SUPPLY_CONTEXT['source']} "
              "(not a CSV column): effective replenishment lead "
              f"<b>{ld.STEP7E_SUPPLY_CONTEXT['effective_replenishment_lead']}</b> · chase capacity "
              f"<b>{ld.STEP7E_SUPPLY_CONTEXT['chase_capacity']}</b>. Context only — "
              "not used in any Page-6 calculation."},
    ])
    st.write("")

    # ============================ SECTION 4 — LAUNCH EXECUTION & REFORECAST ============================
    cards.section("4 · Launch Execution & Reforecast",
                  "What happened after launch, and how did the demand view change?")
    show_latent = st.checkbox("Show evaluation-only latent synthetic demand",
                              value=False, key="p6_show_latent")
    latent = None
    if show_latent:
        latent = ld.load_launch_latent_eval_only()  # filtered to channel inside the chart builder
        st.warning("**Evaluation only** — this latent synthetic demand was not available "
                   "to the operational planner at launch time and was never used by the "
                   "reforecast or planning decisions.")
    _scope(True, channel)
    st.plotly_chart(lc.plan_vs_observed(weekly, channel, latent), width="stretch", config=PLOTLY_CONFIG)
    _scope(False)
    st.plotly_chart(lc.reforecast_waterfall(d["checkpoints"]), width="stretch", config=PLOTLY_CONFIG)

    dec = d["decisions"].copy()
    tbl = dec[["checkpoint", "attainment_pct", "reforecast_total_units",
               "exception_status", "planner_action"]].copy()
    tbl.columns = ["Checkpoint", "Attainment %", "Reforecast (units)", "Exception", "Planner Action"]
    tbl["Reforecast (units)"] = tbl["Reforecast (units)"].round(0)
    st.dataframe(tbl.round({"Attainment %": 1}), hide_index=True, width="stretch")
    st.caption("SKU-level reforecast & decisions — the frozen Step 7E checkpoint file has no "
               "channel dimension, so it stays global. Planner action was HOLD throughout.")
    st.write("")

    # ============================ SECTION 5 — CHANNEL / INVENTORY LEARNING ============================
    reserve_v = fmt.units(buy["reserve_units"])
    if is_all or channel == "ECOM":
        cards.section("5 · Channel / Inventory Learning",
                      "Total supply was sufficient, yet ECOM still stocked out")
        _scope(True, "ALL" if is_all else "ECOM")
        ecom_mix = ld.observed_mix_share(weekly, "ECOM")
        ecom_dev = float(d["decisions"]["max_channel_mix_dev_pp"].max())
        ecom_lost = ld.lost_total(weekly, "ECOM")
        cards.kpi_grid([
            {"label": "ECOM Observed Mix", "value": _pct1(ecom_mix), "sub": "vs 45% planned"},
            {"label": "ECOM Mix Deviation", "value": f"+{ecom_dev:.1f} pp",
             "sub": "peak vs plan", "sub_kind": "warn"},
            {"label": "ECOM Lost Demand", "value": fmt.units(ecom_lost),
             "sub": "W13 stockout", "accent": "p1"},
            {"label": "Idle Flex Reserve", "value": reserve_v, "sub": "Global · never deployed"},
        ])
        cards.callout(
            "why", "A channel-allocation / policy-threshold issue — not a total-supply shortage",
            "ECOM ran hotter than its planned mix while reserve and other-channel inventory "
            "remained available. The historical REALLOCATE trigger (8pp) was never reached, so "
            "the reserve stayed idle and ECOM stocked out in W13. Causality is not claimed.")
    else:
        cards.section(f"5 · Channel / Inventory Learning · {channel}",
                      f"{channel} channel view — observed sell-through & availability")
        _scope(True, channel)
        ch_mix = ld.observed_mix_share(weekly, channel)
        ch_dev = ch_mix * 100 - ld.PLANNED_MIX[channel] * 100
        ch_lost = ld.lost_total(weekly, channel)
        cards.kpi_grid([
            {"label": f"{channel} Observed Mix", "value": _pct1(ch_mix),
             "sub": f"vs {int(ld.PLANNED_MIX[channel]*100)}% planned"},
            {"label": f"{channel} vs Planned", "value": f"{ch_dev:+.1f} pp",
             "sub": "cumulative observed"},
            {"label": f"{channel} Lost Demand", "value": fmt.units(ch_lost),
             "sub": "no stockout" if ch_lost == 0 else "stockout-censored",
             "accent": "ok" if ch_lost == 0 else "p1"},
            {"label": "Idle Flex Reserve", "value": reserve_v, "sub": "Global · never deployed"},
        ])
        cards.callout(
            "why", f"No stockout occurred in {channel}",
            f"{channel} served its observed demand in full on the frozen realized path. The "
            "launch's allocation risk was concentrated in <b>ECOM</b> (which stocked out in W13), "
            "while the flex reserve stayed centrally held. Select ECOM to see that learning.")

    # Policy sensitivity — ECOM-specific counterfactual governance evidence (global to the page)
    st.markdown('<div class="diq-section-sub">COUNTERFACTUAL POLICY SENSITIVITY</div>',
                unsafe_allow_html=True)
    _scope(False)
    pol = d["policy"][["threshold_pp", "would_trigger", "first_trigger_week",
                       "mix_dev_at_trigger_pp", "reserve_available_units",
                       "indicative_deployable_units", "plausibly_arrives_before_w13_stockout"]].copy()
    pol.columns = ["Threshold (pp)", "Would Trigger?", "First Trigger Week",
                   "Mix Dev @ Trigger", "Reserve Avail.", "Indicative Deployable", "Arrives Before W13?"]
    st.dataframe(pol, hide_index=True, width="stretch")
    st.caption("ECOM-specific counterfactual policy evidence — a frozen governance exercise, "
               "not affected by the selected channel. No threshold is optimal/best/recommended; "
               "the historical 8pp Step 7E rule remains frozen.")
    st.write("")

    # ============================ SECTION 6 — FVA + ROLLING + LIFECYCLE ============================
    cards.section("6 · FVA + Rolling Forecast + Lifecycle Handoff",
                  "Did the forecast add value, how did the plan roll, and is HIS-001 mature?")
    _scope(False)
    st.plotly_chart(lc.fva_wape_bar(d["fva"]), width="stretch", config=PLOTLY_CONFIG)
    cards.callout(
        "boundary", "Illustrative governance demonstration — read with care",
        "The Step 7E synthetic launch generator was centered on the V0 analytical baseline. "
        "Therefore this FVA comparison is an <b>illustrative governance demonstration</b> and "
        "<b>not independent empirical evidence that commercial input was harmful</b>.")
    st.plotly_chart(lc.checkpoint_fva_bar(d["fva"]), width="stretch", config=PLOTLY_CONFIG)
    st.caption("SKU-level forecast-accuracy evaluation — the frozen Step 7F FVA has no "
               "channel-level scores, so it stays global. Later reforecasts improved the "
               "still-future horizon; W13 is not measurable.")
    st.write("")

    # Rolling forecast — channel-responsive
    _scope(True, channel)
    st.plotly_chart(lc.rolling_overlap(d["cycle02"], channel), width="stretch", config=PLOTLY_CONFIG)
    mardf = d["cycle02"][d["cycle02"]["planning_month"] == "2028-03"]
    mar_val = pd.to_numeric(ld.filter_channel(mardf, channel)["cycle02_units"], errors="coerce").sum()
    cards.kpi_grid([
        {"label": "Cycle 01 Window", "value": "Sep 2026 → Feb 2028", "sub": "Global"},
        {"label": "Cycle 02 Window", "value": "Oct 2026 → Mar 2028",
         "sub": "as-of 2026-09-28", "accent": "p2"},
        {"label": f"{pfx}Like-for-Like Revision", "value": _pct1(rev["revision_pct"]),
         "sub": f"{rev['n_months']} overlapping months", "sub_kind": "warn"},
        {"label": f"{pfx}New Month · Mar 2028", "value": fmt.units(mar_val),
         "sub": "governed seasonal extension"},
    ])
    st.caption("Full-window totals cover different windows (Sep drops, Mar enters) — that is a "
               "ROLLING-WINDOW OUTLOOK CHANGE, not pure forecast revision. Revision % is "
               "mix-preserving, so it matches across channels but is recomputed per channel.")
    st.write("")

    # Lifecycle handoff — global
    cards.section("Lifecycle handoff", "When does HIS-001 become mature-engine eligible?")
    _scope(False)
    stages = [
        {"label": "COLD_START", "value": "0 wks"},
        {"label": "EARLY_LAUNCH", "value": "1–13 wks", "sub": "HIS-001 IS HERE",
         "sub_kind": "warn", "accent": "p1"},
        {"label": "MATURING_LAUNCH", "value": "14–51 wks"},
        {"label": "SEASONAL_HISTORY", "value": "≥52 wks", "sub": "own-season diagnostics"},
        {"label": "MATURE_MODEL_ELIGIBLE", "value": "≥104 wks", "sub": "+ data-quality gates"},
    ]
    cards.kpi_grid(stages)
    cards.info_cards([
        {"cls": "derived", "h": "Current status",
         "b": f"<b>{handoff['current_lifecycle_status']}</b> · "
              f"{int(handoff['observed_weeks'])} observed weeks · "
              f"own-season history: <b>{handoff['one_season_history_flag']}</b> · "
              f"mature-model eligible: <b>{handoff['mature_104w_eligible_flag']}</b>."},
        {"cls": "synthetic", "h": "Recommended method",
         "b": f"{handoff['recommended_forecast_method']}. No ETS/SARIMA is fitted to "
              "HIS-001 — it is not yet mature-engine eligible."},
    ])
