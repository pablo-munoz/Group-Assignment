# File: pages/3_Comparison_Dashboard.py
# --------------------------------------------------------------
# Enhanced Comparison Dashboard (Iteration 2 — trimmed imports)
# --------------------------------------------------------------
"""
Compare multiple assets across performance and risk dimensions.
Adds risk‑return scatter, optional log‑scale, correlation heat‑map and
consistent colour mapping for cognitive continuity.
Only uses libraries listed in *requirements.txt* (streamlit, yfinance,
plotly, pandas, numpy).
"""

from datetime import date, timedelta
import math

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

from utils import load_data  # shared, cached data fetcher

# ─── Page config & header ─────────────────────────────────────
st.set_page_config(page_title="Comparison Dashboard", page_icon="🔎")
st.subheader("Comparison Dashboard")

# ─── Sidebar inputs ──────────────────────────────────────────
_get_state = lambda k, d: st.session_state.get(k, d)

tickers_input = st.sidebar.text_input(
    "Enter multiple tickers (comma-separated):",
    value=_get_state("tickers_input", "AAPL, MSFT, GOOGL"),
)
st.session_state.tickers_input = tickers_input

raw_list = [t.strip().upper() for t in tickers_input.replace(";", ",").split(",") if t.strip()]
tickers = sorted(set(raw_list))

if not tickers:
    st.info("Enter at least one ticker to compare.")
    st.stop()

MAX_TICKERS = 5
if len(tickers) > MAX_TICKERS:
    st.sidebar.warning(f"Showing first {MAX_TICKERS} tickers for clarity.")
    tickers = tickers[:MAX_TICKERS]

# Date range (default 1‑year)
today = date.today()
def_start = today - timedelta(days=365)
start_date = st.sidebar.date_input("Start Date:", _get_state("start_date", def_start))
end_date = st.sidebar.date_input("End Date:", _get_state("end_date", today))

if start_date > end_date:
    st.sidebar.error("Start date must be before end date.")
    st.stop()

st.session_state.start_date = start_date
st.session_state.end_date = end_date

log_scale = st.sidebar.checkbox("Log scale on performance chart", value=False)

# ─── Global colour map (persistent) ──────────────────────────
if "colour_map" not in st.session_state:
    st.session_state.colour_map = {}
colour_map: dict[str, str] = st.session_state.colour_map
palette = px.colors.qualitative.Plotly

for t in tickers:
    if t not in colour_map:
        colour_map[t] = palette[len(colour_map) % len(palette)]

# ─── Fetch & combine data ────────────────────────────────────
frames: list[pd.DataFrame] = []
market_caps: dict[str, float | None] = {}

with st.spinner("Fetching data …"):
    for t in tickers:
        df = load_data(t, start_date, end_date)
        if df is None or df.empty:
            st.warning(f"No data for {t} – skipping.")
            continue

        price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
        tmp = (
            df[[price_col]]
            .rename(columns={price_col: "Price"})
            .dropna()
            .assign(Ticker=t)
            .reset_index()
            .rename(columns={"index": "Date"})
        )
        frames.append(tmp)

        # Market‑cap info (optional)
        try:
            info = yf.Ticker(t).info
            market_caps[t] = info.get("marketCap")
        except Exception:
            market_caps[t] = None

if not frames:
    st.error("No data available for the selected tickers/date range.")
    st.stop()

combined_df = pd.concat(frames, ignore_index=True)
combined_df["Date"] = pd.to_datetime(combined_df["Date"])  # ensure datetime

# ─── Normalise so all series start at 100 ─────────────────────
start_prices = (
    combined_df.sort_values("Date").groupby("Ticker")["Price"].first().to_dict()
)

combined_df["Indexed"] = combined_df.apply(
    lambda r: r["Price"] / start_prices[r["Ticker"]] * 100, axis=1
)

# ─── Chart: Normalised performance ───────────────────────────
line_fig = px.line(
    combined_df,
    x="Date",
    y="Indexed",
    color="Ticker",
    title="Normalised Performance (Start = 100)",
    labels={"Indexed": "Indexed Price", "Date": "Date"},
    color_discrete_map=colour_map,
)
line_fig.update_layout(legend_title_text="Ticker")
if log_scale:
    line_fig.update_yaxes(type="log")

st.plotly_chart(line_fig, use_container_width=True)

# ─── Summary metrics table ───────────────────────────────────
summary: list[dict[str, float]] = []
for t in tickers:
    subset = combined_df[combined_df["Ticker"] == t].sort_values("Date")
    if subset.empty:
        continue
    price_series = subset["Price"]
    total_ret = (price_series.iloc[-1] / price_series.iloc[0] - 1) * 100
    daily_ret = price_series.pct_change().dropna()
    vol = daily_ret.std() * math.sqrt(252) * 100  # annualised %
    summary.append(
        {
            "Ticker": t,
            "Total Return (%)": round(total_ret, 2),
            "Annual Volatility (%)": round(vol, 2),
            "MarketCap": market_caps.get(t),
        }
    )

summary_df = pd.DataFrame(summary).set_index("Ticker")

st.write("### Comparison Metrics")
st.dataframe(summary_df)

# ─── Risk‑Return scatter plot ────────────────────────────────
if not summary_df.empty:
    scatter_fig = px.scatter(
        summary_df.reset_index(),
        x="Annual Volatility (%)",
        y="Total Return (%)",
        size="MarketCap",
        color="Ticker",
        hover_name="Ticker",
        size_max=60,
        title="Risk‑Return (Bubble ~ Market Cap)",
        color_discrete_map=colour_map,
    )
    st.plotly_chart(scatter_fig, use_container_width=True)

# ─── Correlation heat‑map of returns ─────────────────────────
with st.expander("Correlation Matrix", expanded=False):
    # Build return matrix
    ret_frames: list[pd.Series] = []
    for t in tickers:
        px_sub = combined_df[combined_df["Ticker"] == t].set_index("Date")["Price"]
        ret_frames.append(px_sub.pct_change().rename(t))

    ret_df = pd.concat(ret_frames, axis=1).dropna(how="all")
    if ret_df.shape[1] >= 2:
        corr = ret_df.corr()
        heat = px.imshow(
            corr,
            text_auto=".2f",
            color_continuous_scale="RdBu",
            zmin=-1,
            zmax=1,
            title="Return Correlation Matrix",
        )
        st.plotly_chart(heat, use_container_width=True)
    else:
        st.info("Not enough overlapping data to compute correlations.")
