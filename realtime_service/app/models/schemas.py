from pydantic import BaseModel
from typing import List, Optional

class BBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class Detection(BaseModel):
    track_id: Optional[int] = None
    class_name: str
    confidence: float
    bbox: BBox

class FrameEvent(BaseModel):
    camera_id: str
    frame_index: int
    timestamp: float
    detections: List[Detection]

class CameraCreate(BaseModel):
    source: str  # URL or device index (e.g., "0", "1", "rtsp://...")
    sampling_rate: Optional[int] = None

class CameraResponse(BaseModel):
    id: str
    source: str
    status: str
    sampling_rate: int

class AIConfigUpdate(BaseModel):
    targets: List[str]
    confidence: float
