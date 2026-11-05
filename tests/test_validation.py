"""
Tests for data validation functionality
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.data.validation import (
    MissingValueAnalyzer,
    DuplicateDetector,
    OutlierDetector,
    DataIntegrityChecker,
    DataValidator
)


class TestMissingValueAnalyzer:
    """Tests for missing value analysis"""
    
    def test_no_missing_values(self):
        """Test dataset with no missing values"""
        df = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': ['a', 'b', 'c', 'd', 'e']
        })
        
        analyzer = MissingValueAnalyzer()
        result = analyzer.analyze(df)
        
        assert result['total_missing_values'] == 0
        assert result['missing_percentage'] == 0
        assert len(result['columns_with_missing']) == 0
    
    def test_with_missing_values(self):
        """Test dataset with missing values"""
        df = pd.DataFrame({
            'col1': [1, 2, np.nan, 4, 5],
            'col2': ['a', None, 'c', 'd', 'e']
        })
        
        analyzer = MissingValueAnalyzer()
        result = analyzer.analyze(df)
        
        assert result['total_missing_values'] == 2
        assert result['missing_percentage'] == 20.0  # 2 out of 10 cells
        assert 'col1' in result['columns_with_missing']
        assert 'col2' in result['columns_with_missing']
    
    def test_column_details(self):
        """Test per-column missing value details"""
        df = pd.DataFrame({
            'col1': [1, np.nan, np.nan, 4, 5],
            'col2': ['a', 'b', 'c', 'd', 'e']
        })
        
        analyzer = MissingValueAnalyzer()
        result = analyzer.analyze(df)
        
        assert result['column_details']['col1']['missing_count'] == 2
        assert result['column_details']['col1']['missing_percentage'] == 40.0
        assert result['column_details']['col2']['missing_count'] == 0


class TestDuplicateDetector:
    """Tests for duplicate detection"""
    
    def test_no_duplicates(self):
        """Test dataset with no duplicates"""
        df = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': ['a', 'b', 'c', 'd', 'e']
        })
        
        detector = DuplicateDetector()
        result = detector.detect_exact_duplicates(df)
        
        assert result['exact_duplicate_count'] == 0
        assert result['unique_rows'] == 5
    
    def test_exact_duplicates(self):
        """Test detection of exact duplicate rows"""
        df = pd.DataFrame({
            'col1': [1, 2, 3, 2, 1],
            'col2': ['a', 'b', 'c', 'b', 'a']
        })
        
        detector = DuplicateDetector()
        result = detector.detect_exact_duplicates(df)
        
        assert result['exact_duplicate_count'] == 2
        assert result['unique_rows'] == 3
    
    def test_business_key_duplicates(self):
        """Test business key duplicate detection"""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-01', '2024-01-02'],
            'store_id': ['S001', 'S001', 'S001'],
            'sku_id': ['SKU001', 'SKU001', 'SKU001'],
            'sales': [100, 150, 200]  # Different values but same key
        })
        
        detector = DuplicateDetector()
        business_key = ['date', 'store_id', 'sku_id']
        result = detector.detect_business_key_duplicates(df, business_key)
        
        assert result['business_key_duplicate_count'] == 2  # First two rows
    
    def test_remove_exact_duplicates(self):
        """Test removal of exact duplicates"""
        df = pd.DataFrame({
            'col1': [1, 2, 3, 2, 1],
            'col2': ['a', 'b', 'c', 'b', 'a']
        })
        
        detector = DuplicateDetector()
        cleaned_df, removed_count = detector.remove_exact_duplicates(df)
        
        assert removed_count == 2
        assert len(cleaned_df) == 3


class TestOutlierDetector:
    """Tests for outlier detection"""
    
    def test_no_outliers(self):
        """Test dataset with no outliers"""
        df = pd.DataFrame({
            'values': [10, 12, 11, 13, 12, 11, 10, 13]
        })
        
        detector = OutlierDetector()
        result = detector.detect_iqr_outliers(df)
        
        assert result['total_outliers'] == 0
        assert len(result['columns_with_outliers']) == 0
    
    def test_with_outliers(self):
        """Test dataset with outliers"""
        df = pd.DataFrame({
            'values': [10, 12, 11, 13, 12, 11, 10, 13, 100, 200]  # 100 and 200 are outliers
        })
        
        detector = OutlierDetector()
        result = detector.detect_iqr_outliers(df)
        
        assert result['total_outliers'] > 0
        assert 'values' in result['columns_with_outliers']
    
    def test_outlier_bounds(self):
        """Test outlier boundary calculations"""
        df = pd.DataFrame({
            'values': list(range(1, 21)) + [100]  # 100 is an outlier
        })
        
        detector = OutlierDetector()
        result = detector.detect_iqr_outliers(df)
        
        details = result['outlier_details']['values']
        assert 'lower_bound' in details
        assert 'upper_bound' in details
        assert details['count'] > 0


class TestDataIntegrityChecker:
    """Tests for data integrity checks"""
    
    def test_negative_values(self):
        """Test negative value detection"""
        df = pd.DataFrame({
            'sales': [100, 200, -50, 150],  # One negative value
            'price': [10.0, 20.0, 15.0, 25.0]
        })
        
        checker = DataIntegrityChecker()
        result = checker.check_negative_values(df, ['sales', 'price'])
        
        assert result['total_negative_values'] == 1
        assert 'sales' in result['columns_affected']
        assert 'price' not in result['columns_affected']
    
    def test_date_validity(self):
        """Test date validation"""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-02-30', '2024-03-15', 'invalid']
        })
        
        checker = DataIntegrityChecker()
        result = checker.check_date_validity(df, ['date'])
        
        assert 'date' in result['columns_with_issues']
        assert result['details']['date']['count'] > 0
    
    def test_empty_identifiers(self):
        """Test empty identifier detection"""
        df = pd.DataFrame({
            'store_id': ['S001', '', 'S003', None],
            'sku_id': ['SKU001', 'SKU002', 'SKU003', 'SKU004']
        })
        
        checker = DataIntegrityChecker()
        result = checker.check_empty_identifiers(df, ['store_id', 'sku_id'])
        
        assert 'store_id' in result['columns_with_issues']
        assert result['details']['store_id']['total_invalid'] == 2  # Empty and None
    
    def test_invalid_prices(self):
        """Test price validation"""
        df = pd.DataFrame({
            'price': [10.0, 20.0, -5.0, 0.0, 15.0]
        })
        
        checker = DataIntegrityChecker()
        result = checker.check_invalid_prices(df, 'price')
        
        assert result['issues_found']
        assert 'negative_prices' in result['details']
        assert result['details']['negative_prices']['count'] == 1


class TestDataValidator:
    """Integration tests for complete validation"""
    
    def test_valid_sales_dataset(self):
        """Test validation of a valid sales dataset"""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'store_id': ['S001', 'S001', 'S002'],
            'sku_id': ['SKU001', 'SKU002', 'SKU001'],
            'sales': [100, 150, 200]
        })
        
        validator = DataValidator()
        result = validator.validate_dataset(
            df, 
            'sales',
            business_key=['date', 'store_id', 'sku_id']
        )
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_dataset_with_missing_values(self):
        """Test validation with missing values"""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', np.nan],
            'store_id': ['S001', 'S001', 'S002'],
            'sku_id': ['SKU001', 'SKU002', 'SKU001'],
            'sales': [100, 150, 200]
        })
        
        validator = DataValidator()
        result = validator.validate_dataset(df, 'sales')
        
        assert len(result.warnings) > 0
        assert 'missing values' in result.warnings[0].lower()
    
    def test_dataset_with_duplicates(self):
        """Test validation with duplicates"""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-01', '2024-01-01'],
            'store_id': ['S001', 'S001', 'S002'],
            'sku_id': ['SKU001', 'SKU001', 'SKU001'],
            'sales': [100, 150, 200]
        })
        
        validator = DataValidator()
        result = validator.validate_dataset(
            df,
            'sales',
            business_key=['date', 'store_id', 'sku_id']
        )
        
        # Should have business key duplicate error
        assert len(result.errors) > 0
        assert any('duplicate business keys' in e.lower() for e in result.errors)
    
    def test_dataset_with_negative_sales(self):
        """Test validation with negative sales"""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'store_id': ['S001', 'S001', 'S002'],
            'sku_id': ['SKU001', 'SKU002', 'SKU001'],
            'sales': [100, -50, 200]
        })
        
        validator = DataValidator()
        result = validator.validate_dataset(df, 'sales')
        
        assert len(result.errors) > 0
        assert any('negative' in e.lower() for e in result.errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
