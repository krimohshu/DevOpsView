# ✅ Phase 2 Session Checklist

**Date: December 10, 2025**  
**Duration: ~2-3 hours**  
**Mode: Tutorial with detailed explanations**

---

## 📋 Pre-Session Preparation (Tonight - Dec 9)

### Documents to Review:
- [ ] Read `phase-2-walkthrough-guide.md` (main guide)
- [ ] Print `phase-2-cheat-sheet.md` (quick reference)
- [ ] Study `phase-2-visual-guide.md` (architecture diagrams)
- [ ] Review your CV `Krishan_Shukla_CV_3Page.md` (we're implementing your expertise!)

### Concepts to Understand:
- [ ] Request flow diagram (Client → API → DB → Response)
- [ ] Pydantic vs SQLAlchemy (validation vs database)
- [ ] Dependency injection pattern
- [ ] Multi-stage Docker builds
- [ ] OpenTelemetry benefits

### Questions to Consider:
- [ ] Why use both Pydantic AND SQLAlchemy?
- [ ] What is dependency injection?
- [ ] How does OpenTelemetry work?
- [ ] Why multi-stage Docker builds?

---

## 🚀 Session Day Checklist (Dec 10)

### Before We Start:
- [ ] Open VS Code
- [ ] Have terminal ready
- [ ] Have browser ready (for testing)
- [ ] Coffee/tea prepared ☕
- [ ] Notebook for notes 📝

---

## 📝 Implementation Checklist

### **PART 1: task-service (FastAPI)** ⏱️ 45 minutes

#### Step 2.1: Directory Structure
- [ ] Create `app/services/task-service/` structure
- [ ] Understand each folder's purpose
- [ ] Create all `__init__.py` files
- **Questions to ask:** What is `__init__.py` for?

#### Step 2.2: Main Application (`main.py`)
- [ ] Create FastAPI app instance
- [ ] Add CORS middleware
- [ ] Create health check endpoint
- [ ] Add OpenTelemetry instrumentation
- **Questions to ask:** What does CORS do? Why health checks?

#### Step 2.3: Pydantic Models (`models/task.py`)
- [ ] Create `TaskStatus` enum
- [ ] Create `TaskPriority` enum
- [ ] Create `TaskBase` model
- [ ] Create `TaskCreate` model
- [ ] Create `TaskUpdate` model
- [ ] Create `TaskResponse` model
- [ ] Add validators
- **Questions to ask:** Why separate Create/Update/Response models?

#### Step 2.4: SQLAlchemy Models (`models/database.py`)
- [ ] Create `Base` declarative base
- [ ] Create `Task` table model
- [ ] Define all columns
- [ ] Add indexes
- [ ] Add timestamps
- **Questions to ask:** What are indexes for? Why timestamps?

#### Step 2.5: API Routes (`api/routes.py`)
- [ ] Create router
- [ ] Implement `create_task()` - POST
- [ ] Implement `get_tasks()` - GET all
- [ ] Implement `get_task()` - GET one
- [ ] Implement `update_task()` - PUT
- [ ] Implement `delete_task()` - DELETE
- [ ] Add error handling
- **Questions to ask:** Why use HTTP status codes? What is idempotency?

#### Step 2.6: Database Connection (`database/connection.py`)
- [ ] Create database engine
- [ ] Configure connection pool
- [ ] Create session factory
- **Questions to ask:** What is a connection pool? Why use it?

#### Step 2.7: Dependencies (`api/dependencies.py`)
- [ ] Create `get_db()` function
- [ ] Implement yield pattern
- [ ] Add cleanup logic
- **Questions to ask:** How does `Depends()` work?

#### Step 2.8: Configuration (`config/settings.py`)
- [ ] Create `Settings` class
- [ ] Define all configuration variables
- [ ] Load from environment
- [ ] Create `.env.example`
- **Questions to ask:** Why use environment variables?

#### Step 2.9: OpenTelemetry (`observability/tracing.py`)
- [ ] Create tracer setup
- [ ] Configure OTLP exporter
- [ ] Add auto-instrumentation
- **Questions to ask:** What is a span? What is a trace?

#### Step 2.10: Tests
- [ ] Create `conftest.py` with fixtures
- [ ] Write unit tests (`tests/unit/`)
  - [ ] `test_models.py` - Test Pydantic validation
  - [ ] `test_routes.py` - Test endpoint logic
- [ ] Write integration tests (`tests/integration/`)
  - [ ] `test_database.py` - Test DB operations
- [ ] Write E2E tests (`tests/e2e/`)
  - [ ] `test_api_e2e.py` - Test complete workflows
- **Questions to ask:** What's the difference between unit/integration/e2e?

#### Step 2.11: Docker
- [ ] Create `Dockerfile` (multi-stage)
- [ ] Create `.dockerignore`
- [ ] Add health check
- [ ] Add non-root user
- **Questions to ask:** Why multi-stage? Why non-root?

#### Step 2.12: Dependencies
- [ ] Create `requirements.txt`
- [ ] Create `requirements-dev.txt`
- [ ] Create `pyproject.toml`
- **Questions to ask:** What is pyproject.toml for?

#### Step 2.13: Documentation
- [ ] Create service `README.md`
- [ ] Document API endpoints
- [ ] Add setup instructions
- **Questions to ask:** What makes good documentation?

#### Step 2.14: Testing Everything
- [ ] Run tests: `pytest tests/ -v`
- [ ] Check coverage: `pytest --cov=src tests/`
- [ ] Run linter: `black src/`
- [ ] Build Docker: `docker build -t task-service .`
- [ ] Run container: `docker run -p 8000:8000 task-service`
- [ ] Test API: Open `http://localhost:8000/docs`
- [ ] Create a task via Swagger UI
- [ ] Verify in logs

---

### **BREAK** ☕ 5-10 minutes

---

### **PART 2: user-service (Flask)** ⏱️ 30 minutes

#### Step 2.15: Flask Structure
- [ ] Create directory structure
- [ ] Understand Flask vs FastAPI differences

#### Step 2.16: Flask Application
- [ ] Create `app.py`
- [ ] Define routes
- [ ] Add database models
- **Questions to ask:** How is Flask different from FastAPI?

#### Step 2.17: User CRUD Operations
- [ ] Create user endpoint
- [ ] List users endpoint
- [ ] Update user endpoint
- [ ] Delete user endpoint

#### Step 2.18: Tests & Docker
- [ ] Write Flask tests
- [ ] Create Dockerfile
- [ ] Test service

---

### **PART 3: auth-service (JWT)** ⏱️ 30 minutes

#### Step 2.19: Auth Structure
- [ ] Create directory structure
- [ ] Plan JWT flow

#### Step 2.20: JWT Implementation
- [ ] Create login endpoint
- [ ] Create register endpoint
- [ ] Create token refresh endpoint
- [ ] Implement password hashing
- **Questions to ask:** How does JWT work? Why hash passwords?

#### Step 2.21: Auth Tests
- [ ] Test login flow
- [ ] Test token validation
- [ ] Test authorization

---

### **PART 4: notification-service (Lambda)** ⏱️ 15 minutes

#### Step 2.22: Lambda Function
- [ ] Create `lambda_function.py`
- [ ] Create handler
- [ ] Add SNS integration
- **Questions to ask:** When to use Lambda vs container?

#### Step 2.23: Lambda Deployment Config
- [ ] Create `template.yaml` (SAM)
- [ ] Create Dockerfile for Lambda
- [ ] Test locally

---

### **PART 5: Final Review** ⏱️ 15 minutes

#### Code Review
- [ ] Review all services
- [ ] Discuss patterns used
- [ ] Identify improvements

#### Documentation
- [ ] Ensure all READMEs complete
- [ ] Check all comments
- [ ] Verify examples work

---

## 🎯 Learning Checkpoints

### After task-service:
Can you explain:
- [ ] How a request flows through the system?
- [ ] What Pydantic validation does?
- [ ] How database sessions are managed?
- [ ] What OpenTelemetry captures?
- [ ] Why we use dependency injection?

### After user-service:
Can you explain:
- [ ] Differences between FastAPI and Flask?
- [ ] When to use each framework?
- [ ] How Flask handles routes?

### After auth-service:
Can you explain:
- [ ] How JWT authentication works?
- [ ] Why we hash passwords?
- [ ] What makes a secure API?

### After notification-service:
Can you explain:
- [ ] When to use serverless?
- [ ] Lambda vs container trade-offs?
- [ ] Event-driven architecture benefits?

---

## 📊 Success Metrics

### Code Quality:
- [ ] >85% test coverage achieved
- [ ] All tests passing
- [ ] Linting passes (black, flake8)
- [ ] Type checking passes (mypy)

### Functionality:
- [ ] All services run locally
- [ ] Docker images build successfully
- [ ] API documentation auto-generated
- [ ] Health checks working

### Understanding:
- [ ] Can explain request flow
- [ ] Understand each file's purpose
- [ ] Know why each pattern is used
- [ ] Can debug issues independently

---

## 🐛 Common Issues & Solutions

### Issue: Import errors
**Solution:** Check `__init__.py` files exist, verify PYTHONPATH

### Issue: Database connection fails
**Solution:** Check DATABASE_URL, verify PostgreSQL running

### Issue: Tests fail
**Solution:** Check fixtures in conftest.py, verify test database

### Issue: Docker build fails
**Solution:** Check Dockerfile syntax, verify requirements.txt complete

### Issue: OpenTelemetry not working
**Solution:** Check OTEL_EXPORTER_OTLP_ENDPOINT, verify collector running

---

## 📚 Resources Ready

### During Session:
- [ ] FastAPI docs: https://fastapi.tiangolo.com
- [ ] Pydantic docs: https://docs.pydantic.dev
- [ ] SQLAlchemy docs: https://docs.sqlalchemy.org
- [ ] OpenTelemetry Python: https://opentelemetry.io/docs/languages/python/

### For Reference:
- [ ] phase-2-walkthrough-guide.md (detailed explanations)
- [ ] phase-2-cheat-sheet.md (quick reference)
- [ ] phase-2-visual-guide.md (diagrams)
- [ ] Krishan_Shukla_CV_3Page.md (your achievements to implement)

---

## ⏱️ Time Tracking

| Milestone | Target Time | Actual Time | Notes |
|-----------|-------------|-------------|-------|
| task-service setup | 15 min | | |
| task-service code | 20 min | | |
| task-service tests | 10 min | | |
| task-service Docker | 5 min | | |
| user-service | 30 min | | |
| auth-service | 30 min | | |
| notification-service | 15 min | | |
| Review & Q&A | 15 min | | |
| **TOTAL** | **2h 20min** | | |

---

## 🎓 Post-Session Tasks

### Immediate (Same Day):
- [ ] Commit all code to Git
- [ ] Push to GitHub
- [ ] Tag as `phase-2-complete`
- [ ] Update main README.md progress

### Within 24 Hours:
- [ ] Review all code created
- [ ] Test services again
- [ ] Document any issues found
- [ ] Prepare questions for next session

### Before Next Session:
- [ ] Read Phase 3 preparation docs
- [ ] Understand Kubernetes basics
- [ ] Review Helm chart concepts

---

## 💭 Reflection Questions

After the session, answer:
1. What was the most challenging concept?
2. What pattern did you find most useful?
3. What would you do differently?
4. What do you want to explore more?
5. How will you use this in real projects?

---

## 🎉 Completion Criteria

You've successfully completed Phase 2 when:
- ✅ All 4 services created and working
- ✅ >85% test coverage achieved
- ✅ All Docker images build successfully
- ✅ Can explain each file's purpose
- ✅ Can trace a request through the system
- ✅ Understand observability implementation
- ✅ Code committed to Git
- ✅ Documentation complete

---

## 📞 Session Support

### If You Need Help:
- ❓ Ask questions anytime (no question is too basic!)
- 🐛 We'll debug together (errors are learning opportunities)
- ⏸️ Request breaks when needed
- 🔄 Ask for re-explanation if unclear

### My Commitment:
- ✅ Explain every line of code
- ✅ Answer all questions thoroughly
- ✅ Provide real-world context
- ✅ Ensure you understand before moving on
- ✅ Share production best practices

---

## 🚀 Tomorrow's Session Goals

By end of session, you will:
1. ✅ Have 4 production-grade microservices
2. ✅ Understand modern Python development
3. ✅ Know REST API best practices
4. ✅ Implement comprehensive testing
5. ✅ Use Docker multi-stage builds
6. ✅ Add OpenTelemetry observability
7. ✅ Build portfolio-worthy code

---

**Print this checklist! ✓**  
**Use it during tomorrow's session!**

---

*Prepared: December 9, 2025*  
*For Session: December 10, 2025*  
*Ready to build amazing things! 🚀*
