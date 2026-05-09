from __future__ import annotations


def stop_loss(entry: float, atr_value: float, atr_mult: float = 1.5) -> float:
    return round(entry - atr_mult * atr_value, 2)


def take_profit(entry: float, atr_value: float, atr_mult: float = 3.0) -> float:
    return round(entry + atr_mult * atr_value, 2)


def recommend_position_size(
    account_size: float,
    risk_per_trade_pct: float,
    entry: float,
    stop: float,
) -> tuple[int, float, float]:
    """Return (shares, max_risk_amount, risk_per_share)."""
    risk_per_share = max(0.0, entry - stop)
    max_risk_amount = max(0.0, account_size * (risk_per_trade_pct / 100.0))

    if risk_per_share <= 0 or max_risk_amount <= 0:
        return 0, round(max_risk_amount, 2), round(risk_per_share, 2)

    shares = int(max_risk_amount // risk_per_share)
    return shares, round(max_risk_amount, 2), round(risk_per_share, 2)
