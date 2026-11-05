"""
Dataset schema definitions and validation rules for RetailSense Module 1
Each schema defines required columns, data types, and validation rules
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class ColumnSchema:
    """Definition for a single column"""
    name: str
    dtype: str  # pandas dtype
    required: bool = True
    nullable: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    description: str = ""


class DatasetSchema:
    """Base class for dataset schemas"""
    
    def __init__(self, dataset_type: str, columns: List[ColumnSchema], business_key: List[str]):
        self.dataset_type = dataset_type
        self.columns = columns
        self.business_key = business_key  # Columns that form unique business key
        self.column_map = {col.name.lower(): col for col in columns}
        self.alternative_names = {}  # Maps alternative names to standard names
    
    def get_required_columns(self) -> List[str]:
        """Get list of required column names"""
        return [col.name for col in self.columns if col.required]
    
    def get_column_names(self) -> List[str]:
        """Get list of all column names"""
        return [col.name for col in self.columns]
    
    def standardize_column_name(self, col_name: str) -> Optional[str]:
        """Convert alternative column names to standard format"""
        # Try exact match first
        normalized = col_name.lower().strip()
        if normalized in self.column_map:
            return self.column_map[normalized].name
        
        # Try alternative names
        if normalized in self.alternative_names:
            return self.alternative_names[normalized]
        
        # Try removing special characters and spaces
        cleaned = re.sub(r'[^a-z0-9]', '', normalized)
        for std_name, col in self.column_map.items():
            if re.sub(r'[^a-z0-9]', '', std_name) == cleaned:
                return col.name
        
        return None
    
    def validate_column_value(self, col_name: str, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a single value against column constraints
        Returns (is_valid, error_message)
        """
        col = self.column_map.get(col_name.lower())
        if not col:
            return True, None
        
        # Check nullable
        if value is None or (isinstance(value, float) and value != value):  # NaN check
            if not col.nullable:
                return False, f"{col_name} cannot be null"
            return True, None
        
        # Check min/max for numeric values
        if col.min_value is not None:
            try:
                if float(value) < col.min_value:
                    return False, f"{col_name} value {value} is below minimum {col.min_value}"
            except (ValueError, TypeError):
                pass
        
        if col.max_value is not None:
            try:
                if float(value) > col.max_value:
                    return False, f"{col_name} value {value} exceeds maximum {col.max_value}"
            except (ValueError, TypeError):
                pass
        
        # Check pattern for string values
        if col.pattern and isinstance(value, str):
            if not re.match(col.pattern, value):
                return False, f"{col_name} value '{value}' does not match required pattern"
        
        return True, None


# ============================================================
# SALES DATASET SCHEMA
# ============================================================
class SalesSchema(DatasetSchema):
    """Schema for sales transaction data"""
    
    def __init__(self):
        columns = [
            ColumnSchema(
                name="date",
                dtype="datetime64[ns]",
                required=True,
                description="Transaction date"
            ),
            ColumnSchema(
                name="store_id",
                dtype="object",
                required=True,
                description="Store identifier"
            ),
            ColumnSchema(
                name="sku_id",
                dtype="object",
                required=True,
                description="Product SKU identifier"
            ),
            ColumnSchema(
                name="sales",
                dtype="float64",
                required=True,
                min_value=0,
                description="Sales quantity (units sold)"
            ),
        ]
        business_key = ["date", "store_id", "sku_id"]
        super().__init__("sales", columns, business_key)
        
        # Alternative column names
        self.alternative_names = {
            "transaction_date": "date",
            "sale_date": "date",
            "storeid": "store_id",
            "store": "store_id",
            "skuid": "sku_id",
            "sku": "sku_id",
            "product_id": "sku_id",
            "productid": "sku_id",
            "sales_qty": "sales",
            "salesqty": "sales",
            "sales_quantity": "sales",
            "salesquantity": "sales",
            "quantity": "sales",
            "qty": "sales",
            "units_sold": "sales",
            "unitssold": "sales",
        }


