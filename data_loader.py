# data_loader.py
import pandas as pd
import os
from config import LOCAL_FILE_MAPPING
import streamlit as st

def load_data(data_source, ticker, start_date=None, end_date=None):
    """
    Load data from either Yahoo Finance or local CSV files
    """
    
    if data_source == "Yahoo Finance (Live)":
        try:
            import yfinance as yf
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if df.empty:
                st.error(f"No data returned from Yahoo Finance for {ticker}")
                return None
            return df
        except Exception as e:
            st.error(f"Error loading from Yahoo Finance: {e}")
            return None
    
    else:  # Local CSV Files
        file_path = LOCAL_FILE_MAPPING.get(ticker)
        if file_path and os.path.exists(file_path):
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            
            # Filter by date if provided
            if start_date and end_date:
                df = df[(df.index >= pd.to_datetime(start_date)) & 
                        (df.index <= pd.to_datetime(end_date))]
            return df
        else:
            st.error(f"Local file not found: {file_path}")
            return None
