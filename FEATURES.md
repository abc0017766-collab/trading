# Trading Signal Generator - Features Guide

## Overview

The Quant Trading Logic project provides a complete toolkit for generating stock trading signals with data-driven analysis, risk management, and comprehensive backtesting.

## Core Features

### 1. Signal Generation

Generate buy/sell signals for individual stocks with:
- **Technical Analysis**: Trend (MA50/MA200), Momentum (RSI), Breakout (20-day high)
- **Fundamental Analysis**: P/E ratio, profit margin, revenue growth, debt-to-equity
- **Composite Scoring**: Combined technical (0-70) + fundamental (0-30) = 0-100 overall score
- **Explicit Levels**: Clear buy price, sell target, and stop loss
- **Risk Sizing**: Automatic position size calculation based on account size and risk tolerance

**Usage:**
```bash
python -m quant_trading_logic.cli --ticker AAPL --account-size 10000 --risk-pct 1
```

**Output:**
```
Ticker: AAPL
Signal: BUY
Composite score: 75/100 (Technical 48 + Fundamental 27)
Last close: 293.32
Buy price: 293.50
Sell target: 310.25
Stop loss: 285.00
Max risk amount: 100.00
Risk per share: 8.50
Suggested shares: 12
```

### 2. Watchlist Scanner

Evaluate multiple tickers simultaneously and rank by signal quality:
- **Batch Evaluation**: Process 10+ tickers in one command
- **Ranked Results**: Sorted by composite score (highest first)
- **Filtered Results**: Show top N signals with `--top` parameter
- **Failure Tolerance**: Gracefully handles API timeouts or data issues

**Usage:**
```bash
python -m quant_trading_logic.cli --watchlist AAPL,MSFT,NVDA,TSLA,GS --top 5
```

**Output:**
```
Ticker  Signal  Score  Close    Buy      Target   Stop
------------------------------------------------------
MSFT    BUY        73   415.12   416.00   438.50   408.00
NVDA    BUY        68   215.20   216.00   235.75   208.00
AAPL    NO_BUY     48   293.32        -        -        -
TSLA    NO_BUY     21   428.35        -        -        -
GS      NO_BUY     35   310.00        -        -        -
```

### 3. CSV Export

Save all signal analysis to CSV files for further analysis, reporting, or integration:

**Single Signal Export:**
```bash
python -m quant_trading_logic.cli --ticker AAPL --export signal.csv
```

**Watchlist Export:**
```bash
python -m quant_trading_logic.cli --watchlist AAPL,MSFT,NVDA --export results.csv
```

**CSV Fields Include:**
- Timestamp, Ticker, Signal, Composite/Technical/Fundamental scores
- Last close, Buy price, Sell target, Stop loss
- Technical indicators (RSI, ATR, trend checks)
- Risk metrics (suggested shares, max risk amount, risk per share)

### 4. Trade Journal

Maintain a persistent log of all signals for performance tracking and analysis:

**Log Signals to Journal:**
```bash
python -m quant_trading_logic.cli --ticker AAPL --journal trades.csv
python -m quant_trading_logic.cli --watchlist AAPL,MSFT --journal trades.csv
```

**Journal Features:**
- Persistent CSV file tracks every signal generated
- Initial status: "open" (for BUY) or "no_entry" (for NO_BUY)
- Ready for manual entry/exit tracking
- Fields for exit price, exit date, PnL, PnL %

**Journal Usage Pattern:**
1. Generate signals and log to `trades.csv`
2. Monitor trades in real market
3. Update exit price when position closes
4. Calculate realized PnL for performance review

### 5. Backtest Analysis

Evaluate signal quality through historical backtesting:

**Single Ticker Backtest:**
```bash
python -m quant_trading_logic.cli --ticker AAPL --backtest
```

**Watchlist Backtest:**
```bash
python -m quant_trading_logic.cli --watchlist AAPL,MSFT,NVDA --backtest --top 3
```

**Backtest Metrics:**
- Total bars analyzed (historical data points)
- Buy signals generated (count of buy conditions met)
- Profitable signals (signals where next bar closes above target)
- Loss signals (signals where next bar closes below stop)
- Win rate % (profitable / total)

**Output:**
```
Backtest Analysis for AAPL
Total bars: 501
Buy signals generated: 42
Profitable signals: 28
Loss signals: 14
Win rate: 66.67%
Latest signal: BUY (close: $293.32)
```

## CLI Arguments Reference

### Core Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--ticker` | string | - | Single stock ticker (e.g., AAPL) |
| `--watchlist` | string | - | Comma-separated tickers (e.g., AAPL,MSFT,NVDA) |
| `--period` | string | 2y | Data lookback period (1y, 2y, 5y, max) |
| `--account-size` | float | 10000 | Account size in dollars for position sizing |
| `--risk-pct` | float | 1.0 | Max risk per trade as % of account |

