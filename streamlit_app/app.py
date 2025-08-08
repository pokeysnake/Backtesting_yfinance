import sys
import os
from datetime import datetime, timedelta
import streamlit as st
import time
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
# Append the current directory so we can import from strategies/
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import importlib
import strategies.apply_sma_strategy as sma_module
importlib.reload(sma_module)
sma_strategy = sma_module.sma_strategy
import strategies.apply_ema_strategy as ema_module
importlib.reload(ema_module)
ema_strategy = ema_module.ema_strategy
import strategies.apply_rsi_strategy as rsi_module
importlib.reload(rsi_module)
rsi_strategy = rsi_module.rsi_strategy



#HELPER METHODS
#POPUP MESSAGE FUNCTIONS
def successful(message, location = 'main'):
    if location == 'sidebar':
        msg_placeholder = st.sidebar.empty()
    else:
        msg_placeholder = st.empty()
    
    msg_placeholder.success(message)
    time.sleep(1)
    msg_placeholder.empty()

def combine_signals(signals: dict) -> pd.Series:
    """
    signals: {"sma": Series(0/1), "rsi": Series(0/1), "ema": Series(0/1)} (any can be None)
    2 strategies -> AND (both 1)
    3 strategies -> majority (>=2)
    1 strategy  -> pass-through
    """
    df = pd.DataFrame({k: v for k, v in signals.items() if v is not None})
    if df.shape[1] == 0:
        return None
    if df.shape[1] == 1:
        return df.iloc[:, 0]
    if df.shape[1] == 2:
        return (df.sum(axis=1) == 2).astype(int)
    return (df.sum(axis=1) >= 2).astype(int)

def _fmt_equity(equity_index: float) -> str:
    """1.00 -> 100.00% (+0.00% gain), 2.00 -> 200.00% (+100.00% gain)"""
    return f"{equity_index*100:.2f}% ({(equity_index-1)*100:+.2f}% gain)"

