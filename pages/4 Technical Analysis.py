# File: pages/4_Technical_Analysis.py
import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from utils import load_data
st.set_page_config(page_title="Technical Analysis", page_icon="💹")
st.subheader("Technical Analysis")

# Sidebar inputs: ticker and date range
ticker = st.sidebar.text_input("Ticker for Technical Analysis:", st.session_state.get("selected_ticker", ""))
ticker = ticker.strip().upper()
st.session_state.selected_ticker = ticker

import datetime
# Default 2 years of data for technical analysis
if "ta_start_date" not in st.session_state:
    st.session_state.ta_start_date = datetime.date.today() - datetime.timedelta(days=730)
if "ta_end_date" not in st.session_state:
    st.session_state.ta_end_date = datetime.date.today()

start_date = st.sidebar.date_input("Start Date:", st.session_state.ta_start_date)
end_date = st.sidebar.date_input("End Date:", st.session_state.ta_end_date)
if start_date > end_date:
    st.sidebar.error("Please select a valid date range.")
    st.stop()
st.session_state.ta_start_date = start_date
st.session_state.ta_end_date = end_date

if ticker:
    # Retrieve price data for the ticker
    df = load_data(ticker, start_date, end_date)
    if df is None or df.empty:
        st.error(f"No data for {ticker}.")
    else:
        prices = df['Adj Close'].copy()
        prices.index = pd.to_datetime(prices.index)  # ensure datetime index for plotting
        
        # --- Compute technical indicators ---
        # 1. Moving Averages (50-day and 200-day simple moving averages)
        ma_short = 50
        ma_long = 200
        df['SMA_50'] = prices.rolling(window=ma_short).mean()
        df['SMA_200'] = prices.rolling(window=ma_long).mean()
        
        # 2. RSI (Relative Strength Index, 14-day)
        def compute_rsi(series, window=14):
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        df['RSI'] = compute_rsi(prices, window=14)
        
        # 3. MACD (Moving Average Convergence Divergence)
        exp12 = prices.ewm(span=12, adjust=False).mean()
        exp26 = prices.ewm(span=26, adjust=False).mean()
        df['MACD'] = exp12 - exp26
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['Histogram'] = df['MACD'] - df['Signal']  # difference for MACD histogram

        # --- Create Charts ---
        # Price chart with moving averages
        price_fig = go.Figure()
        price_fig.add_trace(go.Scatter(x=prices.index, y=prices, mode='lines', name='Adj Close'))
        price_fig.add_trace(go.Scatter(x=prices.index, y=df['SMA_50'], mode='lines', name=f'{ma_short}-day SMA'))
        price_fig.add_trace(go.Scatter(x=prices.index, y=df['SMA_200'], mode='lines', name=f'{ma_long}-day SMA'))
        price_fig.update_layout(title=f"{ticker} Price with {ma_short} & {ma_long} Day MA",
                                yaxis_title="Price (USD)")

        # RSI chart
        rsi_fig = go.Figure()
        rsi_fig.add_trace(go.Scatter(x=prices.index, y=df['RSI'], mode='lines', name='RSI(14)'))
        # Add lines at 30 and 70 to indicate oversold/overbought thresholds
        rsi_fig.add_hline(y=30, line_dash="dot", line_color="green", annotation_text="Oversold (30)")
        rsi_fig.add_hline(y=70, line_dash="dot", line_color="red", annotation_text="Overbought (70)")
        rsi_fig.update_layout(title=f"{ticker} RSI (14-day)", yaxis_title="RSI")

        # MACD chart
        macd_fig = go.Figure()
        macd_fig.add_trace(go.Scatter(x=prices.index, y=df['MACD'], mode='lines', name='MACD'))
        macd_fig.add_trace(go.Scatter(x=prices.index, y=df['Signal'], mode='lines', name='Signal Line'))
        # MACD histogram as filled bar chart
        macd_fig.add_trace(go.Bar(x=prices.index, y=df['Histogram'], name='Histogram', marker_color='gray', opacity=0.5))
        macd_fig.update_layout(title=f"{ticker} MACD", yaxis_title="MACD")

        # --- Display Charts ---
        st.plotly_chart(price_fig, use_container_width=True)
        st.plotly_chart(rsi_fig, use_container_width=True)
        st.plotly_chart(macd_fig, use_container_width=True)
        st.caption(f"Technical indicators for {ticker} from {start_date} to {end_date}.")
else:
    st.info("👈 Enter a ticker to view technical analysis charts.")
