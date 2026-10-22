#!/usr/bin/env python3
"""Rebuild DemandIQ from committed inputs, in dependency order.

    python 04_scripts/run_pipeline.py              rebuild every reproducible step
    python 04_scripts/run_pipeline.py --check      rebuild, then fail if any committed output changed
    python 04_scripts/run_pipeline.py --list       show every step and whether it can run
    python 04_scripts/run_pipeline.py --from step5 start part-way through
    python 04_scripts/run_pipeline.py --refit      refit the statsmodels steps and report drift

Step kinds
    exact    rebuilds byte for byte with the pinned requirements. Excel and
             PDF files carry build-time metadata, so --check compares their
             content (cell values; page count and text) and then restores the
             committed bytes.
    refit    re-runnable, but statsmodels optimisers do not reproduce the
             committed fits bit for bit across library versions, and the
             first 52 weeks of recovered demand are known only to the nearest
             float. --refit runs them on a scratch copy, reports the drift and
             restores the committed outputs. Downstream steps read the
             committed outputs.
    blocked  source code or row-level input missing; see
             06_docs/DemandIQ_Reproducibility.md for the recovery path.

Run order, inputs and limitations: 06_docs/DemandIQ_Reproducibility.md
"""

from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "build" / "logs"


@dataclass(frozen=True)
class Step:
    key: str
    title: str
    kind: str  # exact | refit | blocked
    script: str = ""
    args: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    note: str = ""
    needs: tuple[str, ...] = field(default=())


