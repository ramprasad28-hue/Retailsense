"""
Test concurrent database initialization to verify thread safety
"""
import sys
import os
import threading
import time

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import init_db, get_db_session, UploadedDataset, engine
from sqlalchemy import inspect


def test_concurrent_initialization():
    """Test that multiple threads can safely initialize the database"""
    print("=" * 70)
    print("TEST 1: CONCURRENT INITIALIZATION")
    print("=" * 70)
    
    results = []
    errors = []
    
    def init_thread(thread_id):
        try:
            print(f"Thread {thread_id}: Starting initialization...")
            init_db()
            print(f"Thread {thread_id}: Initialization completed")
            results.append(thread_id)
        except Exception as e:
            print(f"Thread {thread_id}: ERROR - {e}")
            errors.append((thread_id, str(e)))
    
    # Create 10 threads that all try to initialize simultaneously
    threads = []
    for i in range(10):
        thread = threading.Thread(target=init_thread, args=(i,))
        threads.append(thread)
    
    # Start all threads at approximately the same time
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print(f"\n✅ All {len(results)} threads completed successfully")
    
    if errors:
        print(f"❌ {len(errors)} threads encountered errors:")
        for thread_id, error in errors:
            print(f"   Thread {thread_id}: {error}")
        return False
    
    return True


def test_partial_table_recovery():
    """Test that missing tables are created even when some tables exist"""
    print("\n" + "=" * 70)
    print("TEST 2: PARTIAL TABLE RECOVERY")
    print("=" * 70)
    
    try:
        # Check current tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        print(f"Current tables: {existing_tables}")
        
        # Verify both required tables exist
        expected_tables = {'uploaded_datasets', 'validation_metrics'}
        missing_tables = expected_tables - set(existing_tables)
        
        if missing_tables:
            print(f"⚠️  Missing tables detected: {missing_tables}")
            print("Attempting to create missing tables...")
            
            # Re-initialize to create missing tables
            from src.database.connection import _db_initialized, _init_lock
            # Reset the flag to allow re-initialization
            import src.database.connection as conn_module
            with conn_module._init_lock:
                conn_module._db_initialized = False
            
            init_db()
            
            # Verify tables now exist
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            missing_tables = expected_tables - set(existing_tables)
            
            if missing_tables:
                print(f"❌ Still missing tables: {missing_tables}")
                return False
            else:
                print(f"✅ All missing tables created successfully")
        else:
            print("✅ All required tables already exist")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_existing_data_preservation():
    """Test that existing data is preserved after re-initialization"""
    print("\n" + "=" * 70)
    print("TEST 3: DATA PRESERVATION")
    print("=" * 70)
    
    try:
        session = get_db_session()
        
        # Count existing records
        initial_count = session.query(UploadedDataset).count()
        print(f"Initial dataset count: {initial_count}")
        
        # Re-initialize database (should not affect data)
        print("Re-initializing database...")
        init_db()
        
        # Check count again
        final_count = session.query(UploadedDataset).count()
        print(f"Final dataset count: {final_count}")
        
        session.close()
        
        if initial_count == final_count:
            print(f"✅ Data preserved: {initial_count} records maintained")
            return True
        else:
            print(f"❌ Data loss detected: {initial_count} -> {final_count}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rapid_sequential_calls():
    """Test rapid sequential initialization calls"""
    print("\n" + "=" * 70)
    print("TEST 4: RAPID SEQUENTIAL INITIALIZATION")
    print("=" * 70)
    
    try:
        start_time = time.time()
        
        for i in range(100):
            init_db()
        
        elapsed = time.time() - start_time
        
        print(f"✅ 100 sequential init_db() calls completed in {elapsed:.3f}s")
        print(f"   Average: {elapsed/100*1000:.2f}ms per call")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_table_verification():
    """Verify all expected tables and columns exist"""
    print("\n" + "=" * 70)
    print("TEST 5: SCHEMA VERIFICATION")
    print("=" * 70)
    
    try:
        inspector = inspect(engine)
        
        # Check uploaded_datasets table
        if 'uploaded_datasets' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('uploaded_datasets')]
            print(f"✅ uploaded_datasets table exists with {len(columns)} columns")
            print(f"   Columns: {', '.join(columns[:5])}...")
        else:
            print("❌ uploaded_datasets table missing")
            return False
        
        # Check validation_metrics table
        if 'validation_metrics' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('validation_metrics')]
            print(f"✅ validation_metrics table exists with {len(columns)} columns")
            print(f"   Columns: {', '.join(columns[:5])}...")
        else:
            print("❌ validation_metrics table missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Run all concurrent initialization tests"""
    print("\n" + "=" * 70)
    print("CONCURRENT DATABASE INITIALIZATION AUDIT")
    print("=" * 70)
    
    all_passed = True
    
    # Run all tests
    tests = [
        ("Concurrent Initialization", test_concurrent_initialization),
        ("Partial Table Recovery", test_partial_table_recovery),
        ("Data Preservation", test_existing_data_preservation),
        ("Rapid Sequential Calls", test_rapid_sequential_calls),
        ("Schema Verification", test_table_verification),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            results.append((test_name, False))
            all_passed = False
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print("=" * 70)
    
    if all_passed:
        print("✅ ALL TESTS PASSED - Database initialization is thread-safe")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Review errors above")
        return 1


if __name__ == "__main__":
    exit(main())
