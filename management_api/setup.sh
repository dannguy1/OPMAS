#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Setting up OPMAS Management API development environment...${NC}"

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ $(echo "$python_version < 3.9" | bc) -eq 1 ]]; then
    echo -e "${RED}Error: Python 3.9 or higher is required${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p /tmp/prometheus_multiproc

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from example...${NC}"
    cp example.env .env
    echo -e "${YELLOW}Please update .env with your configuration${NC}"
fi

# Initialize pre-commit hooks
echo -e "${YELLOW}Setting up pre-commit hooks...${NC}"
pre-commit install

# Create database if it doesn't exist
echo -e "${YELLOW}Checking database...${NC}"
if ! psql -lqt | cut -d \| -f 1 | grep -qw opmas_mgmt; then
    echo -e "${YELLOW}Creating database...${NC}"
    createdb opmas_mgmt
fi

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
alembic upgrade head

echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${YELLOW}To start the development server:${NC}"
echo -e "1. Activate the virtual environment: source venv/bin/activate"
echo -e "2. Run the server: python run.py"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL is not installed. Please install it first:"
    echo "sudo apt update"
    echo "sudo apt install postgresql postgresql-contrib"
    exit 1
fi

# Check if NATS server is installed
if ! command -v nats-server &> /dev/null; then
    echo "Installing NATS server..."
    curl -L https://raw.githubusercontent.com/nats-io/nats-server/master/scripts/install.sh | bash
fi

echo "Access the API documentation at:"
echo "- Swagger UI: http://localhost:8000/docs"
echo "- ReDoc: http://localhost:8000/redoc"
echo "- Health check: http://localhost:8000/health" 