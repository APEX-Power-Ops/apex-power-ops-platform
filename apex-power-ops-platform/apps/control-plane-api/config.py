"""Database configuration for the Apex platform control-plane runtime."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the backend repo, regardless of launch cwd.
load_dotenv(Path(__file__).resolve().with_name(".env"))

def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


DATABASE_URL = _require_env("DATABASE_URL")

# Create engine with connection pooling (tuned for Supabase PgBouncer)
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,  # Test connection before using
    pool_use_lifo=True,  # PgBouncer best practice
    pool_recycle=300,
    connect_args={"options": "-c statement_timeout=30000"},
    echo=False,  # Set to True to see SQL queries
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import declarative base from models
from models.base import Base

# Dependency for FastAPI
def get_db():
    """Database session dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Test database connection."""
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"[OK] Database connection successful!")
        print(f"[OK] Tables found: {len(tables)}")
        return True
    except Exception as e:
        print(f"[ERROR] Database connection failed!")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_connection()
