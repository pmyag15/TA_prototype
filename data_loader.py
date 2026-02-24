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
            # Download data
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if df.empty:
                st.error(f"No data returned from Yahoo Finance for {ticker}")
                return None
            
            # Yahoo Finance returns a DataFrame with columns
            # Reset the index to make Date a column, then set it as index again (standardizes format)
            df = df.reset_index()
            df = df.rename(columns={'Date': 'Date'})
            df = df.set_index('Date')
            
            # Ensure we have the required columns
            # Yahoo Finance returns: Open, High, Low, Close, Adj Close, Volume
            required_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
            
            # Check if we have all columns
            for col in required_cols:
                if col not in df.columns:
                    st.warning(f"Column '{col}' not found in Yahoo Finance data")
            
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
