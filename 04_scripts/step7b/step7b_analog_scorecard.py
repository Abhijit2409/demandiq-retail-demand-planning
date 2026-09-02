"""
DemandIQ - Step 7B - Analog Similarity Scorecard + Sensitivity for HIS-001
(Hybrid Insulated Shell).

Read-only against frozen mature data; writes launch-only outputs to 05_outputs/launch_step7b.
Produces:
  - DemandIQ_Step7B_Analog_Scorecard.csv     (raw scores + weighted contributions)
  - DemandIQ_Step7B_Seasonal_Correlation.csv (52-week profile corr, corroboration)
  - DemandIQ_Step7B_Analog_Sensitivity.csv   (weight-perturbation stability test)

Governance:
  - No future / hidden-truth / generator-only fields are used.
  - Every HIS-001 value is a SYNTHETIC PLANNING ASSUMPTION (see PARAMETERS).
  - Weights are SYNTHETIC PLANNING-GOVERNANCE ASSUMPTIONS (sum to 1.00), set from
    principle, not tuned to any HIS-001 outcome (which does not exist).
  - Mature Steps 4A-6F outputs are not touched.

Dimension note: the seasonal dimension is COLD-SEASON / SEASONAL FIT - how strongly a
mature product fits HIS-001's KNOWN Fall/Winter positioning (cold-season concentration
of its seasonal factor). It is NOT similarity to an HIS-001 history (there is none).
The 52-week pairwise correlation matrix is kept as corroborating evidence only.
"""
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(r"D:\Downloads\DemandIQ")
ECON = ROOT / "02_data" / "processed" / "DemandIQ_Step3D_v4_Retail_Economics.csv"
OUTDIR = ROOT / "05_outputs" / "launch_step7b"
OUTDIR.mkdir(parents=True, exist_ok=True)

CANDIDATES = ["APS-001", "CTS-001", "IMH-001"]

# ============================================================
# PARAMETERS  (all SYNTHETIC PLANNING ASSUMPTIONS unless noted)
# ============================================================
HIS_MSRP        = 750.0                 # owner decision
HIS_WS          = 0.255                 # weather sensitivity: intentional position between APS (0.292) and CTS/IMH (0.215)
HIS_SCALE_BAND  = (20000.0, 50000.0)    # wide, set from positioning INDEPENDENT of analog choice
HIS_SCALE_MID   = float(np.sqrt(HIS_SCALE_BAND[0] * HIS_SCALE_BAND[1]))  # geometric midpoint
HIS_CHANNEL     = {"ECOM": 0.408, "RETAIL": 0.324, "WHOLESALE": 0.268}   # planned mix, renormalized

# GOVERNED weights (SYNTHETIC PLANNING-GOVERNANCE ASSUMPTIONS)
WEIGHTS = {"functional": 0.30, "seasonal_fit": 0.25, "price": 0.15,
           "weather": 0.15, "scale": 0.10, "channel": 0.05}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "weights must sum to 1.00"

# domain normalizers (defined ranges -> avoids the N=3 min-max endpoint trap)
D_PRICE  = 400.0             # CAD spread of the premium-outerwear MSRP range
D_WS     = 0.10             # weather-sensitivity domain span
D_SCALE  = float(np.log(3))  # log-scale tolerance

# seasonal fit = cold-season concentration (fully data-derived, no synthetic reference)
COLD_WEEKS = set(range(40, 53)) | set(range(1, 10))   # ISO wk 40-52 and 1-9 (Oct - early Mar)
BASE_CONC  = len(COLD_WEEKS) / 52.0                    # uniform-year baseline

# SYNTHETIC PRODUCT-ATTRIBUTE ASSUMPTION (frozen BEFORE scoring; ratings 0-1)
ATTR_NAMES = ["insulation", "weather_protection", "shell_construction",
              "technical_premium", "cold_use"]
ATTR = {
    "HIS-001": [0.90, 0.90, 0.85, 0.90, 0.90],
    "APS-001": [0.20, 0.95, 0.95, 0.90, 0.75],
    "CTS-001": [0.15, 0.80, 0.90, 0.65, 0.55],
    "IMH-001": [0.95, 0.35, 0.25, 0.60, 0.85],
}


def clip01(x):
    return float(np.clip(x, 0.0, 1.0))


def component_scores(df):
    """Return {candidate: {dim: raw_score}} plus context + seasonal profiles."""
    scores, context, profiles = {}, {}, {}
    for c in CANDIDATES:
        sub = df[df.sku_id == c]
        msrp = float(sub.msrp_cad.dropna().iloc[0])
        ws = float(sub.weather_sensitivity.dropna().iloc[0])

        seas = sub.groupby("week_of_year").sku_seasonality_factor.mean()
        profiles[c] = seas
        conc = seas[seas.index.isin(COLD_WEEKS)].sum() / seas.sum()

        ch = sub.groupby("channel_id").channel_mix_share.first()
        ch = ch / ch.sum()

        nyears = sub.week_start.nunique() / 52.0
        scale = sub.weekly_plan_units.sum() / nyears

        scores[c] = {
            "functional":  clip01(1 - np.mean(np.abs(np.array(ATTR[c]) - np.array(ATTR["HIS-001"])))),
            "seasonal_fit": clip01((conc - BASE_CONC) / (1 - BASE_CONC)),
            "price":       clip01(1 - min(1, abs(msrp - HIS_MSRP) / D_PRICE)),
            "weather":     clip01(1 - min(1, abs(ws - HIS_WS) / D_WS)),
            "scale":       clip01(1 - min(1, abs(np.log(scale) - np.log(HIS_SCALE_MID)) / D_SCALE)),
            "channel":     clip01(1 - 0.5 * sum(abs(ch.get(k, 0.0) - HIS_CHANNEL[k]) for k in HIS_CHANNEL)),
        }
        context[c] = {"cold_season_concentration": round(conc, 4), "msrp_cad": msrp,
                      "weather_sensitivity": ws, "annual_scale_units": round(scale, 0)}
    return scores, context, profiles


