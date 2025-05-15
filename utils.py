"""
Shared helpers – put in project root next to main.py
"""

import os
import sys
from datetime import date
from typing import Optional

import pandas as pd
import streamlit as st
import yfinance as yf


# --- make sure project root is import-able when pages run standalone ---
root_dir = os.path.abspath(os.path.dirname(__file__))
if root_dir not in sys.path:
    sys.path.append(root_dir)


@st.cache_data(ttl=60 * 60)   # cache one hour
def load_data(ticker: str, start: date, end: date) -> pd.DataFrame:
    """
    Robust download of historical OHLCV.

    1. Try yf.download()
    2. If empty, try yf.Ticker(...).history()
    3. Flatten MultiIndex columns
    4. Ensure an 'Adj Close' column exists (copy Close if missing)
    """
    if not ticker:
        return pd.DataFrame()

    try:
        df = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)
    except Exception as err:
        st.error(f"yfinance error while downloading {ticker}: {err}")
        return pd.DataFrame()

    # fallback if df empty (rare for some indices)
    if df.empty:
        try:
            df = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)
        except Exception as err:
            st.error(f"yfinance history() error for {ticker}: {err}")
            return pd.DataFrame()

    if df.empty:
        return df

    # flatten MultiIndex if present
    if isinstance(df.columns, pd.MultiIndex):
        if ticker in df.columns.get_level_values(1):
            df = df.xs(key=ticker, axis=1, level=1)
        else:
            df.columns = df.columns.droplevel(1)

    # guarantee an Adj Close
    if "Adj Close" not in df.columns and "Close" in df.columns:
        df["Adj Close"] = df["Close"]

    return df
