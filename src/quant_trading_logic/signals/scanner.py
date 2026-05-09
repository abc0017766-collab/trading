from __future__ import annotations

from dataclasses import dataclass

from quant_trading_logic.data.fetch import fetch_daily_ohlcv
from quant_trading_logic.data.fundamentals import fetch_fundamentals
from quant_trading_logic.signals.strategy import SignalResult, evaluate_signal


@dataclass
class WatchlistScanResult:
    results: list[SignalResult]
    failed_tickers: list[str]


def scan_watchlist(
    tickers: list[str],
    period: str = "2y",
    account_size: float = 10000.0,
    risk_per_trade_pct: float = 1.0,
) -> WatchlistScanResult:
    valid_tickers = [t.strip().upper() for t in tickers if t and t.strip()]
    results: list[SignalResult] = []
    failed: list[str] = []

    for ticker in valid_tickers:
        try:
            df = fetch_daily_ohlcv(ticker, period=period)
            fundamentals = fetch_fundamentals(ticker)
            results.append(
                evaluate_signal(
                    ticker,
                    df,
                    fundamentals=fundamentals,
                    account_size=account_size,
                    risk_per_trade_pct=risk_per_trade_pct,
                )
            )
        except Exception:
            failed.append(ticker)

    results.sort(key=lambda r: (r.composite_score, r.signal == "BUY"), reverse=True)
    return WatchlistScanResult(results=results, failed_tickers=failed)
