# File: pages/1_Stock_Timeline.py
# --------------------------------------------------------------
# Enhanced Stock Timeline page (Iteration 2)
# --------------------------------------------------------------

from __future__ import annotations

from datetime import date, timedelta
import io

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf

from utils import load_data  # shared, cached downloader

# ─── Page‑level settings ──────────────────────────────────────
st.set_page_config(page_title="Stock Timeline", page_icon="📈")
st.subheader("Stock Price Timeline")

# ─── Sidebar inputs ──────────────────────────────────────────
# Preserve shared context across pages

def _get_state(key: str, default):
    return st.session_state.get(key, default)

ticker = st.sidebar.text_input(
    "Ticker (stock / ETF / index):",
    value=_get_state("selected_ticker", "AAPL")
).strip().upper()
st.session_state.selected_ticker = ticker

# Date range (1‑year default)
today = date.today()
_default_start = today - timedelta(days=365)
start_date = st.sidebar.date_input("Start Date:", _get_state("start_date", _default_start))
end_date = st.sidebar.date_input("End Date:", _get_state("end_date", today))

if start_date > end_date:
    st.sidebar.error("Start date must be before end date.")
    st.stop()

st.session_state.start_date = start_date
st.session_state.end_date = end_date

scale = st.sidebar.radio("Y‑axis scale:", ["Linear", "Log"], index=0)
normalise = st.sidebar.checkbox("Normalise to 100 (start)", value=False)

# ─── Fetch & prep data ───────────────────────────────────────
if not ticker:
    st.info("Enter a ticker to display its price timeline.")
    st.stop()

with st.spinner("Fetching price data …"):
    df = load_data(ticker, start_date, end_date)

if df is None or df.empty:
    st.warning("No data returned for the selected ticker / date range.")
    st.stop()

price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
prices = df[price_col].dropna()
if prices.empty:
    st.warning("No price data available.")
    st.stop()

# Optional normalisation
if normalise:
    prices = prices / prices.iloc[0] * 100
    y_label = "Normalised Price (Start = 100)"
else:
    y_label = "Price (USD)"

chart_df = prices.reset_index().rename(columns={"index": "Date", price_col: "Price"})

# ─── Build figure: price line + volume bars ──────────────────
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Scatter(x=chart_df["Date"], y=chart_df["Price"], mode="lines", name="Price"),
    secondary_y=False,
)

# Volume (if available)
if "Volume" in df.columns:
    vol_series = df.loc[chart_df["Date"], "Volume"]  # align index
    fig.add_trace(
        go.Bar(x=chart_df["Date"], y=vol_series, name="Volume", opacity=0.3, marker_line_width=0),
        secondary_y=True,
    )
    fig.update_yaxes(title_text="Volume", secondary_y=True, showgrid=False)

fig.update_yaxes(title_text=y_label, secondary_y=False)
fig.update_layout(title=f"{ticker} Price History", xaxis_rangeslider_visible=True, legend_title_text="Legend")

if scale == "Log":
    fig.update_yaxes(type="log", secondary_y=False)

# ─── Event markers: earnings & dividends ─────────────────────
with st.spinner("Fetching corporate actions …"):
    try:
        info = yf.Ticker(ticker)
        # Earnings calendar
        cal = info.earnings_dates
        if cal is not None and not cal.empty:
            cal = cal[(cal.index.date >= start_date) & (cal.index.date <= end_date)]
            for d in cal.index:
                fig.add_vline(x=d, line_dash="dot", line_color="gray", annotation_text="Earnings")
        # Dividend events
        divs = info.dividends
        if divs is not None and not divs.empty:
            divs = divs[(divs.index.date >= start_date) & (divs.index.date <= end_date)]
            for d, v in divs.items():
                fig.add_vline(x=d, line_dash="dot", line_color="green", annotation_text=f"Div {v:.2f}")
    except Exception:
        # Fail silently – corporate events are optional
        pass

# ─── Render chart ────────────────────────────────────────────
st.plotly_chart(fig, use_container_width=True)

# ─── Downloads ───────────────────────────────────────────────
# Raw CSV
tmp_csv = chart_df.to_csv(index=False).encode()
st.download_button("Download CSV", tmp_csv, file_name=f"{ticker}_prices.csv", mime="text/csv")

# PNG snapshot (optional – requires kaleido)
try:
    img_bytes = fig.to_image(format="png", width=1200, height=600, engine="kaleido")
    st.download_button("Download PNG", img_bytes, file_name=f"{ticker}_timeline.png", mime="image/png")
except Exception:
    st.caption("Install **kaleido** for static image export: `pip install -U kaleido`. ")

st.caption(f"Prices from {start_date} to {end_date} · data via Yahoo Finance")
