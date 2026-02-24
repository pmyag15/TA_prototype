# metrics.py
import pandas as pd
import numpy as np

def calculate_metrics(df, initial_capital=10000):
    """
    Calculate core performance metrics
    """
    strategy_returns = df['Strategy_Returns'].dropna()
    account_balance = df['Account_Balance']
    
    if len(strategy_returns) == 0:
        return {
            'total_return_pct': 0,
            'total_pnl': 0,
            'final_balance': initial_capital,
            'sharpe_ratio': 0,
            'max_drawdown_pct': 0,
            'win_rate': 0,
            'number_of_trades': 0
        }
    
    # Total return
    final_balance = account_balance.iloc[-1]
    total_pnl = final_balance - initial_capital
    total_return_pct = (final_balance / initial_capital - 1) * 100
    
    # Sharpe ratio (simplified)
    if strategy_returns.std() != 0:
        sharpe = np.sqrt(252) * strategy_returns.mean() / strategy_returns.std()
    else:
        sharpe = 0
    
    # Max drawdown
    peak = account_balance.cummax()
    drawdown = (account_balance - peak) / peak
    max_dd_pct = drawdown.min() * 100
    
    # Win rate
    trades = df[df['Signal'] != 0].index
    if len(trades) > 1:
        # Simple win rate based on daily returns after signals
        days_after_signal = df['Strategy_Returns'].shift(-1)
        winning_days = (days_after_signal > 0).sum()
        total_days_with_signals = (df['Signal'] != 0).sum()
        win_rate = (winning_days / total_days_with_signals * 100) if total_days_with_signals > 0 else 0
    else:
        win_rate = 0
    
    return {
        'total_return_pct': total_return_pct,
        'total_pnl': total_pnl,
        'final_balance': final_balance,
        'sharpe_ratio': sharpe,
        'max_drawdown_pct': max_dd_pct,
        'win_rate': win_rate,
        'number_of_trades': (df['Signal'] != 0).sum()
    }
