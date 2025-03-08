import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import os

st.set_page_config(layout="wide")

DATA_FILE = "market_data.pkl"

@st.cache_data
def load_data():
    """Loads data from pickle file if it exists, otherwise returns data."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "rb") as f:
            data = pickle.load(f)
            return data
    return None

def fetch_and_save_data():
    """Fetches S&P 500 list and company descriptions and saves to pickle file."""
    try:
        sp500_tickers = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]['Symbol'].tolist()
        company_descriptions = {}
        for ticker in sp500_tickers:
            try:
                info = yf.Ticker(ticker).info
                company_descriptions[ticker] = info.get('longBusinessSummary', "")
            except Exception as e:
                print(f"Error fetching description for {ticker}: {e}")

        data = {"sp500_tickers": sp500_tickers, "company_descriptions": company_descriptions}
        with open(DATA_FILE, "wb") as f:
            pickle.dump(data, f)
        st.success("Data updated successfully!")
        return data
    except Exception as e:
        st.error(f"Error fetching and saving data: {e}")
        return None

# Initialize session state
if 'data' not in st.session_state:
    st.session_state['data'] = load_data()

if st.button("Update Data"):
    st.session_state['data'] = fetch_and_save_data()

if st.session_state['data'] is None:
    sp500_tickers = []
    company_descriptions = {}
    st.warning("No data found. Please update the data by clicking the 'Update Data' button.")
else:
    sp500_tickers = st.session_state['data']["sp500_tickers"]
    company_descriptions = st.session_state['data']["company_descriptions"]


def get_similar_companies(ticker, num_similar=10):
    """
    Finds companies similar to the given ticker based on industry descriptions.
    """
    try:
        target_info = yf.Ticker(ticker).info #yf.Ticker(ticker).info
        target_industry = target_info.get('longBusinessSummary', "") #target_info.get('longBusinessSummary', "")

        if not target_industry:
          return []

        #all_tickers = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]['Symbol'].tolist() #A simple way to get a list of tickers, you may need to adjust this to your needs.
        all_tickers = sp500_tickers
        all_industries = []
        valid_tickers = []

        for t in all_tickers:
            try:
                #info = yf.Ticker(t).info
                #industry = info.get('longBusinessSummary', "")
                industry = company_descriptions.get(t, "")
                if industry:
                    all_industries.append(industry)
                    valid_tickers.append(t)
            except Exception as e:
                print(f"Error fetching info for {t}: {e}")

        if not all_industries:
          return []

        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(all_industries + [target_industry])

        similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()

        similar_indices = similarity_scores.argsort()[-num_similar:][::-1]

        similar_tickers = [valid_tickers[i] for i in similar_indices]

        return similar_tickers

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return []

@st.cache_data
def get_eps_pe(tickers):
    """
    Fetches EPS and P/E data for the given tickers.
    """
    data = []
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            eps = info.get('trailingEps', None)
            pe = info.get('trailingPE', None)
            name = f"{info.get('shortName', ticker)} ({ticker})"
            if eps is not None and pe is not None:
                earnings_yield = 1 / pe if pe != 0 else None
                data.append({'Ticker': ticker, 'EPS': eps, 'PE': pe, 'Earnings Yield': earnings_yield, 'Name': name})
        except Exception as e:
            st.warning(f"Could not fetch EPS/PE for {ticker}: {e}")
    return pd.DataFrame(data)

st.title("Company Comparison")

ticker = st.text_input("Enter Stock Ticker (e.g., AVGO):", "AVGO").upper()

if st.button("Get Similar Companies and Plot"):
    similar_tickers = get_similar_companies(ticker)

    if similar_tickers:
        all_tickers = [ticker] + similar_tickers
        df = get_eps_pe(all_tickers)

        if not df.empty:
            col1, col2 = st.columns([1, 2])  # col1 takes 1/3, col2 takes 2/3 of the width
            with col1:
                fig_eps = px.bar(df, x="Name", y="EPS", title="EPS Comparison")
                st.plotly_chart(fig_eps, use_container_width=True)

                fig_pe = px.bar(df, x="Name", y="PE", title="PE Ratio Comparison")
                st.plotly_chart(fig_pe, use_container_width=True)

                fig_ey = px.bar(df, x="Name", y="Earnings Yield", title="Earnings Yield Comparison")
                st.plotly_chart(fig_ey, use_container_width=True)
        else:
            st.warning("Could not retrieve EPS/PE data for the selected companies.")
    else:
        st.warning("Could not find similar companies or retrieve company descriptions.")