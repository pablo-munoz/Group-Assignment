# File: pages/4_Technical_Analysis.py
"""
Display moving averages, Bollinger Bands, RSI and MACD for a single
asset with fully parametric controls. Relies only on libraries declared
in *requirements.txt* (streamlit, yfinance, plotly, pandas, numpy).
"""

from datetime import date, timedelta
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import load_data  # cached data fetcher

# ─── Page config & header ─────────────────────────────────────
st.set_page_config(page_title="Technical Analysis", page_icon="💹")
st.subheader("Technical Analysis")

# ─── Sidebar inputs ──────────────────────────────────────────
_get_state = lambda k, d: st.session_state.get(k, d)

ticker = st.sidebar.text_input(
    "Ticker for Technical Analysis:",
    value=_get_state("selected_ticker", "AAPL")
).strip().upper()
st.session_state.selected_ticker = ticker

# Shared date state
if "ta_start" not in st.session_state:
    st.session_state.ta_start = date.today() - timedelta(days=730)  # 2 yr default
if "ta_end" not in st.session_state:
    st.session_state.ta_end = date.today()

start_date = st.sidebar.date_input("Start Date:", st.session_state.ta_start)
end_date = st.sidebar.date_input("End Date:", st.session_state.ta_end)

if start_date > end_date:
    st.sidebar.error("Start date must be before end date.")
    st.stop()

st.session_state.ta_start = start_date
st.session_state.ta_end = end_date

# Indicator parameters
short_ma = st.sidebar.slider("Short MA window", 10, 100, 50, step=5)
long_ma = st.sidebar.slider("Long MA window", 100, 400, 200, step=10)
if short_ma >= long_ma:
    st.sidebar.error("Short MA must be < Long MA")
    st.stop()

rsi_win = st.sidebar.slider("RSI window", 7, 30, 14, step=1)

bollinger = st.sidebar.checkbox("Show Bollinger Bands (20, 2σ)", value=True)

# ─── Fetch data ───────────────────────────────────────────────
if not ticker:
    st.info("Enter a ticker to display charts.")
    st.stop()

with st.spinner("Fetching price data …"):
    df = load_data(ticker, start_date, end_date)

if df is None or df.empty:
    st.error(f"No data available for {ticker}.")
    st.stop()

price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
prices = df[price_col].dropna().copy()
prices.index = pd.to_datetime(prices.index)  # ensure datetime index

# ─── Compute indicators ──────────────────────────────────────
df = pd.DataFrame({"Price": prices})

df[f"SMA_{short_ma}"] = prices.rolling(window=short_ma).mean()
df[f"SMA_{long_ma}"] = prices.rolling(window=long_ma).mean()

# Bollinger Bands (20, 2σ)
if bollinger:
    sma20 = prices.rolling(20).mean()
    std20 = prices.rolling(20).std()
    df["BB_upper"] = sma20 + 2 * std20
    df["BB_lower"] = sma20 - 2 * std20

# RSI
delta = prices.diff()
gain = delta.clip(lower=0).rolling(rsi_win).mean()
loss = (-delta.clip(upper=0)).rolling(rsi_win).mean()
rs = gain / loss
rsi_series = 100 - 100 / (1 + rs)

df["RSI"] = rsi_series

# MACD (12-26-9)
ema12 = prices.ewm(span=12, adjust=False).mean()
ema26 = prices.ewm(span=26, adjust=False).mean()
df["MACD"] = ema12 - ema26
df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
df["Hist"] = df["MACD"] - df["Signal"]

# ─── Price chart with moving averages & Bollinger Bands ──────
price_fig = go.Figure()
price_fig.add_trace(go.Scatter(x=df.index, y=df["Price"], name="Price", mode="lines"))
price_fig.add_trace(go.Scatter(x=df.index, y=df[f"SMA_{short_ma}"], name=f"{short_ma}-SMA"))
price_fig.add_trace(go.Scatter(x=df.index, y=df[f"SMA_{long_ma}"], name=f"{long_ma}-SMA"))

if bollinger:
    price_fig.add_trace(go.Scatter(x=df.index, y=df["BB_upper"], name="BB upper", line=dict(width=0.5, dash="dot")))
    price_fig.add_trace(go.Scatter(x=df.index, y=df["BB_lower"], name="BB lower", line=dict(width=0.5, dash="dot")))

price_fig.update_layout(
    title=f"{ticker} Price + MAs", yaxis_title="Price (USD)", legend_title_text="Series"
)
st.plotly_chart(price_fig, use_container_width=True)

# ─── RSI chart ────────────────────────────────────────────────
rsi_fig = go.Figure()
rsi_fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name=f"RSI ({rsi_win})", mode="lines"))
rsi_fig.add_hline(y=30, line_dash="dot", line_color="green", annotation_text="30")
rsi_fig.add_hline(y=70, line_dash="dot", line_color="red", annotation_text="70")
rsi_fig.update_layout(title=f"{ticker} RSI ({rsi_win}-day)", yaxis_title="RSI")
st.plotly_chart(rsi_fig, use_container_width=True)

# ─── MACD chart ───────────────────────────────────────────────
# Colour histogram bars by sign for quicker polarity reading
bar_colors = np.where(df["Hist"] > 0, "green", "red")

macd_fig = go.Figure()
macd_fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD", mode="lines"))
macd_fig.add_trace(go.Scatter(x=df.index, y=df["Signal"], name="Signal", mode="lines"))
macd_fig.add_trace(go.Bar(x=df.index, y=df["Hist"], name="Hist", marker_color=bar_colors, opacity=0.4))
macd_fig.update_layout(title=f"{ticker} MACD", yaxis_title="MACD")

st.plotly_chart(macd_fig, use_container_width=True)

st.caption(f"Technical indicators for **{ticker}** from {start_date} to {end_date}.")
