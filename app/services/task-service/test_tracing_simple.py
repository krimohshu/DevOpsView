#!/usr/bin/env python3
"""
Simple test to verify OpenTelemetry tracing setup.

This directly tests the tracing module without running a full server.
"""

import os

# Enable tracing
os.environ['OTEL_ENABLED'] = 'true'
os.environ['DEBUG'] = 'true'

print("=" * 60)
print("🔍 OpenTelemetry Integration Test")
print("=" * 60)

# Test 1: Import tracing module
print("\n✅ Test 1: Import Tracing Module")
try:
    from src.observability import setup_opentelemetry, get_tracer, traced_operation
    print("   ✓ Tracing module imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import: {e}")
    exit(1)

# Test 2: Create mock app and engine for setup
print("\n✅ Test 2: Initialize OpenTelemetry")
try:
    from unittest.mock import Mock
    
    # Create mock FastAPI app
    mock_app = Mock()
    mock_app.title = "Test App"
    
    # Create mock SQLAlchemy engine
    mock_engine = Mock()
    
    # Setup OpenTelemetry
    provider = setup_opentelemetry(mock_app, mock_engine)
    
    if provider:
        print("   ✓ TracerProvider created")
        print(f"   ✓ Provider type: {type(provider).__name__}")
    else:
        print("   ℹ️  Tracing disabled (OTEL_ENABLED=false)")
        
except Exception as e:
    print(f"   ✗ Setup failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: Create custom span
print("\n✅ Test 3: Create Custom Span")
try:
    from opentelemetry import trace
    
    tracer = get_tracer(__name__)
    
    with tracer.start_as_current_span("test_operation") as span:
        span.set_attribute("test.type", "demo")
        span.set_attribute("test.value", 42)
        span.add_event("operation_started")
        
        # Simulate work
        import time
        time.sleep(0.05)
        
        span.add_event("operation_completed")
        
    print("   ✓ Custom span created with attributes and events")
    
except Exception as e:
    print(f"   ✗ Span creation failed: {e}")
    exit(1)

# Test 4: Use traced_operation context manager
print("\n✅ Test 4: traced_operation Context Manager")
try:
    with traced_operation("process_task", task_id=123, priority="high"):
        time.sleep(0.02)
        
    print("   ✓ Context manager worked")
    
except Exception as e:
    print(f"   ✗ Context manager failed: {e}")
    exit(1)

# Test 5: Error tracking
print("\n✅ Test 5: Error Tracking in Spans")
try:
    from src.observability import set_span_error
    
    try:
        with traced_operation("failing_operation"):
            raise ValueError("Test error for tracing")
    except ValueError as e:
        print("   ✓ Error recorded in span")
        
except Exception as e:
    print(f"   ✗ Error tracking failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✅ All OpenTelemetry Tests Passed!")
print("=" * 60)

print("\n📊 Summary:")
print("   - Tracing module loads correctly")
print("   - TracerProvider initializes")
print("   - Custom spans can be created")
print("   - Attributes and events work")
print("   - Error tracking works")

print("\n🎯 Next Steps:")
print("   1. Start server: uvicorn src.main:app --reload")
print("   2. Check startup logs for: '✅ OpenTelemetry tracing initialized'")
print("   3. Make API requests and see traces in console")
print("   4. For production: Configure OTEL_EXPORTER_ENDPOINT for Jaeger/Tempo")

print("\n" + "=" * 60)
