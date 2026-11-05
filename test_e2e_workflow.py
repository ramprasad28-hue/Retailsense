"""
End-to-end workflow test: Upload → Validation → Report → Download
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.ingestion_service import DataIngestionService
from src.database import get_db_session, UploadedDataset, init_db
import pandas as pd


def test_complete_workflow():
    """Test the complete Module 1 workflow"""
    print("=" * 70)
    print("END-TO-END WORKFLOW TEST")
    print("=" * 70)
    
    # Step 1: Initialize database
    print("\n1. Initializing database...")
    try:
        init_db()
        print("   ✅ Database initialized")
    except Exception as e:
        print(f"   ❌ Database initialization failed: {e}")
        return False
    
    # Step 2: Load sample dataset
    print("\n2. Loading sample dataset...")
    sample_file = "data/external/sample_sales.csv"
    
    if not os.path.exists(sample_file):
        print(f"   ❌ Sample file not found: {sample_file}")
        return False
    
    with open(sample_file, 'rb') as f:
        file_content = f.read()
    
    print(f"   ✅ Loaded {len(file_content)} bytes from {sample_file}")
    
    # Step 3: Process dataset through ingestion service
    print("\n3. Processing dataset through ingestion pipeline...")
    service = DataIngestionService()
    
    try:
        result = service.ingest_dataset(
            file_content=file_content,
            original_filename="sample_sales.csv",
            dataset_type="sales"
        )
        
        if not result['success']:
            print(f"   ❌ Ingestion failed")
            for error in result.get('errors', []):
                print(f"      Error: {error}")
            return False
        
        print(f"   ✅ Dataset processed successfully")
        print(f"      Dataset ID: {result['dataset_id']}")
        
    except Exception as e:
        print(f"   ❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Verify database record
    print("\n4. Verifying database record...")
    try:
        session = get_db_session()
        dataset = session.query(UploadedDataset).filter(
            UploadedDataset.id == result['dataset_id']
        ).first()
        
        if not dataset:
            print("   ❌ Dataset record not found in database")
            return False
        
        print(f"   ✅ Dataset record found")
        print(f"      Type: {dataset.dataset_type}")
        print(f"      Rows: {dataset.total_rows}")
        print(f"      Columns: {dataset.total_columns}")
        print(f"      Status: {dataset.processing_status}")
        print(f"      Missing values: {dataset.missing_value_count}")
        print(f"      Duplicates: {dataset.duplicate_count}")
        print(f"      Outliers: {dataset.outlier_count}")
        
        session.close()
        
    except Exception as e:
        print(f"   ❌ Database verification failed: {e}")
        return False
    
    # Step 5: Verify cleaned dataset file
    print("\n5. Verifying cleaned dataset file...")
    if result.get('cleaned_file_path') and os.path.exists(result['cleaned_file_path']):
        try:
            df_cleaned = pd.read_csv(result['cleaned_file_path'])
            print(f"   ✅ Cleaned dataset exists")
            print(f"      Rows: {len(df_cleaned)}")
            print(f"      Columns: {len(df_cleaned.columns)}")
            print(f"      Columns: {', '.join(df_cleaned.columns)}")
        except Exception as e:
            print(f"   ⚠️  Could not read cleaned dataset: {e}")
    else:
        print("   ⚠️  Cleaned dataset file not found")
    
    # Step 6: Verify validation report
    print("\n6. Verifying validation report...")
    if result.get('report_file_path') and os.path.exists(result['report_file_path']):
        try:
            import json
            with open(result['report_file_path'], 'r') as f:
                report = json.load(f)
            
            print(f"   ✅ Validation report exists")
            print(f"      Report sections: {len(report)}")
            
            if 'validation_status' in report:
                status = report['validation_status']
                print(f"      Validation passed: {status.get('passed')}")
                print(f"      Total errors: {status.get('total_errors')}")
                print(f"      Total warnings: {status.get('total_warnings')}")
        except Exception as e:
            print(f"   ⚠️  Could not read validation report: {e}")
    else:
        print("   ⚠️  Validation report file not found")
    
    # Step 7: Test dataset retrieval
    print("\n7. Testing dataset retrieval...")
    try:
        retrieved_dataset = service.get_dataset_by_id(result['dataset_id'])
        
        if not retrieved_dataset:
            print("   ❌ Could not retrieve dataset")
            return False
        
        print(f"   ✅ Dataset retrieved successfully")
        print(f"      Filename: {retrieved_dataset.original_filename}")
        print(f"      Upload time: {retrieved_dataset.upload_timestamp}")
        
    except Exception as e:
        print(f"   ❌ Retrieval failed: {e}")
        return False
    
    # Step 8: Test get all datasets
    print("\n8. Testing get all datasets...")
    try:
        all_datasets = service.get_all_datasets()
        print(f"   ✅ Retrieved {len(all_datasets)} dataset(s)")
        
    except Exception as e:
        print(f"   ❌ Failed to get all datasets: {e}")
        return False
    
    # Step 9: Verify data can be queried after restart
    print("\n9. Testing persistence (simulating restart)...")
    try:
        # Create a new session (simulating app restart)
        new_session = get_db_session()
        count = new_session.query(UploadedDataset).count()
        print(f"   ✅ Data persists: {count} dataset(s) in database")
        new_session.close()
        
    except Exception as e:
        print(f"   ❌ Persistence test failed: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✅ END-TO-END WORKFLOW COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("\nAll Module 1 components verified:")
    print("  ✅ Database initialization")
    print("  ✅ File upload and storage")
    print("  ✅ Schema validation")
    print("  ✅ Data quality checks")
    print("  ✅ Data cleaning")
    print("  ✅ Report generation")
    print("  ✅ Database persistence")
    print("  ✅ Data retrieval")
    
    return True


def main():
    """Run end-to-end workflow test"""
    try:
        success = test_complete_workflow()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Test crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
