"""
Settings Router
Full CRUD for platform configuration — cameras, AI, rules, Firebase, etc.
All changes are persisted to config.json.
Prefix: /api/settings
"""
import os
import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from unified_server.config import (
    load_config, save_config, UnifiedConfig,
    CameraConfig, AIConfig, RulesConfig, RuleZone,
    FirebaseConfig, StaticAnalysisConfig, ServerConfig,
    AlertConfig
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["Settings"])

# ─── Request Schemas ─────────────────────────────────────────────────────────

class CameraCreateRequest(BaseModel):
    name: str = "Unnamed Camera"
    source: str
    sampling_rate: int = 3
    enabled: bool = True

class CameraUpdateRequest(BaseModel):
    name: Optional[str] = None
    source: Optional[str] = None
    sampling_rate: Optional[int] = None
    enabled: Optional[bool] = None

class AIConfigRequest(BaseModel):
    realtime_model: Optional[str] = None
    clip_model: Optional[str] = None
    targets: Optional[List[str]] = None
    confidence: Optional[float] = None
    frame_sampling: Optional[int] = None

class FirebaseConfigRequest(BaseModel):
    enabled: Optional[bool] = None
    credentials_path: Optional[str] = None
    storage_bucket: Optional[str] = None
    api_key: Optional[str] = None
    auth_domain: Optional[str] = None
    project_id: Optional[str] = None
    messaging_sender_id: Optional[str] = None
    app_id: Optional[str] = None

class StaticAnalysisRequest(BaseModel):
    fps_extract: Optional[float] = None
    batch_size: Optional[int] = None

class AlertConfigRequest(BaseModel):
    enabled: Optional[bool] = None
    cooldown_seconds: Optional[int] = None
    thresholds: Optional[dict] = None
    popup_enabled: Optional[bool] = None
    sound_enabled: Optional[bool] = None

class TestCameraRequest(BaseModel):
    source: str

# ─── Full Config ─────────────────────────────────────────────────────────────

@router.get("/")
def get_settings():
    """Get entire platform configuration."""
    config = load_config()
    return config.model_dump()


@router.put("/")
def update_settings(data: dict):
    """Update entire platform configuration (partial update supported)."""
    config = load_config()
    updated = config.model_dump()
    _deep_merge(updated, data)
    new_config = UnifiedConfig(**updated)
    save_config(new_config)
    return new_config.model_dump()


# ─── Camera Management ───────────────────────────────────────────────────────

@router.get("/cameras")
def list_cameras():
    """List all configured camera sources."""
    config = load_config()
    return config.cameras


@router.post("/cameras")
def add_camera(req: CameraCreateRequest):
    """Add a new camera source to the configuration."""
    config = load_config()
    cam = CameraConfig(
        id=f"cam-{str(uuid.uuid4())[:6]}",
        name=req.name,
        source=req.source,
        sampling_rate=req.sampling_rate,
        enabled=req.enabled
    )
    config.cameras.append(cam)
    save_config(config)
    return cam.model_dump()


@router.put("/cameras/{camera_id}")
def update_camera(camera_id: str, req: CameraUpdateRequest):
    """Update an existing camera's configuration."""
    config = load_config()
    for cam in config.cameras:
        if cam.id == camera_id:
            if req.name is not None:
                cam.name = req.name
            if req.source is not None:
                cam.source = req.source
            if req.sampling_rate is not None:
                cam.sampling_rate = req.sampling_rate
            if req.enabled is not None:
                cam.enabled = req.enabled
            save_config(config)
            return cam.model_dump()
    raise HTTPException(status_code=404, detail="Camera not found")


@router.delete("/cameras/{camera_id}")
def delete_camera(camera_id: str):
    """Remove a camera from the configuration."""
    config = load_config()
    original_len = len(config.cameras)
    config.cameras = [c for c in config.cameras if c.id != camera_id]
    if len(config.cameras) == original_len:
        raise HTTPException(status_code=404, detail="Camera not found")
    save_config(config)
    return {"message": f"Camera {camera_id} removed"}


