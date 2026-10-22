"""Projected supply must never read as confirmed supplier orders.

The 6,512 replenishment units are an estimate, and every surface must say so.
The seasonal drops are projected too (last year's seasonal receipts shifted 52
weeks and grown); they keep the v1 column name committed_receipt_units only
so the v1 plan reproduces, and a status field marks them as projected.


They are last year's replenishment receipts shifted 52 weeks plus SKU growth,
not confirmed open orders. The Jul 13 check validates projected dates only.
So the 0 ESCALATE / 7 PROTECT / 2 HOLD result is conditional on the estimate
arriving as modelled, the zero-replenishment result (3 escalations) stays
visible, and a planner must confirm open-order quantities and receipt dates
before the published escalation list is replaced. These checks protect those
labels in the outputs, docs, brief and app.
"""

from __future__ import annotations

import re

import pandas as pd
import pytest
from pypdf import PdfReader
from streamlit.testing.v1 import AppTest

from conftest import ROOT, read

STEP5 = "05_outputs/ibp_decisions/DemandIQ_Step5_IBP_Decision_Plan.csv"
STEP6A = "05_outputs/decision_layer/DemandIQ_Step6A_{}.csv"
STEP8B = "05_outputs/peak_season_diagnosis/DemandIQ_Step8B_{}.csv"
OUTPUTS = [STEP5] + [STEP6A.format(n) for n in ("Executive_KPI_Summary", "Series_Decision_Summary",
                                               "Weekly_Planning_Trajectory")] + [
    STEP8B.format(n) for n in ("Step5_Reconciliation", "Summary_Metrics", "Replenishment_Proxy_Backtest",
                               "Replenishment_Proxy_Series_Backtest")]

DOCS = {
    "README": "README.md",
    "decision page": "06_docs/DemandIQ_Step8_Peak_Season_Decisions.md",
    "portfolio copy": "06_docs/DemandIQ_Portfolio_Copy.md",
    "v1 README": "05_outputs/v1_published_plan/README.md",
    "appendix": "06_docs/DemandIQ_Technical_Appendix.md",
    "app README": "07_streamlit_app/README_app.md",
    "brief": "06_docs/DemandIQ_Peak_Season_Brief.pdf",
}
CODE = ["04_scripts/step5/step5_ibp_decision_engine.py", "04_scripts/step6/step6a_decision_layer.py",
        "04_scripts/step8/step8b_step5_reconciliation.py", "04_scripts/step8/step8c_build_brief.py",
        "04_scripts/step8/step8_peak_diagnosis.py", *sorted(
            str(p.relative_to(ROOT)) for p in (ROOT / "07_streamlit_app").rglob("*.py"))]

# Wording that presents the estimate as confirmed supply.
BANNED = [
    r"in[- _]transit(?! time)",          # "in-transit replenishment", "IN_TRANSIT" (not "transfer transit time")
    r"already in transit",
    r"committed[ _]replenishment",
    r"committed_seasonal",               # the old split column; 'committed' now means seasonal drops only
    r"corrected (?:plan|calls|step 5|engine|supply view)",
    r"no escalation returns(?! under the tested)",
    r"step 5 corrected",
]
# Reader-facing wording only (docs, brief, app): the seasonal drops are not "committed".
BANNED_READER = [r"committed seasonal", r"committed receipts", r"committed supply"]


def text_of(relative: str) -> str:
    path = ROOT / relative
    if path.suffix == ".pdf":
        raw = " ".join(page.extract_text() or "" for page in PdfReader(path).pages)
    else:
        raw = path.read_text(encoding="utf-8")
    for ligature, letters in {"ﬁ": "fi", "ﬂ": "fl", "‑": "-", "­": ""}.items():
        raw = raw.replace(ligature, letters)
    return " ".join(raw.split()).lower()


@pytest.fixture(scope="module")
def docs() -> dict[str, str]:
    return {name: text_of(path) for name, path in DOCS.items()}


