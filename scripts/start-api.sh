#!/bin/bash
# Start API script for Linux/macOS
# Usage: ./scripts/start-api.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
SKIP_BUILD=false
DETACH=true
RUN_MIGRATIONS=true

# Help function
show_help() {
    echo "Usage: ./scripts/start-api.sh [OPTIONS]"
    echo ""
    echo "Start the FIAP STRIDE API + FRONTEND with Docker Compose"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  --no-build          Skip Docker build (use existing images)"
    echo "  --foreground        Run in foreground (don't detach)"
    echo "  --no-migrations     Skip database migrations"
    echo ""
    echo "Examples:"
    echo "  ./scripts/start-api.sh              # Start API + Frontend with build"
    echo "  ./scripts/start-api.sh --no-build   # Start quickly without rebuild"
    echo "  ./scripts/start-api.sh --foreground # Run in foreground mode"
    echo ""
    echo "Services started:"
    echo "  • Frontend (React): http://localhost:5173"
    echo "  • API (FastAPI):    http://localhost:8001"
    echo "  • PostgreSQL:       localhost:5432"
    echo "  • Redis:            localhost:6379"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --no-build)
            SKIP_BUILD=true
            shift
            ;;
        --foreground)
            DETACH=false
            shift
            ;;
        --no-migrations)
            RUN_MIGRATIONS=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo ""
    echo -e "${YELLOW}Please edit .env file with your configuration:${NC}"
    echo "  - Set DATABASE_URL"
    echo "  - Set API_KEY (for production)"
    echo "  - Adjust other settings as needed"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to exit and edit .env first..."
fi

# Create storage directory if not exists
mkdir -p storage logs

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        FIAP STRIDE API + FRONTEND - Docker Startup   ${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Determine docker compose command
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Build and start containers
if [ "$SKIP_BUILD" = false ]; then
    echo -e "${BLUE}Building and starting containers...${NC}"
    $COMPOSE_CMD up --build -d
else
    echo -e "${BLUE}Starting containers (skipping build)...${NC}"
    $COMPOSE_CMD up -d
fi

if [ "$DETACH" = false ]; then
    echo -e "${BLUE}Running in foreground mode. Press Ctrl+C to stop.${NC}"
    $COMPOSE_CMD logs -f
    exit 0
fi

# Wait for services to be ready
echo ""
echo -e "${BLUE}Waiting for services to be ready...${NC}"
sleep 5

# Check if services are healthy
echo -e "${BLUE}Checking services health...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0
API_HEALTHY=false
FRONTEND_HEALTHY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # Check API (port 8001 is mapped to 8000 in container)
    if [ "$API_HEALTHY" = false ] && curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API is healthy${NC}"
        API_HEALTHY=true
    fi

    # Check Frontend (nginx returns 200 on root)
    if [ "$FRONTEND_HEALTHY" = false ] && curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is healthy${NC}"
        FRONTEND_HEALTHY=true
    fi

    # Break if both are healthy
    if [ "$API_HEALTHY" = true ] && [ "$FRONTEND_HEALTHY" = true ]; then
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -e "${YELLOW}Waiting for services... API: $API_HEALTHY | Frontend: $FRONTEND_HEALTHY ($RETRY_COUNT/$MAX_RETRIES)${NC}"
    sleep 2
done

if [ "$API_HEALTHY" = false ]; then
    echo -e "${RED}✗ API failed to start within expected time${NC}"
    echo "Check logs with: $COMPOSE_CMD logs api"
    exit 1
fi

if [ "$FRONTEND_HEALTHY" = false ]; then
    echo -e "${YELLOW}⚠ Frontend may still be starting...${NC}"
fi

# Run migrations if requested
if [ "$RUN_MIGRATIONS" = true ]; then
    echo ""
    echo -e "${BLUE}Running database migrations...${NC}"
    $COMPOSE_CMD exec api alembic upgrade head || {
        echo -e "${YELLOW}Warning: Migrations failed. Database may already be up to date.${NC}"
    }
fi

# Print success message
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     🚀 API + FRONTEND Started Successfully!          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Frontend (React App):${NC}"
echo -e "  ${GREEN}• Application:${NC} http://localhost:5173"
echo ""
echo -e "${BLUE}API Endpoints:${NC}"
echo -e "  ${GREEN}• Health Check:${NC} http://localhost:8001/health"
echo -e "  ${GREEN}• Swagger UI:${NC}   http://localhost:8001/docs"
echo -e "  ${GREEN}• API Version:${NC}  http://localhost:8001/version"
echo ""
echo -e "${BLUE}To stop all services:${NC}"
echo -e "  ${YELLOW}$COMPOSE_CMD down${NC}"
echo ""
echo -e "${BLUE}To view logs:${NC}"
echo -e "  ${YELLOW}API:     $COMPOSE_CMD logs -f api${NC}"
echo -e "  ${YELLOW}Frontend:$COMPOSE_CMD logs -f frontend${NC}"
echo ""
echo -e "${BLUE}Happy hacking! 🛡️🔍${NC}"
