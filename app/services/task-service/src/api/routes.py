"""
Task Service - API Routes

RESTful API endpoints for task management.
Implements full CRUD operations:
- CREATE: POST /tasks
- READ: GET /tasks, GET /tasks/{id}
- UPDATE: PUT /tasks/{id}
- DELETE: DELETE /tasks/{id}
- STATS: GET /tasks/stats

Features:
✅ Pydantic validation (automatic)
✅ Database session management (via dependency)
✅ Pagination support
✅ Error handling with proper HTTP status codes
✅ OpenAPI documentation (automatic)

Author: Krishan Shukla
Date: December 9, 2025
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..database import get_db, Task
from ..models import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskStatus,
    TaskPriority,
)

# Create API router
router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={
        404: {"description": "Task not found"},
        500: {"description": "Internal server error"},
    },
)
"""
API Router for task endpoints.

All routes are prefixed with /tasks:
- POST /tasks → Create task
- GET /tasks → List tasks
- GET /tasks/{id} → Get single task
- PUT /tasks/{id} → Update task
- DELETE /tasks/{id} → Delete task

Tags for OpenAPI docs:
- Grouped under "tasks" in /docs UI
"""


# ============================================================================
# CREATE - POST /tasks
# ============================================================================

@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="""
    Create a new task with the provided details.
    
    Request body fields:
    - **title** (required): Task title (1-200 chars)
    - **description** (optional): Detailed description (max 2000 chars)
    - **priority** (optional): low, medium, high, urgent (default: medium)
    - **assigned_to** (optional): Email of assignee
    - **due_date** (optional): Deadline (ISO 8601 format)
    - **tags** (optional): List of tags (max 10, each max 50 chars)
    
    Returns:
    - 201: Task created successfully
    - 422: Validation error (invalid data)
    - 500: Server error
    """,
)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """
    Create a new task.
    
    Flow:
    1. Receive task_data (Pydantic validates automatically)
    2. Create SQLAlchemy Task model
    3. Add to database session
    4. Commit transaction
    5. Refresh to get auto-generated fields (id, timestamps)
    6. Return TaskResponse (Pydantic serializes)
    
    Args:
        task_data: Task creation data (validated by Pydantic)
        db: Database session (injected by FastAPI)
    
    Returns:
        TaskResponse: Created task with id and timestamps
    
    Raises:
        HTTPException: 500 if database error occurs
    
    Example:
        POST /tasks
        {
            "title": "Deploy to production",
            "priority": "high",
            "tags": ["deployment", "production"]
        }
        
        Response (201):
        {
            "id": 123,
            "title": "Deploy to production",
            "status": "pending",
            "priority": "high",
            "created_at": "2025-12-09T10:00:00Z",
            ...
        }
    """
    
    try:
        # Create SQLAlchemy model from Pydantic model
        db_task = Task(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            assigned_to=task_data.assigned_to,
            due_date=task_data.due_date,
            tags=task_data.tags,
            # status defaults to PENDING in database model
        )
        
        # Add to session
        db.add(db_task)
        
        # Commit transaction (saves to database)
        db.commit()
        
        # Refresh to get auto-generated fields
        db.refresh(db_task)
        
        # Return as Pydantic model (auto-serialized)
        return TaskResponse.model_validate(db_task)
        
    except Exception as e:
        # Rollback on error (automatic via get_db, but explicit is clear)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}",
        )


# ============================================================================
# READ ALL - GET /tasks (with pagination)
# ============================================================================

@router.get(
    "",
    response_model=TaskListResponse,
    summary="List all tasks with pagination",
    description="""
    Retrieve a paginated list of tasks with optional filtering.
    
    Query parameters:
    - **page** (optional): Page number (default: 1, min: 1)
    - **size** (optional): Items per page (default: 20, min: 1, max: 100)
    - **status** (optional): Filter by status (pending/in_progress/completed/cancelled)
    - **priority** (optional): Filter by priority (low/medium/high/urgent)
    - **assigned_to** (optional): Filter by assignee email
    
    Returns paginated results with:
    - total: Total number of tasks matching filters
    - page: Current page number
    - size: Items per page
    - tasks: Array of tasks for current page
    
    Examples:
    - GET /tasks → First 20 tasks
    - GET /tasks?page=2&size=50 → Page 2, 50 items
    - GET /tasks?status=pending&priority=high → Filtered results
    """,
)
def list_tasks(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    assigned_to: Optional[str] = Query(None, description="Filter by assignee"),
    db: Session = Depends(get_db),
) -> TaskListResponse:
    """
    List tasks with pagination and filtering.
    
    Pagination calculation:
    - offset = (page - 1) * size
    - limit = size
    
    Example:
    - page=1, size=20 → offset=0, limit=20 (items 1-20)
    - page=2, size=20 → offset=20, limit=20 (items 21-40)
    - page=3, size=20 → offset=40, limit=20 (items 41-60)
    
    Args:
        page: Page number (1-indexed)
        size: Items per page
        status: Optional status filter
        priority: Optional priority filter
        assigned_to: Optional assignee filter
        db: Database session
    
    Returns:
        TaskListResponse: Paginated task list with metadata
    
    Example:
        GET /tasks?page=1&size=20&status=pending
        
        Response:
        {
            "total": 156,
            "page": 1,
            "size": 20,
            "tasks": [...]
        }
    """
    
    try:
        # Start with base query
        query = db.query(Task)
        
        # Apply filters (if provided)
        filters = []
        
        if status is not None:
            filters.append(Task.status == status)
        
        if priority is not None:
            filters.append(Task.priority == priority)
        
        if assigned_to is not None:
            filters.append(Task.assigned_to == assigned_to)
        
        # Combine filters with AND
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count (before pagination)
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        tasks = query.order_by(Task.created_at.desc()).offset(offset).limit(size).all()
        
        # Convert to Pydantic models
        task_responses = [TaskResponse.model_validate(task) for task in tasks]
        
        # Return paginated response
        return TaskListResponse(
            total=total,
            page=page,
            size=size,
            tasks=task_responses,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tasks: {str(e)}",
        )


# ============================================================================
# READ ONE - GET /tasks/{id}
# ============================================================================

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a specific task by ID",
    description="""
    Retrieve details of a single task by its ID.
    
    Path parameters:
    - **task_id**: Unique task identifier (integer)
    
    Returns:
    - 200: Task found and returned
    - 404: Task not found
    - 500: Server error
    """,
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """
    Get a single task by ID.
    
    Args:
        task_id: Task ID to retrieve
        db: Database session
    
    Returns:
        TaskResponse: Task details
    
    Raises:
        HTTPException: 404 if task not found
    
    Example:
        GET /tasks/123
        
        Response (200):
        {
            "id": 123,
            "title": "Deploy app",
            "status": "in_progress",
            ...
        }
        
        Response (404):
        {
            "detail": "Task with ID 999 not found"
        }
    """
    
    try:
        # Query by primary key (most efficient)
        task = db.query(Task).filter(Task.id == task_id).first()
        
        # Check if found
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found",
            )
        
        # Return as Pydantic model
        return TaskResponse.model_validate(task)
        
    except HTTPException:
        # Re-raise HTTP exceptions (404)
        raise
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task: {str(e)}",
        )


# ============================================================================
# UPDATE - PUT /tasks/{id}
# ============================================================================

@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
    description="""
    Update an existing task. Only provided fields will be updated.
    
    Path parameters:
    - **task_id**: Task ID to update
    
    Request body (all optional):
    - **title**: Updated title
    - **description**: Updated description
    - **status**: Updated status
    - **priority**: Updated priority
    - **assigned_to**: Updated assignee
    - **due_date**: Updated deadline
    - **tags**: Updated tags
    
    Returns:
    - 200: Task updated successfully
    - 404: Task not found
    - 422: Validation error
    - 500: Server error
    """,
)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """
    Update an existing task.
    
    Partial updates supported - only provided fields are updated.
    updated_at timestamp is automatically updated by database.
    
    Args:
        task_id: Task ID to update
        task_update: Fields to update (all optional)
        db: Database session
    
    Returns:
        TaskResponse: Updated task
    
    Raises:
        HTTPException: 404 if task not found
    
    Example:
        PUT /tasks/123
        {
            "status": "completed",
            "description": "Deployment successful!"
        }
        
        Response (200):
        {
            "id": 123,
            "status": "completed",  ← Updated
            "description": "Deployment successful!",  ← Updated
            "title": "Deploy app",  ← Unchanged
            "updated_at": "2025-12-09T14:30:00Z"  ← Auto-updated
            ...
        }
    """
    
    try:
        # Find task
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found",
            )
        
        # Update only provided fields
        update_data = task_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(task, field, value)
        
        # Commit changes
        db.commit()
        db.refresh(task)
        
        # Return updated task
        return TaskResponse.model_validate(task)
        
    except HTTPException:
        raise
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}",
        )


# ============================================================================
# DELETE - DELETE /tasks/{id}
# ============================================================================

@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    description="""
    Delete a task permanently.
    
    Path parameters:
    - **task_id**: Task ID to delete
    
    Returns:
    - 204: Task deleted successfully (no content)
    - 404: Task not found
    - 500: Server error
    
    ⚠️ Warning: This action cannot be undone!
    """,
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a task permanently.
    
    Note: Returns 204 No Content on success (no response body).
    
    Args:
        task_id: Task ID to delete
        db: Database session
    
    Returns:
        None (204 No Content)
    
    Raises:
        HTTPException: 404 if task not found
    
    Example:
        DELETE /tasks/123
        
        Response (204):
        (No content, but success)
        
        Response (404):
        {
            "detail": "Task with ID 999 not found"
        }
    """
    
    try:
        # Find task
        task = db.query(Task).filter(Task.id == task_id).first()
        
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found",
            )
        
        # Delete task
        db.delete(task)
        db.commit()
        
        # Return None (204 No Content)
        return None
        
    except HTTPException:
        raise
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}",
        )


