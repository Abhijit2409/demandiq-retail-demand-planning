"""
DemandIQ - Step 7F - Forecast Value Add, Rolling Forecast Cycle 02 & Lifecycle Handoff
(HIS-001 - Hybrid Insulated Shell launch).

FINAL SUBSTANTIVE ANALYTICAL/GOVERNANCE STEP of the launch workspace.

This ONE script produces four governed outputs from FROZEN 7C/7D/7E evidence only:
  1. DemandIQ_Step7F_FVA_Analysis.csv          (retrospective forecast-accuracy FVA)
  2. DemandIQ_Step7F_Cycle02_Rolling_Forecast.csv (first TRUE rolling update, Oct2026->Mar2028)
  3. DemandIQ_Step7F_Lifecycle_Handoff.csv      (mature-engine eligibility gates)
  4. DemandIQ_Step7F_Policy_Sensitivity.csv     (counterfactual REALLOCATE-threshold diagnostic)

=========================  TWO SEPARATE ANALYTICAL TIMELINES  =========================
This script deliberately keeps two branches that MUST NOT share information:

  (A) RETROSPECTIVE branch (Parts B, C, G):
        may look at the whole 13-week seeded launch path, incl. the HIDDEN latent
        synthetic demand, but ONLY to *score* forecasts after the fact.

  (B) OPERATIONAL Cycle-02 planning branch (Part D/E):
        may use ONLY information available through the W4 checkpoint (2026-09-28).
        It NEVER sees W5-W13 actuals, W8/W13 reforecasts, the final latent truth,
        final observed sales, final service, the retrospective FVA, or the policy
        sensitivity result.

The latent synthetic demand (`latent_demand_units_HIDDEN_EVAL_ONLY`) is EVALUATION-ONLY.
It never feeds a reforecast, the Cycle-02 forecast, or any planner decision.

=========================  GOVERNANCE / LEAKAGE CONTRACT  =============================
  - No modification of frozen Steps 4A-6F or 7A-7E. Read-only on all frozen files.
  - No ETS/SARIMA fit on HIS-001 (only 13 launch weeks exist).
  - Economics are PLANNING EXPOSURE PROXIES, not accounting profit.
  - FVA is a FORECAST-ACCURACY governance metric, not a CAD "value".
  - Sign conventions: Bias = sum(F-A)/sum(A)*100 ; FVA_pp = WAPE(prior) - WAPE(new).

SIMULATION-DESIGN CAVEAT (do not omit): the Step 7E synthetic actual generator was
centered on the V0 ANALYTICAL BASELINE, not on the +10% V3 consensus plan. Therefore
any result where V0 beats V1/V2/V3 is an ILLUSTRATIVE GOVERNANCE DEMONSTRATION on this
seeded path, NOT independent empirical evidence that the commercial override was harmful.

Run:  python step7f_fva_rolling_handoff.py
The PROJECT OWNER runs this locally. Claude does not run the official analysis.
"""
import os
from pathlib import Path
import numpy as np
import pandas as pd

# ============================================================
# Paths (frozen inputs are read-only)
# ============================================================
ROOT = Path(r"D:\Downloads\DemandIQ")
ECON = ROOT / "02_data" / "processed" / "DemandIQ_Step3D_v4_Retail_Economics.csv"
S7C_13W = ROOT / "05_outputs" / "launch_step7c" / "DemandIQ_Step7C_13W_Launch_Forecast.csv"
S7D_VERS = ROOT / "05_outputs" / "launch_step7d" / "DemandIQ_Step7D_Forecast_Versions.csv"
S7D_RECON = ROOT / "05_outputs" / "launch_step7d" / "DemandIQ_Step7D_Reconciliation_Summary.csv"
S7E_BUY = ROOT / "05_outputs" / "launch_step7e" / "DemandIQ_Step7E_Initial_Buy_Plan.csv"
S7E_WEEKLY = ROOT / "05_outputs" / "launch_step7e" / "DemandIQ_Step7E_Launch_Weekly_Actuals.csv"
S7E_CHECK = ROOT / "05_outputs" / "launch_step7e" / "DemandIQ_Step7E_Checkpoint_Reforecast.csv"
S7E_DECIS = ROOT / "05_outputs" / "launch_step7e" / "DemandIQ_Step7E_Planner_Decisions.csv"
OUTDIR = Path(os.environ.get("STEP7F_OUTDIR", str(ROOT / "05_outputs" / "launch_step7f")))
OUTDIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# FROZEN launch decisions carried forward exactly (7B/7C/7D/7E)
# ============================================================
APS_W, IMH_W = 0.60, 0.40           # analog blend (SHAPE) - frozen 7B
LAUNCH_SCALE_FACTOR = 0.60          # governed first-season scale - frozen 7B/7C
SECOND_SEASON_FACTOR = 1.00         # flat second-season run-rate - frozen 7B
PLANNED_MIX = {"ECOM": 0.45, "RETAIL": 0.35, "WHOLESALE": 0.20}  # frozen 45/35/20
LAUNCH_DATE = pd.Timestamp("2026-08-31")   # Monday, ISO wk36

# Cycle framework
CYCLE01 = "CYCLE_01_2026-08"
CYCLE01_ASOF = "2026-08-24"
CYCLE02 = "CYCLE_02_2026-09"
CYCLE02_ASOF = "2026-09-28"         # end of W4; September complete under Thursday-month rule
EVIDENCE_CUTOFF = "W4"              # HARD gate for the operational Cycle-02 branch

