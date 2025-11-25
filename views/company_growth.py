import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from utils import get_stock_data, get_company_info

def render_company_growth():
    st.header("Company Growth Analysis")
    st.write("Visualize the relationship between EPS (Earnings Per Share) and P/E (Price-to-Earnings) Ratio over time.")

    ticker = st.text_input("Enter Stock Ticker Symbol (e.g., JNPR):", "AAPL").upper()
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=pd.to_datetime("2020-01-01"))
    with col2:
        end_date = st.date_input("End Date", value=pd.to_datetime("today"))

    if st.button("Visualize Growth"):
        with st.spinner(f"Fetching data for {ticker}..."):
            stock_data, error = get_stock_data(ticker, start_date, end_date)

            if error:
                st.error(error)
                return

            # Fetch extra info for calculation
            stock = yf.Ticker(ticker)
            income_stmt = stock.income_stmt

            if income_stmt.empty:
                st.warning(f"Income statement data not available for {ticker}. Cannot calculate EPS.")
                return

            try:
                # Transpose to get dates as index
                net_income = income_stmt.loc['Net Income'].transpose()

                # Get shares outstanding
                info = get_company_info(ticker)
                if not info:
                    st.error("Could not fetch company info.")
                    return

                shares_outstanding = info.get('sharesOutstanding')

                if not shares_outstanding:
                    st.error("Shares outstanding data not available.")
                    return

                # Calculate EPS
                eps_values = net_income / shares_outstanding
                eps_values.index = pd.to_datetime(eps_values.index)

                # Sort index to ensure correct plotting
                eps_values = eps_values.sort_index()

                # Calculate PE Ratio
                # Align stock data with EPS dates or reindex EPS to stock data
                # Reindexing EPS to match stock data (daily) using ffill

                # Ensure stock_data index is datetime
                stock_data.index = pd.to_datetime(stock_data.index)

                # Create a combined dataframe for easier plotting/calculation
                # We need to broadcast the quarterly/annual EPS to daily for the PE calculation
                eps_series = eps_values.reindex(stock_data.index, method='ffill')

                stock_data['PE_Ratio'] = stock_data['Adj Close'] / eps_series

                # Create Plot
                fig = go.Figure()

                # Plot EPS (Scatter/Line) - Filter out NaNs for cleaner plot
                eps_clean = eps_values.dropna()
                fig.add_trace(go.Scatter(
                    x=eps_clean.index,
                    y=eps_clean,
                    name='EPS',
                    mode='lines+markers',
                    yaxis='y1'
                ))

                # Plot PE Ratio
                fig.add_trace(go.Scatter(
                    x=stock_data.index,
                    y=stock_data['PE_Ratio'],
                    name='P/E Ratio',
                    yaxis='y2',
                    line=dict(color='red')
                ))

                fig.update_layout(
                    title=f'{ticker} EPS and P/E Ratio',
                    xaxis=dict(title='Date'),
                    yaxis=dict(title='EPS', side='left', showgrid=False),
                    yaxis2=dict(title='P/E Ratio', side='right', overlaying='y', showgrid=False),
                    legend=dict(x=0, y=1.1, orientation='h'),
                    hovermode='x unified'
                )

                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"An error occurred during calculation: {e}")
