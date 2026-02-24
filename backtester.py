
import pandas as pd
from indicators import add_indicators
from strategies import generate_rsi_signal, generate_macd_signal, generate_bollinger_signal

def backtest_strategy(df, strategy_name, initial_capital=10000, **params):
    """
    Run backtest for a single currency pair
    """
    # Make a copy to avoid modifying original
    df = df.copy()
    
    # Add indicators
    df = add_indicators(
        df,
        rsi_period=params.get('rsi_period', 14),
        macd_fast=params.get('macd_fast', 12),
        macd_slow=params.get('macd_slow', 26),
        macd_signal=params.get('macd_signal', 9),
        boll_period=params.get('boll_period', 20),
        boll_std=params.get('boll_std', 2)
    )
    
    # Generate signals
    if strategy_name == "RSI":
        df['Signal'] = generate_rsi_signal(
            df, 
            oversold_threshold=params.get('oversold', 30),
            overbought_threshold=params.get('overbought', 70)
        )
    elif strategy_name == "MACD":
        df['Signal'] = generate_macd_signal(df)
    elif strategy_name == "Bollinger":
        df['Signal'] = generate_bollinger_signal(df)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    
    # Calculate metrics
    total_return = (df['Portfolio_Value'].iloc[-1] / initial_capital - 1) * 100
    trades = df[df['Signal'] != 0].shape[0]
    # After generating signals, ADD THIS SIMPLE CALCULATION:

# Calculate daily returns
df['Returns'] = df['Adj Close'].pct_change()

# Strategy returns: follow the signal (1 = long, -1 = short, 0 = flat)
df['Strategy_Returns'] = df['Signal'].shift(1) * df['Returns']

# Calculate cumulative returns (starting from 1)
df['Cumulative_Strategy'] = (1 + df['Strategy_Returns']).cumprod()
df['Cumulative_Market'] = (1 + df['Returns']).cumprod()

# Split into train/test
split_idx = int(len(df) * (split_ratio / 100))
train = df.iloc[:split_idx]
test = df.iloc[split_idx:]

# Calculate metrics using returns only
def calculate_simple_metrics(data):
    if len(data) == 0:
        return {
            'total_return': 0,
            'sharpe': 0,
            'max_drawdown': 0,
            'win_rate': 0,
            'trades': 0
        }
    
    total_return = ((1 + data['Strategy_Returns']).prod() - 1) * 100
    
    if data['Strategy_Returns'].std() != 0:
        sharpe = np.sqrt(252) * data['Strategy_Returns'].mean() / data['Strategy_Returns'].std()
    else:
        sharpe = 0
    
    cum_returns = (1 + data['Strategy_Returns']).cumprod()
    peak = cum_returns.cummax()
    drawdown = (cum_returns - peak) / peak
    max_dd = drawdown.min() * 100
    
    trades = (data['Signal'] != 0).sum()
    winning_days = (data['Strategy_Returns'] > 0).sum()
    win_rate = (winning_days / len(data) * 100) if len(data) > 0 else 0
    
    return {
        'total_return': total_return,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'win_rate': win_rate,
        'trades': trades
    }

train_metrics = calculate_simple_metrics(train)
test_metrics = calculate_simple_metrics(test)
    
    daily_win = df[df['Strategy_Returns'] > 0]['Strategy_Returns'].count()
    daily_total = df[df['Strategy_Returns'] != 0]['Strategy_Returns'].count()
    win_rate = (daily_win / daily_total * 100) if daily_total > 0 else 0
    
    metrics = {
        'total_return': total_return,
        'number_of_trades': trades,
        'win_rate': win_rate,
        'final_value': df['Portfolio_Value'].iloc[-1]
    }
    
    return df, metrics

def backtest_all_pairs(strategy_name, **params):
    """
    Run backtest on all 5 currency pairs
    """
    from data_loader import load_all_pairs
    
    all_data = load_all_pairs()
    results = {}
    
    for ticker, df in all_data.items():
        try:
            df_result, metrics = backtest_strategy(df, strategy_name, **params)
            results[ticker] = {
                'data': df_result,
                'metrics': metrics
            }
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            results[ticker] = {'error': str(e)}
    
    return results