def banned_hits(text: str) -> list[str]:
    return [m.group(0) for pattern in BANNED for m in re.finditer(pattern, text, flags=re.I)]


# --------------------------------------------------------------------------- outputs

@pytest.mark.parametrize("relative", OUTPUTS)
def test_outputs_never_call_the_estimate_confirmed(relative):
    frame = read(relative, dtype=str, keep_default_na=False)
    hits = banned_hits(" ".join(frame.columns))
    for column in frame.columns:
        values = frame[column].unique()
        if len(values) < 200:  # text fields; numeric columns have many distinct values
            hits += banned_hits(" ".join(values))
    assert hits == [], f"{relative}: {sorted(set(hits))}"


def test_step5_rows_carry_provenance_and_condition():
    plan = read(STEP5)
    assert set(plan.seasonal_receipt_projection_status) == {"PROJECTED_NOT_CONFIRMED"}
    (seasonal,) = set(plan.seasonal_receipt_provenance)
    assert "SHIFTED 52 WEEKS" in seasonal and "NOT CONFIRMED SUPPLIER ORDERS" in seasonal
    assert "COMPATIBILITY" in seasonal
    assert set(plan.supply_view) == {"SEASONAL_DROPS_PLUS_ESTIMATED_REPLENISHMENT"}
    assert set(plan.replenishment_confirmation_status) == {"UNCONFIRMED_ESTIMATE"}
    (provenance,) = set(plan.replenishment_receipt_provenance)
    assert "SHIFTED 52 WEEKS" in provenance and "NOT CONFIRMED OPEN ORDERS" in provenance
    (condition,) = set(plan.call_condition)
    assert "ARRIVES AS MODELLED" in condition
    assert "CONFIRM OPEN-ORDER QUANTITIES AND RECEIPT DATES" in condition
    assert "PUBLISHED ESCALATION LIST" in condition
    assert "PROJECTED SEASONAL DROPS" in condition and "NEITHER IS A CONFIRMED SUPPLIER ORDER" in condition


def test_decision_layer_status_is_conditional_with_the_comparison():
    exec_row = read(STEP6A.format("Executive_KPI_Summary")).iloc[0]
    status = exec_row.portfolio_decision_status
    assert status.startswith("IF ESTIMATED REPLENISHMENT ARRIVES AS MODELLED: NO ESCALATION - 2 HOLD + 7 PROTECT")
    assert "WITH ZERO REPLENISHMENT (PUBLISHED LIST): 3 ESCALATE + 6 PROTECT" in status
    assert "CONFIRM OPEN-ORDER QUANTITIES AND RECEIPT DATES" in status
    assert status.endswith("SEASONAL DROPS ARE PROJECTED FROM LAST YEAR, NOT CONFIRMED SUPPLIER ORDERS")
    assert exec_row.seasonal_receipt_projection_status == "PROJECTED_NOT_CONFIRMED"
    series = read(STEP6A.format("Series_Decision_Summary"))
    assert series.zero_replenishment_planner_action.value_counts().to_dict() == {"PROTECT": 6, "ESCALATE": 3}
    assert set(series.replenishment_confirmation_status) == {"UNCONFIRMED_ESTIMATE"}


def test_step8b_labels_are_conditional():
    metrics = read(STEP8B.format("Summary_Metrics")).set_index("metric").value
    assert metrics["Replenishment confirmation status"] == "UNCONFIRMED_ESTIMATE"
    assert metrics["Seasonal drop projection status"] == "PROJECTED_NOT_CONFIRMED"
    assert "projected date, not a supplier date" in " ".join(metrics.index)
    assert not any(name.startswith("Step 5 corrected") for name in metrics.index)
    assert metrics["Step 5 if the estimate arrives as modelled: ESCALATE"] == "0"
    assert metrics["v1 published (zero replenishment): ESCALATE"] == "3"


# --------------------------------------------------------------------------- docs and brief

@pytest.mark.parametrize("name", list(DOCS))
def test_docs_never_call_the_estimate_confirmed(docs, name):
    assert banned_hits(docs[name]) == []
    assert [p for p in BANNED_READER if re.search(p, docs[name])] == []


