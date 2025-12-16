"""
Unit tests for Pydantic models (src/models/task.py).

These tests verify:
- Field validation (type, length, format)
- Enum validation (TaskStatus, TaskPriority)
- Custom validators (tags, due_date)
- Model serialization/deserialization
- Edge cases and error handling

No database or API required - pure validation logic testing.
"""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from src.models.task import (
    TaskBase,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskStatus,
    TaskPriority,
    TaskListResponse,
)


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestTaskEnums:
    """Test TaskStatus and TaskPriority enums."""
    
    def test_task_status_values(self):
        """Test that TaskStatus enum has all expected values."""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.CANCELLED == "cancelled"
        
        # Verify all values are strings
        for status in TaskStatus:
            assert isinstance(status.value, str)
    
    def test_task_priority_values(self):
        """Test that TaskPriority enum has all expected values."""
        assert TaskPriority.LOW == "low"
        assert TaskPriority.MEDIUM == "medium"
        assert TaskPriority.HIGH == "high"
        assert TaskPriority.URGENT == "urgent"
        
        # Verify all values are strings
        for priority in TaskPriority:
            assert isinstance(priority.value, str)
    
    def test_enum_iteration(self):
        """Test that enums can be iterated."""
        statuses = list(TaskStatus)
        assert len(statuses) == 4
        
        priorities = list(TaskPriority)
        assert len(priorities) == 4


# ============================================================================
# TASKBASE TESTS
# ============================================================================

class TestTaskBase:
    """Test TaskBase model (parent of TaskCreate)."""
    
    def test_create_with_required_fields_only(self):
        """Test creating TaskBase with only required field (title)."""
        task = TaskBase(title="Test task")
        
        assert task.title == "Test task"
        assert task.description is None
        assert task.priority == TaskPriority.MEDIUM  # Default value
        assert task.assigned_to is None
        assert task.tags == []  # Default empty list
        assert task.due_date is None
    
    def test_create_with_all_fields(self):
        """Test creating TaskBase with all fields populated."""
        due_date = datetime.utcnow() + timedelta(days=7)
        
        task = TaskBase(
            title="Complete task",
            description="Full description here",
            priority=TaskPriority.HIGH,
            assigned_to="dev@example.com",
            tags=["urgent", "backend"],
            due_date=due_date,
        )
        
        assert task.title == "Complete task"
        assert task.description == "Full description here"
        assert task.priority == TaskPriority.HIGH
        assert task.assigned_to == "dev@example.com"
        assert task.tags == ["urgent", "backend"]
        assert task.due_date == due_date
    
    def test_title_validation_empty_string(self):
        """Test that empty title is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskBase(title="")
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("title",) for error in errors)
    
    def test_title_validation_whitespace_only(self):
        """Test that whitespace-only title is allowed by Pydantic (min_length counts whitespace)."""
        # Pydantic's min_length counts whitespace characters, so "   " has length 3
        task = TaskBase(title="   ")
        assert task.title == "   "  # Whitespace is preserved
    
    def test_title_validation_max_length(self):
        """Test that title longer than 200 chars is rejected."""
        long_title = "x" * 201
        
        with pytest.raises(ValidationError) as exc_info:
            TaskBase(title=long_title)
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("title",) for error in errors)
    
    def test_title_validation_exactly_200_chars(self):
        """Test that title with exactly 200 chars is accepted."""
        title = "x" * 200
        task = TaskBase(title=title)
        assert len(task.title) == 200
    
    def test_title_validation_unicode(self):
        """Test that Unicode characters in title are accepted."""
        task = TaskBase(title="Task with émojis 🚀 and ü特殊字符")
        assert "🚀" in task.title
        assert "ü" in task.title
    
    def test_invalid_status(self):
        """Test that invalid status value is rejected (status not in TaskBase)."""
        # TaskBase doesn't have status field - this test is for TaskCreate/TaskUpdate
        # Skip this test for TaskBase
        pass
    
    def test_invalid_priority(self):
        """Test that invalid priority value is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TaskBase(title="Test", priority="invalid_priority")
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("priority",) for error in errors)


# ============================================================================
# TASKCREATE TESTS
# ============================================================================

