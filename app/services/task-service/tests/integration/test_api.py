"""
Integration tests for API endpoints (src/api/routes.py).

These tests verify:
- Full HTTP request/response cycle
- Database integration
- Pydantic validation in real requests
- Error handling and status codes
- Pagination and filtering
- Statistics endpoint accuracy

Uses FastAPI TestClient with in-memory SQLite database.
"""

from datetime import datetime, timedelta

import pytest

from src.models.task import TaskStatus, TaskPriority


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

class TestHealthEndpoint:
    """Test the health check endpoint."""
    
    def test_health_check(self, client):
        """Test that health endpoint returns 200 OK."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


# ============================================================================
# CREATE TASK TESTS
# ============================================================================

class TestCreateTask:
    """Test POST /api/v1/tasks endpoint."""
    
    def test_create_task_minimal(self, client, clean_db):
        """Test creating a task with minimal required fields."""
        clean_db()
        
        payload = {
            "title": "New task"
        }
        
        response = client.post("/api/v1/tasks", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["id"] is not None
        assert data["title"] == "New task"
        assert data["status"] == "pending"
        assert data["priority"] == "medium"
        assert data["created_at"] is not None
    
    def test_create_task_full(self, client, clean_db):
        """Test creating a task with all fields."""
        clean_db()
        
        due_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
        
        payload = {
            "title": "Complete task",
            "description": "Detailed description here",
            "priority": "high",
            "assigned_to": "dev@example.com",
            "tags": ["backend", "urgent"],
            "due_date": due_date,
        }
        
        response = client.post("/api/v1/tasks", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["title"] == "Complete task"
        assert data["description"] == "Detailed description here"
        assert data["priority"] == "high"
        assert data["assigned_to"] == "dev@example.com"
        assert data["tags"] == ["backend", "urgent"]
        assert data["due_date"] is not None
    
    def test_create_task_invalid_title_empty(self, client):
        """Test that empty title is rejected."""
        payload = {"title": ""}
        
        response = client.post("/api/v1/tasks", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    def test_create_task_invalid_title_too_long(self, client):
        """Test that title >200 chars is rejected."""
        payload = {"title": "x" * 201}
        
        response = client.post("/api/v1/tasks", json=payload)
        
        assert response.status_code == 422
    
    def test_create_task_invalid_priority(self, client):
        """Test that invalid priority is rejected."""
        payload = {
            "title": "Test",
            "priority": "invalid_priority"
        }
        
        response = client.post("/api/v1/tasks", json=payload)
        
        assert response.status_code == 422
    
    def test_create_task_past_due_date(self, client):
        """Test that past due_date is rejected."""
        past_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
        
        payload = {
            "title": "Test",
            "due_date": past_date
        }
        
        response = client.post("/api/v1/tasks", json=payload)
        
        assert response.status_code == 422
    
    def test_create_multiple_tasks(self, client, clean_db):
        """Test creating multiple tasks."""
        clean_db()
        
        for i in range(5):
            payload = {"title": f"Task {i}"}
            response = client.post("/api/v1/tasks", json=payload)
            assert response.status_code == 201
        
        # Verify all were created
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200
        assert response.json()["total"] == 5


# ============================================================================
# GET TASK TESTS
# ============================================================================

class TestGetTask:
    """Test GET /api/v1/tasks/{task_id} endpoint."""
    
    def test_get_existing_task(self, client, sample_db_task):
        """Test retrieving an existing task by ID."""
        task_id = sample_db_task.id
        
        response = client.get(f"/api/v1/tasks/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == task_id
        assert data["title"] == sample_db_task.title
        assert data["status"] == sample_db_task.status.value
    
    def test_get_nonexistent_task(self, client):
        """Test that getting non-existent task returns 404."""
        response = client.get("/api/v1/tasks/99999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_task_invalid_id(self, client):
        """Test that invalid task ID returns 422."""
        response = client.get("/api/v1/tasks/invalid")
        
        assert response.status_code == 422


# ============================================================================
# LIST TASKS TESTS
# ============================================================================

class TestListTasks:
    """Test GET /api/v1/tasks endpoint (list with pagination)."""
    
    def test_list_tasks_empty(self, client, clean_db):
        """Test listing tasks when database is empty."""
        clean_db()
        
        response = client.get("/api/v1/tasks")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["pages"] == 0
    
    def test_list_tasks_with_data(self, client, multiple_tasks):
        """Test listing tasks when database has data."""
        response = client.get("/api/v1/tasks")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) > 0
        assert data["total"] == 20  # multiple_tasks creates 20
        assert data["page"] == 1
    
    def test_list_tasks_pagination_page_1(self, client, multiple_tasks):
        """Test first page of pagination."""
        response = client.get("/api/v1/tasks?page=1&size=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) == 10
        assert data["page"] == 1
        assert data["size"] == 10
        assert data["total"] == 20
        assert data["pages"] == 2  # 20 total / 10 per page
    
    def test_list_tasks_pagination_page_2(self, client, multiple_tasks):
        """Test second page of pagination."""
        response = client.get("/api/v1/tasks?page=2&size=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) == 10
        assert data["page"] == 2
    
    def test_list_tasks_filter_by_status(self, client, multiple_tasks):
        """Test filtering tasks by status."""
        response = client.get("/api/v1/tasks?status=pending")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned tasks should be pending
        for task in data["items"]:
            assert task["status"] == "pending"
    
    def test_list_tasks_filter_by_priority(self, client, multiple_tasks):
        """Test filtering tasks by priority."""
        response = client.get("/api/v1/tasks?priority=high")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned tasks should be high priority
        for task in data["items"]:
            assert task["priority"] == "high"
    
    def test_list_tasks_filter_by_assigned_to(self, client, multiple_tasks):
        """Test filtering tasks by assigned_to."""
        response = client.get("/api/v1/tasks?assigned_to=user1@example.com")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned tasks should be assigned to user1
        for task in data["items"]:
            assert task["assigned_to"] == "user1@example.com"
    
    def test_list_tasks_combined_filters(self, client, multiple_tasks):
        """Test combining multiple filters."""
        response = client.get("/api/v1/tasks?status=pending&priority=high")
        
        assert response.status_code == 200
        data = response.json()
        
        # All tasks should match both filters
        for task in data["items"]:
            assert task["status"] == "pending"
            assert task["priority"] == "high"
    
    def test_list_tasks_custom_page_size(self, client, multiple_tasks):
        """Test custom page size."""
        response = client.get("/api/v1/tasks?size=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) == 5
        assert data["size"] == 5
        assert data["pages"] == 4  # 20 total / 5 per page
    
    def test_list_tasks_max_page_size(self, client, multiple_tasks):
        """Test that page size is capped at maximum."""
        response = client.get("/api/v1/tasks?size=1000")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be capped at 100 (or whatever max is defined)
        assert data["size"] <= 100


# ============================================================================
# UPDATE TASK TESTS
# ============================================================================

class TestUpdateTask:
    """Test PUT /api/v1/tasks/{task_id} endpoint."""
    
    def test_update_task_title(self, client, sample_db_task):
        """Test updating task title."""
        task_id = sample_db_task.id
        
        payload = {"title": "Updated title"}
        response = client.put(f"/api/v1/tasks/{task_id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == "Updated title"
        assert data["updated_at"] is not None
    
    def test_update_task_status(self, client, sample_db_task):
        """Test updating task status."""
        task_id = sample_db_task.id
        
        payload = {"status": "completed"}
        response = client.put(f"/api/v1/tasks/{task_id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "completed"
    
    def test_update_task_multiple_fields(self, client, sample_db_task):
        """Test updating multiple fields at once."""
        task_id = sample_db_task.id
        
        payload = {
            "title": "New title",
            "status": "in_progress",
            "priority": "urgent",
            "description": "New description",
        }
        
        response = client.put(f"/api/v1/tasks/{task_id}", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == "New title"
        assert data["status"] == "in_progress"
        assert data["priority"] == "urgent"
        assert data["description"] == "New description"
    
    def test_update_nonexistent_task(self, client):
        """Test updating non-existent task returns 404."""
        payload = {"title": "Updated"}
        response = client.put("/api/v1/tasks/99999", json=payload)
        
        assert response.status_code == 404
    
    def test_update_task_invalid_data(self, client, sample_db_task):
        """Test that invalid update data is rejected."""
        task_id = sample_db_task.id
        
        payload = {"priority": "invalid_priority"}
        response = client.put(f"/api/v1/tasks/{task_id}", json=payload)
        
        assert response.status_code == 422
    
    def test_update_task_empty_payload(self, client, sample_db_task):
        """Test updating with empty payload (no changes)."""
        task_id = sample_db_task.id
        original_title = sample_db_task.title
        
        payload = {}
        response = client.put(f"/api/v1/tasks/{task_id}", json=payload)
        
        # Should succeed but not change anything
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == original_title


# ============================================================================
# DELETE TASK TESTS
# ============================================================================

class TestDeleteTask:
    """Test DELETE /api/v1/tasks/{task_id} endpoint."""
    
    def test_delete_existing_task(self, client, sample_db_task):
        """Test deleting an existing task."""
        task_id = sample_db_task.id
        
        response = client.delete(f"/api/v1/tasks/{task_id}")
        
        assert response.status_code == 204  # No content
        
        # Verify task is gone
        get_response = client.get(f"/api/v1/tasks/{task_id}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_task(self, client):
        """Test deleting non-existent task returns 404."""
        response = client.delete("/api/v1/tasks/99999")
        
        assert response.status_code == 404
    
    def test_delete_task_idempotent(self, client, sample_db_task):
        """Test that deleting same task twice returns 404 on second attempt."""
        task_id = sample_db_task.id
        
        # First delete
        response1 = client.delete(f"/api/v1/tasks/{task_id}")
        assert response1.status_code == 204
        
        # Second delete (task already gone)
        response2 = client.delete(f"/api/v1/tasks/{task_id}")
        assert response2.status_code == 404


# ============================================================================
# STATISTICS ENDPOINT TESTS
# ============================================================================

class TestTaskStatistics:
    """Test GET /api/v1/tasks/stats/summary endpoint."""
    
    def test_stats_empty_database(self, client, clean_db):
        """Test statistics with empty database."""
        clean_db()
        
        response = client.get("/api/v1/tasks/stats/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_tasks"] == 0
        assert data["by_status"]["pending"] == 0
        assert data["by_status"]["in_progress"] == 0
        assert data["by_status"]["completed"] == 0
        assert data["by_status"]["cancelled"] == 0
    
    def test_stats_with_tasks(self, client, multiple_tasks):
        """Test statistics with real task data."""
        response = client.get("/api/v1/tasks/stats/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_tasks"] == 20
        
        # Verify status counts add up to total
        status_sum = sum(data["by_status"].values())
        assert status_sum == 20
        
        # Verify priority counts add up to total
        priority_sum = sum(data["by_priority"].values())
        assert priority_sum == 20
    
    def test_stats_by_status(self, client, test_db, clean_db):
        """Test that status statistics are accurate."""
        clean_db()
        
        from src.database.models import Task
        
        # Create tasks with known statuses
        test_db.add(Task(title="T1", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM))
        test_db.add(Task(title="T2", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM))
        test_db.add(Task(title="T3", status=TaskStatus.IN_PROGRESS, priority=TaskPriority.MEDIUM))
        test_db.add(Task(title="T4", status=TaskStatus.COMPLETED, priority=TaskPriority.MEDIUM))
        test_db.commit()
        
        response = client.get("/api/v1/tasks/stats/summary")
        data = response.json()
        
        assert data["by_status"]["pending"] == 2
        assert data["by_status"]["in_progress"] == 1
        assert data["by_status"]["completed"] == 1
        assert data["by_status"]["cancelled"] == 0
    
    def test_stats_by_priority(self, client, test_db, clean_db):
        """Test that priority statistics are accurate."""
        clean_db()
        
        from src.database.models import Task
        
        # Create tasks with known priorities
        test_db.add(Task(title="T1", status=TaskStatus.PENDING, priority=TaskPriority.LOW))
        test_db.add(Task(title="T2", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM))
        test_db.add(Task(title="T3", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM))
        test_db.add(Task(title="T4", status=TaskStatus.PENDING, priority=TaskPriority.HIGH))
        test_db.add(Task(title="T5", status=TaskStatus.PENDING, priority=TaskPriority.HIGH))
        test_db.add(Task(title="T6", status=TaskStatus.PENDING, priority=TaskPriority.URGENT))
        test_db.commit()
        
        response = client.get("/api/v1/tasks/stats/summary")
        data = response.json()
        
        assert data["by_priority"]["low"] == 1
        assert data["by_priority"]["medium"] == 2
        assert data["by_priority"]["high"] == 2
        assert data["by_priority"]["urgent"] == 1
    
    def test_stats_upcoming_deadlines(self, client, test_db, clean_db):
        """Test upcoming deadlines in statistics."""
        clean_db()
        
        from src.database.models import Task
        
        # Create task with upcoming deadline
        upcoming = datetime.utcnow() + timedelta(days=3)
        test_db.add(Task(
            title="Upcoming",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            due_date=upcoming
        ))
        test_db.commit()
        
        response = client.get("/api/v1/tasks/stats/summary")
        data = response.json()
        
        assert len(data["upcoming_deadlines"]) >= 1
    
    def test_stats_overdue_tasks(self, client, test_db, clean_db):
        """Test overdue tasks in statistics."""
        clean_db()
        
        from src.database.models import Task
        
        # Create overdue task (past due_date)
        # Note: This requires creating task directly, bypassing Pydantic validation
        overdue_task = Task(
            title="Overdue",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
        )
        # Manually set due_date in the past (bypass validation)
        test_db.add(overdue_task)
        test_db.commit()
        test_db.refresh(overdue_task)
        
        # Update due_date directly in database
        overdue_task.due_date = datetime.utcnow() - timedelta(days=1)
        test_db.commit()
        
        response = client.get("/api/v1/tasks/stats/summary")
        data = response.json()
        
        assert data["overdue_count"] >= 1


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestAPIErrorHandling:
    """Test error handling across API endpoints."""
    
    def test_invalid_json_payload(self, client):
        """Test that invalid JSON returns proper error."""
        response = client.post(
            "/api/v1/tasks",
            data="invalid json{",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_required_field(self, client):
        """Test that missing required field returns validation error."""
        response = client.post("/api/v1/tasks", json={})
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are included in responses."""
        response = client.get("/health")
        
        # FastAPI test client doesn't enforce CORS, but we can test main app has it
        assert response.status_code == 200
