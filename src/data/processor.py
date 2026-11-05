"""
Data processing pipeline for standardization and cleaning
Handles schema standardization, type conversion, and data cleaning
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import logging

from src.data.schemas import SchemaRegistry, DatasetSchema
from src.data.validation import DataValidator, ValidationResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchemaStandardizer:
    """Standardizes dataset columns according to schema definitions"""
    
    @staticmethod
    def standardize_columns(df: pd.DataFrame, schema: DatasetSchema) -> Tuple[pd.DataFrame, Dict[str, str], List[str], List[str]]:
        """
        Standardize column names according to schema
        
        Returns:
            - Standardized dataframe
            - Mapping of original -> standard column names
            - List of missing required columns
            - List of unexpected columns
        """
        column_mapping = {}
        missing_columns = []
        unexpected_columns = []
        
        # Create a copy to avoid modifying original
        df_standardized = df.copy()
        
        # Build mapping from original to standardized names
        original_columns = df.columns.tolist()
        standardized_columns = []
        
        for orig_col in original_columns:
            std_col = schema.standardize_column_name(orig_col)
            if std_col:
                column_mapping[orig_col] = std_col
                standardized_columns.append(std_col)
            else:
                unexpected_columns.append(orig_col)
        
        # Rename columns
        if column_mapping:
            df_standardized.rename(columns=column_mapping, inplace=True)
        
        # Check for missing required columns
        required_columns = schema.get_required_columns()
        current_columns = df_standardized.columns.tolist()
        
        for req_col in required_columns:
            if req_col not in current_columns:
                missing_columns.append(req_col)
        
        return df_standardized, column_mapping, missing_columns, unexpected_columns
    
    @staticmethod
    def convert_data_types(df: pd.DataFrame, schema: DatasetSchema) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Convert columns to appropriate data types based on schema
        
        Returns:
            - DataFrame with converted types
            - Dictionary of conversion issues
        """
        df_converted = df.copy()
        conversion_issues = {}
        
        for col_def in schema.columns:
            col_name = col_def.name
            
            if col_name not in df_converted.columns:
                continue
            
            try:
                if col_def.dtype == "datetime64[ns]":
                    # Convert to datetime
                    df_converted[col_name] = pd.to_datetime(df_converted[col_name], errors='coerce')
                    
                    # Check for failed conversions
                    null_count = df_converted[col_name].isna().sum()
                    original_null_count = df[col_name].isna().sum()
                    
                    if null_count > original_null_count:
                        conversion_issues[col_name] = {
                            "type": "datetime",
                            "failed_conversions": int(null_count - original_null_count),
                            "message": f"{null_count - original_null_count} values could not be converted to datetime"
                        }
                
                elif col_def.dtype == "float64":
                    # Convert to float
                    df_converted[col_name] = pd.to_numeric(df_converted[col_name], errors='coerce')
                    
                    # Check for failed conversions
                    null_count = df_converted[col_name].isna().sum()
                    original_null_count = df[col_name].isna().sum()
                    
                    if null_count > original_null_count:
                        conversion_issues[col_name] = {
                            "type": "numeric",
                            "failed_conversions": int(null_count - original_null_count),
                            "message": f"{null_count - original_null_count} values could not be converted to numeric"
                        }
                
                elif col_def.dtype == "object":
                    # Convert to string
                    df_converted[col_name] = df_converted[col_name].astype(str)
                    # Replace 'nan' string with actual NaN
                    df_converted[col_name] = df_converted[col_name].replace('nan', np.nan)
            
            except Exception as e:
                conversion_issues[col_name] = {
                    "type": "error",
                    "message": f"Failed to convert column: {str(e)}"
                }
                logger.error(f"Error converting column {col_name}: {e}")
        
        return df_converted, conversion_issues


