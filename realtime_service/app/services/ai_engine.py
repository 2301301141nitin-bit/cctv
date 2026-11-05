from ultralytics import YOLO
from typing import List, Dict, Any, Tuple
import cv2
import numpy as np
from app.core.config import settings

class AIEngine:
    def __init__(self):
        # Load the state-of-the-art YOLOv8l-worldv2 model for open-vocabulary detection
        self.model = YOLO("yolov8l-worldv2.pt")
        self.current_confidence = 0.25
        self.current_targets = ["person", "car"]
        self.model.set_classes(self.current_targets)

    def set_semantic_targets(self, targets: List[str]):
        if targets:
            self.current_targets = targets
            self.model.set_classes(self.current_targets)
            
    def set_confidence(self, conf: float):
        if 0.0 <= conf <= 1.0:
            self.current_confidence = conf

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Run YOLO detection and ByteTrack tracking on a frame.
        Returns the annotated frame and a list of detections.
        """
        # Run inference with dynamic confidence threshold
        results = self.model.track(
            source=frame,
            persist=True,        # Keep tracking IDs across frames
            tracker="bytetrack.yaml", # Use built-in ByteTrack
            verbose=False,       # Suppress ultralytics console logging per frame
            conf=self.current_confidence
        )

        detections = []
        annotated_frame = frame

        if results and len(results) > 0:
            result = results[0]
            annotated_frame = result.plot()  # Automatically draw bboxes and IDs
            
            # Extract boxes
            boxes = result.boxes
            if boxes is not None:
                for i in range(len(boxes)):
                    box = boxes[i]
                    
                    # Coordinates
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    # Confidence and Class
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    class_name = result.names[cls_id]
                    
                    # Tracking ID (might be None if tracking failed or just initialized)
                    track_id = None
                    if box.id is not None:
                        track_id = int(box.id[0])
                        
                    detections.append({
                        "track_id": track_id,
                        "class_name": class_name,
                        "confidence": conf,
                        "bbox": {
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2
                        }
                    })

        return annotated_frame, detections

# Singleton instance for the AI Engine to avoid reloading the model
engine = AIEngine()
