#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}==>${NC} $1"
}

# Function to handle errors
handle_error() {
    echo -e "${RED}Error:${NC} $1"
    exit 1
}

# Check if we're in the project root
if [ ! -f "pyproject.toml" ]; then
    handle_error "Please run this script from the project root directory"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install development dependencies
print_status "Installing development dependencies..."
pip install -r requirements-dev.txt

# Build core component
print_status "Building core component..."
cd core
pip install -e .
cd ..

# Build management API
print_status "Building management API..."
cd management_api
pip install -e .
cd ..

# Run tests
print_status "Running tests..."
pytest

print_status "Build completed successfully!" 