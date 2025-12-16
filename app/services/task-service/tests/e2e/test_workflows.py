"""
End-to-End workflow tests for task-service.

These tests verify complete user journeys and realistic scenarios:
- Create → Update → Complete → Delete workflows
- Bulk operations
- Complex filtering scenarios
- Real-world edge cases

Tests use the full API stack with in-memory database.
"""

from datetime import datetime, timedelta

import pytest


# ============================================================================
# COMPLETE TASK LIFECYCLE TESTS
# ============================================================================

class TestTaskLifecycle:
    """Test complete task lifecycle from creation to deletion."""
    
    def test_create_update_complete_delete_workflow(self, client, clean_db):
        """Test full CRUD workflow for a single task."""
        clean_db()
        
        # Step 1: Create task
        create_payload = {
            "title": "Deploy to production",
            "description": "Deploy task-service v1.0.0",
            "priority": "high",
            "assigned_to": "dev@example.com",
            "tags": ["deployment", "production"],
        }
        
        create_response = client.post("/api/v1/tasks", json=create_payload)
        assert create_response.status_code == 201
        
        task = create_response.json()
        task_id = task["id"]
        assert task["status"] == "pending"
        
        # Step 2: Start work (update status to in_progress)
        update_payload = {"status": "in_progress"}
        update_response = client.put(f"/api/v1/tasks/{task_id}", json=update_payload)
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "in_progress"
        
        # Step 3: Complete task
        complete_payload = {"status": "completed"}
        complete_response = client.put(f"/api/v1/tasks/{task_id}", json=complete_payload)
        assert complete_response.status_code == 200
        assert complete_response.json()["status"] == "completed"
        
        # Step 4: Verify task exists
        get_response = client.get(f"/api/v1/tasks/{task_id}")
        assert get_response.status_code == 200
        
        # Step 5: Delete completed task
        delete_response = client.delete(f"/api/v1/tasks/{task_id}")
        assert delete_response.status_code == 204
        
        # Step 6: Verify task is gone
        final_get = client.get(f"/api/v1/tasks/{task_id}")
        assert final_get.status_code == 404
    
    def test_task_reassignment_workflow(self, client, clean_db):
        """Test reassigning a task to different users."""
        clean_db()
        
        # Create task assigned to user1
        create_response = client.post("/api/v1/tasks", json={
            "title": "Code review",
            "assigned_to": "user1@example.com",
        })
        task_id = create_response.json()["id"]
        
        # Reassign to user2
        client.put(f"/api/v1/tasks/{task_id}", json={
            "assigned_to": "user2@example.com"
        })
        
        # Reassign to user3
        update_response = client.put(f"/api/v1/tasks/{task_id}", json={
            "assigned_to": "user3@example.com"
        })
        
        assert update_response.json()["assigned_to"] == "user3@example.com"
    
    def test_task_priority_escalation_workflow(self, client, clean_db):
        """Test escalating task priority over time."""
        clean_db()
        
        # Start with low priority
        create_response = client.post("/api/v1/tasks", json={
            "title": "Fix minor bug",
            "priority": "low",
        })
        task_id = create_response.json()["id"]
        
        # Escalate to medium
        client.put(f"/api/v1/tasks/{task_id}", json={"priority": "medium"})
        
        # Escalate to high
        client.put(f"/api/v1/tasks/{task_id}", json={"priority": "high"})
        
        # Final escalation to urgent
        final_response = client.put(f"/api/v1/tasks/{task_id}", json={"priority": "urgent"})
        
        assert final_response.json()["priority"] == "urgent"


# ============================================================================
# BULK OPERATIONS TESTS
# ============================================================================