# Method B - lifecycle attenuation of the W4 forward revision.
# NOTE: 1.00 / 0.50 / 0.25 are SYNTHETIC ROLLING-FORECAST GOVERNANCE ASSUMPTIONS.
# The lifecycle phases provide the STRUCTURE for attenuation; the exact weights are
# NOT statistically estimated / NOT empirically validated. Rationale: W4 evidence is
# most informative for the immediate launch season, confidence decays with forecast
# distance, and four observed weeks cannot fully determine the next Fall/Winter season.
PHASE_WEIGHT = {
    "LAUNCH": 1.00, "RAMP": 1.00, "SEASONAL PEAK": 1.00,   # remaining first-season peak
    "NORMALIZATION": 0.50,                                 # partial carry
    "SECOND-SEASON / MATURATION": 0.25,                    # small carry
}

# Policy sensitivity: counterfactual REALLOCATE thresholds (frozen historical rule = 8.0pp)
POLICY_THRESHOLDS_PP = [5.0, 6.5, 8.0]
RESERVE_TRANSFER_LEAD_WEEKS = 2     # frozen 7E synthetic reserve/transfer lead

TRUTH_TYPE = "LATENT_SYNTHETIC_DEMAND (Step7E seed=7, EVALUATION-ONLY)"


# ============================================================
# Metric helpers (governed sign conventions)
# ============================================================
def wape(F, A):
    A = np.asarray(A, float); F = np.asarray(F, float)
    return float(np.abs(F - A).sum() / A.sum() * 100.0)

def bias(F, A):
    A = np.asarray(A, float); F = np.asarray(F, float)
    return float((F - A).sum() / A.sum() * 100.0)   # sum(F-A)/sum(A)*100

def mae(F, A):
    A = np.asarray(A, float); F = np.asarray(F, float)
    return float(np.abs(F - A).mean())

def err_units(F, A):
    A = np.asarray(A, float); F = np.asarray(F, float)
    return float((F - A).sum())


def month_phase(period_str):
    """7C lifecycle calendar (identical logic; reused for governance consistency)."""
    s = str(period_str)
    if s == "2026-09":
        return "LAUNCH"
    if s in ("2026-10", "2026-11"):
        return "RAMP"
    if s == "2026-12":
        return "SEASONAL PEAK"
    if "2027-01" <= s <= "2027-06":
        return "NORMALIZATION"
    return "SECOND-SEASON / MATURATION"   # 2027-07 .. 2028-03


def qa(cond, msg):
    assert cond, "QA FAIL: " + msg


# ============================================================
# PART A - load frozen evidence
# ============================================================
def load_evidence():
    ev = {}

    # ---- V0 13-week weekly shape (BASE/NORMAL) from frozen Step 7C ----
    c13 = pd.read_csv(S7C_13W)
    base = c13[(c13.launch_scenario == "BASE") & (c13.weather_scenario == "NORMAL")]
    v0_week = base.groupby("launch_week_number").analytical_baseline_units.sum().sort_index()
    qa(list(v0_week.index) == list(range(1, 14)), "V0 must cover launch weeks 1..13")
    ev["v0_week"] = v0_week                                  # pd.Series index 1..13

    # ---- exact frozen Step 7D level factors (V1/V0, V2/V0, V3/V0) ----
    recon = pd.read_csv(S7D_RECON)
    tot = recon[recon.planning_month == "TOTAL_18M"].iloc[0]
    v0_18 = float(tot.v0_units); v1_18 = float(tot.v1_units); v2_18 = float(tot.v2_consensus_units)
    ev["f_v1"] = v1_18 / v0_18          # ~1.10903
    ev["f_v2"] = v2_18 / v0_18          # ~1.10000
    ev["f_v3"] = v2_18 / v0_18          # V3 == V2 (approved == consensus)

    # ---- 7E weekly actuals: V3 weekly plan, latent truth, observed sales ----
    w = pd.read_csv(S7E_WEEKLY)
    v3_week = w.groupby("launch_week_number").planned_units_approved.sum().sort_index()
    latent_week = w.groupby("launch_week_number").latent_demand_units_HIDDEN_EVAL_ONLY.sum().sort_index()
    observed_week = w.groupby("launch_week_number").observed_sales_units.sum().sort_index()
    ev["v3_week"] = v3_week
    ev["latent_week"] = latent_week           # EVAL-ONLY
    ev["observed_week"] = observed_week
    ev["weekly_raw"] = w

    # frozen Step 7E outcome values derived from evidence (NOT magic constants)
    ecom_lost = float(w[w.channel_id == "ECOM"].lost_demand_units.sum())   # ~158.8 (W13 stockout)
    ev["ecom_lost"] = ecom_lost

    buy = pd.read_csv(S7E_BUY)
    rec = buy[buy.recommended_flag == 1]
    qa(len(rec) == 1, "exactly one recommended/BALANCED initial-buy row in Step 7E")
    ev["reserve_units"] = float(rec.reserve_units.iloc[0])                 # ~991 idle flex reserve
    qa(950.0 <= ev["reserve_units"] <= 1050.0, f"reserve reconstructed ~991 (got {ev['reserve_units']:.1f})")
    qa(100.0 <= ecom_lost <= 250.0, f"ECOM lost reconstructed ~159 (got {ecom_lost:.1f})")

    # September (W1-W4) observed by channel  -> ACTUALIZED_PERIOD (operational, no hidden truth)
    sep = w[w.launch_week_number <= 4]
    ev["sep_observed_by_channel"] = sep.groupby("channel_id").observed_sales_units.sum()
    # sanity: no stockout censoring occurred within W1-W4 (so observed == demand there)
    ev["sep_had_stockout"] = int((sep.stockout_flag == 1).any())

    # ---- 7E checkpoint reforecast totals + planner cumulative observed ----
    chk = pd.read_csv(S7E_CHECK)
    dec = pd.read_csv(S7E_DECIS)
    cum = {int(r.launch_week_number): float(r.cum_observed_units) for r in dec.itertuples()}
    reftot = {}
    for r in chk.itertuples():
        v = r.forecast_version
        if v == "ORIGINAL_V3_PLAN":
            continue
        wk = int(v.split("_")[0][1:])          # 'W4_REFORECAST' -> 4
        reftot[wk] = float(r.remaining_horizon_units)
    ev["cum_observed"] = cum                    # {1,2,4,8,13: cum obs}
    ev["reforecast_total"] = reftot             # {1,2,4,8,13: observed-to-date + fcast-of-remaining}
    ev["mix_dev_by_cp"] = {int(r.launch_week_number): float(r.max_channel_mix_dev_pp) for r in dec.itertuples()}
    ev["mix_channel_by_cp"] = {int(r.launch_week_number): str(r.max_dev_channel) for r in dec.itertuples()}

    # ---- Cycle-01 V3 approved monthly plan (Month x Channel) from frozen Step 7D ----
    vers = pd.read_csv(S7D_VERS)
    v3 = vers[vers.forecast_version == "V3_APPROVED_PLAN"].copy()
    ev["v3_monthly"] = (v3.groupby(["planning_month", "channel_id"], as_index=False)
                          .forecast_units.sum())
    ev["v3_18m_total"] = float(v3.forecast_units.sum())

    # ---- frozen cold-start seasonal foundation (for the NEW March-2028 month) ----
    ev["seasonal"] = build_seasonal_foundation()
    return ev


