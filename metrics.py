# metrics.py
import pandas as pd
import numpy as np

def calculate_metrics(data):
    """
    Calculate performance metrics from strategy returns
    No account balance, just pure percentage returns
    """
    if len(data) == 0:
        return {
            'total_return': 0.0,
            'sharpe': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'trades': 0
        }
    
    # Total return as percentage
    if 'Cumulative_Strategy' in data.columns:
        total_return = (data['Cumulative_Strategy'].iloc[-1] - 1) * 100
    else:
        total_return = ((1 + data['Strategy_Returns']).prod() - 1) * 100
    
    # Sharpe ratio (annualized)
    if data['Strategy_Returns'].std() != 0:
        sharpe = np.sqrt(252) * data['Strategy_Returns'].mean() / data['Strategy_Returns'].std()
    else:
        sharpe = 0.0
    
    # Max drawdown
    cum_returns = (1 + data['Strategy_Returns']).cumprod()
    peak = cum_returns.cummax()
    drawdown = (cum_returns - peak) / peak
    max_dd = drawdown.min() * 100
    
    # Win rate (percentage of days with positive returns)
    winning_days = (data['Strategy_Returns'] > 0).sum()
    total_days = len(data)
    win_rate = (winning_days / total_days * 100) if total_days > 0 else 0.0
    
    # Number of trades (days with signal changes)
    trades = (data['Signal'] != 0).sum()
    
    return {
        'total_return': total_return,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
        'trades': trades
    }

def calculate_market_return(data):
    """Calculate buy and hold return"""
    if len(data) == 0:
        return 0.0
    return (data['Cumulative_Market'].iloc[-1] - 1) * 100 if 'Cumulative_Market' in data.columns else 0.0
