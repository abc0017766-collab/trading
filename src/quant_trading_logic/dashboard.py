"""Streamlit dashboard for trading signal analysis and management."""

import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path

try:
    from quant_trading_logic.data.fetch import fetch_daily_ohlcv
    from quant_trading_logic.data.fundamentals import fetch_fundamentals
    from quant_trading_logic.signals.strategy import evaluate_signal
    from quant_trading_logic.signals.scanner import scan_watchlist
    from quant_trading_logic.backtest.analyzer import analyze_backtest
    from quant_trading_logic.reports.csv_export import (
        export_signals_to_csv,
        export_watchlist_to_csv,
    )
    from quant_trading_logic.backtest.journal import (
        log_signal_to_journal,
        get_open_trades,
    )
except ModuleNotFoundError:
    # Streamlit Cloud may run this file directly; ensure src/ is on sys.path.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from quant_trading_logic.data.fetch import fetch_daily_ohlcv
    from quant_trading_logic.data.fundamentals import fetch_fundamentals
    from quant_trading_logic.signals.strategy import evaluate_signal
    from quant_trading_logic.signals.scanner import scan_watchlist
    from quant_trading_logic.backtest.analyzer import analyze_backtest
    from quant_trading_logic.reports.csv_export import (
        export_signals_to_csv,
        export_watchlist_to_csv,
    )
    from quant_trading_logic.backtest.journal import (
        log_signal_to_journal,
        get_open_trades,
    )


# Page config
st.set_page_config(
    page_title="Trading Signal Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
    }
    .buy-signal {
        color: #0ABF53;
        font-weight: bold;
    }
    .no-buy-signal {
        color: #FF2B2B;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_price(value):
    """Format value as price."""
    if value is None:
        return "-"
    return f"${value:.2f}"


def plot_price_with_indicators(df, signal_result):
    """Create interactive price chart with indicators."""
    fig = go.Figure()

    # Price line
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            name="Close Price",
            line=dict(color="#1f77b4", width=2),
        )
    )

    # MA50
    if "MA50" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["MA50"],
                name="MA50",
                line=dict(color="#ff7f0e", dash="dash"),
            )
        )

    # MA200
    if "MA200" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["MA200"],
                name="MA200",
                line=dict(color="#d62728", dash="dash"),
            )
        )

    # Buy/Sell targets
    if signal_result.buy_price:
        fig.add_hline(
            y=signal_result.buy_price,
            line_dash="dashdot",
            line_color="green",
            annotation_text="Buy",
        )
    if signal_result.sell_target:
        fig.add_hline(
            y=signal_result.sell_target,
            line_dash="dashdot",
            line_color="blue",
            annotation_text="Target",
        )
    if signal_result.stop_loss:
        fig.add_hline(
            y=signal_result.stop_loss,
            line_dash="dashdot",
            line_color="red",
            annotation_text="Stop",
        )

    fig.update_layout(
        title=f"{signal_result.ticker} - Price & Indicators",
        yaxis_title="Price (USD)",
        xaxis_title="Date",
        hovermode="x unified",
        height=500,
    )

    return fig


def plot_rsi(df):
    """Create RSI indicator chart."""
    if "RSI14" not in df.columns:
        return None

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["RSI14"],
            name="RSI14",
            line=dict(color="#636EFA"),
        )
    )

    # Overbought/Oversold lines
    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
    fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
    fig.add_hline(y=50, line_dash="dot", line_color="gray")

    fig.update_layout(
        title="RSI14 - Momentum",
        yaxis_title="RSI",
        xaxis_title="Date",
        hovermode="x unified",
        height=350,
    )

    return fig