STEPS: tuple[Step, ...] = (
    # ---------------------------------------------------------------- source data
    Step("step3", "Step 3A-3D synthetic data generator", "blocked",
         outputs=("01_assumptions/DemandIQ_Step3A_v3.1_Assumptions.xlsx", "02_data/processed/*.csv"),
         note="Generator code was never committed. The CSVs are the frozen source data."),
    Step("weather_pull", "Weather: ERA5 daily and weekly (offline from cache)", "exact",
         "02_data/weather/pull_historical_weather_v2.py",
         outputs=("02_data/weather/data/weather_daily.csv", "02_data/weather/data/weather_weekly.csv"),
         note="Reads the committed Open-Meteo cache; network only if a cache file is missing."),
    Step("weather_features", "Weather: weekly planning features", "exact",
         "02_data/weather/weather_features_weekly.py",
         outputs=("02_data/weather/data/weather_features_weekly.csv",
                  "02_data/weather/data/weather_features_weekly.xlsx")),
    # ---------------------------------------------------------------- Step 4
    Step("step4a", "Step 4A demand reconstruction", "blocked",
         outputs=("03_model_evidence/step4a_reconstruction/DemandIQ_Step4A_Demand_Reconstruction.csv",),
         note="Code and row-level output never committed. Method evidence is in "
              "03_model_evidence/step4a_reconstruction/."),
    Step("step4b_1", "Step 4B.1 aggregate Step 4A to SKU x channel", "blocked",
         "04_scripts/step4b/step4b_1_prepare_forecasting_data.py",
         note="Needs the row-level Step 4A file. Step 4B.0 recovers its output instead."),
    Step("step4b_0", "Step 4B.0 recover the forecasting input", "exact",
         "04_scripts/step4b/step4b_0_recover_forecasting_input.py",
         outputs=("03_model_evidence/step4b_forecasting/DemandIQ_Step4B_Forecasting_Input.csv",)),
    Step("step4b_folds", "Step 4B backtest folds", "exact",
         "04_scripts/step4b/DemandIQ_Step4B_Backtest_Folds.py",
         outputs=("03_model_evidence/step4b_forecasting/backtest/DemandIQ_Step4B_Backtest_Folds.csv",)),
    Step("step4b_baseline", "Step 4B seasonal baselines", "exact",
         "04_scripts/step4b/DemandIQ_Step4B_Baseline.py",
         outputs=("03_model_evidence/step4b_forecasting/baseline/DemandIQ_Step4B_Baseline_*.csv",)),
    Step("step4b_ets", "Step 4B ETS backtest", "refit",
         "04_scripts/step4b/DemandIQ_Step4B_ETS_Fit.py",
         outputs=("03_model_evidence/step4b_forecasting/ets/DemandIQ_Step4B_ETS_*.csv",)),
    Step("step4b_sarima", "Step 4B SARIMA screen", "refit",
         "04_scripts/step4b/step4b_5_sarima_models.py",
         outputs=("03_model_evidence/step4b_forecasting/sarima/screen/DemandIQ_Step4B_SARIMA_Screen_*.csv",)),
    Step("step4b_sarima_targeted", "Step 4B SARIMA targeted confirmation", "refit",
         "04_scripts/step4b/step4b_5c_sarima_targeted_confirmation.py",
         outputs=("03_model_evidence/step4b_forecasting/sarima/targeted/*.csv",)),
    Step("step4b_champion", "Step 4B champion selection", "exact",
         "04_scripts/step4b/step4b_6_champion_selection.py",
         outputs=("05_outputs/champion_selection/*.csv",)),
    Step("step4c_1", "Step 4C.1 weather input audit", "blocked",
         "04_scripts/step4c/step4c_1_weather_input_audit.py",
         note="Audit only (no output file). Needs the row-level Step 4A file."),
    Step("step4c_2", "Step 4C.2 regional weather scenarios", "exact",
         "04_scripts/step4c/step4c_2_weather_signal_scenarios.py",
         outputs=("05_outputs/weather_scenarios/*.csv",)),
    Step("step4c_3", "Step 4C.3 weather planning overlay", "blocked",
         "04_scripts/step4c/step4c_3_weather_planning_overlay.py",
         outputs=("05_outputs/weather_overlay/*.csv",),
         note="Regional weights need the row-level Step 4A file. The committed overlay feeds 4C.4."),
    Step("step4c_4", "Step 4C.4 forward weather framework", "exact",
         "04_scripts/step4c/step4c_4_forward_weather_framework.py",
         outputs=("05_outputs/weather_forward/*.csv",)),
    Step("step4d", "Step 4D final 13-week forecast", "refit",
         "04_scripts/step4c/step4d_final_forecast.py",
         outputs=("05_outputs/forecasts/*.csv",)),
    # ---------------------------------------------------------------- Steps 5-8
    Step("step5", "Step 5 IBP decision engine (corrected supply view)", "exact",
         "04_scripts/step5/step5_ibp_decision_engine.py",
         outputs=("05_outputs/ibp_decisions/*.csv",)),
    Step("step6a", "Step 6A KPI and decision layer", "exact",
         "04_scripts/step6/step6a_decision_layer.py",
         outputs=("05_outputs/decision_layer/*.csv",)),
    Step("step7b_setup", "Step 7B launch setup", "exact", "04_scripts/step7b/step7b_launch_setup.py",
         outputs=("05_outputs/launch_step7b/DemandIQ_Step7B_Lifecycle_Calendar.csv",
                  "05_outputs/launch_step7b/DemandIQ_Step7B_Launch_Assumptions.csv")),
    Step("step7b_scorecard", "Step 7B analog scorecard", "exact", "04_scripts/step7b/step7b_analog_scorecard.py",
         outputs=("05_outputs/launch_step7b/DemandIQ_Step7B_Analog_*.csv",
                  "05_outputs/launch_step7b/DemandIQ_Step7B_Seasonal_Correlation.csv")),
    Step("step7c", "Step 7C cold-start forecast", "exact", "04_scripts/step7c/step7c_cold_start_forecast.py",
         outputs=("05_outputs/launch_step7c/*.csv",)),
    Step("step7d", "Step 7D reconciliation and consensus", "exact",
         "04_scripts/step7d/step7d_reconciliation_consensus.py", outputs=("05_outputs/launch_step7d/*.csv",)),
    Step("step7e", "Step 7E launch execution (seeded actuals)", "exact",
         "04_scripts/step7e/step7e_launch_execution.py", outputs=("05_outputs/launch_step7e/*.csv",)),
    Step("step7f", "Step 7F FVA and rolling handoff", "exact",
         "04_scripts/step7f/step7f_fva_rolling_handoff.py", outputs=("05_outputs/launch_step7f/*.csv",)),
    Step("step8", "Step 8 peak-season diagnosis", "exact", "04_scripts/step8/step8_peak_diagnosis.py",
         outputs=("05_outputs/peak_season_diagnosis/DemandIQ_Step8_*.csv", "08_assets/charts/step8_*.png")),
    Step("step8b", "Step 8B reconcile Step 5 with Step 8", "exact",
         "04_scripts/step8/step8b_step5_reconciliation.py",
         outputs=("05_outputs/peak_season_diagnosis/DemandIQ_Step8B_*.csv",)),
    Step("brief", "Step 8C two-page brief (PDF), built and number-checked", "exact",
         "04_scripts/step8/step8c_build_brief.py",
         outputs=("06_docs/DemandIQ_Peak_Season_Brief.pdf",)),
)

