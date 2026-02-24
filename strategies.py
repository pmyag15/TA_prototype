# strategies.py
import pandas as pd

def generate_signal(df, strategy,
                    rsi_oversold=30, rsi_overbought=70):
    
    sig = pd.Series(0, index=df.index)
    
    if strategy == "RSI Strategy":
        # Buy when oversold, sell when overbought
        sig[df["RSI"] < rsi_oversold] = 1
        sig[df["RSI"] > rsi_overbought] = -1
    
    elif strategy == "MACD Strategy":
        # Buy on bullish crossover, sell on bearish crossover
        macd_cross_above = (df["MACD"] > df["MACD_signal"]) & (df["MACD"].shift(1) <= df["MACD_signal"].shift(1))
        macd_cross_below = (df["MACD"] < df["MACD_signal"]) & (df["MACD"].shift(1) >= df["MACD_signal"].shift(1))
        sig[macd_cross_above] = 1
        sig[macd_cross_below] = -1
    
    elif strategy == "Bollinger Strategy":
        # Buy at lower band, sell at upper band
        sig[df["Adj Close"] <= df["BB_lower"]] = 1
        sig[df["Adj Close"] >= df["BB_upper"]] = -1
    
    return sig