def runTest(ticker, take_profit, stop_loss, sma_cfg=None, rsi_cfg=None, ema_cfg=None):
    output = []

    start_date = datetime.today() - timedelta(days=365 * 5)
    end_date = datetime.today()

    successful("Running backtest with current configuration")

    output += [
        f"# Ticker selected: {ticker}",
        "## Configuration used:",
        f"**Take Profit Level:** {take_profit}%",
        f"**Stop Loss Level:** {stop_loss}%"
    ]
    if sma_cfg: output.append(f"**SMA Strategy:** Short = {sma_cfg[0]}, Long = {sma_cfg[1]}")
    if rsi_cfg: output.append(f"**RSI Strategy:** Overbought = {rsi_cfg[0]}, Oversold = {rsi_cfg[1]}")
    if ema_cfg: output.append(f"**EMA Strategy:** Short = {ema_cfg[0]},  Long = {ema_cfg[1]}")

    output.append(f"## **Strategy Results:**")

    # Run individual strategies 
    df_sma = None
    if sma_cfg:
        short_w, long_w = sma_cfg
        df_sma = sma_strategy(
            ticker, start_date, end_date, short_w, long_w,
            take_profit/100.0, stop_loss/100.0
        )

    df_rsi = None
    if rsi_cfg:
        r_overbought, r_oversold = rsi_cfg
        df_rsi = rsi_strategy(
            ticker, start_date, end_date,
            r_overbought, r_oversold,
            take_profit/100.0, stop_loss/100.0,
            period=14  # change if you expose this in UI later
    )

    df_ema = None
    if ema_cfg:
        e_short, e_long = ema_cfg
        df_ema = ema_strategy(
            ticker, start_date, end_date, e_short, e_long,
            take_profit/100.0, stop_loss/100.0
    )

    # Choose reference series (Close)
    ref = df_sma if df_sma is not None else (df_rsi if df_rsi is not None else df_ema)
    if ref is None or ref.empty:
        return output

    close = ref["Close"]
    mkt_ret = close.pct_change().fillna(0)
    cum_mkt = (1 + mkt_ret).cumprod()

    # --- Compute curves for any selected strategies ---
    strat_lines = []  # (label, cumulative_series)
    perf_lines = []   # text output strings

    if df_sma is not None:
        sig = df_sma["TP_SL_Signal"].reindex(close.index).fillna(0)
        cum = (1 + mkt_ret * sig.shift(1)).cumprod()
        strat_lines.append(("SMA Strategy", cum))
        perf_lines.append(f"#### **SMA Strategy Final Equity:** {_fmt_equity(float(cum.iloc[-1]))}")

    if df_rsi is not None:
        sig = df_rsi["TP_SL_Signal"].reindex(close.index).fillna(0)
        cum = (1 + mkt_ret * sig.shift(1)).cumprod()
        strat_lines.append(("RSI Strategy", cum))
        perf_lines.append(f"#### **RSI Strategy Final Equity:** {_fmt_equity(float(cum.iloc[-1]))}")

    if df_ema is not None:
        sig = df_ema["TP_SL_Signal"].reindex(close.index).fillna(0)
        cum = (1 + mkt_ret * sig.shift(1)).cumprod()
        strat_lines.append(("EMA Strategy", cum))
        perf_lines.append(f"#### **EMA Strategy Final Equity:** {_fmt_equity(float(cum.iloc[-1]))}")

    # Combined (if >=2 strategies selected)
    sigs = {
        "sma": df_sma["TP_SL_Signal"] if df_sma is not None else None,
        "rsi": df_rsi["TP_SL_Signal"] if df_rsi is not None else None,
        "ema": df_ema["TP_SL_Signal"] if df_ema is not None else None,
    }
    selected_count = sum(x is not None for x in sigs.values())
    if selected_count >= 2:
        combined = combine_signals({k: (v.reindex(close.index) if v is not None else None) for k, v in sigs.items()})
        cum_combo = (1 + mkt_ret * combined.shift(1).fillna(0)).cumprod()
        strat_lines.append(("Combined Strategy", cum_combo))
        perf_lines.append(f"#### **Combined Strategy Final Equity:** {_fmt_equity(float(cum_combo.iloc[-1]))}")

    # Plot ONE chart total (BuyHold + any strategies + Combined)
    fig, ax = plt.subplots(figsize=(14, 6))
    (cum_mkt * 100).plot(ax=ax, linestyle="--", label="Buy & Hold")
    for label, cum in strat_lines:
        (cum * 100).plot(ax=ax, label=label)

    ax.set_title("Strategy vs Buy & Hold")
    ax.set_ylabel("Growth Index (Start = 100)")
    ax.set_xlabel("Date")
    ax.grid(True, alpha=0.3)
    ax.legend()
    st.pyplot(fig)

    output.extend(perf_lines)
    output.append(f"#### **Buy-and-Hold Final Equity:** {_fmt_equity(float(cum_mkt.iloc[-1]))}")
    return output



#GLOBAL VARIABLES
#TICKER INPUT
TICKER_MAP = {
    "sp500": "SPY",
    "s&p500": "SPY",
    "nasdaq": "QQQ",
    "dow": "DIA",
    "gold": "GLD",
    "totalmarket": "VTI",
    "russell": "IWM",
    "vix": "^VIX",
    "gspc": "^GSPC",
    "ndx": "^NDX"
}



#TITLE DISPLAY
st.set_page_config(layout="wide", page_title="Simple Back Testing Simulator")
st.markdown("""
<style>
/* widen content */
.block-container { max-width: 1200px; }
/* bump general font sizes a bit */
html, body, [class*="css"]  { font-size: 1.05rem; }
h1 { font-size: 2.0rem; }
h2 { font-size: 1.6rem; }
h3 { font-size: 1.3rem; }
</style>
""", unsafe_allow_html=True)


# TABS THAT USER CAN CLICK 
tabs = st.tabs(["How it Works", "BackTester"])


