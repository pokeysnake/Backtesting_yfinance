import streamlit as st
import time
import yfinance as yf
import pandas as pd

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

def display_config():
    config_lines = []

    if sma:
        config_lines.append(f"- SMA Strategy: {sma_short_window} / {sma_long_window}")
    if rsi:
        config_lines.append(f"- RSI Strategy: Overbought {rsi_overbought}, Oversold {rsi_oversold}")
    if ema:
        config_lines.append(f"- EMA Strategy: {ema_short_window} / {ema_long_window}")

    return "\n".join(config_lines)



def runTest(ticker, take_profit, stop_loss, sma_cfg=None, rsi_cfg=None, ema_cfg=None):
    output = []

    successful("Running backtest with current configuration")
    #output.append("---")
    output.append(f"## Ticker selected: {ticker}")
    #output.append("---")
    output.append("### Configuration used:")
    output.append(f"**Take Profit Level:** {take_profit}%")
    output.append(f"**Stop Loss Level:** {stop_loss}%")
    

    if sma_cfg:
        output.append(f"**SMA Strategy:** Short = {sma_cfg[0]}, Long = {sma_cfg[1]}")
    if rsi_cfg:
        output.append(f"**RSI Strategy:** Overbought = {rsi_cfg[0]}, Oversold = {rsi_cfg[1]}")
    if ema_cfg:
        output.append(f"**EMA Strategy:** Short = {ema_cfg[0]},  Long = {ema_cfg[1]}")

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
st.title("Simple Back Testing Simulator")

# TABS THAT USER CAN CLICK 
tabs = st.tabs(["How it Works", "BackTester"])


# *** HOW IT WORKS TAB ***
with tabs[0]:
    st.markdown("# **How do each of these strategies work?**")
    st.markdown("## SMA Strategy")
    st.markdown("""
    The **Simple Moving Average (SMA)** strategy helps identify market trends by comparing two moving averages:

    -  **Buy** when the short SMA crosses **above** the long SMA.
    -  **Sell** when the short SMA crosses **below** the long SMA.
    """)

    st.markdown("###  Common SMA Ranges and What They're Good For")

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
    The Relative Strength Index (RSI) measures the speed and change of price movements on a scale from 0 to 100.

    - **Buy** when RSI crosses above the oversold level (e.g. 30).  
    - **Sell** when RSI crosses below the overbought level (e.g. 70).  

    ### Adjusting thresholds lets you tune between conservative and aggressive trading.
    """)
    rsi_data =({
        "Use Case": ["Default", "Conservative", "Aggressive"],
        "Overbought": [70, 80, 60],
        "Oversold": [30, 20, 40]
    })
    rsi_df = pd.DataFrame(rsi_data)
    st.dataframe(rsi_df, hide_index=True)

    st.divider()


    st.markdown("## EMA Strategy")
    st.markdown("""
    The Exponential Moving Average (EMA) places more weight on recent prices than the SMA.

    - **Buy** when the short EMA crosses above the long EMA.  
    - **Sell** when the short EMA crosses below the long EMA.

    ### Lower-period EMAs react faster but can be noisier, while longer EMAs smooth out trends.
    """)
    ema_data =({
        "Short EMA": [9, 12, 20, 50],
        "Long EMA": [21, 26, 50, 200],
        "Style": ["Fast / Intraday", "Momentum", "Swing Trading", "Long-Term Trends"]
    })
    ema_df = pd.DataFrame(ema_data)
    st.dataframe(rsi_df, hide_index=True)




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
        sma_short_window = st.sidebar.number_input("Short Moving Average (Recommended 20+)", min_value=1, max_value=100, value=20, step = 1)
        sma_long_window = st.sidebar.number_input("Long Moving Average (Recommended 50+)", min_value = sma_short_window + 1, max_value=100, value=50, step = 1)

    rsi = st.sidebar.checkbox("RSI Strategy")
    if rsi:
        min_gap = 10
        #st.sidebar.write("Select Configurations")
        st.sidebar.markdown("## Choose Over bought/sold threshholds: Popular Choice is 70 and 30)")
        rsi_overbought = st.sidebar.number_input("Overbought threshold(Recommended at least 60)", min_value = 50, max_value=100, value=70, step = 1)
        max_oversold = rsi_overbought - min_gap
        rsi_oversold = st.sidebar.number_input("Long Moving Average (Recommended at most 40)", min_value = 10, max_value= max_oversold, value=30, step = 1)

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