class DataCleaner:
    """Cleans data by handling duplicates and basic quality issues"""
    
    @staticmethod
    def remove_exact_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """
        Remove exact duplicate rows
        
        Returns:
            - Cleaned dataframe
            - Count of removed duplicates
        """
        original_count = len(df)
        df_cleaned = df.drop_duplicates()
        removed_count = original_count - len(df_cleaned)
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} exact duplicate rows")
        
        return df_cleaned.reset_index(drop=True), removed_count
    
    @staticmethod
    def handle_missing_values(df: pd.DataFrame, strategy: str = "keep") -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        Handle missing values based on strategy
        
        Strategies:
            - 'keep': Keep all rows (default)
            - 'drop': Drop rows with any missing values
            - 'drop_critical': Drop rows with missing values in critical columns
        
        Returns:
            - Cleaned dataframe
            - Dictionary of rows removed per column
        """
        df_cleaned = df.copy()
        removal_log = {}
        
        if strategy == "drop":
            original_count = len(df_cleaned)
            df_cleaned = df_cleaned.dropna()
            removed_count = original_count - len(df_cleaned)
            removal_log["total"] = removed_count
            logger.info(f"Dropped {removed_count} rows with missing values")
        
        elif strategy == "drop_critical":
            # For now, just keep all data
            # In production, this would drop rows with missing critical fields
            pass
        
        return df_cleaned.reset_index(drop=True), removal_log
    
    @staticmethod
    def normalize_boolean_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        Normalize boolean/binary columns to consistent format (0/1)
        Handles: Yes/No, True/False, 1/0, Y/N
        """
        df_normalized = df.copy()
        
        for col in columns:
            if col not in df_normalized.columns:
                continue
            
            # Convert to string first
            df_normalized[col] = df_normalized[col].astype(str).str.strip().str.lower()
            
            # Map various representations to 0/1
            boolean_map = {
                'yes': 1, 'no': 0,
                'true': 1, 'false': 0,
                'y': 1, 'n': 0,
                '1': 1, '0': 0,
                '1.0': 1, '0.0': 0,
                'nan': 0
            }
            
            df_normalized[col] = df_normalized[col].map(boolean_map)
            
            # Fill any unmapped values with 0
            df_normalized[col] = df_normalized[col].fillna(0).astype(int)
        
        return df_normalized