def main():
    st.title("📈 Trading Signal Dashboard")
    st.write(
        "Real-time analysis of trading signals with technical indicators and position sizing."
    )

    # Sidebar navigation
    page = st.sidebar.radio(
        "📊 Navigation",
        [
            "🎯 Single Signal",
            "📋 Watchlist Scan",
            "📊 Trade Journal",
            "📉 Backtest Analysis",
            "⚙️ Settings",
        ],
    )

    # Settings (in sidebar)
    with st.sidebar:
        st.divider()
        st.subheader("⚙️ Default Settings")
        account_size = st.number_input(
            "Account Size ($)",
            min_value=1000.0,
            value=10000.0,
            step=1000.0,
        )
        risk_pct = st.number_input(
            "Risk Per Trade (%)",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.1,
        )
        period = st.selectbox(
            "Data Period",
            ["1y", "2y", "5y"],
            index=1,
        )

    # Page routing
    if page == "🎯 Single Signal":
        page_single_signal(account_size, risk_pct, period)
    elif page == "📋 Watchlist Scan":
        page_watchlist_scan(account_size, risk_pct, period)
    elif page == "📊 Trade Journal":
        page_trade_journal()
    elif page == "📉 Backtest Analysis":
        page_backtest_analysis(period)
    elif page == "⚙️ Settings":
        page_settings(account_size, risk_pct, period)


