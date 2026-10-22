"""DemandIQ Step 8C: build and verify the two-page peak-season brief (HTML -> PDF).

Every number in the brief is derived from a committed CSV in `facts()`, which
names the file it comes from. The HTML template holds no numbers except the
policy constants listed in POLICY. After building, `verify()` checks the PDF:

    - exactly two Letter pages, with no text smaller than 7.5 pt;
    - every number in the PDF text is a derived fact or a declared policy
      constant (no stray hand-typed figure);
    - every derived fact is present.

    python 04_scripts/step8/step8c_build_brief.py              build, then verify
    python 04_scripts/step8/step8c_build_brief.py --verify     verify the committed PDF only

Needs Playwright's Chromium: python -m playwright install chromium
Fonts are bundled (08_assets/fonts, SIL Open Font License), so the layout is
the same on any machine.
"""

from __future__ import annotations

import argparse
import base64
import html
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
STEP8 = ROOT / "05_outputs" / "peak_season_diagnosis"
PDF_FILE = ROOT / "06_docs" / "DemandIQ_Peak_Season_Brief.pdf"
HTML_FILE = ROOT / "build" / "brief" / "DemandIQ_Peak_Season_Brief.html"
CHART_FILE = ROOT / "08_assets" / "charts" / "step8_fill_trend.png"
FONT_DIR = ROOT / "08_assets" / "fonts"

SOURCES = {
    "headline": STEP8 / "DemandIQ_Step8_Headline_Metrics.csv",
    "recommendation": STEP8 / "DemandIQ_Step8_Peak_Buy_Recommendation.csv",
    "feasibility": STEP8 / "DemandIQ_Step8_Peak_Move_Feasibility.csv",
    "validation": STEP8 / "DemandIQ_Step8_Peak_Buy_Validation.csv",
    "queue": STEP8 / "DemandIQ_Step8_Corrected_SOE_Queue.csv",
    "concentration": STEP8 / "DemandIQ_Step8_Loss_Concentration_PY2026.csv",
    "reconciliation": STEP8 / "DemandIQ_Step8B_Summary_Metrics.csv",
    "launch_buy": ROOT / "05_outputs/launch_step7e/DemandIQ_Step7E_Initial_Buy_Plan.csv",
    "launch_policy": ROOT / "05_outputs/launch_step7f/DemandIQ_Step7F_Policy_Sensitivity.csv",
}

# The only numbers the template may contain: governed policy, not results.
POLICY = {
    "overseas_lead": "22-week",      # seasonal buy lane, Step 3A assumptions workbook
    "window": "13-week",             # published S&OE planning horizon
    "guardrail": "50%",              # over-buy guardrail, Step 8 policy assumption
    "checkpoints": "W1–W2",          # launch checkpoints, Step 7E
}

MIN_FONT_PT = 7.5  # readability floor checked by verify(); not printed
PAGE_HEIGHT_PT, BOTTOM_MARGIN_PT = 792.0, 0.55 * 72  # Letter, @page margin
HEADROOM_PT = 24.0  # free space each page must keep above the bottom margin. CI's
                    # Linux runner lays page 1 out about 15 pt longer than a local build
                    # with the same Chromium and fonts; this keeps both on 2 pages.
NUMBER = re.compile(r"(?<![A-Za-z0-9_.])\d[\d,]*(?:\.\d+)?(?![\d_])")


@dataclass(frozen=True)
class Fact:
    text: str
    source: str


def _n(x: float) -> str:
    return f"{x:,.0f}"


def _day(value) -> str:
    return pd.Timestamp(value).strftime("%b %-d")


