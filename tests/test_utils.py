import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import streamlit as st
from utils import get_stock_data, get_sp500_tickers

class TestUtils(unittest.TestCase):

    def setUp(self):
        # Clear cache before each test to ensure mocks are called
        get_stock_data.clear()
        get_sp500_tickers.clear()

    @patch('utils.yf.download')
    def test_get_stock_data_success_flat(self, mock_download):
        # Scenario 1: Flat columns with 'Adj Close'
        data = {
            'Open': [100, 101],
            'Close': [102, 103],
            'Adj Close': [102, 103]
        }
        df = pd.DataFrame(data, index=pd.to_datetime(['2023-01-01', '2023-01-02']))
        mock_download.return_value = df

        result_df, error = get_stock_data("AAPL", "2023-01-01", "2023-01-02")

        self.assertIsNone(error)
        self.assertIsNotNone(result_df)
        self.assertIn('Adj Close', result_df.columns)

    @patch('utils.yf.download')
    def test_get_stock_data_success_multiindex(self, mock_download):
        # Scenario 2: MultiIndex columns (new yfinance default)
        # Columns: (Price, Ticker)
        arrays = [
            ['Open', 'Close', 'Adj Close'],
            ['AAPL', 'AAPL', 'AAPL']
        ]
        tuples = list(zip(*arrays))
        index = pd.MultiIndex.from_tuples(tuples, names=['Price', 'Ticker'])

        df = pd.DataFrame([[100, 102, 102]], index=pd.to_datetime(['2023-01-01']), columns=index)
        mock_download.return_value = df

        result_df, error = get_stock_data("AAPL", "2023-01-01", "2023-01-02")

        self.assertIsNone(error)
        # The function should flatten the index
        self.assertIsInstance(result_df.columns, pd.Index)
        self.assertNotIsInstance(result_df.columns, pd.MultiIndex)
        self.assertIn('Adj Close', result_df.columns)

    @patch('utils.yf.download')
    def test_get_stock_data_empty(self, mock_download):
        mock_download.return_value = pd.DataFrame()
        result_df, error = get_stock_data("AAPL", "2023-01-01", "2023-01-02")
        self.assertIsNone(result_df)
        self.assertIn("No data found", error)

    @patch('utils.requests.get')
    def test_get_sp500_tickers_success(self, mock_get):
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Create a dummy HTML table
        html_table = """
        <table>
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Security</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>AAPL</td>
                    <td>Apple Inc.</td>
                </tr>
                <tr>
                    <td>MSFT</td>
                    <td>Microsoft Corp.</td>
                </tr>
            </tbody>
        </table>
        """
        mock_response.content = html_table
        mock_get.return_value = mock_response

        tickers, error = get_sp500_tickers()

        self.assertIsNone(error)
        self.assertEqual(tickers, ['AAPL', 'MSFT'])
        # Verify headers were used
        args, kwargs = mock_get.call_args
        self.assertIn('User-Agent', kwargs['headers'])

    @patch('utils.requests.get')
    def test_get_sp500_tickers_failure(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        tickers, error = get_sp500_tickers()
        self.assertIsNone(tickers)
        self.assertIn("Error fetching S&P 500 list", error)

if __name__ == '__main__':
    unittest.main()
