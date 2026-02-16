#!/bin/bash
# Quick Integration Test Runner
# Starts backend server and runs integration tests

echo "============================================================"
echo "R-DIOS Integration Test Runner"
echo "============================================================"

# Check if backend is already running
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✓ Backend server is already running"
    BACKEND_RUNNING=true
else
    echo "✗ Backend server not running"
    echo "Starting backend server..."
    
    # Start backend in background
    cd "$(dirname "$0")"
    uvicorn api.main:app --reload > /dev/null 2>&1 &
    BACKEND_PID=$!
    
    echo "Waiting for server to start..."
    sleep 5
    
    # Check if server started
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "✓ Backend server started (PID: $BACKEND_PID)"
        BACKEND_RUNNING=false
    else
        echo "✗ Failed to start backend server"
        exit 1
    fi
fi

echo ""
echo "Running integration tests..."
echo ""

# Run tests
python3 test_integration.py
TEST_EXIT_CODE=$?

# Cleanup: stop backend if we started it
if [ "$BACKEND_RUNNING" = false ]; then
    echo ""
    echo "Stopping backend server (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
fi

echo ""
echo "============================================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✓ All tests passed!"
else
    echo "✗ Some tests failed (exit code: $TEST_EXIT_CODE)"
fi
echo "============================================================"

exit $TEST_EXIT_CODE
