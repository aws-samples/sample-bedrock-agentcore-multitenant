#!/bin/bash

# Multi-Tenant Insurance Claims Platform - Development Starter

set -e

echo "🚀 Starting Multi-Tenant Insurance Claims Platform..."

# Port configuration
BACKEND_PORT=5001
FRONTEND_PORT=3000

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

kill_port() {
    local port=$1
    local pids=$(lsof -ti :$port 2>/dev/null)
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}Killing existing processes on port $port...${NC}"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

# Cleanup old processes first
echo -e "${BLUE}Cleaning up old processes...${NC}"

# Kill by PID files
if [ -f "backend.pid" ]; then
    pid=$(cat backend.pid)
    kill -9 $pid 2>/dev/null || true
    rm -f backend.pid
fi

if [ -f "frontend.pid" ]; then
    pid=$(cat frontend.pid)
    kill -9 $pid 2>/dev/null || true
    rm -f frontend.pid
fi

# Kill by port
kill_port $BACKEND_PORT
kill_port $FRONTEND_PORT

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}Error: Node.js/npm is not installed${NC}"
    exit 1
fi

if [ ! -f "backend/.env" ]; then
    echo -e "${RED}Error: backend/.env not found${NC}"
    echo "Run the notebook first to generate backend/.env"
    exit 1
fi

# Setup backend
echo -e "${BLUE}Setting up Python backend...${NC}"
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
cd ..

# Setup frontend
echo -e "${BLUE}Setting up React frontend...${NC}"
cd frontend

# Update .env with correct API URL
echo "REACT_APP_API_URL=http://localhost:$BACKEND_PORT" > .env

if [ ! -d "node_modules" ]; then
    npm install
fi
cd ..

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    [ -f backend.pid ] && kill -9 $(cat backend.pid) 2>/dev/null && rm -f backend.pid
    [ -f frontend.pid ] && kill -9 $(cat frontend.pid) 2>/dev/null && rm -f frontend.pid
    kill_port $BACKEND_PORT
    kill_port $FRONTEND_PORT
    echo -e "${GREEN}Cleanup completed${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Start backend
echo -e "${GREEN}Starting Flask backend on port $BACKEND_PORT...${NC}"
cd backend
source venv/bin/activate
PORT=$BACKEND_PORT python app.py 2>&1 | sed 's/^/[BACKEND] /' &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid
cd ..

sleep 3

if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}Error: Backend failed to start${NC}"
    exit 1
fi

# Start frontend
echo -e "${GREEN}Starting React frontend on port $FRONTEND_PORT...${NC}"
cd frontend
npm start 2>&1 | sed 's/^/[FRONTEND] /' &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid
cd ..

sleep 5

echo ""
echo -e "${GREEN}Services started successfully!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}Frontend:${NC} http://localhost:$FRONTEND_PORT"
echo -e "${BLUE}Backend API:${NC} http://localhost:$BACKEND_PORT"
echo -e "${BLUE}Health Check:${NC} http://localhost:$BACKEND_PORT/health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

wait
