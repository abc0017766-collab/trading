from __future__ import annotations

from quant_trading_logic.signals.strategy import SignalResult
from quant_trading_logic.signals.scanner import WatchlistScanResult
from quant_trading_logic.backtest.engine import BacktestSummary
from quant_trading_logic.backtest.analyzer import BacktestStats


def format_signal(signal: SignalResult) -> str:
    sizing_block = ""
    if signal.signal == "BUY":
        sizing_block = (
            f"\nMax risk amount: {signal.max_risk_amount}"
            f"\nRisk per share: {signal.risk_per_share}"
            f"\nSuggested shares: {signal.suggested_shares}"
        )

    return (
        f"Ticker: {signal.ticker}\n"
        f"Signal: {signal.signal}\n"
        f"Composite score: {signal.composite_score}/100 "
        f"(Technical {signal.technical_score} + Fundamental {signal.fundamental_score})\n"
        f"Last close: {signal.last_close}\n"
        f"Buy price: {signal.buy_price}\n"
        f"Sell target: {signal.sell_target}\n"
        f"Stop loss: {signal.stop_loss}\n"
        f"Trend OK: {signal.trend_ok} | Momentum OK: {signal.momentum_ok} | Breakout OK: {signal.breakout_ok}\n"
        f"RSI14: {signal.rsi14} | ATR14: {signal.atr14}"
        f"{sizing_block}"
    )


def format_backtest(summary: BacktestSummary) -> str:
    return (
        f"Backtest summary for {summary.ticker}\n"
        f"Bars: {summary.bars}\n"
        f"Latest close: {summary.latest_close}\n"
        f"Latest signal: {summary.latest_signal}"
    )


def format_backtest_stats(stats: BacktestStats) -> str:
    return (
        f"Backtest Analysis for {stats.ticker}\n"
        f"Total bars: {stats.total_bars}\n"
        f"Buy signals generated: {stats.buy_signals}\n"
        f"Profitable signals: {stats.win_signals}\n"
        f"Loss signals: {stats.loss_signals}\n"
        f"Win rate: {stats.win_rate_percent}%\n"
        f"Latest signal: {stats.latest_signal} (close: ${stats.latest_close:.2f})"
    )


def format_watchlist(scan: WatchlistScanResult, top: int = 10) -> str:
    rows = scan.results[: max(1, top)]
    header = "Ticker  Signal  Score  Close    Buy      Target   Stop"
    line = "-" * len(header)

    body_lines: list[str] = []
    for r in rows:
        body_lines.append(
            f"{r.ticker:<6}  {r.signal:<6}  {r.composite_score:>5}  "
            f"{r.last_close:>7.2f}  {str(r.buy_price or '-'):>7}  "
            f"{str(r.sell_target or '-'):>7}  {str(r.stop_loss or '-'):>7}"
        )

    failed_line = ""
    if scan.failed_tickers:
        failed_line = "\nFailed: " + ", ".join(scan.failed_tickers)

    return "\n".join([header, line, *body_lines]) + failed_line