def split_observed_vs_forward(cp, ev):
    """Shared helper (spine of Part C and Part D).

    The 7E checkpoint file stores full-horizon totals = observed-to-date + forecast-of-remaining,
    NOT weeks-remaining-only. Recover the forward-only quantity and distribute it across the
    still-FUTURE weeks using the frozen ORIGINAL V3 weekly shape. Score nothing already observed.
    """
    total = ev["reforecast_total"][cp]
    cum = ev["cum_observed"][cp]
    forward_total = total - cum                       # forecast of remaining weeks only
    future_weeks = list(range(cp + 1, 14))
    v3_shape = ev["v3_week"].loc[future_weeks]
    v3_rem_total = float(v3_shape.sum())
    if v3_rem_total <= 0:                              # W13: no remaining horizon
        return forward_total, future_weeks, None, None, v3_rem_total
    reforecast_future = (forward_total * v3_shape / v3_rem_total)   # distribute by ORIGINAL V3 shape
    return forward_total, future_weeks, reforecast_future, v3_shape, v3_rem_total


def w4_forward_revision(ev):
    """Operational W4 evidence signal for Cycle 02 (uses ONLY info through W4).

    revision = (W4 forecast-of-remaining W5-13) / (original V3 W5-13) - 1.
    This is the FORWARD signal (~-6.13%), NOT the -7.2% full-horizon headline that
    mixes in already-actualized weeks.
    """
    fwd_total, _, _, _, v3_rem = split_observed_vs_forward(4, ev)
    return fwd_total / v3_rem - 1.0


# ============================================================
# Frozen cold-start seasonal foundation (identical to Step 7C methodology)
# ============================================================
def build_seasonal_foundation():
    """Reproduce Step 7C's frozen seasonal engine so a NEW far-horizon month can be
    generated from methodology (NOT reverse-engineered from 18M lifecycle-treated values).

    Returns dict with: blended 52-week profile, share(iso) fn, his_base_annual scale.
    """
    df = pd.read_csv(ECON)
    # week_of_year must equal ISO week (so future launch weeks map correctly)
    chk = pd.to_datetime(df["week_start"]).dt.isocalendar().week.astype(int)
    qa((chk == df["week_of_year"]).all(), "week_of_year must equal ISO week (seasonal source)")

    def prof(sku):
        s = df[df.sku_id == sku].groupby("week_of_year").sku_seasonality_factor.mean()
        return s / s.sum()
    blended = APS_W * prof("APS-001") + IMH_W * prof("IMH-001")
    qa(abs(blended.sum() - 1.0) < 1e-9, "blended seasonal profile must sum to 1.00")

    def share(iso):
        return float(blended.get(53, blended.loc[52]) if iso == 53 else blended.loc[iso])

    nyears = df.week_start.nunique() / 52.0
    ann = df.groupby("sku_id").weekly_plan_units.sum() / nyears
    his_base_annual = (APS_W * float(ann["APS-001"]) + IMH_W * float(ann["IMH-001"])) * LAUNCH_SCALE_FACTOR
    return {"share": share, "his_base_annual": his_base_annual, "blended": blended}


