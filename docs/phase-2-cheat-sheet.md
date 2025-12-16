# 🎯 Phase 2 Quick Reference - Cheat Sheet

**For Session: December 10, 2025**

---

## 📁 File Structure Quick Map

```
task-service/
├── src/
│   ├── main.py              → FastAPI app (entry point)
│   ├── api/
│   │   ├── routes.py        → CRUD endpoints (POST, GET, PUT, DELETE)
│   │   └── dependencies.py  → Database session provider
│   ├── models/
│   │   ├── task.py          → Pydantic (validation)
│   │   └── database.py      → SQLAlchemy (DB schema)
│   ├── database/
│   │   └── connection.py    → PostgreSQL connection
│   ├── observability/
│   │   └── tracing.py       → OpenTelemetry setup
│   └── config/
│       └── settings.py      → Environment variables
├── tests/
│   ├── conftest.py          → Test fixtures
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── Dockerfile               → Multi-stage build
└── requirements.txt         → Dependencies
```

---

## 🔄 Request Flow (memorize this!)

```
1. Client sends HTTP request
2. main.py receives it (FastAPI)
3. routes.py handles endpoint
4. dependencies.py provides DB session
5. database.py queries PostgreSQL
6. task.py validates response
7. OpenTelemetry traces entire flow
8. Client receives JSON response
```

---

## 🎯 Key Differences

### Pydantic vs SQLAlchemy
| Pydantic (task.py) | SQLAlchemy (database.py) |
|--------------------|-------------------------|
| API validation | Database schema |
| Request/Response | Database operations |
| Type checking | SQL queries |
| Memory only | PostgreSQL storage |

### FastAPI vs Flask
| FastAPI | Flask |
|---------|-------|
| Async support | Sync by default |
| Auto validation | Manual validation |
| Auto docs | No auto docs |
| Type hints required | Optional |
| Modern (2018) | Mature (2010) |

---

## 🔥 Most Important Files (Priority Order)

1. **main.py** - Start here, bootstraps everything
2. **models/task.py** - Understand validation first
3. **api/routes.py** - Core business logic
4. **models/database.py** - Database schema
5. **conftest.py** - Testing setup

---

## 💻 Common Commands

```bash
# Run service locally
uvicorn src.main:app --reload

# Run tests
pytest tests/ -v

# Test with coverage
pytest --cov=src tests/

# Build Docker image
docker build -t task-service:latest .

# Run container
docker run -p 8000:8000 task-service:latest

# Access API docs
# Open browser: http://localhost:8000/docs
```

---

## 📊 API Endpoints (RESTful)

```
POST   /api/v1/tasks          Create task
GET    /api/v1/tasks          List all tasks
GET    /api/v1/tasks/{id}     Get one task
PUT    /api/v1/tasks/{id}     Update task
DELETE /api/v1/tasks/{id}     Delete task
GET    /health                Health check
GET    /metrics               Prometheus metrics
```

---

## 🔧 Key Dependencies

```
fastapi          → Web framework
uvicorn          → ASGI server
sqlalchemy       → ORM (database)
pydantic         → Validation
opentelemetry    → Tracing
pytest           → Testing
```

---

## 🎨 Code Patterns to Remember

### Pattern 1: Dependency Injection
```python
@router.post("/tasks")
async def create_task(
    task: TaskCreate,                    # Auto-validated
    db: Session = Depends(get_db)        # Auto-injected
):
    # db session is automatically provided and closed
```

### Pattern 2: Pydantic Validation
```python
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    # FastAPI automatically validates this!
```

### Pattern 3: Error Handling
```python
if not task:
    raise HTTPException(
        status_code=404,
        detail="Task not found"
    )
```

---

## 🧪 Testing Pattern

```python
def test_create_task(client):
    # Arrange
    task_data = {"title": "Test"}
    
    # Act
    response = client.post("/api/v1/tasks", json=task_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["title"] == "Test"
```

