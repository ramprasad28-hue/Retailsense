"""
Database connection and session management
"""
import os
import logging
import threading
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, scoped_session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database directory if it doesn't exist
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "database")
os.makedirs(DB_DIR, exist_ok=True)

# SQLite database for development
DATABASE_URL = f"sqlite:///{os.path.join(DB_DIR, 'retailsense.db')}"

# Create engine - single instance for the entire application
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True  # Verify connections before using them
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Thread-safe session
session_factory = scoped_session(SessionLocal)

# Thread lock for database initialization
_init_lock = threading.Lock()

# Flag to track if database has been initialized
_db_initialized = False


def init_db():
    """
    Initialize database tables safely with thread synchronization.
    
    This function:
    1. Uses a threading.Lock() to prevent concurrent initialization attempts
    2. Calls create_all(checkfirst=True) which creates only missing tables
    3. Is safe to call multiple times from different sessions/threads
    4. Preserves existing tables and data
    
    Returns:
        None
    
    Raises:
        Exception: If database initialization fails
    """
    global _db_initialized
    
    # Fast path: if already initialized, return immediately without acquiring lock
    if _db_initialized:
        logger.debug("Database already initialized (fast path)")
        return
    
    # Acquire lock to prevent concurrent initialization
    with _init_lock:
        # Double-check after acquiring lock (another thread might have initialized)
        if _db_initialized:
            logger.debug("Database already initialized (double-check)")
            return
        
        try:
            # Import Base here to avoid circular imports
            # This ensures all models are registered with Base before table creation
            from src.database.models import Base
            
            # Log all models registered with Base
            logger.info(f"Registered models: {[table.name for table in Base.metadata.sorted_tables]}")
            
            # Create all tables that don't exist yet
            # checkfirst=True ensures existing tables are not modified
            # This allows partial table creation if some tables are missing
            Base.metadata.create_all(bind=engine, checkfirst=True)
            
            # Verify tables were created
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            logger.info(f"Database tables after initialization: {existing_tables}")
            
            # Verify all expected tables exist
            expected_tables = {'uploaded_datasets', 'validation_metrics'}
            missing_tables = expected_tables - set(existing_tables)
            
            if missing_tables:
                error_msg = f"Failed to create tables: {missing_tables}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            _db_initialized = True
            logger.info(f"Database initialized successfully at: {DATABASE_URL}")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}", exc_info=True)
            raise


def get_db():
    """Get database session (generator for dependency injection)"""
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Get a database session (non-generator version)"""
    return session_factory()