def facts() -> dict[str, Fact]:
    """Every number in the brief, formatted, with the CSV it comes from."""
    h = pd.read_csv(SOURCES["headline"]).set_index("metric").value
    rec = pd.read_csv(SOURCES["recommendation"])
    feas = pd.read_csv(SOURCES["feasibility"])
    val = pd.read_csv(SOURCES["validation"])
    queue = pd.read_csv(SOURCES["queue"])
    cells = pd.read_csv(SOURCES["concentration"])
    s8b = pd.read_csv(SOURCES["reconciliation"]).set_index("metric").value
    buy = pd.read_csv(SOURCES["launch_buy"])
    policy = pd.read_csv(SOURCES["launch_policy"])

    def m(name: str) -> float:
        return float(h[name])

    def b(name: str) -> int:
        return int(float(s8b[name]))

    H, R, F = "Step 8 headline metrics", "Step 8 peak-buy recommendation", "Step 8 move feasibility"
    overseas = pd.to_datetime(feas.latest_order_overseas_lane)
    chase = sorted(set(pd.to_datetime(feas.latest_order_chase_lane)))
    chosen = buy[buy.recommended_flag == 1].iloc[0]
    fires = policy[policy.would_trigger == "YES"].sort_values("threshold_pp").iloc[0]
    plan_date = pd.Timestamp(h["Plan as-of date"])
    calls = queue.corrected_action.value_counts()

    return {
        "plan_date": Fact(f"{plan_date:%B %-d, %Y}", H),
        "fill_2022": Fact(f"{m('Dec-Feb fill, PY2022'):.0f}%", H),
        "fill_2026": Fact(f"{m('Dec-Feb fill, PY2026'):.0f}%", H),
        "fill_2022_exact": Fact(f"{m('Dec-Feb fill, PY2022'):.1f}%", H),
        "fill_2026_exact": Fact(f"{m('Dec-Feb fill, PY2026'):.1f}%", H),
        "lost_revenue": Fact(f"CAD {m('Lost revenue, PY2026') / 1e6:.2f}M", H),
        "lost_revenue_share": Fact(f"{m('Lost revenue as share of net revenue, PY2026'):.1f}%", H),
        "change": Fact(_n(m("Indicative next-peak change")), H),
        "change_vs_sales": Fact(f"+{rec.change_units.sum() / rec.decfeb_sold_units.sum() * 100:.0f}%", R),
        "moved": Fact(_n(rec.moved_units.sum()), R),
        "new": Fact(_n(rec.new_units.sum()), R),
        "accepted_gap": Fact(_n(rec.accepted_gap_units.sum()), R),
        "order_first": Fact(_day(overseas.min()), F),
        "order_last": Fact(_day(overseas.max()), F),
        "order_first_series": Fact(str(int((overseas == overseas.min()).sum())), F),
        "order_last_series": Fact(str(int((overseas == overseas.max()).sum())), F),
        "chase_first": Fact(_day(chase[0]), F),
        "chase_last": Fact(_day(chase[-1]), F),
        "chase_floor": Fact(_n(feas.chase_only_units.sum()), F),
        "october_drop": Fact(_day(h["Regular October-drop order date for the next peak"]), H),
        "weeks_earlier": Fact(f"{feas.weeks_earlier_for_moved_units.min():.0f}–"
                              f"{feas.weeks_earlier_for_moved_units.max():.0f}", F),
        "headroom": Fact(str(h["Series needing new units that fit last season's chase headroom"]), H),
        "buy_basis": Fact(f"{abs(m('Buy basis vs prior-year reconstructed demand, PY2026')):.1f}%", H),
        "uplift": Fact(f"{m('Reconstruction uplift, Dec-Feb PY2026'):.0f}%", H),
        "timing": Fact(f"{m('Timing share of PY2026 lost units'):.0f}%", H),
        "chase_low": Fact(f"{m('Chase trigger rate, lowest-loss quartile'):.0f}", H),
        "chase_high": Fact(f"{m('Chase trigger rate, highest-loss quartile'):.0f}%", H),
        "unused_chase": Fact(_n(m("Unused chase capacity, PY2026")), H),
        "window_share": Fact(f"{m('Share of lost units in Jul-Sep (13-week S&OE window), PY2022-PY2026'):.1f}%", H),
        "series": Fact(str(len(rec)), R),
        "supply_changes": Fact(_n(m("Series changed: replenishment added to supply")), H),
        "weather_changes": Fact(_n(m("Series changed: weather scenario")) if m("Series changed: weather scenario")
                                else "none", H),
        "cells": Fact(str(len(cells)), "Step 8 loss concentration"),
        "top20_observable": Fact(
            f"{m('Top 20 cells by stockout days (observable selection), share of true lost revenue'):.1f}%", H),
        "top20_truth": Fact(f"{m('Top 20 cells by true lost revenue, share of PY2026 lost revenue'):.1f}%", H),
        "top20": Fact("20", H),
        "v1_escalations": Fact(str(b("v1 published (zero replenishment): ESCALATE")), "Step 8B summary"),
        "step5_escalate": Fact(str(b("Step 5 if the estimate arrives as modelled: ESCALATE")), "Step 8B summary"),
        "step5_protect": Fact(str(b("Step 5 if the estimate arrives as modelled: PROTECT")), "Step 8B summary"),
        "step5_hold": Fact(str(b("Step 5 if the estimate arrives as modelled: HOLD")), "Step 8B summary"),
        "est_replen": Fact(_n(float(s8b["Estimated replenishment in the 13-week projection "
                                        "(unconfirmed, not open orders)"])), "Step 8B summary"),
        "est_replen_by": Fact(_day(s8b["Last projected replenishment arrival (projected date, not a supplier date)"]),
                              "Step 8B summary"),
        "replen_week_error": Fact(
            f"{float(s8b['Replenishment proxy series-week WAPE, best backtest year']):.0f}–"
            f"{float(s8b['Replenishment proxy series-week WAPE, worst backtest year']):.0f}%", "Step 8B summary"),
        "replen_stress": Fact(f"{float(s8b['Replenishment stress applied (worst backtest series WAPE)']):.1f}%",
                              "Step 8B summary"),
        "replen_needed": Fact(f"{float(s8b['Most replenishment any v1 escalation needs to clear']):.0f}%",
                              "Step 8B summary"),
        "watch": Fact(str(int(calls.get("WATCH", 0))), "Step 8 corrected queue"),
        "agree": Fact(f"{b('Series where Step 5 and Step 8 agree')} of {len(rec)}", "Step 8B summary"),
        "launch_reserve": Fact(_n(m("Launch reserve units")), H),
        "launch_buy": Fact(_n(chosen.initial_buy_units), "Step 7E initial buy"),
        "launch_ecom_lost": Fact(_n(m("Launch ECOM lost units with reserve idle")), H),
        "launch_rule_pp": Fact(f"{fires.threshold_pp:.0f}-pp", "Step 7F policy sensitivity"),
        "rank_match": Fact(f"{int((val.priority_rank == val.true_priority_rank).sum())} of {len(val)}",
                           "Step 8 validation"),
        "calls_survive": Fact("every call" if val.call_agrees.all() else f"{int(val.call_agrees.sum())} of {len(val)} calls",
                              "Step 8 validation"),
        "gap_recovered": Fact(f"{m('Planner Dec-Feb gap as share of true gap'):.0f}%", H),
        "new_share_planner": Fact(f"{m('New-unit share of the change, planner view'):.0f}%", H),
        "new_share_truth": Fact(f"{m('Quantity share of lost units, simulation truth'):.0f}%", H),
    }


