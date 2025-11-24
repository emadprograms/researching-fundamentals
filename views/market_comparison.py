import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import yfinance as yf
from utils import get_sp500_tickers, get_company_info

# Initialize session state for data if not present
if 'market_data' not in st.session_state:
    st.session_state['market_data'] = {}

def get_similar_companies(ticker, sp500_tickers, num_similar=10):
    """
    Finds companies similar to the given ticker based on industry descriptions.
    """
    try:
        target_info = get_company_info(ticker)
        if not target_info:
            st.error(f"Could not fetch info for {ticker}")
            return []

        target_industry = target_info.get('longBusinessSummary', "")

        if not target_industry:
            st.warning(f"No business summary found for {ticker}.")
            return []

        # Check if we have descriptions cached
        cached_descriptions = st.session_state['market_data'].get('descriptions', {})

        valid_tickers = [t for t in sp500_tickers if t in cached_descriptions]
        all_industries = [cached_descriptions[t] for t in valid_tickers]

        # Add target if not in list
        if ticker not in valid_tickers:
            all_industries.append(target_industry)
            valid_tickers.append(ticker)

        if len(all_industries) < 2:
            st.warning("Not enough market data to perform comparison. Please fetch more descriptions.")
            return []

        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(all_industries)

        # The target is the last one added (or we need to find its index)
        target_idx = len(all_industries) - 1

        similarity_scores = cosine_similarity(tfidf_matrix[target_idx], tfidf_matrix).flatten()

        # Get indices of top similar (excluding self)
        # Use min to avoid out of bounds if fewer than num_similar companies exist
        top_n = min(num_similar, len(all_industries) - 1)
        similar_indices = similarity_scores.argsort()[-(top_n+1):-1][::-1]

        similar_tickers = [valid_tickers[i] for i in similar_indices]

        return similar_tickers

    except Exception as e:
        st.error(f"An error occurred in similarity calculation: {e}")
        return []

def fetch_descriptions(tickers, progress_bar=None):
    """
    Fetches descriptions for a list of tickers.
    """
    descriptions = {}
    total = len(tickers)
    for i, ticker in enumerate(tickers):
        if progress_bar:
            progress_bar.progress((i + 1) / total, text=f"Fetching description for {ticker} ({i+1}/{total})")

        info = get_company_info(ticker)
        if info:
            desc = info.get('longBusinessSummary', "")
            if desc:
                descriptions[ticker] = desc
    return descriptions

def render_market_comparison():
    st.header("Market Comparison")
    st.write("Find similar companies based on business descriptions and compare their key financial metrics.")

    # Data Management Section
    with st.expander("Manage Data (S&P 500 Descriptions)"):
        st.write("To compare companies, we need to download business descriptions for the S&P 500. This is a one-time process per session.")

        sp500_tickers, error = get_sp500_tickers()
        if error:
            st.error(error)
            return

        col1, col2 = st.columns([2, 1])
        with col1:
             fetch_option = st.selectbox(
                 "Fetch Mode",
                 ["Fast (First 100 tickers)", "Complete (All 500+ tickers - Slow)"],
                 index=0
             )

        with col2:
            st.write("") # Spacer
            st.write("") # Spacer
            fetch_btn = st.button("Update/Fetch Market Data")

        if fetch_btn:
            if "Fast" in fetch_option:
                subset_tickers = sp500_tickers[:100]
                st.info(f"Fetching data for the first 100 tickers. This provides a quick sample but may miss relevant peers starting with later letters.")
            else:
                subset_tickers = sp500_tickers
                st.warning("Fetching data for all tickers. This may take several minutes.")

            progress_bar = st.progress(0, text="Starting download...")
            descriptions = fetch_descriptions(subset_tickers, progress_bar)
            st.session_state['market_data']['descriptions'] = descriptions
            st.success(f"Successfully fetched {len(descriptions)} company descriptions.")
            progress_bar.empty()

        # Display status
        cached_count = len(st.session_state['market_data'].get('descriptions', {}))
        if cached_count > 0:
            st.caption(f"Currently {cached_count} descriptions loaded in memory.")

    ticker = st.text_input("Enter Stock Ticker for Comparison (e.g., AVGO):", "AVGO").upper()

    if st.button("Compare"):
        if not sp500_tickers:
            st.error("S&P 500 list unavailable.")
            return

        # Check if we have data to compare against
        if 'descriptions' not in st.session_state['market_data'] or not st.session_state['market_data']['descriptions']:
             st.warning("Please fetch market data first using the section above.")
             return

        with st.spinner("Finding similar companies..."):
            similar_tickers = get_similar_companies(ticker, sp500_tickers)

        if similar_tickers:
            st.write(f"**Similar Companies found:** {', '.join(similar_tickers)}")

            all_tickers = [ticker] + similar_tickers

            # Fetch metrics
            data = []
            for t in all_tickers:
                info = get_company_info(t)
                if info:
                    eps = info.get('trailingEps')
                    pe = info.get('trailingPE')
                    revenue = info.get('totalRevenue')
                    shares = info.get('sharesOutstanding')
                    market_cap = info.get('marketCap')
                    name = info.get('shortName', t)

                    if all(v is not None for v in [eps, pe, revenue, shares, market_cap]):
                         data.append({
                            'Ticker': t,
                            'Name': name,
                            'EPS': eps,
                            'PE': pe,
                            'RPS': revenue / shares if shares else 0,
                            'PS': market_cap / revenue if revenue else 0,
                            'Earnings Yield': 1/pe if pe else 0,
                            'Revenue Yield': revenue/market_cap if market_cap else 0
                         })

            if data:
                df = pd.DataFrame(data)

                # Plotting
                st.subheader("Financial Metrics Comparison")

                col1, col2 = st.columns(2)

                with col1:
                    st.plotly_chart(px.bar(df, x="Ticker", y="EPS", title="EPS", hover_data=['Name']), use_container_width=True)
                    st.plotly_chart(px.bar(df, x="Ticker", y="Earnings Yield", title="Earnings Yield", hover_data=['Name']), use_container_width=True)
                    st.plotly_chart(px.bar(df, x="Ticker", y="RPS", title="Revenue Per Share", hover_data=['Name']), use_container_width=True)

                with col2:
                    st.plotly_chart(px.bar(df, x="Ticker", y="PE", title="P/E Ratio", hover_data=['Name']), use_container_width=True)
                    st.plotly_chart(px.bar(df, x="Ticker", y="PS", title="Price/Sales Ratio", hover_data=['Name']), use_container_width=True)
                    st.plotly_chart(px.bar(df, x="Ticker", y="Revenue Yield", title="Revenue Yield", hover_data=['Name']), use_container_width=True)

            else:
                st.warning("Could not fetch sufficient financial data for comparison.")
        else:
            st.warning("No similar companies found. Ensure you have fetched market data.")
