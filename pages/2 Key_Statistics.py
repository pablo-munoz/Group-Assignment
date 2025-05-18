# File: pages/2_Key_Statistics.py
# --------------------------------------------------------------
# Key Performance Metrics
# --------------------------------------------------------------

from datetime import date, timedelta

import pandas as pd
import streamlit as st
import plotly.express as px
from utils import load_data

st.set_page_config(page_title="Key Statistics", page_icon="📊")
st.subheader("Key Performance Metrics")

# ── sidebar inputs ────────────────────────────────────────────
ticker = st.sidebar.text_input(
    "Ticker:", st.session_state.get("selected_ticker", "AAPL")
).strip().upper()
st.session_state.selected_ticker = ticker

today = date.today()
default_start = today - timedelta(days=365)

start_date = st.sidebar.date_input("Start Date", st.session_state.get("start_date", default_start))
end_date   = st.sidebar.date_input("End Date",   st.session_state.get("end_date", today))

if start_date > end_date:
    st.sidebar.error("Start date must be before end date")
    st.stop()

st.session_state.start_date = start_date
st.session_state.end_date   = end_date

# ── fetch data ────────────────────────────────────────────────
if not ticker:
    st.info("Enter a ticker to view metrics.")
    st.stop()

df = load_data(ticker, start_date, end_date)

if df.empty:
    st.warning("No data returned – check ticker or date range.")
    st.stop()

price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
prices    = df[price_col].dropna()
if prices.empty:
    st.warning("No price data available.")
    st.stop()

# ── compute metrics ───────────────────────────────────────────
total_return = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
daily_ret    = prices.pct_change().dropna()
annual_vol   = daily_ret.std() * (252 ** 0.5) * 100
drawdown     = (prices / prices.cummax() - 1) * 100
max_dd       = abs(drawdown.min())

# ── display ──────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("Return",      f"{total_return:.2f}%")
c2.metric("Volatility",  f"{annual_vol:.2f}%")
c3.metric("Max Drawdown",f"{max_dd:.2f}%")

metrics_df = (
    pd.DataFrame(
        {"Metric": ["Total Return (%)", "Annual Volatility (%)", "Max Drawdown (%)"],
         "Value":  [total_return,       annual_vol,              max_dd]}
    )
    .set_index("Metric")
    .round(2)
)

st.write(
    f"Summary for **{ticker}** ({start_date} → {end_date})",
    metrics_df
)
hist_fig = px.histogram(
    daily_ret * 100,
    nbins=40,
    title="Distribution of Daily Returns (%)",
    labels={"value": "Daily Return (%)"},
    opacity=0.75,
)
st.plotly_chart(hist_fig, use_container_width=True)

# ─── Explanations – cognitive redundancy ────────────────────
with st.expander("What do these numbers mean?", expanded=False):
    st.markdown(
        """
* **Return** – percentage gain/loss over the selected period.
* **Volatility** – annualised standard deviation of daily returns; higher ⇒ wider swings.
* **Max Drawdown** – worst peak-to-trough decline; proxy for tail-risk.
* **Sharpe Ratio** – excess return per unit of total volatility (> 1 is generally ‘good’).
* **Sortino Ratio** – like Sharpe but only penalises downside moves.
* **Beta** – sensitivity to S&P 500 (β=1 tracks the market, >1 is more volatile).
        """
    )