def series_rows() -> list[list[str]]:
    rec = pd.read_csv(SOURCES["recommendation"]).sort_values("priority_rank")
    rows = []
    for r in rec.itertuples():
        channel = "ECOM" if r.channel_id == "ECOM" else r.channel_id.title()
        rows.append([f"{r.sku_id} {channel}", f"+{r.gap_pct_of_sales:.0f}%", _n(r.change_units),
                     _n(r.moved_units), _n(r.new_units), r.call])
    return rows


# --------------------------------------------------------------------------- template

# Fonts are embedded as data URIs: Chromium blocks file:// web fonts (CORS),
# and a unique family name stops a system-installed Carlito from masking that.
CSS = """
@font-face {{ font-family: 'DemandIQ Carlito'; src: url('{regular}'); font-weight: 400; font-style: normal; }}
@font-face {{ font-family: 'DemandIQ Carlito'; src: url('{bold}'); font-weight: 700; font-style: normal; }}
@font-face {{ font-family: 'DemandIQ Carlito'; src: url('{italic}'); font-weight: 400; font-style: italic; }}
@page {{ size: Letter; margin: 0.55in 0.6in; }}
* {{ box-sizing: border-box; }}
body {{ font-family: 'DemandIQ Carlito', sans-serif; color: #0b0b0b; font-size: 9.8pt; line-height: 1.3; margin: 0; }}
.kicker {{ color: #2a78d6; font-weight: 700; letter-spacing: .08em; font-size: 8.5pt; text-transform: uppercase; }}
h1 {{ font-size: 20pt; margin: 2px 0 2px; line-height: 1.15; }}
.sub {{ color: #52514e; font-size: 9.5pt; margin-bottom: 10px; }}
h2 {{ font-size: 12pt; margin: 9px 0 3px; padding-bottom: 2px; border-bottom: 1px solid #e1e0d9; }}
.lead {{ font-size: 11pt; line-height: 1.38; margin: 4px 0 8px; }}
.kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 6px 0 8px; }}
.kpi {{ border: 1px solid #e1e0d9; border-radius: 6px; padding: 7px 9px; }}
.kpi b {{ display: block; font-size: 15pt; line-height: 1.1; }}
.kpi span {{ color: #52514e; font-size: 8.6pt; }}
.kpi.hot {{ border-color: #2a78d6; background: #f2f7fd; }}
img {{ display: block; width: 94%; margin: 0 auto; border: 1px solid #e1e0d9; border-radius: 6px; }}
ul {{ margin: 3px 0 0 0; padding-left: 16px; }} li {{ margin: 0 0 3px; }}
.tag {{ font-size: 7.6pt; color: #52514e; border: 1px solid #c3c2b7; border-radius: 3px; padding: 0 4px; margin-left: 4px; white-space: nowrap; }}
table {{ width: 100%; border-collapse: collapse; font-size: 9pt; margin-top: 4px; }}
th {{ text-align: left; color: #52514e; font-weight: 600; border-bottom: 1px solid #c3c2b7; padding: 3px 5px; }}
td {{ border-bottom: 1px solid #ecebe6; padding: 1px 5px; vertical-align: top; }}
.r {{ text-align: right; }} th.r {{ text-align: right; }}
.total td {{ font-weight: 700; border-top: 1px solid #c3c2b7; }}
.note {{ color: #52514e; font-size: 8.4pt; }}
.box {{ background: #f7f7f4; border-radius: 6px; padding: 6px 10px; margin-top: 6px; }}
.page {{ page-break-after: always; }}
.foot {{ color: #898781; font-size: 7.8pt; margin-top: 10px; }}
"""