@pytest.mark.parametrize("relative", [c for c in CODE if c.startswith("07_streamlit_app")])
def test_app_never_calls_seasonal_drops_committed(relative):
    text = text_of(relative).replace("committed_receipt", "")  # the legacy column name is allowed
    assert [p for p in BANNED_READER if re.search(p, text)] == []


@pytest.mark.parametrize("name", ["README", "decision page", "brief", "v1 README", "app README"])
def test_seasonal_drops_are_explained_as_projected(docs, name):
    text = docs[name]
    assert re.search(r"seasonal drops.{0,120}projected|projected.{0,40}seasonal drops|receipts are projected",
                     text), "seasonal drops must be described as projected"
    assert re.search(r"not confirmed (?:supplier )?orders", text)


@pytest.mark.parametrize("name", ["README", "decision page", "v1 README", "app README"])
def test_legacy_column_name_is_explained(docs, name):
    text = docs[name]
    assert "committed_receipt_units" in text and "projected_not_confirmed" in text


def test_portfolio_copy_does_not_overclaim_reproducibility(docs):
    text = docs["portfolio copy"]
    assert "one command rebuilds every output" not in text
    assert "rebuilds the reproducible downstream outputs" in text
    assert "step 3 data generator is still missing" in text
    assert "row-level step 4a reconstruction is still missing" in text
    assert "refits" in text and "drift" in text


@pytest.mark.parametrize("relative", CODE)
def test_code_and_app_never_call_the_estimate_confirmed(relative):
    assert banned_hits(text_of(relative)) == []


CONFIRM = re.compile(r"confirms? open[- ]orders?(?: quantities)? and (?:receipt )?dates")


@pytest.mark.parametrize("name", ["README", "decision page", "brief", "v1 README", "portfolio copy", "app README"])
def test_conditional_result_comparison_and_confirmation(docs, name):
    text = docs[name]
    assert "estimate" in text
    assert re.search(r"arrives? as modelled", text), "result must be conditional on the estimate arriving"
    assert re.search(r"0 escalate, 7 protect, 2 hold", text)
    assert re.search(r"3 escalat", text), "the zero-replenishment comparison must stay visible"
    assert re.search(r"zero[- ]replenishment|zero replenishment", text)
    assert CONFIRM.search(text), "a planner must confirm open orders and receipt dates"


@pytest.mark.parametrize("name", ["README", "decision page", "brief"])
def test_sensitivity_is_not_presented_as_assurance(docs, name):
    text = docs[name]
    assert "57–71%" in text, "the series-week backtest error must be stated"
    assert "one scenario, not a bound" in text
    assert re.search(r"30(?:\.0)?%", text), "the largest escalation threshold must be stated"


@pytest.mark.parametrize("name", ["README", "decision page"])
def test_threshold_and_stress_are_distinguished(docs, name):
    text = docs[name]
    assert "29.5%" in text and re.search(r"30(?:\.0)?%", text)
    assert "70.5%" in text or "183 estimated units" in text
    assert "not confirmed open orders" in text


# --------------------------------------------------------------------------- app

APP = ROOT / "07_streamlit_app"


def rendered(script_body: str) -> str:
    script = f"import sys\nsys.path.insert(0, {str(APP)!r})\n" + script_body
    app = AppTest.from_string(script, default_timeout=120).run()
    assert not app.exception, [e.value for e in app.exception]
    return " ".join(m.value for m in app.markdown)


def test_service_page_states_the_condition():
    page = APP / "pages" / "3_service_inventory_risk.py"
    text = rendered(f"""
import importlib.util
spec = importlib.util.spec_from_file_location("page", {str(page)!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.render()
""")
    assert "If the estimated replenishment arrives as modelled" in text
    assert "not confirmed open orders" in text and "with zero replenishment, 3 series escalate" in text
    assert "estimated replenishment (unconfirmed" in text
