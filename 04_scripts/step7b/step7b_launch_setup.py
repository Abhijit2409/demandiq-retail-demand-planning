"""
DemandIQ - Step 7B - Launch Setup: 18-month lifecycle calendar + governed
launch-assumption register for HIS-001.

Writes launch-only outputs (no forecast units are produced here):
  - DemandIQ_Step7B_Lifecycle_Calendar.csv
  - DemandIQ_Step7B_Launch_Assumptions.csv

All values are traceable via the `provenance` column:
  DERIVED (frozen mature data) | SYNTHETIC PLANNING ASSUMPTION |
  GOVERNANCE ASSUMPTION | NOT YET SET (Step 7D).
Mature Steps 4A-6F outputs are not touched.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(r"D:\Downloads\DemandIQ")
OUTDIR = ROOT / "05_outputs" / "launch_step7b"
OUTDIR.mkdir(parents=True, exist_ok=True)

LAUNCH_DATE = "2026-08-31"

# ---- decided Step 7B values (informed by the corrected scorecard + planner review) ----
PRIMARY_ANALOG, PRIMARY_W = "APS-001", 0.60
SECONDARY_ANALOG, SECONDARY_W = "IMH-001", 0.40
assert abs(PRIMARY_W + SECONDARY_W - 1.0) < 1e-9

# analog annual comparable demand (DERIVED from frozen mature data; context only, not a HIS forecast)
APS_ANNUAL, IMH_ANNUAL = 28271.0, 72093.0
BLENDED_ANNUAL = round(PRIMARY_W * APS_ANNUAL + SECONDARY_W * IMH_ANNUAL, 0)  # ~45800

ANALYTICAL_MIX = {"ECOM": 0.408, "RETAIL": 0.324, "WHOLESALE": 0.268}   # blended analog mix (identical across SKUs)
COMMERCIAL_MIX = {"ECOM": 0.45, "RETAIL": 0.35, "WHOLESALE": 0.20}      # DTC-led premium-launch override
assert abs(sum(ANALYTICAL_MIX.values()) - 1) < 1e-9
assert abs(sum(COMMERCIAL_MIX.values()) - 1) < 1e-9

BASE_SCALE_FACTOR = 0.60
LOW_MULT, BASE_MULT, HIGH_MULT = 0.75, 1.00, 1.25
assert LOW_MULT < BASE_MULT < HIGH_MULT


# ============================================================
# 1) 18-month lifecycle calendar
# ============================================================
def month_iter(start_year, start_month, n):
    y, m = start_year, start_month
    for _ in range(n):
        yield y, m
        m += 1
        if m > 12:
            m = 1
            y += 1


def season_of(month):
    return {9: "FALL", 10: "FALL", 11: "FALL", 12: "WINTER", 1: "WINTER", 2: "WINTER",
            3: "SPRING", 4: "SPRING", 5: "SPRING", 6: "SUMMER", 7: "SUMMER", 8: "SUMMER"}[month]


# month_index 0 = pre-launch context (Aug 2026); 1..18 = strategic horizon Sep 2026 -> Feb 2028
def phase_of(idx):
    if idx == 0:
        return "PRE-LAUNCH"
    if idx == 1:
        return "LAUNCH"
    if idx in (2, 3):
        return "RAMP"
    if idx == 4:
        return "SEASONAL PEAK"
    if 5 <= idx <= 10:
        return "NORMALIZATION"
    return "SECOND-SEASON / MATURATION"  # 11..18


NOTES = {
    "PRE-LAUNCH": "Pre-launch prep; context only, outside the 18-month strategic horizon",
    "LAUNCH": "On-sale 2026-08-31; first demand signal begins",
    "RAMP": "Adoption climbs toward the borrowed Fall/Winter analog shape",
    "SEASONAL PEAK": "Cold-season peak (analog peaks ISO wk49, early Dec)",
    "NORMALIZATION": "Post-peak settle and off-season trough",
    "SECOND-SEASON / MATURATION": "Second Fall/Winter build; maturing toward mature-engine handoff",
}

cal_rows = []
# index 0 context row = Aug 2026, then 18 strategic months from Sep 2026
seq = [(2026, 8)] + list(month_iter(2026, 9, 18))
for idx, (y, m) in enumerate(seq):
    phase = phase_of(idx)
    cal_rows.append({
        "planning_month": f"{y}-{m:02d}",
        "month_index": idx,
        "lifecycle_phase": phase,
        "season": season_of(m),
        "notes": NOTES[phase],
        "provenance": "SYNTHETIC PLANNING ASSUMPTION (lifecycle structure; no forecast units)",
    })
cal = pd.DataFrame(cal_rows)
cal.to_csv(OUTDIR / "DemandIQ_Step7B_Lifecycle_Calendar.csv", index=False)

# ============================================================
# 2) Launch assumption register
# ============================================================
SYN = "SYNTHETIC PLANNING ASSUMPTION"
GOV = "GOVERNANCE ASSUMPTION"
DER = "DERIVED (frozen mature data)"
TBD = "NOT YET SET (Step 7D)"


def a(name, value, unit, prov, rationale, owner, status, notes=""):
    return {"assumption_name": name, "value": value, "unit": unit, "provenance": prov,
            "rationale": rationale, "owner_role": owner, "status": status,
            "effective_date": LAUNCH_DATE, "notes": notes}


reg = [
    a("launch_sku", "HIS-001", "id", SYN, "Synthetic launch product for the case study", "Demand Planning", "FROZEN"),
    a("product_name", "Hybrid Insulated Shell", "text", SYN, "Premium technical outerwear: insulation + weather protection", "Demand Planning", "FROZEN"),
    a("launch_date", LAUNCH_DATE, "date", SYN, "Start of fall build; gives 13-wk window into the early-Dec peak and an 18-mo horizon spanning two FW seasons", "Demand Planning", "FROZEN"),
    a("launch_season", "FALL/WINTER (FW26)", "text", SYN, "Cold / transitional use case", "Demand Planning", "FROZEN"),
    a("launch_channels", "ECOM|RETAIL|WHOLESALE", "list", SYN, "Full-channel launch with a DTC-led weighting (see channel mix)", "Sales/Channel", "FROZEN"),
    a("his_msrp_cad", 750.0, "CAD", SYN, "Mid-premium position between IMH (400) and APS (800)", "Merchandising", "FROZEN"),
    a("his_weather_sensitivity", 0.255, "index", SYN, "Intentional position between APS (0.292) and CTS/IMH (0.215) for a hybrid insulated shell", "Demand Planning", "FROZEN"),
    a("functional_attribute_framework", "insulation|weather_protection|shell_construction|technical_premium|cold_use", "list", SYN, "5 named product-attribute ratings frozen BEFORE scoring; drives functional similarity", "Demand Planning", "FROZEN"),
    a("scoring_weights", "func0.30|seas0.25|price0.15|weather0.15|scale0.10|channel0.05", "weights", GOV, "Principle-based, sum=1.00, not tuned to any HIS outcome; 0.55 of weight is data-derived", "Demand Planning", "FROZEN"),
    a("selected_primary_analog", PRIMARY_ANALOG, "id", DER + " + planner review", "Top score (0.679) and STABLE across all sensitivity scenarios; anchors shell/weather, price, scale, FW seasonality", "Demand Planning", "FROZEN"),
    a("selected_secondary_analog", SECONDARY_ANALOG, "id", DER + " + planner override", "Uniquely supplies INSULATION (0.95) - the defining half of an insulated shell - that APS lacks (0.20); shares APS's FW shape (corr 0.99)", "Demand Planning", "FROZEN"),
    a("excluded_candidate", "CTS-001", "id", DER + " + planner review", "Ranked #2 by score but is a redundant shell (insulation 0.15) that does NOT fill APS's insulation gap; adds no complementary information", "Demand Planning", "FROZEN"),
    a("analog_blend_weight_primary", PRIMARY_W, "share", SYN, "APS anchors price/scale/seasonality/positioning; kept primary", "Demand Planning", "FROZEN"),
    a("analog_blend_weight_secondary", SECONDARY_W, "share", SYN, "Insulation is a co-equal defining attribute, so IMH gets substantial (not token) weight", "Demand Planning", "FROZEN"),
    a("analytical_channel_mix_ecom", ANALYTICAL_MIX["ECOM"], "share", DER, "Blended analog channel mix (identical across mature SKUs)", "Demand Planning", "FROZEN"),
    a("analytical_channel_mix_retail", ANALYTICAL_MIX["RETAIL"], "share", DER, "Blended analog channel mix", "Demand Planning", "FROZEN"),
    a("analytical_channel_mix_wholesale", ANALYTICAL_MIX["WHOLESALE"], "share", DER, "Blended analog channel mix; low discriminatory value for selection but relevant for allocation", "Demand Planning", "FROZEN"),
    a("commercial_channel_mix_ecom", COMMERCIAL_MIX["ECOM"], "share", SYN, "DTC-led premium launch: shift toward ECOM", "Merchandising", "FROZEN"),
    a("commercial_channel_mix_retail", COMMERCIAL_MIX["RETAIL"], "share", SYN, "DTC-led premium launch: shift toward RETAIL", "Merchandising", "FROZEN"),
    a("commercial_channel_mix_wholesale", COMMERCIAL_MIX["WHOLESALE"], "share", SYN, "Wholesale deferred/scaled-in after launch proof to protect premium presentation", "Merchandising", "FROZEN"),
    a("final_planned_channel_mix", "ECOM0.45|RETAIL0.35|WHOLESALE0.20", "shares", SYN, "Commercial override retained as the planned launch mix; analytical prior preserved separately", "Demand Planning", "FROZEN"),
    a("blended_analog_annual_comparable_units", BLENDED_ANNUAL, "units/yr", DER, "0.60*APS(28271)+0.40*IMH(72093); analog property used as the scale anchor - NOT a HIS forecast", "Demand Planning", "FROZEN"),
    a("base_launch_scale_factor", BASE_SCALE_FACTOR, "x of blended analog", SYN, "Conservative first-season: premium price, unproven demand, product overlap, DTC-led narrower distribution", "Demand Planning", "FROZEN"),
    a("adoption_multiplier_low", LOW_MULT, "x of Base", SYN, "Weak adoption / analog overstatement", "Demand Planning", "FROZEN"),
    a("adoption_multiplier_base", BASE_MULT, "x of Base", SYN, "Expected launch adoption", "Demand Planning", "FROZEN"),
    a("adoption_multiplier_high", HIGH_MULT, "x of Base", SYN, "Strong adoption / analog understatement; symmetric +-25% band (cost asymmetry handled in the buy buffer, not the demand band)", "Demand Planning", "FROZEN"),
    a("lifecycle_horizon", "2026-09 to 2028-02 (18 months)", "range", SYN, "Spans two Fall/Winter seasons for lifecycle + second-season planning", "Demand Planning", "FROZEN"),
    a("lifecycle_phases", "PRE-LAUNCH|LAUNCH|RAMP|SEASONAL PEAK|NORMALIZATION|SECOND-SEASON/MATURATION", "list", SYN, "Phase structure for the 18-month curve; units populated in Step 7C", "Demand Planning", "FROZEN"),
    a("weather_scenario_overlay", "MILD|NORMAL|SEVERE", "list", DER, "Reused from frozen Step 4C; composable with adoption scenarios, kept separate", "Demand Planning", "FROZEN"),
    a("topdown_category_growth", None, "pct", TBD, "Synthetic commercial input for reconciliation; not invented in 7B", "Merchandising/Finance", "NOT YET SET"),
    a("topdown_his_share_of_category", None, "pct", TBD, "HIS share of the outerwear category; set with commercial input in 7D", "Merchandising", "NOT YET SET"),
    a("topdown_merchandising_expectation", None, "units", TBD, "Merchandising launch expectation; set in 7D", "Merchandising", "NOT YET SET"),
    a("topdown_commercial_target", None, "units", TBD, "Commercial/portfolio target for HIS-001; set in 7D", "Finance/Management", "NOT YET SET"),
]
assumptions = pd.DataFrame(reg)
assumptions.to_csv(OUTDIR / "DemandIQ_Step7B_Launch_Assumptions.csv", index=False)

# ---- QA ----
assert len(cal[cal.month_index.between(1, 18)]) == 18, "strategic horizon must be 18 months"
assert abs(sum(ANALYTICAL_MIX.values()) - 1) < 1e-9 and abs(sum(COMMERCIAL_MIX.values()) - 1) < 1e-9
assert LOW_MULT < BASE_MULT < HIGH_MULT
print("Lifecycle calendar rows:", len(cal), "(incl. month 0 pre-launch context); strategic months 1-18 OK")
print(cal.to_string(index=False))
print("\nAssumption register rows:", len(assumptions))
print("Files written to", OUTDIR)
print("QA OK: channel mixes sum to 1.00; LOW<BASE<HIGH; 18 strategic months present.")
