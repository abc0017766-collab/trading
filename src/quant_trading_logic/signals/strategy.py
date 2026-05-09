from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from quant_trading_logic.signals.indicators import sma, rsi, atr
from quant_trading_logic.risk.positioning import (
    stop_loss,
    take_profit,
    recommend_position_size,
)


@dataclass
class SignalResult:
    ticker: str
    signal: str
    last_close: float
    buy_price: float | None
    sell_target: float | None
    stop_loss: float | None
    trend_ok: bool
    momentum_ok: bool
    breakout_ok: bool
    rsi14: float
    atr14: float
    technical_score: int
    fundamental_score: int
    composite_score: int
    max_risk_amount: float | None
    risk_per_share: float | None
    suggested_shares: int | None


def _score_technical(trend_ok: bool, momentum_ok: bool, breakout_ok: bool, rsi14: float) -> int:
    score = 0
    if trend_ok:
        score += 20
    if momentum_ok:
        score += 20
    if breakout_ok:
        score += 20

    # Add up to 10 points for RSI being near neutral momentum (55).
    rsi_bonus = max(0.0, 10.0 - abs(rsi14 - 55.0) / 3.0)
    score += int(round(rsi_bonus))
    return min(70, score)


def _score_fundamentals(fundamentals: dict[str, float | None] | None) -> int:
    if not fundamentals:
        return 0

    score = 0
    pe = fundamentals.get("pe_ratio")
    margin = fundamentals.get("profit_margin")
    growth = fundamentals.get("revenue_growth")
    debt = fundamentals.get("debt_to_equity")

    if pe is not None and 5 <= pe <= 35:
        score += 8
    if margin is not None and margin >= 0.08:
        score += 8
    if growth is not None and growth >= 0.05:
        score += 8
    if debt is not None and debt <= 120:
        score += 8

    return min(30, score)


def evaluate_signal(
    ticker: str,
    df: pd.DataFrame,
    fundamentals: dict[str, float | None] | None = None,
    account_size: float = 10000.0,
    risk_per_trade_pct: float = 1.0,
) -> SignalResult:
    d = df.copy()
    d["MA50"] = sma(d["Close"], 50)
    d["MA200"] = sma(d["Close"], 200)
    d["RSI14"] = rsi(d["Close"], 14)
    d["ATR14"] = atr(d, 14)
    d["HH20"] = d["High"].rolling(20).max()

    row = d.iloc[-1]
    close = float(row["Close"])
    ma50 = float(row["MA50"])
    ma200 = float(row["MA200"])
    rsi14 = float(row["RSI14"])
    atr14 = float(row["ATR14"])
    hh20 = float(row["HH20"])

    trend_ok = close > ma50 and ma50 > ma200
    momentum_ok = 45 <= rsi14 <= 65
    breakout_ok = close >= hh20
    is_buy = trend_ok and momentum_ok and breakout_ok
    technical_score = _score_technical(trend_ok, momentum_ok, breakout_ok, rsi14)
    fundamental_score = _score_fundamentals(fundamentals)
    composite_score = min(100, technical_score + fundamental_score)

    if is_buy:
        entry = round(close, 2)
        sl = stop_loss(entry, atr14)
        tp = take_profit(entry, atr14)
        shares, max_risk_amount, risk_per_share = recommend_position_size(
            account_size=account_size,
            risk_per_trade_pct=risk_per_trade_pct,
            entry=entry,
            stop=sl,
        )
        signal = "BUY"
    else:
        entry = None
        sl = None
        tp = None
        shares = None
        max_risk_amount = None
        risk_per_share = None
        signal = "NO_BUY"

    return SignalResult(
        ticker=ticker.upper(),
        signal=signal,
        last_close=round(close, 2),
        buy_price=entry,
        sell_target=tp,
        stop_loss=sl,
        trend_ok=trend_ok,
        momentum_ok=momentum_ok,
        breakout_ok=breakout_ok,
        rsi14=round(rsi14, 2),
        atr14=round(atr14, 2),
        technical_score=technical_score,
        fundamental_score=fundamental_score,
        composite_score=composite_score,
        max_risk_amount=max_risk_amount,
        risk_per_share=risk_per_share,
        suggested_shares=shares,
    )
