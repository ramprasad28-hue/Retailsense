"""
Tests for data processing pipeline
"""
import pytest
import pandas as pd
import numpy as np

from src.data.processor import (
    SchemaStandardizer,
    DataCleaner,
    DataProcessor
)
from src.data.schemas import SalesSchema, InventorySchema


class TestSchemaStandardizer:
    """Tests for schema standardization"""
    
    def test_standardize_columns(self):
        """Test column name standardization"""
        df = pd.DataFrame({
            'Date': ['2024-01-01', '2024-01-02'],
            'Store ID': ['S001', 'S002'],
            'SKU': ['SKU001', 'SKU002'],
            'sales': [100, 200]  # Already correct
        })
        
        schema = SalesSchema()
        standardizer = SchemaStandardizer()
        
        df_std, mapping, missing, unexpected = standardizer.standardize_columns(df, schema)
        
        # Check that standardized columns are present
        assert 'date' in df_std.columns
        assert 'store_id' in df_std.columns
        assert 'sku_id' in df_std.columns
        assert 'sales' in df_std.columns
        assert len(missing) == 0
        assert len(unexpected) == 0
        
        # Check mapping
        assert mapping['Date'] == 'date'
        assert mapping['Store ID'] == 'store_id'
        assert mapping['SKU'] == 'sku_id'
    
    def test_missing_required_columns(self):
        """Test detection of missing required columns"""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'store_id': ['S001', 'S002']
            # Missing sku_id and sales
        })
        
        schema = SalesSchema()
        standardizer = SchemaStandardizer()
        
        df_std, mapping, missing, unexpected = standardizer.standardize_columns(df, schema)
        
        assert 'sku_id' in missing
        assert 'sales' in missing
    
    def test_unexpected_columns(self):
        """Test detection of unexpected columns"""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'store_id': ['S001', 'S002'],
            'sku_id': ['SKU001', 'SKU002'],
            'sales': [100, 200],
            'extra_column': ['X', 'Y']
        })
        
        schema = SalesSchema()
        standardizer = SchemaStandardizer()
        
        df_std, mapping, missing, unexpected = standardizer.standardize_columns(df, schema)
        
        assert 'extra_column' in unexpected
    
    def test_convert_data_types(self):
        """Test data type conversion"""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'store_id': ['S001', 'S002'],
            'sku_id': ['SKU001', 'SKU002'],
            'sales': ['100', '200']  # String instead of numeric
        })
        
        schema = SalesSchema()
        standardizer = SchemaStandardizer()
        
        df_converted, issues = standardizer.convert_data_types(df, schema)
        
        # Should be numeric (int64 or float64)
        assert pd.api.types.is_numeric_dtype(df_converted['sales'])
        assert pd.api.types.is_datetime64_any_dtype(df_converted['date'])


class TestDataCleaner:
    """Tests for data cleaning"""
    
    def test_remove_exact_duplicates(self):
        """Test exact duplicate removal"""
        df = pd.DataFrame({
            'col1': [1, 2, 3, 2, 1],
            'col2': ['a', 'b', 'c', 'b', 'a']
        })
        
        cleaner = DataCleaner()
        df_cleaned, removed_count = cleaner.remove_exact_duplicates(df)
        
        assert removed_count == 2
        assert len(df_cleaned) == 3
    
    def test_normalize_boolean_columns(self):
        """Test boolean column normalization"""
        df = pd.DataFrame({
            'promotion': ['Yes', 'No', 'yes', 'no', '1', '0', 'true', 'false']
        })
        
        cleaner = DataCleaner()
        df_normalized = cleaner.normalize_boolean_columns(df, ['promotion'])
        
        assert df_normalized['promotion'].dtype == np.int64
        assert df_normalized['promotion'].iloc[0] == 1  # Yes -> 1
        assert df_normalized['promotion'].iloc[1] == 0  # No -> 0
        assert df_normalized['promotion'].iloc[2] == 1  # yes -> 1
        assert df_normalized['promotion'].iloc[3] == 0  # no -> 0


class TestDataProcessor:
    """Integration tests for data processor"""
    
    def test_process_valid_sales_dataset(self):
        """Test processing a valid sales dataset"""
        df = pd.DataFrame({
            'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'Store ID': ['S001', 'S001', 'S002'],
            'SKU': ['SKU001', 'SKU002', 'SKU001'],
            'Sales': [100, 150, 200]
        })
        
        processor = DataProcessor()
        result = processor.process_dataset(df, 'sales', auto_clean=True)
        
        assert result['success']
        assert result['cleaned_df'] is not None
        assert len(result['errors']) == 0
        assert result['standardized_df'] is not None
    
    def test_process_dataset_with_duplicates(self):
        """Test processing dataset with duplicates"""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-01', '2024-01-02'],
            'store_id': ['S001', 'S001', 'S001'],
            'sku_id': ['SKU001', 'SKU001', 'SKU001'],
            'sales': [100, 100, 200]  # First two rows are exact duplicates
        })
        
        processor = DataProcessor()
        result = processor.process_dataset(df, 'sales', auto_clean=True)
        
        assert result['success']
        assert result['processing_stats']['cleaning']['removed_exact_duplicates'] == 1
    
    def test_process_dataset_missing_columns(self):
        """Test processing dataset with missing required columns"""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'store_id': ['S001', 'S002']
            # Missing sku_id and sales
        })
        
        processor = DataProcessor()
        result = processor.process_dataset(df, 'sales', auto_clean=True)
        
        assert not result['success']
        assert len(result['errors']) > 0
        assert any('Missing required columns' in e for e in result['errors'])
    
    def test_validate_file_before_processing(self):
        """Test pre-validation"""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'store_id': ['S001', 'S002'],
            'sku_id': ['SKU001', 'SKU002'],
            'sales': [100, 200]
        })
        
        processor = DataProcessor()
        validation = processor.validate_file_before_processing(df, 'sales')
        
        assert validation['can_process']
        assert len(validation['issues']) == 0
    
    def test_validate_empty_dataset(self):
        """Test validation of empty dataset"""
        df = pd.DataFrame()
        
        processor = DataProcessor()
        validation = processor.validate_file_before_processing(df, 'sales')
        
        assert not validation['can_process']
        assert len(validation['issues']) > 0


class TestInventoryProcessing:
    """Test processing inventory datasets"""
    
    def test_process_valid_inventory(self):
        """Test processing valid inventory dataset"""
        df = pd.DataFrame({
            'store_id': ['S001', 'S002', 'S003'],
            'sku_id': ['SKU001', 'SKU001', 'SKU002'],
            'stock_quantity': [100, 150, 200]
        })
        
        processor = DataProcessor()
        result = processor.process_dataset(df, 'inventory', auto_clean=True)
        
        assert result['success']
        assert result['cleaned_df'] is not None
        assert len(result['cleaned_df']) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