@router.post("/test-camera")
def test_camera(req: TestCameraRequest):
    """Test if a camera source URL is reachable."""
    import cv2
    source = int(req.source) if req.source.isdigit() else req.source
    cap = cv2.VideoCapture(source)
    if cap.isOpened():
        ret, _ = cap.read()
        cap.release()
        if ret:
            return {"status": "success", "message": "Camera is reachable and returning frames"}
        return {"status": "partial", "message": "Camera opened but could not read a frame"}
    cap.release()
    return {"status": "error", "message": "Failed to open camera source. Check the URL or device index."}


# ─── AI Configuration ────────────────────────────────────────────────────────

@router.get("/ai")
def get_ai_config():
    """Get AI detection configuration."""
    config = load_config()
    return config.ai.model_dump()


@router.put("/ai")
def update_ai_config(req: AIConfigRequest):
    """Update AI detection settings."""
    config = load_config()
    if req.realtime_model is not None:
        config.ai.realtime_model = req.realtime_model
    if req.clip_model is not None:
        config.ai.clip_model = req.clip_model
    if req.targets is not None:
        config.ai.targets = req.targets
    if req.confidence is not None:
        config.ai.confidence = req.confidence
    if req.frame_sampling is not None:
        config.ai.frame_sampling = req.frame_sampling
    save_config(config)
    return config.ai.model_dump()


# ─── Rules Configuration ─────────────────────────────────────────────────────

@router.get("/rules")
def get_rules():
    """Get event detection rules."""
    config = load_config()
    return config.rules.model_dump()


@router.put("/rules")
def update_rules(rules_data: dict):
    """Update event detection rules."""
    config = load_config()
    config.rules = RulesConfig(**rules_data)
    save_config(config)
    return config.rules.model_dump()


# ─── Firebase Configuration ──────────────────────────────────────────────────

@router.get("/firebase")
def get_firebase_config():
    """Get Firebase configuration."""
    config = load_config()
    return config.firebase.model_dump()


@router.put("/firebase")
def update_firebase_config(req: FirebaseConfigRequest):
    """Update Firebase configuration."""
    config = load_config()
    if req.enabled is not None:
        config.firebase.enabled = req.enabled
    if req.credentials_path is not None:
        config.firebase.credentials_path = req.credentials_path
    if req.storage_bucket is not None:
        config.firebase.storage_bucket = req.storage_bucket
    if req.api_key is not None:
        config.firebase.api_key = req.api_key
    if req.auth_domain is not None:
        config.firebase.auth_domain = req.auth_domain
    if req.project_id is not None:
        config.firebase.project_id = req.project_id
    if req.messaging_sender_id is not None:
        config.firebase.messaging_sender_id = req.messaging_sender_id
    if req.app_id is not None:
        config.firebase.app_id = req.app_id
    save_config(config)
    return config.firebase.model_dump()


# ─── Static Analysis Configuration ───────────────────────────────────────────

@router.get("/static-analysis")
def get_static_analysis_config():
    """Get static analysis configuration."""
    config = load_config()
    return config.static_analysis.model_dump()


@router.put("/static-analysis")
def update_static_analysis_config(req: StaticAnalysisRequest):
    """Update static analysis settings."""
    config = load_config()
    if req.fps_extract is not None:
        config.static_analysis.fps_extract = req.fps_extract
    if req.batch_size is not None:
        config.static_analysis.batch_size = req.batch_size
    save_config(config)
    return config.static_analysis.model_dump()


# ─── Alert Configuration ─────────────────────────────────────────────────

@router.get("/alerts")
def get_alert_config():
    """Get alert threshold configuration."""
    config = load_config()
    return config.alerts.model_dump()


@router.put("/alerts")
def update_alert_config(req: AlertConfigRequest):
    """Update alert threshold settings."""
    config = load_config()
    if req.enabled is not None:
        config.alerts.enabled = req.enabled
    if req.cooldown_seconds is not None:
        config.alerts.cooldown_seconds = req.cooldown_seconds
    if req.thresholds is not None:
        config.alerts.thresholds = req.thresholds
    if req.popup_enabled is not None:
        config.alerts.popup_enabled = req.popup_enabled
    if req.sound_enabled is not None:
        config.alerts.sound_enabled = req.sound_enabled
    save_config(config)
    return config.alerts.model_dump()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _deep_merge(base: dict, override: dict):
    """Recursively merge override into base dict."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
