import cv2
import threading
import time
import logging
import uuid
from typing import List, Optional
from app.services.ai_engine import engine
from app.services.event_engine import EventEngine
from app.services.sync_engine import sync_engine
from app.models.schemas import FrameEvent, Detection, BBox

logger = logging.getLogger(__name__)
event_engine = EventEngine()

class CameraSource:
    def __init__(self, source: str, sampling_rate: int):
        self.id = str(uuid.uuid4())
        self.source = source
        self.sampling_rate = sampling_rate
        
        # Convert source to int if it's a device index (e.g., "0" -> 0)
        self._capture_source = int(self.source) if self.source.isdigit() else self.source
        
        self.cap = cv2.VideoCapture(self._capture_source)
        if not self.cap.isOpened():
            raise ValueError(f"Failed to open video source: {source}")
            
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self.frame_index = 0
        
        self.latest_event: Optional[FrameEvent] = None
        # In a real app we might want a queue or a pub/sub system to emit events.
        # For Phase 1, we will just store the latest event.

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self.cap and self.cap.isOpened():
            self.cap.release()

    def _capture_loop(self):
        logger.info(f"Started capture loop for camera {self.id} on source {self.source}")
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                logger.warning(f"Failed to grab frame for camera {self.id}. Stream might be disconnected.")
                # We could attempt to reconnect here, but for Phase 1 we will just sleep and retry or break.
                time.sleep(1)
                continue

            self.frame_index += 1
            
            # Apply frame sampling
            if self.frame_index % self.sampling_rate != 0:
                continue

            # Process frame using AI Engine
            try:
                annotated_frame, detections = engine.process_frame(frame)
                
                # Create standard JSON event
                event = FrameEvent(
                    camera_id=self.id,
                    frame_index=self.frame_index,
                    timestamp=time.time(),
                    detections=[Detection(**d) for d in detections]
                )
                
                self.latest_event = event
                
                # Process with Event Engine
                complex_events = event_engine.process(event)
                if complex_events:
                    for ce in complex_events:
                        logger.warning(f"ALERT: {ce.event_type} on camera {self.id}")
                        # Push to Firebase Sync Engine (non-blocking)
                        sync_engine.enqueue_event(ce.model_dump(), frame=annotated_frame)
                
                # In Phase 1 we will display it in a cv2 window for debug purposes if running locally.
                # In production, this should be disabled or streamed over websockets.
                cv2.imshow(f"Camera - {self.id}", annotated_frame)
                cv2.waitKey(1)
                
            except Exception as e:
                logger.error(f"Error processing frame for camera {self.id}: {e}")

        cv2.destroyWindow(f"Camera - {self.id}")
        logger.info(f"Stopped capture loop for camera {self.id}")
