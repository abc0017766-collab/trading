from __future__ import annotations

import pandas as pd

from quant_trading_logic.backtest import analyzer
from quant_trading_logic.signals.strategy import SignalResult


def test_analyze_backtest_simulates_trade_to_target(monkeypatch) -> None:
    df = pd.DataFrame(
        {
            "Open": [100.0, 100.0, 100.0, 100.0, 100.0],
            "High": [101.0, 101.0, 112.0, 101.0, 101.0],
            "Low": [99.0, 99.0, 99.0, 99.0, 99.0],
            "Close": [100.0, 100.0, 108.0, 100.0, 100.0],
            "Volume": [100000] * 5,
        }
    )

    def fake_evaluate_signal(
        ticker: str,
        current_df: pd.DataFrame,
        fundamentals: dict[str, float | None] | None = None,
        account_size: float = 10000.0,
        risk_per_trade_pct: float = 1.0,
    ) -> SignalResult:
        if len(current_df) == 2:
            return SignalResult(
                ticker=ticker,
                signal="BUY",
                last_close=100.0,
                buy_price=100.0,
                sell_target=110.0,
                stop_loss=95.0,
                trend_ok=True,
                momentum_ok=True,
                breakout_ok=True,
                rsi14=55.0,
                atr14=3.0,
                technical_score=70,
                fundamental_score=0,
                composite_score=70,
                max_risk_amount=100.0,
                risk_per_share=5.0,
                suggested_shares=10,
            )

        return SignalResult(
            ticker=ticker,
            signal="NO_BUY",
            last_close=100.0,
            buy_price=None,
            sell_target=None,
            stop_loss=None,
            trend_ok=False,
            momentum_ok=False,
            breakout_ok=False,
            rsi14=45.0,
            atr14=3.0,
            technical_score=0,
            fundamental_score=0,
            composite_score=0,
            max_risk_amount=None,
            risk_per_share=None,
            suggested_shares=None,
        )

    monkeypatch.setattr(analyzer, "evaluate_signal", fake_evaluate_signal)

    stats = analyzer.analyze_backtest("TEST", df, min_history=1)

    assert stats.buy_signals == 1
    assert stats.closed_trades == 1
    assert stats.win_signals == 1
    assert stats.loss_signals == 0
    assert stats.total_pnl == 100.0
    assert stats.ending_equity == 10100.0
    assert stats.total_return_percent == 1.0
    assert stats.win_rate_percent == 100.0


def test_analyze_backtest_filters_date_range(monkeypatch) -> None:
    idx = pd.date_range("2024-01-01", periods=5, freq="D")
    df = pd.DataFrame(
        {
            "Open": [100.0, 100.0, 100.0, 100.0, 100.0],
            "High": [101.0, 101.0, 112.0, 101.0, 101.0],
            "Low": [99.0, 99.0, 99.0, 99.0, 99.0],
            "Close": [100.0, 100.0, 108.0, 100.0, 100.0],
            "Volume": [100000] * 5,
        },
        index=idx,
    )

    call_sizes: list[int] = []

    def fake_evaluate_signal(
        ticker: str,
        current_df: pd.DataFrame,
        fundamentals: dict[str, float | None] | None = None,
        account_size: float = 10000.0,
        risk_per_trade_pct: float = 1.0,
    ) -> SignalResult:
        call_sizes.append(len(current_df))
        return SignalResult(
            ticker=ticker,
            signal="NO_BUY",
            last_close=100.0,
            buy_price=None,
            sell_target=None,
            stop_loss=None,
            trend_ok=False,
            momentum_ok=False,
            breakout_ok=False,
            rsi14=45.0,
            atr14=3.0,
            technical_score=0,
            fundamental_score=0,
            composite_score=0,
            max_risk_amount=None,
            risk_per_share=None,
            suggested_shares=None,
        )

    monkeypatch.setattr(analyzer, "evaluate_signal", fake_evaluate_signal)

    stats = analyzer.analyze_backtest(
        "TEST",
        df,
        start_date="2024-01-03",
        end_date="2024-01-05",
        min_history=1,
    )

    assert stats.total_bars == 3
    assert call_sizes and min(call_sizes) == 2