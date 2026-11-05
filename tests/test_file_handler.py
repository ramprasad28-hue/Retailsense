"""
Tests for file upload handler
"""
import pytest
import os
import tempfile
import pandas as pd

from src.data.file_handler import FileUploadHandler


class TestFileUploadHandler:
    """Tests for file upload security and handling"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.handler = FileUploadHandler(base_dir=self.temp_dir)
    
    def test_validate_file_security_valid_csv(self):
        """Test security validation for valid CSV file"""
        is_valid, error = self.handler.validate_file_security('test.csv', 1024)
        
        assert is_valid
        assert error is None
    
    def test_validate_file_security_invalid_extension(self):
        """Test rejection of invalid file extensions"""
        is_valid, error = self.handler.validate_file_security('test.exe', 1024)
        
        assert not is_valid
        assert 'not allowed' in error.lower()
    
    def test_validate_file_security_too_large(self):
        """Test rejection of oversized files"""
        large_size = 200 * 1024 * 1024  # 200 MB
        is_valid, error = self.handler.validate_file_security('test.csv', large_size)
        
        assert not is_valid
        assert 'exceeds maximum' in error.lower()
    
    def test_validate_file_security_empty_file(self):
        """Test rejection of empty files"""
        is_valid, error = self.handler.validate_file_security('test.csv', 0)
        
        assert not is_valid
        assert 'empty' in error.lower()
    
    def test_validate_file_security_path_traversal(self):
        """Test detection of path traversal attempts"""
        is_valid, error = self.handler.validate_file_security('../../../test.csv', 1024)
        
        assert not is_valid
        # Path traversal should be caught
        assert ('path traversal' in error.lower() or 'invalid filename' in error.lower())
    
    def test_generate_safe_filename(self):
        """Test safe filename generation"""
        filename = self.handler.generate_safe_filename('test file.csv', 'sales')
        
        assert filename.startswith('sales_')
        assert filename.endswith('.csv')
        assert '..' not in filename
        assert '/' not in filename
        assert '\\' not in filename
    
    def test_save_uploaded_file(self):
        """Test saving uploaded file"""
        content = b"date,store_id,sku_id,sales\n2024-01-01,S001,SKU001,100"
        
        success, error, file_info = self.handler.save_uploaded_file(
            content, 'test.csv', 'sales'
        )
        
        assert success
        assert error is None
        assert file_info is not None
        assert 'stored_filename' in file_info
        assert 'file_path' in file_info
        assert os.path.exists(file_info['file_path'])
    
    def test_save_uploaded_file_invalid(self):
        """Test rejection of invalid file"""
        content = b"test"
        
        success, error, file_info = self.handler.save_uploaded_file(
            content, 'test.exe', 'sales'
        )
        
        assert not success
        assert error is not None
        assert file_info is None
    
    def test_read_csv_file(self):
        """Test reading CSV file"""
        # Create a test CSV file
        test_data = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'store_id': ['S001', 'S002'],
            'sku_id': ['SKU001', 'SKU002'],
            'sales': [100, 200]
        })
        
        test_file = os.path.join(self.temp_dir, 'test.csv')
        test_data.to_csv(test_file, index=False)
        
        df, error = self.handler.read_csv_file(test_file)
        
        assert df is not None
        assert error is None
        assert len(df) == 2
        assert 'date' in df.columns
    
    def test_read_csv_file_not_found(self):
        """Test reading non-existent file"""
        df, error = self.handler.read_csv_file('nonexistent.csv')
        
        assert df is None
        assert error is not None
    
    def test_get_file_info(self):
        """Test getting file information"""
        # Create a test file
        test_file = os.path.join(self.temp_dir, 'test.csv')
        with open(test_file, 'w') as f:
            f.write("test content")
        
        info = self.handler.get_file_info(test_file)
        
        assert info['exists']
        assert 'size' in info
        assert 'filename' in info
        assert info['filename'] == 'test.csv'
    
    def teardown_method(self):
        """Cleanup test environment"""
        # Clean up temp directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
