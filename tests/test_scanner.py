from __future__ import annotations

import pandas as pd

from quant_trading_logic.signals import scanner


def test_scan_watchlist_sorts_by_composite_score(monkeypatch) -> None:
    df = pd.DataFrame(
        {
            "Open": [100.0] * 260,
            "High": [101.0] * 260,
            "Low": [99.0] * 260,
            "Close": [100.0] * 260,
            "Volume": [100000] * 260,
        }
    )

    def fake_fetch_daily_ohlcv(ticker: str, period: str = "2y") -> pd.DataFrame:
        if ticker == "BAD":
            raise ValueError("bad ticker")
        return df

    def fake_fetch_fundamentals(ticker: str) -> dict[str, float | None]:
        # AAA should rank above BBB by fundamentals.
        if ticker == "AAA":
            return {
                "pe_ratio": 20.0,
                "profit_margin": 0.2,
                "revenue_growth": 0.15,
                "debt_to_equity": 50.0,
            }
        return {
            "pe_ratio": 45.0,
            "profit_margin": 0.01,
            "revenue_growth": -0.05,
            "debt_to_equity": 250.0,
        }

    monkeypatch.setattr(scanner, "fetch_daily_ohlcv", fake_fetch_daily_ohlcv)
    monkeypatch.setattr(scanner, "fetch_fundamentals", fake_fetch_fundamentals)

    result = scanner.scan_watchlist(["BBB", "AAA", "BAD"])
    assert [r.ticker for r in result.results][:2] == ["AAA", "BBB"]
    assert result.failed_tickers == ["BAD"]