# ============================================================
# INVENTORY DATASET SCHEMA
# ============================================================
class InventorySchema(DatasetSchema):
    """Schema for inventory stock data"""
    
    def __init__(self):
        columns = [
            ColumnSchema(
                name="store_id",
                dtype="object",
                required=True,
                description="Store identifier"
            ),
            ColumnSchema(
                name="sku_id",
                dtype="object",
                required=True,
                description="Product SKU identifier"
            ),
            ColumnSchema(
                name="stock_quantity",
                dtype="float64",
                required=True,
                min_value=0,
                description="Current stock quantity"
            ),
        ]
        business_key = ["store_id", "sku_id"]
        super().__init__("inventory", columns, business_key)
        
        self.alternative_names = {
            "storeid": "store_id",
            "store": "store_id",
            "skuid": "sku_id",
            "sku": "sku_id",
            "product_id": "sku_id",
            "productid": "sku_id",
            "stock": "stock_quantity",
            "stock_qty": "stock_quantity",
            "quantity": "stock_quantity",
            "qty": "stock_quantity",
            "inventory": "stock_quantity",
            "inventory_level": "stock_quantity",
        }


# ============================================================
# PRICES DATASET SCHEMA
# ============================================================
class PricesSchema(DatasetSchema):
    """Schema for product pricing data"""
    
    def __init__(self):
        columns = [
            ColumnSchema(
                name="date",
                dtype="datetime64[ns]",
                required=True,
                description="Price effective date"
            ),
            ColumnSchema(
                name="store_id",
                dtype="object",
                required=True,
                description="Store identifier"
            ),
            ColumnSchema(
                name="sku_id",
                dtype="object",
                required=True,
                description="Product SKU identifier"
            ),
            ColumnSchema(
                name="price",
                dtype="float64",
                required=True,
                min_value=0,
                description="Product price"
            ),
        ]
        business_key = ["date", "store_id", "sku_id"]
        super().__init__("prices", columns, business_key)
        
        self.alternative_names = {
            "effective_date": "date",
            "price_date": "date",
            "storeid": "store_id",
            "store": "store_id",
            "skuid": "sku_id",
            "sku": "sku_id",
            "product_id": "sku_id",
            "productid": "sku_id",
            "unit_price": "price",
            "selling_price": "price",
            "retail_price": "price",
        }


# ============================================================
# PROMOTIONS DATASET SCHEMA
# ============================================================
class PromotionsSchema(DatasetSchema):
    """Schema for promotional activity data"""
    
    def __init__(self):
        columns = [
            ColumnSchema(
                name="date",
                dtype="datetime64[ns]",
                required=True,
                description="Promotion date"
            ),
            ColumnSchema(
                name="store_id",
                dtype="object",
                required=True,
                description="Store identifier"
            ),
            ColumnSchema(
                name="sku_id",
                dtype="object",
                required=True,
                description="Product SKU identifier"
            ),
            ColumnSchema(
                name="promotion",
                dtype="object",
                required=True,
                description="Promotion indicator (0/1, Yes/No, True/False)"
            ),
        ]
        business_key = ["date", "store_id", "sku_id"]
        super().__init__("promotions", columns, business_key)
        
        self.alternative_names = {
            "promo_date": "date",
            "promotion_date": "date",
            "storeid": "store_id",
            "store": "store_id",
            "skuid": "sku_id",
            "sku": "sku_id",
            "product_id": "sku_id",
            "productid": "sku_id",
            "promo": "promotion",
            "is_promotion": "promotion",
            "promo_flag": "promotion",
            "promotion_flag": "promotion",
            "on_promotion": "promotion",
        }


# ============================================================
# CALENDAR DATASET SCHEMA
# ============================================================
class CalendarSchema(DatasetSchema):
    """Schema for calendar and holiday data"""
    
    def __init__(self):
        columns = [
            ColumnSchema(
                name="date",
                dtype="datetime64[ns]",
                required=True,
                description="Calendar date"
            ),
            ColumnSchema(
                name="holiday",
                dtype="object",
                required=True,
                description="Holiday indicator (0/1, Yes/No, True/False)"
            ),
            ColumnSchema(
                name="holiday_name",
                dtype="object",
                required=False,
                nullable=True,
                description="Name of holiday (if applicable)"
            ),
        ]
        business_key = ["date"]
        super().__init__("calendar", columns, business_key)
        
        self.alternative_names = {
            "calendar_date": "date",
            "is_holiday": "holiday",
            "holiday_flag": "holiday",
            "holiday_indicator": "holiday",
            "holidayname": "holiday_name",
            "holiday_desc": "holiday_name",
            "holiday_description": "holiday_name",
        }


