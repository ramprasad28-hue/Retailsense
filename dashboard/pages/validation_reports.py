"""
Validation Reports page - Detailed validation results
"""
import streamlit as st
import json
import pandas as pd
from src.data.ingestion_service import DataIngestionService

def show():
    """Display validation reports page"""
    
    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("📋 Validation Reports")
    st.markdown("Detailed validation results and data quality metrics")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Initialize service
    ingestion_service = DataIngestionService()
    
    # Get all datasets
    all_datasets = ingestion_service.get_all_datasets()
    
    if not all_datasets:
        st.info("No datasets available. Please upload datasets first.")
        return
    
    # Dataset selector
    dataset_options = {
        f"{d.original_filename} ({d.dataset_type}) - ID: {d.id}": d.id
        for d in all_datasets
    }
    
    # Check if a specific dataset was selected from another page
    default_index = 0
    if 'selected_dataset_id' in st.session_state:
        try:
            dataset_ids = list(dataset_options.values())
            default_index = dataset_ids.index(st.session_state.selected_dataset_id)
            del st.session_state.selected_dataset_id  # Clear after use
        except (ValueError, AttributeError):
            pass
    
    selected_dataset_key = st.selectbox(
        "Select Dataset",
        options=list(dataset_options.keys()),
        index=default_index
    )
    
    dataset_id = dataset_options[selected_dataset_key]
    dataset = ingestion_service.get_dataset_by_id(dataset_id)
    
    if not dataset:
        st.error("Dataset not found")
        return
    
    # Dataset information
    st.markdown("---")
    st.subheader("📊 Dataset Information")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Dataset Type", dataset.dataset_type.replace("_", " ").title())
    
    with col2:
        st.metric("Total Rows", f"{dataset.total_rows or 0:,}")
    
    with col3:
        st.metric("Total Columns", dataset.total_columns or 0)
    
    with col4:
        file_size_mb = (dataset.file_size or 0) / (1024 * 1024)
        st.metric("File Size", f"{file_size_mb:.2f} MB")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Upload Date", dataset.upload_timestamp.strftime("%Y-%m-%d %H:%M") if dataset.upload_timestamp else "N/A")
    
    with col2:
        st.metric("Processing Time", f"{dataset.processing_time:.2f}s" if dataset.processing_time else "N/A")
    
    with col3:
        # Status badge
        if dataset.validation_passed == 1:
            st.success("✅ Validation Passed")
        elif dataset.validation_passed == -1:
            st.error("❌ Validation Failed")
        else:
            st.warning("⚠️ Has Warnings")
    
    # Validation summary
    st.markdown("---")
    st.subheader("🔍 Data Quality Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        missing_count = dataset.missing_value_count or 0
        st.metric(
            "Missing Values",
            f"{missing_count:,}",
            delta=None,
            help="Total number of missing values detected"
        )
    
    with col2:
        dup_count = dataset.duplicate_count or 0
        st.metric(
            "Duplicates Removed",
            f"{dup_count:,}",
            delta=f"-{dup_count}" if dup_count > 0 else None,
            help="Exact duplicate rows removed"
        )
    
    with col3:
        outlier_count = dataset.outlier_count or 0
        st.metric(
            "Outliers Detected",
            f"{outlier_count:,}",
            delta=None,
            help="Statistical outliers detected using IQR method"
        )
    
    with col4:
        invalid_count = dataset.invalid_record_count or 0
        st.metric(
            "Invalid Records",
            f"{invalid_count:,}",
            delta=None,
            help="Records with data integrity issues"
        )
    
    # Column mapping
    if dataset.column_mapping:
        st.markdown("---")
        st.subheader("🔄 Column Standardization")
        
        mapping_data = []
        for orig, std in dataset.column_mapping.items():
            mapping_data.append({
                "Original Column": orig,
                "Standardized Column": std,
                "Status": "✅ Mapped"
            })
        
        if mapping_data:
            mapping_df = pd.DataFrame(mapping_data)
            st.dataframe(mapping_df, use_container_width=True, hide_index=True)
    
    # Validation errors and warnings
    col1, col2 = st.columns(2)
    
    with col1:
        if dataset.validation_errors:
            with st.expander(f"❌ Errors ({len(dataset.validation_errors)})", expanded=True):
                for i, error in enumerate(dataset.validation_errors, 1):
                    st.error(f"{i}. {error}")
        else:
            st.success("✅ No validation errors")
    
    with col2:
        if dataset.validation_warnings:
            with st.expander(f"⚠️ Warnings ({len(dataset.validation_warnings)})", expanded=False):
                for i, warning in enumerate(dataset.validation_warnings, 1):
                    st.warning(f"{i}. {warning}")
        else:
            st.info("ℹ️ No warnings")
    
    # Detailed metrics
    if dataset.data_quality_report:
        st.markdown("---")
        st.subheader("📊 Detailed Data Quality Metrics")
        
        report = dataset.data_quality_report
        
        # Missing values detail
        if "missing_values" in report:
            with st.expander("🔍 Missing Values Analysis", expanded=False):
                missing_info = report["missing_values"]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Missing", missing_info.get("total_missing_values", 0))
                with col2:
                    st.metric("Missing %", f"{missing_info.get('missing_percentage', 0):.2f}%")
                with col3:
                    st.metric("Columns Affected", len(missing_info.get("columns_with_missing", [])))
                
                # Per-column details
                if missing_info.get("column_details"):
                    st.markdown("**Missing Values by Column:**")
                    missing_data = []
                    for col, details in missing_info["column_details"].items():
                        if details["missing_count"] > 0:
                            missing_data.append({
                                "Column": col,
                                "Missing Count": details["missing_count"],
                                "Missing %": f"{details['missing_percentage']:.2f}%",
                                "Total Rows": details["total_rows"]
                            })
                    
                    if missing_data:
                        st.dataframe(pd.DataFrame(missing_data), use_container_width=True, hide_index=True)
        
        # Outliers detail
        if "outliers" in report:
            with st.expander("📈 Outlier Analysis", expanded=False):
                outlier_info = report["outliers"]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Outliers", outlier_info.get("total_outliers", 0))
                with col2:
                    st.metric("Method", outlier_info.get("method", "IQR"))
                with col3:
                    st.metric("Columns Affected", len(outlier_info.get("columns_with_outliers", [])))
                
                # Per-column outlier details
                if outlier_info.get("outlier_details"):
                    st.markdown("**Outliers by Column:**")
                    outlier_data = []
                    for col, details in outlier_info["outlier_details"].items():
                        outlier_data.append({
                            "Column": col,
                            "Outlier Count": details["count"],
                            "Percentage": f"{details['percentage']:.2f}%",
                            "Lower Bound": f"{details['lower_bound']:.2f}",
                            "Upper Bound": f"{details['upper_bound']:.2f}"
                        })
                    
                    if outlier_data:
                        st.dataframe(pd.DataFrame(outlier_data), use_container_width=True, hide_index=True)
                
                st.info(f"💡 {outlier_info.get('recommendation', 'Review outliers individually')}")
        
        # Data integrity
        if "data_integrity" in report:
            with st.expander("🔒 Data Integrity Checks", expanded=False):
                integrity_info = report["data_integrity"]
                
                if integrity_info.get("errors"):
                    st.markdown("**Integrity Errors:**")
                    for error in integrity_info["errors"]:
                        st.error(error)
                else:
                    st.success("✅ No integrity errors found")
                
                if integrity_info.get("warnings"):
                    st.markdown("**Integrity Warnings:**")
                    for warning in integrity_info["warnings"]:
                        st.warning(warning)
    
    # Download section
    st.markdown("---")
    st.subheader("📥 Download Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Download original file
        if dataset.raw_file_path:
            try:
                with open(dataset.raw_file_path, 'rb') as f:
                    raw_data = f.read()
                
                st.download_button(
                    label="⬇️ Original Dataset",
                    data=raw_data,
                    file_name=dataset.original_filename,
                    mime="text/csv",
                    use_container_width=True
                )
            except:
                st.button("⬇️ Original Dataset", disabled=True, use_container_width=True)
    
    with col2:
        # Download cleaned file
        if dataset.cleaned_file_path:
            try:
                with open(dataset.cleaned_file_path, 'rb') as f:
                    cleaned_data = f.read()
                
                st.download_button(
                    label="⬇️ Cleaned Dataset",
                    data=cleaned_data,
                    file_name=f"cleaned_{dataset.original_filename}",
                    mime="text/csv",
                    use_container_width=True
                )
            except:
                st.button("⬇️ Cleaned Dataset", disabled=True, use_container_width=True)
        else:
            st.button("⬇️ Cleaned Dataset", disabled=True, use_container_width=True)
    
    with col3:
        # Download validation report
        if dataset.report_file_path:
            try:
                with open(dataset.report_file_path, 'rb') as f:
                    report_data = f.read()
                
                st.download_button(
                    label="⬇️ Validation Report (JSON)",
                    data=report_data,
                    file_name=f"report_{dataset.original_filename.replace('.csv', '.json')}",
                    mime="application/json",
                    use_container_width=True
                )
            except:
                st.button("⬇️ Validation Report", disabled=True, use_container_width=True)
        else:
            st.button("⬇️ Validation Report", disabled=True, use_container_width=True)