def generate_month_v0(period_str, seasonal):
    """Governed V0 (analytical Base) SKU-total for a calendar month, second-season basis.

    Same engine as Step 7C weeks>52: sku_units = his_base_annual * share(iso) * SECOND_SEASON_FACTOR,
    Monday-week assigned to a month by its Thursday. Deterministic; no HIS actuals used.
    """
    target = pd.Period(period_str, freq="M")
    total = 0.0
    n_weeks = 0
    for i in range(120):                              # scan enough Monday-weeks
        ws = LAUNCH_DATE + pd.Timedelta(weeks=i)
        thu = ws + pd.Timedelta(days=3)
        if thu.to_period("M") == target:
            iso = int(ws.isocalendar().week)
            total += seasonal["his_base_annual"] * seasonal["share"](iso) * SECOND_SEASON_FACTOR
            n_weeks += 1
        if thu.to_period("M") > target:
            break
    return total, n_weeks


# ============================================================
# PART B - fair 13-week V0/V1/V2/V3 FVA (RETROSPECTIVE branch)
# ============================================================
def part_b_version_fva(ev):
    A = ev["latent_week"].loc[range(1, 14)].values            # EVAL-ONLY latent truth, W1-13
    v0 = ev["v0_week"].loc[range(1, 14)].values
    versions = [("V0_ANALYTICAL_BASELINE", 1.0, None),
                ("V1_COMMERCIAL_PLAN", ev["f_v1"], "V0_ANALYTICAL_BASELINE"),
                ("V2_CONSENSUS_FORECAST", ev["f_v2"], "V1_COMMERCIAL_PLAN"),
                ("V3_APPROVED_PLAN", ev["f_v3"], "V2_CONSENSUS_FORECAST")]
    wapes = {}
    rows = []
    for name, fac, prior in versions:
        F = v0 * fac
        wp = wape(F, A); wapes[name] = wp
        fva = "" if prior is None else round(wapes[prior] - wp, 3)
        if prior is None:
            status = "BASELINE_ANCHOR"
        elif fva > 0:
            status = "ACCURACY_IMPROVED"
        elif fva < 0:
            status = "ACCURACY_WORSENED"
        else:
            status = "NO_ACCURACY_CHANGE"
        note = ("frozen Step7C BASE/NORMAL weekly shape" if name.startswith("V0")
                else f"V0 shape x frozen Step7D level factor {fac:.5f}")
        if name == "V3_APPROVED_PLAN":
            note += "; V3==V2 (approved==consensus) so FVA logically 0.0"
        rows.append(dict(forecast_stage=name, forecast_as_of=CYCLE01_ASOF,
                         evaluation_start="W1", evaluation_end="W13", evaluation_weeks=13,
                         WAPE=round(wp, 3), Bias=round(bias(F, A), 3), MAE=round(mae(F, A), 2),
                         error_units=round(err_units(F, A), 1), prior_stage=(prior or ""),
                         FVA_WAPE_pp=fva, FVA_status=status, evaluation_truth_type=TRUTH_TYPE,
                         notes=note))
    # cumulative intervention effect V0 -> V3
    fva_cum = round(wapes["V0_ANALYTICAL_BASELINE"] - wapes["V3_APPROVED_PLAN"], 3)
    rows.append(dict(forecast_stage="V3_vs_V0_CUMULATIVE", forecast_as_of=CYCLE01_ASOF,
                     evaluation_start="W1", evaluation_end="W13", evaluation_weeks=13,
                     WAPE=round(wapes["V3_APPROVED_PLAN"], 3), Bias="", MAE="", error_units="",
                     prior_stage="V0_ANALYTICAL_BASELINE", FVA_WAPE_pp=fva_cum,
                     FVA_status=("ACCURACY_WORSENED" if fva_cum < 0 else "ACCURACY_IMPROVED"),
                     evaluation_truth_type=TRUTH_TYPE,
                     notes="cumulative planning-intervention effect; SIM CAVEAT: generator centered on V0"))
    return rows, wapes


# ============================================================
# PART C - checkpoint reforecast FVA (RETROSPECTIVE branch, strict temporal fairness)
# ============================================================
def part_c_checkpoint_fva(ev):
    rows = []
    for cp in (1, 2, 4, 8, 13):
        if cp == 13:
            rows.append(dict(forecast_stage="W13_REFORECAST", forecast_as_of="W13",
                             evaluation_start="", evaluation_end="", evaluation_weeks=0,
                             WAPE="", Bias="", MAE="", error_units="", prior_stage="ORIGINAL_V3_PLAN",
                             FVA_WAPE_pp="", FVA_status="NOT_MEASURABLE_NO_REMAINING_HORIZON",
                             evaluation_truth_type=TRUTH_TYPE,
                             notes="reforecast created at final week; no future launch horizon remains"))
            continue
        fwd_total, future_weeks, reF, v3_shape, v3_rem = split_observed_vs_forward(cp, ev)
        A = ev["latent_week"].loc[future_weeks].values        # EVAL-ONLY, future weeks only
        F_re = reF.values
        F_v3 = v3_shape.values                                # original V3 plan, same future weeks
        w_re = wape(F_re, A); w_v3 = wape(F_v3, A)
        fva = round(w_v3 - w_re, 3)                            # WAPE(orig V3) - WAPE(reforecast)
        status = "ACCURACY_IMPROVED" if fva > 0 else ("ACCURACY_WORSENED" if fva < 0 else "NO_ACCURACY_CHANGE")
        rows.append(dict(forecast_stage=f"W{cp}_REFORECAST", forecast_as_of=f"W{cp}",
                         evaluation_start=f"W{cp+1}", evaluation_end="W13", evaluation_weeks=len(future_weeks),
                         WAPE=round(w_re, 3), Bias=round(bias(F_re, A), 3), MAE=round(mae(F_re, A), 2),
                         error_units=round(err_units(F_re, A), 1), prior_stage="ORIGINAL_V3_PLAN",
                         FVA_WAPE_pp=fva, FVA_status=status, evaluation_truth_type=TRUTH_TYPE,
                         notes=(f"forward-only={fwd_total:.1f} (=reforecast_total-cum_observed) "
                                f"distributed by ORIGINAL V3 shape; baseline=orig V3 same weeks "
                                f"(WAPE {w_v3:.2f}%)")))
    return rows


