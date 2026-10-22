"""DemandIQ Step 4B.0: recover the Step 4B forecasting input from committed evidence.

Why this exists
    The Step 4A demand-reconstruction script and its row-level output
    (DemandIQ_Step4A_Demand_Reconstruction.csv) were never committed, so
    step4b_1, which aggregates that output to SKU x channel x week, cannot run.
    Its product, the 260-week reconstructed-demand series that every Step 4B
    model and Step 4D read, can be recovered exactly from the committed
    Step 4B baseline backtest:

      actual_units (backtest test weeks)       -> weeks 2023-07-03 .. 2026-06-22
      Seasonal_Naive forecast = y[t-52]        -> weeks 2022-07-04 .. 2025-06-23
      Seasonal_MA_2Y forecast = (y[t-52] + y[t-104]) / 2
                                               -> y[t-104], weeks 2021-07-05 .. 2022-06-27

Checks (the script stops if any fails)
    1. Weeks covered by two sources agree exactly.
    2. A series-week with no stockout-censored rows equals its summed observed
       sales in Step 3C (reconstruction leaves uncensored weeks unchanged).
    3. Every Seasonal_MA_2Y forecast is reproduced exactly from the recovered
       series. For the first 52 weeks, which only the MA forecast carries, a
       week without censored rows takes its summed sales; any other week takes
       the float nearest 2f - y[t-52] that passes this check.

Float handling
    Evidence is read with float_precision="round_trip", so values are the exact
    floats the original Step 4B scripts held in memory. pandas' default CSV
    parser is not correctly rounded (it is off by one unit in the last place
    for a few values), so each value is written as a string that the default
    parser maps back to that exact float. Step 4B scripts then see the same
    numbers the original run did.

Output
    03_model_evidence/step4b_forecasting/DemandIQ_Step4B_Forecasting_Input.csv
    (the exact 4-column schema step4b_1 writes)

    python 04_scripts/step4b/step4b_0_recover_forecasting_input.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BASELINE_FILE = ROOT / "03_model_evidence/step4b_forecasting/baseline/DemandIQ_Step4B_Baseline_Predictions.csv"
INVENTORY_FILE = ROOT / "02_data/processed/DemandIQ_Step3C_v5_Seasonal_Buy_Inventory.csv"
OUTPUT_FILE = ROOT / "03_model_evidence/step4b_forecasting/DemandIQ_Step4B_Forecasting_Input.csv"

SERIES = ["sku_id", "channel_id"]
KEY = SERIES + ["week_start"]
EXPECTED_WEEKS = 260
EXPECTED_SERIES = 9
MAX_ULP_STEPS = 8
VALUE = "reconstructed_demand_units"


def check(condition: bool, message: str) -> None:
    print(f"  [{'PASS' if condition else 'FAIL'}] {message}")
    if not condition:
        raise ValueError(f"Recovery check failed: {message}")


def observed_sales_by_series() -> pd.DataFrame:
    """Summed observed sales and whether any region-row was stockout-censored."""
    inv = pd.read_csv(INVENTORY_FILE, usecols=["week_start", "sku_id", "channel_id",
                                               "observed_sales_units", "sales_censored_flag"],
                      parse_dates=["week_start"])
    return inv.groupby(KEY).agg(observed_sales_units=("observed_sales_units", "sum"),
                                censored_rows=("sales_censored_flag", "sum"))


def neighbours(x: float, steps: int = MAX_ULP_STEPS) -> list[float]:
    """x, then floats 1, 2, ... units in the last place away, alternating up and down."""
    out, up, down = [float(x)], float(x), float(x)
    for _ in range(steps):
        up, down = float(np.nextafter(up, np.inf)), float(np.nextafter(down, -np.inf))
        out += [up, down]
    return out


def default_parse(texts: list[str]) -> np.ndarray:
    """How pandas' default CSV parser reads each string."""
    import io

    frame = pd.read_csv(io.StringIO("v\n" + "\n".join(texts) + "\n"))
    return frame.v.to_numpy(dtype=float)


def text_for(target: float) -> str | None:
    """CSV text that pandas' default parser reads back as exactly `target`, or None.

    The original Step 4B scripts only ever held floats produced by that parser,
    so a value it cannot produce cannot have been in the original input.
    """
    options = [repr(c) for c in neighbours(target)] + [f"{target:.17g}"]
    hits = [t for t, v in zip(options, default_parse(options)) if v == target]
    return hits[0] if hits else None


def solve_older_week(a: float, f: float, prior: float | None) -> float:
    """Float b with (a + b) / 2 == f that the CSV parser can produce, nearest the prior.

    The prior is the week's summed observed sales when no row was censored
    (reconstruction leaves those weeks unchanged), otherwise the exact 2f - a.
    """
    from fractions import Fraction

    target = Fraction(prior) if prior is not None else 2 * Fraction(f) - Fraction(a)
    pool = neighbours(float(2 * f - a)) + (neighbours(prior) if prior is not None else [])
    valid = {b for b in pool if (a + b) / 2 == f}
    for b in sorted(valid, key=lambda b: (abs(Fraction(b) - target), b)):
        if text_for(b) is not None:
            return b
    raise ValueError(f"No parser-reachable float reproduces the MA forecast {f!r} from {a!r}.")


