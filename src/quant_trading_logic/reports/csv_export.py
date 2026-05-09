"""CSV export functionality for signals and watchlist results."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from quant_trading_logic.signals.strategy import SignalResult
from quant_trading_logic.signals.scanner import WatchlistScanResult


def export_signals_to_csv(signals: list[SignalResult], filepath: str) -> None:
    """Export a list of signals to CSV file.
    
    Args:
        signals: List of SignalResult objects to export
        filepath: Path to write CSV file to
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "timestamp",
        "ticker",
        "signal",
        "composite_score",
        "technical_score",
        "fundamental_score",
        "last_close",
        "buy_price",
        "sell_target",
        "stop_loss",
        "trend_ok",
        "momentum_ok",
        "breakout_ok",
        "rsi14",
        "atr14",
        "suggested_shares",
        "max_risk_amount",
        "risk_per_share",
    ]
    
    timestamp = datetime.now().isoformat()
    
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for signal in signals:
            writer.writerow({
                "timestamp": timestamp,
                "ticker": signal.ticker,
                "signal": signal.signal,
                "composite_score": signal.composite_score,
                "technical_score": signal.technical_score,
                "fundamental_score": signal.fundamental_score,
                "last_close": round(signal.last_close, 2),
                "buy_price": round(signal.buy_price, 2) if signal.buy_price else None,
                "sell_target": round(signal.sell_target, 2) if signal.sell_target else None,
                "stop_loss": round(signal.stop_loss, 2) if signal.stop_loss else None,
                "trend_ok": signal.trend_ok,
                "momentum_ok": signal.momentum_ok,
                "breakout_ok": signal.breakout_ok,
                "rsi14": round(signal.rsi14, 2),
                "atr14": round(signal.atr14, 2),
                "suggested_shares": signal.suggested_shares,
                "max_risk_amount": round(signal.max_risk_amount, 2) if signal.max_risk_amount else None,
                "risk_per_share": round(signal.risk_per_share, 4) if signal.risk_per_share else None,
            })


def export_watchlist_to_csv(scan: WatchlistScanResult, filepath: str) -> None:
    """Export watchlist scan results to CSV file.
    
    Args:
        scan: WatchlistScanResult from scanner
        filepath: Path to write CSV file to
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "timestamp",
        "ticker",
        "signal",
        "composite_score",
        "technical_score",
        "fundamental_score",
        "last_close",
        "buy_price",
        "sell_target",
        "stop_loss",
        "suggested_shares",
        "max_risk_amount",
    ]
    
    timestamp = datetime.now().isoformat()
    
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for signal in scan.results:
            writer.writerow({
                "timestamp": timestamp,
                "ticker": signal.ticker,
                "signal": signal.signal,
                "composite_score": signal.composite_score,
                "technical_score": signal.technical_score,
                "fundamental_score": signal.fundamental_score,
                "last_close": round(signal.last_close, 2),
                "buy_price": round(signal.buy_price, 2) if signal.buy_price else None,
                "sell_target": round(signal.sell_target, 2) if signal.sell_target else None,
                "stop_loss": round(signal.stop_loss, 2) if signal.stop_loss else None,
                "suggested_shares": signal.suggested_shares,
                "max_risk_amount": round(signal.max_risk_amount, 2) if signal.max_risk_amount else None,
            })
        
        # Append failed tickers section
        if scan.failed_tickers:
            f.write("\n\nFailed tickers:\n")
            for ticker in scan.failed_tickers:
                f.write(f"{ticker}\n")
