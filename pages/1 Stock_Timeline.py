"""
Streamlit App – Iteration 1a: Basic Stock Selector and Timeline
--------------------------------------------------------------
"""

# File: pages/1_Stock_Timeline.py
# --------------------------------------------------------------
# Basic price-timeline page (Iteration 1a)
# --------------------------------------------------------------

from datetime import date, timedelta, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from utils import load_data                # shared cached downloader

# ─── Page config & header ─────────────────────────────────────
st.set_page_config(page_title="Stock Timeline", page_icon="📈")
st.subheader("Stock Price Timeline")

# ─── Sidebar inputs ──────────────────────────────────────────
ticker = st.sidebar.text_input(
    "Ticker (stock / ETF / index):",
    value=st.session_state.get("selected_ticker", "AAPL")
).strip().upper()
st.session_state.selected_ticker = ticker

today         = date.today()
default_start = today - timedelta(days=365)
start_date    = st.sidebar.date_input("Start Date:", default_start)
end_date      = st.sidebar.date_input("End Date:",   today)
if start_date > end_date:
    st.sidebar.error("Start date must be before end date.")
    st.stop()

scale = st.sidebar.radio("Y-axis scale:", ["Linear", "Log"], index=0)

# ─── Fetch data ───────────────────────────────────────────────
if not ticker:
    st.info("Enter a ticker to display its price timeline.")
    st.stop()

df = load_data(ticker, start_date, end_date)
if df is None or df.empty:
    st.warning("No data returned for the selected ticker / date range.")
    st.stop()

# Pick whichever price column exists
price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
prices    = df[price_col].dropna()
if prices.empty:
    st.warning("No price data available.")
    st.stop()

# ─── Build chart dataframe ───────────────────────────────────
chart_df = (
    prices.reset_index()
    .rename(columns={"index": "Date", price_col: "Price"})
)

# ─── Plot line chart ─────────────────────────────────────────
fig = px.line(
    chart_df,
    x="Date",
    y="Price",
    title=f"{ticker} Price History",
    labels={"Price": "Price (USD)"},
)
fig.update_layout(xaxis_rangeslider_visible=True)
if scale == "Log":
    fig.update_yaxes(type="log")

st.plotly_chart(fig, use_container_width=True)
st.caption(f"Prices from {start_date} to {end_date} · data via Yahoo Finance")
