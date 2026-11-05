from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import CameraCreate, CameraResponse, AIConfigUpdate
from app.services.stream_manager import stream_manager
from app.services.ai_engine import engine
from app.core.config import settings

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/cameras", response_model=CameraResponse)
def add_camera(camera_in: CameraCreate):
    sampling = camera_in.sampling_rate if camera_in.sampling_rate else settings.default_frame_sampling
    try:
        cam = stream_manager.add_camera(source=camera_in.source, sampling_rate=sampling)
        return CameraResponse(
            id=cam.id,
            source=cam.source,
            status="running",
            sampling_rate=cam.sampling_rate
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cameras", response_model=List[CameraResponse])
def get_cameras():
    return stream_manager.list_cameras()

@router.delete("/cameras/{camera_id}")
def remove_camera(camera_id: str):
    success = stream_manager.remove_camera(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"message": "Camera stopped and removed"}

@router.get("/events")
def get_events():
    return stream_manager.get_all_latest_events()

@router.post("/ai/config")
def update_ai_config(config: AIConfigUpdate):
    try:
        engine.set_semantic_targets(config.targets)
        engine.set_confidence(config.confidence)
        return {"status": "success", "targets": engine.current_targets, "confidence": engine.current_confidence}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
