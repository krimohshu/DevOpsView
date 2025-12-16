# 🎨 Phase 2 Visual Architecture Guide

**Study Guide for Tomorrow's Session**

---

## 🏗️ Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT APPLICATION                             │
│                     (Browser, Mobile App, Postman)                       │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ HTTP Request
                                 │ POST /api/v1/tasks
                                 ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         TASK-SERVICE (Container)                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      main.py (FastAPI App)                        │  │
│  │  - CORS Middleware                                                │  │
│  │  - Health Check (/health)                                         │  │
│  │  - API Documentation (/docs)                                      │  │
│  └────────────────────┬──────────────────────────────────────────────┘  │
│                       │                                                  │
│                       ↓                                                  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    routes.py (API Endpoints)                      │  │
│  │  - POST   /api/v1/tasks         → create_task()                  │  │
│  │  - GET    /api/v1/tasks         → get_tasks()                    │  │
│  │  - GET    /api/v1/tasks/{id}    → get_task()                     │  │
│  │  - PUT    /api/v1/tasks/{id}    → update_task()                  │  │
│  │  - DELETE /api/v1/tasks/{id}    → delete_task()                  │  │
│  └────────────────────┬──────────────────────────────────────────────┘  │
│                       │                                                  │
│                       ↓                                                  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │              dependencies.py (Dependency Injection)               │  │
│  │  - get_db() → Provides database session                          │  │
│  │  - Automatic session cleanup                                      │  │
│  └────────────────────┬──────────────────────────────────────────────┘  │
│                       │                                                  │
│         ┌─────────────┼─────────────┐                                   │
│         │             │             │                                   │
│         ↓             ↓             ↓                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐                  │
│  │task.py   │  │database  │  │ observability/       │                  │
│  │(Pydantic)│  │.py       │  │ tracing.py           │                  │
│  │          │  │(SQLAlch) │  │ (OpenTelemetry)      │                  │
│  │Validate  │  │DB Model  │  │ - Traces requests    │                  │
│  │Request/  │  │Table     │  │ - Captures spans     │                  │
│  │Response  │  │Schema    │  │ - Exports to Jaeger  │                  │
│  └──────────┘  └────┬─────┘  └──────────────────────┘                  │
│                     │                                                    │
└─────────────────────┼────────────────────────────────────────────────────┘
                      │
                      │ SQL Queries
                      ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                          POSTGRESQL DATABASE                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                         tasks TABLE                               │  │
│  │  ┌──────────┬──────────┬─────────┬──────────┬──────────────────┐ │  │
│  │  │ id (PK)  │  title   │  status │ priority │    created_at    │ │  │
│  │  ├──────────┼──────────┼─────────┼──────────┼──────────────────┤ │  │
│  │  │    1     │ "Buy..."│ pending │  medium  │ 2025-12-09 ...   │ │  │
│  │  │    2     │ "Writ..."│complete │   high   │ 2025-12-09 ...   │ │  │
│  │  └──────────┴──────────┴─────────┴──────────┴──────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                      │
                      │ Traces
                      ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY PLATFORM                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │   Jaeger    │  │ Prometheus  │  │   Grafana   │                     │
│  │  (Traces)   │  │  (Metrics)  │  │ (Dashboards)│                     │
│  └─────────────┘  └─────────────┘  └─────────────┘                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Request Lifecycle (Detailed)

### Example: Creating a Task

