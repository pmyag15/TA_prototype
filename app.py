# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from backtester import backtest_strategy, backtest_all_pairs
from config import CURRENCY_PAIRS, DATA_SOURCE
from data_loader import load_data

st.set_page_config(layout="wide")
st.title("📈 Forex Trading Strategy Backtester")

# Sidebar
st.sidebar.header("Configuration")

# Data source indicator
st.sidebar.info(f"📊 Data Source: **{DATA_SOURCE}**")
if DATA_SOURCE == "local":
    st.sidebar.caption("Using local CSV files from /data folder")

# Strategy selection
strategy = st.sidebar.selectbox(
    "Select Strategy",
    ["RSI", "MACD", "Bollinger"]
)

# Strategy parameters
st.sidebar.header("Strategy Parameters")

if strategy == "RSI":
    rsi_period = st.sidebar.number_input("RSI Period", 5, 50, 14)
    oversold = st.sidebar.number_input("Oversold Threshold", 10, 50, 30)
    overbought = st.sidebar.number_input("Overbought Threshold", 50, 90, 70)
    
    params = {
        'rsi_period': rsi_period,
        'oversold': oversold,
        'overbought': overbought
    }

elif strategy == "MACD":
    macd_fast = st.sidebar.number_input("Fast EMA", 5, 30, 12)
    macd_slow = st.sidebar.number_input("Slow EMA", 15, 50, 26)
    macd_signal = st.sidebar.number_input("Signal Line", 5, 20, 9)
    
    params = {
        'macd_fast': macd_fast,
        'macd_slow': macd_slow,
        'macd_signal': macd_signal
    }

else:  # Bollinger
    boll_period = st.sidebar.number_input("Bollinger Period", 5, 50, 20)
    boll_std = st.sidebar.number_input("Standard Deviations", 1.0, 4.0, 2.0, 0.5)
    
    params = {
        'boll_period': boll_period,
        'boll_std': boll_std
    }

# Backtest scope
st.sidebar.header("Backtest Scope")
scope = st.sidebar.radio("Run backtest on:", ["Single Pair", "All 5 Pairs"])

if scope == "Single Pair":
    selected_pair = st.sidebar.selectbox("Select Currency Pair", CURRENCY_PAIRS)
    
    # Load and backtest
    if st.sidebar.button("Run Backtest"):
        with st.spinner("Running backtest..."):
            df = load_data(selected_pair)
            results_df, metrics = backtest_strategy(df, strategy, **params)
            
        # Display results
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Return", f"{metrics['total_return']:.2f}%")
        col2.metric("Final Value", f"${metrics['final_value']:.2f}")
        col3.metric("Number of Trades", metrics['number_of_trades'])
        col4.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
        
        # Plot
        fig = make_subplots(rows=3, cols=1, 
                           shared_xaxes=True,
                           vertical_spacing=0.05,
                           row_heights=[0.5, 0.25, 0.25])
        
        # Price and signals
        fig.add_trace(go.Scatter(x=results_df.index, y=results_df['Adj Close'],
                                 name='Price', line=dict(color='blue')), row=1, col=1)
        
        # Buy signals
        buys = results_df[results_df['Signal'] == 1]
        fig.add_trace(go.Scatter(x=buys.index, y=buys['Adj Close'],
                                 mode='markers', name='Buy',
                                 marker=dict(color='green', size=10, symbol='triangle-up')), row=1, col=1)
        
        # Sell signals
        sells = results_df[results_df['Signal'] == -1]
        fig.add_trace(go.Scatter(x=sells.index, y=sells['Adj Close'],
                                 mode='markers', name='Sell',
                                 marker=dict(color='red', size=10, symbol='triangle-down')), row=1, col=1)
        
        # RSI if applicable
        if 'RSI' in results_df.columns:
            fig.add_trace(go.Scatter(x=results_df.index, y=results_df['RSI'],
                                     name='RSI', line=dict(color='purple')), row=2, col=1)
            fig.add_hline(y=overbought, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=oversold, line_dash="dash", line_color="green", row=2, col=1)
        
        # Portfolio value
        fig.add_trace(go.Scatter(x=results_df.index, y=results_df['Portfolio_Value'],
                                 name='Portfolio', line=dict(color='gold')), row=3, col=1)
        
        fig.update_layout(height=800, title_text=f"{selected_pair} - {strategy} Strategy")
        st.plotly_chart(fig, use_container_width=True)

else:  # All 5 Pairs
    if st.sidebar.button("Run Backtest on All Pairs"):
        with st.spinner("Running backtests..."):
            results = backtest_all_pairs(strategy, **params)
        
        # Summary table
        summary_data = []
        for ticker, result in results.items():
            metrics = result['metrics']
            summary_data.append({
                'Pair': ticker,
                'Total Return %': round(metrics['total_return'], 2),
                'Final Value $': round(metrics['final_value'], 2),
                'Trades': metrics['number_of_trades'],
                'Win Rate %': round(metrics['win_rate'], 1)
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.subheader("📊 Summary Results - All Pairs")
        st.dataframe(summary_df, use_container_width=True)
        
        # Bar chart comparison
        fig = go.Figure()
        fig.add_trace(go.Bar(x=summary_df['Pair'], y=summary_df['Total Return %'],
                             name='Total Return %', marker_color='lightblue'))
        fig.update_layout(title=f"{strategy} Strategy Performance Across All Pairs",
                         yaxis_title="Total Return %")
        st.plotly_chart(fig, use_container_width=True)
