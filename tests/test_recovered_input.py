"""Step 4B.0: the recovered forecasting input reproduces the committed evidence."""

from __future__ import annotations

import importlib.util

import numpy as np
import pandas as pd

from conftest import ROOT, read

SCRIPT = ROOT / "04_scripts/step4b/step4b_0_recover_forecasting_input.py"
INPUT = "03_model_evidence/step4b_forecasting/DemandIQ_Step4B_Forecasting_Input.csv"


def load_module():
    spec = importlib.util.spec_from_file_location("step4b_0", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_recovery_matches_the_committed_input():
    recovered = load_module().recover()  # raises if any recovery check fails
    committed = read(INPUT, parse_dates=["week_start"])
    assert list(committed.columns) == ["week_start", "sku_id", "channel_id", "reconstructed_demand_units"]
    assert len(committed) == 2340
    assert (committed.reconstructed_demand_units.to_numpy()
            == recovered.reconstructed_demand_units.to_numpy()).all()


def test_baseline_backtest_rebuilds_from_the_recovered_input():
    """The baseline forecasts are lag-52 values and two-year means of the input."""
    data = read(INPUT, parse_dates=["week_start"]).set_index(["sku_id", "channel_id", "week_start"])
    y = data.reconstructed_demand_units
    # The Step 4B scripts read the input with pandas' default parser; their
    # outputs hold exact floats, so read those back with round-trip parsing.
    bt = read("03_model_evidence/step4b_forecasting/baseline/DemandIQ_Step4B_Baseline_Predictions.csv",
              parse_dates=["forecast_date", "reference_1_date", "reference_2_date"],
              float_precision="round_trip")
    key = lambda col: pd.MultiIndex.from_arrays([bt.sku_id, bt.channel_id, bt[col]])  # noqa: E731
    actual = y.reindex(key("forecast_date")).to_numpy()
    lag52 = y.reindex(key("reference_1_date")).to_numpy()
    lag104 = y.reindex(key("reference_2_date")).to_numpy()
    expected = np.where(bt.model == "Seasonal_Naive", lag52, (lag52 + lag104) / 2)
    assert (actual == bt.actual_units.to_numpy()).all()
    assert (expected == bt.forecast_units.to_numpy()).all()
