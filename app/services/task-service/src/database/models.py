"""
Task Service - SQLAlchemy Database Models

Defines database schema using SQLAlchemy ORM.
These models:
- Define table structure in PostgreSQL
- Handle database operations (CRUD)
- Manage relationships and constraints
- Enable type-safe queries

Difference from Pydantic models:
- Pydantic: API validation (JSON ↔ Python)
- SQLAlchemy: Database mapping (Python ↔ SQL)

Author: Krishan Shukla
Date: December 9, 2025
"""

from datetime import datetime
from typing import List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum as SQLEnum,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

# Import enums from Pydantic models for consistency
try:
    from ..models.task import TaskStatus, TaskPriority
except ImportError:
    # For direct execution (python3 src/database/models.py)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models.task import TaskStatus, TaskPriority


# ============================================================================
# DECLARATIVE BASE
# ============================================================================

Base = declarative_base()
"""
SQLAlchemy Base class for all models.

All database models inherit from this.
It tracks model metadata and enables migrations.

Usage:
    class MyModel(Base):
        __tablename__ = "my_table"
        ...
"""


# ============================================================================
# TASK MODEL - Main Database Table
# ============================================================================

class Task(Base):
    """
    Task database model.
    
    Maps to 'tasks' table in PostgreSQL.
    
    Table structure:
    ┌─────────────┬──────────────┬─────────────┬─────────────┐
    │ Column      │ Type         │ Nullable    │ Default     │
    ├─────────────┼──────────────┼─────────────┼─────────────┤
    │ id          │ INTEGER      │ NO (PK)     │ AUTO        │
    │ title       │ VARCHAR(200) │ NO          │ -           │
    │ description │ TEXT         │ YES         │ NULL        │
    │ status      │ ENUM         │ NO          │ 'pending'   │
    │ priority    │ ENUM         │ NO          │ 'medium'    │
    │ assigned_to │ VARCHAR(100) │ YES         │ NULL        │
    │ due_date    │ TIMESTAMP    │ YES         │ NULL        │
    │ tags        │ ARRAY[TEXT]  │ YES         │ []          │
    │ created_at  │ TIMESTAMP    │ NO          │ NOW()       │
    │ updated_at  │ TIMESTAMP    │ NO          │ NOW()       │
    └─────────────┴──────────────┴─────────────┴─────────────┘
    
    Indexes for performance:
    - idx_task_status: Fast filtering by status
    - idx_task_priority: Fast filtering by priority
    - idx_task_assigned_to: Fast user task lookup
    - idx_task_due_date: Fast deadline queries
    - idx_task_created_at: Fast time-based queries
    
    Why these indexes?
    - Common query patterns: "Show my tasks", "Show high priority", "Due this week"
    - Aligns with CV: "40% cost reduction" (faster queries = less DB time)
    """
    
    __tablename__ = "tasks"
    
    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique task identifier (auto-generated)",
    )
    """
    Primary Key - Unique identifier for each task.
    
    - Auto-increments: 1, 2, 3, 4...
    - Indexed automatically (PK always indexed)
    - Used in API: GET /tasks/{id}
    """
    
    # ========================================================================
    # CORE FIELDS
    # ========================================================================
    
    title = Column(
        String(200),
        nullable=False,
        comment="Task title (required, max 200 chars)",
    )
    """
    Task title - Short description of the task.
    
    Constraints:
    - NOT NULL: Title is required
    - VARCHAR(200): Limited length for performance
    
    Examples:
    - "Deploy microservice to production"
    - "Setup CI/CD pipeline"
    - "Configure monitoring alerts"
    """
    
    description = Column(
        Text,
        nullable=True,
        comment="Detailed task description (optional)",
    )
    """
    Detailed description - Longer explanation of task.
    
    - TEXT: No length limit (stored separately in PostgreSQL)
    - NULL allowed: Description is optional
    - Use for: Requirements, instructions, notes
    """
    
    status = Column(
        SQLEnum(TaskStatus, name="task_status", create_type=True),
        nullable=False,
        default=TaskStatus.PENDING,
        comment="Current task status (pending/in_progress/completed/cancelled)",
    )
    """
    Task status - Current state of the task.
    
    Uses Enum for data integrity:
    - Only valid values allowed (pending, in_progress, completed, cancelled)
    - Database-level constraint (can't insert invalid status)
    - Default: 'pending' for new tasks
    
    Status workflow:
    pending → in_progress → completed
                ↓
            cancelled
    """
    
    priority = Column(
        SQLEnum(TaskPriority, name="task_priority", create_type=True),
        nullable=False,
        default=TaskPriority.MEDIUM,
        comment="Task priority (low/medium/high/urgent)",
    )
    """
    Task priority - Importance/urgency level.
    
    - Default: 'medium' (most common)
    - Used for: Sorting, filtering, SLA calculations
    - Helps teams prioritize work
    """
    
    assigned_to = Column(
        String(100),
        nullable=True,
        comment="Email of assigned user (optional)",
    )
    """
    Assigned user - Who's responsible for this task.
    
    - Stores email address (max 100 chars)
    - NULL allowed: Tasks can be unassigned
    - Future: Could be foreign key to users table
    """
    
    due_date = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Task deadline (with timezone)",
    )
    """
    Due date - When task should be completed.
    
    - TIMESTAMP WITH TIME ZONE: Handles timezones correctly
    - NULL allowed: Not all tasks have deadlines
    - Used for: Deadline notifications, overdue alerts
    
    Why timezone-aware?
    - Team may be distributed globally
    - Prevents timezone bugs
    - Best practice for distributed systems
    """
    
    tags = Column(
        ARRAY(Text),
        nullable=True,
        default=[],
        comment="List of tags for categorization",
    )
    """
    Tags - Categorization labels.
    
    - PostgreSQL ARRAY type: Native array support
    - Stores multiple tags per task
    - Examples: ['devops', 'kubernetes', 'production']
    
    Use cases:
    - Filtering: "Show all 'kubernetes' tasks"
    - Reporting: "Count tasks by tag"
    - Organization: Group related tasks
    """
    
    # ========================================================================
    # AUDIT FIELDS - Automatic Timestamps
    # ========================================================================
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When task was created (auto-generated)",
    )
    """
    Created timestamp - When task was first created.
    
    - server_default=func.now(): Database sets this automatically
    - IMMUTABLE: Never changes after creation
    - Used for: Audit trail, reporting, analytics
    
    Why func.now()?
    - Uses database server time (not app server)
    - Consistent across multiple app instances
    - Survives app restarts
    """
    
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update time (auto-updated)",
    )
    """
    Updated timestamp - When task was last modified.
    
    - server_default=func.now(): Set on creation
    - onupdate=func.now(): Auto-updates on every UPDATE
    - Used for: Change tracking, cache invalidation, sync
    
    Updates automatically when:
    - Status changes
    - Title/description edited
    - Priority changed
    - Any field modified
    """
    
    # ========================================================================
    # INDEXES - Performance Optimization
    # ========================================================================
    
    __table_args__ = (
        # Index for filtering by status (most common query)
        Index("idx_task_status", "status"),
        
        # Index for filtering by priority
        Index("idx_task_priority", "priority"),
        
        # Index for user's tasks lookup
        Index("idx_task_assigned_to", "assigned_to"),
        
        # Index for deadline queries (due this week, overdue, etc.)
        Index("idx_task_due_date", "due_date"),
        
        # Index for time-based queries (recent tasks, etc.)
        Index("idx_task_created_at", "created_at"),
        
        # Composite index for common filtering pattern
        Index("idx_task_status_priority", "status", "priority"),
        
        # Check constraint: title cannot be empty string
        CheckConstraint("length(title) > 0", name="check_title_not_empty"),
        
        {
            "comment": "Tasks table - stores all task information with audit trail",
        },
    )
    """
    Table-level configurations.
    
    Indexes explained:
    
    1. idx_task_status:
       Query: SELECT * FROM tasks WHERE status = 'pending'
       Speedup: O(log n) instead of O(n) full table scan
    
    2. idx_task_assigned_to:
       Query: SELECT * FROM tasks WHERE assigned_to = 'user@email.com'
       Use case: "Show my tasks" page
    
    3. idx_task_status_priority (composite):
       Query: SELECT * FROM tasks WHERE status = 'pending' AND priority = 'high'
       Use case: "Show high priority pending tasks"
       
    4. idx_task_due_date:
       Query: SELECT * FROM tasks WHERE due_date < NOW()
       Use case: "Show overdue tasks"
    
    Why indexes matter for CV achievements:
    - "99.95% uptime": Fast queries reduce DB load
    - "40% cost reduction": Less query time = lower DB costs
    - "70% MTTR reduction": Fast queries for debugging
    
    Trade-off:
    - Indexes speed up SELECT queries
    - Slightly slow down INSERT/UPDATE (index maintenance)
    - Acceptable trade-off: Read-heavy workload (more GETs than POSTs)
    """
    
    # ========================================================================
    # MAGIC METHODS - String Representation
    # ========================================================================
    
    def __repr__(self) -> str:
        """
        String representation for debugging.
        
        Example output:
        <Task(id=123, title='Deploy app', status='in_progress')>
        """
        return (
            f"<Task("
            f"id={self.id}, "
            f"title='{self.title[:30]}...', "
            f"status='{self.status.value}', "
            f"priority='{self.priority.value}'"
            f")>"
        )
    
    def to_dict(self) -> dict:
        """
        Convert model to dictionary.
        
        Useful for:
        - JSON serialization
        - Logging
        - Testing
        
        Returns:
            dict: All fields as dictionary
        
        Example:
            task = Task(title="Deploy app", status=TaskStatus.PENDING)
            task_dict = task.to_dict()
            # {'id': 1, 'title': 'Deploy app', ...}
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "assigned_to": self.assigned_to,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# TESTING (if run directly)
# ============================================================================

if __name__ == "__main__":
    """
    Test the database models.
    Run: python3 src/database/models.py
    """
    
    print("=" * 60)
    print("🗄️  Testing SQLAlchemy Models")
    print("=" * 60)
    
    # Test 1: Model structure
    print("\n✅ Test 1: Model Structure")
    print(f"Table name: {Task.__tablename__}")
    print(f"Columns: {[col.name for col in Task.__table__.columns]}")
    print(f"Indexes: {[idx.name for idx in Task.__table__.indexes]}")
    
    # Test 2: Create model instance
    print("\n✅ Test 2: Create Task Instance")
    task = Task(
        title="Setup Kubernetes Cluster",
        description="Configure EKS on AWS",
        status=TaskStatus.PENDING,
        priority=TaskPriority.HIGH,
        assigned_to="krishan@company.com",
        tags=["kubernetes", "aws", "devops"],
    )
    print(f"Created: {task}")
    print(f"Title: {task.title}")
    print(f"Status: {task.status.value}")
    print(f"Priority: {task.priority.value}")
    
    # Test 3: to_dict method
    print("\n✅ Test 3: to_dict() Method")
    task_dict = task.to_dict()
    print(f"Dictionary keys: {list(task_dict.keys())}")
    print(f"Title from dict: {task_dict['title']}")
    
    # Test 4: Show SQL DDL
    print("\n✅ Test 4: Generate SQL DDL")
    from sqlalchemy import create_engine
    from sqlalchemy.schema import CreateTable
    
    # Create in-memory SQLite engine for testing
    engine = create_engine("sqlite:///:memory:")
    
    print("\n📝 SQL CREATE TABLE statement:")
    print("-" * 60)
    create_sql = CreateTable(Task.__table__).compile(engine)
    print(str(create_sql)[:500] + "...")
    
    print("\n" + "=" * 60)
    print("✅ SQLAlchemy model tests completed!")
    print("=" * 60)
    print("\n📊 Next: Connect to PostgreSQL database")
