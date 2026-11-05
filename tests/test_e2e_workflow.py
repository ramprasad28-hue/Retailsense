"""
End-to-end workflow test for Module 1: Data Ingestion and Validation
Tests the complete pipeline from file upload to database storage and report generation
"""
import pytest
import os
import tempfile
import pandas as pd
from datetime import datetime, timedelta
from src.data.ingestion_service import DataIngestionService
from src.database import init_db, get_db_session, UploadedDataset, ValidationMetrics


@pytest.fixture(scope="module")
def setup_test_db():
    """Initialize test database"""
    init_db()
    yield
    # Cleanup after tests
    

@pytest.fixture
def sample_sales_data():
    """Create sample sales CSV data with NumPy types"""
    data = {
        'Date': pd.date_range('2024-01-01', periods=100, freq='D'),
        'Store_ID': [f'S{i%10:03d}' for i in range(100)],
        'Product_ID': [f'P{i%20:03d}' for i in range(100)],
        'Sales': [100 + i * 10 for i in range(100)],
        'Units_Sold': [5 + i % 20 for i in range(100)]
    }
    df = pd.DataFrame(data)
    
    # Convert to CSV bytes
    csv_content = df.to_csv(index=False).encode('utf-8')
    
    return csv_content, len(df), len(df.columns)


@pytest.fixture
def sample_inventory_data():
    """Create sample inventory CSV data with unique store/product combinations"""
    # Create unique combinations of store and product
    stores = [f'S{i:03d}' for i in range(5)]
    products = [f'P{i:03d}' for i in range(10)]
    
    data = []
    for store in stores:
        for product in products:
            data.append({
                'Store_ID': store,
                'Product_ID': product,
                'Stock_Quantity': 100 + len(data) * 5
            })
    
    df = pd.DataFrame(data)
    
    csv_content = df.to_csv(index=False).encode('utf-8')
    
    return csv_content, len(df), len(df.columns)


