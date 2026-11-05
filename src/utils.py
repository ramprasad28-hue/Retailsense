"""
Utility functions for RetailSense
"""
import numpy as np
import pandas as pd
from typing import Any
import json


def convert_numpy_types(obj: Any) -> Any:
    """
    Convert NumPy/Pandas types to Python native types for JSON serialization.
    
    This function recursively converts:
    - numpy.int64 -> int
    - numpy.float64 -> float  
    - numpy.bool_ -> bool
    - pandas NaT/NaN -> None
    - numpy arrays -> lists
    - pandas Series -> lists (WARNING: should only be called on scalars)
    
    Args:
        obj: Any object that might contain NumPy/Pandas types
    
    Returns:
        Object with all NumPy/Pandas types converted to Python native types
    """
    # Handle None early
    if obj is None:
        return None
    
    # Handle dictionaries
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    
    # Handle lists and tuples
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    
    # Handle NumPy arrays first (before scalar check)
    elif isinstance(obj, np.ndarray):
        return [convert_numpy_types(item) for item in obj.tolist()]
    
    # Handle pandas Series (convert to list)
    elif isinstance(obj, pd.Series):
        return [convert_numpy_types(item) for item in obj.tolist()]
    
    # Check if it's a pandas NA type (must come before NumPy type checks)
    elif hasattr(pd, 'isna') and not isinstance(obj, (dict, list, tuple, np.ndarray, pd.Series)):
        try:
            if pd.isna(obj):
                return None
        except (ValueError, TypeError):
            # pd.isna() might fail on some types, just continue
            pass
    
    # Handle NumPy integer types
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    
    # Handle NumPy floating point types
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    
    # Handle NumPy boolean type
    elif isinstance(obj, np.bool_):
        return bool(obj)
    
    # Return as-is for other types (str, int, float, bool, etc.)
    else:
        return obj


def json_dumps_safe(obj: Any, **kwargs) -> str:
    """
    Safe JSON dumps that handles NumPy/Pandas types.
    
    Args:
        obj: Object to serialize
        **kwargs: Additional arguments for json.dumps
    
    Returns:
        JSON string
    """
    converted_obj = convert_numpy_types(obj)
    return json.dumps(converted_obj, **kwargs)


def prepare_for_json_column(obj: Any) -> Any:
    """
    Prepare an object for storage in a SQLAlchemy JSON column.
    Converts all NumPy/Pandas types to Python native types.
    
    Args:
        obj: Object to prepare
        
    Returns:
        Object safe for JSON serialization
    """
    return convert_numpy_types(obj)
