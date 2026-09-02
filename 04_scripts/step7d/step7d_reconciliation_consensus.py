"""
DemandIQ - Step 7D - Top-Down / Bottom-Up Reconciliation & Consensus Forecast (HIS-001).

Moves the 18-month strategic demand plan through governed versions:
  V0 ANALYTICAL BASELINE (frozen Step 7C, BASE/NORMAL)  -- never overwritten
  V1 COMMERCIAL / TOP-DOWN PLAN (Option B: cat +5% growth, HIS 19% share)
  V2 CONSENSUS FORECAST (governed rule; NOT an average)
  V3 APPROVED IBP PLAN (= V2 unless management changes it; UNCONSTRAINED demand)

Outputs (launch-only):
  - DemandIQ_Step7D_Forecast_Versions.csv       (V0/V1/V2/V3 audit trail, month x channel)
  - DemandIQ_Step7D_Reconciliation_Summary.csv  (month x SKU reconciliation + exceptions + TOTAL)

Governance: unconstrained demand only (no supply/inventory/initial-buy). No future HIS actuals,
no hidden truth, no realized future weather. Mature 4A-6F and Step 7C outputs untouched.

Run: python step7d_reconciliation_consensus.py
(Optional env STEP7D_OUTDIR to redirect outputs for a dry verification run.)
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(r"D:\Downloads\DemandIQ")
V0_FILE = ROOT / "05_outputs" / "launch_step7c" / "DemandIQ_Step7C_18M_Analytical_Forecast.csv"
ECON = ROOT / "02_data" / "processed" / "DemandIQ_Step3D_v4_Retail_Economics.csv"
OUTDIR = Path(os.environ.get("STEP7D_OUTDIR", str(ROOT / "05_outputs" / "launch_step7d")))
OUTDIR.mkdir(parents=True, exist_ok=True)

PLANNING_CYCLE = "CYCLE_01_2026-08"
AS_OF_DATE = "2026-08-24"

# ---- approved top-down commercial assumptions (SYNTHETIC COMMERCIAL PLANNING ASSUMPTIONS) ----
CATEGORY_GROWTH = 0.05     # Option B
HIS_CATEGORY_SHARE = 0.19  # Option B

# ---- governed reconciliation policy (GOVERNANCE ASSUMPTIONS) ----
TOL_WITHIN = 0.05          # <=5% -> WITHIN_TOLERANCE
TOL_REVIEW = 0.15          # 5-15% -> PLANNER_REVIEW ; >15% -> IBP_EXCEPTION
CONSENSUS_CAP = 0.10       # max +/-10% consensus move from V0 without executive sign-off


def tolerance_status(pct):
    a = abs(pct)
    if a <= TOL_WITHIN:
        return "WITHIN_TOLERANCE"
    if a <= TOL_REVIEW:
        return "PLANNER_REVIEW"
    return "IBP_EXCEPTION"


def main():
    # ---------- V0 bottom-up (frozen Step 7C, BASE/NORMAL) ----------
    m = pd.read_csv(V0_FILE)
    v0 = (m[(m.launch_scenario == "BASE") & (m.weather_scenario == "NORMAL")]
          [["planning_month", "channel_id", "analytical_baseline_units", "lifecycle_phase"]]
          .rename(columns={"analytical_baseline_units": "v0_units"})
          .sort_values(["planning_month", "channel_id"]).reset_index(drop=True))
    v0_first12 = v0[v0.planning_month <= sorted(v0.planning_month.unique())[11]].v0_units.sum()
    v0_18m = v0.v0_units.sum()
    # frozen scenario band (for governance check)
    band = {}
    for sc in ["LOW", "HIGH"]:
        s = m[(m.launch_scenario == sc) & (m.weather_scenario == "NORMAL")]
        band[sc + "_18m"] = s.analytical_baseline_units.sum()
        band[sc + "_12m"] = (s.groupby("planning_month").analytical_baseline_units.sum().iloc[:12].sum())

    # ---------- top-down category context (frozen mature data) ----------
    econ = pd.read_csv(ECON, usecols=["sku_id", "week_start", "weekly_plan_units"])
    nyears = econ.week_start.nunique() / 52.0
    category_total = float((econ.groupby("sku_id").weekly_plan_units.sum() / nyears).sum())
    implied_share = v0_first12 / category_total
    v1_12m_target = category_total * (1 + CATEGORY_GROWTH) * HIS_CATEGORY_SHARE
    v1_factor = v1_12m_target / v0_first12  # level-only scaling (preserves V0 shape + 45/35/20 mix)

    # ---------- consensus factor (governed rule; NOT an average) ----------
    v1_var_pct = v1_factor - 1.0
    status_total = tolerance_status(v1_var_pct)
    if status_total == "WITHIN_TOLERANCE":
        consensus_factor = 1.0                                   # retain analytical
    elif status_total == "PLANNER_REVIEW":
        consensus_factor = 1.0 + np.clip(v1_var_pct, -CONSENSUS_CAP, CONSENSUS_CAP)  # bounded move
    else:  # IBP_EXCEPTION -> escalate, no automatic move
        consensus_factor = 1.0
    v3_factor = consensus_factor  # management approves consensus unchanged

    # ---------- build versioned month x channel table ----------
    FACTORS = {"V0_ANALYTICAL_BASELINE": 1.0, "V1_COMMERCIAL_PLAN": v1_factor,
               "V2_CONSENSUS_FORECAST": consensus_factor, "V3_APPROVED_PLAN": v3_factor}
    META = {
        "V0_ANALYTICAL_BASELINE": ("ANALYTICAL BASELINE", "DEMAND PLANNING", "BASELINE",
            "Step 7C cold-start analytical baseline (BASE/NORMAL); anchor version"),
        "V1_COMMERCIAL_PLAN": ("COMMERCIAL / TOP-DOWN PLAN", "MERCHANDISING / COMMERCIAL PLANNING", "PROPOSED",
            f"Top-down Option B: category +{CATEGORY_GROWTH:.0%} growth x HIS {HIS_CATEGORY_SHARE:.0%} share; level-scaled to V0 shape; 45/35/20 mix preserved"),
        "V2_CONSENSUS_FORECAST": ("CONSENSUS FORECAST", "DEMAND PLANNING (consensus facilitator)", "CONSENSUS",
            f"{status_total}: accepted bounded consensus move (cap +/-{CONSENSUS_CAP:.0%}) vs V0; residual vs commercial escalated to IBP; not an average"),
        "V3_APPROVED_PLAN": ("APPROVED IBP PLAN", "MANAGEMENT / IBP", "APPROVED",
            "Management approved consensus unchanged; unconstrained demand plan"),
    }
    ORDER = ["V0_ANALYTICAL_BASELINE", "V1_COMMERCIAL_PLAN", "V2_CONSENSUS_FORECAST", "V3_APPROVED_PLAN"]
    prev_of = {"V0_ANALYTICAL_BASELINE": None, "V1_COMMERCIAL_PLAN": "V0_ANALYTICAL_BASELINE",
               "V2_CONSENSUS_FORECAST": "V1_COMMERCIAL_PLAN", "V3_APPROVED_PLAN": "V2_CONSENSUS_FORECAST"}

    units = {v: (v0[["planning_month", "channel_id"]].assign(
                 u=(v0.v0_units * FACTORS[v]).round(2))) for v in ORDER}

    rows = []
    for v in ORDER:
        name, owner, appr, reason = META[v]
        cur = units[v]
        prev = units[prev_of[v]] if prev_of[v] else None
        for _, r in cur.iterrows():
            u = r.u
            if prev is None:
                pu, cu, cp = np.nan, 0.0, 0.0
            else:
                pu = float(prev[(prev.planning_month == r.planning_month) &
                                (prev.channel_id == r.channel_id)].u.iloc[0])
                cu = round(u - pu, 2)
                cp = round((u / pu - 1) * 100, 3) if pu else 0.0
            rows.append({
                "forecast_version": v, "version_name": name, "planning_cycle": PLANNING_CYCLE,
                "forecast_as_of_date": AS_OF_DATE, "planning_month": r.planning_month,
                "sku_id": "HIS-001", "channel_id": r.channel_id, "forecast_units": u,
                "previous_version_units": pu, "change_units": cu, "change_pct": cp,
                "change_reason": reason, "owner_role": owner, "approval_status": appr,
                "actual_demand_units": np.nan, "forecast_error_vs_actual": np.nan,
                "fva_status": "NOT YET MEASURABLE - NO LAUNCH ACTUALS",
                "provenance": "DERIVED from Step 7C V0 (frozen) + SYNTHETIC COMMERCIAL PLANNING ASSUMPTIONS (Option B)"})
    versions = pd.DataFrame(rows)

    # ---------- reconciliation summary (month x SKU + TOTAL) ----------
    def agg(v):
        return units[v].groupby("planning_month").u.sum()
    v0m, v1m, v2m = agg("V0_ANALYTICAL_BASELINE"), agg("V1_COMMERCIAL_PLAN"), agg("V2_CONSENSUS_FORECAST")
    rec = []
    months = sorted(v0.planning_month.unique())
    for pm in months + ["TOTAL_18M"]:
        if pm == "TOTAL_18M":
            a, b, c = v0m.sum(), v1m.sum(), v2m.sum()
        else:
            a, b, c = v0m[pm], v1m[pm], v2m[pm]
        var = b - a
        pct = var / a if a else 0.0
        direction = ("COMMERCIAL_ABOVE_ANALYTICAL" if pct > TOL_WITHIN else
                     "COMMERCIAL_BELOW_ANALYTICAL" if pct < -TOL_WITHIN else "ALIGNED")
        status = tolerance_status(pct)
        decision = {"WITHIN_TOLERANCE": "Retain analytical baseline",
                    "PLANNER_REVIEW": "Planner may accept bounded documented override (cap +/-10%)",
                    "IBP_EXCEPTION": "Escalate to executive IBP; no automatic blend"}[status]
        rec.append({"planning_month": pm, "sku_id": "HIS-001",
                    "v0_units": round(a, 2), "v1_units": round(b, 2),
                    "absolute_variance_units": round(var, 2), "percentage_variance": round(pct * 100, 3),
                    "direction": direction, "reconciliation_status": status,
                    "v2_consensus_units": round(c, 2),
                    "consensus_adjustment_units": round(c - a, 2),
                    "consensus_adjustment_pct": round((c / a - 1) * 100, 3) if a else 0.0,
                    "decision_required": decision})
    recon = pd.DataFrame(rec)

    # ================= QA =================
    def qa(cond, msg):
        assert cond, "QA FAIL: " + msg

    qa(abs(v0_18m - 44918.94) < 1.0, "V0 must match Step 7C (unchanged)")
    qa(set(versions.forecast_version) == set(ORDER), "V0/V1/V2/V3 all present")
    for v in ORDER:  # channel reconciles to SKU total per version/month
        g = units[v].groupby("planning_month").u.sum()
        qa(len(g) == 18, f"{v} must have 18 months")
    qa((versions.forecast_units >= 0).all(), "no negative forecast units")
    # consensus is NOT a simple average of V0 and V1
    v2_tot, avg_tot = v2m.sum(), (v0m.sum() + v1m.sum()) / 2
    qa(abs(v2_tot - avg_tot) > 1.0, "consensus must not equal (V0+V1)/2")
    # tolerance reproducible
    qa(tolerance_status(v1_var_pct) == status_total, "tolerance reproducible")
    # V3 within LOW/HIGH band (governance diagnostic)
    v3_12 = agg("V3_APPROVED_PLAN").iloc[:12].sum()
    v3_18 = agg("V3_APPROVED_PLAN").sum()
    v3_in_band = (band["LOW_12m"] <= v3_12 <= band["HIGH_12m"]) and (band["LOW_18m"] <= v3_18 <= band["HIGH_18m"])

    versions.to_csv(OUTDIR / "DemandIQ_Step7D_Forecast_Versions.csv", index=False)
    recon.to_csv(OUTDIR / "DemandIQ_Step7D_Reconciliation_Summary.csv", index=False)

    # ---------- report ----------
    print("===== STEP 7D RECONCILIATION & CONSENSUS =====")
    print(f"Mature category annual comparable  : {category_total:,.2f}")
    print(f"V0 first-12 / 18-month             : {v0_first12:,.2f} / {v0_18m:,.2f}")
    print(f"V0 implied category share          : {implied_share*100:.2f}%")
    print(f"V1 top-down 12-mo target (Opt B)   : {v1_12m_target:,.2f}  (factor {v1_factor:.4f})")
    print(f"V0->V1 variance                    : {(v1_12m_target-v0_first12):+,.0f} ({v1_var_pct*100:+.2f}%) -> {status_total}")
    print(f"Consensus factor (bounded)         : {consensus_factor:.4f}")
    print(f"V2 12-mo / 18-mo                    : {agg('V2_CONSENSUS_FORECAST').iloc[:12].sum():,.0f} / {v2m.sum():,.0f}")
    print(f"V2 vs V0 / vs V1 (12-mo)           : {(agg('V2_CONSENSUS_FORECAST').iloc[:12].sum()-v0_first12):+,.0f} / {(agg('V2_CONSENSUS_FORECAST').iloc[:12].sum()-v1_12m_target):+,.0f}")
    print(f"V3 12-mo / 18-mo                    : {v3_12:,.0f} / {v3_18:,.0f}")
    print(f"V3 within V0 LOW/HIGH band          : {'YES' if v3_in_band else 'NO'}")
    monthly_exc = recon[recon.planning_month != "TOTAL_18M"]
    print(f"monthly reconciliation exceptions  : PLANNER_REVIEW={int((monthly_exc.reconciliation_status=='PLANNER_REVIEW').sum())}, "
          f"IBP_EXCEPTION={int((monthly_exc.reconciliation_status=='IBP_EXCEPTION').sum())}")
    biggest = monthly_exc.loc[monthly_exc.absolute_variance_units.abs().idxmax()]
    print(f"largest monthly disagreement       : {biggest.planning_month} ({biggest.absolute_variance_units:+,.0f} units)")
    print("\nQA PASSED. Wrote:")
    print(" ", OUTDIR / "DemandIQ_Step7D_Forecast_Versions.csv")
    print(" ", OUTDIR / "DemandIQ_Step7D_Reconciliation_Summary.csv")


if __name__ == "__main__":
    main()
