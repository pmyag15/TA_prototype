
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
    
    # Simple backtest logic
    df['Position'] = df['Signal'].shift(1)
    df['Returns'] = df['Adj Close'].pct_change()
    df['Strategy_Returns'] = df['Position'] * df['Returns']
    df['Portfolio_Value'] = initial_capital * (1 + df['Strategy_Returns']).cumprod()
    
    # Calculate metrics
    total_return = (df['Portfolio_Value'].iloc[-1] / initial_capital - 1) * 100
    trades = df[df['Signal'] != 0].shape[0]
    
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
