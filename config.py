# config.py
import streamlit as st

# Data source selection
DATA_SOURCE_OPTIONS = ["Yahoo Finance (Live)", "Local CSV Files"]

# Currency pairs (Yahoo Finance symbols)
CURRENCY_PAIRS = ["EURUSD=X", "GBPUSD=X", "AUDUSD=X", "USDCAD=X", "USDJPY=X"]

# Local file mapping (only used if local files are selected)
LOCAL_FILE_MAPPING = {
    "EURUSD=X": "data/EURUSD=X.csv",
    "GBPUSD=X": "data/GBPUSD=X.csv",
    "AUDUSD=X": "data/AUDUSD=X.csv",
    "USDCAD=X": "data/USDCAD=X.csv",
    "USDJPY=X": "data/USDJPY=X.csv"
}

STRATEGY_OPTIONS = ["RSI Strategy", "MACD Strategy", "Bollinger Strategy"]
