#!/bin/sh

# Development entrypoint script
# Starts both frontend and backend with hot-reloading

echo "Starting Task Management Application in Development Mode..."

# Start the frontend development server in the background
echo "Starting frontend development server..."
cd /app/frontend
npm run dev &
FRONTEND_PID=$!

# Start the backend development server with hot-reloading
echo "Starting backend development server with auto-reload..."
cd /app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Function to handle shutdown
cleanup() {
    echo "Shutting down servers..."
    kill $FRONTEND_PID $BACKEND_PID 2>/dev/null
    exit 0
}

# Trap signals for graceful shutdown
trap cleanup SIGINT SIGTERM

# Wait for both processes
wait
