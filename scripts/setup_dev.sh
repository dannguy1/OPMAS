#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up OPMAS development environment...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p core/logs
mkdir -p core/config/ssh_keys
mkdir -p management_api/logs
mkdir -p ui/logs

# Create environment files from templates
echo -e "${YELLOW}Creating environment files...${NC}"

# Core environment
cat > core/.env << EOL
# Core Backend
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/opmas
NATS_URL=nats://localhost:4222
NATS_USER=opmas
NATS_PASSWORD=opmas
NATS_CLUSTER=opmas-cluster
EOL

# Management API environment
cat > management_api/.env << EOL
# Management API
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/opmas
SECRET_KEY=development-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOL

# UI environment
cat > ui/.env << EOL
# Frontend UI
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
EOL

# Create docker-compose.yml for development
echo -e "${YELLOW}Creating docker-compose.yml...${NC}"
cat > docker-compose.yml << EOL
version: '3.8'

services:
  postgres:
    image: postgres:latest
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: opmas
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  nats:
    image: nats:latest
    command: --user opmas --pass opmas --cluster opmas-cluster
    ports:
      - "4222:4222"  # Client connections
      - "8222:8222"  # HTTP monitoring
      - "6222:6222"  # Cluster connections
    healthcheck:
      test: ["CMD", "nats-server", "--help"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
EOL

# Start the services
echo -e "${YELLOW}Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Initialize the database
echo -e "${YELLOW}Initializing database...${NC}"
cd core
python -m pip install -r requirements.txt
python -m alembic upgrade head
cd ..

echo -e "${GREEN}Development environment setup complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Start the core backend: cd core && python -m opmas.main"
echo "2. Start the management API: cd management_api && uvicorn opmas_mgmt_api.main:app --reload"
echo "3. Start the UI: cd ui && npm run dev" 