"""README, decision page, brief and portfolio copy quote the same numbers as the CSVs."""

from __future__ import annotations

import re

import pandas as pd
import pytest
from pypdf import PdfReader

from conftest import ROOT, read

DIR = "05_outputs/peak_season_diagnosis/"
DOCS = {
    "README": ROOT / "README.md",
    "decision page": ROOT / "06_docs/DemandIQ_Step8_Peak_Season_Decisions.md",
    "portfolio copy": ROOT / "06_docs/DemandIQ_Portfolio_Copy.md",
    "brief": ROOT / "06_docs/DemandIQ_Peak_Season_Brief.pdf",
}
LINKED = ["README.md", "06_docs/DemandIQ_Step8_Peak_Season_Decisions.md", "06_docs/DemandIQ_Portfolio_Copy.md",
          "06_docs/DemandIQ_Technical_Appendix.md", "06_docs/DemandIQ_Reproducibility.md",
          "05_outputs/v1_published_plan/README.md"]
STALE = ["act now", "window is closing", "can still land", "decision is due now", "10,339 more units (+21%)",
         "+10,339 units (+21%)", "+21% on last", "10,017", "4,088", "5,930", "one-command rebuild of steps 3–7 is on the roadmap"]


def text_of(path) -> str:
    if path.suffix == ".pdf":  # pypdf keeps each table cell's text together
        raw = " ".join(page.extract_text() or "" for page in PdfReader(path).pages)
    else:
        raw = path.read_text(encoding="utf-8")
    return " ".join(raw.replace("‑", "-").split()).lower()


@pytest.fixture(scope="module")
def docs() -> dict[str, str]:
    return {name: text_of(path) for name, path in DOCS.items()}


def expected_tokens() -> dict[str, str]:
    """Canonical values, formatted from the outputs rather than typed in."""
    m = read(DIR + "DemandIQ_Step8_Headline_Metrics.csv").set_index("metric").value
    rec = read(DIR + "DemandIQ_Step8_Peak_Buy_Recommendation.csv")
    feas = read(DIR + "DemandIQ_Step8_Peak_Move_Feasibility.csv")
    s8b = read(DIR + "DemandIQ_Step8B_Summary_Metrics.csv").set_index("metric").value
    num = lambda k: float(m[k])  # noqa: E731
    day = lambda d: pd.Timestamp(d).strftime("%b %-d")  # noqa: E731
    protect, hold = int(float(s8b["Step 5 corrected: PROTECT"])), int(float(s8b["Step 5 corrected: HOLD"]))
    return {
        "fill PY2022": f"{num('Dec-Feb fill, PY2022'):.1f}%",
        "fill PY2026": f"{num('Dec-Feb fill, PY2026'):.1f}%",
        "change": f"{num('Indicative next-peak change'):,.0f}",
        "moved": f"{rec.moved_units.sum():,.0f}",
        "new": f"{rec.new_units.sum():,.0f}",
        "change vs sales": f"+{rec.change_units.sum() / rec.decfeb_sold_units.sum() * 100:.0f}%",
        "chase floor": f"{feas.chase_only_units.sum():,.0f}",
        "observable top 20": f"{num('Top 20 cells by stockout days (observable selection), share of true lost revenue'):.1f}%",
        "truth top 20": f"{num('Top 20 cells by true lost revenue, share of PY2026 lost revenue'):.1f}%",
        "buy basis": f"{abs(num('Buy basis vs prior-year reconstructed demand, PY2026')):.1f}%",
        "plan date": pd.Timestamp(m["Plan as-of date"]).strftime("%B %-d, %Y"),
        "order deadline 1": day(feas.latest_order_overseas_lane.min()),
        "order deadline 2": day(feas.latest_order_overseas_lane.max()),
        "chase deadline 1": day(feas.latest_order_chase_lane.min()),
        "chase deadline 2": day(feas.latest_order_chase_lane.max()),
        "in-transit units": f"{float(s8b['In-transit replenishment counted in the 13-week supply']):,.0f}",
        "corrected calls": f"0 escalate, {protect} protect, {hold} hold",
        "framing": "retrospective",
    }


@pytest.mark.parametrize("label, token", list(expected_tokens().items()))
def test_every_document_quotes_the_output(docs, label, token):
    missing = [name for name, text in docs.items() if token.lower() not in text]
    assert missing == [], f"{label} ({token}) missing from {missing}"


def test_no_stale_phrases(docs):
    found = [(name, phrase) for name, text in docs.items() for phrase in STALE if phrase.lower() in text]
    assert found == []


LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s#]+)(?:#[^)]*)?\)")
CODE_PATH = re.compile(r"`((?:0\d_|tests/|\.github/)[^`\s]*)`")


@pytest.mark.parametrize("relative", LINKED)
def test_links_and_paths_resolve(relative):
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    broken = [link for link in LINK.findall(text)
              if not link.startswith(("http://", "https://", "mailto:")) and not (path.parent / link).resolve().exists()]
    for code in CODE_PATH.findall(text):
        code = code.rstrip("/")
        if any(ch in code for ch in "*…<>") or code.endswith(":"):
            continue
        if not (ROOT / code).exists():
            broken.append(f"`{code}`")
    assert broken == []