VOLATILE_SUFFIXES = {".xlsx", ".pdf"}  # build-time metadata in the container


# --------------------------------------------------------------------------- helpers

def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=check)


def output_files(step: Step) -> list[Path]:
    files: list[Path] = []
    for pattern in step.outputs:
        files += sorted(ROOT.glob(pattern))
    return files


def committed_bytes(path: Path) -> bytes | None:
    result = git("show", f"HEAD:{path.relative_to(ROOT).as_posix()}", check=False)
    return result.stdout if result.returncode == 0 else None


def same_content(path: Path, committed: bytes) -> bool:
    """Compare Excel by cell values and PDF by page count and text."""
    if path.suffix == ".xlsx":
        import pandas as pd

        new = pd.read_excel(path, sheet_name=None)
        old = pd.read_excel(io.BytesIO(committed), sheet_name=None)
        return list(new) == list(old) and all(new[k].equals(old[k]) for k in new)
    if path.suffix == ".pdf":
        from pypdf import PdfReader

        def text(reader: PdfReader) -> list[str]:
            return [" ".join((page.extract_text() or "").split()) for page in reader.pages]

        return text(PdfReader(path)) == text(PdfReader(io.BytesIO(committed)))
    return False


def run(step: Step) -> float:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = LOG_DIR / f"{step.key}.log"
    start = time.time()
    with log.open("w", encoding="utf-8") as handle:
        env = {**os.environ, "PYTHONHASHSEED": "0", "MPLBACKEND": "Agg"}
        result = subprocess.run([sys.executable, str(ROOT / step.script), *step.args],
                                cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT, env=env)
    elapsed = time.time() - start
    if result.returncode != 0:
        tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-25:]
        print("\n".join(tail))
        raise SystemExit(f"FAILED: {step.key} (exit {result.returncode}); full log: {log}")
    return elapsed


def check_outputs(steps: list[Step]) -> list[str]:
    """Paths whose rebuilt content differs from HEAD; volatile files restored when equal."""
    problems = []
    for step in steps:
        for path in output_files(step):
            committed = committed_bytes(path)
            rel = path.relative_to(ROOT).as_posix()
            if committed is None:
                problems.append(f"{rel}: not committed")
                continue
            current = path.read_bytes()
            if current == committed:
                continue
            if path.suffix in VOLATILE_SUFFIXES and same_content(path, committed):
                path.write_bytes(committed)  # same content; keep the committed bytes
                continue
            problems.append(f"{rel}: differs from the committed version")
    return problems


# --------------------------------------------------------------------------- refit drift

