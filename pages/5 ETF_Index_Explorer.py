# File: pages/5_ETF_Index_Explorer.py

"""
Explore major indices & ETFs: price history, 52‑week stats, YTD return,
optional SPY overlay, rolling volatility, and a monthly‑return heatmap.
Only core libraries (streamlit · yfinance · plotly · pandas · numpy).
"""

from datetime import date, timedelta, datetime as dt

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils import load_data

# ─── Page config & header ─────────────────────────────────────
st.set_page_config(page_title="ETF & Index Explorer", page_icon="🌐")
st.subheader("ETF & Index Explorer")

# ─── Pre‑defined list of common benchmarks ───────────────────
options = {
    "S&P 500 Index (^GSPC)": "^GSPC",
    "Dow Jones Industrial Avg (^DJI)": "^DJI",
    "Nasdaq Composite (^IXIC)": "^IXIC",
    "S&P 500 ETF (SPY)": "SPY",
    "Nasdaq‑100 ETF (QQQ)": "QQQ",
    "Russell 2000 ETF (IWM)": "IWM",
    "Developed Mkts ETF (EFA)": "EFA",
    "Emerging Mkts ETF (EEM)": "EEM",
}
choice = st.selectbox("Select an index or ETF:", list(options.keys()), index=0)
ticker = options[choice]

# Optional benchmark compare
compare_spy = st.sidebar.checkbox("Overlay SPY benchmark", value=False)

# Info blurb
info_dict = {
    "^GSPC": "Tracks 500 large‑cap U.S. stocks (market benchmark).",
    "^DJI": "Blue‑chip average of 30 major U.S. companies.",
    "^IXIC": "Broad, tech‑heavy Nasdaq Composite index.",
    "SPY": "ETF that replicates the S&P 500 index.",
    "QQQ": "ETF tracking the Nasdaq‑100 (large tech).",
    "IWM": "ETF tracking small‑cap Russell 2000.",
    "EFA": "ETF for developed markets ex‑US (MSCI EAFE).",
    "EEM": "ETF for MSCI Emerging Markets equities.",
}
st.info(info_dict[ticker])

# ─── Date range controls ─────────────────────────────────────
today = date.today()
start_date = st.sidebar.date_input("Start Date:", today - timedelta(days=5 * 365))
end_date = st.sidebar.date_input("End Date:", today)

if start_date > end_date:
    st.sidebar.error("Start date must be before end date.")
    st.stop()

# ─── Fetch price data ────────────────────────────────────────
with st.spinner("Fetching data …"):
    df = load_data(ticker, start_date, end_date)

if df is None or df.empty:
    st.error("No data available for the selected symbol / date range.")
    st.stop()

price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
prices = df[price_col].dropna()
if prices.empty:
    st.error("Price column is empty.")
    st.stop()

df.index = pd.to_datetime(df.index)

# ─── Price chart (+ optional SPY overlay) ────────────────────
if compare_spy and ticker != "SPY":
    spy_df = load_data("SPY", start_date, end_date)
    if spy_df is not None and not spy_df.empty:
        spy_prices = spy_df[price_col].dropna()
        prices_norm = prices / prices.iloc[0] * 100
        spy_norm = spy_prices / spy_prices.iloc[0] * 100
        price_fig = px.line(title=f"{choice} vs SPY (Normalised)")
        price_fig.add_scatter(x=prices_norm.index, y=prices_norm, name=ticker)
        price_fig.add_scatter(x=spy_norm.index, y=spy_norm, name="SPY", line=dict(dash="dot"))
    else:
        st.warning("Could not fetch SPY benchmark data.")
        price_fig = px.line(x=df.index, y=prices, title=f"{choice} Price History")
else:
    price_fig = px.line(x=df.index, y=prices, title=f"{choice} Price History")

price_fig.update_layout(xaxis_title="Date", yaxis_title="Price (USD)")
st.plotly_chart(price_fig, use_container_width=True)

# ─── Key metrics ─────────────────────────────────────────────
latest_price = prices.iloc[-1]
rolling_year = 252
rolling_high = prices.rolling(window=rolling_year).max().iloc[-1]
rolling_low = prices.rolling(window=rolling_year).min().iloc[-1]

ytd_start = dt(today.year, 1, 1)
ytd_prices = prices[prices.index >= ytd_start]
ytd_return = (latest_price / ytd_prices.iloc[0] - 1) * 100 if not ytd_prices.empty else np.nan
period_return = (latest_price / prices.iloc[0] - 1) * 100

col1, col2, col3 = st.columns(3)
col1.metric("Latest Price", f"{latest_price:.2f}")
col2.metric("52‑Week High", f"{rolling_high:.2f}")
col3.metric("52‑Week Low", f"{rolling_low:.2f}")

col4, col5 = st.columns(2)
if not np.isnan(ytd_return):
    col4.metric("YTD Return", f"{ytd_return:.2f}%")
col5.metric("Period Return", f"{period_return:.2f}%")

# ─── Rolling volatility chart ───────────────────────────────
vol_window = 30  # days
rolling_vol = prices.pct_change().rolling(vol_window).std() * np.sqrt(252) * 100
vol_fig = px.line(
    x=rolling_vol.index,
    y=rolling_vol,
    title=f"{vol_window}-Day Rolling Volatility (Annualised %)",
    labels={"x": "Date", "y": "Volatility (%)"},
)
st.plotly_chart(vol_fig, use_container_width=True)

# ─── Monthly return heatmap ─────────────────────────────────
with st.expander("Monthly Return Heatmap", expanded=False):
    monthly_prices = prices.resample("M").last()
    monthly_ret = monthly_prices.pct_change() * 100  # %
    monthly_ret = monthly_ret.dropna()
    if monthly_ret.empty:
        st.info("Not enough data to compute monthly returns.")
    else:
        heat_df = monthly_ret.to_frame("Return")
        heat_df["Year"] = heat_df.index.year
        heat_df["Month"] = heat_df.index.month_name().str[:3]
        pivot = heat_df.pivot(index="Year", columns="Month", values="Return").sort_index()
        # Ensure month order
        pivot = pivot[["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]]
        fig_heat = px.imshow(
            pivot,
            color_continuous_scale="RdYlGn",
            aspect="auto",
            title="Monthly % Returns",
        )
        st.plotly_chart(fig_heat, use_container_width=True)

# ─── Footer/caption ──────────────────────────────────────────
st.caption(f"Data via Yahoo Finance · {start_date} → {end_date}")
