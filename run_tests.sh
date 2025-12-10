#!/bin/bash
# Helper script to run tests with proper environment setup

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running GIA Tests${NC}"
echo ""

# Check if we're in a venv
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  No virtual environment detected${NC}"
    echo ""
    echo "Looking for virtual environment..."
    
    # Check common venv locations
    if [ -d "venv" ]; then
        echo -e "${GREEN}Found venv in ./venv${NC}"
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        echo -e "${GREEN}Found venv in ./.venv${NC}"
        source .venv/bin/activate
    elif [ -d "api/venv" ]; then
        echo -e "${GREEN}Found venv in ./api/venv${NC}"
        source api/venv/bin/activate
    else
        echo -e "${RED}❌ No virtual environment found${NC}"
        echo ""
        echo "Please either:"
        echo "  1. Activate your virtual environment manually, or"
        echo "  2. Create one: python3 -m venv venv && source venv/bin/activate"
        echo "  3. Install dependencies: cd api && pip install -r requirements.txt"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Virtual environment active: $VIRTUAL_ENV${NC}"
fi

echo ""

# Check if celery is installed
if ! python -c "import celery" 2>/dev/null; then
    echo -e "${RED}❌ Celery not found in current Python environment${NC}"
    echo ""
    echo "Installing dependencies..."
    cd api
    pip install -r requirements.txt
    cd ..
    echo ""
fi

# Check if pytest is installed
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Pytest not found, installing...${NC}"
    pip install pytest pytest-mock
    echo ""
fi

echo -e "${GREEN}✅ Environment ready${NC}"
echo ""

# Run pytest with any passed arguments
python -m pytest "$@"