---

## 🐳 Docker Multi-Stage Benefits

```
Single-stage image:  ~1.2 GB
Multi-stage image:   ~200 MB (83% smaller!)

Why?
- Builder stage: Install all dependencies
- Runtime stage: Copy only what's needed
- No gcc, no build tools in production
```

---

## 🔍 OpenTelemetry Magic

```python
# Just 3 lines to instrument entire app!
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

FastAPIInstrumentor.instrument_app(app)
# Now every request is automatically traced!
```

---

## ⚡ Performance Tips

1. **Database Connection Pool**: Reuse connections
   ```python
   engine = create_engine(url, pool_size=10)
   ```

2. **Async Endpoints**: Handle more concurrent requests
   ```python
   async def get_tasks():  # async = non-blocking
   ```

3. **Indexes**: Speed up queries
   ```python
   Column(String, index=True)  # Creates DB index
   ```

---

## 🔒 Security Checklist

- ✅ Input validation (Pydantic)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Non-root Docker user
- ✅ Environment variables for secrets
- ✅ CORS configuration
- ✅ Rate limiting (to add)

---

## 📈 Testing Levels

```
Unit Tests        → Test single functions (fast)
Integration Tests → Test with database (medium)
E2E Tests         → Test full API workflow (slow)

Pyramid:
       /\
      /E2E\        10%
     /----\
    / Int  \       30%
   /--------\
  /   Unit   \     60%
 /____________\
```

---

## 🎯 Success Criteria for Tomorrow

- [ ] Understand request flow diagram
- [ ] Know difference: Pydantic vs SQLAlchemy
- [ ] Can explain dependency injection
- [ ] Understand multi-stage Docker build
- [ ] Know why OpenTelemetry is important
- [ ] Can run and test the service locally

---

## 🚀 Tomorrow's Workflow

```
For each file:
1. I explain the purpose (2 min)
2. I explain the code line-by-line (5 min)
3. I create the file (1 min)
4. We test it together (2 min)
5. Questions & clarifications (2 min)

Total per file: ~12 minutes
```

---

## 💡 Mental Model

**Think of the service as layers:**

```
┌─────────────────────────┐
│  HTTP (FastAPI)         │  ← API Layer (routes.py)
├─────────────────────────┤
│  Validation (Pydantic)  │  ← Data Layer (task.py)
├─────────────────────────┤
│  Business Logic         │  ← Service Layer (routes.py)
├─────────────────────────┤
│  Database (SQLAlchemy)  │  ← Persistence Layer (database.py)
├─────────────────────────┤
│  PostgreSQL             │  ← Storage
└─────────────────────────┘
```

Each layer has a specific responsibility!

---

## 📚 Recommended Reading (Optional)

- FastAPI Docs: https://fastapi.tiangolo.com
- Pydantic Docs: https://docs.pydantic.dev
- SQLAlchemy Tutorial: https://docs.sqlalchemy.org/en/20/tutorial/
- OpenTelemetry Python: https://opentelemetry.io/docs/languages/python/

---

## ❓ FAQ

**Q: Why not just use Flask?**
A: FastAPI has async support, auto-validation, and auto-docs

**Q: Do I need to know async/await?**
A: Basic understanding helps, but we'll explain as we go

**Q: Why PostgreSQL instead of MySQL?**
A: Better JSON support, more features, industry standard for modern apps

**Q: Can I use this in production?**
A: Yes! This follows production best practices

---

## 🎓 Learning Objectives

After tomorrow, you'll be able to:
- ✅ Build production-grade REST APIs
- ✅ Implement proper validation
- ✅ Write comprehensive tests
- ✅ Containerize applications
- ✅ Add observability (tracing)
- ✅ Follow REST best practices
- ✅ Understand microservices architecture

---

**Print this sheet and keep it handy tomorrow! 📋**

See you tomorrow for the implementation! 🚀
