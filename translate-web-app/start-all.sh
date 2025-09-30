#!/bin/bash

echo "Starting Document Translation Web App..."

# Check if .env file exists in project root
if [ ! -f "../.env" ]; then
    echo "Error: .env file not found in project root!"
    echo "Please create it from .env.example and add your API keys"
    echo "Expected location: $(pwd)/../.env"
    exit 1
fi

# Install dependencies if needed
echo "Checking dependencies..."
cd backend && npm install && cd ..
cd worker && npm install && cd ..
cd frontend && npm install && cd ..

# Start all services
echo "Starting backend server on port 3001..."
cd backend && npm start &
BACKEND_PID=$!

echo "Starting worker service..."
cd ../worker && npm start &
WORKER_PID=$!

echo "Starting frontend on port 3000..."
cd ../frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "Services started:"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:3001"
echo "- Process IDs: Backend=$BACKEND_PID, Worker=$WORKER_PID, Frontend=$FRONTEND_PID"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "echo 'Stopping services...'; kill $BACKEND_PID $WORKER_PID $FRONTEND_PID; exit" INT
wait