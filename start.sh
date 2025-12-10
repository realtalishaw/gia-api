#!/bin/bash
# Simple shell script alternative for starting services
# Usage: ./start.sh [service1] [service2] ... or ./start.sh all

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Get Python executable
PYTHON_EXE=$(which python3 || which python)

# Function to start a service
start_service() {
    local service=$1
    local name=$2
    local color=$3
    shift 3
    local command="$@"
    
    echo -e "${color}🚀 Starting ${name}...${NC}"
    echo -e "${NC}   Command: $command${NC}"
    echo -e "${NC}   Python: ${PYTHON_EXE}${NC}"
    
    # Run in background and save PID
    eval "$command" > "/tmp/gia-${service}.log" 2>&1 &
    local pid=$!
    echo $pid > "/tmp/gia-${service}.pid"
    echo -e "${GREEN}✅ ${name} started (PID: $pid)${NC}"
    echo -e "${YELLOW}   Logs: tail -f /tmp/gia-${service}.log${NC}"
}

# Function to stop all services
stop_services() {
    echo -e "\n${YELLOW}🛑 Stopping all services...${NC}"
    for pidfile in /tmp/gia-*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            service=$(basename "$pidfile" .pid | sed 's/gia-//')
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${YELLOW}   Stopping $service (PID: $pid)...${NC}"
                kill "$pid" 2>/dev/null || true
            fi
            rm -f "$pidfile"
        fi
    done
    echo -e "${GREEN}✅ All services stopped${NC}"
}

# Trap Ctrl+C
trap stop_services EXIT INT TERM

# Check arguments
if [ $# -eq 0 ]; then
    echo -e "${CYAN}GIA Services Startup${NC}"
    echo -e "${CYAN}====================${NC}"
    echo ""
    echo "Available services:"
    echo "  1. API Server"
    echo "  2. Task Worker"
    echo "  3. Context Worker"
    echo "  4. Flower Monitoring"
    echo "  5. Admin Panel"
    echo "  a. All services"
    echo ""
    read -p "Select services (comma-separated numbers, 'a' for all): " selection
    
    if [ "$selection" = "a" ]; then
        SERVICES=("api" "task-worker" "context-worker" "flower" "web")
    else
        SERVICES=()
        IFS=',' read -ra SELECTED <<< "$selection"
        for num in "${SELECTED[@]}"; do
            case $num in
                1) SERVICES+=("api") ;;
                2) SERVICES+=("task-worker") ;;
                3) SERVICES+=("context-worker") ;;
                4) SERVICES+=("flower") ;;
                5) SERVICES+=("web") ;;
            esac
        done
    fi
elif [ "$1" = "all" ]; then
    SERVICES=("api" "task-worker" "context-worker" "flower" "web")
else
    SERVICES=("$@")
fi

# Start selected services
for service in "${SERVICES[@]}"; do
    case $service in
        api)
            start_service "api" "API Server" "$CYAN" "cd api && ${PYTHON_EXE} -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
            ;;
        task-worker)
            start_service "task-worker" "Task Worker" "$GREEN" "cd api && ${PYTHON_EXE} -m celery -A worker.celery_app worker --loglevel=info --queues=agent_initialization_queue,agent_results_queue"
            ;;
        context-worker)
            start_service "context-worker" "Context Worker" "$MAGENTA" "cd api && ${PYTHON_EXE} -m celery -A context_engine.worker.celery_app worker --loglevel=info --queues=context_queue"
            ;;
        flower)
            start_service "flower" "Flower Monitoring" "$YELLOW" "cd api && ${PYTHON_EXE} -m celery -A worker.celery_app flower --port=5555 --address=0.0.0.0 --unauthenticated_api"
            ;;
        web)
            start_service "web" "Admin Panel" "$BLUE" "cd admin-panel && npm run dev"
            ;;
        *)
            echo -e "${RED}⚠️  Unknown service: $service${NC}"
            ;;
    esac
    sleep 1
done

echo -e "\n${GREEN}✅ All services started!${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}\n"

# Wait for all background processes
wait