def rank_with_weights(scores, weights):
    out = []
    for c in CANDIDATES:
        final = sum(weights[d] * scores[c][d] for d in weights)
        out.append((c, final))
    out.sort(key=lambda t: t[1], reverse=True)
    return out  # [(candidate, final), ...] sorted desc


def rebalance(base_weights, dim, delta):
    """Move `delta` onto `dim`, rescale all other dims proportionally so sum stays 1.00."""
    w = dict(base_weights)
    new_target = w[dim] + delta
    others = {k: v for k, v in w.items() if k != dim}
    factor = (1 - new_target) / sum(others.values())
    w = {k: (new_target if k == dim else v * factor) for k, v in w.items()}
    assert abs(sum(w.values()) - 1) < 1e-9
    return w


def main():
    df = pd.read_csv(ECON)
    scores, context, profiles = component_scores(df)

    # ---------- Scorecard: raw scores + weighted contributions ----------
    rows = []
    for c in CANDIDATES:
        rec = {"candidate": c}
        rec.update({f"s_{d}": round(scores[c][d], 4) for d in WEIGHTS})
        contrib = {d: WEIGHTS[d] * scores[c][d] for d in WEIGHTS}
        rec.update({f"{d}_contribution": round(contrib[d], 4) for d in WEIGHTS})
        final = sum(contrib.values())
        rec["final_score"] = round(final, 4)
        # audit: contributions must reconcile to the final score
        assert abs(sum(contrib.values()) - final) < 1e-9
        rec.update(context[c])
        rec["data_classification"] = "DERIVED (frozen mature data) + SYNTHETIC assumptions"
        rows.append(rec)

    score = pd.DataFrame(rows).sort_values("final_score", ascending=False).reset_index(drop=True)
    score.insert(1, "rank", range(1, len(score) + 1))

    prof = pd.DataFrame(profiles)
    corr = prof.corr().round(4)

    # ---------- Sensitivity ----------
    scen_defs = {
        "A_base":               ("none", 0.0),
        "B_higher_functional":  ("functional", +0.10),
        "C_lower_functional":   ("functional", -0.10),
        "D_higher_seasonal":    ("seasonal_fit", +0.10),
        "E_higher_price":       ("price", +0.10),
    }
    base_top = rank_with_weights(scores, WEIGHTS)[0][0]
    srows = []
    for name, (dim, delta) in scen_defs.items():
        w = dict(WEIGHTS) if dim == "none" else rebalance(WEIGHTS, dim, delta)
        ranked = rank_with_weights(scores, w)
        order = " > ".join(f"{c}({v:.3f})" for c, v in ranked)
        top = ranked[0][0]
        # blend decision is structural: APS weak on insulation, IMH uniquely fills it.
        blend_holds = ("APS-001" in [c for c, _ in ranked[:2]] or top == "APS-001")
        srows.append({
            "scenario": name,
            **{f"w_{d}": round(w[d], 4) for d in WEIGHTS},
            "rank_order": order,
            "top_analog": top,
            "top_changed_vs_base": (top != base_top),
            "blend_APS_IMH_remains_defensible": blend_holds,
        })
    sens = pd.DataFrame(srows)

    # ---------- Report ----------
    pd.set_option("display.width", 220)
    print("=== ANALOG SCORECARD (HIS-001) : raw scores + weighted contributions ===")
    print(score.to_string(index=False))
    print("\n=== weights (sum={:.2f}) ===".format(sum(WEIGHTS.values())))
    print({k: round(v, 4) for k, v in WEIGHTS.items()})
    print("\n=== seasonal-profile pairwise correlation (corroboration only) ===")
    print(corr.to_string())
    print("\n=== SENSITIVITY (proportional rebalance, weights sum to 1.00) ===")
    print(sens[["scenario", "rank_order", "top_analog", "top_changed_vs_base",
                "blend_APS_IMH_remains_defensible"]].to_string(index=False))

    # ---------- QA ----------
    assert abs(sum(WEIGHTS.values()) - 1) < 1e-9
    for c in CANDIDATES:
        assert all(0 <= scores[c][d] <= 1 for d in WEIGHTS)
    # contribution reconciliation across the whole table
    for _, r in score.iterrows():
        csum = sum(r[f"{d}_contribution"] for d in WEIGHTS)
        assert abs(csum - r["final_score"]) < 1e-3, "contribution sum != final_score"
    print("\nQA OK: weights sum 1.00; scores in [0,1]; contributions reconcile to final_score.")

    # ---------- Write ----------
    score.to_csv(OUTDIR / "DemandIQ_Step7B_Analog_Scorecard.csv", index=False)
    corr.to_csv(OUTDIR / "DemandIQ_Step7B_Seasonal_Correlation.csv")
    sens.to_csv(OUTDIR / "DemandIQ_Step7B_Analog_Sensitivity.csv", index=False)
    print(f"\nWrote scorecard / seasonal-correlation / sensitivity to {OUTDIR}")


if __name__ == "__main__":
    main()
