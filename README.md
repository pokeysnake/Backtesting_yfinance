# 📈 Backtesting SMA/EMA/RSI Strategy with yFinance in Python

This project implements a simple but powerful backtesting framework for financial trading strategies using historical stock data from the `yfinance` API. It focuses on using common technical indicators — **Simple Moving Average (SMA)**, **Exponential Moving Average (EMA)**, and **Relative Strength Index (RSI)** — to simulate buy/sell decisions and visualize performance against the market.

The final goal is to transform this notebook into a **Streamlit-powered web app**, allowing users to experiment with different strategies, inputs, and thresholds interactively.

---

## ✅ Features

- Download historical OHLCV data using `yfinance`
- Calculate technical indicators:
  - Simple Moving Average (SMA)
  - Exponential Moving Average (EMA)
  - Relative Strength Index (RSI)
- Signal generation for:
  - Long-only strategy
  - Long/short strategy (enter short positions when bearish)
- Take-Profit (TP) and Stop-Loss (SL) logic for dynamic exits
- Strategy hold/until logic (e.g., hold until SMA cross or RSI reversal)
- Return calculations:
  - Daily market returns
  - Strategy returns
  - Cumulative return curves
- Signal markers (buy/sell) on price chart
- Compare strategy vs. buy-and-hold benchmark

---

## 📊 Sample Output

Plots include:
- Close price with SMA/EMA lines or RSI levels
- Buy/sell signal markers
  - Green ↑ triangle = long entry
  - Red ↓ triangle = short entry
- Cumulative return graph for strategy vs. benchmark (Buy & Hold)

---

## 🚀 How to Run

1. **Clone the repository**:

    ```bash
    git clone https://github.com/your-username/Backtesting_yfinance.git
    cd Backtesting_yfinance
    ```

2. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

    Or manually:

    ```bash
    pip install yfinance pandas matplotlib seaborn mplfinance
    ```

3. **Open a notebook**:

    ```bash
    jupyter notebook notebooks/SMA_Strategy_dev.ipynb
    ```

4. **Run all cells** to fetch data, compute signals, and visualize results.

---

## 🧠 Strategy Logic Overview

### SMA Crossover

- Buy (long) when SMA(20) crosses above SMA(50)
- Sell (short) when SMA(20) crosses below SMA(50)
- Take-Profit / Stop-Loss (%) levels trigger exit conditions
- Strategy holds until either TP/SL or next crossover

### RSI Crossover

- Buy when RSI crosses above oversold (default: 30)
- Sell when RSI crosses below overbought (default: 70)
- TP/SL logic plus optional RSI-based exit (e.g., cross under 50)
- Support for both long and short entries

Returns are compounded using:

```python
(principle + strategy_return).cumprod()
```

🌐 Future Features & Streamlit Goals

Planned expansion includes a fully interactive Streamlit app with:

- User-uploaded or selected tickers (via input box)

- Toggleable indicators (SMA, EMA, RSI, or combo)

- Adjustable indicator windows (e.g., SMA 20/50, RSI 14/30)

- TP/SL (%) configuration

- Profit curve vs SPY, QQQ, or VTI over same period

- Strategy signal visualization with export options

- Multi-ticker backtesting and summary

- Save/load strategy presets (optional)

- Candlestick charts and enhanced UI responsiveness

📦 Dependencies
  ```
    yfinance

    pandas

    numpy

    matplotlib

    seaborn

    mplfinance (optional for candlesticks)
  ```
📁 File Structure

Backtesting_yfinance/
│

├── notebooks/

│     ├── SMA_Strategy_dev.ipynb       # Current working SMA strategy

│     ├── RSI_Strategy_dev.ipynb       # Working RSI crossover strategy

│     └── [future] EMA_Strategy_dev.ipynb

│

├── requirements.txt                 # Python dependencies

├── README.md                        # This file

└── .gitignore                       # To ignore data/output
