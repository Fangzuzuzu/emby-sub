# Stage 1: Build Frontend
FROM node:20 as build-frontend

WORKDIR /frontend

# Copy package files
COPY front-end/package*.json ./

# Install dependencies
# Force installation of optional dependencies (rollup needs this on some archs)
# Also ensuring we have a clean slate if caching caused issues
RUN rm -rf node_modules package-lock.json && \
    npm install && \
    npm install @rollup/rollup-linux-arm64-gnu --save-optional

# Copy frontend source code
COPY front-end/ .

# Build the app
RUN npm run build

# Stage 2: Setup Backend & Run
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies (if any, e.g. curl for healthcheck)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY back-end/requirements.txt .

# Install backend dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
# We copy src content to /app/src so python can find 'backend' package
COPY back-end/src /app/src

# Copy built frontend files from Stage 1
# We place them in /app/static so main.py can find them
COPY --from=build-frontend /frontend/dist /app/static

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

