#!/bin/bash

# Auto-Certy Startup Script
echo "🎓 Starting Auto-Certy..."

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Check if backend is already running
if check_port 8000; then
    echo "⚠️  Backend server already running on port 8000"
else
    echo "🚀 Starting backend server..."
    cd backend
    source venv/bin/activate 2>/dev/null || {
        echo "❌ Backend virtual environment not found. Run setup.sh first."
        exit 1
    }
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    echo "✅ Backend started (PID: $BACKEND_PID)"
    cd ..
fi

# Wait a moment for backend to start
sleep 3

# Check if frontend is already running
if check_port 8501; then
    echo "⚠️  Frontend already running on port 8501"
else
    echo "🎨 Starting frontend..."
    cd frontend
    source venv/bin/activate 2>/dev/null || {
        echo "❌ Frontend virtual environment not found. Run setup.sh first."
        exit 1
    }
    streamlit run app.py &
    FRONTEND_PID=$!
    echo "✅ Frontend started (PID: $FRONTEND_PID)"
    cd ..
fi

echo ""
echo "🌐 Application URLs:"
echo "   Backend API: http://localhost:8000"
echo "   Frontend UI: http://localhost:8501"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit' INT
wait
