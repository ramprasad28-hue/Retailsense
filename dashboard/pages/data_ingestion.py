"""
Data Ingestion page - Upload and process datasets
"""
import streamlit as st
import pandas as pd
from src.data.ingestion_service import DataIngestionService
from src.data.schemas import SchemaRegistry
import io

def show():
    """Display data ingestion page"""
    
    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("📁 Data Ingestion & Validation")
    st.markdown("Upload datasets for validation and quality checks")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Initialize service
    ingestion_service = DataIngestionService()
    
    # Upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("📤 Upload Dataset")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            help="Upload a CSV file containing retail data. Maximum file size: 100 MB"
        )
    
    with col2:
        # Dataset type selector
        dataset_types = SchemaRegistry.get_all_types()
        type_display_names = SchemaRegistry.get_type_display_names()
        
        selected_type = st.selectbox(
            "Dataset Type",
            options=dataset_types,
            format_func=lambda x: type_display_names.get(x, x),
            help="Select the type of dataset you're uploading"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display expected schema
    if selected_type:
        with st.expander("📋 Expected Schema & Column Names", expanded=False):
            schema = SchemaRegistry.get_schema(selected_type)
            if schema:
                st.markdown(f"**Required Columns for {type_display_names.get(selected_type, selected_type)}:**")
                
                schema_data = []
                for col in schema.columns:
                    schema_data.append({
                        "Column Name": col.name,
                        "Data Type": col.dtype.replace("64[ns]", "").replace("object", "text"),
                        "Required": "✅ Yes" if col.required else "⬜ No",
                        "Description": col.description
                    })
                
                schema_df = pd.DataFrame(schema_data)
                st.dataframe(schema_df, use_container_width=True, hide_index=True)
                
                st.info(
                    "💡 **Tip:** Column names are flexible! We support common variations like "
                    "'Store ID', 'store_id', 'StoreID', etc. The system will automatically standardize them."
                )
    
    # Download sample template
    st.markdown("---")
    st.subheader("📥 Download Sample Templates")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📈 Sales Template", use_container_width=True):
            st.session_state.download_template = "sales"
    
    with col2:
        if st.button("📦 Inventory Template", use_container_width=True):
            st.session_state.download_template = "inventory"
    
    with col3:
        if st.button("💰 Prices Template", use_container_width=True):
            st.session_state.download_template = "prices"
    
    with col4:
        if st.button("🎯 Promotions Template", use_container_width=True):
            st.session_state.download_template = "promotions"
    
    # Provide download link if template was requested
    if 'download_template' in st.session_state:
        template_type = st.session_state.download_template
        schema = SchemaRegistry.get_schema(template_type)
        
        if schema:
            # Create sample data
            sample_data = {}
            for col in schema.columns:
                if "date" in col.name.lower():
                    sample_data[col.name] = ["2024-01-01", "2024-01-02", "2024-01-03"]
                elif col.name in ["store_id", "sku_id"]:
                    sample_data[col.name] = ["S001", "S001", "S002"]
                elif col.dtype == "float64":
                    sample_data[col.name] = [100.0, 150.0, 200.0]
                else:
                    sample_data[col.name] = ["Sample1", "Sample2", "Sample3"]
            
            sample_df = pd.DataFrame(sample_data)
            csv_buffer = io.StringIO()
            sample_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()
            
            st.download_button(
                label=f"⬇️ Download {type_display_names.get(template_type, template_type)} Template",
                data=csv_data,
                file_name=f"{template_type}_template.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # Clear the state after showing download
        if st.button("Clear", use_container_width=True):
            del st.session_state.download_template
            st.rerun()
    
    # Process uploaded file
    if uploaded_file is not None:
        st.markdown("---")
        st.subheader("📊 Upload Preview")
        
        # Show file details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Filename", uploaded_file.name)
        
        with col2:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.metric("File Size", f"{file_size_mb:.2f} MB")
        
        with col3:
            st.metric("Dataset Type", type_display_names.get(selected_type, selected_type))
        
        # Preview data
        try:
            df_preview = pd.read_csv(uploaded_file)
            uploaded_file.seek(0)  # Reset file pointer
            
            st.markdown("**Data Preview (First 10 Rows):**")
            st.dataframe(df_preview.head(10), use_container_width=True)
            
            st.info(f"📊 Dataset contains **{len(df_preview)} rows** and **{len(df_preview.columns)} columns**")
            
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            return
        
        # Process button
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            process_button = st.button(
                "🚀 Process & Validate Dataset",
                type="primary",
                use_container_width=True
            )
        
        if process_button:
            with st.spinner("Processing dataset... This may take a moment."):
                # Read file content
                file_content = uploaded_file.read()
                
                # Process dataset
                result = ingestion_service.ingest_dataset(
                    file_content=file_content,
                    original_filename=uploaded_file.name,
                    dataset_type=selected_type
                )
                
                # Display results
                st.markdown("---")
                st.subheader("✅ Processing Results")
                
                if result["success"]:
                    st.success("✅ Dataset processed successfully!")
                    
                    # Show summary
                    dataset_record = result.get("dataset_record")
                    if dataset_record:
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Rows Processed", dataset_record.total_rows or 0)
                        
                        with col2:
                            st.metric("Missing Values", dataset_record.missing_value_count or 0)
                        
                        with col3:
                            st.metric("Duplicates Removed", dataset_record.duplicate_count or 0)
                        
                        with col4:
                            st.metric("Outliers Detected", dataset_record.outlier_count or 0)
                        
                        # Validation status
                        if dataset_record.validation_passed == 1:
                            st.success("🎉 Dataset passed all validation checks!")
                        elif dataset_record.validation_passed == -1:
                            st.error("❌ Dataset failed validation. Review errors below.")
                        else:
                            st.warning("⚠️ Dataset has warnings but can be used.")
                    
                    # Show warnings
                    if result.get("warnings"):
                        with st.expander("⚠️ Warnings", expanded=False):
                            for warning in result["warnings"]:
                                st.warning(warning)
                    
                    # Show errors
                    if result.get("errors"):
                        with st.expander("❌ Errors", expanded=True):
                            for error in result["errors"]:
                                st.error(error)
                    
                    # Download options
                    st.markdown("---")
                    st.subheader("📥 Download Results")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Download cleaned dataset
                        if result.get("cleaned_file_path"):
                            try:
                                with open(result["cleaned_file_path"], 'rb') as f:
                                    cleaned_data = f.read()
                                
                                st.download_button(
                                    label="⬇️ Download Cleaned Dataset",
                                    data=cleaned_data,
                                    file_name=f"cleaned_{uploaded_file.name}",
                                    mime="text/csv",
                                    use_container_width=True
                                )
                            except:
                                st.info("Cleaned dataset not available")
                    
                    with col2:
                        # Download validation report
                        if result.get("report_file_path"):
                            try:
                                with open(result["report_file_path"], 'rb') as f:
                                    report_data = f.read()
                                
                                st.download_button(
                                    label="⬇️ Download Validation Report",
                                    data=report_data,
                                    file_name=f"report_{uploaded_file.name.replace('.csv', '.json')}",
                                    mime="application/json",
                                    use_container_width=True
                                )
                            except:
                                st.info("Report not available")
                    
                    # Navigation options
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("📋 View Detailed Report", use_container_width=True):
                            st.session_state.navigation = "📋 Validation Reports"
                            st.session_state.selected_dataset_id = result.get("dataset_id")
                            st.rerun()
                    
                    with col2:
                        if st.button("📁 Upload Another Dataset", use_container_width=True):
                            st.rerun()
                
                else:
                    st.error("❌ Processing failed!")
                    
                    # Show errors
                    for error in result.get("errors", []):
                        st.error(error)
                    
                    st.info("💡 Please check your file format and try again.")
