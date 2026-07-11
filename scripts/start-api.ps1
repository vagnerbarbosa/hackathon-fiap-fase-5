#!/usr/bin/env pwsh
# Start API script for Windows (PowerShell)
# Usage: .\scripts\start-api.ps1 [options]

param(
    [switch]$Help,
    [switch]$NoBuild,
    [switch]$Foreground,
    [switch]$NoMigrations
)

# Colors for output
$Red = "`e[0;31m"
$Green = "`e[0;32m"
$Yellow = "`e[1;33m"
$Blue = "`e[0;34m"
$NC = "`e[0m"  # No Color

# Script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

# Help function
function Show-Help {
    Write-Host "Usage: .\scripts\start-api.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Start the FIAP STRIDE API with Docker Compose"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Help              Show this help message"
    Write-Host "  -NoBuild           Skip Docker build (use existing images)"
    Write-Host "  -Foreground        Run in foreground (don't detach)"
    Write-Host "  -NoMigrations      Skip database migrations"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\scripts\start-api.ps1              # Start with build and migrations"
    Write-Host "  .\scripts\start-api.ps1 -NoBuild    # Start quickly without rebuild"
    Write-Host "  .\scripts\start-api.ps1 -Foreground  # Run in foreground mode"
}

# Show help if requested
if ($Help) {
    Show-Help
    exit 0
}

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "${Red}Error: Docker is not installed${NC}"
    Write-Host "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
}

# Check if Docker Compose is installed
$dockerComposeAvailable = $false
try {
    docker compose version | Out-Null
    $dockerComposeAvailable = $true
} catch {
    if (Get-Command docker-compose -ErrorAction SilentlyContinue) {
        $dockerComposeAvailable = $true
    }
}

if (-not $dockerComposeAvailable) {
    Write-Host "${Red}Error: Docker Compose is not installed${NC}"
    Write-Host "Please install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
}

# Change to project directory
Set-Location $ProjectDir

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "${Yellow}Warning: .env file not found${NC}"
    Write-Host "Creating .env from .env.example..."
    Copy-Item ".env.example" ".env"
    Write-Host "${Green}✓ Created .env file${NC}"
    Write-Host ""
    Write-Host "${Yellow}Please edit .env file with your configuration:${NC}"
    Write-Host "  - Set DATABASE_URL"
    Write-Host "  - Set API_KEY (for production)"
    Write-Host "  - Adjust other settings as needed"
    Write-Host ""
    Read-Host "Press Enter to continue or Ctrl+C to exit and edit .env first"
}

# Create storage directory if not exists
New-Item -ItemType Directory -Force -Path "storage" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

Write-Host "${Blue}╔════════════════════════════════════════════════════════╗${NC}"
Write-Host "${Blue}║        FIAP STRIDE API - Docker Startup               ║${NC}"
Write-Host "${Blue}╚════════════════════════════════════════════════════════╝${NC}"
Write-Host ""

# Determine docker compose command
try {
    docker compose version | Out-Null
    $ComposeCmd = "docker compose"
} catch {
    $ComposeCmd = "docker-compose"
}

# Build and start containers
if (-not $NoBuild) {
    Write-Host "${Blue}Building and starting containers...${NC}"
    Invoke-Expression "$ComposeCmd up --build -d"
} else {
    Write-Host "${Blue}Starting containers (skipping build)...${NC}"
    Invoke-Expression "$ComposeCmd up -d"
}

if ($Foreground) {
    Write-Host "${Blue}Running in foreground mode. Press Ctrl+C to stop.${NC}"
    Invoke-Expression "$ComposeCmd logs -f"
    exit 0
}

# Wait for services to be ready
Write-Host ""
Write-Host "${Blue}Waiting for services to be ready...${NC}"
Start-Sleep -Seconds 5

# Check if API is healthy
Write-Host "${Blue}Checking API health...${NC}"
$MaxRetries = 30
$RetryCount = 0
$ApiHealthy = $false

while ($RetryCount -lt $MaxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "${Green}✓ API is healthy${NC}"
            $ApiHealthy = $true
            break
        }
    } catch {
        $RetryCount++
        Write-Host "${Yellow}Waiting for API to be ready... ($RetryCount/$MaxRetries)${NC}"
        Start-Sleep -Seconds 2
    }
}

if (-not $ApiHealthy) {
    Write-Host "${Red}✗ API failed to start within expected time${NC}"
    Write-Host "Check logs with: ${ComposeCmd} logs api"
    exit 1
}

# Run migrations if requested
if (-not $NoMigrations) {
    Write-Host ""
    Write-Host "${Blue}Running database migrations...${NC}"
    try {
        Invoke-Expression "$ComposeCmd exec api alembic upgrade head"
    } catch {
        Write-Host "${Yellow}Warning: Migrations failed. Database may already be up to date.${NC}"
    }
}

# Print success message
Write-Host ""
Write-Host "${Green}╔════════════════════════════════════════════════════════╗${NC}"
Write-Host "${Green}║           🚀 API Started Successfully!                 ║${NC}"
Write-Host "${Green}╚════════════════════════════════════════════════════════╝${NC}"
Write-Host ""
Write-Host "${Blue}Available endpoints:${NC}"
Write-Host "  ${Green}• Health Check:${NC} http://localhost:8000/health"
Write-Host "  ${Green}• Swagger UI:${NC}   http://localhost:8000/docs"
Write-Host "  ${Green}• Redoc:${NC}        http://localhost:8000/redoc"
Write-Host "  ${Green}• API Version:${NC}  http://localhost:8000/version"
Write-Host ""
Write-Host "${Blue}To stop the API:${NC}"
Write-Host "  ${Yellow}${ComposeCmd} down${NC}"
Write-Host ""
Write-Host "${Blue}To view logs:${NC}"
Write-Host "  ${Yellow}${ComposeCmd} logs -f api${NC}"
Write-Host ""
Write-Host "${Blue}Happy hacking! 🛡️🔍${NC}"
