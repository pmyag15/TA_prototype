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
            
            # Format dates
            start_str = start_date.strftime('%Y-%m-%d') if start_date else '2020-01-01'
            end_str = end_date.strftime('%Y-%m-%d') if end_date else '2024-01-01'
            
            # METHOD 1: Try with interval='1d' (most reliable for forex)
            df = yf.download(
                ticker, 
                start=start_str, 
                end=end_str,
                interval='1d',
                progress=False,
                auto_adjust=True
            )
            
            # If that fails, try alternative approach
            if df.empty:
                st.warning("Trying alternative download method...")
                
                # METHOD 2: Use Ticker object
                ticker_obj = yf.Ticker(ticker)
                df = ticker_obj.history(start=start_str, end=end_str)
            
            # If still empty, try with period parameter
            if df.empty:
                st.warning("Trying with period parameter...")
                df = yf.download(ticker, period='5y', progress=False)
            
            if df.empty:
                st.error(f"No data returned from Yahoo Finance for {ticker}")
                return None
            
            # Standardize column names
            df.columns = [col.capitalize() for col in df.columns]
            
            # Ensure we have Adj Close (if not, use Close)
            if 'Adj Close' not in df.columns and 'Close' in df.columns:
                df['Adj Close'] = df['Close']
                st.info("Using 'Close' as 'Adj Close'")
            
            st.success(f"✅ Successfully loaded {len(df)} rows for {ticker}")
            return df
            
        except Exception as e:
            st.error(f"Error loading from Yahoo Finance: {e}")
            
            # Try one last method with different interval
            try:
                st.warning("Attempting final fallback method...")
                import yfinance as yf
                df = yf.download(ticker, period='max', interval='1d', progress=False)
                if not df.empty:
                    df.columns = [col.capitalize() for col in df.columns]
                    if 'Adj Close' not in df.columns and 'Close' in df.columns:
                        df['Adj Close'] = df['Close']
                    st.success("✅ Fallback method successful!")
                    return df
            except:
                pass
            
            return None
    
    else:  # Local CSV Files
        file_path = LOCAL_FILE_MAPPING.get(ticker)
        if file_path and os.path.exists(file_path):
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            
            # Filter by date if provided
            if start_date and end_date:
                df = df[(df.index >= pd.to_datetime(start_date)) & 
                        (df.index <= pd.to_datetime(end_date))]
            
            # Ensure we have Adj Close
            if 'Adj Close' not in df.columns:
                if 'Close' in df.columns:
                    df['Adj Close'] = df['Close']
                elif 'Price' in df.columns:
                    df['Adj Close'] = df['Price']
            
            return df
        else:
            st.error(f"Local file not found: {file_path}")
            return None