# *** HOW IT WORKS TAB ***
with tabs[0]:
    st.markdown("""
    #  How to Use This Application

    #### 1.**Enter a Ticker** 
       - In the sidebar, type a stock symbol (e.g., `AAPL`, `NVDA`) or a common index name (e.g., `sp500`, `nasdaq`).  
       - The app will try to fetch the full company/index name for confirmation.
                
    #### 2.**Set Take Profit & Stop Loss** 
       - Enter your desired **Stop Loss (%)** and **Take Profit (%)** levels.  
       - These are applied to all selected strategies.
                
    #### 3.**Choose Your Strategies** 
       - **SMA Strategy** — Buy when the short SMA is above the long SMA; sell when it's below or TP/SL is hit.  
       - **RSI Strategy** — Buy when RSI exits oversold; sell when exiting overbought.   
       - **EMA Strategy** — Buy when short EMA is above the long EMA; sell when it's below or TP/SL is hit.   
       - You can select any combination:
         - **One strategy** : Trades follow that strategy's signals only.  
         - **Two strategies** : Trade only when **both** agree.  
         - **Three strategies** : Trade when at least **two out of three** agree.
                
    #### 4.**Run the Backtest** 
       - Click **"Run Tests"** in the sidebar.  
       - The chart will display:
         - **Buy & Hold** performance 
         - Each selected strategy's return curve  
         - **Combined Strategy** curve (if more than one strategy is selected)
                
    #### 5.**Review Results** 
       - Final results show **Final Equity** (ex:  200%) and **Net Gain** (ex:  +100% gain).  
       - **Final Equity** is your total account value relative to the start (100% = starting capital).  
       - **Net Gain** shows the percentage increase over the initial investment.

    """)
    
    
    st.divider()
    st.markdown("# **How do each of these strategies work?**")
    st.markdown("## SMA Strategy")
    st.markdown("""
    The **Simple Moving Average (SMA)** strategy helps identify market trends by comparing two moving averages:

    -  **Buy** when the short SMA crosses **above** the long SMA.
    -  **Sell** when the short SMA crosses **below** the long SMA.
    """)

    st.markdown("####  Common SMA Ranges and What They're Good For")

    # Create the SMA table
    sma_data = {
        "Short SMA": ["5 - 10", "10 - 20", "20", "50"],
        "Long SMA": ["20 - 30", "50", "50", "200"],
        "Description": [
            "Very short-term. Good for quick trades or scalping.",
            "Balanced approach. Good for swing trading.",
            "One of the most popular settings for medium-term trend following.",
            "Long-term trend strategy. Stronger signals, fewer trades."
        ]
    }
    sma_df = pd.DataFrame(sma_data)
    st.dataframe(sma_df, hide_index=True)
    
    st.divider()

    st.markdown("## RSI Strategy")
    st.markdown("""
    The **Relative Strength Index (RSI)** measures the speed and change of price movements on a scale from 0 to 100.

    - **Buy** when RSI crosses above the oversold level (e.g. 30).  
    - **Sell** when RSI crosses below the overbought level (e.g. 70).  

    #### Adjusting thresholds lets you tune between conservative and aggressive trading.
    """)

    rsi_data ={
        "Use Case": ["Default", "Conservative", "Aggressive"],
        "Overbought": ["70", "80", "60"],
        "Oversold": ["30", "20", "40"],
        "Period" : ["5-9", "10-14", "20-30"]
    }
    rsi_df = pd.DataFrame(rsi_data)
    st.dataframe(rsi_df, hide_index=True)

    st.divider()


    st.markdown("## EMA Strategy")
    st.markdown("""
    **The Exponential Moving Average (EMA)** places more weight on recent prices than the SMA.

    - **Buy** when the short EMA crosses above the long EMA.  
    - **Sell** when the short EMA crosses below the long EMA.

    #### Lower-period EMAs react faster but can be noisier, while longer EMAs smooth out trends.
    """)
    ema_data =({
        "Short EMA": ["9", "12", "20", "50"],
        "Long EMA": ["21", "26", "50", "200"],
        "Style": ["Fast / Intraday", "Momentum", "Swing Trading", "Long-Term Trends"]
    })
    ema_df = pd.DataFrame(ema_data)
    st.dataframe(ema_df, hide_index=True)


