"""
Task Service - Pydantic Models

Defines data validation models for Task API.
These models handle:
- Request validation (TaskCreate, TaskUpdate)
- Response serialization (TaskResponse)
- Data type validation
- API documentation generation

Pydantic automatically:
✅ Validates data types
✅ Parses JSON
✅ Generates OpenAPI schema
✅ Provides clear error messages

Author: Krishan Shukla
Date: December 9, 2025
"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# ENUMS - Predefined Valid Values
# ============================================================================

class TaskStatus(str, Enum):
    """
    Valid task status values.
    
    Using Enum ensures only these values are accepted:
    - PENDING: Task created but not started
    - IN_PROGRESS: Task is being worked on
    - COMPLETED: Task finished successfully
    - CANCELLED: Task was cancelled
    
    Why str, Enum?
    - str: Makes it JSON-serializable (returns "pending" not TaskStatus.PENDING)
    - Enum: Provides type safety and autocomplete
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """
    Valid task priority values.
    
    Priority levels:
    - LOW: Can wait, non-urgent
    - MEDIUM: Normal priority
    - HIGH: Important, should be done soon
    - URGENT: Critical, needs immediate attention
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# ============================================================================
# BASE MODEL - Shared Fields
# ============================================================================

class TaskBase(BaseModel):
    """
    Base model with common task fields.
    
    Other models inherit from this to avoid code duplication.
    Contains fields that are common across Create/Update/Response.
    
    Why use inheritance?
    - DRY principle (Don't Repeat Yourself)
    - Consistent field definitions
    - Easy to add new common fields
    """
    
    title: str = Field(
        ...,  # ... means required field
        min_length=1,
        max_length=200,
        description="Task title (1-200 characters)",
        examples=["Deploy microservice to production"]
    )
    
    description: Optional[str] = Field(
        None,  # Optional field (can be null)
        max_length=2000,
        description="Detailed task description (max 2000 chars)",
        examples=["Deploy task-service v1.0.0 to EKS production cluster"]
    )
    
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,  # Default if not provided
        description="Task priority level",
        examples=["high"]
    )
    
    assigned_to: Optional[str] = Field(
        None,
        max_length=100,
        description="User assigned to this task",
        examples=["krishan.shukla@company.com"]
    )
    
    due_date: Optional[datetime] = Field(
        None,
        description="Task deadline (ISO 8601 format)",
        examples=["2025-12-31T23:59:59Z"]
    )
    
    tags: Optional[list[str]] = Field(
        default=[],
        description="List of tags for categorization",
        examples=[["devops", "kubernetes", "production"]]
    )


# ============================================================================
# CREATE MODEL - For POST /tasks
# ============================================================================

class TaskCreate(TaskBase):
    """
    Model for creating new tasks.
    
    Used when client sends POST request to create a task.
    Inherits all fields from TaskBase.
    
    Example API request:
    POST /tasks
    {
        "title": "Setup CI/CD pipeline",
        "description": "Configure GitLab CI for automated deployments",
        "priority": "high",
        "assigned_to": "krishan@company.com",
        "tags": ["cicd", "automation"]
    }
    
    Validation happens automatically:
    ✅ title is required and 1-200 chars
    ✅ priority must be valid enum value
    ✅ due_date is parsed from ISO string to datetime
    ❌ Invalid data returns 422 Unprocessable Entity
    """
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """
        Custom validator for tags.
        
        Rules:
        - Maximum 10 tags per task
        - Each tag max 50 characters
        - No duplicate tags
        """
        if v is None:
            return []
        
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        
        for tag in v:
            if len(tag) > 50:
                raise ValueError(f"Tag '{tag}' exceeds 50 characters")
        
        # Remove duplicates (case-insensitive)
        unique_tags = []
        seen = set()
        for tag in v:
            tag_lower = tag.lower()
            if tag_lower not in seen:
                unique_tags.append(tag)
                seen.add(tag_lower)
        
        return unique_tags
    
    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v):
        """
        Validate that due_date is in the future.
        
        Prevents creating tasks with past deadlines.
        """
        if v is not None and v < datetime.now():
            raise ValueError("due_date must be in the future")
        return v


# ============================================================================
# UPDATE MODEL - For PUT/PATCH /tasks/{id}
# ============================================================================

class TaskUpdate(BaseModel):
    """
    Model for updating existing tasks.
    
    All fields are optional - client can update only specific fields.
    
    Example API request:
    PATCH /tasks/123
    {
        "status": "completed",
        "description": "Updated description"
    }
    
    Why all optional?
    - Allows partial updates
    - Client doesn't need to send all fields
    - More flexible API
    """
    
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Updated task title"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Updated description"
    )
    
    status: Optional[TaskStatus] = Field(
        None,
        description="Updated status"
    )
    
    priority: Optional[TaskPriority] = Field(
        None,
        description="Updated priority"
    )
    
    assigned_to: Optional[str] = Field(
        None,
        max_length=100,
        description="Updated assignee"
    )
    
    due_date: Optional[datetime] = Field(
        None,
        description="Updated due date"
    )
    
    tags: Optional[list[str]] = Field(
        None,
        description="Updated tags"
    )
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Reuse same tag validation as TaskCreate"""
        if v is None:
            return None
        
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        
        for tag in v:
            if len(tag) > 50:
                raise ValueError(f"Tag '{tag}' exceeds 50 characters")
        
        unique_tags = []
        seen = set()
        for tag in v:
            tag_lower = tag.lower()
            if tag_lower not in seen:
                unique_tags.append(tag)
                seen.add(tag_lower)
        
        return unique_tags


# ============================================================================
# RESPONSE MODEL - For API Responses
# ============================================================================

class TaskResponse(TaskBase):
    """
    Model for returning tasks in API responses.
    
    Includes all TaskBase fields PLUS database fields:
    - id: Database primary key
    - status: Current task status
    - created_at: When task was created
    - updated_at: Last modification time
    
    Example API response:
    GET /tasks/123
    {
        "id": 123,
        "title": "Setup CI/CD pipeline",
        "description": "Configure GitLab CI",
        "status": "in_progress",
        "priority": "high",
        "assigned_to": "krishan@company.com",
        "due_date": "2025-12-31T23:59:59Z",
        "tags": ["cicd", "automation"],
        "created_at": "2025-12-09T10:00:00Z",
        "updated_at": "2025-12-09T14:30:00Z"
    }
    
    orm_mode enables reading from SQLAlchemy models:
    task_orm = db.query(Task).first()  # SQLAlchemy model
    return TaskResponse.from_orm(task_orm)  # Converts to Pydantic
    """
    
    id: int = Field(
        ...,
        description="Unique task identifier",
        examples=[123]
    )
    
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current task status"
    )
    
    created_at: datetime = Field(
        ...,
        description="Task creation timestamp"
    )
    
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp"
    )
    
    # Enable ORM mode for SQLAlchemy compatibility
    model_config = {
        "from_attributes": True,  # Pydantic V2: replaces orm_mode=True
        "json_schema_extra": {
            "example": {
                "id": 123,
                "title": "Deploy microservice to production",
                "description": "Deploy task-service v1.0.0 to EKS",
                "status": "in_progress",
                "priority": "high",
                "assigned_to": "krishan.shukla@company.com",
                "due_date": "2025-12-31T23:59:59Z",
                "tags": ["devops", "kubernetes", "production"],
                "created_at": "2025-12-09T10:00:00Z",
                "updated_at": "2025-12-09T14:30:00Z"
            }
        }
    }