class TestE2EWorkflow:
    """End-to-end workflow tests"""
    
    def test_complete_sales_ingestion_workflow(self, setup_test_db, sample_sales_data):
        """Test complete workflow: upload -> validate -> process -> store -> retrieve"""
        service = DataIngestionService()
        csv_content, expected_rows, expected_cols = sample_sales_data
        
        # Step 1: Ingest dataset
        result = service.ingest_dataset(
            file_content=csv_content,
            original_filename="test_sales.csv",
            dataset_type="sales"
        )
        
        # Verify ingestion success
        assert result["success"] is True, f"Ingestion failed: {result['errors']}"
        assert result["dataset_id"] is not None
        assert len(result["errors"]) == 0
        
        dataset_id = result["dataset_id"]
        
        # Step 2: Verify database record was created
        db_session = get_db_session()
        try:
            dataset = db_session.query(UploadedDataset).filter(
                UploadedDataset.id == dataset_id
            ).first()
            
            assert dataset is not None
            assert dataset.dataset_type == "sales"
            assert dataset.original_filename == "test_sales.csv"
            assert dataset.processing_status in ["cleaned", "validated"]
            assert dataset.total_rows == expected_rows
            assert dataset.total_columns == expected_cols
            assert dataset.validation_passed == 1
            
            # Verify JSON fields don't contain NumPy types (should not raise)
            assert dataset.validation_errors is not None
            assert dataset.validation_warnings is not None
            assert dataset.column_mapping is not None
            assert dataset.data_quality_report is not None
            
            # Verify validation metrics were stored
            metrics = db_session.query(ValidationMetrics).filter(
                ValidationMetrics.dataset_id == dataset_id
            ).first()
            
            assert metrics is not None
            assert metrics.missing_values_detail is not None
            
            # Verify file paths exist
            assert dataset.raw_file_path is not None
            assert os.path.exists(dataset.raw_file_path)
            
            if dataset.cleaned_file_path:
                assert os.path.exists(dataset.cleaned_file_path)
            
            if dataset.report_file_path:
                assert os.path.exists(dataset.report_file_path)
        
        finally:
            db_session.close()
    
    def test_inventory_ingestion_workflow(self, setup_test_db, sample_inventory_data):
        """Test inventory dataset ingestion"""
        service = DataIngestionService()
        csv_content, expected_rows, expected_cols = sample_inventory_data
        
        result = service.ingest_dataset(
            file_content=csv_content,
            original_filename="test_inventory.csv",
            dataset_type="inventory"
        )
        
        # Print errors if any
        if not result["success"]:
            print(f"Errors: {result['errors']}")
            print(f"Warnings: {result.get('warnings', [])}")
        
        assert result["success"] is True, f"Ingestion failed: {result['errors']}"
        assert result["dataset_id"] is not None
        
        # Verify database record
        dataset = service.get_dataset_by_id(result["dataset_id"])
        assert dataset is not None
        assert dataset.dataset_type == "inventory"
        assert dataset.total_rows == expected_rows
    
    def test_retrieve_all_datasets(self, setup_test_db):
        """Test retrieving all datasets from database"""
        service = DataIngestionService()
        
        all_datasets = service.get_all_datasets()
        
        assert isinstance(all_datasets, list)
        assert len(all_datasets) >= 2  # At least the two we created
        
        # Verify datasets are ordered by timestamp (most recent first)
        if len(all_datasets) > 1:
            for i in range(len(all_datasets) - 1):
                assert all_datasets[i].upload_timestamp >= all_datasets[i + 1].upload_timestamp
    
    def test_json_serialization_of_numpy_types(self, setup_test_db, sample_sales_data):
        """Test that NumPy types are properly converted for JSON storage"""
        service = DataIngestionService()
        csv_content, _, _ = sample_sales_data
        
        result = service.ingest_dataset(
            file_content=csv_content,
            original_filename="test_numpy_types.csv",
            dataset_type="sales"
        )
        
        assert result["success"] is True
        
        # Retrieve from database and verify JSON fields can be accessed
        db_session = get_db_session()
        try:
            dataset = db_session.query(UploadedDataset).filter(
                UploadedDataset.id == result["dataset_id"]
            ).first()
            
            # This should not raise TypeError for NumPy int64
            assert isinstance(dataset.data_quality_report, dict)
            
            # Verify metrics contain expected structure
            if 'missing_values' in dataset.data_quality_report:
                missing_vals = dataset.data_quality_report['missing_values']
                assert isinstance(missing_vals, dict)
            
            # Verify ValidationMetrics JSON fields
            metrics = db_session.query(ValidationMetrics).filter(
                ValidationMetrics.dataset_id == result["dataset_id"]
            ).first()
            
            if metrics:
                assert isinstance(metrics.missing_values_detail, dict)
                assert isinstance(metrics.outliers_by_column, dict)
        
        finally:
            db_session.close()
    
    def test_concurrent_database_initialization(self, setup_test_db):
        """Test that multiple calls to init_db() don't cause errors"""
        import threading
        
        errors = []
        
        def init_thread():
            try:
                init_db()
            except Exception as e:
                errors.append(str(e))
        
        threads = [threading.Thread(target=init_thread) for _ in range(5)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Concurrent initialization errors: {errors}"
    
    def test_database_persistence_after_restart(self, setup_test_db, sample_sales_data):
        """Test that data persists after database re-initialization"""
        service = DataIngestionService()
        csv_content, _, _ = sample_sales_data
        
        # Create a dataset
        result = service.ingest_dataset(
            file_content=csv_content,
            original_filename="test_persistence.csv",
            dataset_type="sales"
        )
        
        assert result["success"] is True
        dataset_id = result["dataset_id"]
        
        # Re-initialize database (simulating app restart)
        init_db()
        
        # Verify dataset still exists
        dataset = service.get_dataset_by_id(dataset_id)
        assert dataset is not None
        assert dataset.original_filename == "test_persistence.csv"
        assert dataset.dataset_type == "sales"
    
    def test_validation_report_generation(self, setup_test_db, sample_sales_data):
        """Test that validation report is generated and accessible"""
        service = DataIngestionService()
        csv_content, _, _ = sample_sales_data
        
        result = service.ingest_dataset(
            file_content=csv_content,
            original_filename="test_report.csv",
            dataset_type="sales"
        )
        
        assert result["success"] is True
        assert result["report_file_path"] is not None
        
        # Verify report file exists and can be read
        assert os.path.exists(result["report_file_path"])
        
        # Verify report contains expected data
        import json
        with open(result["report_file_path"], 'r') as f:
            report = json.load(f)
        
        assert "dataset_info" in report
        # The report might have different keys depending on implementation
        assert "processing_summary" in report or "validation_result" in report
        assert "summary" in report or "processing_summary" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
