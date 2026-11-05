# RetailSense: Intelligent Demand Forecasting and Inventory Optimization

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-55%20passed-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**RetailSense** is an intelligent demand forecasting and inventory optimization system powered by machine learning. This academic mini-project demonstrates a complete data science pipeline from data ingestion through model deployment.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Module 1: Data Ingestion and Validation](#module-1-data-ingestion-and-validation)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Dataset Types](#dataset-types)
- [Architecture](#architecture)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Future Modules](#future-modules)
- [Contributing](#contributing)

---

## 🎯 Project Overview

RetailSense addresses the critical challenge of inventory optimization in retail by:

1. **Data Ingestion & Validation** (Module 1) - Current Implementation
2. **Feature Engineering** (Module 2) - Coming Soon
3. **Demand Forecasting** (Module 3) - Coming Soon
4. **Inventory Optimization** (Module 4) - Coming Soon

This repository contains the complete implementation of **Module 1: Data Ingestion and Validation**.

---

## 📦 Module 1: Data Ingestion and Validation

Module 1 provides a robust, enterprise-grade data ingestion and validation pipeline with:

### ✨ Key Features

- **Multi-Dataset Support**: Handles 8 different retail dataset types
- **Schema Validation**: Automatic column name standardization and type checking
- **Data Quality Checks**: Missing values, duplicates, outliers, and integrity validation
- **Security**: File upload validation, size limits, and path traversal protection
- **Interactive Dashboard**: Professional Streamlit-based UI
- **Automated Testing**: 55 comprehensive unit tests
- **Detailed Reporting**: JSON and CSV validation reports

### 🔍 Validation Capabilities

#### Schema Validation
- ✅ Required column detection
- ✅ Column name standardization (handles variations like `Store ID`, `store_id`, `StoreID`)
- ✅ Data type validation and conversion
- ✅ Date format validation

#### Data Quality Checks
- ✅ **Missing Values**: Per-column analysis with counts and percentages
- ✅ **Duplicate Detection**: Exact duplicates and business key violations
- ✅ **Outlier Detection**: Statistical outlier identification using IQR method
- ✅ **Data Integrity**: 
  - Negative value detection in sales/inventory
  - Invalid date validation
  - Empty identifier detection
  - Price validation (negative, zero, extreme values)

#### Security Features
- ✅ File type validation (CSV only)
- ✅ File size limits (100 MB max)
- ✅ Path traversal protection
- ✅ Safe filename generation
- ✅ Malformed CSV handling

---

## 🚀 Installation

### Prerequisites

- Python 3.12+
- pip (Python package manager)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd Retailsense
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
```

### Step 3: Activate Virtual Environment

**Windows:**
```bash
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Initialize Database

The database will be automatically initialized on first run. The SQLite database will be created at `data/database/retailsense.db`.

---

## 🎬 Quick Start

### 1. Run the Application

```bash
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`.

### 2. Upload Your First Dataset

1. Navigate to **Data Ingestion** page
2. Select a dataset type (e.g., Sales Dataset)
3. Upload a CSV file or download a sample template
4. Click **Process & Validate Dataset**
5. Review validation results and download cleaned data

### 3. Explore Validation Reports

1. Navigate to **Validation Reports** page
2. Select a dataset to view detailed metrics
3. Download cleaned datasets or validation reports

### 4. View Dataset History

1. Navigate to **Dataset History** page
2. Filter by type, status, or date
3. Manage and delete datasets

---

## 📊 Dataset Types

RetailSense supports 8 different dataset types:

### 1. **Sales Dataset**
Transaction-level sales data.

**Required Columns:**
- `date` (datetime) - Transaction date
- `store_id` (string) - Store identifier
- `sku_id` (string) - Product SKU identifier
- `sales` (numeric) - Sales quantity (units sold)

**Business Key:** `date + store_id + sku_id`

---

### 2. **Inventory Dataset**
Current stock levels per store and product.

**Required Columns:**
- `store_id` (string) - Store identifier
- `sku_id` (string) - Product SKU identifier
- `stock_quantity` (numeric) - Current stock quantity

**Business Key:** `store_id + sku_id`

---

### 3. **Prices Dataset**
Historical pricing data.

**Required Columns:**
- `date` (datetime) - Price effective date
- `store_id` (string) - Store identifier
- `sku_id` (string) - Product SKU identifier
- `price` (numeric) - Product price

**Business Key:** `date + store_id + sku_id`

---

### 4. **Promotions Dataset**
Promotional activity indicators.

**Required Columns:**
- `date` (datetime) - Promotion date
- `store_id` (string) - Store identifier
- `sku_id` (string) - Product SKU identifier
- `promotion` (boolean) - Promotion indicator (0/1, Yes/No, True/False)

**Business Key:** `date + store_id + sku_id`

---

### 5. **Calendar Dataset**
Date dimension with holidays.

**Required Columns:**
- `date` (datetime) - Calendar date
- `holiday` (boolean) - Holiday indicator (0/1, Yes/No)
- `holiday_name` (string, optional) - Name of holiday

**Business Key:** `date`

---

### 6. **Store Master Dataset**
Store-level master data.

**Required Columns:**
- `store_id` (string) - Store identifier
- `store_type` (string) - Store type/category
- `location` (string) - Store location

**Business Key:** `store_id`

---

### 7. **Product Master Dataset**
Product-level master data.

**Required Columns:**
- `sku_id` (string) - Product SKU identifier
- `category` (string) - Product category
- `product_name` (string) - Product name/description

**Business Key:** `sku_id`

---

### 8. **Supplier / Lead Time Dataset**
Supplier lead time information.

**Required Columns:**
- `sku_id` (string) - Product SKU identifier
- `lead_time` (numeric) - Lead time in days

**Business Key:** `sku_id`

---

## 🏗️ Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Dashboard                      │
│  (Overview | Data Ingestion | Reports | History)            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data Ingestion Service                      │
│  (Orchestrates entire pipeline)                             │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ File Handler │    │  Processor   │    │  Validator   │
│  - Security  │    │  - Schema    │    │  - Missing   │
│  - Upload    │    │  - Clean     │    │  - Duplicates│
│  - Storage   │    │  - Transform │    │  - Outliers  │
└──────────────┘    └──────────────┘    └──────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Report Generator │
                    │  - JSON/CSV      │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   SQLite DB      │
                    │  - Metadata      │
                    │  - Validation    │
                    └──────────────────┘
```

### Component Overview

#### 1. **Database Layer** (`src/database/`)
- **models.py**: SQLAlchemy models for datasets and validation metrics
- **connection.py**: Database connection and session management

#### 2. **Data Layer** (`src/data/`)
- **schemas.py**: Schema definitions for all 8 dataset types
- **validation.py**: Comprehensive data quality validation
- **processor.py**: Data processing pipeline
- **file_handler.py**: Secure file upload and storage
- **report_generator.py**: Validation report generation
- **ingestion_service.py**: Main orchestration service
- **sample_generator.py**: Sample dataset generation

#### 3. **Dashboard** (`dashboard/`)
- **pages/overview.py**: Summary dashboard
- **pages/data_ingestion.py**: Upload interface
- **pages/validation_reports.py**: Detailed reports
- **pages/dataset_history.py**: Dataset management

#### 4. **Tests** (`tests/`)
- 55 comprehensive unit tests
- Coverage: validation, schemas, processing, file handling

---

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Files

```bash
pytest tests/test_validation.py -v
pytest tests/test_schemas.py -v
pytest tests/test_processor.py -v
pytest tests/test_file_handler.py -v
```

### Test Coverage

- **test_validation.py**: 17 tests - Missing values, duplicates, outliers, integrity
- **test_schemas.py**: 14 tests - Schema definitions, column standardization
- **test_processor.py**: 13 tests - Data processing pipeline
- **test_file_handler.py**: 11 tests - File security and handling

**Total: 55 tests - All passing ✅**

---

## 📁 Project Structure

```
Retailsense/
│
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── data/                           # Data directory
│   ├── raw/                        # Uploaded raw datasets
│   ├── processed/                  # Cleaned datasets
│   ├── external/                   # Sample datasets
│   └── database/                   # SQLite database
│
├── src/                            # Source code
│   ├── data/                       # Data ingestion module
│   │   ├── __init__.py
│   │   ├── schemas.py              # Dataset schemas
│   │   ├── validation.py           # Validation logic
│   │   ├── processor.py            # Processing pipeline
│   │   ├── file_handler.py         # File operations
│   │   ├── report_generator.py    # Report generation
│   │   ├── ingestion_service.py   # Main service
│   │   └── sample_generator.py    # Sample data generator
│   │
│   └── database/                   # Database module
│       ├── __init__.py
│       ├── models.py               # SQLAlchemy models
│       └── connection.py           # DB connection
│
├── dashboard/                      # Streamlit dashboard
│   ├── __init__.py
│   ├── pages/                      # Dashboard pages
│   │   ├── overview.py
│   │   ├── data_ingestion.py
│   │   ├── validation_reports.py
│   │   └── dataset_history.py
│   └── components/                 # Reusable components
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── test_validation.py          # Validation tests
│   ├── test_schemas.py             # Schema tests
│   ├── test_processor.py           # Processing tests
│   └── test_file_handler.py        # File handling tests
│
├── reports/                        # Generated reports
├── notebooks/                      # Jupyter notebooks (future)
└── docs/                           # Documentation (future)
```

---

## 🔮 Future Modules

### Module 2: Feature Engineering (Coming Soon)
- Lag features
- Rolling window statistics
- Cyclical features (day of week, month)
- Holiday features
- Promotion features
- Price change features

### Module 3: Demand Forecasting (Coming Soon)
- Multiple ML algorithms (Random Forest, XGBoost, LightGBM)
- Time series models (Prophet, SARIMA)
- Deep learning models (LSTM)
- Ensemble methods
- Model evaluation (MAE, RMSE, MAPE)
- Hyperparameter tuning

### Module 4: Inventory Optimization (Coming Soon)
- Safety stock calculation
- Reorder point optimization
- EOQ (Economic Order Quantity)
- Service level optimization
- Cost minimization

### Module 5: Monitoring & Deployment (Coming Soon)
- MLflow integration
- Model versioning
- A/B testing
- Performance monitoring
- Automated retraining

---

## 📝 Usage Examples

### Example 1: Upload and Validate Sales Data

```python
# Sample sales data
data = {
    'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
    'store_id': ['S001', 'S001', 'S002'],
    'sku_id': ['SKU001', 'SKU002', 'SKU001'],
    'sales': [100, 150, 200]
}
```

1. Save as CSV: `sales_data.csv`
2. Upload via Dashboard → Data Ingestion
3. Select "Sales Dataset" as type
4. Click "Process & Validate"
5. Download cleaned dataset and validation report

### Example 2: Generate Sample Datasets

```bash
python src/data/sample_generator.py
```

This generates all 8 sample datasets in `data/external/`.

### Example 3: Programmatic Usage

```python
from src.data.ingestion_service import DataIngestionService

# Initialize service
service = DataIngestionService()

# Ingest dataset
with open('sales_data.csv', 'rb') as f:
    file_content = f.read()

result = service.ingest_dataset(
    file_content=file_content,
    original_filename='sales_data.csv',
    dataset_type='sales'
)

# Check results
if result['success']:
    print(f"Dataset ID: {result['dataset_id']}")
    print(f"Errors: {result['errors']}")
    print(f"Warnings: {result['warnings']}")
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root (optional):

```env
# Database
DATABASE_URL=sqlite:///data/database/retailsense.db

# File Upload
MAX_FILE_SIZE=104857600  # 100 MB
UPLOAD_DIR=data/raw
PROCESSED_DIR=data/processed

# Logging
LOG_LEVEL=INFO
```

---

## 🐛 Troubleshooting

### Issue: Module not found error

**Solution:** Ensure you're running from the project root with PYTHONPATH set:

```bash
$env:PYTHONPATH="$PWD"
streamlit run app.py
```

### Issue: Database locked

**Solution:** Close any existing database connections and restart the application.

### Issue: File upload fails

**Solution:** Check file size (max 100 MB) and format (CSV only).

---

## 🤝 Contributing

This is an academic project, but contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is created for academic purposes. Feel free to use and modify as needed.

---

## 👥 Team

**Project Type:** Academic Mini Project  
**Course:** Machine Learning / Data Science  
**Module:** 1 - Data Ingestion and Validation

---

## 🙏 Acknowledgments

- Streamlit for the amazing dashboard framework
- Pandas and NumPy for data processing
- Plotly for interactive visualizations
- SQLAlchemy for database ORM
- Pytest for testing framework

---

## 📞 Support

For issues and questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review test files for usage examples
3. Examine sample datasets in `data/external/`

---

## 📊 Project Status

- ✅ **Module 1: Data Ingestion & Validation** - Complete
- ⏳ **Module 2: Feature Engineering** - Coming Soon
- ⏳ **Module 3: Demand Forecasting** - Coming Soon
- ⏳ **Module 4: Inventory Optimization** - Coming Soon

---

**Last Updated:** 2024  
**Version:** 1.0.0 (Module 1)