# ============================================================
# STORE MASTER DATASET SCHEMA
# ============================================================
class StoreMasterSchema(DatasetSchema):
    """Schema for store master data"""
    
    def __init__(self):
        columns = [
            ColumnSchema(
                name="store_id",
                dtype="object",
                required=True,
                description="Store identifier"
            ),
            ColumnSchema(
                name="store_type",
                dtype="object",
                required=True,
                description="Store type/category"
            ),
            ColumnSchema(
                name="location",
                dtype="object",
                required=True,
                description="Store location"
            ),
        ]
        business_key = ["store_id"]
        super().__init__("store_master", columns, business_key)
        
        self.alternative_names = {
            "storeid": "store_id",
            "store": "store_id",
            "storetype": "store_type",
            "store_category": "store_type",
            "type": "store_type",
            "store_location": "location",
            "city": "location",
            "region": "location",
        }


# ============================================================
# PRODUCT MASTER DATASET SCHEMA
# ============================================================
class ProductMasterSchema(DatasetSchema):
    """Schema for product master data"""
    
    def __init__(self):
        columns = [
            ColumnSchema(
                name="sku_id",
                dtype="object",
                required=True,
                description="Product SKU identifier"
            ),
            ColumnSchema(
                name="category",
                dtype="object",
                required=True,
                description="Product category"
            ),
            ColumnSchema(
                name="product_name",
                dtype="object",
                required=True,
                description="Product name/description"
            ),
        ]
        business_key = ["sku_id"]
        super().__init__("product_master", columns, business_key)
        
        self.alternative_names = {
            "skuid": "sku_id",
            "sku": "sku_id",
            "product_id": "sku_id",
            "productid": "sku_id",
            "product_category": "category",
            "productcategory": "category",
            "productname": "product_name",
            "product": "product_name",
            "name": "product_name",
            "description": "product_name",
            "product_description": "product_name",
        }


# ============================================================
# SUPPLIER / LEAD TIME DATASET SCHEMA
# ============================================================
class SupplierSchema(DatasetSchema):
    """Schema for supplier and lead time data"""
    
    def __init__(self):
        columns = [
            ColumnSchema(
                name="sku_id",
                dtype="object",
                required=True,
                description="Product SKU identifier"
            ),
            ColumnSchema(
                name="lead_time",
                dtype="float64",
                required=True,
                min_value=0,
                description="Lead time in days"
            ),
        ]
        business_key = ["sku_id"]
        super().__init__("supplier", columns, business_key)
        
        self.alternative_names = {
            "skuid": "sku_id",
            "sku": "sku_id",
            "product_id": "sku_id",
            "productid": "sku_id",
            "leadtime": "lead_time",
            "lead_time_days": "lead_time",
            "delivery_time": "lead_time",
            "supplier_lead_time": "lead_time",
        }


# ============================================================
# SCHEMA REGISTRY
# ============================================================
class SchemaRegistry:
    """Central registry for all dataset schemas"""
    
    _schemas = {
        "sales": SalesSchema(),
        "inventory": InventorySchema(),
        "prices": PricesSchema(),
        "promotions": PromotionsSchema(),
        "calendar": CalendarSchema(),
        "store_master": StoreMasterSchema(),
        "product_master": ProductMasterSchema(),
        "supplier": SupplierSchema(),
    }
    
    @classmethod
    def get_schema(cls, dataset_type: str) -> Optional[DatasetSchema]:
        """Get schema for a dataset type"""
        return cls._schemas.get(dataset_type.lower())
    
    @classmethod
    def get_all_types(cls) -> List[str]:
        """Get list of all supported dataset types"""
        return list(cls._schemas.keys())
    
    @classmethod
    def get_type_display_names(cls) -> Dict[str, str]:
        """Get display names for dataset types"""
        return {
            "sales": "Sales Dataset",
            "inventory": "Inventory Dataset",
            "prices": "Prices Dataset",
            "promotions": "Promotions Dataset",
            "calendar": "Calendar Dataset",
            "store_master": "Store Master Dataset",
            "product_master": "Product Master Dataset",
            "supplier": "Supplier / Lead Time Dataset",
        }
