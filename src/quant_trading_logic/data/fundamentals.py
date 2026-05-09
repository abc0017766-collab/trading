from __future__ import annotations

from typing import Any

import yfinance as yf


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_fundamentals(ticker: str) -> dict[str, float | None]:
    """Fetch a compact set of fundamentals used for scoring.

    Values can be None when the provider has no data for the symbol.
    """
    info: dict[str, Any] = {}
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception:
        # Keep empty info; scoring can continue with missing values.
        info = {}

    return {
        "pe_ratio": _to_float(info.get("trailingPE")),
        "profit_margin": _to_float(info.get("profitMargins")),
        "revenue_growth": _to_float(info.get("revenueGrowth")),
        "debt_to_equity": _to_float(info.get("debtToEquity")),
    }
