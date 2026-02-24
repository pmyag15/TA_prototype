import pandas as pd

def generate_rsi_signal(df, oversold_threshold, overbought_threshold):
    """Strategy 1: RSI with user-provided thresholds"""
    sig = pd.Series(0, index=df.index)
    sig[df["RSI"] < oversold_threshold] = 1
    sig[df["RSI"] > overbought_threshold] = -1
    return sig

def generate_macd_signal(df):
    """Strategy 2: MACD crossover"""
    sig = pd.Series(0, index=df.index)
    macd_cross_above = (df["MACD"] > df["MACD_signal"]) & (df["MACD"].shift(1) <= df["MACD_signal"].shift(1))
    macd_cross_below = (df["MACD"] < df["MACD_signal"]) & (df["MACD"].shift(1) >= df["MACD_signal"].shift(1))
    sig[macd_cross_above] = 1
    sig[macd_cross_below] = -1
    return sig

def generate_bollinger_signal(df):
    """Strategy 3: Bollinger Bands"""
    sig = pd.Series(0, index=df.index)
    price = df["Adj Close"]
    sig[price <= df["BB_lower"]] = 1
    sig[price >= df["BB_upper"]] = -1
    return sig