```
1. CLIENT
   ├─ Action: User clicks "Create Task" button
   └─ HTTP Request:
      POST http://localhost:8000/api/v1/tasks
      Headers: Content-Type: application/json
      Body: {
        "title": "Buy groceries",
        "description": "Milk, eggs, bread",
        "priority": "high"
      }
      
      ↓
      
2. DOCKER CONTAINER (Port 8000)
   ├─ Container receives request
   └─ Forwards to uvicorn server
      
      ↓
      
3. main.py (FastAPI Application)
   ├─ CORS Middleware checks origin
   ├─ Request logging middleware
   └─ Routes request to appropriate endpoint
      
      ↓
      
4. routes.py → create_task()
   ├─ Function signature:
   │  async def create_task(
   │      task: TaskCreate,              ← Pydantic validates this
   │      db: Session = Depends(get_db)  ← Injected automatically
   │  )
   │
   ├─ Step 4a: Pydantic Validation (task.py)
   │  ├─ Check: title exists? ✓
   │  ├─ Check: title length 1-200? ✓
   │  ├─ Check: priority valid enum? ✓
   │  └─ If validation fails → Return 422 error
   │
   ├─ Step 4b: Get Database Session (dependencies.py)
   │  └─ get_db() creates session from pool
   │
   ├─ Step 4c: Create Database Model (database.py)
   │  └─ db_task = Task(**task.dict())
   │      - Converts Pydantic → SQLAlchemy
   │
   ├─ Step 4d: Save to Database
   │  ├─ db.add(db_task)
   │  ├─ db.commit()  → Executes SQL INSERT
   │  └─ db.refresh(db_task)  → Gets auto-generated ID
   │
   └─ Step 4e: Return Response
      └─ FastAPI converts Task model → JSON
      
      ↓
      
5. POSTGRESQL
   ├─ Receives SQL: INSERT INTO tasks (title, description, ...) VALUES (...)
   ├─ Executes query
   ├─ Assigns ID: 42
   └─ Returns row
      
      ↓
      
6. OPENTELEMETRY (Parallel Process)
   ├─ Creates trace_id: abc123...
   ├─ Creates spans:
   │  ├─ Span 1: HTTP Request (200ms total)
   │  ├─ Span 2: Validation (5ms)
   │  ├─ Span 3: Database Query (150ms)
   │  │  └─ Span 4: SQL INSERT (145ms)
   │  └─ Span 5: Serialization (10ms)
   │
   └─ Exports to Jaeger/Prometheus
      
      ↓
      
7. RESPONSE TO CLIENT
   HTTP/1.1 201 Created
   Content-Type: application/json
   
   {
     "id": 42,
     "title": "Buy groceries",
     "description": "Milk, eggs, bread",
     "status": "pending",
     "priority": "high",
     "created_at": "2025-12-10T10:30:00",
     "updated_at": null,
     "user_id": null
   }
```

---

## 📊 Data Flow Diagram

```
┌──────────────┐
│ Request Body │  {"title": "Task", "priority": "high"}
└──────┬───────┘
       │
       ↓
┌──────────────────────────────────┐
│   Pydantic Model (task.py)       │
│   class TaskCreate(BaseModel):   │
│       title: str                 │  ← Validates type
│       priority: TaskPriority     │  ← Validates enum
└──────┬───────────────────────────┘
       │ Validation passes ✓
       ↓
┌──────────────────────────────────┐
│  SQLAlchemy Model (database.py)  │
│  class Task(Base):               │
│      id = Column(Integer, ...)   │  ← Auto-generated
│      title = Column(String, ...) │  ← From Pydantic
│      created_at = Column(...)    │  ← Auto-set
└──────┬───────────────────────────┘
       │
       ↓
┌──────────────────────────────────┐
│     PostgreSQL Database          │
│  INSERT INTO tasks               │
│  (title, status, priority, ...)  │
│  VALUES ('Task', 'pending', ...) │
└──────┬───────────────────────────┘
       │
       ↓
┌──────────────────────────────────┐
│  Response (Pydantic again)       │
│  class TaskResponse(BaseModel):  │
│      id: int = 42                │  ← From DB
│      title: str = "Task"         │  ← From DB
│      created_at: datetime = ...  │  ← From DB
└──────┬───────────────────────────┘
       │
       ↓
┌──────────────┐
│ JSON Response│  {"id": 42, "title": "Task", ...}
└──────────────┘
```

---

## 🧩 File Relationships

```
main.py (Entry Point)
  │
  ├─→ Imports routes.py
  │     │
  │     ├─→ Uses task.py (Pydantic models)
  │     │     └─→ Validates request/response
  │     │
  │     ├─→ Uses database.py (SQLAlchemy models)
  │     │     └─→ Defines table schema
  │     │
  │     └─→ Uses dependencies.py
  │           └─→ Imports connection.py
  │                 └─→ Imports settings.py
  │                       └─→ Reads .env file
  │
  └─→ Imports tracing.py (OpenTelemetry)
        └─→ Instruments entire application
```

---

## 🎯 Layer Responsibilities

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  Files: main.py, routes.py                                   │
│  Job:   Handle HTTP, validate input, return responses        │
│  Tech:  FastAPI, Pydantic                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                     BUSINESS LOGIC LAYER                     │
│  Files: routes.py (functions like create_task)              │
│  Job:   Implement business rules, orchestrate operations    │
│  Tech:  Python functions                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    PERSISTENCE LAYER                         │
│  Files: database.py, connection.py                           │
│  Job:   Database operations, connection management          │
│  Tech:  SQLAlchemy ORM                                       │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                      DATA LAYER                              │
│  Tech:  PostgreSQL Database                                  │
│  Job:   Persistent storage                                   │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔍 Dependency Injection Explained

### Without Dependency Injection (Bad ❌)
```python
@router.post("/tasks")
async def create_task(task: TaskCreate):
    # Manually create session
    db = SessionLocal()
    
    try:
        db_task = Task(**task.dict())
        db.add(db_task)
        db.commit()
        return db_task
    finally:
        db.close()  # Easy to forget!
```

