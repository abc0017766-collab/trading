"""Backtest analysis and statistics calculation."""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from quant_trading_logic.signals.strategy import evaluate_signal


@dataclass
class BacktestStats:
    ticker: str
    total_bars: int
    buy_signals: int
    win_signals: int
    loss_signals: int
    win_rate_percent: float
    latest_signal: str
    latest_close: float


def analyze_backtest(ticker: str, df: pd.DataFrame) -> BacktestStats:
    """Analyze backtest results and compute statistics.
    
    Args:
        ticker: Stock ticker symbol
        df: OHLCV dataframe with sufficient history
        
    Returns:
        BacktestStats with performance metrics
    """
    total_bars = len(df)
    buy_signals = 0
    profitable_count = 0
    loss_count = 0
    
    # Iterate through dataframe and count signals
    for i in range(1, len(df)):
        # Use data up to current row for signal evaluation
        current_df = df.iloc[: i + 1].copy()
        try:
            signal = evaluate_signal(ticker, current_df)
            
            if signal.signal == "BUY":
                buy_signals += 1
                
                # Simple win/loss check: if next bar closes above target, it's a win
                if i + 1 < len(df):
                    next_close = df.iloc[i + 1]["Close"]
                    if signal.sell_target and next_close > signal.sell_target:
                        profitable_count += 1
                    elif signal.stop_loss and next_close < signal.stop_loss:
                        loss_count += 1
        except Exception:
            # Skip bars where we can't compute signal (e.g., insufficient history)
            continue
    
    win_rate = (profitable_count / buy_signals * 100) if buy_signals > 0 else 0.0
    
    # Get latest signal
    latest_signal = evaluate_signal(ticker, df)
    
    return BacktestStats(
        ticker=ticker.upper(),
        total_bars=total_bars,
        buy_signals=buy_signals,
        win_signals=profitable_count,
        loss_signals=loss_count,
        win_rate_percent=round(win_rate, 2),
        latest_signal=latest_signal.signal,
        latest_close=latest_signal.last_close,
    )
