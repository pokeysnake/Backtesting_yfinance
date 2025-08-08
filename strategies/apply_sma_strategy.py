import pandas as pd
import yfinance as yf
from datetime import datetime

def _download_prices(ticker: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    # Match the notebook: do NOT auto_adjust; flatten columns if needed
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def _compute_sma(df: pd.DataFrame, short_window: int, long_window: int) -> pd.DataFrame:
    df = df.copy()
    df[f"SMA_{short_window}"] = df["Close"].rolling(window=short_window).mean()
    df[f"SMA_{long_window}"] = df["Close"].rolling(window=long_window).mean()
    # Match notebook behavior: drop early NaNs after both SMAs are available
    df = df.dropna().copy()
    return df

def sma_strategy(
    ticker: str,
    start_date: datetime,
    end_date: datetime,
    short_window: int,
    long_window: int,
    take_profit: float,   # e.g. 0.20 for 20%
    stop_loss: float,     # e.g. 0.05 for 5%
) -> pd.DataFrame:

    df = _download_prices(ticker, start_date, end_date)
    if df.empty:
        return pd.DataFrame()

    df = _compute_sma(df, short_window, long_window)

    # --- Position logic (mirror the notebook’s TP/SL + trend behavior) ---
    in_trade = False
    entry_price = 0.0
    pos = []  # 1 in-trade, 0 flat

    sma_s = df[f"SMA_{short_window}"]
    sma_l = df[f"SMA_{long_window}"]
    close = df["Close"]

    for i in range(len(df)):
        s = sma_s.iat[i]
        l = sma_l.iat[i]
        c = close.iat[i]

        if not in_trade:
            # NOTE: enter whenever s > l (no crossing check)
            if s > l:
                in_trade = True
                entry_price = float(c)
                pos.append(1)
            else:
                pos.append(0)
        else:
            ret = (c - entry_price) / entry_price if entry_price else 0.0
            exit_trend = s < l
            hit_tp = (take_profit is not None and take_profit > 0 and ret >= take_profit)
            hit_sl = (stop_loss   is not None and stop_loss   > 0 and ret <= -stop_loss)

            if exit_trend or hit_tp or hit_sl:
                in_trade = False
                entry_price = 0.0
                pos.append(0)
            else:
                pos.append(1)

    df["TP_SL_Signal"] = pd.Series(pos, index=df.index, name="TP_SL_Signal")

    # --- Returns (match notebook math) ---
    df["Market Return"] = df["Close"].pct_change()
    df["Strategy Return"] = df["Market Return"] * df["TP_SL_Signal"].shift(1).fillna(0)

    # Cumulative (growth index, starts at 1.0)
    df["Cumulative Market Return"] = (1 + df["Market Return"].fillna(0)).cumprod()
    df["Cumulative Strategy Return"] = (1 + df["Strategy Return"]).cumprod()

    return df