### Feature Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--top` | integer | 10 | Number of top results for watchlist |
| `--backtest` | boolean | false | Run backtest analysis |
| `--export` | string | - | Export results to CSV file path |
| `--journal` | string | - | Log signal to trade journal CSV file |

## Usage Examples

### Example 1: Single Stock Analysis
```bash
python -m quant_trading_logic.cli --ticker AAPL --account-size 50000 --risk-pct 2
```
Analyze AAPL with $50k account and 2% risk per trade.

### Example 2: Watchlist with Top 5 Results
```bash
python -m quant_trading_logic.cli \
  --watchlist AAPL,MSFT,NVDA,TSLA,GS,BA,JPM,IBM \
  --top 5 --account-size 100000
```
Scan 8 tickers, show top 5 by score, $100k account.

### Example 3: Export Results for Reporting
```bash
python -m quant_trading_logic.cli \
  --watchlist AAPL,MSFT,NVDA \
  --export daily_scan_2026-05-09.csv
```
Scan tickers and export results to CSV for reports or further analysis.

### Example 4: Track Signals Over Time
```bash
python -m quant_trading_logic.cli \
  --ticker AAPL \
  --backtest \
  --journal ~/trading_journal.csv
```
Analyze AAPL with backtesting and log to persistent journal for performance tracking.

### Example 5: Complete Workflow - Full Analysis
```bash
python -m quant_trading_logic.cli \
  --watchlist AAPL,MSFT,NVDA,TSLA,GS,BA,JPM,IBM,INTC,AMD \
  --top 5 \
  --backtest \
  --export scan_results.csv \
  --journal trades.csv \
  --account-size 250000 \
  --risk-pct 1.5
```
Comprehensive analysis: scan 10 tickers, backtest top 5, export results, log signals, $250k account, 1.5% risk.

## Signal Interpretation

### BUY Signal
A BUY signal indicates three conditions are met:
1. **Trend OK**: Price > MA50 > MA200 (uptrend)
2. **Momentum OK**: RSI between 45-65 (neutral to slightly bullish)
3. **Breakout OK**: Price >= 20-day high (breakout confirmed)

When BUY is generated:
- **Buy price**: Entry level (current close)
- **Sell target**: ATR-based profit target (~2% above entry)
- **Stop loss**: ATR-based stop (~2-3% below entry)
- **Suggested shares**: Calculated for account size and risk tolerance

### NO_BUY Signal
A NO_BUY signal means one or more conditions failed. Review the individual checks:
- `Trend OK`: Check if in uptrend
- `Momentum OK`: Check if RSI is not overbought
- `Breakout OK`: Check if at key resistance level

## Technical Indicators

- **MA50/MA200**: 50 and 200-day simple moving averages for trend
- **RSI14**: 14-period relative strength index for momentum
- **ATR14**: 14-period average true range for volatility
- **HH20**: 20-day highest high for breakout detection

## Position Sizing Model

Position size is calculated to limit risk:

```
Max Risk Amount = Account Size × (Risk % / 100)
Risk Per Share = Entry Price - Stop Loss
Suggested Shares = Max Risk Amount / Risk Per Share
```

Example:
- Account: $10,000, Risk: 1% → Max Risk = $100
- Entry: $100, Stop: $95 → Risk Per Share = $5
- Suggested Shares: $100 / $5 = 20 shares

## Files Generated

### CSV Outputs

**signal.csv** - Single signal export
```
timestamp,ticker,signal,composite_score,...
2026-05-09T10:30:45,AAPL,BUY,75,...
```

**watchlist.csv** - Watchlist results export
```
timestamp,ticker,signal,composite_score,...
2026-05-09T10:30:45,MSFT,BUY,73,...
2026-05-09T10:30:45,NVDA,BUY,68,...
```

**trades.csv** - Trade journal
```
timestamp,ticker,signal,...,status,exit_price,pnl
2026-05-09T10:30:45,AAPL,BUY,...,open,,
2026-05-08T09:15:30,MSFT,BUY,...,closed,420.50,145.00
```

## Next Steps

1. **Monitor Trades**: Watch positions opened from BUY signals
2. **Log Exits**: Record exit prices in trade journal
3. **Track Performance**: Analyze win rate and PnL over time
4. **Refine Rules**: Adjust RSI bands, ATR multiples, or MA periods
5. **Scale Up**: Increase position sizes as confidence in system grows

## Tips & Best Practices

- **Backtest Before Trading**: Always run `--backtest` to review historical signal quality
- **Track Everything**: Use `--journal` to maintain permanent trading record
- **Export Results**: Use `--export` for reporting and external analysis
- **Risk Management**: Adjust `--risk-pct` based on account size and experience
- **Regular Reviews**: Export weekly/monthly results to track performance trends
- **Validate Signals**: Cross-reference with your own technical analysis before trading
