"""The Streamlit app renders every page on the corrected plan; validation is rule-based."""

from __future__ import annotations

import sys

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from conftest import ROOT

APP = ROOT / "07_streamlit_app"
PAGES = sorted(p.name for p in (APP / "pages").glob("*.py"))


@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page):
    script = f"""
import sys, importlib.util
sys.path.insert(0, {str(APP)!r})
spec = importlib.util.spec_from_file_location("page", {str(APP / 'pages' / page)!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.render()
"""
    app = AppTest.from_string(script, default_timeout=120).run()
    assert not app.exception, [e.value for e in app.exception]
    assert not app.error, [e.value for e in app.error]


@pytest.mark.parametrize("folder", ["05_outputs/decision_layer", "05_outputs/v1_published_plan"])
def test_validation_passes(folder):
    sys.path.insert(0, str(APP))
    from utils.validation import all_passed, run_validation

    frames = [pd.read_csv(ROOT / folder / f"DemandIQ_Step6A_{name}.csv")
              for name in ["Executive_KPI_Summary", "Series_Decision_Summary", "Weekly_Planning_Trajectory"]]
    exec_df, series_df, weekly_df = frames
    if "committed_receipts_13w_units" not in exec_df:  # v1 predates this field
        exec_df["committed_receipts_13w_units"] = weekly_df.committed_receipt_units.sum()
    checks = run_validation(exec_df, series_df, weekly_df)
    assert all_passed(checks), [k for k, v in checks.items() if not v]


def test_status_banner_reports_no_escalation():
    script = f"""
import sys
sys.path.insert(0, {str(APP)!r})
from utils.data_loader import get_step6a
from components import cards
e, s, w = get_step6a()
cards.status_banner(e.iloc[0])
"""
    app = AppTest.from_string(script, default_timeout=120).run()
    text = " ".join(m.value for m in app.markdown)
    assert "No Escalation" in text and "0 ESCALATE · 7 PROTECT · 2 HOLD" in text
