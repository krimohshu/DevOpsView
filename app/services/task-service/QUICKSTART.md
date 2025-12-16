# 🚀 Task Service - Quick Start Guide

Get the Task Service running in 5 minutes!

---

## ⚡ Quick Start (Without Database)

The service can run without PostgreSQL for testing the API and tracing:

```bash
# 1. Navigate to service directory
cd app/services/task-service

# 2. Install dependencies
pip install -r requirements.txt

# 3. Enable OpenTelemetry tracing (optional)
export OTEL_ENABLED=true
export DEBUG=true

# 4. Start the server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Access the API:**
- Swagger UI: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- OpenAPI JSON: http://localhost:8000/openapi.json

---

## 📊 Test OpenTelemetry Tracing

Run the tracing test script to see distributed traces:

```bash
python3 test_tracing_simple.py
```

**Expected output:**
```json
{
    "name": "test_operation",
    "trace_id": "0x3e4cb2e013a80aa927f7139e2984d29c",
    "span_id": "0xedb26e807cddca5e",
    "attributes": {
        "test.type": "demo",
        "test.value": 42
    },
    "service.name": "task-service"
}
```

✅ **Success indicators:**
- JSON trace output with `trace_id` and `span_id`
- Service metadata (`service.name`, `service.version`)
- Attributes and events in spans

---

## 🗄️ Full Setup (With PostgreSQL)

For full functionality with database:

### 1. Start PostgreSQL (Docker)
```bash
docker run -d \
  --name taskdb \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=taskdb \
  -p 5432:5432 \
  postgres:15-alpine
```

### 2. Configure Environment
```bash
# Create .env file
cat > .env << 'ENVFILE'
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=taskdb
DB_USER=postgres
DB_PASSWORD=postgres

# OpenTelemetry
OTEL_ENABLED=true
OTEL_SERVICE_NAME=task-service

# App
DEBUG=true
ENVIRONMENT=development
ENVFILE
```

### 3. Initialize Database
```bash
python3 -c "from src.database import init_db; init_db()"
```

### 4. Start Service
```bash
uvicorn src.main:app --reload
```

### 5. Test CRUD Operations

**Create a task:**
```bash
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deploy to production",
    "description": "Deploy task-service v1.0.0",
    "priority": "high",
    "tags": ["deployment", "production"]
  }'
```

**List tasks:**
```bash
curl "http://localhost:8000/tasks?page=1&size=20"
```

**Get statistics:**
```bash
curl "http://localhost:8000/tasks/stats/summary"
```

---

## 🔍 View Traces with Jaeger (Optional)

To visualize traces in Jaeger:

### 1. Start Jaeger
```bash
docker run -d \
  --name jaeger \
  -p 16686:16686 \
  -p 4317:4317 \
  jaegertracing/all-in-one:latest
```

### 2. Configure Service
```bash
export OTEL_ENABLED=true
export OTEL_EXPORTER_ENDPOINT=http://localhost:4317
```

### 3. Make Requests
```bash
# Create some tasks to generate traces
for i in {1..5}; do
  curl -X POST "http://localhost:8000/tasks" \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"Task $i\",\"priority\":\"medium\"}"
done
```

### 4. View in Jaeger
Open http://localhost:16686 and search for `task-service` traces.

---

## ✅ Verification Checklist

Run these commands to verify setup:

```bash
# 1. Check app loads
python3 -c "from src.main import app; print(f'✅ App: {app.title}')"

# 2. Check database connection (requires PostgreSQL)
python3 -c "from src.database import check_database_connection; print('✅ DB OK' if check_database_connection() else '⚠️  DB not available')"

# 3. Check tracing setup
python3 test_tracing_simple.py

# 4. Check API routes
python3 -c "from src.main import app; print(f'✅ Routes: {len([r for r in app.routes if hasattr(r, \"methods\")])}')"
```

---

## 🐛 Troubleshooting

### Issue: Module not found errors
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: Database connection refused
**Solution:** PostgreSQL not running (expected without Docker/local install)
- App will work without DB for API schema/docs testing
- Database errors are expected if PostgreSQL isn't running
- Start PostgreSQL with Docker command above

### Issue: No traces appearing
**Solution:** Enable tracing
```bash
export OTEL_ENABLED=true
export DEBUG=true
uvicorn src.main:app --reload
```

Check startup logs for:
```
✅ OpenTelemetry tracing initialized
```

### Issue: Import errors in IDE
**Solution:** VS Code/PyCharm doesn't see installed packages
- Packages are installed and work at runtime
- IDE lint errors can be ignored
- Verify with: `pip list | grep opentelemetry`

---

## 📚 Next Steps

1. **Explore API**: Open http://localhost:8000/docs and try endpoints
2. **Read Code**: Start with `src/main.py` then `src/api/routes.py`
3. **Run Tests**: `python3 test_tracing_simple.py`
4. **Add Features**: Create new endpoints in `src/api/routes.py`
5. **Deploy**: Move to Phase 3 (Docker, Kubernetes, AWS)

---

## 📖 Documentation

- **Full Summary**: See `PHASE2_SUMMARY.md`
- **API Docs**: http://localhost:8000/docs (when running)
- **Main README**: See `../../README.md` for project overview
- **Configuration**: Check `src/config/settings.py` for all settings

---

**Questions?** Check `PHASE2_SUMMARY.md` for detailed architecture and implementation notes.
