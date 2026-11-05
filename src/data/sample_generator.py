"""
Sample dataset generator for testing and demonstration
Creates realistic sample CSV files for all dataset types
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from src.data.schemas import SchemaRegistry

class SampleDatasetGenerator:
    """Generate sample datasets for testing and demonstration"""
    
    def __init__(self, output_dir: str = "data/external"):
        """
        Initialize generator
        
        Args:
            output_dir: Directory to save sample files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_sales_sample(self, num_rows: int = 1000) -> pd.DataFrame:
        """Generate sample sales dataset"""
        np.random.seed(42)
        
        start_date = datetime(2023, 1, 1)
        dates = [start_date + timedelta(days=i) for i in range(365)]
        
        stores = [f"S{str(i).zfill(3)}" for i in range(1, 11)]  # 10 stores
        skus = [f"SKU{str(i).zfill(4)}" for i in range(1, 51)]  # 50 products
        
        data = []
        for _ in range(num_rows):
            data.append({
                'date': np.random.choice(dates).strftime('%Y-%m-%d'),
                'store_id': np.random.choice(stores),
                'sku_id': np.random.choice(skus),
                'sales': np.random.poisson(50)  # Poisson distribution for sales
            })
        
        return pd.DataFrame(data)
    
    def generate_inventory_sample(self, num_rows: int = 500) -> pd.DataFrame:
        """Generate sample inventory dataset"""
        np.random.seed(42)
        
        stores = [f"S{str(i).zfill(3)}" for i in range(1, 11)]
        skus = [f"SKU{str(i).zfill(4)}" for i in range(1, 51)]
        
        data = []
        for store in stores:
            for sku in skus:
                data.append({
                    'store_id': store,
                    'sku_id': sku,
                    'stock_quantity': np.random.randint(0, 500)
                })
        
        return pd.DataFrame(data).sample(n=min(num_rows, len(data)), random_state=42)
    
    def generate_prices_sample(self, num_rows: int = 800) -> pd.DataFrame:
        """Generate sample prices dataset"""
        np.random.seed(42)
        
        start_date = datetime(2023, 1, 1)
        dates = [start_date + timedelta(days=i*7) for i in range(52)]  # Weekly prices
        
        stores = [f"S{str(i).zfill(3)}" for i in range(1, 11)]
        skus = [f"SKU{str(i).zfill(4)}" for i in range(1, 51)]
        
        data = []
        for _ in range(num_rows):
            base_price = np.random.uniform(10, 200)
            data.append({
                'date': np.random.choice(dates).strftime('%Y-%m-%d'),
                'store_id': np.random.choice(stores),
                'sku_id': np.random.choice(skus),
                'price': round(base_price, 2)
            })
        
        return pd.DataFrame(data)
    
    def generate_promotions_sample(self, num_rows: int = 500) -> pd.DataFrame:
        """Generate sample promotions dataset"""
        np.random.seed(42)
        
        start_date = datetime(2023, 1, 1)
        dates = [start_date + timedelta(days=i) for i in range(365)]
        
        stores = [f"S{str(i).zfill(3)}" for i in range(1, 11)]
        skus = [f"SKU{str(i).zfill(4)}" for i in range(1, 51)]
        
        data = []
        for _ in range(num_rows):
            data.append({
                'date': np.random.choice(dates).strftime('%Y-%m-%d'),
                'store_id': np.random.choice(stores),
                'sku_id': np.random.choice(skus),
                'promotion': np.random.choice([0, 1], p=[0.8, 0.2])  # 20% promotion rate
            })
        
        return pd.DataFrame(data)
    
    def generate_calendar_sample(self) -> pd.DataFrame:
        """Generate sample calendar dataset"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        dates = pd.date_range(start_date, end_date, freq='D')
        
        # Define some holidays
        holidays = {
            '2023-01-01': 'New Year',
            '2023-02-14': 'Valentine\'s Day',
            '2023-04-07': 'Good Friday',
            '2023-05-29': 'Memorial Day',
            '2023-07-04': 'Independence Day',
            '2023-09-04': 'Labor Day',
            '2023-11-23': 'Thanksgiving',
            '2023-12-25': 'Christmas',
            '2023-12-31': 'New Year\'s Eve'
        }
        
        data = []
        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            is_holiday = 1 if date_str in holidays else 0
            holiday_name = holidays.get(date_str, '')
            
            data.append({
                'date': date_str,
                'holiday': is_holiday,
                'holiday_name': holiday_name if holiday_name else None
            })
        
        return pd.DataFrame(data)
    
    def generate_store_master_sample(self) -> pd.DataFrame:
        """Generate sample store master dataset"""
        stores = [f"S{str(i).zfill(3)}" for i in range(1, 11)]
        
        store_types = ['Superstore', 'Hypermarket', 'Convenience', 'Department Store']
        locations = [
            'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
            'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose'
        ]
        
        data = []
        for i, store in enumerate(stores):
            data.append({
                'store_id': store,
                'store_type': np.random.choice(store_types),
                'location': locations[i]
            })
        
        return pd.DataFrame(data)
    
    def generate_product_master_sample(self) -> pd.DataFrame:
        """Generate sample product master dataset"""
        skus = [f"SKU{str(i).zfill(4)}" for i in range(1, 51)]
        
        categories = [
            'Electronics', 'Clothing', 'Food & Beverage', 'Home & Garden',
            'Sports & Outdoors', 'Health & Beauty', 'Toys & Games', 'Books'
        ]
        
        product_prefixes = {
            'Electronics': ['Laptop', 'Phone', 'Tablet', 'TV', 'Camera'],
            'Clothing': ['Shirt', 'Pants', 'Dress', 'Jacket', 'Shoes'],
            'Food & Beverage': ['Snack', 'Beverage', 'Cereal', 'Pasta', 'Sauce'],
            'Home & Garden': ['Furniture', 'Decor', 'Tool', 'Plant', 'Lighting'],
            'Sports & Outdoors': ['Ball', 'Racket', 'Bike', 'Tent', 'Gear'],
            'Health & Beauty': ['Shampoo', 'Lotion', 'Makeup', 'Supplement', 'Soap'],
            'Toys & Games': ['Puzzle', 'Doll', 'Game', 'Action Figure', 'Board Game'],
            'Books': ['Novel', 'Magazine', 'Textbook', 'Comic', 'Biography']
        }
        
        data = []
        for sku in skus:
            category = np.random.choice(categories)
            prefix = np.random.choice(product_prefixes[category])
            product_name = f"{prefix} {np.random.randint(100, 999)}"
            
            data.append({
                'sku_id': sku,
                'category': category,
                'product_name': product_name
            })
        
        return pd.DataFrame(data)
    
    def generate_supplier_sample(self) -> pd.DataFrame:
        """Generate sample supplier/lead time dataset"""
        skus = [f"SKU{str(i).zfill(4)}" for i in range(1, 51)]
        
        data = []
        for sku in skus:
            # Lead time typically between 1 and 30 days
            lead_time = np.random.choice([3, 5, 7, 10, 14, 21], p=[0.2, 0.25, 0.25, 0.15, 0.1, 0.05])
            
            data.append({
                'sku_id': sku,
                'lead_time': lead_time
            })
        
        return pd.DataFrame(data)
    
    def generate_all_samples(self) -> dict:
        """
        Generate all sample datasets and save them
        
        Returns:
            Dictionary mapping dataset types to file paths
        """
        samples = {}
        
        # Sales
        df = self.generate_sales_sample(1000)
        path = os.path.join(self.output_dir, 'sample_sales.csv')
        df.to_csv(path, index=False)
        samples['sales'] = path
        print(f"✓ Generated sales sample: {path}")
        
        # Inventory
        df = self.generate_inventory_sample(500)
        path = os.path.join(self.output_dir, 'sample_inventory.csv')
        df.to_csv(path, index=False)
        samples['inventory'] = path
        print(f"✓ Generated inventory sample: {path}")
        
        # Prices
        df = self.generate_prices_sample(800)
        path = os.path.join(self.output_dir, 'sample_prices.csv')
        df.to_csv(path, index=False)
        samples['prices'] = path
        print(f"✓ Generated prices sample: {path}")
        
        # Promotions
        df = self.generate_promotions_sample(500)
        path = os.path.join(self.output_dir, 'sample_promotions.csv')
        df.to_csv(path, index=False)
        samples['promotions'] = path
        print(f"✓ Generated promotions sample: {path}")
        
        # Calendar
        df = self.generate_calendar_sample()
        path = os.path.join(self.output_dir, 'sample_calendar.csv')
        df.to_csv(path, index=False)
        samples['calendar'] = path
        print(f"✓ Generated calendar sample: {path}")
        
        # Store Master
        df = self.generate_store_master_sample()
        path = os.path.join(self.output_dir, 'sample_store_master.csv')
        df.to_csv(path, index=False)
        samples['store_master'] = path
        print(f"✓ Generated store master sample: {path}")
        
        # Product Master
        df = self.generate_product_master_sample()
        path = os.path.join(self.output_dir, 'sample_product_master.csv')
        df.to_csv(path, index=False)
        samples['product_master'] = path
        print(f"✓ Generated product master sample: {path}")
        
        # Supplier
        df = self.generate_supplier_sample()
        path = os.path.join(self.output_dir, 'sample_supplier.csv')
        df.to_csv(path, index=False)
        samples['supplier'] = path
        print(f"✓ Generated supplier sample: {path}")
        
        return samples


if __name__ == "__main__":
    # Generate all sample datasets
    generator = SampleDatasetGenerator()
    samples = generator.generate_all_samples()
    
    print("\n" + "="*50)
    print("Sample datasets generated successfully!")
    print("="*50)
    print("\nGenerated files:")
    for dataset_type, path in samples.items():
        print(f"  - {dataset_type}: {path}")