def render(f: dict[str, Fact]) -> str:
    v = {k: html.escape(fact.text) for k, fact in f.items()}
    p = {k: html.escape(text) for k, text in POLICY.items()}
    fonts = {style: "data:font/ttf;base64,"
             + base64.b64encode((FONT_DIR / f"Carlito-{style.title()}.ttf").read_bytes()).decode()
             for style in ("regular", "bold", "italic")}
    chart = base64.b64encode(CHART_FILE.read_bytes()).decode()
    rows = "".join(
        "<tr>" + "".join(f"<td{' class=r' if 1 <= i <= 4 else ''}>{html.escape(c)}</td>" for i, c in enumerate(row))
        + "</tr>" for row in series_rows())
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS.format(**fonts)}</style></head><body>
<div class="page">
<div class="kicker">DemandIQ · Peak-season planning brief</div>
<h1>Plan the outerwear peak on demand, not on last year's sales</h1>
<div class="sub">Premium outerwear demand planning case study · Abhijit Mishra · retrospective decision evaluated at the {v['plan_date']} planning date · simulated data</div>
<p class="lead"><b>Peak-season fill fell from {v['fill_2022']} to {v['fill_2026']} in four plan years</b> because every buy starts from last year's sales, and stockouts suppress exactly the peak weeks. Evaluated at the {v['plan_date']} planning date, planning the coming peak on reconstructed demand meant an indicative <b>{v['change']} more units ({v['change_vs_sales']} on last peak's Dec–Feb sales)</b>, with orders due by <b>{v['order_first']}–{v['order_last']}</b>. Those deadlines have passed; this brief shows the decision the planner should have made then.</p>
<div class="kpis">
<div class="kpi"><b>{v['fill_2026_exact']}</b><span>Dec–Feb fill in PY2026, down from {v['fill_2022_exact']} in PY2022 <i>(truth)</i></span></div>
<div class="kpi"><b>{v['lost_revenue']}</b><span>lost revenue, {v['lost_revenue_share']} of net revenue <i>(truth, upper bound)</i></span></div>
<div class="kpi hot"><b>+{v['change']} units</b><span>indicative peak change at the planning date: {v['moved']} moved, {v['new']} new <i>(observable)</i></span></div>
<div class="kpi"><b>{v['order_first']}–{v['order_last']}</b><span>{p['overseas_lead']} order deadlines at the planning date, for arrival before the first stockout (now past)</span></div>
</div>
<img src="data:image/png;base64,{chart}" alt="Peak-season fill fell from {v['fill_2022']} to {v['fill_2026']} in four plan years">
<h2>Why it happens</h2>
<ul>
<li><b>The buy plans the business down.</b> Each buy starts from last year's sales, {v['buy_basis']} below last year's reconstructed demand. In Dec–Feb, reconstructed demand runs {v['uplift']} above sales.<span class=tag>observable</span></li>
<li><b>Most of the loss is timing.</b> {v['timing']} of lost units had stock arriving within the plan year, but after the stockouts.<span class=tag>truth</span></li>
<li><b>Chase is aimed at the wrong signal.</b> It fires in mid-September in {v['chase_low']}–{v['chase_high']} of cells whatever their eventual loss, and {v['unused_chase']} units of chase capacity went unused.<span class=tag>observable</span></li>
<li><b>The published {p['window']} plan looked at the wrong season.</b> Its summer window held {v['window_share']} of lost demand, and its {v['v1_escalations']} escalations assume zero replenishment. Weather changes {v['weather_changes']} of the {v['series']} planner actions; adding estimated replenishment changes {v['supply_changes']}.<span class=tag>observable</span></li>
</ul>
<p class="note">Evidence labels: <b>observable</b> = sales, in-stock days, receipts, inventory and reconstructed demand, which a planner can see. <b>Truth</b> = hidden simulation fields, used only to size the problem and to validate.</p>
</div>