def refit_report() -> None:
    """Refit ETS, SARIMA and Step 4D on a scratch copy and report drift from HEAD."""
    import numpy as np
    import pandas as pd

    refit = [s for s in STEPS if s.kind == "refit"] + [s for s in STEPS if s.key == "step4b_champion"]
    backup = Path(tempfile.mkdtemp(prefix="demandiq_refit_"))
    saved = {p: backup / p.relative_to(ROOT) for s in refit for p in output_files(s)}
    for original, copy in saved.items():
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, copy)
    try:
        for step in refit:
            print(f"  refit {step.key:<24} {run(step):6.1f}s")

        def frame(path: Path, committed: bool) -> pd.DataFrame:
            data = committed_bytes(path) if committed else path.read_bytes()
            return pd.read_csv(io.BytesIO(data), float_precision="round_trip")

        evidence = ROOT / "03_model_evidence/step4b_forecasting"
        print()
        for label, path in (("ETS backtest", evidence / "ets/DemandIQ_Step4B_ETS_Summary.csv"),
                            ("SARIMA screen", evidence / "sarima/screen/DemandIQ_Step4B_SARIMA_Screen_Summary.csv"),
                            ("SARIMA targeted",
                             evidence / "sarima/targeted/DemandIQ_Step4B_SARIMA_Targeted_Summary.csv")):
            old, new = frame(path, True), frame(path, False)
            merged = old.merge(new, on=["sku_id", "channel_id", "model"], suffixes=("_old", "_new"))
            drift = (merged.pooled_wape_pct_new - merged.pooled_wape_pct_old).abs().max()
            print(f"  {label:<16} pooled WAPE drift, max {drift:.4f} pp")

        champ = ROOT / "05_outputs/champion_selection/DemandIQ_Step4B_Champion_Selection.csv"
        old, new = frame(champ, True), frame(champ, False)
        both = old.merge(new, on=["sku_id", "channel_id"], suffixes=("_old", "_new"))
        flips = both[both.selected_champion_old != both.selected_champion_new]
        print(f"  Champion changes on refit: {len(flips)} of {len(both)}")
        for row in flips.itertuples():
            print(f"    {row.sku_id} {row.channel_id}: {row.selected_champion_old} "
                  f"({row.champion_wape_pct_old:.3f}%) -> {row.selected_champion_new} "
                  f"({row.champion_wape_pct_new:.3f}%)")

        fc = ROOT / "05_outputs/forecasts/DemandIQ_Step4D_Final_13Week_Forecast.csv"
        old, new = frame(fc, True), frame(fc, False)
        diff = new.base_forecast_units - old.base_forecast_units
        print(f"  Step 4D 13-week base forecast drift: max {np.abs(diff).max():.3f} units/week, "
              f"total {diff.sum():+.1f} units ({diff.sum() / old.base_forecast_units.sum():+.3%}). "
              "Step 4D keeps its frozen champions.")
    finally:
        for original, copy in saved.items():
            shutil.copy2(copy, original)
        shutil.rmtree(backup, ignore_errors=True)
        print("  Committed outputs restored.")


# --------------------------------------------------------------------------- main

def print_table() -> None:
    print(f"{'step':<24}{'kind':<9}title / note")
    for step in STEPS:
        print(f"{step.key:<24}{step.kind:<9}{step.title}")
        if step.note:
            print(f"{'':<33}{step.note}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if any committed output changes")
    parser.add_argument("--list", action="store_true", help="show the step table and exit")
    parser.add_argument("--refit", action="store_true", help="refit statsmodels steps and report drift")
    parser.add_argument("--from", dest="start", metavar="STEP", help="start at this step key")
    args = parser.parse_args()

    if args.list:
        print_table()
        return
    if args.refit:
        refit_report()
        return

    steps = [s for s in STEPS if s.kind == "exact"]
    if args.start:
        keys = [s.key for s in steps]
        if args.start not in keys:
            raise SystemExit(f"Unknown or non-exact step {args.start!r}. Exact steps: {', '.join(keys)}")
        steps = steps[keys.index(args.start):]

    total = time.time()
    for step in steps:
        print(f"  {step.key:<24} {run(step):6.1f}s  {step.title}")
    print(f"Rebuilt {len(steps)} steps in {time.time() - total:.0f}s. "
          f"Skipped: {', '.join(s.key for s in STEPS if s.kind != 'exact')} (see --list).")

    if args.check:
        problems = check_outputs(steps)
        if problems:
            print("\nCHECK FAILED: rebuilt outputs differ from the committed versions")
            print("\n".join(f"  {p}" for p in problems))
            raise SystemExit(1)
        print("CHECK PASSED: every rebuilt output matches the committed version.")


if __name__ == "__main__":
    main()
