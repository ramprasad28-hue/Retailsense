"""
Tests for schema definitions and column standardization
"""
import pytest
import pandas as pd

from src.data.schemas import (
    SchemaRegistry,
    SalesSchema,
    InventorySchema,
    PricesSchema,
    CalendarSchema
)


class TestSchemaRegistry:
    """Tests for schema registry"""
    
    def test_get_all_types(self):
        """Test getting all supported dataset types"""
        types = SchemaRegistry.get_all_types()
        
        assert 'sales' in types
        assert 'inventory' in types
        assert 'prices' in types
        assert 'promotions' in types
        assert 'calendar' in types
        assert 'store_master' in types
        assert 'product_master' in types
        assert 'supplier' in types
        assert len(types) == 8
    
    def test_get_schema(self):
        """Test retrieving schema by type"""
        schema = SchemaRegistry.get_schema('sales')
        assert schema is not None
        assert isinstance(schema, SalesSchema)
        
        schema = SchemaRegistry.get_schema('invalid_type')
        assert schema is None
    
    def test_get_type_display_names(self):
        """Test display names"""
        display_names = SchemaRegistry.get_type_display_names()
        
        assert display_names['sales'] == 'Sales Dataset'
        assert display_names['inventory'] == 'Inventory Dataset'


class TestSalesSchema:
    """Tests for sales schema"""
    
    def test_required_columns(self):
        """Test required columns"""
        schema = SalesSchema()
        required = schema.get_required_columns()
        
        assert 'date' in required
        assert 'store_id' in required
        assert 'sku_id' in required
        assert 'sales' in required
    
    def test_column_standardization(self):
        """Test column name standardization"""
        schema = SalesSchema()
        
        # Exact match
        assert schema.standardize_column_name('date') == 'date'
        assert schema.standardize_column_name('store_id') == 'store_id'
        
        # Alternative names
        assert schema.standardize_column_name('Store ID') == 'store_id'
        assert schema.standardize_column_name('StoreID') == 'store_id'
        assert schema.standardize_column_name('SKU') == 'sku_id'
        assert schema.standardize_column_name('sales_qty') == 'sales'
        
        # Unknown column
        assert schema.standardize_column_name('unknown_column') is None
    
    def test_business_key(self):
        """Test business key definition"""
        schema = SalesSchema()
        
        assert schema.business_key == ['date', 'store_id', 'sku_id']


class TestInventorySchema:
    """Tests for inventory schema"""
    
    def test_required_columns(self):
        """Test required columns"""
        schema = InventorySchema()
        required = schema.get_required_columns()
        
        assert 'store_id' in required
        assert 'sku_id' in required
        assert 'stock_quantity' in required
    
    def test_column_standardization(self):
        """Test column name standardization"""
        schema = InventorySchema()
        
        assert schema.standardize_column_name('stock') == 'stock_quantity'
        assert schema.standardize_column_name('inventory') == 'stock_quantity'
        assert schema.standardize_column_name('stock_qty') == 'stock_quantity'


class TestPricesSchema:
    """Tests for prices schema"""
    
    def test_required_columns(self):
        """Test required columns"""
        schema = PricesSchema()
        required = schema.get_required_columns()
        
        assert 'date' in required
        assert 'store_id' in required
        assert 'sku_id' in required
        assert 'price' in required
    
    def test_column_standardization(self):
        """Test column name standardization"""
        schema = PricesSchema()
        
        assert schema.standardize_column_name('unit_price') == 'price'
        assert schema.standardize_column_name('selling_price') == 'price'


class TestCalendarSchema:
    """Tests for calendar schema"""
    
    def test_required_columns(self):
        """Test required columns"""
        schema = CalendarSchema()
        required = schema.get_required_columns()
        
        assert 'date' in required
        assert 'holiday' in required
        # holiday_name is optional
    
    def test_optional_columns(self):
        """Test optional columns"""
        schema = CalendarSchema()
        
        # Find holiday_name column
        holiday_name_col = None
        for col in schema.columns:
            if col.name == 'holiday_name':
                holiday_name_col = col
                break
        
        assert holiday_name_col is not None
        assert not holiday_name_col.required


class TestColumnValidation:
    """Tests for column value validation"""
    
    def test_min_value_validation(self):
        """Test minimum value validation"""
        schema = SalesSchema()
        
        # Sales should be >= 0
        is_valid, error = schema.validate_column_value('sales', 100)
        assert is_valid
        
        is_valid, error = schema.validate_column_value('sales', -10)
        assert not is_valid
        assert 'below minimum' in error.lower()
    
    def test_nullable_validation(self):
        """Test nullable field validation"""
        schema = SalesSchema()
        
        # Required field with null value
        is_valid, error = schema.validate_column_value('sales', None)
        assert not is_valid
        assert 'cannot be null' in error.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
