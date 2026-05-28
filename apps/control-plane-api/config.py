"""Database configuration for the Apex platform control-plane runtime."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv


def runtime_env_files(config_path: Path | None = None) -> tuple[Path, ...]:
    resolved_path = (config_path or Path(__file__)).resolve()
    return (
        resolved_path.parents[2] / ".env.local",
        resolved_path.with_name(".env"),
    )


def load_runtime_env(config_path: Path | None = None, loader=load_dotenv) -> tuple[Path, ...]:
    env_files = runtime_env_files(config_path)
    for env_file in env_files:
        if env_file.exists():
            loader(env_file)
    return env_files


# Load environment variables for the local runtime, regardless of launch cwd.
# The repo-root .env.local carries governed live settings while the backend-local
# .env provides local fallbacks; load_dotenv keeps earlier values by default.
load_runtime_env()

DATABASE_URL_ENV_NAMES = (
    "APEX_OLARES_LIVE_DSN",
    "SEAM_DATABASE_URL",
    "APEX_DB_CONNECTION_STRING",
    "DATABASE_URL",
)


def resolve_database_url(getenv=os.getenv) -> str:
    for name in DATABASE_URL_ENV_NAMES:
        value = getenv(name)
        if value:
            return value

    supported_names = ", ".join(DATABASE_URL_ENV_NAMES)
    raise RuntimeError(
        "Missing required database environment variable. "
        f"Expected one of: {supported_names}"
    )


def build_connect_args(database_url: str) -> dict[str, str]:
    parsed = urlparse(database_url)
    hostname = (parsed.hostname or "").lower()
    port = parsed.port

    # Supabase poolers reject startup options like statement_timeout.
    if hostname.endswith(".pooler.supabase.com") or port == 6543:
        return {}

    return {"options": "-c statement_timeout=30000"}


DATABASE_URL = resolve_database_url()
CONNECT_ARGS = build_connect_args(DATABASE_URL)

# Create engine with connection pooling (tuned for Supabase PgBouncer)
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,  # Test connection before using
    pool_use_lifo=True,  # PgBouncer best practice
    pool_recycle=300,
    connect_args=CONNECT_ARGS,
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
