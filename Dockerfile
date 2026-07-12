# Build stage
FROM python:3.11-slim-bookworm as builder

WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --only main --no-interaction --no-ansi

# Runtime stage
FROM python:3.11-slim-bookworm as runtime

WORKDIR /app

# Install runtime dependencies (otimizado para OpenCV headless)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libmagic1 \
    curl \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Nota: Removidas libs de GUI (libsm6, libxext6, libxrender-dev, libgl1-mesa-glx)
# O OpenCV headless não requer essas dependências visuais

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Create storage directory and set permissions
RUN mkdir -p /app/storage /app/logs && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