<div>
<h2 style="margin-top:0">What the planner should have decided on {v['plan_date']}</h2>
<table>
<colgroup><col style="width:27%"><col style="width:45%"><col style="width:28%"></colgroup>
<tr><th>Decision</th><th>Quantity</th><th>Deadline · owner</th></tr>
<tr><td><b>Plan the peak on reconstructed demand; move stock before buying</b></td><td>Indicative +{v['change']}: {v['moved']} moved forward from spring replenishment, {v['new']} new, {v['accepted_gap']} accepted gap (excess guardrail)</td><td>Commit suppliers by {v['order_first']} ({v['order_first_series']} series) or {v['order_last']} ({v['order_last_series']}) · planner, S&amp;OP, supply</td></tr>
<tr><td><b>Size chase from the peak gap, not early shipments</b></td><td>Fallback floor of about {v['chase_floor']} units within last season's unused chase capacity</td><td>Chase order by {v['chase_first']} or {v['chase_last']} · planner with supply planning</td></tr>
<tr><td><b>Rank exceptions by stockout days</b>, by SKU × region × channel</td><td>Top {v['top20']} of {v['cells']} cells by stockout days capture {v['top20_observable']} of true lost revenue (true top {v['top20']}: {v['top20_truth']})</td><td>Each monthly S&amp;OP · Demand Planner</td></tr>
<tr><td><b>Escalate only shortfalls that survive forecast error</b></td><td>If {v['est_replen']} estimated replenishment units arrive as modelled (by {v['est_replen_by']}; unconfirmed): {v['step5_escalate']} escalate, {v['step5_protect']} protect, {v['step5_hold']} hold; error band adds {v['watch']} watch. Zero replenishment (published): {v['v1_escalations']} escalate.</td><td>Weekly S&amp;OE · planner confirms open orders and receipt dates before replacing the published list</td></tr>
<tr><td><b>Release launch reserve on a <span style="white-space:nowrap">{v['launch_rule_pp']}</span> channel-mix rule</b></td><td>{v['launch_reserve']}-unit reserve on a {v['launch_buy']}-unit buy; ECOM lost {v['launch_ecom_lost']} units while it sat idle</td><td>Launch checkpoints {p['checkpoints']}</td></tr>
</table>

