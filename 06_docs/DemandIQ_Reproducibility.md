# DemandIQ: reproducibility

This page explains how to rebuild DemandIQ from the repository, what each step needs, and which steps cannot run and why. All paths are relative to the repository root, and no script depends on a local drive letter.

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
python -m pip install -r requirements-dev.txt
python -m playwright install chromium             # only needed for the PDF brief

python 04_scripts/run_pipeline.py --list          # every step, and whether it can run
python 04_scripts/run_pipeline.py --check         # rebuild, then fail if any committed output changed
python -m pytest -q                               # focused checks
```

`--check` rebuilds every reproducible step in dependency order. It fails if any output differs from the committed version. Two file types embed their build time, so the check compares their content instead and then restores the committed bytes:

- Excel workbooks are compared by cell values.
- The PDF brief is compared by page count and text.

Each step's log is written to `build/logs/`.

Verified in a clean virtual environment with `requirements-dev.txt`:

- 19 steps rebuild in about 25 seconds (18 analysis steps plus the brief).
- Every output matches the committed files.

CI runs the same check on every push (`.github/workflows/ci.yml`).

## Run order

| # | Step | Script | Reads | Writes | Kind |
| --- | --- | --- | --- | --- | --- |
| 1 | Synthetic data generator (3A–3D) | *missing* | — | `01_assumptions/`, `02_data/processed/` | blocked |
| 2 | Weather pull (ERA5) | `02_data/weather/pull_historical_weather_v2.py` | `02_data/weather/cache/*.json` | `weather_daily.csv`, `weather_weekly.csv` | exact |
| 3 | Weather features | `02_data/weather/weather_features_weekly.py` | `weather_weekly.csv` | `weather_features_weekly.csv`, `.xlsx` | exact |
| 4 | Demand reconstruction (4A) | *missing* | Step 3C inventory | `DemandIQ_Step4A_Demand_Reconstruction.csv` | blocked |
| 5 | Aggregate 4A to SKU × channel (4B.1) | `04_scripts/step4b/step4b_1_prepare_forecasting_data.py` | row-level 4A file | forecasting input | blocked |
| 6 | Recover the forecasting input (4B.0) | `04_scripts/step4b/step4b_0_recover_forecasting_input.py` | Step 4B baseline backtest, Step 3C | `03_model_evidence/step4b_forecasting/DemandIQ_Step4B_Forecasting_Input.csv` | exact |
| 7 | Backtest folds | `04_scripts/step4b/DemandIQ_Step4B_Backtest_Folds.py` | forecasting input | `backtest/` | exact |
| 8 | Seasonal baselines | `04_scripts/step4b/DemandIQ_Step4B_Baseline.py` | input, folds | `baseline/` | exact |
| 9 | ETS backtest | `04_scripts/step4b/DemandIQ_Step4B_ETS_Fit.py` | input, folds | `ets/` | refit |
| 10 | SARIMA screen | `04_scripts/step4b/step4b_5_sarima_models.py` | input, folds | `sarima/screen/` | refit |
| 11 | SARIMA targeted | `04_scripts/step4b/step4b_5c_sarima_targeted_confirmation.py` | input, folds, summaries | `sarima/targeted/` | refit |
| 12 | Champion selection | `04_scripts/step4b/step4b_6_champion_selection.py` | baseline, ETS, SARIMA summaries | `05_outputs/champion_selection/` | exact |
| 13 | Weather input audit (4C.1) | `04_scripts/step4c/step4c_1_weather_input_audit.py` | features, row-level 4A | console only | blocked |
| 14 | Regional weather scenarios (4C.2) | `04_scripts/step4c/step4c_2_weather_signal_scenarios.py` | weather features | `05_outputs/weather_scenarios/` | exact |
| 15 | Weather planning overlay (4C.3) | `04_scripts/step4c/step4c_3_weather_planning_overlay.py` | row-level 4A, scenarios | `05_outputs/weather_overlay/` | blocked |
| 16 | Forward weather framework (4C.4) | `04_scripts/step4c/step4c_4_forward_weather_framework.py` | overlay | `05_outputs/weather_forward/` | exact |
| 17 | Final 13-week forecast (4D) | `04_scripts/step4c/step4d_final_forecast.py` | input, forward weather | `05_outputs/forecasts/` | refit |
| 18 | IBP decision engine (5) | `04_scripts/step5/step5_ibp_decision_engine.py` | 4D forecast, 3C inventory, 3D economics | `05_outputs/ibp_decisions/` | exact |
| 19 | KPI and decision layer (6A) | `04_scripts/step6/step6a_decision_layer.py` | 4D forecast, Step 5 plan, v1 plan (zero-replenishment comparison) | `05_outputs/decision_layer/` | exact |
| 20 | Launch planning (7B–7F) | `04_scripts/step7b/` … `step7f/` | 3D economics, earlier 7x outputs | `05_outputs/launch_step7*/` | exact |
| 21 | Peak-season diagnosis (8) | `04_scripts/step8/step8_peak_diagnosis.py` | 3D economics, 4B baseline, v1 plan, 4B champions, 7E, 7F | `05_outputs/peak_season_diagnosis/DemandIQ_Step8_*`, `08_assets/charts/` | exact |
| 22 | Step 5 reconciliation and replenishment sensitivity (8B) | `04_scripts/step8/step8b_step5_reconciliation.py` | 3C inventory, Step 5 plan, v1 plan, Step 8 queue | `DemandIQ_Step8B_*` | exact |
| 23 | Two-page brief | `04_scripts/step8/step8c_build_brief.py` | Step 8 and 8B outputs, chart | `06_docs/DemandIQ_Peak_Season_Brief.pdf` | exact (content) |

**exact**: rebuilt by `run_pipeline.py` and checked byte for byte.

**refit**: re-runnable, but not bit-reproducible (see below). Downstream steps read the committed outputs.

**blocked**: code or row-level input is missing (see below).

The Streamlit app (`07_streamlit_app/`) reads `05_outputs/decision_layer/` and the Step 4 evidence. It writes nothing.

## Refit steps: what drifts and by how much

The statsmodels optimisers behind ETS and SARIMA don't reproduce committed fits bit for bit across library versions. Two things cause this:

- The original environment's exact versions were not recorded.
- The first 52 weeks of the recovered demand series are known only to the nearest float (see the next section). Moving those values by one float step alone shifts Step 4D's refitted forecast by up to 0.01 units.

`python 04_scripts/run_pipeline.py --refit` refits the four steps on a scratch copy, prints the drift and restores the committed files. With the pinned requirements:

| Refit | Drift from the committed outputs |
| --- | --- |
| ETS backtest | Pooled WAPE changes by at most 0.29 pp |
| SARIMA screen and targeted | Pooled WAPE changes by at most 0.001 pp |
| Champion selection | 1 of 9 changes: IMH-001 RETAIL moves from HW_Damped_Mul (8.485%) to HW_Damped_Add (8.317%). In the committed backtest the two were 0.007 pp apart. |
| Step 4D forecast | Max 1.27 units a week (APS-001 WHOLESALE); 13-week total +8.7 units (+0.02%) |
| Step 5 on the refitted forecast | All 9 calls unchanged; ending cover moves by at most 0.07 weeks |

Step 4D keeps its champions frozen in code, so a refit never switches a model silently. Read the IMH-001 RETAIL result as a near-tie between two damped ETS variants. It does not mean the published champion is wrong.

## What cannot run, and the recovery path

### Where I looked

I looked in three places for the missing code:

- **GitHub history.** Every commit on `main` and on the PR branches. Neither the generator nor the reconstruction code was ever committed.
- **The original working folder (`D:\Downloads\DemandIQ`).** Its `step3` and `step4a` script folders exist but are empty. Its two local commits never contained either script.
- **The project notes.** They list the Step 3 and Step 4A output files but name no script.

The code is genuinely missing.

### Step 3 generator (3A–3D): blocked; recovery is not recommended

The committed CSVs and the assumptions workbook are the frozen source data. Their SHA-256 checksums are in `02_data/SOURCE_DATA_SHA256SUMS.txt`, and a test verifies them. Treat them like an ERP extract: every later step starts from them.

The workbook documents the generator's rules (seasonal buy, replenishment, chase, observability). The generator could be rewritten from them, but a new random draw would not reproduce these numbers. It would be a new dataset version, and every result would have to be re-derived. Only do that if the case study needs new data.

### Step 4A reconstruction: blocked; the series is recovered and the row-level output is not

`step4b_0` rebuilds the 260-week × 9-series reconstructed-demand series that Step 4B and 4D read. It uses the committed baseline backtest:

- **Weeks 2022-07-04 to 2026-06-22 (1,872 series-weeks).** Exact. They come from the backtest actuals and the lag-52 forecasts, and every week covered by both agrees.
- **Weeks 2021-07-05 to 2022-06-27 (468 series-weeks).** Recovered from the two-year moving-average forecasts, which constrain each value to a few adjacent floats.
  - **345 weeks with no stockout-censored rows.** The script anchors them on summed sales. 343 match exactly; the other 2 sit one float step away.
  - **123 censored weeks.** 42 are pinned uniquely. The other 81 are known to within 2–4 adjacent floats, a few parts in 10¹⁶.

The script checks three things:

- All 1,404 moving-average forecasts reproduce exactly.
- Every uncensored series-week equals its summed observed sales.
- The baseline backtest rebuilds byte for byte.

pandas' default CSV parser is off by one float step for a few values. The script reads the evidence with `float_precision="round_trip"` and writes text that the default parser maps back to the exact floats.

The row-level output (SKU × region × channel × week) can't be recovered this way. Steps 4B.1, 4C.1 and 4C.3 need it. Their status:

- 4B.1's output is superseded by 4B.0.
- 4C.1 is an audit that writes no file.
- 4C.3's output (the weather overlay) is committed and feeds 4C.4.

**Recovery path for Step 4A:** re-implement the seasonal-profile imputation and accept it only when it hits these committed targets:

1. **The recovered series.** All 2,340 series-weeks. They must match exactly, or for the 83 first-year weeks noted above, to within their few adjacent floats.
2. **335 single-censored-row weeks.** In these series-weeks exactly one region-row was censored, so that row's imputed value is pinned exactly: the series value minus the other regions' sales. Every one is at least the observed sales, which is consistent with `max(observed, profile estimate)`.
3. **The method comparison** (`03_model_evidence/step4a_reconstruction/DemandIQ_Step4A_Method_Comparison.csv`):

   | Rows | Predicted units |
   | --- | --- |
   | 1,912 censored rows | 98,578.395191 |
   | 677 stockout rows | 34,794.492446 |
   | 1,235 partial rows | 63,783.902745 |

   Also WAPE 26.08%, bias −2.61%, recovery 95.68%, plus the nine per-series totals.

I tried the obvious variants and none reproduces target 2: same-week means and medians over other years, with and without a plan-year level factor, keyed by plan week or ISO week. The best had a mean absolute error of about 8 units. The original method used something these variants don't, so it needs its code or a closer description. If the original script turns up, add it in a new `step4a` folder under `04_scripts/` and remove `step4a` from the blocked list in `run_pipeline.py`. The targets above then become its test.

## Environment notes

- **Python 3.13**, with the pins in `requirements.txt` (`requirements-dev.txt` adds tests and the PDF toolchain).
  - Pillow is pinned because it writes the chart PNGs.
  - statsmodels is pinned for the refit steps.
- **Charts** use the bundled Inter font (`08_assets/fonts/`, SIL Open Font License) and set matplotlib's font family and hinting explicitly. A stock install therefore renders the same PNG bytes as the original environment, which had changed those defaults.
- **The brief** uses the bundled Carlito font, metric-compatible with Calibri, so it is two pages on any machine.
- **Line endings.** The weather pull writes LF line endings on every OS, matching the committed files.
- **`DemandIQ_Step4B_Full12Fold_Candidate_Evidence.csv`** had been re-saved by Excel (10 significant digits, `TRUE`). It is now written by the script. Values are unchanged to within 4 × 10⁻⁹.
- **Weather data:** Open-Meteo Historical Weather API (CC BY 4.0), ERA5 reanalysis from the Copernicus Climate Change Service. The raw responses are committed in `02_data/weather/cache/`, so the weather layer rebuilds offline.
