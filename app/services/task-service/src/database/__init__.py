"""
Task Service - Database Package

Exports database models, connection, and session utilities.

Usage:
    from src.database import Task, Base, get_db, engine
"""

from .models import Base, Task
from .connection import (
    engine,
    SessionLocal,
    get_db,
    init_db,
    drop_db,
    check_database_connection,
    get_pool_status,
)

__all__ = [
    # Models
    "Base",
    "Task",
    # Connection
    "engine",
    "SessionLocal",
    "get_db",
    # Utilities
    "init_db",
    "drop_db",
    "check_database_connection",
    "get_pool_status",
]
