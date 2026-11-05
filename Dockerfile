# ==============================================================================
# Multi-Stage Dockerfile for Antigravity CCTV AI Platform
# Combines: React Frontend Build + FastAPI + PyTorch + YOLO AI Engine
# ==============================================================================

# ---- Stage 1: Build the Web Frontend ----
FROM node:20-alpine AS frontend-builder
WORKDIR /app/web

# Install frontend dependencies
COPY unified_server/web/package*.json ./
RUN npm ci --silent || npm install --silent

# Build production frontend bundle
COPY unified_server/web/ ./
RUN npm run build

# ---- Stage 2: Python Backend & AI Inference Runner ----
FROM python:3.11-slim

# Install system dependencies required for OpenCV, FFmpeg, and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip & install PyTorch (CPU-optimized for cloud deployment)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install Python requirements
COPY unified_server/requirements.txt ./unified_server/requirements.txt
RUN pip install --no-cache-dir -r ./unified_server/requirements.txt

# Pre-cache YOLO weights inside the image
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Copy application backend & unified server code
COPY backend/ ./backend/
COPY unified_server/ ./unified_server/

# Copy built frontend assets from Stage 1 into unified server distribution folder
COPY --from=frontend-builder /app/web/dist ./unified_server/web/dist

# Ensure static directories exist
RUN mkdir -p backend/static/videos backend/static/frames unified_server/backend/static

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

# Start Unified Server
CMD ["python", "unified_server/main.py"]
