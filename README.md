# Stock Analysis Tool

A Streamlit application for analyzing company growth trends and comparing market performance against similar industry peers.

## Features

### 1. Company Growth Analysis
Visualizes the relationship between a company's Earnings Per Share (EPS) and Price-to-Earnings (P/E) Ratio over time.
- **Input:** Stock Ticker (e.g., AAPL), Start Date, End Date.
- **Output:** A combined chart showing EPS trends and P/E Ratio fluctuations.
- **Data Source:** Yahoo Finance.

### 2. Market Comparison
Finds companies similar to a target stock based on business descriptions and compares their key financial metrics.
- **Input:** Stock Ticker (e.g., AVGO).
- **Process:**
    1. Fetches S&P 500 company descriptions (User needs to click "Update/Fetch Market Data" once).
    2. Uses TF-IDF and Cosine Similarity to find similar companies.
- **Output:** Bar charts comparing EPS, P/E Ratio, Earnings Yield, Revenue Per Share (RPS), Price/Sales Ratio, and Revenue Yield.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```bash
    streamlit run Introduction.py
    ```

## Testing

To run the unit tests for the data utility functions:

```bash
python -m unittest tests/test_utils.py
```

## Structure

- `Introduction.py`: Main entry point of the application. Handles the UI layout and tabs.
- `utils.py`: Contains robust functions for fetching data from Yahoo Finance and Wikipedia, including error handling and caching.
- `views/`:
    - `company_growth.py`: Logic and UI for the Company Growth tab.
    - `market_comparison.py`: Logic and UI for the Market Comparison tab.
- `tests/`: Contains unit tests.

## Notes
- The application uses `yfinance` to fetch stock data. Ensure you have an active internet connection.
- "Adj Close" data is automatically handled even if the API returns a MultiIndex format.
- S&P 500 data is fetched from Wikipedia with proper User-Agent headers to avoid 403 errors.
