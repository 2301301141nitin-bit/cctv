"""
Real-Time Monitoring Router
GPU-accelerated YOLO detection with threshold-based WebSocket alerts.
Prefix: /api/realtime
"""
import os
import sys
import time
import uuid
import json
import logging
import asyncio
import threading
import base64
from typing import List, Dict, Optional, Any, Set
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/realtime", tags=["Real-Time Monitoring"])

# ─── Pydantic Schemas ────────────────────────────────────────────────────────

class CameraAddRequest(BaseModel):
    source: str
    name: str = "Unnamed Camera"
    sampling_rate: int = 3

class CameraResponse(BaseModel):
    id: str
    name: str
    source: str
    status: str
    sampling_rate: int
    frame_count: int = 0

class AIConfigUpdate(BaseModel):
    targets: List[str]
    confidence: float

class DetectionInfo(BaseModel):
    track_id: Optional[int] = None
    class_name: str
    confidence: float
    bbox: Dict[str, float]

class EventResponse(BaseModel):
    camera_id: str
    camera_name: str
    frame_index: int
    timestamp: float
    detections: List[DetectionInfo]

class AlertThresholdUpdate(BaseModel):
    thresholds: Dict[str, float]
    cooldown_seconds: int = 10
    enabled: bool = True

# ─── WebSocket Alert Manager ────────────────────────────────────────────────

class AlertManager:
    """Manages WebSocket connections and threshold-based alert dispatch."""

    def __init__(self):
        self.connections: Set[WebSocket] = set()
        self.thresholds: Dict[str, float] = {"person": 0.6, "car": 0.5}
        self.cooldown_seconds: int = 10
        self.enabled: bool = True
        self._last_alert_time: Dict[str, float] = {}  # "camera_id:class_name" -> timestamp
        self._lock = threading.Lock()

    def _can_alert(self, camera_id: str, class_name: str) -> bool:
        """Check if alert should fire based on cooldown."""
        key = f"{camera_id}:{class_name}"
        now = time.time()
        with self._lock:
            last = self._last_alert_time.get(key, 0)
            if now - last >= self.cooldown_seconds:
                self._last_alert_time[key] = now
                return True
        return False

    def check_detections(self, camera_id: str, camera_name: str,
                         detections: List[Dict], frame_bytes: Optional[bytes] = None):
        """Check detections against thresholds and dispatch alerts."""
        if not self.enabled or not self.connections:
            return

        matching = []
        for d in detections:
            class_name = d.get("class_name", "")
            confidence = d.get("confidence", 0)
            threshold = self.thresholds.get(class_name)

            if threshold is not None and confidence >= threshold:
                if self._can_alert(camera_id, class_name):
                    matching.append({
                        "class_name": class_name,
                        "confidence": confidence,
                        "track_id": d.get("track_id"),
                        "bbox": d.get("bbox", {}),
                    })

        if not matching:
            return

        # Build alert payload
        alert = {
            "type": "threshold_alert",
            "camera_id": camera_id,
            "camera_name": camera_name,
            "timestamp": time.time(),
            "detections": matching,
            "snapshot": None,
        }

        # Attach snapshot if available (base64 JPEG)
        if frame_bytes:
            alert["snapshot"] = base64.b64encode(frame_bytes).decode("ascii")

        # Broadcast to all connected WebSockets
        alert_json = json.dumps(alert)
        dead = set()
        for ws in self.connections.copy():
            try:
                asyncio.run_coroutine_threadsafe(ws.send_text(alert_json),
                                                 _ws_loop) if _ws_loop else None
            except Exception:
                dead.add(ws)
        self.connections -= dead

    async def send_alert_async(self, alert_json: str):
        """Send alert to all connections (called from async context)."""
        dead = set()
        for ws in self.connections.copy():
            try:
                await ws.send_text(alert_json)
            except Exception:
                dead.add(ws)
        self.connections -= dead


_alert_manager = AlertManager()
_ws_loop = None  # Will be set when the first WebSocket connects


# ─── In-Process Camera Manager ──────────────────────────────────────────────

