import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import DATA_SOURCE_OPTIONS, CURRENCY_PAIRS, STRATEGY_OPTIONS
from data_loader import load_data
from indicators import add_indicators
from strategies import generate_signal
from metrics import calculate_metrics

st.set_page_config(layout="wide")
st.title("📊 Forex Trading Strategy Backtester")
st.caption("Test RSI, MACD, and Bollinger Band strategies on major forex pairs")

# ==============================
# Sidebar
# ==============================
st.sidebar.header("Configuration")

# Data source
data_source = st.sidebar.selectbox("Data Source", DATA_SOURCE_OPTIONS)

# Currency pair
selected_pair = st.sidebar.selectbox("Currency Pair", CURRENCY_PAIRS)

# Date range
if data_source == "Yahoo Finance (Live)":
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime(2020, 1, 1))
    with col2:
        end_date = st.date_input("End Date", datetime(2024, 1, 1))
else:
    start_date = None
    end_date = None

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

# Position sizing (simplified)
st.sidebar.header("Position")
initial_capital = st.sidebar.number_input("Starting Capital (£)", 1000, 100000, 10000, 1000)
lot_size = st.sidebar.selectbox("Position Size", ["Standard (100k)", "Mini (10k)", "Micro (1k)"], index=1)

# Convert lot size
lot_units = {
    "Standard (100k)": 100000,
    "Mini (10k)": 10000,
    "Micro (1k)": 1000
}[lot_size]

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
        
        # Calculate returns with position sizing
        df['Returns'] = df['Adj Close'].pct_change()
        
        # Simple P&L calculation
        df['Position_Value'] = df['Signal'] * lot_units * df['Adj Close'] / 100000  # Simplified
        df['Daily_PnL'] = df['Position_Value'].shift(1) * df['Returns']
        df['Account_Balance'] = initial_capital + df['Daily_PnL'].cumsum()
        df['Strategy_Returns'] = df['Daily_PnL'] / df['Account_Balance'].shift(1)
        df['Strategy_Returns'] = df['Strategy_Returns'].fillna(0)
        df = df.dropna()
        
        # Split into train/test
        split_idx = int(len(df) * (split_ratio / 100))
        train = df.iloc[:split_idx]
        test = df.iloc[split_idx:]
        
        # Calculate metrics
        train_metrics = calculate_metrics(train, initial_capital)
        test_metrics = calculate_metrics(test, train_metrics['final_balance'])
        
        # ==============================
        # Display Results
        # ==============================
        st.subheader(f"📊 {selected_pair} - {strategy}")
        
        # Metrics in simple columns
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Test Return", f"{test_metrics['total_return_pct']:.2f}%")
        col2.metric("Final Balance", f"£{test_metrics['final_balance']:,.0f}")
        col3.metric("Sharpe", f"{test_metrics['sharpe_ratio']:.2f}")
        col4.metric("Max DD", f"{test_metrics['max_drawdown_pct']:.1f}%")
        
        col5, col6, col7, col8 = st.columns(4)
        col5.metric("Win Rate", f"{test_metrics['win_rate']:.1f}%")
        col6.metric("Trades", test_metrics['number_of_trades'])
        col7.metric("Train Return", f"{train_metrics['total_return_pct']:.2f}%")
        col8.metric("Train Sharpe", f"{train_metrics['sharpe_ratio']:.2f}")
        
        # Equity curve
        st.subheader("📈 Account Balance")
        equity_df = pd.DataFrame({
            'Strategy': df['Account_Balance'],
            'Buy & Hold': initial_capital * (df['Adj Close'] / df['Adj Close'].iloc[0])
        })
        st.line_chart(equity_df)
        
        # Price chart with signals
        st.subheader("📉 Price & Signals")
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.05, row_heights=[0.7, 0.3])
        
        # Price
        fig.add_trace(go.Scatter(x=df.index, y=df['Adj Close'],
                                 name='Price', line=dict(color='blue')), row=1, col=1)
        
        # Buy signals
        buys = df[df['Signal'] == 1]
        fig.add_trace(go.Scatter(x=buys.index, y=buys['Adj Close'],
                                 mode='markers', name='Buy',
                                 marker=dict(color='green', size=8, symbol='triangle-up')), row=1, col=1)
        
        # Sell signals
        sells = df[df['Signal'] == -1]
        fig.add_trace(go.Scatter(x=sells.index, y=sells['Adj Close'],
                                 mode='markers', name='Sell',
                                 marker=dict(color='red', size=8, symbol='triangle-down')), row=1, col=1)
        
               # Add train/test split line
        if len(train) > 0:
            split_date = train.index[-1]
            # Convert to string to avoid Plotly datetime bug
            split_date_str = split_date.strftime('%Y-%m-%d')
            
            # Add the vertical line without annotation first
            fig.add_vline(x=split_date, line_dash="dash", line_color="orange", row=1, col=1)
            
            # Add annotation separately
            fig.add_annotation(
                x=split_date,
                y=0.98,
                yref="paper",
                text="Train/Test Split",
                showarrow=False,
                font=dict(size=10, color="orange"),
                row=1, col=1
            )
        # Indicator subplot
        if strategy == "RSI Strategy":
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'],
                                     name='RSI', line=dict(color='purple')), row=2, col=1)
            fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=2, col=1)
            
        elif strategy == "MACD Strategy":
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD'],
                                     name='MACD', line=dict(color='blue')), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD_signal'],
                                     name='Signal', line=dict(color='orange')), row=2, col=1)
            
        else:  # Bollinger
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_upper'],
                                     name='Upper', line=dict(color='gray', dash='dash')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_lower'],
                                     name='Lower', line=dict(color='gray', dash='dash')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_middle'],
                                     name='Middle', line=dict(color='black')), row=1, col=1)
        
        fig.update_layout(height=600, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent trades
        st.subheader("📋 Recent Trades")
        recent_trades = df[df['Signal'] != 0].tail(10)[['Adj Close', 'Signal', 'Daily_PnL']]
        st.dataframe(recent_trades)
