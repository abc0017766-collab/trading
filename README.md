# Quant Trading Logic

A Python project to generate stock trading signals with explicit buy/sell levels.

## What it does

- Downloads daily OHLCV data for a selected ticker
- Computes trend and momentum indicators (MA50, MA200, RSI14, ATR14)
- Pulls basic fundamentals (P/E, margin, revenue growth, debt-to-equity)
- Produces a signal with:
  - Buy/No Buy
  - Buy price
  - Sell target
  - Stop loss
  - Composite score (technical + fundamental)
  - Suggested position size by account risk
- Includes a basic backtest summary

## Quick start

1. Create and activate virtual environment
2. Install dependencies
3. Run signal command

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python -m quant_trading_logic.cli --ticker AAPL --account-size 10000 --risk-pct 1
```

## Backtest command

```bash
python -m quant_trading_logic.cli --ticker AAPL --backtest
```

## Watchlist scanner command

```bash
python -m quant_trading_logic.cli --watchlist AAPL,MSFT,NVDA,TSLA --top 5 --account-size 10000 --risk-pct 1
```

## Advanced features

### CSV Export

Export single signal or watchlist results to CSV file:

```bash
# Export single ticker signal
python -m quant_trading_logic.cli --ticker AAPL --export signal.csv

# Export watchlist results
python -m quant_trading_logic.cli --watchlist AAPL,MSFT,NVDA --export watchlist.csv --top 5
```

### Trade Journal

Log all generated signals to a persistent trade journal for tracking:

```bash
python -m quant_trading_logic.cli --ticker AAPL --journal trades.csv
python -m quant_trading_logic.cli --watchlist AAPL,MSFT,NVDA --journal trades.csv
```

Journal tracks:
- Signal timestamp
- Ticker, signal type, composite score
- Entry, target, and stop levels
- Suggested position size
- Trade status (open/closed)
- Exit price and PnL (when closed)

### Backtest Analysis

Run comprehensive backtest analysis to evaluate signal quality:

```bash
# Single ticker backtest with statistics
python -m quant_trading_logic.cli --ticker AAPL --backtest

# Watchlist backtest for all tickers
python -m quant_trading_logic.cli --watchlist AAPL,MSFT,NVDA --backtest --top 3
```

Backtest metrics include:
- Total bars analyzed
- Number of buy signals generated
- Win rate percentage
- Profitable vs loss signals
- Latest signal status

### Combined Operations

You can combine features for comprehensive analysis:

```bash
# Scan watchlist, backtest top 5, export results, and journal signals
python -m quant_trading_logic.cli --watchlist AAPL,MSFT,NVDA,TSLA,GS \
  --top 5 --backtest --export results.csv --journal trades.csv \
  --account-size 50000 --risk-pct 2
```

## Project structure

- `src/quant_trading_logic/data`: market data fetching
- `src/quant_trading_logic/signals`: indicators and strategy logic
- `src/quant_trading_logic/risk`: stop/target calculation
- `src/quant_trading_logic/backtest`: backtest engine and analysis
- `src/quant_trading_logic/reports`: result formatting and CSV export
