# File: pages/6_Chatbot.py
import streamlit as st

st.set_page_config(page_title="Chatbot Assistant", page_icon="💬")
st.title("💬 Finance Chatbot Assistant")

st.write("Ask any basic finance question or ask for help with the dashboard. The assistant can explain terms or guide you to the right page.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display existing chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input widget
user_input = st.chat_input("Type your question here...")  # waits for user to submit
if user_input:
    # Append user's message to history and display it
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate a response based on simple keyword matching
    query = user_input.lower()
    response = ""
    if "volat" in query:
        response = ("Volatility refers to how much an asset's price fluctuates over time. "
                    "Higher volatility means larger price swings, indicating higher risk.")
    elif "drawdown" in query:
        response = ("Drawdown is the percentage drop from a peak to a subsequent low. "
                    "A max drawdown tells you the worst loss from a high point during a period.")
    elif "return" in query and "year" in query:
        response = ("Return typically means how much an investment has gained or lost, usually expressed as a percentage. "
                    "For example, a 10% annual return means the investment grew by 10% in one year.")
    elif "moving average" in query or "ma" in query:
        response = ("A moving average is the average price of an asset over a specific number of past days. "
                    "It's used to smooth out short-term fluctuations and highlight longer-term trends.")
    elif "rsi" in query or "relative strength index" in query:
        response = ("The Relative Strength Index (RSI) is a momentum indicator that ranges from 0 to 100. "
                    "Values above 70 suggest an asset might be overbought, while below 30 suggests it might be oversold.")
    elif "macd" in query:
        response = ("MACD (Moving Average Convergence Divergence) is a trend-following indicator. "
                    "It shows the difference between a short-term and a long-term exponential moving average and helps identify trend changes.")
    elif "etf" in query:
        response = ("An ETF (Exchange-Traded Fund) is a basket of securities that trades on an exchange like a stock. "
                    "ETFs often track an index (like SPY tracks the S&P 500) and allow easy diversification.")
    elif "compare" in query or "comparison" in query:
        response = ("To compare multiple assets, go to the **Comparison Dashboard** page. "
                    "There, you can enter multiple ticker symbols and see their performance side by side.")
    elif "technical" in query or "indicator" in query:
        response = ("The **Technical Analysis** page shows technical indicators for a chosen stock (moving averages, RSI, MACD). "
                    "Go to that page from the sidebar, enter a ticker, and you'll see those charts.")
    elif "metric" in query or "volatility" in query or "drawdown" in query:
        response = ("On the **Key Statistics** page, you can find metrics like volatility, drawdown, and total return for the selected asset. "
                    "Just select a stock or ETF and the dashboard will calculate those for you.")
    else:
        response = ("I'm not sure about that. I can help with definitions of finance terms (e.g., volatility, RSI) or how to use the dashboard pages.")
    # Append assistant response to history and display it
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)

# Clear chat history button
if st.sidebar.button("Clear Chat History"):
    st.session_state.messages = []
    st.experimental_rerun()
