"""
RetailSense - Main Streamlit Application
Module 1: Data Ingestion and Validation
"""
import streamlit as st
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import init_db

# Page configuration
st.set_page_config(
    page_title="RetailSense - Data Ingestion & Validation",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on first run
# Uses Streamlit session state to prevent re-initialization on every rerun
if 'db_initialized' not in st.session_state:
    try:
        init_db()
        st.session_state.db_initialized = True
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        st.error(f"Database initialization error: {e}")
        st.stop()

# Custom CSS for professional styling
st.markdown("""
    <style>
    /* Main theme colors */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ca02c;
        --warning-color: #ff9800;
        --error-color: #d62728;
        --background-color: #f8f9fa;
    }
    
    /* Header styling */
    .main-header {
        padding: 1.5rem 0;
        border-bottom: 3px solid #1f77b4;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: #1f77b4;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        color: #666;
        font-size: 1.1rem;
    }
    
    /* Card styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    
    .metric-card h3 {
        color: #333;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .metric-card .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1f77b4;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-success {
        background-color: #d4edda;
        color: #155724;
    }
    
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .status-error {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    .status-info {
        background-color: #d1ecf1;
        color: #0c5460;
    }
    
    /* Upload section */
    .upload-section {
        background: white;
        padding: 2rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    
    /* Table styling */
    .dataframe {
        font-size: 0.9rem;
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
    }
    
    /* Info boxes */
    .info-box {
        background-color: #e7f3ff;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    
    .warning-box {
        background-color: #fff8e1;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    
    .error-box {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    
    .success-box {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("🏪 RetailSense")
st.sidebar.markdown("### Intelligent Demand Forecasting")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["📊 Overview", "📁 Data Ingestion", "📋 Validation Reports", "📜 Dataset History"],
    key="navigation"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Module Status")
st.sidebar.success("✅ Module 1: Data Ingestion & Validation")
st.sidebar.info("⏳ Module 2: Feature Engineering (Coming Soon)")
st.sidebar.info("⏳ Module 3: Forecasting (Coming Soon)")
st.sidebar.info("⏳ Module 4: Inventory Optimization (Coming Soon)")

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    "**RetailSense** is an intelligent demand forecasting and inventory optimization system "
    "powered by machine learning. Module 1 focuses on data ingestion, validation, and quality checks."
)

# Route to appropriate page
if page == "📊 Overview":
    from dashboard.pages import overview
    overview.show()
elif page == "📁 Data Ingestion":
    from dashboard.pages import data_ingestion
    data_ingestion.show()
elif page == "📋 Validation Reports":
    from dashboard.pages import validation_reports
    validation_reports.show()
elif page == "📜 Dataset History":
    from dashboard.pages import dataset_history
    dataset_history.show()
