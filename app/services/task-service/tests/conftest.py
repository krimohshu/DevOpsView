"""
Pytest configuration and shared fixtures for task-service tests.

This module provides reusable test fixtures for:
- In-memory SQLite database for fast testing
- FastAPI test client for API testing
- Sample test data generators
- Mock configurations

Fixtures are automatically discovered by pytest and can be used
in any test by adding them as function parameters.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Add src to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.models import Base, Task
from src.database.connection import get_db
from src.main import app
from src.models.task import TaskCreate, TaskUpdate, TaskStatus, TaskPriority


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_engine():
    """
    Create an in-memory SQLite database engine for testing.
    
    Why SQLite?
    - Fast: Lives in memory, no disk I/O
    - Isolated: Each test gets a fresh database
    - Compatible: SQL standard, works with SQLAlchemy
    
    Scope: function = new database for each test
    """
    # In-memory database, shared across threads for FastAPI async tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Keep connection alive for in-memory DB
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup: Drop all tables after test
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator[Session, None, None]:
    """
    Provide a database session for testing.
    
    Each test gets a fresh session that automatically rolls back
    after the test completes, ensuring test isolation.
    
    Usage in tests:
        def test_something(test_db):
            task = Task(title="Test")
            test_db.add(task)
            test_db.commit()
    """
    # Create session factory
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()  # Rollback any uncommitted changes
        session.close()


@pytest.fixture(scope="function")
def client(test_db) -> Generator[TestClient, None, None]:
    """
    Provide a FastAPI test client with database override.
    
    This client:
    - Makes requests to your API endpoints
    - Uses the test database instead of production
    - Automatically handles startup/shutdown
    
    Usage in tests:
        def test_create_task(client):
            response = client.post("/api/v1/tasks", json={...})
            assert response.status_code == 201
    """
    # Override the database dependency
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # Session cleanup handled by test_db fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    with TestClient(app) as test_client:
        yield test_client
    
    # Cleanup: Remove override
    app.dependency_overrides.clear()


# ============================================================================
# DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_task_data() -> dict:
    """
    Provide sample task data for testing.
    
    Returns valid task data that passes all Pydantic validators.
    """
    return {
        "title": "Write unit tests",
        "description": "Create comprehensive test suite with pytest",
        "status": TaskStatus.PENDING,
        "priority": TaskPriority.HIGH,
        "assigned_to": "dev@example.com",
        "tags": ["testing", "quality", "phase-2"],
        "due_date": datetime.utcnow() + timedelta(days=7),
    }


@pytest.fixture
def sample_task_create(sample_task_data) -> TaskCreate:
    """
    Provide a valid TaskCreate Pydantic model.
    
    Usage:
        def test_validation(sample_task_create):
            assert sample_task_create.title == "Write unit tests"
    """
    return TaskCreate(**sample_task_data)


@pytest.fixture
def sample_db_task(test_db, sample_task_data) -> Task:
    """
    Create and save a task in the test database.
    
    Usage:
        def test_update(test_db, sample_db_task):
            sample_db_task.status = TaskStatus.COMPLETED
            test_db.commit()
    """
    task = Task(**sample_task_data)
    test_db.add(task)
    test_db.commit()
    test_db.refresh(task)
    return task


@pytest.fixture
def multiple_tasks(test_db) -> list[Task]:
    """
    Create multiple tasks with different statuses and priorities.
    
    Useful for testing:
    - Pagination
    - Filtering
    - Statistics endpoints
    """
    tasks_data = [
        {
            "title": f"Task {i}",
            "description": f"Description for task {i}",
            "status": TaskStatus.PENDING if i % 3 == 0 else TaskStatus.IN_PROGRESS if i % 3 == 1 else TaskStatus.COMPLETED,
            "priority": TaskPriority.LOW if i % 4 == 0 else TaskPriority.MEDIUM if i % 4 == 1 else TaskPriority.HIGH if i % 4 == 2 else TaskPriority.URGENT,
            "assigned_to": f"user{i}@example.com",
            "tags": [f"tag{i}", "test"],
            "due_date": datetime.utcnow() + timedelta(days=i) if i % 2 == 0 else None,
        }
        for i in range(1, 21)  # Create 20 tasks
    ]
    
    tasks = []
    for data in tasks_data:
        task = Task(**data)
        test_db.add(task)
        tasks.append(task)
    
    test_db.commit()
    
    # Refresh all tasks to get IDs
    for task in tasks:
        test_db.refresh(task)
    
    return tasks


# ============================================================================
# ENVIRONMENT FIXTURES
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Configure environment variables for testing.
    
    autouse=True means this runs automatically before all tests.
    scope="session" means it runs once per test session.
    """
    # Set test environment variables
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DEBUG"] = "false"
    os.environ["DB_HOST"] = "localhost"
    os.environ["DB_PORT"] = "5432"
    os.environ["DB_NAME"] = "test_db"
    os.environ["DB_USER"] = "test_user"
    os.environ["DB_PASSWORD"] = "test_password"
    os.environ["OTEL_ENABLED"] = "false"  # Disable tracing in most tests
    
    yield
    
    # Cleanup: Restore original environment
    # (In practice, pytest runs in isolated process, so not critical)