class ManagedCamera:
    """Lightweight camera wrapper that runs YOLO detection in a background thread."""
    def __init__(self, camera_id: str, name: str, source: str, sampling_rate: int):
        self.id = camera_id
        self.name = name
        self.source = source
        self.sampling_rate = sampling_rate
        self.is_running = False
        self.frame_index = 0
        self.latest_detections: List[Dict[str, Any]] = []
        self.latest_timestamp: float = 0
        self.latest_frame_bytes = None
        self._thread: Optional[threading.Thread] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._yolo_model = None
        self._latest_raw_frame = None  # Always holds the most recent frame from the camera
        self._frame_lock = threading.Lock()

    def start(self, model):
        if self.is_running:
            return
        self._yolo_model = model
        self.is_running = True
        self._reader_thread = threading.Thread(target=self._read_frames, daemon=True)
        self._reader_thread.start()
        self._thread = threading.Thread(target=self._process_frames, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=3.0)
        if self._reader_thread:
            self._reader_thread.join(timeout=3.0)

    def _read_frames(self):
        """Dedicated thread that constantly drains the OpenCV buffer, keeping only the latest frame."""
        import cv2
        capture_source = int(self.source) if self.source.isdigit() else self.source
        cap = cv2.VideoCapture(capture_source)

        # Minimize OpenCV's internal buffer to reduce latency
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            logger.error(f"Failed to open camera source: {self.source}")
            self.is_running = False
            return

        logger.info(f"Camera {self.id} ({self.name}) started on source: {self.source}")

        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            # Always overwrite with the newest frame — this drains the buffer
            with self._frame_lock:
                self._latest_raw_frame = frame

        cap.release()
        logger.info(f"Camera {self.id} stopped.")

    def _process_frames(self):
        """Processes the latest frame for AI detection — never touches old buffered frames."""
        import cv2
        last_processed_frame = None

        while self.is_running:
            # Grab the latest frame from the reader
            with self._frame_lock:
                raw = self._latest_raw_frame

            if raw is None:
                time.sleep(0.01)
                continue

            # Skip if the frame reference hasn't changed (same object = no new frame)
            if raw is last_processed_frame:
                time.sleep(0.005)
                continue
            last_processed_frame = raw

            self.frame_index += 1
            frame = raw.copy()

            try:
                if self._yolo_model is not None:
                    results = self._yolo_model.track(
                        source=frame, persist=True,
                        tracker="bytetrack.yaml", verbose=False,
                        conf=_realtime_state["confidence"]
                    )
                    detections = []
                    person_count = 0
                    if results and len(results) > 0:
                        boxes = results[0].boxes
                        if boxes is not None:
                            for i in range(len(boxes)):
                                box = boxes[i]
                                x1, y1, x2, y2 = box.xyxy[0].tolist()
                                conf = float(box.conf[0])
                                cls_id = int(box.cls[0])
                                class_name = results[0].names[cls_id]
                                track_id = int(box.id[0]) if box.id is not None else None
                                detections.append({
                                    "track_id": track_id,
                                    "class_name": class_name,
                                    "confidence": conf,
                                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
                                })
                                if class_name == "person":
                                    person_count += 1

                                # Draw red box on frame
                                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
                                label = f"{class_name} {conf:.2f}"
                                if track_id is not None:
                                    label = f"#{track_id} " + label
                                cv2.putText(frame, label, (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                    if person_count >= 3:
                        detections.append({"track_id": None, "class_name": "Group of People", "confidence": 1.0, "bbox": {"x1": 0, "y1": 0, "x2": 0, "y2": 0}})
                    elif person_count == 1:
                        detections.append({"track_id": None, "class_name": "Solo Person", "confidence": 1.0, "bbox": {"x1": 0, "y1": 0, "x2": 0, "y2": 0}})

                    self.latest_detections = detections
                    self.latest_timestamp = time.time()

                # Encode frame as JPEG (lower quality for streaming = lower latency)
                ret_jpg, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                if ret_jpg:
                    self.latest_frame_bytes = jpeg.tobytes()

                    # Check threshold alerts
                    if detections:
                        _alert_manager.check_detections(
                            camera_id=self.id,
                            camera_name=self.name,
                            detections=detections,
                            frame_bytes=self.latest_frame_bytes
                        )

            except Exception as e:
                logger.error(f"Error processing frame for camera {self.id}: {e}")


# ─── Global State ────────────────────────────────────────────────────────────

_realtime_state: Dict[str, Any] = {
    "cameras": {},  # id -> ManagedCamera
    "model": None,
    "model_loaded": False,
    "model_loading": False,
    "targets": ["person", "car"],
    "confidence": 0.25,
}


_model_lock = threading.Lock()

def _ensure_model():
    """Lazily load the YOLO model on first camera add in a thread-safe way.
    Uses GPU with FP16 when available for maximum performance."""
    with _model_lock:
        if _realtime_state["model_loaded"]:
            return

        try:
            import torch
            from ultralytics import YOLO

            # Model selection: prefer yolov8m (medium) for best accuracy/speed tradeoff
            model_path = "yolov8m.pt"
            # Search for model in known locations
            search_dirs = [
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # project root
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "realtime_service"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"),
            ]

            found_model = None
            for d in search_dirs:
                candidate = os.path.join(d, model_path)
                if os.path.exists(candidate):
                    found_model = candidate
                    break

            # Fallback to yolov8n if medium not found (it will auto-download)
            if not found_model:
                # Try nano as fallback
                for d in search_dirs:
                    for fallback in ["yolov8s.pt", "yolov8n.pt"]:
                        candidate = os.path.join(d, fallback)
                        if os.path.exists(candidate):
                            found_model = candidate
                            break
                    if found_model:
                        break

            if not found_model:
                found_model = model_path  # Let ultralytics auto-download

            logger.info(f"Loading YOLO model: {found_model}")
            yolo_model = YOLO(found_model)

            # GPU acceleration
            if torch.cuda.is_available():
                yolo_model.to('cuda')
                logger.info(f"YOLO model loaded on GPU ({torch.cuda.get_device_name(0)})")
            else:
                logger.info("YOLO model loaded on CPU")

            if _realtime_state["targets"]:
                try:
                    yolo_model.set_classes(_realtime_state["targets"])
                except Exception:
                    pass

            _realtime_state["model"] = yolo_model
            _realtime_state["model_loaded"] = True

        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")


# ─── Load alert config from config.json ──────────────────────────────────────

def _load_alert_config():
    """Load alert thresholds from config.json into AlertManager."""
    try:
        from unified_server.config import load_config
        cfg = load_config()
        _alert_manager.thresholds = dict(cfg.alerts.thresholds)
        _alert_manager.cooldown_seconds = cfg.alerts.cooldown_seconds
        _alert_manager.enabled = cfg.alerts.enabled
        logger.info(f"Alert config loaded: thresholds={_alert_manager.thresholds}, cooldown={_alert_manager.cooldown_seconds}s")
    except Exception as e:
        logger.warning(f"Could not load alert config, using defaults: {e}")

_load_alert_config()


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "model_loaded": _realtime_state["model_loaded"],
        "active_cameras": len(_realtime_state["cameras"]),
        "websocket_clients": len(_alert_manager.connections),
    }


@router.post("/cameras", response_model=CameraResponse)
def add_camera(req: CameraAddRequest):
    """Add and start a new camera source."""
    _ensure_model()
    cam_id = str(uuid.uuid4())[:8]
    cam = ManagedCamera(
        camera_id=cam_id,
        name=req.name,
        source=req.source,
        sampling_rate=req.sampling_rate
    )
    if _realtime_state["model"]:
        cam.start(_realtime_state["model"])
    _realtime_state["cameras"][cam_id] = cam
    return CameraResponse(
        id=cam.id, name=cam.name, source=cam.source,
        status="running" if cam.is_running else "starting",
        sampling_rate=cam.sampling_rate, frame_count=cam.frame_index
    )


@router.get("/cameras", response_model=List[CameraResponse])
def list_cameras():
    """List all active cameras."""
    return [
        CameraResponse(
            id=c.id, name=c.name, source=c.source,
            status="running" if c.is_running else "stopped",
            sampling_rate=c.sampling_rate, frame_count=c.frame_index
        )
        for c in _realtime_state["cameras"].values()
    ]


@router.delete("/cameras/{camera_id}")
def remove_camera(camera_id: str):
    """Stop and remove a camera."""
    cam = _realtime_state["cameras"].pop(camera_id, None)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    cam.stop()
    return {"message": f"Camera {camera_id} stopped and removed"}


@router.get("/events")
def get_events():
    """Get latest detection events from all cameras."""
    events = []
    for cam in _realtime_state["cameras"].values():
        if cam.latest_detections:
            events.append({
                "camera_id": cam.id,
                "camera_name": cam.name,
                "frame_index": cam.frame_index,
                "timestamp": cam.latest_timestamp,
                "detections": cam.latest_detections
            })
    return events


@router.post("/ai/config")
def update_ai_config(config: AIConfigUpdate):
    """Update AI detection targets and confidence threshold."""
    _realtime_state["targets"] = config.targets
    _realtime_state["confidence"] = config.confidence
    if _realtime_state["model"]:
        try:
            _realtime_state["model"].set_classes(config.targets)
        except Exception:
            pass
    return {
        "status": "success",
        "targets": _realtime_state["targets"],
        "confidence": _realtime_state["confidence"]
    }


@router.get("/ai/config")
def get_ai_config():
    """Get current AI detection configuration."""
    return {
        "targets": _realtime_state["targets"],
        "confidence": _realtime_state["confidence"],
        "model_loaded": _realtime_state["model_loaded"]
    }


# ─── Alert Threshold Routes ─────────────────────────────────────────────────

@router.get("/alerts/config")
def get_alert_config():
    """Get current alert threshold configuration."""
    return {
        "enabled": _alert_manager.enabled,
        "thresholds": _alert_manager.thresholds,
        "cooldown_seconds": _alert_manager.cooldown_seconds,
        "connected_clients": len(_alert_manager.connections),
    }


@router.post("/alerts/config")
def update_alert_config(update: AlertThresholdUpdate):
    """Update alert thresholds and cooldown."""
    _alert_manager.thresholds = dict(update.thresholds)
    _alert_manager.cooldown_seconds = update.cooldown_seconds
    _alert_manager.enabled = update.enabled

    # Persist to config.json
    try:
        from unified_server.config import load_config, save_config
        cfg = load_config()
        cfg.alerts.thresholds = update.thresholds
        cfg.alerts.cooldown_seconds = update.cooldown_seconds
        cfg.alerts.enabled = update.enabled
        save_config(cfg)
    except Exception as e:
        logger.warning(f"Could not persist alert config: {e}")

    return {
        "status": "success",
        "thresholds": _alert_manager.thresholds,
        "cooldown_seconds": _alert_manager.cooldown_seconds,
        "enabled": _alert_manager.enabled,
    }


# ─── WebSocket for Real-Time Alerts ─────────────────────────────────────────

@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for push-based threshold alerts.
    Connect to receive real-time popup notifications when detections exceed thresholds."""
    global _ws_loop
    await websocket.accept()
    _alert_manager.connections.add(websocket)
    _ws_loop = asyncio.get_event_loop()

    logger.info(f"WebSocket alert client connected ({len(_alert_manager.connections)} total)")

    # Send initial config to client
    await websocket.send_text(json.dumps({
        "type": "config",
        "thresholds": _alert_manager.thresholds,
        "cooldown_seconds": _alert_manager.cooldown_seconds,
        "enabled": _alert_manager.enabled,
    }))

    try:
        while True:
            # Keep connection alive; handle incoming messages (config updates, pings)
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "update_thresholds":
                    _alert_manager.thresholds = msg.get("thresholds", _alert_manager.thresholds)
                    _alert_manager.cooldown_seconds = msg.get("cooldown_seconds", _alert_manager.cooldown_seconds)
                elif msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        _alert_manager.connections.discard(websocket)
        logger.info(f"WebSocket alert client disconnected ({len(_alert_manager.connections)} remaining)")


# ─── MJPEG Streaming ────────────────────────────────────────────────────────

def generate_frames(cam_id: str):
    """Adaptive frame rate MJPEG generator."""
    while True:
        cam = _realtime_state["cameras"].get(cam_id)
        if not cam or not cam.is_running:
            break
        frame = cam.latest_frame_bytes
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        # Adaptive sleep: faster when we have frames, slower when idle
        time.sleep(0.033 if frame else 0.1)  # ~30fps max vs 10fps idle


@router.get("/cameras/{camera_id}/stream")
def stream_video(camera_id: str):
    """Stream MJPEG video for the camera."""
    if camera_id not in _realtime_state["cameras"]:
        raise HTTPException(status_code=404, detail="Camera not found")
    return StreamingResponse(generate_frames(camera_id), media_type="multipart/x-mixed-replace; boundary=frame")
