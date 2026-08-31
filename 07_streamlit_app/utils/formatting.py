"""Reusable, UI-only number/label formatters for DemandIQ.

These change how governed values are DISPLAYED. They never alter the
underlying frozen dataframe values or business logic.
"""
from __future__ import annotations
import math
import pandas as pd


# ------------------------------------------------------------------
# Business-friendly labels (UI only; dataframe fields stay governed)
# ------------------------------------------------------------------

SKU_NAMES = {
    "APS-001": "Alpine Performance Shell",
    "CTS-001": "Core Technical Shell",
    "IMH-001": "Insulated Midlayer Hoody",
}

FIELD_LABELS = {
    "priority_tier": "Priority",
    "sku_id": "SKU",
    "channel_id": "Channel",
    "risk_type": "Risk",
    "planner_action": "Action",
    "base_13w_fill_rate": "13W Base Fill",
    "min_weekly_base_fill_rate": "Worst Weekly Fill",
    "worst_base_service_week": "Worst Week",
    "worst_week_service_gap_units": "Worst-Week Gap",
    "weeks_below_service_target": "Weeks Below Target",
    "base_final_wos": "Ending WOS",
    "chase_capacity_units": "Chase Capacity",
}

RISK_LABELS = {
    "WEEKLY_SERVICE_RISK": "Weekly Service Risk",
    "LOW_COVERAGE_RISK": "Low Coverage Risk",
    "BASE_SERVICE_RISK": "Base Service Risk",
    "SEVERE_SCENARIO_RISK": "Severe Scenario Risk",
    "EXCESS_INVENTORY_RISK": "Excess Inventory Risk",
    "BALANCED": "Balanced",
}


def sku_label(sku_id: str) -> str:
    name = SKU_NAMES.get(sku_id)
    return f"{sku_id} · {name}" if name else str(sku_id)


def series_label(sku_id: str, channel_id: str) -> str:
    return f"{sku_id} / {channel_id}"


# ------------------------------------------------------------------
# Number formatters
# ------------------------------------------------------------------

def _na(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


def units(x, suffix: str = " units") -> str:
    """Full integer units with thousands separators, e.g. '36,435 units'."""
    if _na(x):
        return "—"
    return f"{round(float(x)):,.0f}{suffix}"


def units_k(x, suffix: str = "K units") -> str:
    """Compact units for KPI cards, e.g. '36.4K units', '7.0K units'."""
    if _na(x):
        return "—"
    v = float(x)
    if abs(v) >= 1000:
        return f"{v / 1000:,.1f}{suffix}"
    return f"{v:,.0f} units"


def pct(x, decimals: int = 1) -> str:
    """Fraction (0..1) to percent, e.g. 0.9877 -> '98.8%'."""
    if _na(x):
        return "—"
    return f"{float(x) * 100:.{decimals}f}%"


def pct_points(x_fraction, decimals: int = 1, signed: bool = True) -> str:
    """Fraction difference to percentage points, e.g. 0.0677 -> '+6.8 pp'."""
    if _na(x_fraction):
        return "—"
    pp = float(x_fraction) * 100
    sign = "+" if (signed and pp >= 0) else ("" if pp >= 0 else "-")
    return f"{sign}{abs(pp):.{decimals}f} pp"


def cad(x) -> str:
    """CAD exposure proxy, e.g. '$192,468'. Not accounting profit."""
    if _na(x):
        return "—"
    return f"${round(float(x)):,.0f}"


def wos(x, decimals: int = 2) -> str:
    if _na(x):
        return "—"
    return f"{float(x):.{decimals}f} weeks"


def date_long(d) -> str:
    """'2026-08-24' / Timestamp -> 'Aug 24, 2026'."""
    if _na(d):
        return "—"
    ts = pd.Timestamp(d)
    return ts.strftime("%b %d, %Y")


def date_short(d) -> str:
    """-> 'Aug 24'."""
    if _na(d):
        return "—"
    return pd.Timestamp(d).strftime("%b %d")


def count_of(n, total) -> str:
    return f"{int(n)} of {int(total)}"
