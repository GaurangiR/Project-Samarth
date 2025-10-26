"""
Project Samarth - Intelligent Q&A System for Indian Agricultural Economy
Main Streamlit Application

Author: BTech Engineering Candidate
Purpose: Challenge Submission - Live Data Integration from data.gov.in
"""

import sys
import streamlit as st

from pathlib import Path
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

sys.path.append('.')
from src.query_engine import QueryEngine
from src.data_fetcher import DataFetcher
from src.config import Config

# Page configuration
st.set_page_config(
    page_title="Project Samarth - Agricultural Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .source-citation {
        background-color: #f0f2f6;
        border-left: 4px solid #2E7D32;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'query_engine' not in st.session_state:
    st.session_state.query_engine = QueryEngine()
    st.session_state.data_fetcher = DataFetcher()
    st.session_state.history = []

# Header
st.markdown('<div class="main-header">🌾 Project Samarth</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Intelligent Q&A System for Indian Agricultural Economy & Climate Data</div>',
    unsafe_allow_html=True
)

# Sidebar
with st.sidebar:
    st.header("⚙️ System Configuration")
    
    # API Status Check
    st.subheader("📡 API Connection Status")
    
    if st.button("Check API Status", use_container_width=True):
        with st.spinner("Checking connections..."):
            status = st.session_state.data_fetcher.check_api_status()
            for api, is_ok in status.items():
                if is_ok:
                    st.success(f"✅ {api}")
                else:
                    st.error(f"❌ {api}")
    
    st.divider()
    
    # Data Sources
    st.subheader("📊 Data Sources")
    st.info("""
    **Primary Sources:**
    - India Meteorological Department (IMD)
    - Ministry of Agriculture & Farmers Welfare
    - data.gov.in Open Data Platform
    """)
    
    st.divider()
    
    # Sample Queries
    st.subheader("💡 Sample Queries")
    sample_queries = [
        "Compare rainfall in Punjab and Haryana for last 5 years",
        "Top 3 crops produced in Maharashtra",
        "Rice production trend in West Bengal 2015-2020",
        "District with highest wheat production in UP"
    ]
    
    selected_sample = st.selectbox(
        "Try a sample query:",
        [""] + sample_queries,
        index=0
    )
    
    if selected_sample:
        st.session_state.sample_query = selected_sample

# Main content area
tab1, tab2, tab3 = st.tabs(["🔍 Query Interface", "📈 Analytics Dashboard", "📚 Documentation"])

with tab1:
    st.header("Ask Your Question")
    
    # Query input
    query_text = st.text_area(
        "Enter your question about Indian agriculture or climate:",
        value=st.session_state.get('sample_query', ''),
        height=100,
        placeholder="E.g., Compare the average annual rainfall in Punjab and Haryana for the last 5 years and list the top 3 most produced crops in those states"
    )
    
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        submit_button = st.button("🚀 Submit Query", type="primary", use_container_width=True)
    
    with col2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)
    
    if clear_button:
        st.session_state.sample_query = ""
        st.rerun()
    
    # Process query
    if submit_button and query_text:
        with st.spinner("🔄 Processing your query... Fetching live data from data.gov.in APIs..."):
            try:
                result = st.session_state.query_engine.process_query(query_text)
                
                # Add to history
                st.session_state.history.append({
                    'timestamp': datetime.now().isoformat(),
                    'query': query_text,
                    'result': result
                })
                
                # Display results
                st.success("✅ Query processed successfully!")
                
                # Answer section
                st.subheader("📝 Answer")
                st.markdown(result['answer'])
                
                # Data section
                if result.get('data'):
                    st.subheader("📊 Retrieved Data")
                    
                    for dataset_name, dataset_info in result['data'].items():
                        with st.expander(f"📁 {dataset_name}", expanded=True):
                            if isinstance(dataset_info, dict) and 'dataframe' in dataset_info:
                                st.dataframe(
                                    dataset_info['dataframe'],
                                    use_container_width=True
                                )
                            else:
                                st.json(dataset_info)
                
                # Visualizations
                if result.get('visualizations'):
                    st.subheader("📈 Visualizations")
                    for viz in result['visualizations']:
                        st.plotly_chart(viz, use_container_width=True)
                
                # Citations
                if result.get('sources'):
                    st.subheader("📚 Data Sources & Citations")
                    for idx, source in enumerate(result['sources'], 1):
                        st.markdown(f"""
                        <div class="source-citation">
                            <strong>Source {idx}:</strong> {source['name']}<br>
                            <strong>Endpoint:</strong> <code>{source['endpoint']}</code><br>
                            <strong>Accessed:</strong> {source['timestamp']}<br>
                            <strong>Parameters:</strong> {json.dumps(source.get('parameters', {}), indent=2)}
                        </div>
                        """, unsafe_allow_html=True)
                
                # Confidence & Metadata
                with st.expander("ℹ️ Query Metadata"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Confidence", f"{result.get('confidence', 0):.1%}")
                    with col2:
                        st.metric("Processing Time", f"{result.get('processing_time', 0):.2f}s")
                    with col3:
                        st.metric("Data Points", result.get('data_points', 0))
                
            except Exception as e:
                st.error(f"❌ Error processing query: {str(e)}")
                st.exception(e)

with tab2:
    st.header("Analytics Dashboard")
    
    if st.session_state.history:
        st.subheader("📊 Query Statistics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Queries", len(st.session_state.history))
        with col2:
            avg_time = sum(q['result'].get('processing_time', 0) for q in st.session_state.history) / len(st.session_state.history)
            st.metric("Avg Processing Time", f"{avg_time:.2f}s")
        with col3:
            total_sources = sum(len(q['result'].get('sources', [])) for q in st.session_state.history)
            st.metric("Data Sources Used", total_sources)
        
        st.subheader("🕒 Query History")
        for idx, item in enumerate(reversed(st.session_state.history[-10:]), 1):
            with st.expander(f"Query {len(st.session_state.history) - idx + 1}: {item['query'][:50]}..."):
                st.write(f"**Time:** {item['timestamp']}")
                st.write(f"**Answer:** {item['result']['answer'][:200]}...")
    else:
        st.info("No queries submitted yet. Try asking a question in the Query Interface tab!")

with tab3:
    st.header("Documentation")
    
    st.markdown("""
    ## 🎯 About Project Samarth
    
    Project Samarth is an intelligent Q&A system that provides real-time insights into India's agricultural 
    economy and climate patterns using live data from data.gov.in APIs.
    
    ### 🏗️ System Architecture
    
    **1. Data Ingestion Layer**
    - Connects to IMD (India Meteorological Department) APIs
    - Fetches data from Ministry of Agriculture & Farmers Welfare
    - Implements intelligent caching to minimize API calls
    - Handles rate limiting and connection failures gracefully
    
    **2. Data Processing Layer**
    - Normalizes heterogeneous datasets (different formats, units, coding schemes)
    - Cleans and validates data for accuracy
    - Maintains data lineage for full traceability
    
    **3. Query Intelligence Layer**
    - Natural Language Processing using spaCy
    - Entity recognition (states, crops, districts, years)
    - Intent classification (comparison, ranking, trend analysis)
    - Multi-step query decomposition
    
    **4. Analytics Engine**
    - Statistical analysis and aggregations
    - Trend detection and forecasting
    - Correlation analysis between climate and agriculture
    - Policy recommendation engine
    
    **5. Presentation Layer**
    - Interactive Streamlit interface
    - Real-time visualizations using Plotly
    - Comprehensive source citations
    - Export capabilities
    
    ### 📋 Supported Query Types
    
    1. **Comparative Analysis**
       - Compare metrics across states, districts, or time periods
       - Example: "Compare rainfall in Punjab vs Haryana"
    
    2. **Ranking & Top-N**
       - Identify top performers or extremes
       - Example: "Top 5 rice producing states in 2020"
    
    3. **Trend Analysis**
       - Analyze temporal patterns and forecasts
       - Example: "Wheat production trend in UP over last decade"
    
    4. **Correlation Studies**
       - Link climate patterns with agricultural outcomes
       - Example: "Correlation between monsoon rainfall and crop yield"
    
    5. **Policy Recommendations**
       - Data-backed suggestions for policy decisions
       - Example: "Should we promote rice or wheat cultivation in region X?"
    
    ### 🔒 Data Privacy & Security
    
    - All API keys stored in environment variables
    - No personal data collected or stored
    - Data cached with TTL for freshness
    - Secure HTTPS connections only
    - Audit logs for all data access
    
    ### 🚀 Getting Started
    
    1. Configure API keys in `.env` file
    2. Install dependencies: `pip install -r requirements.txt`
    3. Run application: `streamlit run app.py`
    4. Ask questions in natural language
    5. Explore results with full citations
    
    ### 📞 Technical Support
    
    For issues or questions, refer to:
    - GitHub Repository: [Project Samarth]
    - Documentation: README.md
    - API Documentation: data.gov.in
    
    ---
    
    **Built with ❤️ for India's Agricultural Future**
    
    *Submission for BTech Engineering Challenge*
    """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <strong>Project Samarth</strong> | Intelligent Agricultural Analytics Platform<br>
    Data sourced from <a href='https://data.gov.in' target='_blank'>data.gov.in</a> | 
    Built with Streamlit, Python, and ❤️<br>
    <em>BTech Engineering Challenge Submission 2025</em>
</div>
""", unsafe_allow_html=True)