import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

def visualize_eps_pe_plotly(ticker, start_date, end_date):
    """
    Visualizes the relationship between EPS and P/E ratio for a given stock using Plotly.
    """
    try:
        stock_data = yf.download(ticker, start=start_date, end=end_date)
        if stock_data.empty:
            st.error(f"No data found for {ticker} within the specified date range.")
            return None

        if "Adj Close" not in stock_data.columns:
            st.error(f"'Adj Close' data not found for {ticker}. Check ticker or date range.")
            st.write(stock_data)
            return None

        if stock_data['Adj Close'].isnull().values.any():
            st.error("Adj Close column contains NaN values")
            st.write(stock_data)
            return None

        if not isinstance(stock_data['Adj Close'], pd.Series):
            st.error("Adj Close is not a pandas series.")
            st.write(stock_data)
            return None

        stock = yf.Ticker(ticker)
        income_stmt = stock.income_stmt
        if income_stmt.empty:
            st.error(f"Income statement data not available for {ticker}.")
            return None

        net_income = income_stmt.loc['Net Income'].transpose()
        shares_outstanding = stock.info.get('sharesOutstanding')

        if shares_outstanding is None:
          st.error("Shares outstanding data not available.")
          return None

        eps_values = net_income / shares_outstanding
        eps_values.index = pd.to_datetime(eps_values.index)

        stock_data['PE_Ratio'] = stock_data['Adj Close'] / eps_values.reindex(stock_data.index, method='ffill')

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=eps_values.index, y=eps_values, name='EPS', yaxis='y1'))
        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['PE_Ratio'], name='P/E Ratio', yaxis='y2'))
        fig.update_layout(
            title=f'{ticker} EPS and P/E Ratio',
            xaxis=dict(title='Date'),
            yaxis=dict(title='EPS', side='left', color='blue'),
            yaxis2=dict(title='P/E Ratio', side='right', overlaying='y', color='red'),
            legend=dict(x=0, y=1, traceorder='normal')
        )
        return fig

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

def main():
    st.title("EPS and P/E Ratio Visualization")
    ticker = st.text_input("Enter Stock Ticker Symbol (e.g., JNPR):", "AAPL").upper()
    start_date = st.date_input("Start Date", value=pd.to_datetime("2020-01-01"))
    end_date = st.date_input("End Date", value=pd.to_datetime("today"))
    if st.button("Visualize"):
        fig = visualize_eps_pe_plotly(ticker, start_date, end_date)
        if fig:
            st.plotly_chart(fig)

if __name__ == "__main__":
    main()