class TestBulkOperations:
    """Test bulk operations and batch processing."""
    
    def test_create_multiple_tasks_bulk(self, client, clean_db):
        """Test creating many tasks in succession."""
        clean_db()
        
        task_titles = [
            "Write documentation",
            "Update dependencies",
            "Fix failing tests",
            "Review pull request",
            "Deploy to staging",
        ]
        
        created_ids = []
        for title in task_titles:
            response = client.post("/api/v1/tasks", json={"title": title})
            assert response.status_code == 201
            created_ids.append(response.json()["id"])
        
        # Verify all tasks exist
        list_response = client.get("/api/v1/tasks")
        assert list_response.json()["total"] == len(task_titles)
    
    def test_bulk_status_update_workflow(self, client, clean_db):
        """Test updating status of multiple tasks."""
        clean_db()
        
        # Create 5 tasks
        task_ids = []
        for i in range(5):
            response = client.post("/api/v1/tasks", json={"title": f"Task {i}"})
            task_ids.append(response.json()["id"])
        
        # Mark all as in_progress
        for task_id in task_ids:
            response = client.put(f"/api/v1/tasks/{task_id}", json={
                "status": "in_progress"
            })
            assert response.status_code == 200
        
        # Verify all are in_progress
        list_response = client.get("/api/v1/tasks?status=in_progress")
        assert list_response.json()["total"] == 5
    
    def test_bulk_delete_workflow(self, client, multiple_tasks):
        """Test deleting multiple tasks."""
        # Get all task IDs
        list_response = client.get("/api/v1/tasks")
        tasks = list_response.json()["items"]
        
        # Delete first 10 tasks
        for task in tasks[:10]:
            response = client.delete(f"/api/v1/tasks/{task['id']}")
            assert response.status_code == 204
        
        # Verify count decreased
        new_list = client.get("/api/v1/tasks")
        assert new_list.json()["total"] == 10  # 20 - 10 = 10


# ============================================================================
# COMPLEX FILTERING SCENARIOS
# ============================================================================

class TestComplexFiltering:
    """Test complex filtering and search scenarios."""
    
    def test_filter_urgent_pending_tasks(self, client, test_db, clean_db):
        """Test finding urgent tasks that are still pending."""
        clean_db()
        
        from src.database.models import Task
        from src.models.task import TaskStatus, TaskPriority
        
        # Create mix of tasks
        test_db.add(Task(title="T1", status=TaskStatus.PENDING, priority=TaskPriority.URGENT))
        test_db.add(Task(title="T2", status=TaskStatus.PENDING, priority=TaskPriority.LOW))
        test_db.add(Task(title="T3", status=TaskStatus.COMPLETED, priority=TaskPriority.URGENT))
        test_db.add(Task(title="T4", status=TaskStatus.PENDING, priority=TaskPriority.URGENT))
        test_db.commit()
        
        response = client.get("/api/v1/tasks?status=pending&priority=urgent")
        data = response.json()
        
        assert data["total"] == 2  # Only T1 and T4
        for task in data["items"]:
            assert task["status"] == "pending"
            assert task["priority"] == "urgent"
    
    def test_filter_tasks_by_user_and_status(self, client, test_db, clean_db):
        """Test finding all in-progress tasks for a specific user."""
        clean_db()
        
        from src.database.models import Task
        from src.models.task import TaskStatus, TaskPriority
        
        # Create tasks for different users
        test_db.add(Task(title="T1", status=TaskStatus.IN_PROGRESS, priority=TaskPriority.MEDIUM, assigned_to="alice@example.com"))
        test_db.add(Task(title="T2", status=TaskStatus.IN_PROGRESS, priority=TaskPriority.MEDIUM, assigned_to="bob@example.com"))
        test_db.add(Task(title="T3", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM, assigned_to="alice@example.com"))
        test_db.add(Task(title="T4", status=TaskStatus.IN_PROGRESS, priority=TaskPriority.MEDIUM, assigned_to="alice@example.com"))
        test_db.commit()
        
        response = client.get("/api/v1/tasks?status=in_progress&assigned_to=alice@example.com")
        data = response.json()
        
        assert data["total"] == 2  # Only T1 and T4
        for task in data["items"]:
            assert task["status"] == "in_progress"
            assert task["assigned_to"] == "alice@example.com"
    
    def test_pagination_with_filters(self, client, multiple_tasks):
        """Test that pagination works correctly with filters."""
        # Get pending tasks, page 1
        page1 = client.get("/api/v1/tasks?status=pending&page=1&size=3")
        data1 = page1.json()
        
        assert len(data1["items"]) <= 3
        assert data1["page"] == 1
        
        # All items should be pending
        for task in data1["items"]:
            assert task["status"] == "pending"


