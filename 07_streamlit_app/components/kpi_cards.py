"""Backwards-compat shim. Card rendering now lives in components.cards.

Kept so existing imports remain valid; new code should import components.cards.
"""
from __future__ import annotations

from components.cards import kpi_grid, status_banner  # noqa: F401