# ============================================================================
# LIST RESPONSE - For Paginated Results
# ============================================================================

class TaskListResponse(BaseModel):
    """
    Model for paginated task lists.
    
    Used for GET /tasks endpoint with pagination.
    
    Example:
    GET /tasks?page=1&size=20
    {
        "total": 156,
        "page": 1,
        "size": 20,
        "tasks": [...]
    }
    
    Why pagination?
    - Prevents returning thousands of records
    - Improves API performance
    - Better client-side rendering
    - Aligns with CV: "40% cost reduction" (less data transfer)
    """
    
    total: int = Field(
        ...,
        description="Total number of tasks",
        examples=[156]
    )
    
    page: int = Field(
        ...,
        ge=1,  # Greater than or equal to 1
        description="Current page number",
        examples=[1]
    )
    
    size: int = Field(
        ...,
        ge=1,
        le=100,  # Max 100 items per page
        description="Items per page",
        examples=[20]
    )
    
    tasks: list[TaskResponse] = Field(
        ...,
        description="List of tasks for current page"
    )


# ============================================================================
# TESTING (if run directly)
# ============================================================================

if __name__ == "__main__":
    """
    Test the Pydantic models with sample data.
    Run: python3 src/models/task.py
    """
    
    print("=" * 60)
    print("🧪 Testing Pydantic Models")
    print("=" * 60)
    
    # Test 1: Valid task creation
    print("\n✅ Test 1: Valid TaskCreate")
    try:
        task_data = {
            "title": "Setup Kubernetes cluster",
            "description": "Configure EKS cluster on AWS",
            "priority": "high",
            "assigned_to": "krishan@company.com",
            "tags": ["kubernetes", "aws", "devops"]
        }
        task = TaskCreate(**task_data)
        print(f"✓ Created task: {task.title}")
        print(f"  Priority: {task.priority}")
        print(f"  Tags: {task.tags}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Invalid task (title too long)
    print("\n❌ Test 2: Invalid TaskCreate (title too long)")
    try:
        invalid_task = TaskCreate(
            title="x" * 201,  # 201 chars, max is 200
            description="This should fail"
        )
        print("✗ Should have failed!")
    except Exception as e:
        print(f"✓ Correctly rejected: {e}")
    
    # Test 3: Invalid priority
    print("\n❌ Test 3: Invalid priority value")
    try:
        invalid_task = TaskCreate(
            title="Test task",
            priority="super_urgent"  # Not in enum
        )
        print("✗ Should have failed!")
    except Exception as e:
        print(f"✓ Correctly rejected: Invalid priority")
    
    # Test 4: Tag validation
    print("\n🏷️  Test 4: Tag deduplication")
    try:
        task = TaskCreate(
            title="Test task",
            tags=["devops", "DevOps", "DEVOPS", "kubernetes"]
        )
        print(f"✓ Original: ['devops', 'DevOps', 'DEVOPS', 'kubernetes']")
        print(f"  Deduplicated: {task.tags}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 5: Partial update
    print("\n🔄 Test 5: Partial TaskUpdate")
    try:
        update = TaskUpdate(
            status="completed",
            description="Task finished successfully"
        )
        print(f"✓ Update model created")
        print(f"  Status: {update.status}")
        print(f"  Title: {update.title} (None - not updated)")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All Pydantic model tests completed!")
    print("=" * 60)
