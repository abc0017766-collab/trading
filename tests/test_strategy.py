from __future__ import annotations

import pandas as pd

from quant_trading_logic.signals.strategy import evaluate_signal


def test_evaluate_signal_outputs_shape() -> None:
    n = 260
    base = pd.Series([100 + i * 0.1 for i in range(n)])
    df = pd.DataFrame(
        {
            "Open": base,
            "High": base + 1,
            "Low": base - 1,
            "Close": base,
            "Volume": [100000] * n,
        }
    )

    result = evaluate_signal("TEST", df)
    assert result.ticker == "TEST"
    assert result.signal in {"BUY", "NO_BUY"}