<h2>Peak scenario by series <span class=tag>observable</span></h2>
<table>
<tr><th>Series</th><th class=r>Gap vs sales</th><th class=r>Change</th><th class=r>Moved</th><th class=r>New</th><th>Call</th></tr>
{rows}
<tr class=total><td>Total</td><td></td><td class=r>{v['change']}</td><td class=r>{v['moved']}</td><td class=r>{v['new']}</td><td>{v['accepted_gap']} units accepted as a gap</td></tr>
</table>
<p class="note">Change = (reconstructed − sold) Dec–Feb units × (1 + SKU growth), allocated to regions by stockout days. Unsold spring-replenishment stock moves first; the rest is new. No new units where over-buy exposure is at least {p['guardrail']} of estimated lost revenue (policy).</p>

<div class="box"><b>Could it have landed in time? (at the planning date; all dates now past)</b>
<ul>
<li><b>New units:</b> the regular October-drop order date ({v['october_drop']}) had already passed. New {p['overseas_lead']} orders had to be placed by {v['order_first']}–{v['order_last']}; supplier capacity was <b>unconfirmed</b>.</li>
<li><b>Moved units:</b> they had to ship {v['weeks_earlier']} weeks earlier than last season's spring receipts, which needed a supplier order change. Order-change windows are not modelled: <b>unconfirmed</b>.</li>
<li><b>Fallback:</b> chase alone could have landed about {v['chase_floor']} units, with orders due by {v['chase_first']}–{v['chase_last']}. New units fit last season's chase headroom in {v['headroom']} series.</li>
</ul></div>

