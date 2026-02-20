# Stage 1: Prepare Frontend (Static HTML)
FROM python:3.11-slim AS frontend-prep

WORKDIR /app

# Copy static frontend files from "Front end right"
COPY ["Front end right/", "/app/static/frontend/"]

# Stage 2: Base Python Image with Dependencies
FROM python:3.11-slim AS base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies only (code will be copied/mounted per stage)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["rm", "requirements.txt"]

# Stage 3: API Service with Frontend
# App folder is mounted via docker-compose for hot reload
FROM base AS api

# Copy static frontend files OUTSIDE of /app/app to avoid volume mount override
COPY --from=frontend-prep /app/static/frontend /app/static/frontend

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the FastAPI application with reload enabled
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 4: Scrapers Service (for one-time runs)
FROM base AS scrapers

# Install dos2unix for handling Windows line endings
RUN apt-get update && apt-get install -y --no-install-recommends \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Copy only scrapers code
COPY backend/scrapers /app/scrapers

# Copy and set entrypoint (seeds taxonomy then runs scrapers)
COPY backend/scrapers/entrypoint.sh /app/entrypoint.sh
# Convert Windows line endings to Unix and make executable
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]

# Stage 5: Cron Service (scheduled scraper runs)
FROM base AS cron

# Install cron and dos2unix for line ending conversion
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Copy scrapers code (needed for cron to run them)
COPY backend/scrapers /app/scrapers

# Copy entrypoint (handles seeding, env passthrough, configurable schedule)
COPY backend/cron/entrypoint.sh /app/entrypoint.sh
# Convert Windows line endings to Unix and make executable
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Create log file for cron output
RUN touch /var/log/cron.log

CMD ["/app/entrypoint.sh"]
