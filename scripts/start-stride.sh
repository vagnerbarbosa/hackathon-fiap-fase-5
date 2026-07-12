#!/bin/bash
# Start STRIDE System script for Linux/macOS
# Usage: ./scripts/start-stride.sh [options]

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
    echo "Usage: ./scripts/start-stride.sh [OPTIONS]"
    echo ""
    echo "Start the complete STRIDE Threat Modeling System (API + Frontend + Database)"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  --no-build          Skip Docker build (use existing images)"
    echo "  --foreground        Run in foreground (don't detach)"
    echo "  --no-migrations     Skip database migrations"
    echo ""
    echo "Examples:"
    echo "  ./scripts/start-stride.sh              # Start all services"
    echo "  ./scripts/start-stride.sh --no-build   # Use existing images"
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

# Health check com timeout de 60 segundos
HEALTH_CHECK_URL="http://localhost:8001/health"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API is ready!${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}✗ API failed to start within expected time${NC}"
        echo "Check logs with: $COMPOSE_CMD logs api"
        exit 1
    fi
    echo -n "."
    sleep 2
done

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
echo ""
echo -e "${BLUE}Happy hacking! 🛡️🔍${NC}"
