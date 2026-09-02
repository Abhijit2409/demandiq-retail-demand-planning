"""
DemandIQ - Step 7E - Launch Buy, Sell-Through & Reforecast Decision Loop (HIS-001).

TWO-STAGE, ORDER-ENFORCED:
  PART A  Pre-launch initial buy + channel allocation + reserve  -> FREEZE (uses no actuals)
  PART B  Synthetic launch actuals (seeded)  -- generated only AFTER the freeze
  PART C  Checkpoint sell-through + reforecast (analog-prior -> actual shrinkage)
  PART D  Supply feasibility + planner decisions (CHASE/HOLD/REALLOCATE/CUT/ESCALATE)

The initial buy is NEVER optimized with launch actuals (buy is fixed before Part B runs).
Hidden latent demand is EVALUATION ONLY and never used by the reforecast.
Unconstrained demand vs supply kept separate; economics are PLANNING EXPOSURE PROXIES.
Mature 4A-6F and Steps 7A-7D outputs are untouched.

Run: python step7e_launch_execution.py   (env STEP7E_OUTDIR to redirect for a dry run)
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(r"D:\Downloads\DemandIQ")
V0V3 = ROOT / "05_outputs" / "launch_step7d" / "DemandIQ_Step7D_Forecast_Versions.csv"
W13 = ROOT / "05_outputs" / "launch_step7c" / "DemandIQ_Step7C_13W_Launch_Forecast.csv"
OUTDIR = Path(os.environ.get("STEP7E_OUTDIR", str(ROOT / "05_outputs" / "launch_step7e")))
OUTDIR.mkdir(parents=True, exist_ok=True)

CHANNELS = ["ECOM", "RETAIL", "WHOLESALE"]
PLANNED_MIX = {"ECOM": 0.45, "RETAIL": 0.35, "WHOLESALE": 0.20}
PLANNING_CYCLE = "CYCLE_01_2026-08"
BUY_FREEZE_DATE = "2026-08-24"
CHECKPOINTS = [1, 2, 4, 8, 13]

# ---- frozen upstream factors ----
V3_OVER_V0 = 1.10  # Step 7D consensus/approved factor (governed)

# ---- approved supply setup: B - BALANCED (SYNTHETIC SUPPLY PLANNING ASSUMPTIONS) ----
EFFECTIVE_LEAD_WEEKS = 8
CHASE_MAX_PCT = 0.15          # <=15% of initial buy
CHASE_DECISION_DEADLINE_WK = 5  # order by W5 to arrive <=W13 (5+8=13)

# ---- buy policy (SYNTHETIC / GOVERNANCE ASSUMPTIONS) ----
BUFFERS = {"LEAN": 0.04, "BALANCED": 0.09, "PROTECTIVE": 0.14}  # launch uncertainty buffer, NOT mature 2.5wk SS
SELECTED_POSITION = "BALANCED"
RESERVE_PCT = 0.12            # flex/unallocated reserve as share of initial buy

# ---- economics (PLANNING EXPOSURE PROXIES) ----
NET_ASP = 609.8               # HIS net-ASP proxy = 0.813 analog realization x MSRP 750
CARRYING_ANNUAL = 0.18        # frozen carrying-cost proxy
MARKDOWN_RATE = 0.20          # SYNTHETIC launch clearance markdown on residual overbuy

# ---- reforecast + exception governance (SYNTHETIC GOVERNANCE ASSUMPTIONS) ----
K_PRIOR = 4                   # w_actual = n/(n+k)
VAR_ON_PLAN, VAR_WATCH = 0.10, 0.20        # cumulative demand variance bands
MIX_WATCH_PP, MIX_ACTION_PP = 0.05, 0.08   # channel-mix deviation bands

# ---- synthetic-actuals generation (seeded; centered on ANALYTICAL BASE, not the lifted plan) ----
SEED = 7
ADOPTION_SD = 0.08
WEEKLY_NOISE_SD = 0.10
CHANNEL_SKEW = {"ECOM": 1.15, "RETAIL": 1.00, "WHOLESALE": 0.80}  # mix skew, renormalized to hold total


def load_weekly_base():
    w = pd.read_csv(W13)
    bn = w[(w.launch_scenario == "BASE") & (w.weather_scenario == "NORMAL")]
    base = bn.pivot_table(index=["launch_week_number", "week_start"], columns="channel_id",
                          values="analytical_baseline_units").reset_index().sort_values("launch_week_number")
    lohi = {}
    for sc in ["LOW", "HIGH"]:
        lohi[sc] = w[(w.launch_scenario == sc) & (w.weather_scenario == "NORMAL")].analytical_baseline_units.sum()
    return base, lohi


def main():
    base, lohi = load_weekly_base()
    weeks = base.launch_week_number.tolist()
    # analytical BASE weekly per channel, and APPROVED plan = BASE x V3/V0
    base_ch = {c: base[c].to_numpy() for c in CHANNELS}
    approved_ch = {c: base_ch[c] * V3_OVER_V0 for c in CHANNELS}
    approved_total = float(sum(approved_ch[c].sum() for c in CHANNELS))
    base_total = float(sum(base_ch[c].sum() for c in CHANNELS))
    # demand-scenario band (genuine adoption uncertainty, from Step 7C)
    DEM = {"LOW": lohi["LOW"], "BASE": base_total, "HIGH": lohi["HIGH"]}

    # ================= PART A - PRE-LAUNCH BUY (no actuals) =================
    covered = approved_total
    buy_rows = []
    for pos, buf in BUFFERS.items():
        buy = covered * (1 + buf)
        reserve = buy * RESERVE_PCT
        prealloc = buy - reserve
        alloc = {c: prealloc * PLANNED_MIX[c] for c in CHANNELS}
        underbuy_high = max(0.0, DEM["HIGH"] - buy)
        overbuy_low = max(0.0, buy - DEM["LOW"])
        underbuy_exp = underbuy_high * NET_ASP
        overbuy_exp = overbuy_low * NET_ASP * MARKDOWN_RATE
        carrying = buy * NET_ASP * CARRYING_ANNUAL * (13 / 52)
        buy_rows.append({
            "buy_position": pos, "covered_demand_units": round(covered, 1),
            "buffer_pct": buf, "buffer_units": round(buy - covered, 1),
            "initial_buy_units": round(buy, 1), "reserve_units": round(reserve, 1),
            "preallocated_units": round(prealloc, 1),
            "alloc_ecom": round(alloc["ECOM"], 1), "alloc_retail": round(alloc["RETAIL"], 1),
            "alloc_wholesale": round(alloc["WHOLESALE"], 1),
            "excess_vs_low": round(buy - DEM["LOW"], 1), "excess_vs_base": round(buy - DEM["BASE"], 1),
            "short_vs_high": round(min(0.0, buy - DEM["HIGH"]), 1),
            "underbuy_exposure_cad": round(underbuy_exp, 0), "overbuy_markdown_exposure_cad": round(overbuy_exp, 0),
            "carrying_cost_proxy_cad": round(carrying, 0),
            "two_sided_exposure_cad": round(underbuy_exp + overbuy_exp, 0),
            "recommended_flag": int(pos == SELECTED_POSITION),
            "prelaunch_buy_frozen": int(pos == SELECTED_POSITION),
            "buy_freeze_date": BUY_FREEZE_DATE, "planning_cycle": PLANNING_CYCLE,
            "demand_version_used": "V3_APPROVED_PLAN",
            "provenance": "DERIVED from Step 7D V3 + SYNTHETIC SUPPLY/BUY GOVERNANCE ASSUMPTIONS"})
    buy_df = pd.DataFrame(buy_rows)
    buy_df.to_csv(OUTDIR / "DemandIQ_Step7E_Initial_Buy_Plan.csv", index=False)

    sel = buy_df[buy_df.buy_position == SELECTED_POSITION].iloc[0]
    initial_buy = float(sel.initial_buy_units)
    reserve_pool = float(sel.reserve_units)
    alloc0 = {c: float(sel[f"alloc_{c.lower()}"]) for c in CHANNELS}
    print(f"[A] FROZEN buy={initial_buy:,.0f} ({SELECTED_POSITION}) reserve={reserve_pool:,.0f} "
          f"alloc={ {c: round(alloc0[c]) for c in CHANNELS} }")

    # ================= PART B - SYNTHETIC ACTUALS (after freeze) =================
    rng = np.random.default_rng(SEED)
    adoption = float(rng.normal(1.0, ADOPTION_SD))                       # one launch-level draw (on BASE)
    skew_w = {c: PLANNED_MIX[c] * CHANNEL_SKEW[c] for c in CHANNELS}
    ssum = sum(skew_w.values())
    realized_mix = {c: skew_w[c] / ssum for c in CHANNELS}               # mix changes, SKU total preserved
    nwk = len(weeks)
    weekly_noise = rng.normal(1.0, WEEKLY_NOISE_SD, nwk)
    base_week_total = np.array([sum(base_ch[c][i] for c in CHANNELS) for i in range(nwk)])
    latent_sku = base_week_total * adoption * np.clip(weekly_noise, 0.4, 1.8)
    latent = {c: latent_sku * realized_mix[c] for c in CHANNELS}         # latent = HIDDEN TRUTH (eval only)

    # forward inventory sim with scheduled receipts (reserve/chase decided at checkpoints)
    inv = dict(alloc0)
    receipts = {c: np.zeros(nwk) for c in CHANNELS}   # scheduled future receipts
    reserve_left = reserve_pool
    chase_units_total = 0.0
    act_rows, decisions = [], []

    def cum(arr_dict, upto, key):
        return float(sum(arr_dict[c][:upto].sum() if key == "arr" else 0 for c in CHANNELS))

    obs = {c: np.zeros(nwk) for c in CHANNELS}
    lost = {c: np.zeros(nwk) for c in CHANNELS}
    begin = {c: np.zeros(nwk) for c in CHANNELS}
    endinv = {c: np.zeros(nwk) for c in CHANNELS}

    for i, wk in enumerate(weeks):
        for c in CHANNELS:
            inv[c] += receipts[c][i]
            begin[c][i] = inv[c]
            d = latent[c][i]
            ship = min(d, inv[c])
            obs[c][i] = ship
            lost[c][i] = d - ship
            inv[c] -= ship
            endinv[c][i] = inv[c]
            act_rows.append({
                "launch_week_number": wk, "week_start": base.week_start.iloc[i], "channel_id": c,
                "planned_units_approved": round(approved_ch[c][i], 1),
                "latent_demand_units_HIDDEN_EVAL_ONLY": round(d, 1),
                "observed_sales_units": round(ship, 1), "begin_inventory_units": round(begin[c][i], 1),
                "receipt_units": round(receipts[c][i], 1), "end_inventory_units": round(inv[c], 1),
                "lost_demand_units": round(lost[c][i], 1), "stockout_flag": int(lost[c][i] > 1e-6),
                "provenance": "SYNTHETIC LAUNCH ACTUALS (seed=%d); latent=hidden eval-only" % SEED})

        # ---- checkpoint decision (uses ONLY observable info) ----
        if wk in CHECKPOINTS:
            up = i + 1
            cum_obs = sum(obs[c][:up].sum() for c in CHANNELS)
            cum_plan = sum(approved_ch[c][:up].sum() for c in CHANNELS)
            attain = cum_obs / cum_plan if cum_plan else 0.0
            var_pct = attain - 1.0
            # observed channel mix vs planned
            mix_obs = {c: (obs[c][:up].sum() / cum_obs if cum_obs else 0) for c in CHANNELS}
            mix_dev = {c: mix_obs[c] - PLANNED_MIX[c] for c in CHANNELS}
            max_dev_ch = max(CHANNELS, key=lambda c: mix_dev[c])
            max_dev = mix_dev[max_dev_ch]
            # velocity (recent up-to-4wk observed run-rate) & remaining coverage
            recent = min(up, 4)
            vel = sum(obs[c][up - recent:up].sum() for c in CHANNELS) / recent
            rem_weeks = nwk - up
            # reforecast remaining via shrinkage toward observed attainment
            n = up
            w_actual = n / (n + K_PRIOR)
            orig_rem_plan = sum(approved_ch[c][up:].sum() for c in CHANNELS)
            reforecast_rem = orig_rem_plan * (w_actual * attain + (1 - w_actual))
            reforecast_total = cum_obs + reforecast_rem
            rem_inv = sum(inv_c for inv_c in inv.values()) + reserve_left
            coverage_ratio = rem_inv / reforecast_rem if reforecast_rem > 1e-6 else 99.0
            wos = rem_inv / vel if vel > 1e-6 else 99.0
            chase_feasible = wk <= CHASE_DECISION_DEADLINE_WK

            # ----- governed decision (var-based and mix-based severity) -----
            var_status = ("ON_PLAN" if abs(var_pct) <= VAR_ON_PLAN else
                          "WATCH" if abs(var_pct) <= VAR_WATCH else "ACTION_REQUIRED")
            mix_status = ("ON_PLAN" if abs(max_dev) < MIX_WATCH_PP else
                          "WATCH" if abs(max_dev) < MIX_ACTION_PP else "CANDIDATE")
            sev = {"ON_PLAN": 0, "WATCH": 1, "CANDIDATE": 1, "ACTION_REQUIRED": 2, "ESCALATE": 3}
            status = max([var_status, mix_status], key=lambda s: sev[s])
            if status == "CANDIDATE":
                status = "WATCH"
            action, reason, reserve_deploy, chase = "HOLD", "", 0.0, 0.0
            if mix_status == "CANDIDATE" and abs(var_pct) <= VAR_WATCH and reserve_left > 1:
                action, status = "REALLOCATE", "ACTION_REQUIRED"
                reserve_deploy = min(reserve_left, max(0.0, reforecast_rem * max_dev))
                reason = (f"{max_dev_ch} mix {max_dev*100:+.1f}pp (>= {MIX_ACTION_PP*100:.0f}pp) while total "
                          f"within tolerance; deploy reserve to the leading channel")
                if rem_weeks > 0 and reserve_deploy > 0:
                    receipts[max_dev_ch][up] += reserve_deploy
                    reserve_left -= reserve_deploy
            elif var_pct > VAR_WATCH and coverage_ratio < 1.0:
                if chase_feasible:
                    chase = min(initial_buy * CHASE_MAX_PCT, reforecast_rem - rem_inv)
                    action, status = "CHASE", "ACTION_REQUIRED"
                    reason = "demand >> plan and coverage short; chase feasible within lead time (order by W5)"
                    arrive = up + EFFECTIVE_LEAD_WEEKS
                    if arrive < nwk and chase > 0:
                        receipts[max(CHANNELS, key=lambda c: mix_dev[c])][arrive] += chase
                        chase_units_total += chase
                else:
                    action, status = "ESCALATE", "ESCALATE"
                    reason = "demand >> plan and coverage short but chase cannot arrive within the launch window"
            elif var_pct < -VAR_WATCH and coverage_ratio > 1.25:
                action, status = "CUT", "ACTION_REQUIRED"
                reason = "demand << plan with rising excess; hold back reserve / reduce future commitment"
            elif abs(var_pct) > VAR_WATCH:
                action, status = "ESCALATE", "ESCALATE"
                reason = "material variance with unresolved feasibility"
            else:
                action = "HOLD"
                reason = (f"demand {var_pct*100:+.1f}% vs plan ({var_status}); {max_dev_ch} mix "
                          f"{max_dev*100:+.1f}pp ({mix_status}); coverage {coverage_ratio:.2f}x; "
                          f"reforecast updated, no action required")

            long_range = ("DECREASE second-season outlook" if var_pct < -VAR_ON_PLAN else
                          "INCREASE second-season outlook" if var_pct > VAR_ON_PLAN else
                          "MAINTAIN second-season outlook")

            decisions.append({
                "checkpoint": f"W{wk}", "launch_week_number": wk,
                "cum_plan_units": round(cum_plan, 1), "cum_observed_units": round(cum_obs, 1),
                "attainment_pct": round(attain * 100, 1), "demand_variance_pct": round(var_pct * 100, 1),
                "reforecast_total_units": round(reforecast_total, 1),
                "w_actual": round(w_actual, 3),
                "remaining_inventory_units": round(rem_inv, 1), "weeks_of_supply": round(wos, 1),
                "coverage_ratio": round(coverage_ratio, 2),
                "max_channel_mix_dev_pp": round(max_dev * 100, 1), "max_dev_channel": max_dev_ch,
                "channel_mix_status": mix_status, "chase_feasible_flag": int(chase_feasible),
                "exception_status": status, "planner_action": action, "action_reason": reason,
                "reserve_deployed_units": round(reserve_deploy, 1), "chase_units": round(chase, 1),
                "long_range_signal": long_range,
                "provenance": "DERIVED from synthetic actuals + SYNTHETIC governance thresholds"})

    actuals = pd.DataFrame(act_rows)
    actuals.to_csv(OUTDIR / "DemandIQ_Step7E_Launch_Weekly_Actuals.csv", index=False)

    # ================= PART C - checkpoint reforecast versions =================
    orig_total_plan = approved_total
    ref_rows = [{"forecast_version": "ORIGINAL_V3_PLAN", "forecast_as_of": BUY_FREEZE_DATE,
                 "remaining_horizon_units": round(orig_total_plan, 1), "change_vs_original_units": 0.0,
                 "change_vs_original_pct": 0.0, "reason": "approved launch plan (V3 x Step7C weekly shape)",
                 "evidence_available": "none (pre-launch)"}]
    for d in decisions:
        ref_rows.append({
            "forecast_version": f"W{d['launch_week_number']}_REFORECAST",
            "forecast_as_of": f"W{d['launch_week_number']}",
            "remaining_horizon_units": d["reforecast_total_units"],
            "change_vs_original_units": round(d["reforecast_total_units"] - orig_total_plan, 1),
            "change_vs_original_pct": round((d["reforecast_total_units"] / orig_total_plan - 1) * 100, 2),
            "reason": f"shrinkage w_actual={d['w_actual']} toward observed attainment {d['attainment_pct']}%",
            "evidence_available": f"{d['launch_week_number']} obs weeks"})
    reforecast = pd.DataFrame(ref_rows)
    reforecast.to_csv(OUTDIR / "DemandIQ_Step7E_Checkpoint_Reforecast.csv", index=False)

    dec_df = pd.DataFrame(decisions)
    dec_df.to_csv(OUTDIR / "DemandIQ_Step7E_Planner_Decisions.csv", index=False)

    # ================= evaluation (forecast vs planning quality) =================
    realized_total = float(sum(latent[c].sum() for c in CHANNELS))   # latent = truth (eval only)
    observed_total = float(sum(obs[c].sum() for c in CHANNELS))
    fill_rate = observed_total / realized_total if realized_total else 0.0
    ending_inv = sum(inv.values()) + reserve_left                    # unsold = channel inv + idle reserve
    total_supply = initial_buy + chase_units_total
    lost_units = float(sum(lost[c].sum() for c in CHANNELS))          # under-buy / stockout-censored demand
    underbuy_units = lost_units
    overbuy_units = max(0.0, total_supply - observed_total)           # unsold inventory
    # forecast accuracy (original plan vs realized truth) -- weekly
    plan_wk = base_week_total * V3_OVER_V0
    truth_wk = np.array([sum(latent[c][i] for c in CHANNELS) for i in range(nwk)])
    wape = np.abs(truth_wk - plan_wk).sum() / truth_wk.sum() * 100
    bias = (plan_wk.sum() - truth_wk.sum()) / truth_wk.sum() * 100

    # ================= QA =================
    def qa(cond, msg):
        assert cond, "QA FAIL: " + msg
    qa(sel.demand_version_used == "V3_APPROVED_PLAN", "buy must use V3")
    qa(int(sel.prelaunch_buy_frozen) == 1, "freeze recorded")
    qa(abs(sum(alloc0.values()) + reserve_pool - initial_buy) < 1.0, "alloc + reserve = buy")
    qa((actuals.observed_sales_units <= actuals.begin_inventory_units + 1e-6).all(), "sales cannot exceed available inv")
    qa((actuals.end_inventory_units >= -1e-6).all(), "inventory never negative")
    qa(set(dec_df.checkpoint) == {"W1", "W2", "W4", "W8", "W13"}, "checkpoints W1/2/4/8/13")
    qa((reforecast.forecast_version == "ORIGINAL_V3_PLAN").any(), "original plan preserved")
    # channel reconciliation of actuals to SKU
    qa(abs(actuals.observed_sales_units.sum() - observed_total) < 1.0, "channel obs reconcile to SKU")

    print(f"[B] adoption draw={adoption:.3f} realized_mix={{'ECOM':{realized_mix['ECOM']:.3f},'RETAIL':{realized_mix['RETAIL']:.3f},'WHOLESALE':{realized_mix['WHOLESALE']:.3f}}}")
    print(f"    realized demand(truth)={realized_total:,.0f} observed sales={observed_total:,.0f} fill={fill_rate*100:.1f}%")
    print(f"[C] reforecast W1..W13 totals: " + ", ".join(f"{d['checkpoint']}={d['reforecast_total_units']:,.0f}" for d in decisions))
    print(f"[D] actions: " + ", ".join(f"{d['checkpoint']}:{d['planner_action']}({d['exception_status']})" for d in decisions))
    print(f"    reserve deployed={reserve_pool-reserve_left:,.0f} chase={chase_units_total:,.0f}")
    print(f"[perf] initial_buy={initial_buy:,.0f} ending_inv={ending_inv:,.0f} underbuy={underbuy_units:,.0f} overbuy={overbuy_units:,.0f}")
    print(f"[fcst quality] original-plan WAPE={wape:.1f}% Bias={bias:+.1f}% (vs hidden truth, eval only)")
    print("QA PASSED. Files written to", OUTDIR)


if __name__ == "__main__":
    main()