def stable_text(values: pd.Series) -> list[str]:
    """Shortest-repr strings, nudged where the default parser would not return the float."""
    texts = [repr(float(v)) for v in values]
    parsed = default_parse(texts)
    for i in np.flatnonzero(parsed != values.to_numpy()):
        text = text_for(float(values.iloc[i]))
        if text is None:
            raise ValueError(f"No CSV text parses back to {values.iloc[i]!r}.")
        texts[i] = text
    return texts


def recover() -> pd.DataFrame:
    backtest = pd.read_csv(BASELINE_FILE, float_precision="round_trip",
                           parse_dates=["forecast_date", "reference_1_date", "reference_2_date"])
    naive = backtest[backtest.model == "Seasonal_Naive"]
    moving = backtest[backtest.model == "Seasonal_MA_2Y"].copy()

    actual = naive.drop_duplicates(SERIES + ["forecast_date"]).rename(
        columns={"forecast_date": "week_start"}).set_index(KEY).actual_units
    lagged = naive.rename(columns={"reference_1_date": "week_start"}).set_index(KEY).forecast_units

    print("Sources")
    overlap = actual.index.intersection(lagged.index)
    check(bool((actual.loc[overlap] == lagged.loc[overlap]).all()),
          f"actuals and lag-52 forecasts agree on all {len(overlap)} shared series-weeks")
    y = pd.concat([actual, lagged[~lagged.index.isin(actual.index)]])

    moving["a"] = y.reindex(pd.MultiIndex.from_arrays(
        [moving.sku_id, moving.channel_id, moving.reference_1_date], names=KEY)).to_numpy()
    moving["b_known"] = y.reindex(pd.MultiIndex.from_arrays(
        [moving.sku_id, moving.channel_id, moving.reference_2_date], names=KEY)).to_numpy()
    known = moving.dropna(subset=["b_known"])
    check(bool(np.allclose(2 * known.forecast_units - known.a, known.b_known, rtol=0, atol=1e-9)),
          f"MA forecasts imply the same values on all {len(known)} overlapping series-weeks")

    sales = observed_sales_by_series()
    older = moving[moving.b_known.isna()].copy()
    recovered = {}
    uncensored_weeks = 0
    for row in older.itertuples():
        key = (row.sku_id, row.channel_id, row.reference_2_date)
        exact = sales.loc[key]
        prior = float(exact.observed_sales_units) if exact.censored_rows == 0 else None
        uncensored_weeks += prior is not None
        recovered[key] = solve_older_week(row.a, row.forecast_units, prior)
    print(f"  First 52 weeks: {len(older)} series-weeks solved from the MA forecast; "
          f"{uncensored_weeks} anchored on summed sales (no censored rows)")
    older_series = pd.Series(recovered, name="reconstructed_demand_units")
    older_series.index.names = KEY
    y = pd.concat([y, older_series]).sort_index()

    out = y.rename("reconstructed_demand_units").reset_index()
    out = out.sort_values(SERIES + ["week_start"]).reset_index(drop=True)
    out = out[["week_start", "sku_id", "channel_id", "reconstructed_demand_units"]]

    print("Recovered series")
    check(len(out) == EXPECTED_WEEKS * EXPECTED_SERIES, f"{len(out)} rows = 260 weeks x 9 series")
    check(out.groupby(SERIES).week_start.nunique().eq(EXPECTED_WEEKS).all(), "260 weeks per series")
    check(not out.duplicated(KEY).any(), "no duplicate series-weeks")
    check(bool((out.reconstructed_demand_units >= 0).all()), "no negative demand")
    joined = out.join(sales, on=KEY)
    uncensored = joined[joined.censored_rows == 0]
    check(bool(np.allclose(uncensored.reconstructed_demand_units, uncensored.observed_sales_units,
                           rtol=0, atol=1e-9)),
          f"uncensored series-weeks equal summed observed sales ({len(uncensored)} of {len(out)})")
    check(bool((joined.reconstructed_demand_units >= joined.observed_sales_units - 1e-9).all()),
          "reconstructed demand is never below observed sales")
    lookup = out.set_index(KEY).reconstructed_demand_units
    a = lookup.reindex(pd.MultiIndex.from_arrays(
        [moving.sku_id, moving.channel_id, moving.reference_1_date], names=KEY)).to_numpy()
    b = lookup.reindex(pd.MultiIndex.from_arrays(
        [moving.sku_id, moving.channel_id, moving.reference_2_date], names=KEY)).to_numpy()
    check(bool(((a + b) / 2 == moving.forecast_units.to_numpy()).all()),
          f"all {len(moving)} Seasonal_MA_2Y forecasts reproduce exactly")
    return out


def main() -> None:
    out = recover()
    written = out.copy()
    written["week_start"] = written.week_start.dt.strftime("%Y-%m-%d")
    written[VALUE] = stable_text(out[VALUE])
    written.to_csv(OUTPUT_FILE, index=False)

    reread = pd.read_csv(OUTPUT_FILE)
    check(bool((reread[VALUE].to_numpy() == out[VALUE].to_numpy()).all()),
          "default pandas parsing of the written file returns the recovered floats exactly")
    print(f"\nWrote {OUTPUT_FILE.relative_to(ROOT)} ({len(out)} rows)")


if __name__ == "__main__":
    main()
