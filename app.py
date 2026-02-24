import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import DATA_SOURCE_OPTIONS, CURRENCY_PAIRS, STRATEGY_OPTIONS
from data_loader import load_data
from indicators import add_indicators
from strategies import generate_signal
from metrics import run_backtest_with_position_sizing, calculate_metrics

st.set_page_config(layout="wide")
st.title("📊 Forex Trading Strategy Backtester")
st.caption("Backtest RSI, MACD, and Bollinger Band strategies on major forex pairs")

# ==============================
# Sidebar
# ==============================
st.sidebar.header("Configuration")

# Data source selection
data_source = st.sidebar.selectbox("Data Source", DATA_SOURCE_OPTIONS)

# Currency pair selection
selected_pair = st.sidebar.selectbox("Currency Pair", CURRENCY_PAIRS)

# Date range (only for Yahoo Finance)
if data_source == "Yahoo Finance (Live)":
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime(2020, 1, 1))
    with col2:
        end_date = st.date_input("End Date", datetime(2024, 1, 1))
else:
    start_date = None
    end_date = None
    st.sidebar.info("Using local CSV files - date range from file")

# Strategy selection
strategy = st.sidebar.selectbox("Trading Strategy", STRATEGY_OPTIONS)

# Train/Test split
split_ratio = st.sidebar.slider("Train/Test Split (% for training)", 50, 90, 70)

# Strategy-specific parameters
st.sidebar.header("Strategy Parameters")

if strategy == "RSI Strategy":
    rsi_period = st.sidebar.slider("RSI Period", 5, 30, 14)
    oversold = st.sidebar.slider("Oversold Threshold", 10, 40, 30)
    overbought = st.sidebar.slider("Overbought Threshold", 60, 90, 70)
    
    params = {
        'rsi_period': rsi_period,
        'rsi_oversold': oversold,
        'rsi_overbought': overbought
    }

elif strategy == "MACD Strategy":
    macd_fast = st.sidebar.slider("MACD Fast", 5, 20, 12)
    macd_slow = st.sidebar.slider("MACD Slow", 20, 40, 26)
    macd_signal = st.sidebar.slider("MACD Signal", 5, 20, 9)
    
    params = {
        'macd_fast': macd_fast,
        'macd_slow': macd_slow,
        'macd_signal': macd_signal
    }

else:  # Bollinger Strategy
    boll_period = st.sidebar.slider("Bollinger Period", 10, 50, 20)
    boll_std = st.sidebar.slider("Standard Deviations", 1.0, 3.0, 2.0, 0.5)
    
    params = {
        'boll_period': boll_period,
        'boll_std': boll_std
    }

# Position Sizing
st.sidebar.header("💰 Position Sizing")

initial_capital = st.sidebar.number_input(
    "Initial Capital (£)", 
    min_value=1000, 
    max_value=1000000, 
    value=50000, 
    step=1000,
    help="Starting account balance in GBP"
)

lot_option = st.sidebar.selectbox(
    "Lot Size",
    options=["Standard (100,000 units)", "Mini (10,000 units)", "Micro (1,000 units)", "Custom"],
    index=0,
    help="Standard lot = 100,000 units of base currency"
)

if lot_option == "Standard (100,000 units)":
    lot_size = 100000
    st.sidebar.info("💰 1 pip = $10.00")
elif lot_option == "Mini (10,000 units)":
    lot_size = 10000
    st.sidebar.info("💰 1 pip = $1.00")
elif lot_option == "Micro (1,000 units)":
    lot_size = 1000
    st.sidebar.info("💰 1 pip = $0.10")
else:
    lot_size = st.sidebar.number_input("Custom Units", 100, 1000000, 10000, 100)
    st.sidebar.info(f"💰 1 pip ≈ ${lot_size * 0.0001:.2f}")

# Risk warning
margin_required = lot_size * 0.01  # Rough 1% margin
if margin_required > initial_capital * 0.5:
    st.sidebar.error("⚠️ HIGH LEVERAGE: Margin required exceeds 50% of capital")
