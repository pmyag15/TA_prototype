# metrics.py
import pandas as pd
import numpy as np

def run_backtest_with_position_sizing(df, strategy, initial_capital=50000, lot_size=100000):
    """
    Run backtest with proper forex position sizing
    
    Parameters:
    - initial_capital: Starting account balance in GBP
    - lot_size: Number of units (100000 = standard lot, 10000 = mini, 1000 = micro)
    """
    
    df = df.copy()
    
    # Calculate daily returns
    df['Returns'] = df['Adj Close'].pct_change()
    
    # Position sizing: Each signal trades 'lot_size' units
    # For EUR/USD, 1 pip = 0.0001, so pip value = lot_size * 0.0001 in USD
    df['Position_Units'] = df['Signal'] * lot_size
    
    # Simplified P&L calculation for forex
    # For a long position: P&L = (new_price - old_price) * lot_size
    # For a short position: P&L = (old_price - new_price) * lot_size
    price_change = df['Adj Close'].diff()
    df['Daily_PnL_USD'] = df['Position_Units'].shift(1) * price_change
    
    # Convert USD P&L to GBP (approximate using current rate)
    # In reality, you'd need proper GBP/USD rate
    gbp_usd_rate = 1.25  # Approximate
    df['Daily_PnL_GBP'] = df['Daily_PnL_USD'] / gbp_usd_rate
    
    # Track account balance
    df['Account_Balance'] = initial_capital + df['Daily_PnL_GBP'].cumsum()
    df['Account_Balance'] = df['Account_Balance'].clip(lower=0)  # Can't go below 0
    
    # Calculate strategy returns based on account balance
    df['Strategy_Returns'] = df['Daily_PnL_GBP'] / df['Account_Balance'].shift(1)
    df['Strategy_Returns'] = df['Strategy_Returns'].fillna(0)
    
    # Replace infinite values with 0
    df['Strategy_Returns'] = df['Strategy_Returns'].replace([np.inf, -np.inf], 0)
    
    return df

def calculate_metrics(df, initial_capital=50000):
    """
    Calculate all performance metrics
    """
    strategy_returns = df['Strategy_Returns'].dropna()
    account_balance = df['Account_Balance']
    
    if len(strategy_returns) == 0 or len(account_balance) == 0:
        return {
            'total_return_pct': 0,
            'total_pnl_gbp': 0,
            'final_balance': initial_capital,
            'sharpe_ratio': 0,
            'max_drawdown_pct': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'number_of_trades': 0,
            'avg_trade_pnl': 0,
            'total_pips': 0
        }
    
    # Total return in £ and %
    final_balance = account_balance.iloc[-1]
    total_pnl_gbp = final_balance - initial_capital
    total_return_pct = (final_balance / initial_capital - 1) * 100
    
    # Sharpe ratio (annualized)
    if strategy_returns.std() != 0:
        sharpe = np.sqrt(252) * strategy_returns.mean() / strategy_returns.std()
    else:
        sharpe = 0
    
    # Max drawdown
    peak = account_balance.cummax()
    drawdown = (account_balance - peak) / peak
    max_dd_pct = drawdown.min() * 100
    
    # Trade analysis
    trades = df[df['Signal'] != 0].copy()
    
    if len(trades) > 1:
        # Calculate trade P&L and pips
        trade_pnls = []
        trade_pips = []
        
        for i in range(len(trades) - 1):
            entry_idx = trades.index[i]
            exit_idx = trades.index[i + 1]
            
            # Get prices
            entry_price = df.loc[entry_idx, 'Adj Close']
            exit_price = df.loc[exit_idx, 'Adj Close']
            
            # Get signal
            signal = trades.loc[entry_idx, 'Signal']
            
            # Calculate pips (for EUR/USD, 1 pip = 0.0001)
            if signal == 1:  # Long
                pips = (exit_price - entry_price) / 0.0001
                trade_pnl = (exit_price - entry_price) * trades.loc[entry_idx, 'Position_Units']
            else:  # Short
                pips = (entry_price - exit_price) / 0.0001
                trade_pnl = (entry_price - exit_price) * trades.loc[entry_idx, 'Position_Units']
            
            # Convert to GBP (simplified)
            trade_pnl_gbp = trade_pnl / 1.25  # Approximate USD/GBP
            trade_pnls.append(trade_pnl_gbp)
            trade_pips.append(pips)
        
        if trade_pnls:
            winning_trades = sum(1 for pnl in trade_pnls if pnl > 0)
            win_rate = (winning_trades / len(trade_pnls)) * 100
            
            gross_profit = sum(pnl for pnl in trade_pnls if pnl > 0)
            gross_loss = abs(sum(pnl for pnl in trade_pnls if pnl < 0))
            profit_factor = gross_profit / gross_loss if gross_loss != 0 else float('inf')
            
            avg_trade_pnl = np.mean(trade_pnls)
            total_pips = np.sum(trade_pips)
        else:
            win_rate = 0
            profit_factor = 0
            avg_trade_pnl = 0
            total_pips = 0
    else:
        win_rate = 0
        profit_factor = 0
        avg_trade_pnl = 0
        total_pips = 0
    
    return {
        'total_return_pct': total_return_pct,
        'total_pnl_gbp': total_pnl_gbp,
        'final_balance': final_balance,
        'sharpe_ratio': sharpe,
        'max_drawdown_pct': max_dd_pct,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'number_of_trades': len(trades),
        'avg_trade_pnl': avg_trade_pnl,
        'total_pips': total_pips
    }
