#!/usr/bin/env python3
"""
Test script to demonstrate OpenTelemetry tracing with console exporter.

This script:
1. Starts the FastAPI app with tracing enabled
2. Makes sample API requests
3. Shows traces in console output

Run: python3 test_tracing.py
"""

import os
import time
import sys
from multiprocessing import Process

# Enable tracing with console exporter
os.environ['OTEL_ENABLED'] = 'true'
os.environ['DEBUG'] = 'true'
os.environ['LOG_LEVEL'] = 'INFO'


def start_server():
    """Start uvicorn server"""
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=False,  # Reduce noise
    )


def make_requests():
    """Make sample API requests to generate traces"""
    import requests
    
    base_url = "http://127.0.0.1:8000"
    
    print("\n" + "=" * 60)
    print("🧪 Testing OpenTelemetry Tracing")
    print("=" * 60)
    
    # Wait for server to start
    print("\n⏳ Waiting for server to start...")
    for i in range(30):
        try:
            response = requests.get(f"{base_url}/health", timeout=1)
            if response.status_code == 200:
                print("✅ Server is ready!\n")
                break
        except requests.exceptions.RequestException:
            time.sleep(0.5)
    else:
        print("❌ Server failed to start")
        return
    
    # Test 1: Health check
    print("=" * 60)
    print("Test 1: Health Check (GET /health)")
    print("=" * 60)
    response = requests.get(f"{base_url}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    time.sleep(1)  # Let trace export
    
    # Test 2: List tasks (empty)
    print("\n" + "=" * 60)
    print("Test 2: List Tasks (GET /tasks)")
    print("=" * 60)
    response = requests.get(f"{base_url}/tasks")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total tasks: {data.get('total', 0)}")
    time.sleep(1)
    
    # Test 3: Create task (will fail without DB, but trace will show)
    print("\n" + "=" * 60)
    print("Test 3: Create Task (POST /tasks)")
    print("=" * 60)
    task_data = {
        "title": "Test OpenTelemetry Tracing",
        "description": "Verify distributed tracing works",
        "priority": "high",
        "tags": ["testing", "observability"]
    }
    try:
        response = requests.post(f"{base_url}/tasks", json=task_data)
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            print(f"Task created: {response.json()['id']}")
        else:
            print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Request failed: {e}")
    
    time.sleep(2)  # Let traces export
    
    print("\n" + "=" * 60)
    print("✅ Test Complete!")
    print("=" * 60)
    print("\n📊 Check console output above for OpenTelemetry traces")
    print("   Look for JSON blocks with:")
    print("   - trace_id")
    print("   - span_id")
    print("   - name (operation name)")
    print("   - attributes (HTTP method, status, etc.)")
    print("\n⚠️  Note: Database errors are expected (PostgreSQL not running)")
    print("   The traces will still show the full request flow\n")


if __name__ == "__main__":
    print("=" * 60)
    print("🔍 OpenTelemetry Tracing Demo")
    print("=" * 60)
    print("\nThis demo will:")
    print("1. Start FastAPI server with OpenTelemetry")
    print("2. Make sample HTTP requests")
    print("3. Show distributed traces in console")
    print("\nPress Ctrl+C to stop\n")
    
    # Start server in background
    server_process = Process(target=start_server, daemon=True)
    server_process.start()
    
    try:
        # Make test requests
        make_requests()
        
        # Keep running to see more traces
        print("Server still running... Press Ctrl+C to stop")
        server_process.join()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping server...")
        server_process.terminate()
        server_process.join(timeout=5)
        print("✅ Server stopped")