elif margin_required > initial_capital * 0.2:
    st.sidebar.warning("⚠️ Moderate leverage: Margin required is 20-50% of capital")
else:
    st.sidebar.success("✅ Conservative leverage: Margin required < 20% of capital")

run_button = st.sidebar.button("🚀 Run Backtest", type="primary")

# ==============================
# Main App
# ==============================
if run_button:
    with st.spinner("Loading data and running backtest..."):
        
        # Load data
        df = load_data(data_source, selected_pair, start_date, end_date)
        
        if df is None or df.empty:
            st.error("No data loaded. Please check your settings.")
            st.stop()
        
        # Add indicators based on strategy
        if strategy == "RSI Strategy":
            df = add_indicators(df, strategy,
                              rsi_period=params.get('rsi_period', 14))
        
        elif strategy == "MACD Strategy":
            df = add_indicators(df, strategy,
                              macd_fast=params.get('macd_fast', 12),
                              macd_slow=params.get('macd_slow', 26),
                              macd_signal=params.get('macd_signal', 9))
        
        else:  # Bollinger Strategy
            df = add_indicators(df, strategy,
                              boll_period=params.get('boll_period', 20),
                              boll_std=params.get('boll_std', 2))
        
        # Generate signals
        if strategy == "RSI Strategy":
            df['Signal'] = generate_signal(df, strategy,
                                         rsi_oversold=params.get('rsi_oversold', 30),
                                         rsi_overbought=params.get('rsi_overbought', 70))
        else:
            df['Signal'] = generate_signal(df, strategy)
        
        # Run backtest with position sizing
        df = run_backtest_with_position_sizing(df, strategy, initial_capital, lot_size)
        df = df.dropna()
        
        # Split into train/test
        split_idx = int(len(df) * (split_ratio / 100))
        train = df.iloc[:split_idx]
        test = df.iloc[split_idx:]
        
        # Calculate metrics
        train_metrics = calculate_metrics(train, initial_capital)
        test_metrics = calculate_metrics(test, train_metrics['final_balance'] if len(train) > 0 else initial_capital)
        
        # ==============================
        # Display Results
        # ==============================
        st.subheader(f"📊 Results for {selected_pair} - {strategy}")
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Performance", "📉 Charts", "📋 Trade List", "ℹ️ Data"])
        
        with tab1:
            # Training metrics
            st.subheader("🎓 Training Period Metrics")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Return", f"{train_metrics['total_return_pct']:.2f}%", 
                       delta=f"£{train_metrics['total_pnl_gbp']:,.0f}")
            col2.metric("Final Balance", f"£{train_metrics['final_balance']:,.0f}")
            col3.metric("Sharpe Ratio", f"{train_metrics['sharpe_ratio']:.2f}")
            col4.metric("Max Drawdown", f"{train_metrics['max_drawdown_pct']:.2f}%")
            
            col5, col6, col7, col8 = st.columns(4)
            col5.metric("Win Rate", f"{train_metrics['win_rate']:.1f}%")
            col6.metric("Profit Factor", f"{train_metrics['profit_factor']:.2f}")
            col7.metric("Total Trades", train_metrics['number_of_trades'])
            col8.metric("Total Pips", f"{train_metrics['total_pips']:.0f}")
            
            st.divider()
            
            # Testing metrics
            st.subheader("📝 Testing Period Metrics")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Return", f"{test_metrics['total_return_pct']:.2f}%",
                       delta=f"£{test_metrics['total_pnl_gbp']:,.0f}")
            col2.metric("Final Balance", f"£{test_metrics['final_balance']:,.0f}")
            col3.metric("Sharpe Ratio", f"{test_metrics['sharpe_ratio']:.2f}")
            col4.metric("Max Drawdown", f"{test_metrics['max_drawdown_pct']:.2f}%")
            
            col5, col6, col7, col8 = st.columns(4)
            col5.metric("Win Rate", f"{test_metrics['win_rate']:.1f}%")
            col6.metric("Profit Factor", f"{test_metrics['profit_factor']:.2f}")
            col7.metric("Total Trades", test_metrics['number_of_trades'])
            col8.metric("Total Pips", f"{test_metrics['total_pips']:.0f}")
            
            # Summary
            st.divider()
            st.subheader("📊 Strategy Summary")
            
            if test_metrics['total_return_pct'] > 0:
                st.success(f"✅ Strategy profitable in test period: {test_metrics['total_return_pct']:.2f}% return")
            else:
                st.error(f"❌ Strategy lost money in test period: {test_metrics['total_return_pct']:.2f}% return")
            
            if test_metrics['sharpe_ratio'] > 1:
                st.info(f"✅ Good risk-adjusted returns (Sharpe: {test_metrics['sharpe_ratio']:.2f})")
            elif test_metrics['sharpe_ratio'] > 0:
                st.info(f"⚠️ Acceptable risk-adjusted returns (Sharpe: {test_metrics['sharpe_ratio']:.2f})")
            else:
                st.info(f"❌ Poor risk-adjusted returns (Sharpe: {test_metrics['sharpe_ratio']:.2f})")
        
        with tab2:
            # Equity curves
            st.subheader("📈 Equity Curves")
            
            # Create equity curve dataframe
            train_equity = train['Account_Balance'] if len(train) > 0 else pd.Series()
            test_equity = test['Account_Balance'] if len(test) > 0 else pd.Series()
            
            # Plot
            fig = go.Figure()
            
            if len(train_equity) > 0:
                fig.add_trace(go.Scatter(x=train_equity.index, y=train_equity,
                                        name='Training Period', line=dict(color='blue')))
            
            if len(test_equity) > 0:
                fig.add_trace(go.Scatter(x=test_equity.index, y=test_equity,
                                        name='Testing Period', line=dict(color='green')))
            
            # Add buy & hold for comparison
            buy_hold = initial_capital * (df['Adj Close'] / df['Adj Close'].iloc[0])
            fig.add_trace(go.Scatter(x=df.index, y=buy_hold,
                                    name='Buy & Hold', line=dict(color='gray', dash='dash')))
            
            fig.update_layout(
                title="Account Balance Over Time",
                xaxis_title="Date",
                yaxis_title="Account Balance (£)",
                height=500,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Price chart with signals
            st.subheader("📉 Price Chart with Trading Signals")
            
            fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.05, row_heights=[0.7, 0.3])
            
            # Price line
            fig2.add_trace(go.Scatter(x=df.index, y=df['Adj Close'],
                                     name='Price', line=dict(color='blue')), row=1, col=1)
            
            # Buy signals
            buys = df[df['Signal'] == 1]
            fig2.add_trace(go.Scatter(x=buys.index, y=buys['Adj Close'],
                                     mode='markers', name='Buy Signal',
                                     marker=dict(color='green', size=10, symbol='triangle-up')), row=1, col=1)
            
            # Sell signals
            sells = df[df['Signal'] == -1]
            fig2.add_trace(go.Scatter(x=sells.index, y=sells['Adj Close'],
                                     mode='markers', name='Sell Signal',
                                     marker=dict(color='red', size=10, symbol='triangle-down')), row=1, col=1)
            
            # Add train/test divider
            if len(train) > 0:
                split_date = train.index[-1]
                fig2.add_vline(x=split_date, line_dash="dash", line_color="orange",
                              annotation_text="Train/Test Split", row=1, col=1)
            
            # Add indicator subplot
            if strategy == "RSI Strategy":
                fig2.add_trace(go.Scatter(x=df.index, y=df['RSI'],
                                         name='RSI', line=dict(color='purple')), row=2, col=1)
                fig2.add_hline(y=overbought, line_dash="dash", line_color="red", 
                              annotation_text="Overbought", row=2, col=1)
                fig2.add_hline(y=oversold, line_dash="dash", line_color="green",
                              annotation_text="Oversold", row=2, col=1)
                fig2.update_yaxes(title_text="RSI", row=2, col=1)
                
            elif strategy == "MACD Strategy":
                fig2.add_trace(go.Scatter(x=df.index, y=df['MACD'],
                                         name='MACD', line=dict(color='blue')), row=2, col=1)
                fig2.add_trace(go.Scatter(x=df.index, y=df['MACD_signal'],
                                         name='Signal Line', line=dict(color='orange')), row=2, col=1)
                fig2.update_yaxes(title_text="MACD", row=2, col=1)
                
            else:  # Bollinger
                fig2.add_trace(go.Scatter(x=df.index, y=df['BB_upper'],
                                         name='Upper Band', line=dict(color='gray', dash='dash')), row=1, col=1)
                fig2.add_trace(go.Scatter(x=df.index, y=df['BB_lower'],
                                         name='Lower Band', line=dict(color='gray', dash='dash')), row=1, col=1)
                fig2.add_trace(go.Scatter(x=df.index, y=df['BB_middle'],
                                         name='Middle Band', line=dict(color='black')), row=1, col=1)
            
            fig2.update_layout(height=700, showlegend=True)
            fig2.update_xaxes(title_text="Date", row=2, col=1)
            st.plotly_chart(fig2, use_container_width=True)
        
        with tab3:
            st.subheader("📋 Trade List")
            
            # Create trade list
            trades = df[df['Signal'] != 0].copy()
            if len(trades) > 0:
                trade_data = []
                for i in range(len(trades) - 1):
                    entry = trades.index[i]
                    exit_idx = trades.index[i + 1]
                    
                    entry_price = df.loc[entry, 'Adj Close']
                    exit_price = df.loc[exit_idx, 'Adj Close']
                    signal = trades.loc[entry, 'Signal']
                    
                    # Calculate pips
                    if signal == 1:
                        pips = (exit_price - entry_price) / 0.0001
                        pnl = (exit_price - entry_price) * lot_size / 1.25  # Approx GBP
                    else:
                        pips = (entry_price - exit_price) / 0.0001
                        pnl = (entry_price - exit_price) * lot_size / 1.25
                    
                    trade_data.append({
                        'Entry Date': entry.strftime('%Y-%m-%d'),
                        'Exit Date': exit_idx.strftime('%Y-%m-%d'),
                        'Type': 'LONG' if signal == 1 else 'SHORT',
                        'Entry Price': f"{entry_price:.5f}",
                        'Exit Price': f"{exit_price:.5f}",
                        'Pips': f"{pips:.1f}",
                        'P&L (£)': f"£{pnl:,.2f}",
                        'Period': 'Train' if entry <= train.index[-1] else 'Test'
                    })
                
                trade_df = pd.DataFrame(trade_data)
                st.dataframe(trade_df, use_container_width=True)
                
                # Download button
                csv = trade_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Trade List as CSV",
                    data=csv,
                    file_name=f"{selected_pair}_{strategy}_trades.csv",
                    mime="text/csv"
                )
            else:
                st.info("No trades generated by this strategy")
        
        with tab4:
            st.subheader("ℹ️ Raw Data")
            
            # Show recent data
            st.write("Recent Data (Last 50 rows)")
            display_cols = ['Adj Close', 'Signal', 'Account_Balance', 'Strategy_Returns']
            if 'RSI' in df.columns:
                display_cols.append('RSI')
            if 'MACD' in df.columns:
                display_cols.extend(['MACD', 'MACD_signal'])
            if 'BB_upper' in df.columns:
                display_cols.extend(['BB_upper', 'BB_middle', 'BB_lower'])
            
            st.dataframe(df[display_cols].tail(50), use_container_width=True)
            
            # Data stats
            st.subheader("📊 Data Statistics")
            col1, col2, col3 = st.columns(3)
            col1.metric("Date Range", f"{df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
            col2.metric("Total Days", len(df))
            col3.metric("Trading Days", len(df[df['Returns'] != 0]))
            
            # Download full data
            csv_full = df.to_csv()
            st.download_button(
                label="📥 Download Full Data as CSV",
                data=csv_full,
                file_name=f"{selected_pair}_{strategy}_full_data.csv",
                mime="text/csv"
            )

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Forex Strategy Backtester v1.0")
st.sidebar.caption("RSI (30/70) | MACD (12/26/9) | Bollinger (20,2)")
