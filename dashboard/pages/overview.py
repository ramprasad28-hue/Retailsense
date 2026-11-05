"""
Overview page - Dashboard summary
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from src.data.ingestion_service import DataIngestionService
from src.data.report_generator import ReportGenerator

def show():
    """Display overview page"""
    
    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("📊 Overview Dashboard")
    st.markdown("Monitor data ingestion and validation status across all datasets")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Initialize services
    ingestion_service = DataIngestionService()
    report_generator = ReportGenerator()
    
    # Get all datasets
    all_datasets = ingestion_service.get_all_datasets()
    
    if not all_datasets:
        st.info("👋 Welcome to RetailSense! No datasets have been uploaded yet. Navigate to **Data Ingestion** to get started.")
        
        # Show what's possible
        st.markdown("---")
        st.subheader("📁 Supported Dataset Types")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Transaction Data:**
            - 📈 Sales Dataset
            - 📦 Inventory Dataset
            - 💰 Prices Dataset
            - 🎯 Promotions Dataset
            """)
        
        with col2:
            st.markdown("""
            **Master Data:**
            - 📅 Calendar Dataset
            - 🏪 Store Master Dataset
            - 📦 Product Master Dataset
            - 🚚 Supplier / Lead Time Dataset
            """)
        
        st.markdown("---")
        st.subheader("✨ Data Validation Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **Schema Validation**
            - Column name standardization
            - Data type validation
            - Required field checks
            """)
        
        with col2:
            st.markdown("""
            **Quality Checks**
            - Missing value analysis
            - Duplicate detection
            - Outlier identification
            """)
        
        with col3:
            st.markdown("""
            **Integrity Validation**
            - Business key validation
            - Negative value detection
            - Date format validation
            """)
        
        return
    
    # Summary metrics
    st.subheader("📈 Summary Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_datasets = len(all_datasets)
    validated_datasets = len([d for d in all_datasets if d.validation_passed == 1])
    failed_datasets = len([d for d in all_datasets if d.validation_passed == -1])
    pending_datasets = len([d for d in all_datasets if d.validation_passed == 0])
    
    with col1:
        st.metric("Total Datasets", total_datasets, help="Total number of uploaded datasets")
    
    with col2:
        st.metric("✅ Validated", validated_datasets, help="Datasets that passed validation")
    
    with col3:
        st.metric("⚠️ With Warnings", pending_datasets, help="Datasets with validation warnings")
    
    with col4:
        st.metric("❌ Failed", failed_datasets, help="Datasets that failed validation")
    
    st.markdown("---")
    
    # Data quality overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Dataset Types Distribution")
        
        # Count by dataset type
        type_counts = {}
        for dataset in all_datasets:
            type_counts[dataset.dataset_type] = type_counts.get(dataset.dataset_type, 0) + 1
        
        if type_counts:
            fig = px.pie(
                values=list(type_counts.values()),
                names=list(type_counts.keys()),
                title="Datasets by Type",
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")
    
    with col2:
        st.subheader("✅ Validation Status")
        
        # Validation status distribution
        status_counts = {
            "Passed": validated_datasets,
            "Warnings": pending_datasets,
            "Failed": failed_datasets
        }
        
        colors = ['#2ca02c', '#ff9800', '#d62728']
        
        fig = go.Figure(data=[go.Bar(
            x=list(status_counts.keys()),
            y=list(status_counts.values()),
            marker_color=colors,
            text=list(status_counts.values()),
            textposition='auto',
        )])
        
        fig.update_layout(
            title="Validation Status Distribution",
            xaxis_title="Status",
            yaxis_title="Count",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Data quality metrics
    st.subheader("🔍 Data Quality Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_missing = sum([d.missing_value_count or 0 for d in all_datasets])
    total_duplicates = sum([d.duplicate_count or 0 for d in all_datasets])
    total_outliers = sum([d.outlier_count or 0 for d in all_datasets])
    total_invalid = sum([d.invalid_record_count or 0 for d in all_datasets])
    
    with col1:
        st.metric("Missing Values", f"{total_missing:,}", help="Total missing values across all datasets")
    
    with col2:
        st.metric("Duplicates Removed", f"{total_duplicates:,}", help="Total duplicate records removed")
    
    with col3:
        st.metric("Outliers Detected", f"{total_outliers:,}", help="Total outliers detected")
    
    with col4:
        st.metric("Invalid Records", f"{total_invalid:,}", help="Records with integrity issues")
    
    st.markdown("---")
    
    # Recent datasets
    st.subheader("📜 Recent Datasets")
    
    # Create summary dataframe
    summary_df = report_generator.create_summary_report(all_datasets[:10])  # Show last 10
    
    if not summary_df.empty:
        # Style the dataframe
        def color_validation(val):
            if val == "Passed":
                return 'background-color: #d4edda; color: #155724'
            elif val == "Failed":
                return 'background-color: #f8d7da; color: #721c24'
            else:
                return 'background-color: #fff3cd; color: #856404'
        
        styled_df = summary_df.style.applymap(color_validation, subset=['Validation'])
        st.dataframe(styled_df, use_container_width=True, height=400)
    else:
        st.info("No datasets to display")
    
    # Quick actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📁 Upload New Dataset", use_container_width=True):
            st.session_state.navigation = "📁 Data Ingestion"
            st.rerun()
    
    with col2:
        if st.button("📋 View Reports", use_container_width=True):
            st.session_state.navigation = "📋 Validation Reports"
            st.rerun()
    
    with col3:
        if st.button("📜 Dataset History", use_container_width=True):
            st.session_state.navigation = "📜 Dataset History"
            st.rerun()
