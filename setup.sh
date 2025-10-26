#!/bin/bash

# Project Samarth Setup Script
# Automates the setup process for local development

echo "========================================="
echo "   Project Samarth - Setup Script"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then 
    echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"
else
    echo -e "${RED}✗ Python 3.9+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠ Virtual environment already exists. Skipping...${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ Pip upgraded${NC}"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create necessary directories
echo ""
echo "Creating project directories..."
mkdir -p data/cache
mkdir -p logs
mkdir -p tests
echo -e "${GREEN}✓ Directories created${NC}"

# Setup environment file
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
    echo -e "${YELLOW}⚠ Please edit .env file and add your DATA_GOV_API_KEY${NC}"
    echo -e "${YELLOW}  Get your API key from: https://data.gov.in/${NC}"
else
    echo -e "${YELLOW}⚠ .env file already exists. Skipping...${NC}"
fi

# Create __init__.py files
echo ""
echo "Creating __init__.py files..."
touch src/__init__.py
touch tests/__init__.py
echo -e "${GREEN}✓ Package files created${NC}"

# Run basic tests
echo ""
echo "Running basic system checks..."
python3 -c "import streamlit; import pandas; import plotly; print('All core libraries imported successfully')"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ System check passed${NC}"
else
    echo -e "${RED}✗ System check failed${NC}"
    exit 1
fi

# Summary
echo ""
echo "========================================="
echo "   Setup Complete!"
echo "========================================="
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Edit .env file and add your DATA_GOV_API_KEY"
echo "   Get your key from: https://data.gov.in/"
echo ""
echo "2. Run the application:"
echo "   ${YELLOW}streamlit run app.py${NC}"
echo ""
echo "3. Access the application at:"
echo "   ${YELLOW}http://localhost:8501${NC}"
echo ""
echo "4. (Optional) Run tests:"
echo "   ${YELLOW}pytest tests/${NC}"
echo ""
echo -e "${GREEN}For more information, see README.md${NC}"
echo ""