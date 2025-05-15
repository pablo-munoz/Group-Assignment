# File: pages/3_Comparison_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils import load_data

st.set_page_config(page_title="Comparison Dashboard", page_icon="🔎")
st.subheader("Comparison Dashboard")

# Sidebar inputs
tickers_input = st.sidebar.text_input(
    "Enter multiple tickers (comma-separated):", 
    value="AAPL, MSFT, GOOGL"
)
tickers = [t.strip().upper() for t in tickers_input.replace(";", ",").split(",") if t.strip()]
# Remove duplicate or empty entries
tickers = sorted(set(filter(None, tickers)))
if len(tickers) == 0:
    st.info("Enter at least one ticker symbol to compare.")
    st.stop()
if len(tickers) > 5:
    st.sidebar.warning("Limiting to first 5 tickers for clarity.")
    tickers = tickers[:5]

# Date range selection (default 1 year)
today = datetime.today().date()
default_start = today - timedelta(days=365)
start_date = st.sidebar.date_input("Start Date:", default_start)
end_date = st.sidebar.date_input("End Date:", today)
if start_date > end_date:
    st.sidebar.error("Start date must be before end date.")
    st.stop()

# Fetch data for each ticker and combine
combined_df = pd.DataFrame()
for t in tickers:
    try:
        df = load_data(t, start_date, end_date)  # cached data fetch
    except Exception:
        st.error(f"Error fetching data for {t}.")
        st.stop()
    if df.empty:
        st.warning(f"No data for {t} - skipping.")
        continue
    df['Ticker'] = t
    df['Adj Close'] = df['Adj Close'].astype(float)
    combined_df = pd.concat([combined_df, df[['Adj Close', 'Ticker']]])

if combined_df.empty:
    st.warning("No data available to compare with the given inputs.")
    st.stop()

# Create a normalized price column for comparison (percentage or indexed to 100)
# For each ticker, normalize prices to start at 100
combined_df = combined_df.reset_index()
combined_df.rename(columns={'index': 'Date'}, inplace=True)
# Get start prices for each ticker
start_prices = combined_df.groupby('Ticker').first()['Adj Close']
combined_df['Normalized'] = combined_df.apply(lambda row: row['Adj Close'] / start_prices[row['Ticker']] * 100, axis=1)

# Line chart of normalized performance
fig = px.line(
    combined_df, 
    x="Date", 
    y="Normalized", 
    color="Ticker",
    title="Normalized Performance Comparison",
    labels={"Normalized": "Indexed Price (Start = 100)", "Date": "Date"}
)
fig.update_layout(legend_title_text="Ticker")
st.plotly_chart(fig, use_container_width=True)

# Calculate final return and volatility for each ticker
comparison_metrics = []
for t in tickers:
    df_t = combined_df[combined_df['Ticker'] == t]
    if df_t.empty: 
        continue
    start_val = df_t['Adj Close'].iloc[0]
    end_val = df_t['Adj Close'].iloc[-1]
    total_ret = (end_val / start_val - 1) * 100
    # Compute volatility (daily std dev annualized) on that ticker's series
    prices = df_t.sort_values("Date")['Adj Close']
    daily_ret = prices.pct_change().dropna()
    vol = daily_ret.std() * (252 ** 0.5) * 100
    comparison_metrics.append([t, f"{total_ret:.2f}%", f"{vol:.2f}%"])

if comparison_metrics:
    comp_df = pd.DataFrame(comparison_metrics, columns=["Ticker", "Total Return (%)", "Annual Volatility (%)"])
    comp_df.set_index("Ticker", inplace=True)
    st.write("**Comparison Metrics:**", comp_df)
