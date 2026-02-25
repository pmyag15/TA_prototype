# config.py
import streamlit as st

# Data source selection
DATA_SOURCE_OPTIONS = [
    "Yahoo Finance (Live)", 
    "Selected Backtest Pairs (5 Major Forex Pairs)"
]

# Yahoo Finance - ALL available pairs (for live data)
YAHOO_PAIRS = [
    "EURUSD=X", "GBPUSD=X", "AUDUSD=X", "USDCAD=X", "USDJPY=X",
    "NZDUSD=X", "USDCHF=X", "EURGBP=X", "EURAUD=X", "GBPJPY=X",
    "AUDJPY=X", "EURJPY=X", "CADJPY=X", "CHFJPY=X", "NZDJPY=X"
]

# Local files - ONLY the 5 pairs 
LOCAL_PAIRS = ["EURUSD=X", "GBPUSD=X", "AUDUSD=X", "USDCAD=X", "USDJPY=X"]

# Local file mapping
LOCAL_FILE_MAPPING = {
    "EURUSD=X": "data/EURUSD=X.csv",
    "GBPUSD=X": "data/GBPUSD=X.csv",
    "AUDUSD=X": "data/AUDUSD=X.csv",
    "USDCAD=X": "data/USDCAD=X.csv",
    "USDJPY=X": "data/USDJPY=X.csv"
}

STRATEGY_OPTIONS = ["RSI Strategy", "MACD Strategy", "Bollinger Strategy"]
