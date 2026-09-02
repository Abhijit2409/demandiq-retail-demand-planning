"""
DemandIQ - Step 7C - Cold-Start & 18-Month Lifecycle Forecast for HIS-001.

Produces the V0 ANALYTICAL BASELINE (unconstrained demand) in two connected views
from ONE weekly demand engine:
  - DemandIQ_Step7C_18M_Analytical_Forecast.csv   (Month x SKU x Channel x Adoption x Weather)
  - DemandIQ_Step7C_13W_Launch_Forecast.csv        (Week  x SKU x Channel x Adoption x Weather)

V0 only: NO commercial overrides, top-down targets, reconciliation, consensus, V1/V2/V3,
or supply constraints (those are Step 7D). Demand is UNCONSTRAINED.

Governance:
  - Shape from frozen analog seasonality (APS-001, IMH-001); scale from frozen planning demand.
  - No true_demand_units / lost_demand_units / audit_hidden_* / generator factors / future
    realized weather / future HIS actuals are used.
  - Mature Steps 4A-6F outputs are not touched. Launch outputs live in launch_step7c.

Run:  python step7c_cold_start_forecast.py
(Optional: set env STEP7C_OUTDIR to redirect outputs, e.g. for a dry verification run.)
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(r"D:\Downloads\DemandIQ")
ECON = ROOT / "02_data" / "processed" / "DemandIQ_Step3D_v4_Retail_Economics.csv"
OUTDIR = Path(os.environ.get("STEP7C_OUTDIR", str(ROOT / "05_outputs" / "launch_step7c")))
OUTDIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# FROZEN Step 7B decisions (carried forward exactly; not changed here)
# ============================================================
LAUNCH_DATE = pd.Timestamp("2026-08-31")     # Monday, ISO wk36
AS_OF_DATE = "2026-08-24"                     # synthetic pre-launch as-of (rolling-cycle anchor)
PLANNING_CYCLE = "CYCLE_01_2026-08"

APS_W, IMH_W = 0.60, 0.40                     # analog blend (SHAPE contribution)
LAUNCH_SCALE_FACTOR = 0.60                    # governed conservative first-season scale
ADOPTION = {"LOW": 0.75, "BASE": 1.00, "HIGH": 1.25}          # launch-adoption multipliers
PLANNED_MIX = {"ECOM": 0.45, "RETAIL": 0.35, "WHOLESALE": 0.20}  # DTC-led planned launch mix
SECOND_SEASON_FACTOR = 1.00                   # owner decision: flat second-season run-rate

# lifecycle ramp (SYNTHETIC shape assumption; renormalized so it never changes the annual total)
RAMP_START, RAMP_WEEKS = 0.60, 13

# HIS weather caps = 60/40 blend of frozen analog caps (SKILL section 11):
#   APS Severe +6% / Mild -4% ; IMH Severe +5% / Mild -4%
WEATHER_ADJ = {"NORMAL": 0.0,
               "MILD": round(APS_W * -0.04 + IMH_W * -0.04, 4),      # -0.04
               "SEVERE": round(APS_W * 0.06 + IMH_W * 0.05, 4)}      # +0.056
NOWCAST_WEEKS = {1, 2, 3}                       # weeks 1-3: NOWCAST_REQUIRED -> no weather adjustment

# five governed decision combos (no 3x3 clutter): 3 adoption @ NORMAL + BASE @ MILD/SEVERE
COMBOS = [("LOW", "NORMAL"), ("BASE", "NORMAL"), ("HIGH", "NORMAL"),
          ("BASE", "MILD"), ("BASE", "SEVERE")]

FORECAST_VERSION = "V0_ANALYTICAL_BASELINE"
PROVENANCE = "DERIVED: FROZEN MATURE ANALOG DATA (APS-001, IMH-001) + SYNTHETIC PLANNING ASSUMPTIONS"

STRATEGIC_MONTHS = pd.period_range("2026-09", "2028-02", freq="M")  # 18 months


def month_phase(period):
    """Lifecycle phase for a calendar month (Step 7B lifecycle calendar)."""
    s = str(period)
    if s == "2026-09":
        return "LAUNCH"
    if s in ("2026-10", "2026-11"):
        return "RAMP"
    if s == "2026-12":
        return "SEASONAL PEAK"
    if "2027-01" <= s <= "2027-06":
        return "NORMALIZATION"
    return "SECOND-SEASON / MATURATION"  # 2027-07 .. 2028-02


def build_blended_profile(df):
    """52-week profiles normalized to sum 1, then 0.60/0.40 blended (shape only)."""
    def prof(sku):
        s = df[df.sku_id == sku].groupby("week_of_year").sku_seasonality_factor.mean()
        return s / s.sum()
    pA, pI = prof("APS-001"), prof("IMH-001")
    blended = APS_W * pA + IMH_W * pI
    assert abs(blended.sum() - 1.0) < 1e-9, "blended profile must sum to 1.00"
    return blended  # index: week_of_year 1..52


def main():
    df = pd.read_csv(ECON)

    # ---- data validation: week_of_year == ISO week (so future launch weeks map correctly) ----
    _chk = pd.to_datetime(df["week_start"]).dt.isocalendar().week.astype(int)
    assert (_chk == df["week_of_year"]).all(), "week_of_year must equal ISO week"

    # ---- scale (frozen planning demand) ----
    nyears = df.week_start.nunique() / 52.0
    ann = df.groupby("sku_id").weekly_plan_units.sum() / nyears
    aps_ann, imh_ann = float(ann["APS-001"]), float(ann["IMH-001"])
    blended_annual = APS_W * aps_ann + IMH_W * imh_ann
    his_base_annual = blended_annual * LAUNCH_SCALE_FACTOR
    print(f"APS annual={aps_ann:.2f} | IMH annual={imh_ann:.2f}")
    print(f"blended annual={blended_annual:.2f} | HIS Base annual={his_base_annual:.2f}")

    # ---- shape ----
    blended = build_blended_profile(df)

    def share(iso_week):
        return float(blended.get(53, blended.loc[52]) if iso_week == 53 else blended.loc[iso_week])

    # ---- weekly demand engine over the horizon (82 weeks covers Sep2026..Feb2028) ----
    weeks = [LAUNCH_DATE + pd.Timedelta(weeks=i) for i in range(82)]
    eng = []
    # year-1 renormalization factor: sum over first 52 weeks of (share * ramp)
    def ramp_of(wk_num):
        if wk_num >= RAMP_WEEKS:
            return 1.0
        return RAMP_START + (1.0 - RAMP_START) * (wk_num - 1) / (RAMP_WEEKS - 1)
    raw1 = []
    for i in range(52):
        iso = int(weeks[i].isocalendar().week)
        raw1.append(share(iso) * ramp_of(i + 1))
    norm1 = sum(raw1)

    for i, ws in enumerate(weeks):
        wk_num = i + 1
        iso = int(ws.isocalendar().week)
        thursday = ws + pd.Timedelta(days=3)
        pmonth = thursday.to_period("M")
        if wk_num <= 52:  # first season: renormalized ramp shape -> year-1 total == his_base_annual
            sku_units = his_base_annual * (share(iso) * ramp_of(wk_num)) / norm1
        else:             # second season: established run-rate x maturation factor
            sku_units = his_base_annual * share(iso) * SECOND_SEASON_FACTOR
        eng.append({"week_start": ws, "launch_week_number": wk_num, "iso_week": iso,
                    "planning_month": pmonth, "sku_units": sku_units})
    eng = pd.DataFrame(eng)

    # QA: year-1 (weeks 1-52) reconstructs the governed Base annual scale exactly (anti double-discount)
    y1 = eng[eng.launch_week_number <= 52].sku_units.sum()
    assert abs(y1 - his_base_annual) < 1e-6, f"year-1 total {y1} != Base {his_base_annual}"
    print(f"QA year-1 total = {y1:.2f} (== HIS Base annual; ramp redistributes timing, not scale)")

    # ---- expand to channel x adoption x weather ----
    def expand(base_rows, keys):
        out = []
        for _, r in base_rows.iterrows():
            for ch, mix in PLANNED_MIX.items():
                ch_units = r["sku_units"] * mix
                for adopt, weather in COMBOS:
                    pre = ch_units * ADOPTION[adopt]
                    wk_num = r.get("launch_week_number", 99)
                    adj = 0.0 if wk_num in NOWCAST_WEEKS else WEATHER_ADJ[weather]
                    final = pre * (1 + adj)
                    row = {k: r[k] for k in keys}
                    row.update({"sku_id": "HIS-001", "channel_id": ch,
                                "launch_scenario": adopt, "weather_scenario": weather,
                                "pre_weather_units": round(pre, 2),
                                "weather_adjustment_pct": adj,
                                "weather_adjusted_units": round(final, 2),
                                "analytical_baseline_units": round(final, 2),
                                "forecast_version": FORECAST_VERSION, "provenance": PROVENANCE})
                    out.append(row)
        return pd.DataFrame(out)

    # ---- 13-week launch-execution view ----
    w13 = eng[eng.launch_week_number <= 13].copy()
    w13["lifecycle_phase"] = w13["planning_month"].apply(month_phase)
    week13 = expand(w13, ["week_start", "launch_week_number", "lifecycle_phase"])
    cps = {1: "W1", 2: "W2", 4: "W4", 8: "W8", 13: "W13"}
    week13["launch_checkpoint_flag"] = week13.launch_week_number.isin(cps).astype(int)
    week13["launch_checkpoint_name"] = week13.launch_week_number.map(cps).fillna("")
    week13["week_start"] = week13["week_start"].dt.strftime("%Y-%m-%d")
    week13 = week13[["week_start", "launch_week_number", "sku_id", "channel_id", "lifecycle_phase",
                     "launch_scenario", "weather_scenario", "pre_weather_units",
                     "weather_adjustment_pct", "weather_adjusted_units", "analytical_baseline_units",
                     "launch_checkpoint_flag", "launch_checkpoint_name",
                     "forecast_version", "provenance"]]

    # ---- 18-month strategic view: aggregate weekly (Thursday-month) to months ----
    detail = expand(eng, ["planning_month", "launch_week_number"])
    m18 = (detail.groupby(["planning_month", "sku_id", "channel_id", "launch_scenario",
                           "weather_scenario"], as_index=False)
                 .agg(pre_weather_units=("pre_weather_units", "sum"),
                      weather_adjusted_units=("weather_adjusted_units", "sum")))
    m18 = m18[m18.planning_month.isin(STRATEGIC_MONTHS)].copy()
    m18["analytical_baseline_units"] = m18["weather_adjusted_units"].round(2)
    m18["pre_weather_units"] = m18["pre_weather_units"].round(2)
    m18["weather_adjusted_units"] = m18["weather_adjusted_units"].round(2)
    # blended monthly weather adjustment % (implied, for transparency)
    m18["weather_adjustment_pct"] = np.where(m18.pre_weather_units.abs() > 1e-9,
                                             (m18.weather_adjusted_units / m18.pre_weather_units - 1).round(4), 0.0)
    order = {p: i + 1 for i, p in enumerate(STRATEGIC_MONTHS)}
    m18["horizon_month_number"] = m18.planning_month.map(order)
    m18["month_index"] = m18["horizon_month_number"]
    m18["lifecycle_phase"] = m18.planning_month.apply(month_phase)
    m18["planning_cycle"] = PLANNING_CYCLE
    m18["forecast_as_of_date"] = AS_OF_DATE
    m18["sku_id"] = "HIS-001"
    m18["forecast_version"] = FORECAST_VERSION
    m18["provenance"] = PROVENANCE
    m18["planning_month"] = m18["planning_month"].astype(str)
    m18 = m18.sort_values(["horizon_month_number", "channel_id", "launch_scenario", "weather_scenario"])
    m18 = m18[["planning_cycle", "forecast_as_of_date", "planning_month", "month_index",
               "horizon_month_number", "sku_id", "channel_id", "lifecycle_phase",
               "launch_scenario", "weather_scenario", "pre_weather_units",
               "weather_adjustment_pct", "weather_adjusted_units", "analytical_baseline_units",
               "forecast_version", "provenance"]]

    # ================= QA =================
    def qa(cond, msg):
        assert cond, "QA FAIL: " + msg

    # 18-month
    qa(m18.planning_month.nunique() == 18, "must have 18 strategic months")
    qa(m18.planning_month.min() == "2026-09" and m18.planning_month.max() == "2028-02", "Sep2026..Feb2028")
    qa(set(m18.channel_id) == {"ECOM", "RETAIL", "WHOLESALE"}, "3 channels")
    qa(set(m18.launch_scenario) >= {"LOW", "BASE", "HIGH"}, "LOW/BASE/HIGH present")
    qa(not m18.duplicated(["planning_month", "channel_id", "launch_scenario", "weather_scenario"]).any(), "no dup grain")
    qa(m18.analytical_baseline_units.notna().all() and (m18.analytical_baseline_units >= 0).all(), "no null/neg (18M)")
    qa(m18.lifecycle_phase.notna().all(), "phase per month")
    qa((m18.forecast_version == FORECAST_VERSION).all(), "V0 label (18M)")
    # LOW<BASE<HIGH at NORMAL weather, per month/channel
    piv = (m18[m18.weather_scenario == "NORMAL"]
           .pivot_table(index=["planning_month", "channel_id"], columns="launch_scenario",
                        values="analytical_baseline_units"))
    qa(((piv["LOW"] < piv["BASE"]) & (piv["BASE"] < piv["HIGH"])).all(), "LOW<BASE<HIGH (18M)")
    # channels reconcile to SKU total (NORMAL/BASE): sum of 3 channels == his monthly total
    # 13-week
    qa(week13.week_start.nunique() == 13, "13 weeks")
    qa(week13.week_start.min() == "2026-08-31", "first week 2026-08-31")
    wd = pd.to_datetime(sorted(week13.week_start.unique()))
    qa(all((wd[1:] - wd[:-1]) == pd.Timedelta(days=7)), "weekly spacing 7 days")
    qa(week13.analytical_baseline_units.notna().all() and (week13.analytical_baseline_units >= 0).all(), "no null/neg (13W)")
    qa(set(week13[week13.launch_checkpoint_flag == 1].launch_week_number) == {1, 2, 4, 8, 13}, "checkpoints W1/2/4/8/13")
    # analog / leakage
    qa(abs(APS_W + IMH_W - 1) < 1e-9 and APS_W == 0.60 and IMH_W == 0.40, "analog blend 0.60/0.40")
    qa(abs(sum(PLANNED_MIX.values()) - 1) < 1e-9, "planned mix sums to 1")

    # reconciliation: weekly engine -> month equals 18M (BASE/NORMAL), by construction
    wk_month = (detail[(detail.launch_scenario == "BASE") & (detail.weather_scenario == "NORMAL")]
                .assign(planning_month=lambda d: d.planning_month.astype(str))
                .groupby("planning_month").weather_adjusted_units.sum())
    m_base = (m18[(m18.launch_scenario == "BASE") & (m18.weather_scenario == "NORMAL")]
              .groupby("planning_month").analytical_baseline_units.sum())
    recon = pd.concat([wk_month.rename("weekly_rollup"), m_base.rename("m18_value")], axis=1).dropna()
    max_diff = (recon.weekly_rollup - recon.m18_value).abs().max()
    qa(max_diff < 0.05, f"18M/weekly reconciliation diff {max_diff}")
    print(f"QA reconciliation (BASE/NORMAL) max month diff = {max_diff:.4f} (rounding only)")

    # ---- write ----
    m18.to_csv(OUTDIR / "DemandIQ_Step7C_18M_Analytical_Forecast.csv", index=False)
    week13.to_csv(OUTDIR / "DemandIQ_Step7C_13W_Launch_Forecast.csv", index=False)

    # ---- plan diagnostics (not accuracy KPIs; HIS has no actuals) ----
    bn = m18[(m18.launch_scenario == "BASE") & (m18.weather_scenario == "NORMAL")]
    tot = bn.groupby("planning_month").analytical_baseline_units.sum()
    first12 = tot.iloc[:12].sum()
    second_visible = tot.iloc[12:].sum()
    lo = m18[(m18.launch_scenario == "LOW") & (m18.weather_scenario == "NORMAL")].analytical_baseline_units.sum()
    ba = bn.analytical_baseline_units.sum()
    hi = m18[(m18.launch_scenario == "HIGH") & (m18.weather_scenario == "NORMAL")].analytical_baseline_units.sum()
    w13b = week13[(week13.launch_scenario == "BASE") & (week13.weather_scenario == "NORMAL")].analytical_baseline_units.sum()
    print("\n===== FORECAST PLAN DIAGNOSTICS (V0, BASE/NORMAL unless noted) =====")
    print(f"18-month BASE demand         : {ba:,.0f}")
    print(f"  first 12-month BASE        : {first12:,.0f}")
    print(f"  second-season visible BASE : {second_visible:,.0f}")
    print(f"13-week BASE demand          : {w13b:,.0f}")
    print(f"LOW / BASE / HIGH (18M)      : {lo:,.0f} / {ba:,.0f} / {hi:,.0f}  (spread {hi-lo:,.0f})")
    print(f"peak month (BASE/NORMAL)     : {tot.idxmax()}  ({tot.max():,.0f})")
    print("channel shares (18M BASE/NORMAL):",
          (bn.groupby("channel_id").analytical_baseline_units.sum() / ba).round(3).to_dict())
    print("\nWrote:", OUTDIR / "DemandIQ_Step7C_18M_Analytical_Forecast.csv")
    print("Wrote:", OUTDIR / "DemandIQ_Step7C_13W_Launch_Forecast.csv")
    print("ALL QA PASSED.")


if __name__ == "__main__":
    main()
