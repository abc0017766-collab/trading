from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from quant_trading_logic.signals.strategy import evaluate_signal


@dataclass
class BacktestSummary:
    ticker: str
    bars: int
    latest_signal: str
    latest_close: float


def run_simple_backtest(ticker: str, df: pd.DataFrame) -> BacktestSummary:
    result = evaluate_signal(ticker, df)
    return BacktestSummary(
        ticker=ticker.upper(),
        bars=len(df),
        latest_signal=result.signal,
        latest_close=result.last_close,
    )