# ============================================================
# PART D/E - temporally valid Cycle 02 (OPERATIONAL branch, W1-W4 info ONLY) + roll
# ============================================================
def part_d_cycle02(ev):
    revision = w4_forward_revision(ev)                        # ~ -0.0613 (W4-only forward signal)
    seasonal = ev["seasonal"]
    v3m = ev["v3_monthly"].copy()
    v3m["pm"] = v3m.planning_month.astype(str)

    # continuing months = Cycle-01 months minus dropped September
    cont_months = sorted(m for m in v3m.pm.unique() if m != "2026-09")   # Oct2026 .. Feb2028 (17)
    prov_cont = (f"DERIVED: Cycle-01 V3 approved x Method-B lifecycle attenuation of W4 forward "
                 f"revision {revision:+.4f}; SYNTHETIC ROLLING-FORECAST GOVERNANCE WEIGHTS 1.00/0.50/0.25")
    rows = []

    # ---- ACTUALIZED September (separate; NOT one of the 18 forward months) ----
    for ch in ("ECOM", "RETAIL", "WHOLESALE"):
        prev = float(v3m[(v3m.pm == "2026-09") & (v3m.channel_id == ch)].forecast_units.iloc[0])
        act = float(ev["sep_observed_by_channel"].get(ch, 0.0))
        rows.append(dict(planning_cycle=CYCLE02, forecast_as_of_date=CYCLE02_ASOF,
                         planning_month="2026-09", horizon_month_number=0, sku_id="HIS-001",
                         channel_id=ch, previous_cycle_units=round(prev, 2),
                         cycle02_units=round(act, 2), revision_units=round(act - prev, 2),
                         revision_pct=round((act / prev - 1) * 100, 3) if prev else "",
                         lifecycle_phase="ACTUALIZED (LAUNCH month)", evidence_cutoff=EVIDENCE_CUTOFF,
                         forecast_version="ACTUALIZED_PERIOD",
                         provenance=("ACTUALIZED from W1-W4 observed sales (operational; no hidden "
                                     "truth). September complete under Thursday-month rule.")))

    # ---- 17 continuing forward months (shift one horizon closer) ----
    for pm in cont_months:
        phase = month_phase(pm)
        weight = PHASE_WEIGHT[phase]
        factor = 1.0 + weight * revision
        for ch in ("ECOM", "RETAIL", "WHOLESALE"):
            prev = float(v3m[(v3m.pm == pm) & (v3m.channel_id == ch)].forecast_units.iloc[0])
            new = prev * factor
            rows.append(dict(planning_cycle=CYCLE02, forecast_as_of_date=CYCLE02_ASOF,
                             planning_month=pm, horizon_month_number=None, sku_id="HIS-001",
                             channel_id=ch, previous_cycle_units=round(prev, 2),
                             cycle02_units=round(new, 2), revision_units=round(new - prev, 2),
                             revision_pct=round((new / prev - 1) * 100, 3),
                             lifecycle_phase=phase, evidence_cutoff=EVIDENCE_CUTOFF,
                             forecast_version="CYCLE_02_ANALYTICAL_UPDATE", provenance=prov_cont))

    # ---- NEW far-horizon month: March 2028 (generated from FROZEN methodology) ----
    # Built on the SAME approved planning basis as the continuing months for a consistent
    # rolling forecast: V0 analytical (frozen 7C cold-start seasonality) x frozen Step 7D V3/V0
    # factor (the approved-plan basis) x Cycle-02 second-season evidence attenuation.
    mar_v0_sku, n_wk = generate_month_v0("2028-03", seasonal)   # V0 Base analytical foundation
    phase_mar = month_phase("2028-03")                          # SECOND-SEASON / MATURATION
    factor_mar = 1.0 + PHASE_WEIGHT[phase_mar] * revision       # 0.25 x W4 forward revision
    mar_v3_sku = mar_v0_sku * ev["f_v3"]                        # approved (V3) planning basis
    for ch in ("ECOM", "RETAIL", "WHOLESALE"):
        new = mar_v3_sku * PLANNED_MIX[ch] * factor_mar
        rows.append(dict(planning_cycle=CYCLE02, forecast_as_of_date=CYCLE02_ASOF,
                         planning_month="2028-03", horizon_month_number=None, sku_id="HIS-001",
                         channel_id=ch, previous_cycle_units="", cycle02_units=round(new, 2),
                         revision_units="", revision_pct="", lifecycle_phase=phase_mar,
                         evidence_cutoff=EVIDENCE_CUTOFF, forecast_version="CYCLE_02_NEW_HORIZON_MONTH",
                         provenance=(f"NEW month generated from FROZEN cold-start seasonal foundation "
                                     f"(0.60 APS+0.40 IMH, {n_wk} Thursday-weeks, V0 Base scale, "
                                     f"second-season 1.00, 45/35/20) x frozen V3/V0={ev['f_v3']:.5f} "
                                     f"(approved-plan basis, consistent with continuing months) "
                                     f"x 0.25 W4 attenuation. No literal Cycle-01 value (did not exist).")))

    df = pd.DataFrame(rows)
    # assign horizon numbers 1..18 to the forward Oct2026..Mar2028 months (Sep2026 stays 0)
    fwd = df[df.forecast_version != "ACTUALIZED_PERIOD"].copy()
    order = {pm: i + 1 for i, pm in enumerate(sorted(fwd.planning_month.unique()))}
    df.loc[df.forecast_version != "ACTUALIZED_PERIOD", "horizon_month_number"] = \
        df.loc[df.forecast_version != "ACTUALIZED_PERIOD", "planning_month"].map(order)
    df["horizon_month_number"] = df["horizon_month_number"].astype(int)
    df = df.sort_values(["horizon_month_number", "channel_id"]).reset_index(drop=True)
    return df, revision, mar_v0_sku


