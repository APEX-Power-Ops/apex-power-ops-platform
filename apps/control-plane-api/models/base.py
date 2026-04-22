"""
Base configuration for SQLAlchemy models
"""
from sqlalchemy.orm import declarative_base
from datetime import datetime

# Create declarative base
Base = declarative_base()

# Common mixins can go here if needed
class TimestampMixin:
    """Mixin for created_at timestamp"""
    # This is handled in individual models since we're using
    # server-side defaults from PostgreSQL
    pass