class DataProcessor:
    """Main data processing pipeline orchestrator"""
    
    def __init__(self):
        self.standardizer = SchemaStandardizer()
        self.cleaner = DataCleaner()
        self.validator = DataValidator()
    
    def process_dataset(
        self,
        df: pd.DataFrame,
        dataset_type: str,
        auto_clean: bool = True
    ) -> Dict[str, Any]:
        """
        Complete processing pipeline for a dataset
        
        Steps:
        1. Schema validation and standardization
        2. Data type conversion
        3. Data validation
        4. Data cleaning (if auto_clean=True)
        5. Final validation
        
        Args:
            df: Input dataframe
            dataset_type: Type of dataset
            auto_clean: Whether to automatically clean data
        
        Returns:
            Dictionary containing:
                - success: Boolean indicating overall success
                - standardized_df: Dataframe with standardized columns
                - cleaned_df: Cleaned dataframe (if auto_clean=True)
                - column_mapping: Original to standard column mapping
                - validation_result: Initial validation results
                - final_validation_result: Post-cleaning validation results
                - processing_stats: Statistics about processing
                - errors: List of critical errors
                - warnings: List of warnings
        """
        result = {
            "success": False,
            "standardized_df": None,
            "cleaned_df": None,
            "column_mapping": {},
            "validation_result": None,
            "final_validation_result": None,
            "processing_stats": {},
            "errors": [],
            "warnings": []
        }
        
        try:
            # Get schema for dataset type
            schema = SchemaRegistry.get_schema(dataset_type)
            if not schema:
                result["errors"].append(f"Unknown dataset type: {dataset_type}")
                return result
            
            logger.info(f"Processing {dataset_type} dataset with {len(df)} rows, {len(df.columns)} columns")
            
            # Step 1: Standardize column names
            df_standardized, column_mapping, missing_cols, unexpected_cols = \
                self.standardizer.standardize_columns(df, schema)
            
            result["column_mapping"] = column_mapping
            result["standardized_df"] = df_standardized
            
            # Check for missing required columns
            if missing_cols:
                result["errors"].append(f"Missing required columns: {', '.join(missing_cols)}")
                return result
            
            if unexpected_cols:
                result["warnings"].append(f"Unexpected columns (will be ignored): {', '.join(unexpected_cols)}")
            
            # Step 2: Convert data types
            df_converted, conversion_issues = \
                self.standardizer.convert_data_types(df_standardized, schema)
            
            if conversion_issues:
                result["warnings"].append(f"Data type conversion issues in {len(conversion_issues)} columns")
                result["processing_stats"]["conversion_issues"] = conversion_issues
            
            # Step 3: Normalize boolean columns if applicable
            if dataset_type in ["promotions", "calendar"]:
                boolean_columns = []
                if dataset_type == "promotions":
                    boolean_columns = ["promotion"]
                elif dataset_type == "calendar":
                    boolean_columns = ["holiday"]
                
                df_converted = self.cleaner.normalize_boolean_columns(df_converted, boolean_columns)
            
            # Step 4: Validate data
            validation_result = self.validator.validate_dataset(
                df_converted,
                dataset_type,
                business_key=schema.business_key
            )
            
            result["validation_result"] = validation_result
            result["errors"].extend(validation_result.errors)
            result["warnings"].extend(validation_result.warnings)
            
            # Step 5: Auto-clean if requested
            if auto_clean:
                df_cleaned = df_converted.copy()
                cleaning_stats = {}
                
                # Remove exact duplicates
                df_cleaned, dup_count = self.cleaner.remove_exact_duplicates(df_cleaned)
                cleaning_stats["removed_exact_duplicates"] = dup_count
                
                # For now, keep missing values (production would have more sophisticated handling)
                # df_cleaned, missing_stats = self.cleaner.handle_missing_values(df_cleaned, strategy="keep")
                
                result["cleaned_df"] = df_cleaned
                result["processing_stats"]["cleaning"] = cleaning_stats
                
                # Step 6: Final validation on cleaned data
                final_validation = self.validator.validate_dataset(
                    df_cleaned,
                    dataset_type,
                    business_key=schema.business_key
                )
                
                result["final_validation_result"] = final_validation
                
                logger.info(f"Processing complete: {len(df_cleaned)} rows in cleaned dataset")
            else:
                result["cleaned_df"] = df_converted
            
            # Processing statistics
            result["processing_stats"].update({
                "original_rows": len(df),
                "original_columns": len(df.columns),
                "standardized_columns": len(df_standardized.columns),
                "final_rows": len(result["cleaned_df"]),
                "columns_mapped": len(column_mapping),
                "columns_removed": len(unexpected_cols)
            })
            
            # Success if no critical errors
            result["success"] = len([e for e in result["errors"] if "Missing required columns" in e]) == 0
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing dataset: {e}", exc_info=True)
            result["errors"].append(f"Processing failed: {str(e)}")
            return result
    
    def validate_file_before_processing(self, df: pd.DataFrame, dataset_type: str) -> Dict[str, Any]:
        """
        Quick validation before full processing
        Checks basic requirements without modifying data
        
        Returns:
            Dictionary with validation status and messages
        """
        validation = {
            "can_process": True,
            "issues": []
        }
        
        # Check if dataframe is empty
        if df.empty:
            validation["can_process"] = False
            validation["issues"].append("Dataset is empty")
            return validation
        
        # Check column count
        if len(df.columns) == 0:
            validation["can_process"] = False
            validation["issues"].append("No columns found in dataset")
            return validation
        
        # Get schema
        schema = SchemaRegistry.get_schema(dataset_type)
        if not schema:
            validation["can_process"] = False
            validation["issues"].append(f"Unknown dataset type: {dataset_type}")
            return validation
        
        # Check if we can map to required columns
        required_cols = schema.get_required_columns()
        mappable_cols = []
        
        for req_col in required_cols:
            for orig_col in df.columns:
                std_col = schema.standardize_column_name(orig_col)
                if std_col == req_col:
                    mappable_cols.append(req_col)
                    break
        
        missing = set(required_cols) - set(mappable_cols)
        if missing:
            validation["can_process"] = False
            validation["issues"].append(f"Cannot map required columns: {', '.join(missing)}")
        
        return validation
