"""
Antigravity CCTV Intelligence Platform — Unified Server
Single FastAPI application that combines static analysis, real-time monitoring,
SOC dashboard, and settings into one server with one port.
"""
import os
import sys
import logging
import torch

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

# ─── Path Setup ──────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNIFIED_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
FRONTEND_DIST = os.path.join(UNIFIED_DIR, "web", "dist")

# Add project root and backend to path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("unified_server")

# ─── Load Config ─────────────────────────────────────────────────────────────
from unified_server.config import load_config
config = load_config()

# ─── Create App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Antigravity CCTV Intelligence Platform",
    description="Unified AI-powered CCTV surveillance, forensic analysis, and real-time monitoring",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Mount Routers ───────────────────────────────────────────────────────────
from unified_server.routers.static_analysis import router as static_analysis_router
from unified_server.routers.realtime import router as realtime_router
from unified_server.routers.settings import router as settings_router

app.include_router(static_analysis_router)
app.include_router(realtime_router)
app.include_router(settings_router)

# ─── System Routes ───────────────────────────────────────────────────────────

@app.get("/api/system/health")
def system_health():
    """System-wide health check."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return {
        "status": "ok",
        "platform": "Antigravity CCTV Intelligence Platform",
        "version": "2.0.0",
        "device": device,
        "cpu_cores": os.cpu_count(),
    }


@app.get("/api/system/info")
def system_info():
    """Extended system information for the Settings page."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        import ai_engine  # type: ignore
        indexed_frames = ai_engine.index.ntotal
    except Exception:
        indexed_frames = 0

    gpu_info = {}
    if torch.cuda.is_available():
        gpu_info = {
            "name": torch.cuda.get_device_name(0),
            "vram_gb": round(torch.cuda.get_device_properties(0).total_memory / 1e9, 2),
            "cuda_version": torch.version.cuda,
            "vram_used_gb": round(torch.cuda.memory_allocated(0) / 1e9, 2),
        }

    return {
        "platform": "Antigravity CCTV Intelligence Platform",
        "version": "2.0.0",
        "device": device,
        "gpu": gpu_info,
        "cpu_cores": os.cpu_count(),
        "indexed_frames": indexed_frames,
        "project_root": PROJECT_ROOT,
        "python_version": sys.version.split()[0],
        "torch_version": torch.__version__,
    }


# ─── Static File Mounts ─────────────────────────────────────────────────────

# Serve backend static files (uploaded videos, frames)
backend_static = os.path.join(BACKEND_DIR, "static")
os.makedirs(backend_static, exist_ok=True)
app.mount("/backend-static", StaticFiles(directory=backend_static), name="backend-static")

# Serve frontend build (if it exists)
if os.path.isdir(FRONTEND_DIST):
    # Serve asset files
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/app/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/app/{rest_of_path:path}")
    async def serve_spa(rest_of_path: str):
        """Serve the SPA for all /app/* routes — React Router handles client-side routing."""
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return HTMLResponse("<h1>Frontend not built yet. Run: cd unified_server/web && npm run build</h1>", status_code=503)

    @app.get("/app")
    async def serve_spa_root():
        """Redirect /app to /app/."""
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return HTMLResponse("<h1>Frontend not built yet. Run: cd unified_server/web && npm run build</h1>", status_code=503)
else:
    @app.get("/app/{rest_of_path:path}")
    async def serve_spa_not_built(rest_of_path: str = ""):
        return HTMLResponse(
            """
            <html><body style="background:#0f172a;color:#f8fafc;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
            <div style="text-align:center">
            <h1 style="font-size:2rem;margin-bottom:1rem">🚀 Antigravity CCTV Platform</h1>
            <p style="color:#94a3b8">Frontend not built yet. Run the start.bat script or manually build:</p>
            <code style="background:#1e293b;padding:0.5rem 1rem;border-radius:8px;display:block;margin-top:1rem">cd unified_server/web && npm install && npm run build</code>
            </div></body></html>
            """,
            status_code=503
        )

    @app.get("/app")
    async def serve_spa_root_not_built():
        return await serve_spa_not_built()


# ─── Root Redirect & Health Check ──────────────────────────────────────────

@app.api_route("/", methods=["GET", "HEAD"])
async def root_redirect():
    """Redirect root to the application."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/app/")


# ─── Entry Point ─────────────────────────────────────────────────────────────

def main():
    """Start the unified server."""
    cfg = load_config()
    print()
    print("  +=======================================================+")
    print("  |   * Antigravity CCTV Intelligence Platform v2.0      |")
    print("  +=======================================================+")
    print(f"  |   Server:   http://localhost:{cfg.server.port}/app/          |")
    print(f"  |   API Docs: http://localhost:{cfg.server.port}/docs           |")
    print(f"  |   Device:   {'CUDA GPU' if torch.cuda.is_available() else 'CPU':>10s}                          |")
    print("  +=======================================================+")
    print()

    uvicorn.run(
        "unified_server.main:app",
        host=cfg.server.host,
        port=cfg.server.port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
