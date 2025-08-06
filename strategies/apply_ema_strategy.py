import yfinance as yf
import pandas as pd

def ema_strategy(ticker, start_date, end_date, short_window, long_window, take_profit_pct, stop_loss_pct):
    # Step 1: Download data
    df = yf.download(ticker, start=start_date, end=end_date)
    df = df[['Close']].copy()

    # Step 2: Calculate EMAs
    df['EMA_Short'] = df['Close'].ewm(span=short_window, adjust=False).mean()
    df['EMA_Long'] = df['Close'].ewm(span=long_window, adjust=False).mean()

    # Step 3: Generate crossover signals
    df['Signal'] = 0
    df.loc[df['EMA_Short'] > df['EMA_Long'], 'Signal'] = 1    # Long
    df.loc[df['EMA_Short'] < df['EMA_Long'], 'Signal'] = -1   # Short

    # Step 4: TP/SL execution logic
    in_trade = False
    trade_type = None
    entry_price = 0
    tp_sl_signal = []

    for i in range(len(df)):
        price = df['Close'].iloc[i]
        signal = df['Signal'].iloc[i]

        if not in_trade:
            if signal != 0:
                in_trade = True
                trade_type = 'long' if signal == 1 else 'short'
                entry_price = price
                tp_sl_signal.append(signal)
            else:
                tp_sl_signal.append(0)
        else:
            # calculate return based on direction
            if trade_type == 'long':
                current_return = (price - entry_price) / entry_price
            else:
                current_return = (entry_price - price) / entry_price

            ema_exit = (signal == 0)

            if current_return >= take_profit_pct or current_return <= -stop_loss_pct or ema_exit:
                in_trade = False
                tp_sl_signal.append(0)
            else:
                tp_sl_signal.append(1 if trade_type == 'long' else -1)

    df['TP_SL_Signal'] = tp_sl_signal

    # Step 5: Return calculations
    df['Market Return'] = df['Close'].pct_change()
    df['Strategy Return'] = df['Market Return'] * df['TP_SL_Signal'].shift(1)
    df['Cumulative Market Return'] = (1 + df['Market Return']).cumprod()
    df['Cumulative Strategy Return'] = (1 + df['Strategy Return']).cumprod()

    return df