def page_single_signal(account_size, risk_pct, period):
    """Single signal analysis page."""
    st.header("🎯 Single Stock Analysis")

    col1, col2 = st.columns(2)

    with col1:
        ticker = st.text_input(
            "Enter Stock Ticker",
            value="AAPL",
            placeholder="AAPL",
        ).upper()

    with col2:
        if st.button("🔍 Analyze", use_container_width=True):
            st.session_state.analyze = True

    if ticker and "analyze" in st.session_state and st.session_state.analyze:
        with st.spinner(f"Analyzing {ticker}..."):
            try:
                # Fetch data
                df = fetch_daily_ohlcv(ticker, period=period)
                fundamentals = fetch_fundamentals(ticker)

                # Calculate indicators
                from quant_trading_logic.signals.indicators import sma, rsi, atr

                df["MA50"] = sma(df["Close"], 50)
                df["MA200"] = sma(df["Close"], 200)
                df["RSI14"] = rsi(df["Close"], 14)
                df["ATR14"] = atr(df, 14)

                # Evaluate signal
                signal = evaluate_signal(
                    ticker,
                    df,
                    fundamentals=fundamentals,
                    account_size=account_size,
                    risk_per_trade_pct=risk_pct,
                )

                # Display signal result
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    signal_color = "🟢" if signal.signal == "BUY" else "🔴"
                    st.metric("Signal", f"{signal_color} {signal.signal}")

                with col2:
                    st.metric("Composite Score", f"{signal.composite_score}/100")

                with col3:
                    st.metric("Last Close", format_price(signal.last_close))

                with col4:
                    st.metric("RSI14", f"{signal.rsi14:.1f}")

                # Detailed metrics
                st.divider()
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.subheader("📊 Score Breakdown")
                    st.write(f"**Technical Score**: {signal.technical_score}/70")
                    st.write(f"**Fundamental Score**: {signal.fundamental_score}/30")

                with col2:
                    st.subheader("📍 Price Levels")
                    st.write(f"**Buy Price**: {format_price(signal.buy_price)}")
                    st.write(f"**Sell Target**: {format_price(signal.sell_target)}")
                    st.write(f"**Stop Loss**: {format_price(signal.stop_loss)}")

                with col3:
                    st.subheader("💰 Position Sizing")
                    st.write(
                        f"**Max Risk Amount**: {format_price(signal.max_risk_amount)}"
                    )
                    st.write(f"**Risk Per Share**: {format_price(signal.risk_per_share)}")
                    st.write(f"**Suggested Shares**: {signal.suggested_shares or '-'}")

                # Signal conditions
                st.divider()
                st.subheader("✓ Signal Conditions")
                col1, col2, col3 = st.columns(3)

                with col1:
                    status = "✓" if signal.trend_ok else "✗"
                    st.write(f"{status} Trend OK (Price > MA50 > MA200)")

                with col2:
                    status = "✓" if signal.momentum_ok else "✗"
                    st.write(f"{status} Momentum OK (RSI 45-65)")

                with col3:
                    status = "✓" if signal.breakout_ok else "✗"
                    st.write(f"{status} Breakout OK (Close >= 20-day high)")

                # Charts
                st.divider()
                st.subheader("📈 Charts")

                tab1, tab2 = st.tabs(["Price & Indicators", "RSI"])

                with tab1:
                    fig_price = plot_price_with_indicators(df, signal)
                    st.plotly_chart(fig_price, use_container_width=True)

                with tab2:
                    fig_rsi = plot_rsi(df)
                    if fig_rsi:
                        st.plotly_chart(fig_rsi, use_container_width=True)

                # Export & Journal options
                st.divider()
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("💾 Export to CSV", use_container_width=True):
                        export_signals_to_csv(
                            [signal],
                            f"signal_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        )
                        st.success("✓ Exported to CSV")

                with col2:
                    if st.button("📔 Log to Journal", use_container_width=True):
                        log_signal_to_journal(signal, "trading_journal.csv")
                        st.success("✓ Logged to journal")

                with col3:
                    if st.button("📉 Run Backtest", use_container_width=True):
                        stats = analyze_backtest(ticker, df)
                        st.session_state.backtest_stats = stats

                # Backtest results if available
                if "backtest_stats" in st.session_state:
                    st.divider()
                    st.subheader("📉 Backtest Results")
                    stats = st.session_state.backtest_stats

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Bars", stats.total_bars)
                    with col2:
                        st.metric("Trades Taken", stats.closed_trades)
                    with col3:
                        st.metric("Win Rate", f"{stats.win_rate_percent:.1f}%")
                    with col4:
                        st.metric("Total Return", f"{stats.total_return_percent:.1f}%")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total PnL", format_price(stats.total_pnl))
                    with col2:
                        st.metric("Ending Equity", format_price(stats.ending_equity))
                    with col3:
                        st.metric("Avg Trade", f"{stats.average_return_percent:.1f}%")
                    with col4:
                        st.metric("Max Drawdown", f"{stats.max_drawdown_percent:.1f}%")

            except Exception as e:
                st.error(f"❌ Error analyzing {ticker}: {str(e)}")


def page_watchlist_scan(account_size, risk_pct, period):
    """Watchlist scan page."""
    st.header("📋 Watchlist Scan")

    col1, col2, col3 = st.columns(3)

    with col1:
        watchlist_input = st.text_area(
            "Enter Tickers (comma-separated)",
            value="AAPL,MSFT,NVDA,TSLA",
            height=100,
        )

    with col2:
        top_n = st.number_input(
            "Show Top N Results",
            min_value=1,
            value=5,
        )

    with col3:
        st.write("")  # Spacer
        if st.button("🚀 Scan Watchlist", use_container_width=True):
            st.session_state.scan = True

    if watchlist_input and "scan" in st.session_state and st.session_state.scan:
        tickers = [t.strip() for t in watchlist_input.split(",") if t.strip()]

        if not tickers:
            st.error("Please enter valid tickers")
            return

        with st.spinner(f"Scanning {len(tickers)} tickers..."):
            try:
                scan = scan_watchlist(
                    tickers=tickers,
                    period=period,
                    account_size=account_size,
                    risk_per_trade_pct=risk_pct,
                )

                # Results table
                st.subheader("📊 Scan Results")
                results_data = []
                for result in scan.results[:top_n]:
                    results_data.append({
                        "Ticker": result.ticker,
                        "Signal": "🟢 BUY" if result.signal == "BUY" else "🔴 NO_BUY",
                        "Score": result.composite_score,
                        "Close": f"${result.last_close:.2f}",
                        "Buy": format_price(result.buy_price),
                        "Target": format_price(result.sell_target),
                        "Stop": format_price(result.stop_loss),
                        "Shares": result.suggested_shares or "-",
                    })

                results_df = pd.DataFrame(results_data)
                st.dataframe(results_df, use_container_width=True, hide_index=True)

                if scan.failed_tickers:
                    st.warning(f"Failed tickers: {', '.join(scan.failed_tickers)}")

                # Export & Backtest
                st.divider()
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("💾 Export Results", use_container_width=True):
                        export_watchlist_to_csv(
                            scan,
                            f"watchlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        )
                        st.success("✓ Exported to CSV")

                with col2:
                    if st.button("📔 Log All to Journal", use_container_width=True):
                        for result in scan.results:
                            log_signal_to_journal(result, "trading_journal.csv")
                        st.success(f"✓ Logged {len(scan.results)} signals")

                with col3:
                    if st.button("📉 Backtest Top Results", use_container_width=True):
                        st.session_state.run_backtest = True

                # Run backtest if requested
                if "run_backtest" in st.session_state and st.session_state.run_backtest:
                    st.divider()
                    st.subheader("📉 Backtest Analysis")

                    backtest_results = []
                    progress_bar = st.progress(0)

                    for idx, result in enumerate(scan.results[:top_n]):
                        try:
                            df = fetch_daily_ohlcv(result.ticker, period=period)
                            stats = analyze_backtest(result.ticker, df)
                            backtest_results.append({
                                "Ticker": result.ticker,
                                "Signal": result.signal,
                                "Score": result.composite_score,
                                "Total Bars": stats.total_bars,
                                "Trades": stats.closed_trades,
                                "Win Rate %": f"{stats.win_rate_percent:.1f}%",
                                "Return %": f"{stats.total_return_percent:.1f}%",
                                "PnL": f"${stats.total_pnl:.2f}",
                                "Wins": stats.win_signals,
                                "Losses": stats.loss_signals,
                            })
                        except Exception as e:
                            st.warning(f"Backtest failed for {result.ticker}: {str(e)}")

                        progress_bar.progress((idx + 1) / top_n)

                    if backtest_results:
                        backtest_df = pd.DataFrame(backtest_results)
                        st.dataframe(backtest_df, use_container_width=True, hide_index=True)

            except Exception as e:
                st.error(f"❌ Error scanning watchlist: {str(e)}")


def page_trade_journal():
    """Trade journal page."""
    st.header("📊 Trade Journal")

    journal_file = "trading_journal.csv"

    if not Path(journal_file).exists():
        st.info("📝 No trades logged yet. Run analysis and click 'Log to Journal' to start.")
        return

    # Load journal
    df_journal = pd.read_csv(journal_file)

    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            df_journal["status"].unique(),
            default=df_journal["status"].unique(),
        )

    with col2:
        ticker_filter = st.multiselect(
            "Filter by Ticker",
            df_journal["ticker"].unique(),
            default=df_journal["ticker"].unique(),
        )

    # Filter data
    df_filtered = df_journal[
        (df_journal["status"].isin(status_filter))
        & (df_journal["ticker"].isin(ticker_filter))
    ]

    # Display statistics
    st.subheader("📈 Journal Statistics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Trades", len(df_filtered))

    with col2:
        open_count = len(df_filtered[df_filtered["status"] == "open"])
        st.metric("Open Trades", open_count)

    with col3:
        closed_count = len(df_filtered[df_filtered["status"] == "closed"])
        st.metric("Closed Trades", closed_count)

    with col4:
        if closed_count > 0:
            closed_df = df_filtered[df_filtered["status"] == "closed"]
            if "pnl" in closed_df.columns:
                total_pnl = closed_df["pnl"].sum()
                st.metric("Total PnL", format_price(total_pnl))

    # Display journal table
    st.divider()
    st.subheader("📋 Trade Details")

    # Select columns to display
    display_cols = [
        "timestamp",
        "ticker",
        "signal",
        "composite_score",
        "buy_price",
        "suggested_shares",
        "status",
        "exit_price",
        "pnl",
    ]
    display_cols = [c for c in display_cols if c in df_filtered.columns]

    st.dataframe(df_filtered[display_cols], use_container_width=True, hide_index=True)

    # Export journal
    if st.button("💾 Export Journal", use_container_width=True):
        st.download_button(
            label="Download Journal CSV",
            data=df_filtered.to_csv(index=False),
            file_name=f"journal_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )


def page_backtest_analysis(period):
    """Backtest analysis page."""
    st.header("📉 Backtest Analysis")

    col1, col2 = st.columns(2)

    with col1:
        ticker = st.text_input("Enter Ticker for Backtest", value="AAPL").upper()

    with col2:
        if st.button("▶️ Run Backtest", use_container_width=True):
            st.session_state.run_backtest = True

    if ticker and "run_backtest" in st.session_state and st.session_state.run_backtest:
        with st.spinner(f"Running backtest for {ticker}..."):
            try:
                df = fetch_daily_ohlcv(ticker, period=period)
                stats = analyze_backtest(ticker, df)

                # Display results
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Bars", stats.total_bars)

                with col2:
                    st.metric("Trades Taken", stats.closed_trades)

                with col3:
                    st.metric("Win Rate", f"{stats.win_rate_percent:.1f}%")

                with col4:
                    st.metric("Total Return", f"{stats.total_return_percent:.1f}%")

                # Detailed breakdown
                st.divider()
                st.subheader("📊 Detailed Results")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Profitable Signals**: {stats.win_signals}")

                with col2:
                    st.write(f"**Loss Signals**: {stats.loss_signals}")

                with col3:
                    st.write(f"**Latest Close**: ${stats.latest_close:.2f}")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Total PnL**: {format_price(stats.total_pnl)}")

                with col2:
                    st.write(f"**Ending Equity**: {format_price(stats.ending_equity)}")

                with col3:
                    st.write(f"**Average Holding Days**: {stats.average_holding_days}")

                st.write(f"**Max Drawdown**: {stats.max_drawdown_percent:.2f}%")

                # Interpretation
                st.divider()
                st.subheader("💡 Interpretation")

                if stats.win_rate_percent >= 60 and stats.total_return_percent > 0:
                    st.success(
                        f"✓ Strong backtest: {stats.win_rate_percent:.1f}% win rate and {stats.total_return_percent:.1f}% return"
                    )
                elif stats.win_rate_percent >= 50 and stats.total_return_percent >= 0:
                    st.info(
                        f"Moderate backtest: {stats.win_rate_percent:.1f}% win rate and {stats.total_return_percent:.1f}% return"
                    )
                else:
                    st.warning(
                        f"Weak backtest: {stats.win_rate_percent:.1f}% win rate and {stats.total_return_percent:.1f}% return"
                    )

            except Exception as e:
                st.error(f"❌ Error running backtest: {str(e)}")


def page_settings(account_size, risk_pct, period):
    """Settings page."""
    st.header("⚙️ Settings & Documentation")

    st.markdown("""
    ### 📊 Current Settings
    
    These settings are used for all analysis:
    - **Account Size**: ${}
    - **Risk Per Trade**: {}%
    - **Data Period**: {}
    
    ### 📖 How to Use
    
    1. **Single Signal**: Analyze one stock with technical/fundamental scoring
    2. **Watchlist Scan**: Evaluate multiple stocks and rank by signal quality
    3. **Trade Journal**: Track all logged signals and their performance
    4. **Backtest Analysis**: Test signal quality historically
    
    ### 📊 Understanding the Signal
    
    - **BUY**: All three conditions met (Trend, Momentum, Breakout)
    - **Score**: Technical (0-70) + Fundamental (0-30) = 0-100
    - **Buy Price**: Current close price (entry level)
    - **Target**: ATR-based profit target (~2% above entry)
    - **Stop**: ATR-based stop loss (~2-3% below entry)
    
    ### 💡 Position Sizing
    
    Shares are calculated as:
    ```
    Max Risk = Account Size × (Risk % / 100)
    Risk Per Share = Buy Price - Stop Loss
    Suggested Shares = Max Risk / Risk Per Share
    ```
    
    ### 🔍 Technical Indicators
    
    - **MA50/MA200**: Trend (Price > MA50 > MA200 = uptrend)
    - **RSI14**: Momentum (45-65 = neutral/bullish)
    - **ATR14**: Volatility (used for stop/target)
    - **HH20**: Breakout (Price >= 20-day high)
    """.format(account_size, risk_pct, period))

    st.divider()
    st.subheader("📚 Resources")

    st.markdown("""
    - **Command Line Usage**: `python -m quant_trading_logic.cli --help`
    - **Documentation**: Check README.md and FEATURES.md
    - **GitHub**: Project repository for source code
    """)


if __name__ == "__main__":
    main()