# ============================================================================
# STATISTICS - GET /tasks/stats
# ============================================================================

@router.get(
    "/stats/summary",
    summary="Get task statistics",
    description="""
    Get aggregated statistics about tasks.
    
    Returns:
    - Total tasks
    - Count by status (pending, in_progress, completed, cancelled)
    - Count by priority (low, medium, high, urgent)
    - Tasks with upcoming deadlines (due in next 7 days)
    - Overdue tasks
    
    Useful for:
    - Dashboard metrics
    - Reporting
    - Monitoring workload
    """,
)
def get_task_stats(
    db: Session = Depends(get_db),
) -> dict:
    """
    Get task statistics.
    
    Aggregates:
    - Total count
    - Status breakdown
    - Priority breakdown
    - Deadline info
    
    Args:
        db: Database session
    
    Returns:
        dict: Statistics summary
    
    Example:
        GET /tasks/stats/summary
        
        Response:
        {
            "total": 156,
            "by_status": {
                "pending": 45,
                "in_progress": 67,
                "completed": 40,
                "cancelled": 4
            },
            "by_priority": {
                "low": 20,
                "medium": 80,
                "high": 50,
                "urgent": 6
            },
            "upcoming_deadlines": 15,
            "overdue": 3
        }
    """
    
    try:
        from datetime import datetime, timedelta
        
        # Total tasks
        total = db.query(func.count(Task.id)).scalar()
        
        # Count by status
        by_status = {}
        for status_value in TaskStatus:
            count = db.query(func.count(Task.id)).filter(
                Task.status == status_value
            ).scalar()
            by_status[status_value.value] = count
        
        # Count by priority
        by_priority = {}
        for priority_value in TaskPriority:
            count = db.query(func.count(Task.id)).filter(
                Task.priority == priority_value
            ).scalar()
            by_priority[priority_value.value] = count
        
        # Upcoming deadlines (next 7 days)
        now = datetime.now()
        week_from_now = now + timedelta(days=7)
        upcoming = db.query(func.count(Task.id)).filter(
            and_(
                Task.due_date.isnot(None),
                Task.due_date >= now,
                Task.due_date <= week_from_now,
                Task.status != TaskStatus.COMPLETED,
                Task.status != TaskStatus.CANCELLED,
            )
        ).scalar()
        
        # Overdue tasks
        overdue = db.query(func.count(Task.id)).filter(
            and_(
                Task.due_date.isnot(None),
                Task.due_date < now,
                Task.status != TaskStatus.COMPLETED,
                Task.status != TaskStatus.CANCELLED,
            )
        ).scalar()
        
        return {
            "total": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "upcoming_deadlines": upcoming,
            "overdue": overdue,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}",
        )


# ============================================================================
# EXPORT (for testing or other modules)
# ============================================================================

__all__ = ["router"]
