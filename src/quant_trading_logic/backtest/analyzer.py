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
    closed_trades: int
    win_signals: int
    loss_signals: int
    win_rate_percent: float
    latest_signal: str
    latest_close: float
    total_pnl: float
    ending_equity: float
    total_return_percent: float
    average_return_percent: float
    average_holding_days: float
    max_drawdown_percent: float


def _max_drawdown_percent(equity_curve: list[float]) -> float:
    if not equity_curve:
        return 0.0

    peak = equity_curve[0]
    max_drawdown = 0.0
    for equity in equity_curve:
        peak = max(peak, equity)
        if peak <= 0:
            continue
        drawdown = ((peak - equity) / peak) * 100.0
        max_drawdown = max(max_drawdown, drawdown)
    return round(max_drawdown, 2)


def analyze_backtest(
    ticker: str,
    df: pd.DataFrame,
    account_size: float = 10000.0,
    risk_per_trade_pct: float = 1.0,
    max_holding_days: int = 20,
    min_history: int = 200,
) -> BacktestStats:
    """Run a walk-forward backtest over historical OHLCV data.

    The simulation uses the existing signal logic on each bar, enters at that bar's
    close, then walks forward until stop loss, profit target, or a max holding
    period is reached. Only one trade is open at a time.
    """
    total_bars = len(df)
    if total_bars == 0:
        raise ValueError("Backtest requires non-empty OHLCV data")

    start_index = max(1, min_history)
    buy_signals = 0
    win_count = 0
    loss_count = 0
    closed_trades = 0
    total_pnl = 0.0
    trade_returns: list[float] = []
    holding_days: list[int] = []
    equity = float(account_size)
    equity_curve = [equity]

    i = start_index
    while i < total_bars - 1:
        current_df = df.iloc[: i + 1].copy()
        try:
            signal = evaluate_signal(
                ticker,
                current_df,
                account_size=equity,
                risk_per_trade_pct=risk_per_trade_pct,
            )
        except Exception:
            i += 1
            continue

        if (
            signal.signal != "BUY"
            or signal.buy_price is None
            or signal.stop_loss is None
            or signal.sell_target is None
            or not signal.suggested_shares
        ):
            i += 1
            continue

        buy_signals += 1
        exit_index = None
        exit_price = None

        last_index = min(total_bars - 1, i + max_holding_days)
        for j in range(i + 1, last_index + 1):
            bar = df.iloc[j]

            # Conservative assumption: if both levels are touched intraday,
            # treat the stop as having hit first.
            if float(bar["Low"]) <= signal.stop_loss:
                exit_index = j
                exit_price = signal.stop_loss
                break
            if float(bar["High"]) >= signal.sell_target:
                exit_index = j
                exit_price = signal.sell_target
                break

        if exit_index is None:
            exit_index = last_index
            exit_price = float(df.iloc[exit_index]["Close"])

        pnl = (exit_price - signal.buy_price) * signal.suggested_shares
        trade_return_pct = ((exit_price - signal.buy_price) / signal.buy_price) * 100.0
        days_held = max(1, exit_index - i)

        equity += pnl
        equity_curve.append(equity)
        total_pnl += pnl
        trade_returns.append(trade_return_pct)
        holding_days.append(days_held)
        closed_trades += 1

        if pnl > 0:
            win_count += 1
        elif pnl < 0:
            loss_count += 1

        i = exit_index + 1

    win_rate = (win_count / closed_trades * 100.0) if closed_trades > 0 else 0.0
    avg_return = sum(trade_returns) / len(trade_returns) if trade_returns else 0.0
    avg_holding_days = sum(holding_days) / len(holding_days) if holding_days else 0.0
    total_return_pct = ((equity - account_size) / account_size * 100.0) if account_size else 0.0
    latest_signal = evaluate_signal(ticker, df)

    return BacktestStats(
        ticker=ticker.upper(),
        total_bars=total_bars,
        buy_signals=buy_signals,
        closed_trades=closed_trades,
        win_signals=win_count,
        loss_signals=loss_count,
        win_rate_percent=round(win_rate, 2),
        latest_signal=latest_signal.signal,
        latest_close=latest_signal.last_close,
        total_pnl=round(total_pnl, 2),
        ending_equity=round(equity, 2),
        total_return_percent=round(total_return_pct, 2),
        average_return_percent=round(avg_return, 2),
        average_holding_days=round(avg_holding_days, 2),
        max_drawdown_percent=_max_drawdown_percent(equity_curve),
    )
