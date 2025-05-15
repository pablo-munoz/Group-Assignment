import streamlit as st

# Configure the main page (appears in browser tab and sidebar)
st.set_page_config(
    page_title="Financial Dashboard",
    page_icon="💹",           # Chart icon for the app
    layout="wide"            # Use wide layout for more space
)

# Main page content
st.title("📊 Financial Dashboard")
st.markdown("""
**Welcome to the Financial Dashboard!** This Streamlit app allows investors, analysts, and students to explore stocks, ETFs, and indices with interactive charts and metrics.

Use the sidebar to navigate between pages:
- **Stock Timeline:** Select a stock or index to view its price over time.
- **Key Metrics:** View calculated statistics (returns, volatility, drawdowns) for a selected asset.
- **Comparison Dashboard:** Compare performance of multiple tickers side-by-side.
- **Technical Analysis:** Analyze a stock with moving averages, RSI, and MACD indicators.
- **ETF & Index Explorer:** Explore common market indices and ETFs with price charts and highlights.
- **Chatbot Assistant:** Ask basic finance questions or get help navigating the app.

Each page is designed with a clean layout and cognitive principles in mind, showing information in manageable chunks. Select a page from the sidebar to get started!
""")