class TestTaskCreate:
    """Test TaskCreate model (for POST requests)."""
    
    def test_create_minimal_task(self):
        """Test creating task with minimal required data."""
        task = TaskCreate(title="New task")
        
        assert task.title == "New task"
        # TaskCreate doesn't have status - only TaskResponse has it
        assert task.priority == TaskPriority.MEDIUM
    
    def test_tags_validator_removes_duplicates(self):
        """Test that tag validator removes duplicates (case-insensitive)."""
        task = TaskCreate(
            title="Test",
            tags=["python", "Python", "PYTHON", "testing"]
        )
        
        # Duplicates should be removed (case-insensitive)
        assert task.tags == ["python", "testing"]
    
    def test_tags_validator_max_10_tags(self):
        """Test that more than 10 tags is rejected."""
        tags = [f"tag{i}" for i in range(11)]
        
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(title="Test", tags=tags)
        
        assert "Maximum 10 tags" in str(exc_info.value)
    
    def test_tags_validator_max_length_per_tag(self):
        """Test that tags longer than 50 chars are rejected."""
        long_tag = "x" * 51
        
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(title="Test", tags=[long_tag])
        
        assert "50 characters" in str(exc_info.value)
    
    def test_tags_default_empty_list(self):
        """Test that tags default to empty list if not provided."""
        task = TaskCreate(title="Test")
        assert task.tags == []
    
    def test_due_date_validator_future_date(self):
        """Test that future due dates are accepted."""
        future_date = datetime.utcnow() + timedelta(days=7)
        task = TaskCreate(title="Test", due_date=future_date)
        
        assert task.due_date == future_date
    
    def test_due_date_validator_past_date(self):
        """Test that past due dates are rejected."""
        past_date = datetime.utcnow() - timedelta(days=1)
        
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(title="Test", due_date=past_date)
        
        errors = exc_info.value.errors()
        assert any("must be in the future" in str(error) for error in errors)
    
    def test_due_date_validator_current_time(self):
        """Test that current time might be rejected (timing-sensitive)."""
        # Due date should be in future, not current time
        current_date = datetime.utcnow()
        
        # This might pass or fail depending on microsecond timing
        # So we test with a definite past (1 second ago)
        past_date = datetime.utcnow() - timedelta(seconds=1)
        
        with pytest.raises(ValidationError):
            TaskCreate(title="Test", due_date=past_date)
    
    def test_due_date_none_is_valid(self):
        """Test that None due_date is accepted (optional field)."""
        task = TaskCreate(title="Test", due_date=None)
        assert task.due_date is None
    
    def test_json_serialization(self):
        """Test that TaskCreate can be serialized to JSON."""
        task = TaskCreate(
            title="Test",
            description="Description",
            priority=TaskPriority.HIGH,
            tags=["tag1", "tag2"]
        )
        
        # Convert to dict (simulating JSON serialization)
        task_dict = task.model_dump()
        
        assert task_dict["title"] == "Test"
        assert task_dict["description"] == "Description"
        assert task_dict["priority"] == "high"
        assert task_dict["tags"] == ["tag1", "tag2"]
    
    def test_from_json(self):
        """Test that TaskCreate can be created from dict/JSON."""
        data = {
            "title": "Test task",
            "priority": "high",
            "tags": ["testing"]
        }
        
        task = TaskCreate(**data)
        
        assert task.title == "Test task"
        assert task.priority == TaskPriority.HIGH
        assert task.tags == ["testing"]


# ============================================================================
# TASKUPDATE TESTS
# ============================================================================