# ============================================================
# PART F - lifecycle handoff eligibility
# ============================================================
def part_f_handoff(ev):
    observed_weeks = 13
    # data-quality gates (governed)
    w = ev["weekly_raw"]
    weeks_ok = int(w.launch_week_number.nunique() == 13)
    channels_ok = int(set(w.channel_id.unique()) == {"ECOM", "RETAIL", "WHOLESALE"})
    no_neg = int((w.observed_sales_units >= 0).all() and w.observed_sales_units.notna().all())
    availability_flag = "CENSORED_W13_ECOM_STOCKOUT (demand reconstruction required before handoff)"
    status = "EARLY_LAUNCH"     # 1-13 weeks
    # as-of = immediately AFTER the 13-week launch window completes (W13 starts 2026-11-23)
    row = dict(sku_id="HIS-001", as_of_date="2026-11-30", observed_weeks=observed_weeks,
               current_lifecycle_status=status,
               one_season_history_flag="NO (need >=52 clean weeks)",
               mature_104w_eligible_flag="NO (need >=104 clean weeks AND all data-quality gates)",
               calendar_quality_flag=("PASS 13/13 weekly calendar complete" if weeks_ok else "FAIL"),
               availability_quality_flag=availability_flag,
               channel_coverage_flag=("PASS all 3 channels" if channels_ok else "FAIL"),
               recommended_forecast_method="ANALOG (0.60 APS+0.40 IMH) + actual-evidence blend; NO ETS/SARIMA yet",
               next_handoff_review="At 52-week milestone (begin own-season diagnostics)",
               handoff_reason=("13 observed launch weeks << 52-week seasonal milestone and 104-week "
                               "mature-engine milestone; W13 ECOM stockout means observed sales are "
                               "censored, not full demand; product remains EARLY_LAUNCH / maturing. "
                               "Do NOT fit the mature ETS/SARIMA engine or auto-assign the APS/IMH model."))
    qa(no_neg == 1, "no negative/null observed sales in launch actuals")
    # lifecycle stage ladder (for the decision record / transparency)
    ladder = pd.DataFrame([
        dict(lifecycle_status="COLD_START", weeks="0", meaning="pre-launch; analog-only"),
        dict(lifecycle_status="EARLY_LAUNCH", weeks="1-13", meaning="launch window; analog+evidence (HIS-001 NOW)"),
        dict(lifecycle_status="MATURING_LAUNCH", weeks="14-51", meaning="ramp/normalization; still analog-blended"),
        dict(lifecycle_status="SEASONAL_HISTORY_AVAILABLE", weeks=">=52", meaning="one own-season cycle; begin diagnostics"),
        dict(lifecycle_status="MATURE_MODEL_ELIGIBLE", weeks=">=104 + gates", meaning="frozen mature-engine validation/champion selection"),
    ])
    return row, ladder


