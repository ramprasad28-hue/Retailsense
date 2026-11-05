"""
Main data ingestion service - orchestrates the entire pipeline
"""
import time
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from src.data.file_handler import FileUploadHandler
from src.data.processor import DataProcessor
from src.data.report_generator import ReportGenerator
from src.database import get_db_session, UploadedDataset, ValidationMetrics
from src.utils import prepare_for_json_column

logger = logging.getLogger(__name__)


class DataIngestionService:
    """Main service for data ingestion and validation pipeline"""
    
    def __init__(self):
        self.file_handler = FileUploadHandler()
        self.processor = DataProcessor()
        self.report_generator = ReportGenerator()
    
    def ingest_dataset(
        self,
        file_content: bytes,
        original_filename: str,
        dataset_type: str
    ) -> Dict[str, Any]:
        """
        Complete ingestion pipeline:
        1. Save uploaded file
        2. Read and validate CSV
        3. Process and validate data
        4. Save cleaned data
        5. Generate report
        6. Store metadata in database
        
        Args:
            file_content: Bytes content of uploaded file
            original_filename: Original filename
            dataset_type: Type of dataset
        
        Returns:
            Dictionary with results including dataset_id, success status, and paths
        """
        start_time = time.time()
        result = {
            "success": False,
            "dataset_id": None,
            "errors": [],
            "warnings": []
        }
        
        db_session = get_db_session()
        dataset_record = None
        
        try:
            # Step 1: Save uploaded file
            logger.info(f"Starting ingestion for {original_filename} ({dataset_type})")
            
            save_success, save_error, file_info = self.file_handler.save_uploaded_file(
                file_content, original_filename, dataset_type
            )
            
            if not save_success:
                result["errors"].append(save_error)
                return result
            
            # Create database record
            dataset_record = UploadedDataset(
                dataset_type=dataset_type,
                original_filename=original_filename,
                stored_filename=file_info["stored_filename"],
                file_size=file_info["file_size"],
                upload_timestamp=datetime.utcnow(),
                processing_status="uploaded",
                raw_file_path=file_info["file_path"]
            )
            db_session.add(dataset_record)
            db_session.commit()
            
            result["dataset_id"] = dataset_record.id
            logger.info(f"Created dataset record with ID: {dataset_record.id}")
            
            # Step 2: Read CSV file
            dataset_record.processing_status = "validating"
            db_session.commit()
            
            df, read_error = self.file_handler.read_csv_file(file_info["file_path"])
            
            if df is None:
                result["errors"].append(read_error)
                dataset_record.processing_status = "failed"
                dataset_record.error_message = read_error
                db_session.commit()
                return result
            
            logger.info(f"Read CSV: {len(df)} rows, {len(df.columns)} columns")
            
            # Quick pre-validation
            pre_validation = self.processor.validate_file_before_processing(df, dataset_type)
            if not pre_validation["can_process"]:
                error_msg = "; ".join(pre_validation["issues"])
                result["errors"].append(error_msg)
                dataset_record.processing_status = "failed"
                dataset_record.error_message = error_msg
                db_session.commit()
                return result
            
            # Step 3: Process and validate data
            processing_result = self.processor.process_dataset(
                df, dataset_type, auto_clean=True
            )
            
            # Update dataset record with processing results
            dataset_record.total_rows = processing_result.get("processing_stats", {}).get("original_rows", len(df))
            dataset_record.total_columns = processing_result.get("processing_stats", {}).get("original_columns", len(df.columns))
            
            # Extract validation metrics
            final_validation = processing_result.get("final_validation_result") or processing_result.get("validation_result")
            
            if final_validation:
                metrics = final_validation.metrics
                
                # Missing values
                missing_info = metrics.get("missing_values", {})
                dataset_record.missing_value_count = missing_info.get("total_missing_values", 0)
                
                # Duplicates
                dup_info = metrics.get("exact_duplicates", {})
                dataset_record.duplicate_count = dup_info.get("exact_duplicate_count", 0)
                
                # Outliers
                outlier_info = metrics.get("outliers", {})
                dataset_record.outlier_count = outlier_info.get("total_outliers", 0)
                
                # Integrity issues
                integrity_info = metrics.get("data_integrity", {})
                dataset_record.invalid_record_count = len(integrity_info.get("errors", []))
                
                # Validation status
                dataset_record.validation_passed = 1 if final_validation.is_valid else -1
                
                # Store detailed validation data (convert NumPy types for JSON serialization)
                dataset_record.validation_errors = prepare_for_json_column(processing_result.get("errors", []))
                dataset_record.validation_warnings = prepare_for_json_column(processing_result.get("warnings", []))
                dataset_record.column_mapping = prepare_for_json_column(processing_result.get("column_mapping", {}))
                dataset_record.data_quality_report = prepare_for_json_column(metrics)
            
            result["errors"].extend(processing_result.get("errors", []))
            result["warnings"].extend(processing_result.get("warnings", []))
            
            # Step 4: Save cleaned dataset
            if processing_result.get("cleaned_df") is not None:
                save_success, save_error, cleaned_path = self.file_handler.save_processed_file(
                    processing_result["cleaned_df"],
                    file_info["stored_filename"],
                    suffix="cleaned"
                )
                
                if save_success:
                    dataset_record.cleaned_file_path = cleaned_path
                    logger.info(f"Saved cleaned dataset: {cleaned_path}")
                else:
                    result["warnings"].append(f"Failed to save cleaned dataset: {save_error}")
            
            # Step 5: Generate validation report
            dataset_info = {
                "original_filename": original_filename,
                "stored_filename": file_info["stored_filename"],
                "dataset_type": dataset_type,
                "file_size": file_info["file_size"],
                "upload_timestamp": dataset_record.upload_timestamp.isoformat()
            }
            
            report_result = self.report_generator.generate_validation_report(
                dataset_info, processing_result, format="json"
            )
            
            if report_result.get("success"):
                dataset_record.report_file_path = report_result.get("file_path")
                logger.info(f"Generated validation report: {report_result.get('file_path')}")
            
            # Step 6: Store detailed validation metrics (convert NumPy types for JSON serialization)
            if final_validation:
                metrics = final_validation.metrics
                
                validation_metrics = ValidationMetrics(
                    dataset_id=dataset_record.id,
                    missing_values_detail=prepare_for_json_column(metrics.get("missing_values", {})),
                    exact_duplicates=metrics.get("exact_duplicates", {}).get("exact_duplicate_count", 0),
                    business_key_duplicates=metrics.get("business_key_duplicates", {}).get("business_key_duplicate_count", 0),
                    duplicate_details=prepare_for_json_column(metrics.get("business_key_duplicates", {})),
                    outliers_by_column=prepare_for_json_column(metrics.get("outliers", {}).get("outlier_details", {})),
                    outlier_method="IQR",
                    negative_values=prepare_for_json_column(metrics.get("data_integrity", {}).get("details", {}).get("negative_sales", {})),
                    invalid_dates=prepare_for_json_column(metrics.get("data_integrity", {}).get("details", {}).get("invalid_dates", {})),
                    invalid_identifiers=prepare_for_json_column(metrics.get("data_integrity", {}).get("details", {}).get("empty_identifiers", {})),
                    missing_columns=prepare_for_json_column(processing_result.get("missing_columns", [])),
                    unexpected_columns=prepare_for_json_column(processing_result.get("unexpected_columns", [])),
                    type_mismatches=prepare_for_json_column(processing_result.get("processing_stats", {}).get("conversion_issues", {}))
                )
                db_session.add(validation_metrics)
            
            # Final status update
            if processing_result.get("success") and len(result["errors"]) == 0:
                dataset_record.processing_status = "cleaned"
                result["success"] = True
            else:
                dataset_record.processing_status = "validated" if len(result["errors"]) == 0 else "failed"
                if not result["success"] and len(result["errors"]) == 0:
                    result["success"] = True  # Success with warnings
            
            # Calculate processing time
            processing_time = time.time() - start_time
            dataset_record.processing_time = processing_time
            
            db_session.commit()
            
            logger.info(f"Ingestion complete for dataset {dataset_record.id} in {processing_time:.2f}s")
            
            result["dataset_record"] = dataset_record
            result["processing_result"] = processing_result
            result["cleaned_file_path"] = dataset_record.cleaned_file_path
            result["report_file_path"] = dataset_record.report_file_path
            
            return result
        
        except Exception as e:
            logger.error(f"Error in ingestion pipeline: {e}", exc_info=True)
            result["errors"].append(f"Ingestion failed: {str(e)}")
            
            if dataset_record:
                dataset_record.processing_status = "failed"
                dataset_record.error_message = str(e)
                db_session.commit()
            
            return result
        
        finally:
            db_session.close()
    
    def get_dataset_by_id(self, dataset_id: int) -> Optional[UploadedDataset]:
        """Retrieve dataset record by ID"""
        db_session = get_db_session()
        try:
            return db_session.query(UploadedDataset).filter(UploadedDataset.id == dataset_id).first()
        finally:
            db_session.close()
    
    def get_all_datasets(self) -> list:
        """Retrieve all dataset records"""
        db_session = get_db_session()
        try:
            return db_session.query(UploadedDataset).order_by(UploadedDataset.upload_timestamp.desc()).all()
        finally:
            db_session.close()
    
    def delete_dataset(self, dataset_id: int) -> tuple[bool, Optional[str]]:
        """Delete dataset and associated files"""
        db_session = get_db_session()
        try:
            dataset = db_session.query(UploadedDataset).filter(UploadedDataset.id == dataset_id).first()
            
            if not dataset:
                return False, "Dataset not found"
            
            # Delete files
            if dataset.raw_file_path:
                self.file_handler.delete_file(dataset.raw_file_path)
            if dataset.cleaned_file_path:
                self.file_handler.delete_file(dataset.cleaned_file_path)
            if dataset.report_file_path:
                self.file_handler.delete_file(dataset.report_file_path)
            
            # Delete validation metrics
            db_session.query(ValidationMetrics).filter(ValidationMetrics.dataset_id == dataset_id).delete()
            
            # Delete dataset record
            db_session.delete(dataset)
            db_session.commit()
            
            logger.info(f"Deleted dataset {dataset_id}")
            return True, None
        
        except Exception as e:
            logger.error(f"Error deleting dataset: {e}", exc_info=True)
            db_session.rollback()
            return False, str(e)
        
        finally:
            db_session.close()
