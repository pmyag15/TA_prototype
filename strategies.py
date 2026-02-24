# strategies.py
import pandas as pd

def generate_signal(df, strategy, **kwargs):
    """
    Generate trading signals based on the selected strategy
    """
    sig = pd.Series(0, index=df.index)
    
    if strategy == "RSI Strategy":
        # Get parameters with defaults
        rsi_oversold = kwargs.get('rsi_oversold', 30)
        rsi_overbought = kwargs.get('rsi_overbought', 70)
        
        # Buy when oversold, sell when overbought
        sig[df["RSI"] < rsi_oversold] = 1
        sig[df["RSI"] > rsi_overbought] = -1
    
    elif strategy == "MACD Strategy":
        # MACD crossover signals
        macd_cross_above = (df["MACD"] > df["MACD_signal"]) & (df["MACD"].shift(1) <= df["MACD_signal"].shift(1))
        macd_cross_below = (df["MACD"] < df["MACD_signal"]) & (df["MACD"].shift(1) >= df["MACD_signal"].shift(1))
        
        sig[macd_cross_above] = 1
        sig[macd_cross_below] = -1
    
    elif strategy == "Bollinger Strategy":
        # Bollinger Band signals
        sig[df["Adj Close"] <= df["BB_lower"]] = 1
        sig[df["Adj Close"] >= df["BB_upper"]] = -1
    
    return sig
