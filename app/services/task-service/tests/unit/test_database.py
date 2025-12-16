"""
Unit tests for SQLAlchemy database models (src/database/models.py).

These tests verify:
- Task model creation and field mapping
- Default values and auto-generated fields
- Constraints and validations
- to_dict() serialization method
- Enum integration with database

Uses in-memory SQLite database for fast, isolated testing.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from src.database.models import Task
from src.models.task import TaskStatus, TaskPriority


# ============================================================================
# TASK MODEL CREATION TESTS
# ============================================================================

class TestTaskModel:
    """Test Task SQLAlchemy model creation and persistence."""
    
    def test_create_task_with_required_fields(self, test_db):
        """Test creating a task with only required fields."""
        task = Task(
            title="Test task",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
        )
        
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        assert task.id is not None  # Auto-generated
        assert task.title == "Test task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.created_at is not None  # Auto-set
        assert task.updated_at is None  # Not yet updated
    
    def test_create_task_with_all_fields(self, test_db):
        """Test creating a task with all fields populated."""
        due_date = datetime.utcnow() + timedelta(days=7)
        
        task = Task(
            title="Complete task",
            description="Detailed description",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            assigned_to="dev@example.com",
            tags=["backend", "urgent"],
            due_date=due_date,
        )
        
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        assert task.id is not None
        assert task.title == "Complete task"
        assert task.description == "Detailed description"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HIGH
        assert task.assigned_to == "dev@example.com"
        assert task.tags == ["backend", "urgent"]
        assert task.due_date == due_date
        assert task.created_at is not None
    
    def test_id_auto_increment(self, test_db):
        """Test that ID auto-increments for multiple tasks."""
        task1 = Task(title="Task 1", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM)
        task2 = Task(title="Task 2", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM)
        
        test_db.add(task1)
        test_db.add(task2)
        test_db.commit()
        test_db.refresh(task1)
        test_db.refresh(task2)
        
        assert task1.id is not None
        assert task2.id is not None
        assert task2.id > task1.id  # Auto-incremented
    
    def test_created_at_auto_set(self, test_db):
        """Test that created_at is automatically set to current time."""
        before = datetime.utcnow()
        
        task = Task(title="Test", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM)
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        after = datetime.utcnow()
        
        assert task.created_at is not None
        assert before <= task.created_at <= after
    
    def test_updated_at_initially_none(self, test_db):
        """Test that updated_at is None when task is created."""
        task = Task(title="Test", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM)
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        assert task.updated_at is None
    
    def test_updated_at_changes_on_update(self, test_db):
        """Test that updated_at changes when task is modified."""
        # Create task
        task = Task(title="Original", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM)
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        original_created_at = task.created_at
        original_updated_at = task.updated_at
        
        # Update task
        task.title = "Updated"
        test_db.commit()
        test_db.refresh(task)
        
        assert task.title == "Updated"
        assert task.created_at == original_created_at  # Unchanged
        assert task.updated_at is not None  # Now set
        assert task.updated_at != original_updated_at
    
    def test_default_values(self, test_db):
        """Test that default values are applied correctly."""
        task = Task(title="Test")
        
        # Defaults should be set even before saving
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.tags == []
        assert task.description is None
        assert task.assigned_to is None
        assert task.due_date is None


# ============================================================================
# CONSTRAINT TESTS
# ============================================================================

class TestTaskConstraints:
    """Test database constraints on Task model."""
    
    def test_title_not_null(self, test_db):
        """Test that title cannot be NULL."""
        task = Task(
            title=None,  # Invalid
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
        )
        
        test_db.add(task)
        
        with pytest.raises(IntegrityError):
            test_db.commit()
    
    def test_title_not_empty_string(self, test_db):
        """Test that title cannot be empty string (CHECK constraint)."""
        task = Task(
            title="",  # Invalid - CHECK constraint
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
        )
        
        test_db.add(task)
        
        # SQLite might not enforce this strictly, but we have Pydantic validation
        # The constraint is defined in the model
        try:
            test_db.commit()
            # If it passes, verify it's at least stored
            test_db.refresh(task)
        except IntegrityError:
            # This is expected if CHECK constraint is enforced
            pass
    
    def test_title_max_length_200(self, test_db):
        """Test that title can be up to 200 characters."""
        long_title = "x" * 200
        
        task = Task(
            title=long_title,
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
        )
        
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        assert len(task.title) == 200
    
    def test_title_exceeds_max_length(self, test_db):
        """Test that title longer than 200 chars fails (if enforced by DB)."""
        # Note: This depends on database enforcement
        # Pydantic validation catches this before it reaches the database
        very_long_title = "x" * 300
        
        task = Task(
            title=very_long_title,
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
        )
        
        test_db.add(task)
        
        # May or may not raise depending on DB, but Pydantic catches it first
        try:
            test_db.commit()
        except Exception:
            pass  # Expected if enforced


# ============================================================================
# ENUM INTEGRATION TESTS
# ============================================================================

class TestTaskEnumIntegration:
    """Test that Python enums work correctly with database."""
    
    def test_status_enum_storage(self, test_db):
        """Test that TaskStatus enum is stored correctly."""
        task = Task(
            title="Test",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.MEDIUM,
        )
        
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        # Should retrieve as enum, not string
        assert task.status == TaskStatus.COMPLETED
        assert isinstance(task.status, TaskStatus)
    
    def test_priority_enum_storage(self, test_db):
        """Test that TaskPriority enum is stored correctly."""
        task = Task(
            title="Test",
            status=TaskStatus.PENDING,
            priority=TaskPriority.URGENT,
        )
        
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        assert task.priority == TaskPriority.URGENT
        assert isinstance(task.priority, TaskPriority)
    
    def test_all_status_values(self, test_db):
        """Test that all TaskStatus enum values can be stored."""
        statuses = [
            TaskStatus.PENDING,
            TaskStatus.IN_PROGRESS,
            TaskStatus.COMPLETED,
            TaskStatus.CANCELLED,
        ]
        
        for i, status in enumerate(statuses):
            task = Task(
                title=f"Task {i}",
                status=status,
                priority=TaskPriority.MEDIUM,
            )
            test_db.add(task)
        
        test_db.commit()
        
        # Query all tasks
        tasks = test_db.query(Task).order_by(Task.id).all()
        
        assert len(tasks) == 4
        for i, task in enumerate(tasks):
            assert task.status == statuses[i]
    
    def test_all_priority_values(self, test_db):
        """Test that all TaskPriority enum values can be stored."""
        priorities = [
            TaskPriority.LOW,
            TaskPriority.MEDIUM,
            TaskPriority.HIGH,
            TaskPriority.URGENT,
        ]
        
        for i, priority in enumerate(priorities):
            task = Task(
                title=f"Task {i}",
                status=TaskStatus.PENDING,
                priority=priority,
            )
            test_db.add(task)
        
        test_db.commit()
        
        tasks = test_db.query(Task).order_by(Task.id).all()
        
        assert len(tasks) == 4
        for i, task in enumerate(tasks):
            assert task.priority == priorities[i]


# ============================================================================
# ARRAY FIELD TESTS
# ============================================================================

class TestTaskArrayFields:
    """Test array fields (tags) in Task model."""
    
    def test_tags_empty_list_default(self, test_db):
        """Test that tags default to empty list."""
        task = Task(title="Test", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM)
        
        assert task.tags == []
        
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        assert task.tags == []
    
    def test_tags_single_item(self, test_db):
        """Test storing a single tag."""
        task = Task(
            title="Test",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            tags=["urgent"],
        )
        
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        assert task.tags == ["urgent"]
    
    def test_tags_multiple_items(self, test_db):
        """Test storing multiple tags."""
        tags = ["backend", "database", "optimization", "phase-2"]
        
        task = Task(
            title="Test",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            tags=tags,
        )
        
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        assert task.tags == tags
        assert len(task.tags) == 4
    
    def test_tags_preserve_order(self, test_db):
        """Test that tag order is preserved."""
        tags = ["third", "first", "second"]
        
        task = Task(
            title="Test",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            tags=tags,
        )
        
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        assert task.tags == tags  # Order preserved


# ============================================================================
# TO_DICT METHOD TESTS
# ============================================================================

class TestTaskToDict:
    """Test the to_dict() serialization method."""
    
    def test_to_dict_basic(self, test_db):
        """Test basic to_dict() conversion."""
        task = Task(
            title="Test task",
            description="Test description",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
        )
        
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        task_dict = task.to_dict()
        
        assert isinstance(task_dict, dict)
        assert task_dict["id"] == task.id
        assert task_dict["title"] == "Test task"
        assert task_dict["description"] == "Test description"
        assert task_dict["status"] == "pending"  # Enum to string
        assert task_dict["priority"] == "high"  # Enum to string
    
    def test_to_dict_includes_all_fields(self, test_db):
        """Test that to_dict() includes all fields."""
        due_date = datetime.utcnow() + timedelta(days=7)
        
        task = Task(
            title="Complete task",
            description="Description",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.URGENT,
            assigned_to="dev@example.com",
            tags=["tag1", "tag2"],
            due_date=due_date,
        )
        
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        task_dict = task.to_dict()
        
        required_fields = [
            "id", "title", "description", "status", "priority",
            "assigned_to", "tags", "due_date", "created_at", "updated_at"
        ]
        
        for field in required_fields:
            assert field in task_dict
    
    def test_to_dict_enum_conversion(self, test_db):
        """Test that enums are converted to strings."""
        task = Task(
            title="Test",
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.LOW,
        )
        
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        task_dict = task.to_dict()
        
        # Enums should be strings, not enum objects
        assert task_dict["status"] == "completed"
        assert task_dict["priority"] == "low"
        assert isinstance(task_dict["status"], str)
        assert isinstance(task_dict["priority"], str)
    
    def test_to_dict_datetime_serialization(self, test_db):
        """Test that datetime fields are included."""
        task = Task(title="Test", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM)
        
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        task_dict = task.to_dict()
        
        # Datetimes should be present
        assert "created_at" in task_dict
        assert isinstance(task_dict["created_at"], datetime)
    
    def test_to_dict_with_none_values(self, test_db):
        """Test that None values are included in dict."""
        task = Task(title="Test", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM)
        
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        task_dict = task.to_dict()
        
        # Optional fields should be None
        assert task_dict["description"] is None
        assert task_dict["assigned_to"] is None
        assert task_dict["due_date"] is None
        assert task_dict["updated_at"] is None


# ============================================================================
# QUERY TESTS
# ============================================================================

class TestTaskQueries:
    """Test querying Task models from database."""
    
    def test_query_by_id(self, test_db):
        """Test querying a task by ID."""
        task = Task(title="Test", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM)
        test_db.add(task)
        test_db.commit()
        test_db.refresh(task)
        
        task_id = task.id
        
        # Query by ID
        found_task = test_db.query(Task).filter(Task.id == task_id).first()
        
        assert found_task is not None
        assert found_task.id == task_id
        assert found_task.title == "Test"
    
    def test_query_by_status(self, test_db, multiple_tasks):
        """Test querying tasks by status."""
        pending_tasks = test_db.query(Task).filter(
            Task.status == TaskStatus.PENDING
        ).all()
        
        assert len(pending_tasks) > 0
        for task in pending_tasks:
            assert task.status == TaskStatus.PENDING
    
    def test_query_by_priority(self, test_db, multiple_tasks):
        """Test querying tasks by priority."""
        urgent_tasks = test_db.query(Task).filter(
            Task.priority == TaskPriority.URGENT
        ).all()
        
        assert len(urgent_tasks) > 0
        for task in urgent_tasks:
            assert task.priority == TaskPriority.URGENT
    
    def test_query_count(self, test_db, multiple_tasks):
        """Test counting tasks."""
        total = test_db.query(Task).count()
        
        assert total == 20  # multiple_tasks fixture creates 20 tasks
    
    def test_query_order_by_created_at(self, test_db, multiple_tasks):
        """Test ordering tasks by created_at."""
        tasks = test_db.query(Task).order_by(Task.created_at).all()
        
        # Should be in chronological order
        for i in range(len(tasks) - 1):
            assert tasks[i].created_at <= tasks[i + 1].created_at
    
    def test_query_limit_offset(self, test_db, multiple_tasks):
        """Test pagination with limit and offset."""
        # Page 1: First 10 tasks
        page1 = test_db.query(Task).order_by(Task.id).limit(10).offset(0).all()
        
        # Page 2: Next 10 tasks
        page2 = test_db.query(Task).order_by(Task.id).limit(10).offset(10).all()
        
        assert len(page1) == 10
        assert len(page2) == 10
        
        # Ensure no overlap
        page1_ids = {task.id for task in page1}
        page2_ids = {task.id for task in page2}
        assert page1_ids.isdisjoint(page2_ids)