@pytest.fixture
def mock_settings(monkeypatch):
    """
    Provide a way to mock settings in tests.
    
    Usage:
        def test_with_tracing_enabled(mock_settings):
            mock_settings["OTEL_ENABLED"] = True
            # Test code that checks OTEL_ENABLED
    """
    settings_dict = {
        "DB_HOST": "localhost",
        "DB_PORT": 5432,
        "DB_NAME": "test_db",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_password",
        "OTEL_ENABLED": False,
        "DEBUG": False,
        "ENVIRONMENT": "testing",
    }
    
    def mock_get_setting(key, default=None):
        return settings_dict.get(key, default)
    
    # You can update settings_dict in tests
    return settings_dict


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def assert_valid_task_response():
    """
    Provide a helper function to validate task API responses.
    
    Usage:
        def test_create(client, assert_valid_task_response):
            response = client.post("/api/v1/tasks", json={...})
            assert_valid_task_response(response.json())
    """
    def _validate(task_dict: dict):
        """Validate that a task response has all required fields."""
        required_fields = ["id", "title", "status", "priority", "created_at"]
        for field in required_fields:
            assert field in task_dict, f"Missing required field: {field}"
        
        # Validate types
        assert isinstance(task_dict["id"], int)
        assert isinstance(task_dict["title"], str)
        assert task_dict["status"] in [s.value for s in TaskStatus]
        assert task_dict["priority"] in [p.value for p in TaskPriority]
        
        return True
    
    return _validate


@pytest.fixture
def clean_db(test_db):
    """
    Provide a helper to clean all tasks from database.
    
    Usage:
        def test_something(test_db, clean_db):
            # ... create tasks ...
            clean_db()  # Remove all tasks
    """
    def _clean():
        test_db.query(Task).delete()
        test_db.commit()
    
    return _clean


# ============================================================================
# PARAMETRIZE HELPERS
# ============================================================================

# Invalid task data for testing validation failures
INVALID_TASK_DATA = [
    # Empty title
    ({"title": "", "priority": "high"}, "title"),
    # Title too long
    ({"title": "x" * 201, "priority": "high"}, "title"),
    # Invalid priority
    ({"title": "Valid title", "priority": "invalid"}, "priority"),
    # Invalid status
    ({"title": "Valid title", "status": "invalid_status"}, "status"),
    # Invalid due_date format
    ({"title": "Valid title", "due_date": "not-a-date"}, "due_date"),
    # Negative tags
    ({"title": "Valid title", "tags": ["", "  "]}, "tags"),
]

# Valid task variations for testing edge cases
VALID_TASK_VARIATIONS = [
    # Minimal required fields only
    {"title": "Minimal task"},
    # All fields populated
    {
        "title": "Complete task",
        "description": "Full description",
        "status": TaskStatus.PENDING,
        "priority": TaskPriority.HIGH,
        "assigned_to": "user@example.com",
        "tags": ["tag1", "tag2"],
        "due_date": datetime.utcnow() + timedelta(days=7),
    },
    # Unicode characters
    {"title": "Task with émojis 🚀 and ü特殊字符"},
    # Maximum length title
    {"title": "x" * 200},
]
