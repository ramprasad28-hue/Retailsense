"""
Data validation service for quality checks
Implements missing value detection, duplicate detection, outlier detection, and data integrity checks
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from src.utils import convert_numpy_types


@dataclass
class ValidationResult:
    """Container for validation results"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]


class MissingValueAnalyzer:
    """Analyzes missing values in datasets"""
    
    @staticmethod
    def analyze(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze missing values in the dataframe
        Returns detailed metrics about missing values
        """
        total_cells = df.shape[0] * df.shape[1]
        total_missing = df.isnull().sum().sum()
        missing_percentage = (total_missing / total_cells * 100) if total_cells > 0 else 0
        
        # Per-column analysis
        column_analysis = {}
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            # Ensure missing_count is a scalar
            if isinstance(missing_count, pd.Series):
                missing_count = missing_count.iloc[0] if len(missing_count) > 0 else 0
            col_percentage = (missing_count / len(df) * 100) if len(df) > 0 else 0
            
            column_analysis[col] = {
                "missing_count": int(missing_count),
                "missing_percentage": round(col_percentage, 2),
                "total_rows": len(df)
            }
        
        result = {
            "total_missing_values": int(total_missing),
            "total_cells": int(total_cells),
            "missing_percentage": round(missing_percentage, 2),
            "columns_with_missing": [
                col for col, stats in column_analysis.items() 
                if stats["missing_count"] > 0
            ],
            "column_details": column_analysis
        }
        
        return result
    
    @staticmethod
    def get_handling_strategy(missing_percentage: float) -> str:
        """Recommend handling strategy based on missing percentage"""
        if missing_percentage == 0:
            return "No missing values"
        elif missing_percentage < 5:
            return "Low missing rate - consider imputation or forward fill"
        elif missing_percentage < 20:
            return "Moderate missing rate - investigate patterns, consider imputation"
        else:
            return "High missing rate - investigate data quality, may need to exclude or collect new data"


class DuplicateDetector:
    """Detects duplicate records"""
    
    @staticmethod
    def detect_exact_duplicates(df: pd.DataFrame) -> Dict[str, Any]:
        """Detect completely duplicate rows"""
        duplicate_mask = df.duplicated()
        num_duplicates = duplicate_mask.sum()
        
        result = {
            "exact_duplicate_count": int(num_duplicates),
            "duplicate_percentage": round((num_duplicates / len(df) * 100) if len(df) > 0 else 0, 2),
            "unique_rows": len(df) - int(num_duplicates),
            "total_rows": len(df)
        }
        
        return result
    
    @staticmethod
    def detect_business_key_duplicates(df: pd.DataFrame, business_key: List[str]) -> Dict[str, Any]:
        """
        Detect duplicates based on business key columns
        Business key duplicates indicate data integrity issues
        """
        # Check if all business key columns exist
        missing_keys = [key for key in business_key if key not in df.columns]
        if missing_keys:
            return {
                "business_key_duplicate_count": 0,
                "error": f"Missing business key columns: {missing_keys}"
            }
        
        # Find duplicates based on business key
        duplicate_mask = df.duplicated(subset=business_key, keep=False)
        num_duplicates = duplicate_mask.sum()
        
        # Get duplicate groups for detailed analysis
        duplicate_groups = []
        if num_duplicates > 0:
            duplicated_df = df[duplicate_mask].copy()
            grouped = duplicated_df.groupby(business_key)
            
            # Sample first few duplicate groups
            for name, group in list(grouped)[:5]:
                duplicate_groups.append({
                    "key": str(name),
                    "count": len(group),
                    "sample_indices": group.index.tolist()[:3]
                })
        
        result = {
            "business_key": business_key,
            "business_key_duplicate_count": int(num_duplicates),
            "duplicate_percentage": round((num_duplicates / len(df) * 100) if len(df) > 0 else 0, 2),
            "unique_combinations": len(df) - int(num_duplicates),
            "duplicate_groups_sample": duplicate_groups
        }
        
        return result
    
    @staticmethod
    def remove_exact_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Remove exact duplicate rows, keeping the first occurrence
        Returns cleaned dataframe and count of removed rows
        """
        original_count = len(df)
        df_cleaned = df.drop_duplicates()
        removed_count = original_count - len(df_cleaned)
        
        return df_cleaned, removed_count


class OutlierDetector:
    """Detects outliers using statistical methods"""
    
    @staticmethod
    def detect_iqr_outliers(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Detect outliers using Interquartile Range (IQR) method
        Outliers are values below Q1 - 1.5*IQR or above Q3 + 1.5*IQR
        """
        if columns is None:
            # Auto-detect numeric columns
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        outlier_details = {}
        total_outliers = 0
        
        for col in columns:
            if col not in df.columns:
                continue
            
            # Skip if column is not numeric
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue
            
            # Calculate IQR
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            # Define outlier boundaries
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Identify outliers
            outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            num_outliers = outlier_mask.sum()
            total_outliers += num_outliers
            
            if num_outliers > 0:
                outlier_details[col] = {
                    "count": int(num_outliers),
                    "percentage": round((num_outliers / len(df) * 100) if len(df) > 0 else 0, 2),
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound),
                    "Q1": float(Q1),
                    "Q3": float(Q3),
                    "IQR": float(IQR),
                    "min_outlier": float(df[col][outlier_mask].min()) if num_outliers > 0 else None,
                    "max_outlier": float(df[col][outlier_mask].max()) if num_outliers > 0 else None
                }
        
        result = {
            "method": "IQR",
            "total_outliers": int(total_outliers),
            "columns_with_outliers": list(outlier_details.keys()),
            "outlier_details": outlier_details,
            "recommendation": OutlierDetector._get_outlier_recommendation(total_outliers, len(df))
        }
        
        return result
    
    @staticmethod
    def _get_outlier_recommendation(outlier_count: int, total_rows: int) -> str:
        """Provide recommendation based on outlier analysis"""
        if outlier_count == 0:
            return "No outliers detected"
        
        percentage = (outlier_count / total_rows * 100) if total_rows > 0 else 0
        
        if percentage < 1:
            return "Few outliers detected - review individually, may be genuine extreme values"
        elif percentage < 5:
            return "Moderate outliers - investigate patterns, consider capping or transformation"
        else:
            return "High outlier rate - investigate data collection process and quality"


class DataIntegrityChecker:
    """Checks data integrity constraints"""
    
    @staticmethod
    def check_negative_values(df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
        """Check for negative values in columns that should be non-negative"""
        issues = {}
        total_negative = 0
        
        for col in columns:
            if col not in df.columns:
                continue
            
            if pd.api.types.is_numeric_dtype(df[col]):
                negative_mask = df[col] < 0
                num_negative = negative_mask.sum()
                
                if num_negative > 0:
                    total_negative += num_negative
                    issues[col] = {
                        "count": int(num_negative),
                        "percentage": round((num_negative / len(df) * 100) if len(df) > 0 else 0, 2),
                        "min_value": float(df[col].min()),
                        "sample_indices": df[negative_mask].index.tolist()[:5]
                    }
        
        return {
            "total_negative_values": int(total_negative),
            "columns_affected": list(issues.keys()),
            "details": issues
        }
    
    @staticmethod
    def check_date_validity(df: pd.DataFrame, date_columns: List[str]) -> Dict[str, Any]:
        """Check for invalid dates"""
        issues = {}
        
        for col in date_columns:
            if col not in df.columns:
                continue
            
            # Try to convert to datetime if not already
            try:
                if not pd.api.types.is_datetime64_any_dtype(df[col]):
                    temp_dates = pd.to_datetime(df[col], errors='coerce')
                else:
                    temp_dates = df[col]
                
                # Check for NaT (invalid dates after conversion)
                invalid_mask = temp_dates.isna()
                num_invalid = invalid_mask.sum()
                
                if num_invalid > 0:
                    issues[col] = {
                        "count": int(num_invalid),
                        "percentage": round((num_invalid / len(df) * 100) if len(df) > 0 else 0, 2),
                        "sample_invalid_values": df[col][invalid_mask].head(5).tolist()
                    }
                
            except Exception as e:
                issues[col] = {
                    "error": f"Failed to validate dates: {str(e)}"
                }
        
        return {
            "columns_checked": date_columns,
            "columns_with_issues": list(issues.keys()),
            "details": issues
        }
    
    @staticmethod
    def check_empty_identifiers(df: pd.DataFrame, id_columns: List[str]) -> Dict[str, Any]:
        """Check for empty or null identifier columns"""
        issues = {}
        
        for col in id_columns:
            if col not in df.columns:
                continue
            
            # Check for null values
            null_mask = df[col].isna()
            num_null = null_mask.sum()
            
            # Check for empty strings
            empty_mask = df[col].astype(str).str.strip() == ''
            num_empty = empty_mask.sum()
            
            total_invalid = num_null + num_empty
            
            if total_invalid > 0:
                issues[col] = {
                    "null_count": int(num_null),
                    "empty_count": int(num_empty),
                    "total_invalid": int(total_invalid),
                    "percentage": round((total_invalid / len(df) * 100) if len(df) > 0 else 0, 2)
                }
        
        return {
            "columns_checked": id_columns,
            "columns_with_issues": list(issues.keys()),
            "details": issues
        }
    
    @staticmethod
    def check_invalid_prices(df: pd.DataFrame, price_column: str = 'price') -> Dict[str, Any]:
        """Check for invalid prices (negative, zero, extremely high)"""
        if price_column not in df.columns:
            return {"error": f"Column '{price_column}' not found"}
        
        if not pd.api.types.is_numeric_dtype(df[price_column]):
            return {"error": f"Column '{price_column}' is not numeric"}
        
        issues = {}
        
        # Check for negative prices
        negative_mask = df[price_column] < 0
        num_negative = negative_mask.sum()
        if num_negative > 0:
            issues["negative_prices"] = {
                "count": int(num_negative),
                "min_value": float(df[price_column][negative_mask].min())
            }
        
        # Check for zero prices (warning, not necessarily error)
        zero_mask = df[price_column] == 0
        num_zero = zero_mask.sum()
        if num_zero > 0:
            issues["zero_prices"] = {
                "count": int(num_zero),
                "note": "Zero prices may be valid for promotions or free items"
            }
        
        # Check for extremely high prices (potential data entry errors)
        # Define "extremely high" as > 99.9th percentile * 10
        if len(df) > 100:
            percentile_99_9 = df[price_column].quantile(0.999)
            extreme_threshold = percentile_99_9 * 10
            extreme_mask = df[price_column] > extreme_threshold
            num_extreme = extreme_mask.sum()
            
            if num_extreme > 0:
                issues["extremely_high_prices"] = {
                    "count": int(num_extreme),
                    "threshold": float(extreme_threshold),
                    "max_value": float(df[price_column][extreme_mask].max()),
                    "note": "Unusually high prices detected - verify data entry"
                }
        
        return {
            "column": price_column,
            "total_rows": len(df),
            "issues_found": len(issues) > 0,
            "details": issues
        }


class DataValidator:
    """Main validator class that orchestrates all validation checks"""
    
    def __init__(self):
        self.missing_analyzer = MissingValueAnalyzer()
        self.duplicate_detector = DuplicateDetector()
        self.outlier_detector = OutlierDetector()
        self.integrity_checker = DataIntegrityChecker()
    
    def validate_dataset(
        self, 
        df: pd.DataFrame, 
        dataset_type: str,
        business_key: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Perform comprehensive validation on a dataset
        
        Args:
            df: DataFrame to validate
            dataset_type: Type of dataset (sales, inventory, etc.)
            business_key: List of columns that form the business key
        
        Returns:
            ValidationResult object with all validation metrics
        """
        errors = []
        warnings = []
        metrics = {}
        
        # 1. Missing Value Analysis
        missing_analysis = self.missing_analyzer.analyze(df)
        metrics["missing_values"] = missing_analysis
        
        if missing_analysis["total_missing_values"] > 0:
            warnings.append(
                f"Found {missing_analysis['total_missing_values']} missing values "
                f"({missing_analysis['missing_percentage']}% of total cells)"
            )
        
        # 2. Duplicate Detection - Exact Duplicates
        exact_dup_analysis = self.duplicate_detector.detect_exact_duplicates(df)
        metrics["exact_duplicates"] = exact_dup_analysis
        
        if exact_dup_analysis["exact_duplicate_count"] > 0:
            warnings.append(
                f"Found {exact_dup_analysis['exact_duplicate_count']} exact duplicate rows"
            )
        
        # 3. Business Key Duplicate Detection
        if business_key:
            bk_dup_analysis = self.duplicate_detector.detect_business_key_duplicates(df, business_key)
            metrics["business_key_duplicates"] = bk_dup_analysis
            
            if bk_dup_analysis.get("business_key_duplicate_count", 0) > 0:
                errors.append(
                    f"Found {bk_dup_analysis['business_key_duplicate_count']} records with duplicate business keys "
                    f"({', '.join(business_key)}). This indicates data integrity issues."
                )
        
        # 4. Outlier Detection
        outlier_analysis = self.outlier_detector.detect_iqr_outliers(df)
        metrics["outliers"] = outlier_analysis
        
        if outlier_analysis["total_outliers"] > 0:
            warnings.append(
                f"Detected {outlier_analysis['total_outliers']} outliers across "
                f"{len(outlier_analysis['columns_with_outliers'])} columns"
            )
        
        # 5. Data Integrity Checks - Dataset-specific
        integrity_issues = self._check_dataset_specific_integrity(df, dataset_type)
        metrics["data_integrity"] = integrity_issues
        
        # Add errors and warnings from integrity checks
        if integrity_issues.get("errors"):
            errors.extend(integrity_issues["errors"])
        if integrity_issues.get("warnings"):
            warnings.extend(integrity_issues["warnings"])
        
        # Determine overall validation status
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metrics=metrics
        )
    
    def _check_dataset_specific_integrity(self, df: pd.DataFrame, dataset_type: str) -> Dict[str, Any]:
        """Perform dataset-specific integrity checks"""
        issues = {
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        # Sales dataset checks
        if dataset_type == "sales":
            # Check for negative sales
            neg_check = self.integrity_checker.check_negative_values(df, ["sales"])
            if neg_check["total_negative_values"] > 0:
                issues["errors"].append(
                    f"Found {neg_check['total_negative_values']} negative sales values"
                )
                issues["details"]["negative_sales"] = neg_check
            
            # Check date validity
            date_check = self.integrity_checker.check_date_validity(df, ["date"])
            if date_check["columns_with_issues"]:
                issues["errors"].append("Found invalid dates in sales data")
                issues["details"]["invalid_dates"] = date_check
            
            # Check for empty identifiers
            id_check = self.integrity_checker.check_empty_identifiers(df, ["store_id", "sku_id"])
            if id_check["columns_with_issues"]:
                issues["errors"].append("Found empty or null identifiers")
                issues["details"]["empty_identifiers"] = id_check
        
        # Inventory dataset checks
        elif dataset_type == "inventory":
            neg_check = self.integrity_checker.check_negative_values(df, ["stock_quantity"])
            if neg_check["total_negative_values"] > 0:
                issues["warnings"].append(
                    f"Found {neg_check['total_negative_values']} negative stock quantities - "
                    "may indicate backorders"
                )
                issues["details"]["negative_stock"] = neg_check
            
            id_check = self.integrity_checker.check_empty_identifiers(df, ["store_id", "sku_id"])
            if id_check["columns_with_issues"]:
                issues["errors"].append("Found empty or null identifiers")
                issues["details"]["empty_identifiers"] = id_check
        
        # Prices dataset checks
        elif dataset_type == "prices":
            price_check = self.integrity_checker.check_invalid_prices(df, "price")
            if price_check.get("issues_found"):
                issues["warnings"].append("Found pricing anomalies")
                issues["details"]["price_issues"] = price_check
            
            date_check = self.integrity_checker.check_date_validity(df, ["date"])
            if date_check["columns_with_issues"]:
                issues["errors"].append("Found invalid dates in price data")
                issues["details"]["invalid_dates"] = date_check
        
        # Supplier dataset checks
        elif dataset_type == "supplier":
            neg_check = self.integrity_checker.check_negative_values(df, ["lead_time"])
            if neg_check["total_negative_values"] > 0:
                issues["errors"].append(
                    f"Found {neg_check['total_negative_values']} negative lead time values"
                )
                issues["details"]["negative_lead_time"] = neg_check
        
        # Calendar dataset checks
        elif dataset_type == "calendar":
            date_check = self.integrity_checker.check_date_validity(df, ["date"])
            if date_check["columns_with_issues"]:
                issues["errors"].append("Found invalid dates in calendar data")
                issues["details"]["invalid_dates"] = date_check
        
        # Master data checks (store_master, product_master)
        elif dataset_type in ["store_master", "product_master", "promotions"]:
            id_columns = []
            if dataset_type == "store_master":
                id_columns = ["store_id"]
            elif dataset_type == "product_master":
                id_columns = ["sku_id"]
            
            if id_columns:
                id_check = self.integrity_checker.check_empty_identifiers(df, id_columns)
                if id_check["columns_with_issues"]:
                    issues["errors"].append("Found empty or null identifiers in master data")
                    issues["details"]["empty_identifiers"] = id_check
        
        return issues
