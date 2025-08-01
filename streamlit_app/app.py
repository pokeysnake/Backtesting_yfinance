import streamlit as st
import time
import yfinance as yf

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



#TITLE DISPLAY
st.title("Simple Back Testing Simulator")
st.sidebar.title("Select Desired Configurations")

#BACKTESTING BUTTON
with st.sidebar.container():
    run_backtest = st.button("Run Tests")

#TICKER INPUT
# Step 1: Mapping of common index names to valid tickers since you cant trade an index only etfs that reflect an index
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
        successful(f"✅ Selected Ticker: {resolved_ticker}",location = 'sidebar')
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



#LINKS TO BACKTESTING BUTTON --> RUNS CONFIGS USER HAS
if run_backtest:
    successful("Running backtest with current configuration")
    st.markdown(f"### Ticker selected: {user_input.upper()}")

    st.markdown(f"TP Level: {take_profit}%  \nStop Loss Level: {stop_loss}%")
    if sma:
        st.markdown(f"### **SMA Windows:**  \nShort = {sma_short_window},  \nLong = {sma_long_window}")
    if rsi:
        st.markdown(f"### **RSI Thresholds:**  \nOverbought = {rsi_overbought},  \nOversold: {rsi_oversold}")





