# Antigravity CCTV AI Analysis Platform

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15%2B-black.svg)](https://nextjs.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C.svg)](https://pytorch.org/)
[![Ultralytics YOLOv8](https://img.shields.io/badge/YOLO-v8-00FFFF.svg)](https://github.com/ultralytics/ultralytics)

> **Enterprise-grade, privacy-first CCTV video intelligence platform.** 
> Search through hundreds of hours of surveillance footage in milliseconds using natural language or reference images, monitor live streams with real-time YOLO object & behavior detection, and manage alerts from a high-performance SOC dashboard.

---

## 🌟 Key Capabilities

- **🔍 Semantic Natural Language Video Search**
  Search CCTV archives as easily as searching the web (*"person wearing a red backpack"*, *"white delivery van parked near entrance"*, *"bicyclist crossing road"*). Powered by OpenAI CLIP vision-language embeddings and Facebook AI Similarity Search (FAISS).

- **🖼️ Reference Image Suspect Search**
  Upload a reference photo of an individual or vehicle to immediately identify matching timestamps, frames, and confidence scores across video archives.

- **⚡ Real-Time Stream Monitoring & Detection**
  Continuous RTSP, webcam, or video stream ingestion with real-time YOLOv8 object recognition, boundary / geofence line-crossing tracking, and loitering detection.

- **🖥️ SOC (Security Operations Center) Dashboard**
  Built with Next.js, React, and Tailwind CSS. Features live event feeds, filter bars, camera health monitoring, and interactive semantic search overlays.

- **🔒 100% Offline & Privacy-First**
  All model inferences, frame extraction, and vector searches run locally on-premise. Sensitive surveillance video data never leaves your infrastructure.

- **💼 Enterprise Desktop Client with HWID Licensing**
  A standalone Windows desktop application (built with CustomTkinter) bundled with hardware-locked (HWID) activation keys and customizable subscription terms.

---

## 🏗️ Architecture & Repository Structure

```text
cctv/
├── unified_server/         # Unified FastAPI application (Static Search + Realtime YOLO)
│   ├── backend/            # Uploaded video storage & frame cache
│   ├── routers/            # API endpoints: static analysis, realtime, settings
│   ├── web/                # React / Vite unified monitoring UI
│   └── main.py             # Server entry point
├── soc_dashboard/          # Next.js modern SOC web application
│   ├── src/app/            # App router, pages, and layout
│   └── src/components/     # Camera list, event feed, semantic search controls
├── backend/                # Desktop application & offline inference engine
│   ├── desktop_app.py      # CustomTkinter GUI client
│   ├── ai_engine.py        # CLIP + FAISS vector indexing & search
│   ├── license_manager.py  # Machine HWID licensing validation
│   └── generate_license.py # Admin license generator tool
├── realtime_service/       # Dedicated live streaming & event detection microservice
│   └── app/                # Rules engine, camera source handlers, Firebase sync
├── frontend/               # Standalone React + Vite frontend
├── start.bat               # One-click Windows development launcher
├── start.sh                # One-click Linux / Ubuntu deployment script
└── PITCH_DECK.md           # Business overview, market thesis, and pitch deck
```

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python**: 3.10 or 3.11 (with `pip` and `venv`)
- **Node.js**: 18.x or 20.x (with `npm`)
- **Hardware**: CPU supported; NVIDIA GPU with CUDA 12.x recommended for faster inference.

### 2. One-Click Launcher

#### Windows
Run the automated launcher:
```cmd
start.bat
```
*This script will create the virtual environment, install PyTorch (with CUDA fallback), download dependencies, install frontend packages, and launch both backend and UI.*

#### Linux / Ubuntu Server
Make the script executable and run:
```bash
chmod +x start.sh
./start.sh
```

---

## 🛠️ Manual Installation

### Unified Server (FastAPI + React UI)

1. **Create and activate a virtual environment:**
   ```bash
   cd unified_server
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

2. **Install PyTorch & Dependencies:**
   ```bash
   # Optional: For CUDA GPU acceleration
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

   pip install -r requirements.txt
   ```

3. **Install Frontend Dependencies & Build:**
   ```bash
   cd web
   npm install
   npm run build
   cd ..
   ```

4. **Launch Server:**
   ```bash
   python main.py
   ```
   Access the dashboard at `http://localhost:8000`. Swagger documentation is available at `http://localhost:8000/docs`.

---

### SOC Dashboard (Next.js)

```bash
cd soc_dashboard
npm install
npm run dev
```
Open `http://localhost:3000` to interact with the Security Operations Center interface.

---

### Desktop Application

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run the desktop app
python desktop_app.py

# Run the license generator (Admin)
python generate_license.py
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` in `realtime_service/` or set environment variables:

| Variable | Default | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Host interface to bind |
| `PORT` | `8000` | Port for the API server |
| `DEFAULT_FRAME_SAMPLING` | `3` | Analyze 1 frame out of every $N$ frames |
| `MODEL_NAME` | `yolov8n.pt` | YOLO model weights (`yolov8n`, `yolov8s`, `yolov8m`) |
| `FIREBASE_ENABLED` | `False` | Toggle remote sync to Firebase Firestore |

---

## 🤝 Contributing

Contributions are welcome!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

