#!/bin/bash
# Setup script for initial project configuration

set -e

echo "Setting up FIAP STRIDE API..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry not found. Installing..."
    pip install poetry
fi

# Install dependencies
echo "Installing dependencies..."
poetry install

# Copy environment file
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Create storage directory
mkdir -p storage

echo "Setup complete!"
echo "Next steps:"
echo "  1. Edit .env file with your configuration"
echo "  2. Run: docker-compose up --build"
echo "  3. Test: curl http://localhost:8000/health"
