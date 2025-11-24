import yfinance as yf
import pandas as pd
import requests
import streamlit as st

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def get_stock_data(ticker, start_date, end_date):
    """
    Fetches stock data using yfinance.
    Handles MultiIndex columns and ensures 'Adj Close' or 'Close' is available.
    """
    try:
        # Fetch data with auto_adjust=False to get 'Adj Close' explicitly if possible,
        # or handle the default behavior.
        # However, to be robust, we'll ask for auto_adjust=False so we get 'Adj Close'.
        stock_data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False, progress=False)

        if stock_data.empty:
            return None, f"No data found for {ticker} within the specified date range."

        # Flatten MultiIndex columns if present
        if isinstance(stock_data.columns, pd.MultiIndex):
            # Drop the ticker level if it exists (usually level 1)
            stock_data.columns = stock_data.columns.droplevel(1)

        # yfinance might return 'Adj Close' or just 'Close' depending on versions/settings.
        # If 'Adj Close' is missing but 'Close' exists, we use 'Close' (assuming it might be adjusted if auto_adjust was True, but we set it to False).
        # Wait, if we set auto_adjust=False, we SHOULD get Adj Close.

        if "Adj Close" not in stock_data.columns:
            if "Close" in stock_data.columns:
                 # Fallback: create Adj Close from Close if it's missing (though strictly they are different)
                 # Or better, just alias it for the app's logic
                 stock_data['Adj Close'] = stock_data['Close']
            else:
                return None, f"'Adj Close' data not found for {ticker}."

        return stock_data, None

    except Exception as e:
        return None, f"An error occurred fetching data for {ticker}: {e}"

@st.cache_data(ttl=86400) # Cache for 24 hours
def get_sp500_tickers():
    """
    Fetches the list of S&P 500 tickers from Wikipedia.
    Uses a User-Agent header to avoid 403 Forbidden errors.
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse tables
        tables = pd.read_html(response.content)

        # The first table usually contains the S&P 500 list
        df = tables[0]

        # Ensure 'Symbol' column exists
        if 'Symbol' not in df.columns:
             return None, "Could not find 'Symbol' column in Wikipedia table."

        tickers = df['Symbol'].tolist()
        return tickers, None

    except Exception as e:
        return None, f"Error fetching S&P 500 list: {e}"

@st.cache_data(ttl=86400)
def get_company_info(ticker):
    """
    Fetches company info safely.
    """
    try:
        info = yf.Ticker(ticker).info
        return info
    except Exception as e:
        return None