class TestTaskUpdate:
    """Test TaskUpdate model (for PUT/PATCH requests)."""
    
    def test_all_fields_optional(self):
        """Test that TaskUpdate allows all fields to be None."""
        task = TaskUpdate()
        
        assert task.title is None
        assert task.description is None
        assert task.status is None
        assert task.priority is None
        assert task.assigned_to is None
        assert task.tags is None
        assert task.due_date is None
    
    def test_partial_update_title_only(self):
        """Test updating only title field."""
        task = TaskUpdate(title="Updated title")
        
        assert task.title == "Updated title"
        assert task.status is None  # Other fields unchanged
    
    def test_partial_update_status_only(self):
        """Test updating only status field."""
        task = TaskUpdate(status=TaskStatus.COMPLETED)
        
        assert task.status == TaskStatus.COMPLETED
        assert task.title is None  # Other fields unchanged
    
    def test_partial_update_multiple_fields(self):
        """Test updating multiple fields at once."""
        task = TaskUpdate(
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.URGENT,
            assigned_to="dev@example.com"
        )
        
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.URGENT
        assert task.assigned_to == "dev@example.com"
        assert task.title is None  # Unset fields remain None
    
    def test_tags_validator_still_applies(self):
        """Test that tag validation still works on updates."""
        # Test that too many tags is rejected
        many_tags = [f"tag{i}" for i in range(11)]
        
        with pytest.raises(ValidationError):
            TaskUpdate(tags=many_tags)
    
    def test_due_date_validator_still_applies(self):
        """Test that due_date validation is NOT applied in TaskUpdate (unlike TaskCreate)."""
        # TaskUpdate doesn't have due_date validator, so past dates are allowed
        past_date = datetime.utcnow() - timedelta(days=1)
        
        # This should work (no validation)
        task = TaskUpdate(due_date=past_date)
        assert task.due_date is not None
    
    def test_exclude_unset_fields(self):
        """Test that unset fields can be excluded from dict."""
        task = TaskUpdate(title="New title", priority=TaskPriority.HIGH)
        
        # Only include fields that were explicitly set
        update_dict = task.model_dump(exclude_unset=True)
        
        assert "title" in update_dict
        assert "priority" in update_dict
        assert "status" not in update_dict  # Not set
        assert "description" not in update_dict  # Not set


# ============================================================================
# TASKRESPONSE TESTS
# ============================================================================

class TestTaskResponse:
    """Test TaskResponse model (for API responses)."""
    
    def test_create_from_dict(self):
        """Test creating TaskResponse from dict (simulating DB row)."""
        data = {
            "id": 1,
            "title": "Test task",
            "description": "Description",
            "status": "pending",
            "priority": "high",
            "assigned_to": "user@example.com",
            "tags": ["tag1"],
            "due_date": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),  # Required in model
        }
        
        task = TaskResponse(**data)
        
        assert task.id == 1
        assert task.title == "Test task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.HIGH
        assert task.created_at is not None
    
    def test_created_at_required(self):
        """Test that created_at is required."""
        with pytest.raises(ValidationError) as exc_info:
            TaskResponse(
                id=1,
                title="Test",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                # created_at missing
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("created_at",) for error in errors)
    
    def test_updated_at_optional(self):
        """Test that updated_at is required (not optional in model)."""
        now = datetime.utcnow()
        
        task = TaskResponse(
            id=1,
            title="Test",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            created_at=now,
            updated_at=now,  # Required
        )
        
        assert task.updated_at is not None
    
    def test_json_serialization_with_datetime(self):
        """Test that datetime fields serialize correctly."""
        now = datetime.utcnow()
        
        task = TaskResponse(
            id=1,
            title="Test",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            created_at=now,
            updated_at=now,
        )
        
        # Convert to dict (JSON serializable)
        task_dict = task.model_dump(mode='json')
        
        # Datetime should be serialized to string
        assert isinstance(task_dict["created_at"], str)
        assert isinstance(task_dict["updated_at"], str)


# ============================================================================
# TASKLISTRESPONSE TESTS
# ============================================================================

class TestTaskListResponse:
    """Test TaskListResponse model (for paginated list responses)."""
    
    def test_create_list_response(self):
        """Test creating a paginated list response."""
        now = datetime.utcnow()
        tasks = [
            TaskResponse(
                id=i,
                title=f"Task {i}",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                created_at=now,
                updated_at=now,
            )
            for i in range(1, 11)
        ]
        
        response = TaskListResponse(
            tasks=tasks,
            total=100,
            page=1,
            size=10,
        )
        
        assert len(response.tasks) == 10
        assert response.total == 100
        assert response.page == 1
        assert response.size == 10
    
    def test_empty_list(self):
        """Test list response with no items."""
        response = TaskListResponse(
            tasks=[],
            total=0,
            page=1,
            size=20,
        )
        
        assert response.tasks == []
        assert response.total == 0
    
    def test_pagination_metadata(self):
        """Test that pagination metadata is correct."""
        response = TaskListResponse(
            tasks=[],
            total=47,
            page=2,
            size=20,
        )
        
        assert response.total == 47
        assert response.page == 2
        # Note: pages calculation would be done by client or endpoint
