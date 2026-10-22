"""Shared helpers for the DemandIQ checks. Tests read committed outputs; the
clean rebuild itself is `python 04_scripts/run_pipeline.py --check` (CI runs it
first, so these tests check the same bytes it rebuilt)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SERIES = ["sku_id", "channel_id"]


def read(relative: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / relative, **kwargs)


def run_script(relative: str, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONHASHSEED": "0", "MPLBACKEND": "Agg"}
    result = subprocess.run([sys.executable, str(ROOT / relative), *args], cwd=ROOT,
                            capture_output=True, text=True, env=env)
    assert result.returncode == 0, (result.stdout[-4000:] + result.stderr[-4000:])
    return result


def series_level(plan: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """First row per series of series-level Step 5 fields."""
    return plan.sort_values("horizon_week").groupby(SERIES)[columns].first()
