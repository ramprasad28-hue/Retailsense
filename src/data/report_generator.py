"""
Validation report generator
Generates detailed reports in various formats (JSON, CSV, HTML)
"""
import pandas as pd
import json
from typing import Dict, Any, Optional
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates validation reports in various formats"""
    
    REPORTS_DIR = os.path.join("reports")
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize report generator
        
        Args:
            base_dir: Base directory for the project
        """
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.base_dir = base_dir
        self.reports_dir = os.path.join(base_dir, self.REPORTS_DIR)
        
        # Create reports directory if it doesn't exist
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate_validation_report(
        self,
        dataset_info: Dict[str, Any],
        processing_result: Dict[str, Any],
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive validation report
        
        Args:
            dataset_info: Information about the dataset (filename, type, etc.)
            processing_result: Result from DataProcessor.process_dataset()
            format: Report format (json, csv, or dict)
        
        Returns:
            Dictionary with report data and file path (if saved)
        """
        try:
            # Build report structure
            report = self._build_report_structure(dataset_info, processing_result)
            
            # Save report based on format
            if format == "json":
                file_path = self._save_json_report(report, dataset_info.get("stored_filename", "unknown"))
                return {"success": True, "report": report, "file_path": file_path, "format": "json"}
            
            elif format == "csv":
                file_path = self._save_csv_report(report, dataset_info.get("stored_filename", "unknown"))
                return {"success": True, "report": report, "file_path": file_path, "format": "csv"}
            
            else:  # dict/in-memory
                return {"success": True, "report": report, "format": "dict"}
        
        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _build_report_structure(
        self,
        dataset_info: Dict[str, Any],
        processing_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build comprehensive report structure"""
        
        validation_result = processing_result.get("validation_result")
        final_validation = processing_result.get("final_validation_result")
        processing_stats = processing_result.get("processing_stats", {})
        
        # Use final validation if available, otherwise use initial validation
        active_validation = final_validation if final_validation else validation_result
        
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_version": "1.0"
            },
            "dataset_info": {
                "original_filename": dataset_info.get("original_filename", "Unknown"),
                "stored_filename": dataset_info.get("stored_filename", "Unknown"),
                "dataset_type": dataset_info.get("dataset_type", "Unknown"),
                "file_size_bytes": dataset_info.get("file_size", 0),
                "file_size_mb": round(dataset_info.get("file_size", 0) / (1024 * 1024), 2),
                "upload_timestamp": dataset_info.get("upload_timestamp", datetime.now().isoformat())
            },
            "processing_summary": {
                "status": "success" if processing_result.get("success") else "failed",
                "original_rows": processing_stats.get("original_rows", 0),
                "original_columns": processing_stats.get("original_columns", 0),
                "final_rows": processing_stats.get("final_rows", 0),
                "final_columns": processing_stats.get("standardized_columns", 0),
                "rows_removed": processing_stats.get("original_rows", 0) - processing_stats.get("final_rows", 0)
            },
            "column_mapping": {
                "mapped_columns": processing_result.get("column_mapping", {}),
                "columns_mapped_count": len(processing_result.get("column_mapping", {})),
                "columns_removed": processing_stats.get("columns_removed", 0)
            },
            "data_quality_summary": {},
            "validation_details": {},
            "errors": processing_result.get("errors", []),
            "warnings": processing_result.get("warnings", []),
            "recommendations": []
        }
        
        # Add validation details if available
        if active_validation:
            metrics = active_validation.metrics
            
            # Missing values summary
            missing_info = metrics.get("missing_values", {})
            report["data_quality_summary"]["missing_values"] = {
                "total_count": missing_info.get("total_missing_values", 0),
                "percentage": missing_info.get("missing_percentage", 0),
                "columns_affected": len(missing_info.get("columns_with_missing", []))
            }
            report["validation_details"]["missing_values"] = missing_info
            
            # Duplicates summary
            exact_dup = metrics.get("exact_duplicates", {})
            report["data_quality_summary"]["duplicates"] = {
                "exact_duplicate_count": exact_dup.get("exact_duplicate_count", 0),
                "duplicate_percentage": exact_dup.get("duplicate_percentage", 0)
            }
            report["validation_details"]["exact_duplicates"] = exact_dup
            
            # Business key duplicates
            if "business_key_duplicates" in metrics:
                bk_dup = metrics["business_key_duplicates"]
                report["data_quality_summary"]["business_key_duplicates"] = {
                    "count": bk_dup.get("business_key_duplicate_count", 0),
                    "percentage": bk_dup.get("duplicate_percentage", 0)
                }
                report["validation_details"]["business_key_duplicates"] = bk_dup
            
            # Outliers summary
            outlier_info = metrics.get("outliers", {})
            report["data_quality_summary"]["outliers"] = {
                "total_count": outlier_info.get("total_outliers", 0),
                "columns_affected": len(outlier_info.get("columns_with_outliers", []))
            }
            report["validation_details"]["outliers"] = outlier_info
            
            # Data integrity
            integrity_info = metrics.get("data_integrity", {})
            report["validation_details"]["data_integrity"] = integrity_info
        
        # Add recommendations
        report["recommendations"] = self._generate_recommendations(report)
        
        # Overall validation status
        report["validation_status"] = {
            "passed": active_validation.is_valid if active_validation else False,
            "total_errors": len(report["errors"]),
            "total_warnings": len(report["warnings"]),
            "critical_issues": len([e for e in report["errors"] if "Missing required" in e or "duplicate business keys" in e])
        }
        
        return report
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> list:
        """Generate actionable recommendations based on report"""
        recommendations = []
        
        quality = report.get("data_quality_summary", {})
        
        # Missing values recommendations
        missing = quality.get("missing_values", {})
        if missing.get("percentage", 0) > 0:
            if missing["percentage"] < 5:
                recommendations.append({
                    "category": "missing_values",
                    "severity": "low",
                    "message": f"Low missing value rate ({missing['percentage']}%). Consider forward fill or interpolation for time series data."
                })
            elif missing["percentage"] < 20:
                recommendations.append({
                    "category": "missing_values",
                    "severity": "medium",
                    "message": f"Moderate missing value rate ({missing['percentage']}%). Investigate patterns and consider appropriate imputation strategies."
                })
            else:
                recommendations.append({
                    "category": "missing_values",
                    "severity": "high",
                    "message": f"High missing value rate ({missing['percentage']}%). Review data collection process. Consider excluding incomplete records or collecting new data."
                })
        
        # Duplicate recommendations
        duplicates = quality.get("duplicates", {})
        if duplicates.get("exact_duplicate_count", 0) > 0:
            recommendations.append({
                "category": "duplicates",
                "severity": "medium",
                "message": f"Found {duplicates['exact_duplicate_count']} exact duplicate rows. These have been automatically removed in the cleaned dataset."
            })
        
        # Business key duplicates (critical)
        bk_dup = quality.get("business_key_duplicates", {})
        if bk_dup.get("count", 0) > 0:
            recommendations.append({
                "category": "data_integrity",
                "severity": "critical",
                "message": f"Found {bk_dup['count']} records with duplicate business keys. This indicates data quality issues. Review data source and deduplication logic."
            })
        
        # Outliers recommendations
        outliers = quality.get("outliers", {})
        if outliers.get("total_count", 0) > 0:
            recommendations.append({
                "category": "outliers",
                "severity": "low",
                "message": f"Detected {outliers['total_count']} outliers. Review to determine if they are genuine extreme values or data errors. Consider capping or transformation if appropriate."
            })
        
        # Overall data quality
        if report.get("validation_status", {}).get("passed"):
            recommendations.append({
                "category": "overall",
                "severity": "info",
                "message": "Dataset passed validation. Ready for use in downstream processing (feature engineering, forecasting)."
            })
        else:
            recommendations.append({
                "category": "overall",
                "severity": "critical",
                "message": "Dataset failed validation. Address critical errors before proceeding to next module."
            })
        
        return recommendations
    
    def _save_json_report(self, report: Dict[str, Any], stored_filename: str) -> str:
        """Save report as JSON file"""
        try:
            base_name = os.path.splitext(stored_filename)[0]
            report_filename = f"{base_name}_validation_report.json"
            report_path = os.path.join(self.reports_dir, report_filename)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Saved JSON report: {report_filename}")
            return report_path
        
        except Exception as e:
            logger.error(f"Error saving JSON report: {e}")
            raise
    
    def _save_csv_report(self, report: Dict[str, Any], stored_filename: str) -> str:
        """Save report as CSV file (flattened structure)"""
        try:
            base_name = os.path.splitext(stored_filename)[0]
            report_filename = f"{base_name}_validation_report.csv"
            report_path = os.path.join(self.reports_dir, report_filename)
            
            # Flatten report for CSV format
            rows = []
            
            # Dataset info
            rows.append(["Section", "Metric", "Value"])
            rows.append(["", "", ""])
            rows.append(["DATASET INFORMATION", "", ""])
            for key, value in report["dataset_info"].items():
                rows.append(["Dataset Info", key, str(value)])
            
            rows.append(["", "", ""])
            rows.append(["PROCESSING SUMMARY", "", ""])
            for key, value in report["processing_summary"].items():
                rows.append(["Processing", key, str(value)])
            
            rows.append(["", "", ""])
            rows.append(["DATA QUALITY SUMMARY", "", ""])
            for category, metrics in report["data_quality_summary"].items():
                if isinstance(metrics, dict):
                    for key, value in metrics.items():
                        rows.append(["Data Quality", f"{category}.{key}", str(value)])
                else:
                    rows.append(["Data Quality", category, str(metrics)])
            
            rows.append(["", "", ""])
            rows.append(["VALIDATION STATUS", "", ""])
            for key, value in report["validation_status"].items():
                rows.append(["Validation", key, str(value)])
            
            rows.append(["", "", ""])
            rows.append(["ERRORS", "", ""])
            for i, error in enumerate(report["errors"], 1):
                rows.append(["Errors", f"Error {i}", error])
            
            rows.append(["", "", ""])
            rows.append(["WARNINGS", "", ""])
            for i, warning in enumerate(report["warnings"], 1):
                rows.append(["Warnings", f"Warning {i}", warning])
            
            rows.append(["", "", ""])
            rows.append(["RECOMMENDATIONS", "", ""])
            for i, rec in enumerate(report["recommendations"], 1):
                rows.append(["Recommendations", f"{rec['severity'].upper()}", rec["message"]])
            
            # Save to CSV
            df = pd.DataFrame(rows)
            df.to_csv(report_path, index=False, header=False)
            
            logger.info(f"Saved CSV report: {report_filename}")
            return report_path
        
        except Exception as e:
            logger.error(f"Error saving CSV report: {e}")
            raise
    
    def create_summary_report(self, all_datasets: list) -> pd.DataFrame:
        """
        Create summary report for multiple datasets
        
        Args:
            all_datasets: List of dataset records from database
        
        Returns:
            DataFrame with summary statistics
        """
        summary_data = []
        
        for dataset in all_datasets:
            summary_data.append({
                "Dataset Type": dataset.dataset_type,
                "Original Filename": dataset.original_filename,
                "Upload Date": dataset.upload_timestamp.strftime("%Y-%m-%d %H:%M:%S") if dataset.upload_timestamp else "N/A",
                "Status": dataset.processing_status,
                "Total Rows": dataset.total_rows or 0,
                "Total Columns": dataset.total_columns or 0,
                "Missing Values": dataset.missing_value_count or 0,
                "Duplicates": dataset.duplicate_count or 0,
                "Outliers": dataset.outlier_count or 0,
                "Invalid Records": dataset.invalid_record_count or 0,
                "Validation": "Passed" if dataset.validation_passed == 1 else "Failed" if dataset.validation_passed == -1 else "Pending"
            })
        
        return pd.DataFrame(summary_data)