# *** BACKTESTING TAB ***
with tabs[1]:
    #st.divider()
    st.sidebar.title("Select Desired Configurations")

    #BACKTESTING BUTTON
    with st.sidebar.container():
        if st.button("Run Tests"):
            st.session_state["run_test_triggered"] = True


    # ticker resolution
    user_input = st.sidebar.text_input("Enter ticker or common index name (e.g., AAPL, sp500, gold):").strip().lower()
    resolved_ticker = None
    full_name = None
    if user_input:
        # checks map if it is a known ticker
        resolved_ticker = TICKER_MAP.get(user_input, user_input.upper())  # default: all caps input

        # try pulling the full company name using yfinance
        try:
            ticker_info = yf.Ticker(resolved_ticker).info
            full_name = ticker_info.get('shortName') or ticker_info.get('longName') or "Unknown Company"
            #successful(f"✅ Selected Ticker: {resolved_ticker}",location = 'sidebar')
            st.sidebar.write(f"Full Name: **{full_name}**")
        except:
            st.sidebar.error("⚠️ Could not fetch data. Please check the ticker.")
            resolved_ticker = None  # prevent running backtest


    #TP/SL INPUTS
    st.sidebar.write("Select Desired Take Profit and Stop Loss Levels (%): ")
    stop_loss = st.sidebar.number_input("Stop Loss: ", min_value=0, max_value=100, step = 1, value = 5)
    take_profit = st.sidebar.number_input("Take Profit: ", min_value= stop_loss + 1, max_value=100, step = 1, value = 10)

    #SIDEBAR STRATEGY SELECTION
    st.sidebar.markdown("# Select strategy(s) you would like to use")
    sma = st.sidebar.checkbox("SMA Strategy")
    if sma:
        #st.sidebar.write("Select Configurations")
        st.sidebar.markdown("## Choose Short Moving Average Periods: Popular Choice is SMA(20/50)")
        sma_short_window = st.sidebar.number_input("Short Moving Average (Recommended 20+)", min_value=1, max_value=200, value=20, step = 1)
        sma_long_window = st.sidebar.number_input("Long Moving Average (Recommended 50+)", min_value = sma_short_window + 1, max_value=200, value=50, step = 1)

    rsi = st.sidebar.checkbox("RSI Strategy")
    if rsi:
        min_gap = 10
        #st.sidebar.write("Select Configurations")
        st.sidebar.markdown("## Choose Over bought/sold threshholds: Popular Choice is 70 and 30)")
        rsi_overbought = st.sidebar.number_input("Overbought threshold(Recommended at least 60)", min_value = 50, max_value=100, value=70, step = 1)
        max_oversold = rsi_overbought - min_gap
        rsi_oversold = st.sidebar.number_input("Long Moving Average (Recommended at most 40)", min_value = 10, max_value= max_oversold, value=30, step = 1)
        rsi_period = st.sidebar.number_input("RSI Period:", min_value=1, max_value=100, value=20, step = 1)

    ema = st.sidebar.checkbox("EMA Strategy")
    if ema:
        st.sidebar.markdown("## Choose the Short and Long moving averages: ")
        ema_short_window = st.sidebar.number_input("Short Moving Average: Recommended 10-20", min_value = 1, max_value=100, value = 10, step = 1)
        ema_long_window = st.sidebar.number_input("Long Moving Average: Recommended 2 - 2.5x of short window", min_value = ema_short_window + 1, max_value=100, value = 30, step = 1)

    #LINKS TO BACKTESTING BUTTON --> RUNS CONFIGS USER HAS
    # RUN TESTS IF TRIGGERED
    if st.session_state.get("run_test_triggered"):
        if not resolved_ticker or not any([sma, rsi, ema]):
            st.error("Please enter a valid ticker and select at least one strategy.")
        else:
            sma_cfg = (sma_short_window, sma_long_window) if sma else None
            rsi_cfg = (rsi_overbought, rsi_oversold) if rsi else None
            ema_cfg = (ema_short_window, ema_long_window) if ema else None

            st.session_state["backtest_output"] = runTest(
                resolved_ticker,
                take_profit,
                stop_loss,
                sma_cfg,
                rsi_cfg,
                ema_cfg
            )
        
        st.session_state["run_test_triggered"] = False

    if "backtest_output" in st.session_state:
        for line in st.session_state["backtest_output"]:
            st.markdown(line)






