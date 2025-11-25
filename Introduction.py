import streamlit as st
from views.company_growth import render_company_growth
from views.market_comparison import render_market_comparison

st.set_page_config(
    page_title="Stock Analysis Tool",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling
st.markdown("""
<style>
    .small-title {
        font-size: 24px !important;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .small-text {
        font-size: 14px !important;
        color: #555;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Introduction Section
    st.markdown('<p class="small-title">Stock Analysis Tool</p>', unsafe_allow_html=True)
    st.markdown('<p class="small-text">A comprehensive tool for analyzing company growth trends and comparing market performance against similar industry peers.</p>', unsafe_allow_html=True)

    # Tabs for different segments
    tab1, tab2 = st.tabs(["Company Growth", "Market Comparison"])

    with tab1:
        render_company_growth()

    with tab2:
        render_market_comparison()

if __name__ == "__main__":
    main()
