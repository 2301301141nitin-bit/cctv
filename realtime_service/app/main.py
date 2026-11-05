import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import settings
from app.services.stream_manager import stream_manager
from app.services.sync_engine import sync_engine

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Real-Time CCTV Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
def startup_event():
    sync_engine.start()

@app.on_event("shutdown")
def shutdown_event():
    sync_engine.stop()
    # Clean up all cameras on exit
    for cam_id in list(stream_manager.cameras.keys()):
        stream_manager.remove_camera(cam_id)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)
