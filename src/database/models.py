"""
Database models for RetailSense Module 1 - Data Ingestion and Validation
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON
from sqlalchemy.orm import declarative_base
import enum

# Create a single declarative base that will be shared across the application
Base = declarative_base()


class DatasetType(enum.Enum):
    """Enum for dataset types"""
    SALES = "sales"
    INVENTORY = "inventory"
    PRICES = "prices"
    PROMOTIONS = "promotions"
    CALENDAR = "calendar"
    STORE_MASTER = "store_master"
    PRODUCT_MASTER = "product_master"
    SUPPLIER = "supplier"


class ProcessingStatus(enum.Enum):
    """Enum for processing status"""
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    VALIDATED = "validated"
    FAILED = "failed"
    CLEANED = "cleaned"


class UploadedDataset(Base):
    """Model to track uploaded datasets"""
    __tablename__ = "uploaded_datasets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_type = Column(String(50), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_status = Column(String(50), default=ProcessingStatus.UPLOADED.value, nullable=False)
    
    # Dataset statistics
    total_rows = Column(Integer)
    total_columns = Column(Integer)
    
    # Validation results
    validation_passed = Column(Integer, default=0)  # 0=not validated, 1=passed, -1=failed
    missing_value_count = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    outlier_count = Column(Integer, default=0)
    invalid_record_count = Column(Integer, default=0)
    
    # File paths
    raw_file_path = Column(String(500))
    cleaned_file_path = Column(String(500))
    report_file_path = Column(String(500))
    
    # Validation details stored as JSON
    validation_errors = Column(JSON)
    validation_warnings = Column(JSON)
    column_mapping = Column(JSON)  # original -> standardized column names
    data_quality_report = Column(JSON)
    
    # Processing metadata
    processing_time = Column(Float)  # in seconds
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<UploadedDataset(id={self.id}, type={self.dataset_type}, status={self.processing_status})>"


class ValidationMetrics(Base):
    """Detailed validation metrics per dataset"""
    __tablename__ = "validation_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, nullable=False)  # FK to uploaded_datasets
    
    # Missing values breakdown per column
    missing_values_detail = Column(JSON)
    
    # Duplicate analysis
    exact_duplicates = Column(Integer, default=0)
    business_key_duplicates = Column(Integer, default=0)
    duplicate_details = Column(JSON)
    
    # Outlier analysis
    outliers_by_column = Column(JSON)
    outlier_method = Column(String(50), default="IQR")
    
    # Data integrity issues
    negative_values = Column(JSON)
    invalid_dates = Column(JSON)
    invalid_identifiers = Column(JSON)
    
    # Schema validation
    missing_columns = Column(JSON)
    unexpected_columns = Column(JSON)
    type_mismatches = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ValidationMetrics(id={self.id}, dataset_id={self.dataset_id})>"
