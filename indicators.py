# indicators.py
import pandas as pd

def add_indicators(df, rsi_period, macd_fast, macd_slow, macd_signal, boll_period, boll_std):
    """
    Add technical indicators to dataframe with user-provided parameters
    """
    price = df["Adj Close"]
    
    # RSI Indicator
    delta = price.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(rsi_period).mean()
    avg_loss = loss.rolling(rsi_period).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    
    # MACD Indicator
    ema_fast = price.ewm(span=macd_fast, adjust=False).mean()
    ema_slow = price.ewm(span=macd_slow, adjust=False).mean()
    df["MACD"] = ema_fast - ema_slow
    df["MACD_signal"] = df["MACD"].ewm(span=macd_signal, adjust=False).mean()
    df["MACD_histogram"] = df["MACD"] - df["MACD_signal"]
    
    # Bollinger Bands
    df["BB_middle"] = price.rolling(boll_period).mean()
    bb_std = price.rolling(boll_period).std()
    df["BB_upper"] = df["BB_middle"] + (bb_std * boll_std)
    df["BB_lower"] = df["BB_middle"] - (bb_std * boll_std)
    
    return df
