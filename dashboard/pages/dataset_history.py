"""
Dataset History page - View and manage all uploaded datasets
"""
import streamlit as st
import pandas as pd
from src.data.ingestion_service import DataIngestionService
from src.data.report_generator import ReportGenerator

def show():
    """Display dataset history page"""
    
    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("📜 Dataset History")
    st.markdown("View and manage all uploaded datasets")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Initialize services
    ingestion_service = DataIngestionService()
    report_generator = ReportGenerator()
    
    # Get all datasets
    all_datasets = ingestion_service.get_all_datasets()
    
    if not all_datasets:
        st.info("📭 No datasets have been uploaded yet.")
        
        if st.button("📁 Go to Data Ingestion"):
            st.session_state.navigation = "📁 Data Ingestion"
            st.rerun()
        
        return
    
    # Summary statistics
    st.subheader("📊 Summary Statistics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_count = len(all_datasets)
    passed_count = len([d for d in all_datasets if d.validation_passed == 1])
    failed_count = len([d for d in all_datasets if d.validation_passed == -1])
    warning_count = len([d for d in all_datasets if d.validation_passed == 0])
    total_rows = sum([d.total_rows or 0 for d in all_datasets])
    
    with col1:
        st.metric("Total Datasets", total_count)
    
    with col2:
        st.metric("✅ Passed", passed_count)
    
    with col3:
        st.metric("⚠️ Warnings", warning_count)
    
    with col4:
        st.metric("❌ Failed", failed_count)
    
    with col5:
        st.metric("Total Rows", f"{total_rows:,}")
    
    st.markdown("---")
    
    # Filters
    st.subheader("🔍 Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Dataset type filter
        dataset_types = ["All"] + sorted(list(set([d.dataset_type for d in all_datasets])))
        selected_type = st.selectbox("Dataset Type", dataset_types)
    
    with col2:
        # Status filter
        status_options = ["All", "Passed", "Failed", "Warnings"]
        selected_status = st.selectbox("Validation Status", status_options)
    
    with col3:
        # Sort by
        sort_options = ["Upload Date (Newest)", "Upload Date (Oldest)", "File Size (Largest)", "File Size (Smallest)"]
        selected_sort = st.selectbox("Sort By", sort_options)
    
    # Apply filters
    filtered_datasets = all_datasets
    
    if selected_type != "All":
        filtered_datasets = [d for d in filtered_datasets if d.dataset_type == selected_type]
    
    if selected_status == "Passed":
        filtered_datasets = [d for d in filtered_datasets if d.validation_passed == 1]
    elif selected_status == "Failed":
        filtered_datasets = [d for d in filtered_datasets if d.validation_passed == -1]
    elif selected_status == "Warnings":
        filtered_datasets = [d for d in filtered_datasets if d.validation_passed == 0]
    
    # Apply sorting
    if "Newest" in selected_sort:
        filtered_datasets = sorted(filtered_datasets, key=lambda x: x.upload_timestamp or "", reverse=True)
    elif "Oldest" in selected_sort:
        filtered_datasets = sorted(filtered_datasets, key=lambda x: x.upload_timestamp or "")
    elif "Largest" in selected_sort:
        filtered_datasets = sorted(filtered_datasets, key=lambda x: x.file_size or 0, reverse=True)
    elif "Smallest" in selected_sort:
        filtered_datasets = sorted(filtered_datasets, key=lambda x: x.file_size or 0)
    
    # Display results
    st.markdown("---")
    st.subheader(f"📋 Datasets ({len(filtered_datasets)} found)")
    
    if not filtered_datasets:
        st.info("No datasets match the selected filters.")
        return
    
    # Create summary table
    summary_df = report_generator.create_summary_report(filtered_datasets)
    
    # Style the dataframe
    def style_validation(val):
        if val == "Passed":
            return 'background-color: #d4edda; color: #155724; font-weight: bold'
        elif val == "Failed":
            return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
        elif val == "Pending":
            return 'background-color: #fff3cd; color: #856404; font-weight: bold'
        return ''
    
    def style_status(val):
        if val == "cleaned":
            return 'background-color: #d4edda; color: #155724'
        elif val == "failed":
            return 'background-color: #f8d7da; color: #721c24'
        elif val == "validated":
            return 'background-color: #d1ecf1; color: #0c5460'
        return ''
    
    # Display styled dataframe
    styled_df = summary_df.style.applymap(style_validation, subset=['Validation'])
    styled_df = styled_df.applymap(style_status, subset=['Status'])
    
    st.dataframe(styled_df, use_container_width=True, height=500)
    
    # Bulk actions
    st.markdown("---")
    st.subheader("⚡ Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📥 Export Summary (CSV)", use_container_width=True):
            csv = summary_df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name="dataset_history.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("📋 View Reports", use_container_width=True):
            st.session_state.navigation = "📋 Validation Reports"
            st.rerun()
    
    with col4:
        if st.button("📁 Upload New", use_container_width=True):
            st.session_state.navigation = "📁 Data Ingestion"
            st.rerun()
    
    # Dataset details and management
    st.markdown("---")
    st.subheader("🔧 Dataset Management")
    
    # Select dataset for detailed actions
    dataset_options = {
        f"{d.original_filename} (ID: {d.id})": d.id
        for d in filtered_datasets
    }
    
    selected_key = st.selectbox(
        "Select dataset for detailed actions:",
        options=list(dataset_options.keys())
    )
    
    selected_id = dataset_options[selected_key]
    selected_dataset = next((d for d in filtered_datasets if d.id == selected_id), None)
    
    if selected_dataset:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Dataset Details:**")
            st.write(f"**Type:** {selected_dataset.dataset_type}")
            st.write(f"**Status:** {selected_dataset.processing_status}")
            st.write(f"**Rows:** {selected_dataset.total_rows or 0:,}")
            st.write(f"**Columns:** {selected_dataset.total_columns or 0}")
            st.write(f"**Size:** {(selected_dataset.file_size or 0) / (1024*1024):.2f} MB")
        
        with col2:
            st.markdown("**Quality Metrics:**")
            st.write(f"**Missing Values:** {selected_dataset.missing_value_count or 0:,}")
            st.write(f"**Duplicates:** {selected_dataset.duplicate_count or 0:,}")
            st.write(f"**Outliers:** {selected_dataset.outlier_count or 0:,}")
            st.write(f"**Invalid Records:** {selected_dataset.invalid_record_count or 0:,}")
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 View Detailed Report", use_container_width=True, key="view_report"):
                st.session_state.navigation = "📋 Validation Reports"
                st.session_state.selected_dataset_id = selected_id
                st.rerun()
        
        with col2:
            # Download cleaned dataset
            if selected_dataset.cleaned_file_path:
                try:
                    with open(selected_dataset.cleaned_file_path, 'rb') as f:
                        cleaned_data = f.read()
                    
                    st.download_button(
                        label="⬇️ Download Cleaned",
                        data=cleaned_data,
                        file_name=f"cleaned_{selected_dataset.original_filename}",
                        mime="text/csv",
                        use_container_width=True,
                        key="download_cleaned"
                    )
                except:
                    st.button("⬇️ Download Cleaned", disabled=True, use_container_width=True)
            else:
                st.button("⬇️ Download Cleaned", disabled=True, use_container_width=True)
        
        with col3:
            # Delete dataset
            if st.button("🗑️ Delete Dataset", type="secondary", use_container_width=True, key="delete"):
                st.session_state.confirm_delete = selected_id
        
        # Confirm deletion
        if 'confirm_delete' in st.session_state and st.session_state.confirm_delete == selected_id:
            st.warning("⚠️ Are you sure you want to delete this dataset? This action cannot be undone.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Yes, Delete", type="primary", use_container_width=True):
                    success, error = ingestion_service.delete_dataset(selected_id)
                    
                    if success:
                        st.success("Dataset deleted successfully!")
                        del st.session_state.confirm_delete
                        st.rerun()
                    else:
                        st.error(f"Failed to delete dataset: {error}")
            
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    del st.session_state.confirm_delete
                    st.rerun()
