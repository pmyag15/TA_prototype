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
            
            # Download data
            df = yf.download(ticker, start=start_str, end=end_str, progress=False)
            
            if df.empty:
                st.error(f"No data returned from Yahoo Finance for {ticker}")
                return None
            
            # Handle multi-level columns (tuple issue)
            if isinstance(df.columns, pd.MultiIndex):
                # Flatten multi-index columns
                df.columns = [col[0] for col in df.columns]
            else:
                # If not multi-index, just use as is
                df.columns = [str(col).replace(f' {ticker}', '').replace(ticker, '').strip() for col in df.columns]
            
            # Ensure we have standard column names
            column_mapping = {
                'Open': 'Open',
                'High': 'High',
                'Low': 'Low',
                'Close': 'Close', 
                'Adj Close': 'Adj Close',
                'Volume': 'Volume'
            }
            
            # Create standardized columns
            for std_col in column_mapping.values():
                # Try to find matching column
                for col in df.columns:
                    if std_col.lower() in col.lower():
                        df[std_col] = df[col]
                        break
            
            # Ensure we have Adj Close (use Close if not available)
            if 'Adj Close' not in df.columns:
                if 'Close' in df.columns:
                    df['Adj Close'] = df['Close']
                else:
                    # Try to find any price column
                    price_cols = [col for col in df.columns if 'close' in col.lower() or 'price' in col.lower()]
                    if price_cols:
                        df['Adj Close'] = df[price_cols[0]]
                    else:
                        st.error("No price data found in Yahoo Finance response")
                        return None
            
            # Keep only necessary columns
            keep_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
            df = df[[col for col in keep_cols if col in df.columns]]
            
            st.success(f"✅ Loaded {len(df)} rows for {ticker}")
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
