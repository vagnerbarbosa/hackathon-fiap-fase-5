#!/usr/bin/env pwsh
# Start STRIDE System script for Windows (PowerShell)
# Usage: .\scripts\powershell\start-stride.ps1 [options]

param(
    [switch]$Help,
    [switch]$NoBuild,
    [switch]$Foreground,
    [switch]$NoMigrations
)

# Script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent (Split-Path -Parent $ScriptDir)

# Help function
function Show-Help {
    Write-Host "Usage: .\scripts\powershell\start-stride.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Start the complete STRIDE Threat Modeling System (API + Frontend + Database)"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Help              Show this help message"
    Write-Host "  -NoBuild           Skip Docker build (use existing images)"
    Write-Host "  -Foreground        Run in foreground (don't detach)"
    Write-Host "  -NoMigrations      Skip database migrations"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\scripts\powershell\start-stride.ps1              # Start all services"
    Write-Host "  .\scripts\powershell\start-stride.ps1 -NoBuild      # Use existing images"
}

# Show help if requested
if ($Help) {
    Show-Help
    exit 0
}

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker is not installed" -ForegroundColor Red
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
    Write-Host "ERROR: Docker Compose is not installed" -ForegroundColor Red
    Write-Host "Please install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
}

# Change to project directory
Set-Location $ProjectDir

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found" -ForegroundColor Yellow
    Write-Host "Creating .env from .env.example..."
    Copy-Item ".env.example" ".env"
    Write-Host "[OK] Created .env file" -ForegroundColor Green
    Write-Host ""
    Write-Host "Please edit .env file with your configuration:" -ForegroundColor Yellow
    Write-Host "  - Set DATABASE_URL"
    Write-Host "  - Set API_KEY (for production)"
    Write-Host "  - Adjust other settings as needed"
    Write-Host ""
    Read-Host "Press Enter to continue or Ctrl+C to exit and edit .env first"
}

# Create storage directory if not exists
New-Item -ItemType Directory -Force -Path "storage" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

Write-Host "========================================================" -ForegroundColor Blue
Write-Host "  STRIDE Threat Modeling System - Starting..." -ForegroundColor Blue
Write-Host "========================================================" -ForegroundColor Blue
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
    Write-Host "Building and starting containers..." -ForegroundColor Blue
    Invoke-Expression "$ComposeCmd up --build -d"
} else {
    Write-Host "Starting containers (skipping build)..." -ForegroundColor Blue
    Invoke-Expression "$ComposeCmd up -d"
}

if ($Foreground) {
    Write-Host "Running in foreground mode. Press Ctrl+C to stop." -ForegroundColor Blue
    Invoke-Expression "$ComposeCmd logs -f"
    exit 0
}

# Wait for services to be ready
Write-Host ""
Write-Host "Waiting for services to be ready..." -ForegroundColor Blue

# Health check with 60 second timeout
$HealthCheckUrl = "http://localhost:8001/health"
$MaxRetries = 30
$RetryCount = 0
$ApiHealthy = $false

while ($RetryCount -lt $MaxRetries) {
    try {
        $response = Invoke-WebRequest -Uri $HealthCheckUrl -Method GET -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $ApiHealthy = $true
            Write-Host "[OK] API is ready!" -ForegroundColor Green
            break
        }
    } catch {
        # Keep trying
    }
    $RetryCount++
    if ($RetryCount -eq $MaxRetries) {
        Write-Host "[FAIL] API failed to start within expected time" -ForegroundColor Red
        Write-Host "Check logs with: $ComposeCmd logs api"
        exit 1
    }
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 2
}

if (-not $ApiHealthy) {
    Write-Host "[FAIL] API failed to start within expected time" -ForegroundColor Red
    Write-Host "Check logs with: $ComposeCmd logs api"
    exit 1
}

# Run migrations if requested
if (-not $NoMigrations) {
    Write-Host ""
    Write-Host "Running database migrations..." -ForegroundColor Blue
    try {
        Invoke-Expression "$ComposeCmd exec api alembic upgrade head"
    } catch {
        Write-Host "Warning: Migrations failed. Database may already be up to date." -ForegroundColor Yellow
    }
}

# Print success message
Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  STRIDE System is UP!" -ForegroundColor Green
Write-Host "  API:      http://localhost:8001/health" -ForegroundColor Green
Write-Host "  Docs:     http://localhost:8001/docs" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Happy hacking!" -ForegroundColor Blue