<h2>How sure are we?</h2>
<ul>
<li><b>Direction: high.</b> Scored against simulation truth, the priority ranking matches {v['rank_match']} and {v['calls_survive']} survives recomputation with true demand. The observable top {v['top20']} cells capture {v['top20_observable']} of true lost revenue, against {v['top20_truth']} for the true top {v['top20']}.<span class=tag>truth</span></li>
<li><b>Size: conservative.</b> Reconstruction finds {v['gap_recovered']} of the true Dec–Feb gap. The planner view also asks for more new units than truth suggests ({v['new_share_planner']} vs {v['new_share_truth']}).<span class=tag>truth</span></li>
<li><b>Weekly escalations: conditional.</b> The replenishment estimate missed by {v['replen_week_error']} series-week in backtests. One published escalation needs {v['replen_needed']} of its estimate to clear; a {v['replen_stress']} cut is one scenario, not a bound.</li>
<li><b>Limits.</b> Simulated data with the failure modes designed in; the test is that the diagnosis finds them. Lost revenue assumes no substitution; supplier capacity, MOQs and order-change windows are not modelled.</li>
</ul>
<div class="foot">Every number is generated from the CSVs: <b>python 04_scripts/run_pipeline.py --check</b> · github.com/Abhijit2409/demandiq-retail-demand-planning · simulated data</div>
</div>
</body></html>"""


# --------------------------------------------------------------------------- build and verify

def build(pdf_path: Path = PDF_FILE) -> None:
    from playwright.sync_api import sync_playwright

    HTML_FILE.parent.mkdir(parents=True, exist_ok=True)
    HTML_FILE.write_text(render(facts()), encoding="utf-8")
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(HTML_FILE.resolve().as_uri())
        page.evaluate("document.fonts.ready")
        page.pdf(path=str(pdf_path), format="Letter", print_background=True, prefer_css_page_size=True)
        browser.close()


def pdf_text(pdf_path: Path) -> tuple[int, str, float]:
    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        text = " ".join(page.extract_text() or "" for page in pdf.pages)
        smallest = min(char["size"] for page in pdf.pages for char in page.chars)
        return len(pdf.pages), " ".join(text.split()), smallest


def page_bottoms(pdf_path: Path) -> list[float]:
    """Lowest text position on each page, in points from the top."""
    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        return [max(char["bottom"] for char in page.chars) for page in pdf.pages]


def pdf_fonts(pdf_path: Path) -> set[str]:
    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        return {char["fontname"] for page in pdf.pages for char in page.chars}


def verify(pdf_path: Path = PDF_FILE) -> list[str]:
    """Problems with the PDF; empty when it passes."""
    derived = facts()
    allowed = {t for fact in derived.values() for t in NUMBER.findall(fact.text)}
    allowed |= {t for row in series_rows() for cell in row for t in NUMBER.findall(cell)}
    allowed |= {t for text in POLICY.values() for t in NUMBER.findall(text)}
    pages, text, smallest = pdf_text(pdf_path)
    found = set(NUMBER.findall(text))
    problems = []
    fonts = pdf_fonts(pdf_path)
    if not fonts or not all("Carlito" in name for name in fonts):
        problems.append(f"PDF fonts are {sorted(fonts)}; expected only the bundled Carlito")
    if pages != 2:
        problems.append(f"{pages} pages (expected 2)")
    if smallest < MIN_FONT_PT:
        problems.append(f"smallest text is {smallest:.1f} pt (minimum {MIN_FONT_PT} pt)")
    limit = PAGE_HEIGHT_PT - BOTTOM_MARGIN_PT - HEADROOM_PT
    for number, bottom in enumerate(page_bottoms(pdf_path), start=1):
        if bottom > limit:
            problems.append(f"page {number} text ends {PAGE_HEIGHT_PT - BOTTOM_MARGIN_PT - bottom:.0f} pt above the "
                            f"bottom margin; keep at least {HEADROOM_PT:.0f} pt so other machines stay on 2 pages")
    stray = sorted(found - allowed)
    if stray:
        problems.append(f"numbers not derived from the CSVs or declared as policy: {stray}")
    for key, fact in derived.items():
        missing = [t for t in NUMBER.findall(fact.text) if t not in found]
        if missing:
            problems.append(f"fact '{key}' ({fact.text}, from {fact.source}) not in the PDF")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verify", action="store_true", help="verify the existing PDF without rebuilding")
    args = parser.parse_args()
    if not args.verify:
        build()
        print(f"Wrote {PDF_FILE.relative_to(ROOT)}")
    problems = verify()
    if problems:
        raise SystemExit("Brief verification FAILED:\n  " + "\n  ".join(problems))
    pages, _, smallest = pdf_text(PDF_FILE)
    print(f"Verified: {pages} pages, smallest text {smallest:.1f} pt, {len(facts())} derived facts present, "
          "no stray numbers.")


if __name__ == "__main__":
    main()