# ============================================================================
# EDGE CASES AND ERROR SCENARIOS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_update_task_to_same_values(self, client, sample_db_task):
        """Test that updating task to same values works."""
        task_id = sample_db_task.id
        original_title = sample_db_task.title
        
        response = client.put(f"/api/v1/tasks/{task_id}", json={
            "title": original_title
        })
        
        assert response.status_code == 200
        assert response.json()["title"] == original_title
    
    def test_create_task_with_unicode_characters(self, client, clean_db):
        """Test creating task with Unicode characters in various fields."""
        clean_db()
        
        payload = {
            "title": "测试任务 with émojis 🚀",
            "description": "Descripción con acentos: ñ, ü, é",
            "tags": ["日本語", "한국어", "русский"],
        }
        
        response = client.post("/api/v1/tasks", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert "🚀" in data["title"]
        assert "日本語" in data["tags"]
    
    def test_task_with_maximum_length_title(self, client, clean_db):
        """Test task with title at maximum length (200 chars)."""
        clean_db()
        
        max_title = "x" * 200
        response = client.post("/api/v1/tasks", json={"title": max_title})
        
        assert response.status_code == 201
        assert len(response.json()["title"]) == 200
    
    def test_task_with_many_tags(self, client, clean_db):
        """Test task with many tags."""
        clean_db()
        
        many_tags = [f"tag{i}" for i in range(20)]
        response = client.post("/api/v1/tasks", json={
            "title": "Task with many tags",
            "tags": many_tags
        })
        
        assert response.status_code == 201
        assert len(response.json()["tags"]) == 20
    
    def test_delete_already_deleted_task(self, client, sample_db_task):
        """Test deleting a task that's already been deleted."""
        task_id = sample_db_task.id
        
        # First delete
        response1 = client.delete(f"/api/v1/tasks/{task_id}")
        assert response1.status_code == 204
        
        # Second delete attempt
        response2 = client.delete(f"/api/v1/tasks/{task_id}")
        assert response2.status_code == 404
    
    def test_get_task_after_update(self, client, sample_db_task):
        """Test that GET reflects latest updates."""
        task_id = sample_db_task.id
        
        # Update task
        client.put(f"/api/v1/tasks/{task_id}", json={"title": "New title"})
        
        # Get task
        response = client.get(f"/api/v1/tasks/{task_id}")
        
        assert response.json()["title"] == "New title"


# ============================================================================
# STATISTICS ACCURACY TESTS
# ============================================================================

class TestStatisticsAccuracy:
    """Test that statistics endpoint returns accurate data."""
    
    def test_stats_reflect_task_creation(self, client, clean_db):
        """Test that stats update when tasks are created."""
        clean_db()
        
        # Initial stats
        response1 = client.get("/api/v1/tasks/stats/summary")
        initial_total = response1.json()["total_tasks"]
        
        # Create task
        client.post("/api/v1/tasks", json={"title": "New task"})
        
        # Updated stats
        response2 = client.get("/api/v1/tasks/stats/summary")
        new_total = response2.json()["total_tasks"]
        
        assert new_total == initial_total + 1
    
    def test_stats_reflect_task_updates(self, client, sample_db_task):
        """Test that stats update when task status changes."""
        task_id = sample_db_task.id
        
        # Get initial stats
        response1 = client.get("/api/v1/tasks/stats/summary")
        initial_completed = response1.json()["by_status"]["completed"]
        
        # Mark task as completed
        client.put(f"/api/v1/tasks/{task_id}", json={"status": "completed"})
        
        # Get updated stats
        response2 = client.get("/api/v1/tasks/stats/summary")
        new_completed = response2.json()["by_status"]["completed"]
        
        assert new_completed == initial_completed + 1
    
    def test_stats_reflect_task_deletion(self, client, sample_db_task):
        """Test that stats update when tasks are deleted."""
        task_id = sample_db_task.id
        
        # Get initial stats
        response1 = client.get("/api/v1/tasks/stats/summary")
        initial_total = response1.json()["total_tasks"]
        
        # Delete task
        client.delete(f"/api/v1/tasks/{task_id}")
        
        # Get updated stats
        response2 = client.get("/api/v1/tasks/stats/summary")
        new_total = response2.json()["total_tasks"]
        
        assert new_total == initial_total - 1


# ============================================================================
# REALISTIC USER SCENARIOS
# ============================================================================

class TestRealisticScenarios:
    """Test realistic user scenarios and workflows."""
    
    def test_daily_standup_workflow(self, client, clean_db):
        """
        Simulate daily standup: Create today's tasks, review yesterday's.
        """
        clean_db()
        
        # Create today's tasks
        todays_tasks = [
            {"title": "Review PRs", "priority": "high"},
            {"title": "Fix bug #123", "priority": "urgent"},
            {"title": "Update documentation", "priority": "low"},
        ]
        
        for task_data in todays_tasks:
            response = client.post("/api/v1/tasks", json=task_data)
            assert response.status_code == 201
        
        # Check pending tasks
        pending_response = client.get("/api/v1/tasks?status=pending")
        assert pending_response.json()["total"] == 3
        
        # Start working on highest priority
        urgent_tasks = client.get("/api/v1/tasks?status=pending&priority=urgent")
        urgent_task = urgent_tasks.json()["items"][0]
        
        client.put(f"/api/v1/tasks/{urgent_task['id']}", json={
            "status": "in_progress"
        })
        
        # Verify one task in progress
        in_progress = client.get("/api/v1/tasks?status=in_progress")
        assert in_progress.json()["total"] == 1
    
    def test_sprint_planning_workflow(self, client, clean_db):
        """
        Simulate sprint planning: Create backlog, assign priorities and owners.
        """
        clean_db()
        
        # Create sprint backlog
        backlog = [
            {
                "title": "Implement user authentication",
                "priority": "urgent",
                "assigned_to": "alice@example.com",
                "tags": ["backend", "security"],
            },
            {
                "title": "Design dashboard UI",
                "priority": "high",
                "assigned_to": "bob@example.com",
                "tags": ["frontend", "ui"],
            },
            {
                "title": "Write API documentation",
                "priority": "medium",
                "assigned_to": "charlie@example.com",
                "tags": ["documentation"],
            },
        ]
        
        created_tasks = []
        for task_data in backlog:
            response = client.post("/api/v1/tasks", json=task_data)
            created_tasks.append(response.json())
        
        # Verify sprint size
        assert len(created_tasks) == 3
        
        # Check Alice's tasks
        alice_tasks = client.get("/api/v1/tasks?assigned_to=alice@example.com")
        assert alice_tasks.json()["total"] == 1
    
    def test_end_of_sprint_cleanup(self, client, test_db, clean_db):
        """
        Simulate end of sprint: Complete finished tasks, move incomplete to next sprint.
        """
        clean_db()
        
        from src.database.models import Task
        from src.models.task import TaskStatus, TaskPriority
        
        # Create sprint tasks
        test_db.add(Task(title="Completed feature", status=TaskStatus.COMPLETED, priority=TaskPriority.HIGH))
        test_db.add(Task(title="In progress feature", status=TaskStatus.IN_PROGRESS, priority=TaskPriority.HIGH))
        test_db.add(Task(title="Not started", status=TaskStatus.PENDING, priority=TaskPriority.MEDIUM))
        test_db.commit()
        
        # Archive completed tasks (delete them)
        completed = client.get("/api/v1/tasks?status=completed")
        for task in completed.json()["items"]:
            client.delete(f"/api/v1/tasks/{task['id']}")
        
        # Carry over incomplete tasks
        remaining = client.get("/api/v1/tasks")
        assert remaining.json()["total"] == 2  # Only in_progress and pending remain
