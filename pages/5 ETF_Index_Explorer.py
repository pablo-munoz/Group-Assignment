# File: pages/5_ETF_Index_Explorer.py
# --------------------------------------------------------------
# Quickly explore popular indices & ETFs
# --------------------------------------------------------------

from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from utils import load_data             # robust cached fetcher

# ─── Page config & header ─────────────────────────────────────
st.set_page_config(page_title="ETF & Index Explorer", page_icon="🌐")
st.subheader("ETF & Index Explorer")

# ─── Pre-defined list of common market benchmarks ─────────────
options = {
    "S&P 500 Index (^GSPC)":           "^GSPC",
    "Dow Jones Industrial Avg (^DJI)": "^DJI",
    "Nasdaq Composite (^IXIC)":        "^IXIC",
    "S&P 500 ETF (SPY)":               "SPY",
    "Nasdaq-100 ETF (QQQ)":            "QQQ",
    "Russell 2000 ETF (IWM)":          "IWM",
    "Developed Mkts ETF (EFA)":        "EFA",
    "Emerging Mkts ETF (EEM)":         "EEM",
}
choice = st.selectbox("Select an index or ETF:", list(options.keys()), index=0)
ticker = options[choice]

descriptions = {
    "^GSPC": "Tracks 500 large-cap U.S. stocks (market benchmark).",
    "^DJI":  "Blue-chip average of 30 major U.S. companies.",
    "^IXIC": "Broad, tech-heavy Nasdaq Composite index.",
    "SPY":   "ETF that replicates the S&P 500 index.",
    "QQQ":   "ETF tracking the Nasdaq-100 (large tech).",
    "IWM":   "ETF tracking small-cap Russell 2000.",
    "EFA":   "ETF for developed markets ex-US (MSCI EAFE).",
    "EEM":   "ETF for MSCI Emerging Markets equities.",
}
st.info(descriptions[ticker])

# ─── Date range (default 5 years) ────────────────────────────
today       = date.today()
start_date  = st.sidebar.date_input("Start Date:", today - timedelta(days=5 * 365))
end_date    = st.sidebar.date_input("End Date:",   today)
if start_date > end_date:
    st.sidebar.error("Start date must be before end date.")
    st.stop()

# ─── Fetch data ───────────────────────────────────────────────
df = load_data(ticker, start_date, end_date)
if df is None or df.empty:
    st.error("No data available for the selected symbol / date range.")
    st.stop()

# choose whichever price column exists
price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
prices    = df[price_col].dropna()
if prices.empty:
    st.error("Price column is empty.")
    st.stop()

# make sure the index is datetime
df.index = pd.to_datetime(df.index)

# ─── Price chart ──────────────────────────────────────────────
price_fig = px.line(
    x=df.index,
    y=prices,
    title=f"{choice} Price History",
    labels={"x": "Date", "y": "Price (USD)"},
)
st.plotly_chart(price_fig, use_container_width=True)

# ─── Key metrics ──────────────────────────────────────────────
latest_price = prices.iloc[-1]
rolling_year = 252
df["52w_high"] = prices.rolling(window=rolling_year).max()
df["52w_low"]  = prices.rolling(window=rolling_year).min()
high_52w       = df["52w_high"].iloc[-1]
low_52w        = df["52w_low"].iloc[-1]

# Year-to-date return
ytd_start   = datetime(today.year, 1, 1)
ytd_prices  = prices[prices.index >= ytd_start]
ytd_return  = (latest_price / ytd_prices.iloc[0] - 1) * 100 if not ytd_prices.empty else None
period_ret  = (latest_price / prices.iloc[0]      - 1) * 100

# ─── Display metrics ─────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Latest Price",   f"{latest_price:.2f}")
col2.metric("52-Week High",   f"{high_52w:.2f}")
col3.metric("52-Week Low",    f"{low_52w:.2f}")

col4, col5 = st.columns(2)
if ytd_return is not None:
    col4.metric("YTD Return", f"{ytd_return:.2f}%")
col5.metric("Period Return",  f"{period_ret:.2f}%")
