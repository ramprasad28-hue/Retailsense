"""
File upload handler with security validation and safe storage
"""
import os
import hashlib
import pandas as pd
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class FileUploadHandler:
    """Handles file uploads with security validation"""
    
    # Security settings
    ALLOWED_EXTENSIONS = {'.csv'}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
    UPLOAD_BASE_DIR = os.path.join("data", "raw")
    PROCESSED_BASE_DIR = os.path.join("data", "processed")
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize file handler
        
        Args:
            base_dir: Base directory for the project (defaults to current working directory)
        """
        if base_dir is None:
            # Get project root (3 levels up from this file)
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.base_dir = base_dir
        self.upload_dir = os.path.join(base_dir, self.UPLOAD_BASE_DIR)
        self.processed_dir = os.path.join(base_dir, self.PROCESSED_BASE_DIR)
        
        # Create directories if they don't exist
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
    
    def validate_file_security(self, filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        Validate file for security issues
        
        Returns:
            (is_valid, error_message)
        """
        # Check file size
        if file_size > self.MAX_FILE_SIZE:
            return False, f"File size ({file_size / (1024*1024):.1f} MB) exceeds maximum allowed size ({self.MAX_FILE_SIZE / (1024*1024):.0f} MB)"
        
        if file_size == 0:
            return False, "File is empty"
        
        # Check file extension
        _, ext = os.path.splitext(filename.lower())
        if ext not in self.ALLOWED_EXTENSIONS:
            return False, f"File type '{ext}' not allowed. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}"
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False, "Invalid filename: path traversal detected"
        
        # Check for suspicious characters
        if not re.match(r'^[\w\-. ]+$', filename):
            return False, "Invalid filename: contains suspicious characters"
        
        return True, None
    
    def generate_safe_filename(self, original_filename: str, dataset_type: str) -> str:
        """
        Generate a safe, unique filename
        
        Format: {dataset_type}_{timestamp}_{hash}.csv
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create a short hash of the original filename for uniqueness
        hash_obj = hashlib.md5(original_filename.encode())
        short_hash = hash_obj.hexdigest()[:8]
        
        safe_filename = f"{dataset_type}_{timestamp}_{short_hash}.csv"
        
        return safe_filename
    
    def save_uploaded_file(
        self,
        file_content: bytes,
        original_filename: str,
        dataset_type: str
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Save uploaded file securely
        
        Returns:
            (success, error_message, file_info)
            file_info contains: {
                'stored_filename': str,
                'file_path': str,
                'file_size': int,
                'original_filename': str
            }
        """
        try:
            # Validate security
            file_size = len(file_content)
            is_valid, error = self.validate_file_security(original_filename, file_size)
            
            if not is_valid:
                return False, error, None
            
            # Generate safe filename
            safe_filename = self.generate_safe_filename(original_filename, dataset_type)
            file_path = os.path.join(self.upload_dir, safe_filename)
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"Saved file: {safe_filename} ({file_size} bytes)")
            
            file_info = {
                'stored_filename': safe_filename,
                'file_path': file_path,
                'file_size': file_size,
                'original_filename': original_filename
            }
            
            return True, None, file_info
        
        except Exception as e:
            logger.error(f"Error saving file: {e}", exc_info=True)
            return False, f"Failed to save file: {str(e)}", None
    
    def read_csv_file(self, file_path: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Safely read CSV file
        
        Returns:
            (dataframe, error_message)
        """
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            
            df = None
            last_error = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    logger.info(f"Successfully read CSV with {encoding} encoding: {len(df)} rows, {len(df.columns)} columns")
                    break
                except UnicodeDecodeError:
                    last_error = f"Encoding {encoding} failed"
                    continue
                except Exception as e:
                    last_error = str(e)
                    break
            
            if df is None:
                return None, f"Failed to read CSV file: {last_error}"
            
            # Basic validation
            if df.empty:
                return None, "CSV file is empty"
            
            if len(df.columns) == 0:
                return None, "CSV file has no columns"
            
            return df, None
        
        except Exception as e:
            logger.error(f"Error reading CSV: {e}", exc_info=True)
            return None, f"Error reading CSV file: {str(e)}"
    
    def save_processed_file(
        self,
        df: pd.DataFrame,
        original_stored_filename: str,
        suffix: str = "cleaned"
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Save processed/cleaned dataset
        
        Returns:
            (success, error_message, file_path)
        """
        try:
            # Generate filename for processed file
            base_name = os.path.splitext(original_stored_filename)[0]
            processed_filename = f"{base_name}_{suffix}.csv"
            processed_path = os.path.join(self.processed_dir, processed_filename)
            
            # Save to CSV
            df.to_csv(processed_path, index=False)
            
            logger.info(f"Saved processed file: {processed_filename}")
            
            return True, None, processed_path
        
        except Exception as e:
            logger.error(f"Error saving processed file: {e}", exc_info=True)
            return False, f"Failed to save processed file: {str(e)}", None
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a file"""
        try:
            if not os.path.exists(file_path):
                return {"error": "File not found"}
            
            stat_info = os.stat(file_path)
            
            return {
                "path": file_path,
                "filename": os.path.basename(file_path),
                "size": stat_info.st_size,
                "size_mb": round(stat_info.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "exists": True
            }
        except Exception as e:
            return {"error": str(e), "exists": False}
    
    def delete_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Safely delete a file
        
        Returns:
            (success, error_message)
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
                return True, None
            else:
                return False, "File not found"
        except Exception as e:
            logger.error(f"Error deleting file: {e}", exc_info=True)
            return False, f"Failed to delete file: {str(e)}"
