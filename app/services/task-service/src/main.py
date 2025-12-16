"""
Task Service - Main Application Entry Point

This is the heart of the task-service microservice.
It creates the FastAPI application and configures all middleware.

Author: Krishan Shukla
Date: December 9, 2025
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ============================================================================
# CREATE FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="Task Service API",
    description="""
    Production-grade task management microservice with:
    - Full CRUD operations for tasks
    - OpenTelemetry distributed tracing
    - Prometheus metrics
    - Comprehensive error handling
    - >85% test coverage
    
    Implements patterns from DNB Bank's 200+ microservices architecture.
    """,
    version="1.0.0",
    docs_url="/docs",       # Swagger UI: http://localhost:8000/docs
    redoc_url="/redoc",     # ReDoc: http://localhost:8000/redoc
    openapi_url="/openapi.json"  # OpenAPI schema
)


# ============================================================================
# CORS MIDDLEWARE CONFIGURATION
# ============================================================================
# CORS = Cross-Origin Resource Sharing
# Allows frontend applications (React, Angular, Vue) to call this API
# from different domains/ports

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Production: Use specific domains ["https://app.example.com"]
    allow_credentials=True,     # Allow cookies and auth headers
    allow_methods=["*"],        # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],        # Allow all headers
)


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - Returns API information and navigation links.
    
    This is the first endpoint users see when visiting the service.
    Provides helpful navigation to documentation and health checks.
    """
    return {
        "service": "task-service",
        "version": "1.0.0",
        "message": "Welcome to Task Service API - Production-grade task management",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "api": "/api/v1"
        },
        "status": "operational"
    }


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================
# Critical for:
# 1. Kubernetes liveness/readiness probes
# 2. Load balancer health checks
# 3. Monitoring systems (Prometheus, Datadog)
# 4. Achieving 99.95% uptime SLA

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for Kubernetes and monitoring systems.
    
    Returns:
        dict: Service health status
        
    Kubernetes uses this to:
    - Liveness probe: Is the service running?
    - Readiness probe: Can it accept traffic?
    
    If this endpoint fails → Kubernetes restarts the pod
    """
    return {
        "status": "healthy",
        "service": "task-service",
        "version": "1.0.0"
    }


# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Runs once when the application starts.
    
    Use this for:
    - Database connection pool initialization
    - Loading configuration
    - Setting up OpenTelemetry tracing
    - Pre-loading ML models
    """
    print("=" * 60)
    print("🚀 Task Service Starting...")
    print("=" * 60)
    print(f"📝 Service: task-service")
    print(f"🔢 Version: 1.0.0")
    print(f"📚 Docs: http://localhost:8000/docs")
    print(f"💚 Health: http://localhost:8000/health")
    print("=" * 60)
    
    # Initialize OpenTelemetry tracing
    from .observability import setup_opentelemetry
    from .database import engine
    
    try:
        tracer_provider = setup_opentelemetry(app, engine)
        if tracer_provider:
            # Store provider for graceful shutdown
            app.state.tracer_provider = tracer_provider
            print("✅ OpenTelemetry tracing initialized")
        else:
            print("ℹ️  OpenTelemetry tracing disabled (OTEL_ENABLED=false)")
    except Exception as e:
        print(f"⚠️  OpenTelemetry setup failed: {e}")
        print("   Service will continue without tracing")


# ============================================================================
# SHUTDOWN EVENT
# ============================================================================

@app.on_event("shutdown")
async def shutdown_event():
    """
    Runs once when the application shuts down.
    
    Use this for:
    - Closing database connections
    - Flushing logs
    - Graceful shutdown of tracing
    """
    print("=" * 60)
    print("🛑 Task Service Shutting Down...")
    print("=" * 60)
    
    # Gracefully shutdown OpenTelemetry tracing
    if hasattr(app.state, 'tracer_provider') and app.state.tracer_provider:
        try:
            # Force flush any pending spans
            app.state.tracer_provider.force_flush()
            print("✅ OpenTelemetry spans flushed")
        except Exception as e:
            print(f"⚠️  Failed to flush traces: {e}")


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

# Import and include task routes
from .api import router as task_router

app.include_router(task_router)

print("✅ API Routes registered: /tasks")


# ============================================================================
# MAIN EXECUTION
# ============================================================================
# This allows running the app directly: python src/main.py
# In production, use: uvicorn src.main:app --host 0.0.0.0 --port 8000

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",      # Listen on all network interfaces
        port=8000,           # Standard port for microservices
        reload=True,         # Auto-reload on code changes (dev only!)
        log_level="info"     # Logging level
    )
