import pandas as pd
import yfinance as yf


def apply_sma_strategy(ticker, start_date, end_date, short_window, long_window, take_profit_pct, stop_loss_pct):
    # Step 1: Download data
    df = yf.download(ticker, start=start_date, end=end_date)
    df = df[['Close']].copy()

    # Step 2: Calculate SMAs
    df['SMA_Short'] = df['Close'].rolling(window=short_window).mean()
    df['SMA_Long'] = df['Close'].rolling(window=long_window).mean()

    # Step 3: Generate signals
    df['Signal'] = 0
    df.loc[short_window:, 'Signal'] = (df['SMA_Short'][short_window:] > df['SMA_Long'][short_window:]).astype(int)
    df['Signal'] = df['Signal'].diff()

    # Step 4: TP/SL logic
    in_trade = False
    entry_price = 0
    tp_sl_signal = []

    for i in range(len(df)):
        price = df['Close'].iloc[i]
        signal = df['Signal'].iloc[i]

        if not in_trade:
            if signal == 1:
                entry_price = price
                in_trade = True
                tp_sl_signal.append(1)
            else:
                tp_sl_signal.append(0)
        else:
            current_return = (price - entry_price) / entry_price
            sma_exit = signal == -1

            if current_return >= take_profit_pct or current_return <= -stop_loss_pct or sma_exit:
                in_trade = False
                tp_sl_signal.append(0)
            else:
                tp_sl_signal.append(1)

    df['TP_SL_Signal'] = tp_sl_signal

    # Step 5: Return calculations
    df['Market Return'] = df['Close'].pct_change()
    df['Strategy Return'] = df['Market Return'] * df['TP_SL_Signal'].shift(1)
    df['Cumulative Market Return'] = (1 + df['Market Return']).cumprod()
    df['Cumulative Strategy Return'] = (1 + df['Strategy Return']).cumprod()

    return df
