#!/bin/bash

# Map Poster Generator - Start Script

echo "🗺️  Map Poster Generator - Web UI"
echo "=================================="
echo ""

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "✓ Using uv for Python environment"
    PYTHON_CMD="uv run python"
else
    echo "✓ Using Python directly (make sure dependencies are installed)"
    PYTHON_CMD="python"
fi

# Function to cleanup processes
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    
    echo "✓ All servers stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT TERM

# Start backend
echo "🚀 Starting backend server on port 8000..."
cd "$(dirname "$0")"
$PYTHON_CMD api_server.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend started successfully
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "❌ Backend server failed to start"
    exit 1
fi

echo "✓ Backend server started (PID: $BACKEND_PID)"

# Start frontend
echo "🚀 Starting frontend server on port 3000..."
cd webapp

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

# Check if frontend started successfully
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo "❌ Frontend server failed to start"
    kill $BACKEND_PID
    exit 1
fi

echo "✓ Frontend server started (PID: $FRONTEND_PID)"
echo ""
echo "=================================="
echo "✨ Application is running!"
echo ""
echo "📱 Web UI:  http://localhost:3000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "=================================="
echo ""

# Wait for processes
wait