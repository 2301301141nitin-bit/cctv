#!/bin/bash

# Antigravity CCTV Intelligence Platform - Linux/Ubuntu Deployment Script
# Specifically tailored for CPU-only / ARM64 environments (like Oracle Cloud)

set -e

PROJECT_ROOT=$(pwd)
VENV_DIR="$PROJECT_ROOT/unified_server/venv"
WEB_DIR="$PROJECT_ROOT/unified_server/web"
REQUIREMENTS="$PROJECT_ROOT/unified_server/requirements.txt"
SERVER_PORT=8000

echo "============================================================"
echo "  Antigravity CCTV Intelligence Platform (Linux Server)"
echo "============================================================"

# 1. Install system dependencies if missing
echo "[1/5] Checking system dependencies..."
if ! command -v python3 &> /dev/null || ! command -v npm &> /dev/null; then
    echo "Installing Python and Node.js..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-venv python3-pip nodejs npm ffmpeg libsm6 libxext6
fi

# 2. Setup Python Virtual Environment
echo "[2/5] Setting up Python Virtual Environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# 3. Install Python Dependencies
echo "[3/5] Installing Python dependencies..."
# Upgrade pip first
pip install --upgrade pip

# Install PyTorch for CPU (ARM64 friendly)
echo "Installing PyTorch (CPU version)..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the requirements
echo "Installing remaining requirements..."
pip install -r "$REQUIREMENTS"

# 4. Build Frontend
echo "[4/5] Building Frontend..."
cd "$WEB_DIR"
if [ ! -d "node_modules" ]; then
    npm install
fi
if [ ! -d "dist" ]; then
    npm run build
fi
cd "$PROJECT_ROOT"

# 5. Start the Server
echo "[5/5] Starting Unified Server..."
echo "Server will run on http://0.0.0.0:$SERVER_PORT"
echo "Make sure to open port $SERVER_PORT in your Oracle Cloud Ingress Rules!"

# Use 0.0.0.0 to bind to all public IPs for cloud hosting
python -m uvicorn unified_server.main:app --host 0.0.0.0 --port $SERVER_PORT
