# metrics.py
import pandas as pd
import numpy as np

def calculate_metrics(data):
    """
    Calculate performance metrics from strategy returns
    """
    if len(data) == 0:
        return {
            'total_return': 0.0,
            'win_rate': 0.0,
            'trades': 0
        }
    
    # Total return as percentage
    if 'Cumulative_Strategy' in data.columns:
        total_return = (data['Cumulative_Strategy'].iloc[-1] - 1) * 100
    else:
        total_return = ((1 + data['Strategy_Returns']).prod() - 1) * 100
    
    # Win rate calculated ONLY on active trading days
    active_days = data[data['Strategy_Returns'] != 0]
    if len(active_days) > 0:
        winning_days = (active_days['Strategy_Returns'] > 0).sum()
        win_rate = (winning_days / len(active_days) * 100)
    else:
        win_rate = 0.0
    
    # Number of trades (days with signal changes)
    trades = (data['Signal'] != 0).sum()
    
    return {
        'total_return': total_return,
        'win_rate': win_rate,
        'trades': trades
    }  # <-- Closing bracket added here

def calculate_market_return(data):
    """Calculate buy and hold return"""
    if len(data) == 0:
        return 0.0
    if 'Cumulative_Market' in data.columns:
        return (data['Cumulative_Market'].iloc[-1] - 1) * 100
    else:
        return ((1 + data['Returns']).prod() - 1) * 100
