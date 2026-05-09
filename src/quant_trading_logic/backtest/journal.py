"""Trade journal functionality for logging signals and tracking outcomes."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from quant_trading_logic.signals.strategy import SignalResult


def log_signal_to_journal(signal: SignalResult, journal_path: str) -> None:
    """Log a signal to the trade journal CSV file.
    
    Args:
        signal: SignalResult object to log
        journal_path: Path to journal CSV file (will be created if not exists)
    """
    path = Path(journal_path)
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
        "risk_per_share",
        "trend_ok",
        "momentum_ok",
        "breakout_ok",
        "exit_price",
        "exit_date",
        "pnl",
        "pnl_percent",
        "status",
    ]
    
    # Check if file exists to decide if we need to write header
    file_exists = path.exists() and path.stat().st_size > 0
    
    timestamp = datetime.now().isoformat()
    
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
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
            "risk_per_share": round(signal.risk_per_share, 4) if signal.risk_per_share else None,
            "trend_ok": signal.trend_ok,
            "momentum_ok": signal.momentum_ok,
            "breakout_ok": signal.breakout_ok,
            "exit_price": None,  # To be filled in manually or via separate closing logic
            "exit_date": None,   # To be filled in manually or via separate closing logic
            "pnl": None,         # To be calculated when trade closes
            "pnl_percent": None, # To be calculated when trade closes
            "status": "open" if signal.signal == "BUY" else "no_entry",
        })


def get_open_trades(journal_path: str) -> list[dict]:
    """Retrieve all open trades from the journal.
    
    Args:
        journal_path: Path to journal CSV file
        
    Returns:
        List of dictionaries representing open trades
    """
    path = Path(journal_path)
    if not path.exists():
        return []
    
    open_trades = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("status") == "open":
                open_trades.append(row)
    
    return open_trades


def close_trade(journal_path: str, row_index: int, exit_price: float) -> None:
    """Mark a trade as closed and calculate PnL.
    
    Args:
        journal_path: Path to journal CSV file
        row_index: Index of the row to close (0-based, excluding header)
        exit_price: Price at which the trade was closed
    """
    path = Path(journal_path)
    if not path.exists():
        return
    
    rows = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    if row_index < 0 or row_index >= len(rows):
        return
    
    trade = rows[row_index]
    buy_price = float(trade["buy_price"]) if trade["buy_price"] else 0
    shares = int(trade["suggested_shares"]) if trade["suggested_shares"] else 0
    
    if buy_price > 0 and shares > 0:
        pnl = (exit_price - buy_price) * shares
        pnl_percent = ((exit_price - buy_price) / buy_price) * 100
        
        trade["exit_price"] = round(exit_price, 2)
        trade["exit_date"] = datetime.now().isoformat()
        trade["pnl"] = round(pnl, 2)
        trade["pnl_percent"] = round(pnl_percent, 2)
        trade["status"] = "closed"
    
    # Write back to file
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
