# strategies/apply_rsi_strategy.py
import pandas as pd
import yfinance as yf
from datetime import datetime

def _download_prices(ticker: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    # Keep parity with SMA/EMA: no auto_adjust
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    Wilder's RSI (standard): uses exponential smoothing (adjust=False, alpha=1/period)
    """
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # If avg_loss is 0, rs -> inf, rsi -> 100; if avg_gain is 0, rsi -> 0 — fine.
    return rsi

def rsi_strategy(
    ticker: str,
    start_date: datetime,
    end_date: datetime,
    overbought: int,      # e.g., 70
    oversold: int,        # e.g., 30
    take_profit: float,   # 0.20 for 20%
    stop_loss: float,     # 0.05 for 5%
    period: int = 14,
) -> pd.DataFrame:
    """
    RSI swing strategy with TP/SL and next-bar execution, aligned with your app:

    Entry:
      • Go long when RSI crosses UP through the oversold level (yesterday <= oversold AND today > oversold)

    Exit (while in a trade):
      • RSI crosses DOWN through the overbought level (yesterday >= overbought AND today < overbought), OR
      • Take-profit: (Close - entry) / entry >= take_profit, OR
      • Stop-loss:   (Close - entry) / entry <= -stop_loss

    Returns DataFrame with:
      Close, RSI, TP_SL_Signal (0/1),
      Market Return, Strategy Return,
      Cumulative Market Return, Cumulative Strategy Return
    """
    df = _download_prices(ticker, start_date, end_date)
    if df.empty:
        return pd.DataFrame()

    df = df.copy()
    df["RSI"] = _compute_rsi(df["Close"], period=period)
    df = df.dropna().copy()

    rsi = df["RSI"]
    close = df["Close"]

    in_trade = False
    entry_price = 0.0
    pos = []

    for i in range(len(df)):
        r = rsi.iat[i]
        c = close.iat[i]

        # For cross checks we need the previous RSI value
        if i == 0:
            prev_r = r
        else:
            prev_r = rsi.iat[i - 1]

        if not in_trade:
            # Enter when RSI exits oversold (crosses up through oversold)
            crossed_up_from_oversold = (prev_r <= oversold) and (r > oversold)
            if crossed_up_from_oversold:
                in_trade = True
                entry_price = float(c)
                pos.append(1)
            else:
                pos.append(0)
        else:
            # Manage open trade
            ret = (c - entry_price) / entry_price if entry_price else 0.0

            crossed_down_from_overbought = (prev_r >= overbought) and (r < overbought)
            hit_tp = (take_profit is not None and take_profit > 0 and ret >= take_profit)
            hit_sl = (stop_loss   is not None and stop_loss   > 0 and ret <= -stop_loss)

            if crossed_down_from_overbought or hit_tp or hit_sl:
                in_trade = False
                entry_price = 0.0
                pos.append(0)
            else:
                pos.append(1)

    df["TP_SL_Signal"] = pd.Series(pos, index=df.index, name="TP_SL_Signal")

    # Returns (use next-bar execution like SMA/EMA)
    df["Market Return"] = df["Close"].pct_change()
    df["Strategy Return"] = df["Market Return"] * df["TP_SL_Signal"].shift(1).fillna(0)

    df["Cumulative Market Return"] = (1 + df["Market Return"].fillna(0)).cumprod()
    df["Cumulative Strategy Return"] = (1 + df["Strategy Return"]).cumprod()

    return df
