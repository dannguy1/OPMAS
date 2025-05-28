#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default to development
ENV=${1:-dev}
LOG_FILE="startup_${ENV}.log"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Function to log messages
log() {
    echo -e "${2}${TIMESTAMP} - $1${NC}" | tee -a "$LOG_FILE"
}

# Function to check if services are running
check_services_running() {
    local services_running=$(docker ps --format '{{.Names}}' | grep -E 'opmas-(postgres|redis|nats|management_api|backend|ui|prometheus|grafana)')
    if [ ! -z "$services_running" ]; then
        log "Found running services:" "$YELLOW"
        echo "$services_running"
        read -p "Do you want to stop existing services and start fresh? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log "Stopping existing services..." "$YELLOW"
            docker compose down
        else
            log "Using existing services" "$GREEN"
            return 0
        fi
    fi
    return 1
}

# Function to check service health
check_service_health() {
    local service=$1
    local type=$2
    local max_retries=30
    local retry_count=0
    local sleep_time=2

    log "Checking health of $service..." "$YELLOW"
    
    while [ $retry_count -lt $max_retries ]; do
        case $type in
            "postgres")
                if docker exec opmas-postgres-1 pg_isready -U opmas > /dev/null 2>&1; then
                    log "$service is healthy" "$GREEN"
                    return 0
                fi
                ;;
            "redis")
                if docker exec opmas-redis-1 redis-cli ping > /dev/null 2>&1; then
                    log "$service is healthy" "$GREEN"
                    return 0
                fi
                ;;
            "nats")
                if curl -s -f "http://localhost:8222/healthz" > /dev/null; then
                    log "$service is healthy" "$GREEN"
                    return 0
                fi
                ;;
            "http")
                if curl -s -f "http://localhost:$3" > /dev/null; then
                    log "$service is healthy" "$GREEN"
                    return 0
                fi
                ;;
        esac
        
        retry_count=$((retry_count + 1))
        log "Waiting for $service to be healthy... (Attempt $retry_count/$max_retries)" "$YELLOW"
        sleep $sleep_time
    done
    
    log "$service failed to become healthy after $max_retries attempts" "$RED"
    return 1
}

# Validate environment
if [[ "$ENV" != "dev" && "$ENV" != "prod" ]]; then
    log "Invalid environment. Use 'dev' or 'prod'" "$RED"
    exit 1
fi

# Set compose file
COMPOSE_FILE="docker-compose.yaml"
if [[ "$ENV" == "dev" ]]; then
    COMPOSE_FILE="docker-compose.yaml -f docker-compose.dev.yml"
else
    COMPOSE_FILE="docker-compose.yaml -f docker-compose.prod.yml"
fi

# Check for running services
if ! check_services_running; then
    # Start services
    log "Starting OPMAS services in $ENV environment..." "$YELLOW"
    docker compose -f $COMPOSE_FILE up -d
fi

# Wait for infrastructure services
log "Waiting for infrastructure services..." "$YELLOW"
check_service_health "PostgreSQL" "postgres" || exit 1
check_service_health "Redis" "redis" || exit 1
check_service_health "NATS" "nats" || exit 1

# Wait for management API
log "Waiting for Management API..." "$YELLOW"
check_service_health "Management API" "http" "8000" || exit 1

# Wait for backend
log "Waiting for Backend..." "$YELLOW"
check_service_health "Backend" "http" "8000" || exit 1

# Wait for UI
log "Waiting for UI..." "$YELLOW"
check_service_health "UI" "http" "3000" || exit 1

# Wait for monitoring services
log "Waiting for monitoring services..." "$YELLOW"
check_service_health "Prometheus" "http" "9090" || exit 1
check_service_health "Grafana" "http" "3001" || exit 1

# Print service URLs
log "\nService URLs:" "$GREEN"
log "UI: http://localhost:3000" "$GREEN"
log "Management API: http://localhost:8000/docs" "$GREEN"
log "Grafana: http://localhost:3001" "$GREEN"
log "Prometheus: http://localhost:9090" "$GREEN"

# Print service status
log "\nService Status:" "$GREEN"
docker compose -f $COMPOSE_FILE ps

log "\nStartup complete! Check $LOG_FILE for detailed logs." "$GREEN" 