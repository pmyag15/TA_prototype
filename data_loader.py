# data_loader.py
import pandas as pd
import os
from config import DATA_SOURCE, LOCAL_FILE_MAPPING, CURRENCY_PAIRS

def load_data(ticker, start_date=None, end_date=None):
    """
    Load data for a single currency pair from either local CSV or Yahoo Finance
    """
    if DATA_SOURCE == "local":
        # Load from your GitHub repo's data folder
        file_path = LOCAL_FILE_MAPPING.get(ticker)
        if file_path and os.path.exists(file_path):
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            
            # Filter by date if needed
            if start_date:
                df = df[df.index >= start_date]
            if end_date:
                df = df[df.index <= end_date]
                
            return df
        else:
            raise FileNotFoundError(f"Local file for {ticker} not found: {file_path}")
    
    elif DATA_SOURCE == "yahoo":
        # Future: Load from Yahoo Finance
        import yfinance as yf
        df = yf.download(ticker, start=start_date, end=end_date)
        return df
    
    else:
        raise ValueError(f"Unknown data source: {DATA_SOURCE}")

def load_all_pairs(start_date=None, end_date=None):
    """
    Load all 5 currency pairs
    """
    data = {}
    for ticker in CURRENCY_PAIRS:
        data[ticker] = load_data(ticker, start_date, end_date)
    return data
