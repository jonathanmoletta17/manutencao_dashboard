# Simple production image: FastAPI backend + static frontend
FROM python:3.11-slim AS base

# Prevent python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better layer caching
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend source
COPY backend/ /app/backend/

# Build frontend in a separate lightweight stage and copy built assets
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
# Build the frontend; base is configured in vite.config.ts
RUN npm run build

FROM base AS final
# Copy frontend build output into final image
COPY --from=frontend-build /app/frontend/dist /app/frontend_build

# Expose API port
EXPOSE 8000

# Default command: run uvicorn without reload
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]