# ============================================================
# PART G - counterfactual REALLOCATE-threshold policy sensitivity
# ============================================================
def part_g_policy(ev):
    """Retrospective diagnostic on the FROZEN Step 7E realized path. Does NOT change history.
    Every row labelled COUNTERFACTUAL POLICY SENSITIVITY. No optimality/causality claims.
    """
    # max sustained ECOM mix deviation on the frozen path (per checkpoint): +5.4pp (W1-W8), +4.2pp (W13)
    cp_order = [1, 2, 4, 8, 13]
    cp_week = {1: 1, 2: 2, 4: 4, 8: 8, 13: 13}
    reserve_idle = ev["reserve_units"]   # frozen idle flex reserve (from Step 7E buy plan; never deployed)
    ecom_lost = ev["ecom_lost"]          # frozen realized ECOM stockout-censored demand (from 7E actuals)
    rows = []
    for thr in POLICY_THRESHOLDS_PP:
        first_cp = None
        for cp in cp_order:
            if ev["mix_dev_by_cp"][cp] >= thr and ev["mix_channel_by_cp"][cp] == "ECOM":
                first_cp = cp
                break
        if first_cp is None:
            rows.append(dict(threshold_pp=thr, would_trigger="NO", first_trigger_checkpoint="",
                             first_trigger_week="", trigger_channel="", mix_dev_at_trigger_pp="",
                             reserve_available_units=reserve_idle, indicative_deployable_units="",
                             reserve_transfer_lead_weeks=RESERVE_TRANSFER_LEAD_WEEKS,
                             plausibly_arrives_before_w13_stockout="",
                             label="COUNTERFACTUAL POLICY SENSITIVITY",
                             notes=(f"max ECOM mix deviation on frozen path (5.4pp) never reaches "
                                    f"{thr}pp; rule would not fire. (8.0pp = frozen historical rule.)")))
        else:
            wk = cp_week[first_cp]
            arrives_wk = wk + RESERVE_TRANSFER_LEAD_WEEKS
            plausible = "YES" if arrives_wk <= 13 else "NO"
            indic = min(reserve_idle, ecom_lost)     # indicative only; ECOM shortfall ~159
            rows.append(dict(threshold_pp=thr, would_trigger="YES", first_trigger_checkpoint=f"W{first_cp}",
                             first_trigger_week=wk, trigger_channel="ECOM",
                             mix_dev_at_trigger_pp=ev["mix_dev_by_cp"][first_cp],
                             reserve_available_units=reserve_idle, indicative_deployable_units=round(indic, 1),
                             reserve_transfer_lead_weeks=RESERVE_TRANSFER_LEAD_WEEKS,
                             plausibly_arrives_before_w13_stockout=plausible,
                             label="COUNTERFACTUAL POLICY SENSITIVITY",
                             notes=(f"ECOM mix +{ev['mix_dev_by_cp'][first_cp]}pp >= {thr}pp at W{first_cp}; "
                                    f"idle reserve {reserve_idle:.0f}u could indicatively cover the ~{ecom_lost:.0f}u "
                                    f"W13 ECOM shortfall; ~{RESERVE_TRANSFER_LEAD_WEEKS}-wk lead -> arrive ~W{arrives_wk}. "
                                    f"NOT a claim of optimality/causality or that all lost demand is prevented.")))
    return pd.DataFrame(rows)


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("DemandIQ Step 7F - FVA, Rolling Cycle 02 & Lifecycle Handoff (HIS-001)")
    print("=" * 70)
    ev = load_evidence()
    print(f"Frozen level factors: V1/V0={ev['f_v1']:.5f}  V2/V0={ev['f_v2']:.5f}  V3/V0={ev['f_v3']:.5f}")
    print(f"V0 13W total={ev['v0_week'].sum():.2f} | V3 13W(plan)={ev['v3_week'].sum():.2f} | "
          f"latent 13W={ev['latent_week'].sum():.2f} | observed 13W={ev['observed_week'].sum():.2f}")

    # ---- RETROSPECTIVE branch ----
    b_rows, wapes = part_b_version_fva(ev)
    c_rows = part_c_checkpoint_fva(ev)
    fva = pd.DataFrame(b_rows + c_rows)

    # ---- OPERATIONAL Cycle-02 branch (W1-W4 info only) ----
    cyc02, revision, mar_v0 = part_d_cycle02(ev)

    # ---- lifecycle handoff ----
    hrow, ladder = part_f_handoff(ev)
    handoff = pd.DataFrame([hrow])

    # ---- policy sensitivity ----
    policy = part_g_policy(ev)

    # ================= QA =================
    # Part B/C FVA
    _pre = ["V0_ANALYTICAL_BASELINE", "V1_COMMERCIAL_PLAN", "V2_CONSENSUS_FORECAST", "V3_APPROVED_PLAN"]
    for _s in _pre:
        _ew = fva[fva.forecast_stage == _s].evaluation_weeks.iloc[0]
        qa(_ew == 13, f"{_s} must evaluate exactly 13 weeks (got {_ew})")
    qa(abs(wapes["V2_CONSENSUS_FORECAST"] - wapes["V3_APPROVED_PLAN"]) < 1e-9, "V2==V3 WAPE (identical forecasts)")
    v3v0 = fva[fva.forecast_stage == "V3_vs_V0_CUMULATIVE"].FVA_WAPE_pp.iloc[0]
    qa(v3v0 < 0, "on this seeded path V0 beats V3 (cumulative FVA negative) - SIM CAVEAT applies")
    w13 = fva[fva.forecast_stage == "W13_REFORECAST"].iloc[0]
    qa(w13.FVA_status == "NOT_MEASURABLE_NO_REMAINING_HORIZON", "W13 not measurable")
    for cp in (1, 2, 4, 8):
        r = fva[fva.forecast_stage == f"W{cp}_REFORECAST"].iloc[0]
        qa(r.evaluation_start == f"W{cp+1}" and r.evaluation_end == "W13", f"W{cp} scored on future weeks only")

    # Cycle 02
    fwd = cyc02[cyc02.forecast_version != "ACTUALIZED_PERIOD"]
    qa(fwd.planning_month.nunique() == 18, "Cycle02 has exactly 18 forward months")
    qa(fwd.planning_month.min() == "2026-10" and fwd.planning_month.max() == "2028-03", "Cycle02 = Oct2026..Mar2028")
    qa("2026-09" not in set(fwd.planning_month), "Sep2026 dropped from forward forecast")
    qa("2028-03" in set(fwd.planning_month), "Mar2028 added as new month")
    qa((cyc02.forecast_as_of_date == CYCLE02_ASOF).all(), "as-of 2026-09-28")
    qa(set(cyc02.channel_id.unique()) == {"ECOM", "RETAIL", "WHOLESALE"}, "3 channels")
    qa(abs(revision - (-0.0613)) < 0.001, f"W4 forward revision ~ -6.13% (got {revision:.4f})")
    # like-for-like rolling overlap must be exactly the 17 shared months Oct2026..Feb2028
    _ovl = [m for m in fwd.planning_month.unique() if "2026-10" <= m <= "2028-02"]
    qa(len(_ovl) == 17, f"like-for-like overlap must be 17 months (got {len(_ovl)})")
    # channel totals reconcile to a positive SKU total per forward month
    smt = fwd.groupby("planning_month").cycle02_units.sum()
    qa((smt > 0).all(), "every Cycle02 forward month has positive SKU total")

    # Handoff
    qa(hrow["observed_weeks"] == 13, "HIS has 13 observed weeks")
    qa("NO" in hrow["mature_104w_eligible_flag"], "mature_model_eligible = NO")

    # Policy
    qa(set(policy.threshold_pp) == set(POLICY_THRESHOLDS_PP), "policy thresholds 5.0/6.5/8.0")
    qa((policy.label == "COUNTERFACTUAL POLICY SENSITIVITY").all(), "policy rows labelled counterfactual")

    # ================= WRITE =================
    p1 = OUTDIR / "DemandIQ_Step7F_FVA_Analysis.csv"
    p2 = OUTDIR / "DemandIQ_Step7F_Cycle02_Rolling_Forecast.csv"
    p3 = OUTDIR / "DemandIQ_Step7F_Lifecycle_Handoff.csv"
    p4 = OUTDIR / "DemandIQ_Step7F_Policy_Sensitivity.csv"
    fva.to_csv(p1, index=False)
    cyc02.to_csv(p2, index=False)
    handoff.to_csv(p3, index=False)
    policy.to_csv(p4, index=False)

    # ================= CONSOLE SUMMARY =================
    print("\n----- PART B: VERSION FVA (W1-13, truth=latent synthetic; EVAL-ONLY) -----")
    for r in b_rows:
        print(f"  {r['forecast_stage']:<24} WAPE={r['WAPE']}%  Bias={r['Bias']}%  FVA_pp={r['FVA_WAPE_pp']}  {r['FVA_status']}")
    print("  SIM CAVEAT: generator centered on V0 -> V0 beating V1/V2/V3 is an illustrative")
    print("              governance demonstration, NOT proof the commercial override was harmful.")

    print("\n----- PART C: CHECKPOINT REFORECAST FVA (forward-only vs orig V3) -----")
    for r in c_rows:
        print(f"  {r['forecast_stage']:<16} eval {r['evaluation_start']}-{r['evaluation_end']:<4} "
              f"WAPE={r['WAPE']}  FVA_pp={r['FVA_WAPE_pp']}  {r['FVA_status']}")

    print(f"\n----- PART D/E: CYCLE 02 (as-of {CYCLE02_ASOF}; W4 fwd revision {revision:+.4f}) -----")
    print(f"  Sep2026 ACTUALIZED (obs W1-4): "
          f"{ev['sep_observed_by_channel'].round(1).to_dict()}  (had stockout: {ev['sep_had_stockout']})")
    print(f"  Forward months: {fwd.planning_month.min()}..{fwd.planning_month.max()} "
          f"({fwd.planning_month.nunique()} months x 3 channels)")
    # ---- like-for-like overlap (Oct2026..Feb2028, 17 mo) vs full rolling-window outlook ----
    overlap_months = [m for m in sorted(fwd.planning_month.unique()) if "2026-10" <= m <= "2028-02"]
    v3m = ev["v3_monthly"].assign(pm=lambda d: d.planning_month.astype(str))
    c1_overlap = float(v3m[v3m.pm.isin(overlap_months)].forecast_units.sum())
    c2_overlap = float(fwd[fwd.planning_month.isin(overlap_months)].cycle02_units.sum())
    c1_full = ev["v3_18m_total"]                              # Cycle01 Sep26-Feb28
    c2_full = float(fwd.cycle02_units.sum())                  # Cycle02 Oct26-Mar28
    print(f"  LIKE-FOR-LIKE overlap Oct2026-Feb2028 ({len(overlap_months)} mo): "
          f"Cycle01 V3={c1_overlap:,.1f} -> Cycle02={c2_overlap:,.1f} "
          f"(revision {c2_overlap-c1_overlap:+,.1f} = {(c2_overlap/c1_overlap-1)*100:+.2f}%)  [pure forecast revision]")
    print(f"  ROLLING-WINDOW OUTLOOK CHANGE: Cycle01 Sep26-Feb28={c1_full:,.1f} -> "
          f"Cycle02 Oct26-Mar28={c2_full:,.1f} (Sep drops, Mar enters; NOT pure forecast revision)")
    print(f"  NEW March2028: V0 base SKU={mar_v0:.1f} x V3/V0={ev['f_v3']:.5f} -> "
          f"Cycle02 SKU={smt.get('2028-03'):.1f} (approved-plan basis, consistent w/ continuing months)")

    print("\n----- PART F: LIFECYCLE HANDOFF -----")
    print(f"  status={hrow['current_lifecycle_status']} | 52w={hrow['one_season_history_flag']} | "
          f"104w={hrow['mature_104w_eligible_flag']}")
    print(f"  method: {hrow['recommended_forecast_method']}")

    print("\n----- PART G: COUNTERFACTUAL POLICY SENSITIVITY (frozen 8.0pp unchanged) -----")
    for r in policy.itertuples():
        print(f"  {r.threshold_pp}pp -> trigger={r.would_trigger} "
              f"{('@'+str(r.first_trigger_checkpoint)) if r.would_trigger=='YES' else ''}")

    print("\nWrote:")
    for p in (p1, p2, p3, p4):
        print("  ", p)
    print("\nALL QA PASSED.")


if __name__ == "__main__":
    main()
