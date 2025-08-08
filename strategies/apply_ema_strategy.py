# strategies/apply_ema_strategy.py
import pandas as pd
import yfinance as yf
from datetime import datetime

def _download_prices(ticker: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    # Match notebook/SMA parity: no auto_adjust
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def _compute_ema(df: pd.DataFrame, short_window: int, long_window: int) -> pd.DataFrame:
    df = df.copy()
    # EMA via ewm; adjust=False = recursive (what most traders use)
    df[f"EMA_{short_window}"] = df["Close"].ewm(span=short_window, adjust=False).mean()
    df[f"EMA_{long_window}"] = df["Close"].ewm(span=long_window, adjust=False).mean()
    # Warmup drop after both EMAs have meaningful values (optional but consistent)
    df = df.dropna().copy()
    return df

def ema_strategy(
    ticker: str,
    start_date: datetime,
    end_date: datetime,
    short_window: int,
    long_window: int,
    take_profit: float,   # 0.20 -> 20%
    stop_loss: float,     # 0.05 -> 5%
) -> pd.DataFrame:

    df = _download_prices(ticker, start_date, end_date)
    if df.empty:
        return pd.DataFrame()

    df = _compute_ema(df, short_window, long_window)

    ema_s = df[f"EMA_{short_window}"]
    ema_l = df[f"EMA_{long_window}"]
    close = df["Close"]

    in_trade = False
    entry_price = 0.0
    pos = []

    for i in range(len(df)):
        s = ema_s.iat[i]
        l = ema_l.iat[i]
        c = close.iat[i]

        if not in_trade:
            # Enter whenever short > long (no explicit crossing)
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

    # Returns (next-bar application)
    df["Market Return"] = df["Close"].pct_change()
    df["Strategy Return"] = df["Market Return"] * df["TP_SL_Signal"].shift(1).fillna(0)

    df["Cumulative Market Return"] = (1 + df["Market Return"].fillna(0)).cumprod()
    df["Cumulative Strategy Return"] = (1 + df["Strategy Return"]).cumprod()

    return df