### With Dependency Injection (Good ✅)
```python
@router.post("/tasks")
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db)  # Automatic!
):
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    return db_task
    # Session automatically closed!
```

**Benefits:**
- ✅ No manual session management
- ✅ Automatic cleanup (even on errors)
- ✅ Easy to mock in tests
- ✅ Cleaner code

---

## 🧪 Testing Strategy Pyramid

```
                     /\
                    /  \
                   / E2E \          ← 5 tests (slow, complete flows)
                  /______\
                 /        \
                / Integr.  \       ← 15 tests (medium, with DB)
               /____________\
              /              \
             /      Unit       \   ← 30 tests (fast, isolated)
            /____________________\

Total: 50 tests = >85% coverage
```

### Test Examples:

**Unit Test** (Fast, no DB):
```python
def test_task_validation():
    task = TaskCreate(title="Test", priority="high")
    assert task.title == "Test"
    assert task.priority == "high"
```

**Integration Test** (With DB):
```python
def test_database_save(db):
    task = Task(title="Test", status="pending")
    db.add(task)
    db.commit()
    
    saved = db.query(Task).first()
    assert saved.title == "Test"
```

**E2E Test** (Full API):
```python
def test_create_and_get_task(client):
    # Create
    response = client.post("/api/v1/tasks", json={"title": "Test"})
    task_id = response.json()["id"]
    
    # Retrieve
    get_response = client.get(f"/api/v1/tasks/{task_id}")
    assert get_response.json()["title"] == "Test"
```

---

## 🐳 Docker Multi-Stage Build Explained

```
┌─────────────────────────────────────────────────────────────┐
│                    STAGE 1: BUILDER                          │
│  FROM python:3.11-slim as builder                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • Install gcc, build tools                             │ │
│  │ • Install Python packages                              │ │
│  │ • Compile dependencies                                 │ │
│  │                                                         │ │
│  │ Size: ~1.2 GB (includes build tools)                   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Copy only /root/.local
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    STAGE 2: RUNTIME                          │
│  FROM python:3.11-slim                                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • Copy compiled packages from builder                  │ │
│  │ • Copy application code                                │ │
│  │ • Set non-root user                                    │ │
│  │ • No build tools included                              │ │
│  │                                                         │ │
│  │ Size: ~200 MB (production-ready)                       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Final image
                            ↓
                   DEPLOYED TO AWS EKS
```

**Savings: 83% smaller image!**

---

## 📈 OpenTelemetry Trace Example

```
Trace ID: abc123def456  (Unique per request)
│
├─ Span: POST /api/v1/tasks [200ms total]
│  ├─ Span: Parse JSON [2ms]
│  ├─ Span: Validate with Pydantic [5ms]
│  ├─ Span: Get database session [1ms]
│  ├─ Span: Database operation [150ms]
│  │  └─ Span: SQL INSERT [145ms]
│  ├─ Span: Serialize response [3ms]
│  └─ Span: Send response [1ms]
│
└─ Total: 200ms (automatically calculated)
```

**What you see in Jaeger UI:**
- Timeline of all operations
- Which step was slowest (database: 150ms)
- Full context of the request
- Errors and exceptions

---

## 🎯 Tomorrow's Learning Path

```
Hour 1: Core Implementation
├─ 00-15: Structure + main.py
├─ 15-30: Models (Pydantic + SQLAlchemy)
├─ 30-45: API routes
└─ 45-60: Database + Config

Hour 2: Testing + Docker
├─ 00-15: Write tests
├─ 15-30: Create Dockerfile
├─ 30-45: Test everything
└─ 45-60: Build & run container

Hour 3: Additional Services
├─ 00-30: user-service (Flask)
├─ 30-60: auth-service (JWT)
└─ 60-75: notification-service (Lambda)
```

---

## 💡 Key Concepts to Master

1. **Separation of Concerns**
   - Pydantic = Validation
   - SQLAlchemy = Database
   - Routes = Business logic

2. **Dependency Injection**
   - FastAPI magic: `Depends()`
   - Auto cleanup

3. **Testing Pyramid**
   - More unit tests
   - Fewer E2E tests
   - Balance speed vs coverage

4. **Observability**
   - Trace every request
   - Find bottlenecks
   - Debug in production

5. **Containerization**
   - Multi-stage = smaller images
   - Non-root user = security
   - Health checks = reliability

---

**Study this tonight! 📚**
**See you tomorrow for implementation! 🚀**

---

*Visual guide prepared: December 9, 2025*
