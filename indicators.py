# indicators.py
import pandas as pd

def add_indicators(df, strategy, **kwargs):
    """
    Add technical indicators to dataframe
    """
    price = df["Adj Close"]
    
    if strategy == "RSI Strategy":
        # RSI calculation
        rsi_period = kwargs.get('rsi_period', 14)
        delta = price.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(rsi_period).mean()
        avg_loss = loss.rolling(rsi_period).mean()
        rs = avg_gain / avg_loss
        df["RSI"] = 100 - (100 / (1 + rs))
    
    elif strategy == "MACD Strategy":
        # MACD calculation
        macd_fast = kwargs.get('macd_fast', 12)
        macd_slow = kwargs.get('macd_slow', 26)
        macd_signal = kwargs.get('macd_signal', 9)
        
        ema_fast = price.ewm(span=macd_fast, adjust=False).mean()
        ema_slow = price.ewm(span=macd_slow, adjust=False).mean()
        df["MACD"] = ema_fast - ema_slow
        df["MACD_signal"] = df["MACD"].ewm(span=macd_signal, adjust=False).mean()
    
    elif strategy == "Bollinger Strategy":
        # Bollinger Bands calculation
        boll_period = kwargs.get('boll_period', 20)
        boll_std = kwargs.get('boll_std', 2)
        
        df["BB_middle"] = price.rolling(boll_period).mean()
        bb_std = price.rolling(boll_period).std()
        df["BB_upper"] = df["BB_middle"] + (bb_std * boll_std)
        df["BB_lower"] = df["BB_middle"] - (bb_std * boll_std)
    
    return df
