from __future__ import annotations

import argparse
from datetime import datetime

from quant_trading_logic.data.fetch import fetch_daily_ohlcv
from quant_trading_logic.data.fundamentals import fetch_fundamentals
from quant_trading_logic.signals.strategy import evaluate_signal
from quant_trading_logic.signals.scanner import scan_watchlist
from quant_trading_logic.backtest.analyzer import analyze_backtest
from quant_trading_logic.reports.formatters import (
    format_signal,
    format_backtest_stats,
    format_watchlist,
)
from quant_trading_logic.reports.csv_export import (
    export_signals_to_csv,
    export_watchlist_to_csv,
)
from quant_trading_logic.backtest.journal import log_signal_to_journal


def main() -> None:
    parser = argparse.ArgumentParser(description="Quant trading signal CLI")
    parser.add_argument("--ticker", help="Ticker symbol, e.g. AAPL")
    parser.add_argument("--watchlist", help="Comma-separated tickers, e.g. AAPL,MSFT,NVDA")
    parser.add_argument("--period", default="2y", help="Data period, e.g. 1y, 2y, 5y")
    parser.add_argument("--account-size", type=float, default=10000.0, help="Account size in dollars")
    parser.add_argument("--risk-pct", type=float, default=1.0, help="Max risk per trade in percent")
    parser.add_argument("--top", type=int, default=10, help="Top rows for watchlist output")
    parser.add_argument("--backtest", action="store_true", help="Run backtest analysis")
    parser.add_argument("--start-date", help="Backtest start date in YYYY-MM-DD format")
    parser.add_argument("--end-date", help="Backtest end date in YYYY-MM-DD format")
    parser.add_argument("--export", help="Export results to CSV file")
    parser.add_argument("--journal", help="Log signal to trade journal CSV file")
    args = parser.parse_args()

    def parse_date(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            parser.error(f"Invalid date '{value}'. Use YYYY-MM-DD.")
            raise exc

    start_date = parse_date(args.start_date)
    end_date = parse_date(args.end_date)

    if args.watchlist:
        tickers = [t.strip() for t in args.watchlist.split(",") if t.strip()]
        if not tickers:
            parser.error("--watchlist provided but no valid tickers were found")
        
        scan = scan_watchlist(
            tickers=tickers,
            period=args.period,
            account_size=args.account_size,
            risk_per_trade_pct=args.risk_pct,
        )
        
        print(format_watchlist(scan, top=args.top))
        
        if args.backtest:
            print("\n" + "=" * 60)
            print("Backtest Analysis (per ticker):")
            print("=" * 60)
            for signal in scan.results[:args.top]:
                try:
                    df = fetch_daily_ohlcv(signal.ticker, period=args.period)
                    stats = analyze_backtest(
                        signal.ticker,
                        df,
                        start_date=start_date,
                        end_date=end_date,
                    )
                    print("\n" + format_backtest_stats(stats))
                except Exception as e:
                    print(f"\nBacktest failed for {signal.ticker}: {e}")
        
        if args.export:
            export_watchlist_to_csv(scan, args.export)
            print(f"\n✓ Results exported to {args.export}")
        
        return

    if not args.ticker:
        parser.error("Provide either --ticker or --watchlist")

    df = fetch_daily_ohlcv(args.ticker, period=args.period)
    fundamentals = fetch_fundamentals(args.ticker)
    signal = evaluate_signal(
        args.ticker,
        df,
        fundamentals=fundamentals,
        account_size=args.account_size,
        risk_per_trade_pct=args.risk_pct,
    )
    print(format_signal(signal))

    if args.backtest:
        print("\n" + "=" * 60)
        stats = analyze_backtest(
            args.ticker,
            df,
            start_date=start_date,
            end_date=end_date,
        )
        print(format_backtest_stats(stats))
        print("=" * 60)
    
    if args.journal:
        log_signal_to_journal(signal, args.journal)
        print(f"✓ Signal logged to {args.journal}")
    
    if args.export:
        export_signals_to_csv([signal], args.export)
        print(f"✓ Signal exported to {args.export}")


if __name__ == "__main__":
    main()
