import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

def get_similar_companies(ticker, num_similar=10):
    """
    Finds companies similar to the given ticker based on industry descriptions.
    """
    try:
        target_info = yf.Ticker(ticker).info
        target_industry = target_info.get('longBusinessSummary', "")

        if not target_industry:
          return []

        all_tickers = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]['Symbol'].tolist() #A simple way to get a list of tickers, you may need to adjust this to your needs.
        all_industries = []
        valid_tickers = []

        for t in all_tickers:
            try:
                info = yf.Ticker(t).info
                industry = info.get('longBusinessSummary', "")
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
            name = info.get('shortName', ticker)
            if eps is not None and pe is not None:
                data.append({'Ticker': ticker, 'EPS': eps, 'PE': pe, 'Name': name})
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
            fig_eps = px.bar(df, x="Name", y="EPS", title="EPS Comparison")
            fig_pe = px.bar(df, x="Name", y="PE", title="PE Ratio Comparison")

            st.plotly_chart(fig_eps)
            st.plotly_chart(fig_pe)
        else:
            st.warning("Could not retrieve EPS/PE data for the selected companies.")
    else:
        st.warning("Could not find similar companies or retrieve company descriptions.")