from __future__ import annotations

import yfinance as yf
import pandas as pd


def fetch_daily_ohlcv(ticker: str, period: str = "2y") -> pd.DataFrame:
    df = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False)
    if df is None or df.empty:
        raise ValueError(f"No data returned for ticker: {ticker}")

    # yfinance can return MultiIndex columns like ('Close', 'AAPL').
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    needed = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in data: {missing}")

    return df[needed].dropna().copy()
