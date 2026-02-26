import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import DATA_SOURCE_OPTIONS, YAHOO_PAIRS, LOCAL_PAIRS, STRATEGY_OPTIONS
from data_loader import load_data
from indicators import add_indicators
from strategies import generate_signal
from metrics import calculate_metrics, calculate_market_return

st.set_page_config(layout="wide")
st.title("📊 Forex Trading Strategy Backtester")
st.caption("Test RSI, MACD, and Bollinger Band strategies on major forex pairs")

# ==============================
# Sidebar
# ==============================
st.sidebar.header("Data Settings")

data_source = st.sidebar.selectbox("Data Source", DATA_SOURCE_OPTIONS)

# Currency pair selection based on data source
if data_source == "Yahoo Finance (Live)":
    from config import YAHOO_PAIRS
    available_pairs = YAHOO_PAIRS
    pair_help = "All major forex pairs available via Yahoo Finance"
else:  # Local CSV Files
    from config import LOCAL_PAIRS
    available_pairs = LOCAL_PAIRS
    pair_help = "Only pairs with local CSV files in /data folder"

selected_pair = st.sidebar.selectbox(
    "Currency Pair", 
    available_pairs,
    help=pair_help
)

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

# Strategy
strategy = st.sidebar.selectbox("Trading Strategy", STRATEGY_OPTIONS)

# Train/Test split
split_ratio = st.sidebar.slider("Train/Test Split (% for training)", 50, 90, 70)

# Strategy parameters
st.sidebar.header("Parameters")

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

else:  # Bollinger
    boll_period = st.sidebar.slider("Bollinger Period", 10, 50, 20)
    boll_std = st.sidebar.slider("Standard Deviations", 1.0, 3.0, 2.0, 0.5)
    
    params = {
        'boll_period': boll_period,
        'boll_std': boll_std
    }

run_button = st.sidebar.button("🚀 Run Backtest", type="primary")

# ==============================
# Main App
# ==============================
if run_button:
    with st.spinner("Running backtest..."):
        
        # Load data
        df = load_data(data_source, selected_pair, start_date, end_date)
        
        if df is None or df.empty:
            st.error("No data loaded. Please check your settings.")
            st.stop()
        
        # Add indicators
        df = add_indicators(df, strategy, **params)
        
        # Generate signals
        df['Signal'] = generate_signal(df, strategy, **params)
        
        # ==============================
        # SIMPLE RETURNS CALCULATION
        # ==============================
        # Daily returns
        df['Returns'] = df['Adj Close'].pct_change()
        
        # Strategy returns (follow signal with 1 day delay)
        df['Strategy_Returns'] = df['Signal'].shift(1) * df['Returns']
        
        # Cumulative returns (starting from 1)
        df['Cumulative_Strategy'] = (1 + df['Strategy_Returns']).cumprod()
        df['Cumulative_Market'] = (1 + df['Returns']).cumprod()
        
        # Remove NaN
        df = df.dropna()
        
        # Split into train/test
        split_idx = int(len(df) * (split_ratio / 100))
        train = df.iloc[:split_idx]
        test = df.iloc[split_idx:]
        
        # ==============================
        # Display Results
        # ==============================
        st.subheader(f"📊 {selected_pair} - {strategy}")
        
        # Calculate metrics
        train_metrics = calculate_metrics(train)
        test_metrics = calculate_metrics(test)
        market_return = calculate_market_return(df)
        
        # Metrics row 1 - Profitability
        col1, col2, col3 = st.columns(3)
        col1.metric("Test Return", f"{test_metrics['total_return']:.2f}%")
        col2.metric("Buy-and-Hold Return", f"{market_return:.2f}%")
        col3.metric("Outperformance", f"{test_metrics['total_return'] - market_return:.2f}%")
        
        # Metrics row 2 - Consistency & Context
        col4, col5, col6, col7 = st.columns(4)
        col4.metric("Win Rate (Test)", f"{test_metrics['win_rate']:.1f}%")
        col5.metric("Test Trades", test_metrics['trades'])
        col6.metric("Train Trades", train_metrics['trades'])
        col7.metric("Train Return", f"{train_metrics['total_return']:.2f}%")
        
        # Equity curve
        st.subheader("📈 Growth of 1 unit")
        equity_df = pd.DataFrame({
            'Strategy': df['Cumulative_Strategy'],
            'Buy & Hold': df['Cumulative_Market']
        })
        st.line_chart(equity_df)
        
        # Price chart with signals
        st.subheader("📉 Price Chart with Signals")
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.05, row_heights=[0.7, 0.3])
        
        # Price line
        fig.add_trace(go.Scatter(x=df.index, y=df['Adj Close'],
                                 name='Price', line=dict(color='blue')), row=1, col=1)
        
        # Buy signals
        buys = df[df['Signal'] == 1]
        if len(buys) > 0:
            fig.add_trace(go.Scatter(x=buys.index, y=buys['Adj Close'],
                                     mode='markers', name='Buy',
                                     marker=dict(color='green', size=8, symbol='triangle-up')), row=1, col=1)
        
        # Sell signals
        sells = df[df['Signal'] == -1]
        if len(sells) > 0:
            fig.add_trace(go.Scatter(x=sells.index, y=sells['Adj Close'],
                                     mode='markers', name='Sell',
                                     marker=dict(color='red', size=8, symbol='triangle-down')), row=1, col=1)
        
        # Train/test split line
        if len(train) > 0:
            split_date = train.index[-1]
            fig.add_vline(x=split_date, line_dash="dash", line_color="orange", row=1, col=1)
            fig.add_annotation(x=split_date, y=0.98, yref="paper", text="Train/Test Split",
                              showarrow=False, font=dict(size=10, color="orange"), row=1, col=1)
        
        # Indicator subplot
        if strategy == "RSI Strategy":
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'],
                                     name='RSI', line=dict(color='purple')), row=2, col=1)
            fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=2, col=1)
            fig.update_yaxes(title_text="RSI", row=2, col=1)
            
        elif strategy == "MACD Strategy":
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD'],
                                     name='MACD', line=dict(color='blue')), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD_signal'],
                                     name='Signal', line=dict(color='orange')), row=2, col=1)
            fig.update_yaxes(title_text="MACD", row=2, col=1)
            
        else:  # Bollinger
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_upper'],
                                     name='Upper Band', line=dict(color='gray', dash='dash')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_lower'],
                                     name='Lower Band', line=dict(color='gray', dash='dash')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_middle'],
                                     name='Middle Band', line=dict(color='black')), row=1, col=1)
        
        fig.update_layout(height=700, showlegend=True)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent data
        st.subheader("📋 Recent Data")
        display_cols = ['Adj Close', 'Signal', 'Strategy_Returns', 'Cumulative_Strategy']
        if 'RSI' in df.columns:
            display_cols.append('RSI')
        if 'MACD' in df.columns:
            display_cols.extend(['MACD', 'MACD_signal'])
        if 'BB_upper' in df.columns:
            display_cols.extend(['BB_upper', 'BB_middle', 'BB_lower'])
        
        st.dataframe(df[display_cols].tail(20), use_container_width=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Forex Strategy Backtester v2.0")
st.sidebar.caption("RSI (30/70) | MACD (12/26/9) | Bollinger (20,2)")
