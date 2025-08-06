import pandas as pd
import yfinance as yf

def sma_strategy(ticker, start_date, end_date, short_window, long_window, take_profit_pct, stop_loss_pct):
    # Step 1: Download and prepare data
    df = yf.download(ticker, start=start_date, end=end_date)
    df = df[['Close']].copy()

    # Step 2: Calculate SMAs
    df['SMA_Short'] = df['Close'].rolling(window=short_window).mean()
    df['SMA_Long'] = df['Close'].rolling(window=long_window).mean()

    # Step 3: Generate signals
    df['Signal'] = 0
    df.loc[(df['SMA_Short'] > df['SMA_Long']), 'Signal'] = 1   # Long signal
    df.loc[(df['SMA_Short'] < df['SMA_Long']), 'Signal'] = -1  # Short signal

    # Step 4: TP/SL logic
    in_trade = False
    entry_price = 0
    position_type = None  # 'long' or 'short'
    tp_sl_signal = []

    for i in range(len(df)):
        price = df['Close'].iloc[i]
        signal = df['Signal'].iloc[i]

        if not in_trade:
            if signal == 1:
                in_trade = True
                position_type = 'long'
                entry_price = price
                tp_sl_signal.append(1)
            elif signal == -1:
                in_trade = True
                position_type = 'short'
                entry_price = price
                tp_sl_signal.append(-1)
            else:
                tp_sl_signal.append(0)
        else:
            if position_type == 'long':
                current_return = (price - entry_price) / entry_price
                sma_exit = signal == -1
            else:
                current_return = (entry_price - price) / entry_price
                sma_exit = signal == 1

            if current_return >= take_profit_pct or current_return <= -stop_loss_pct or sma_exit:
                in_trade = False
                position_type = None
                tp_sl_signal.append(0)
            else:
                tp_sl_signal.append(1 if position_type == 'long' else -1)

    df['TP_SL_Signal'] = tp_sl_signal

    # Step 5: Calculate returns
    df['Market Return'] = df['Close'].pct_change()
    strat_returns = []

    for i in range(len(df)):
        if i == 0:
            strat_returns.append(0)
        else:
            signal = df['TP_SL_Signal'].iloc[i-1]
            ret = df['Market Return'].iloc[i]
            strat_returns.append(ret if signal == 1 else (-ret if signal == -1 else 0))

    df['Strategy Return'] = strat_returns
    df['Cumulative Market Return'] = (1 + df['Market Return']).cumprod()
    df['Cumulative Strategy Return'] = (1 + df['Strategy Return']).cumprod()

    return df
