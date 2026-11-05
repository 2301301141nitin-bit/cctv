import logging
import threading
import time
import queue
import cv2
import numpy as np
from typing import Tuple, Dict, Any
from app.services.firebase_client import firebase_client
from app.core.config import settings

logger = logging.getLogger(__name__)

class SyncEngine:
    def __init__(self):
        self.enabled = settings.firebase_enabled
        self.queue = queue.Queue()
        self.is_running = False
        self._thread = None
        self.max_retries = 3

    def start(self):
        if not self.enabled:
            logger.info("Firebase sync is disabled. SyncEngine will not start.")
            return
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()
        logger.info("SyncEngine started.")

    def stop(self):
        self.is_running = False
        if self._thread:
            # Wake up the queue if it's blocking
            self.queue.put(None)
            self._thread.join(timeout=2.0)

    def enqueue_event(self, event_dict: Dict[str, Any], frame: np.ndarray = None):
        """Adds an event and an optional frame snapshot to the sync queue."""
        if not self.enabled:
            return
        self.queue.put({"event": event_dict, "frame": frame, "retries": 0})

    def enqueue_camera_status(self, camera_id: str, source: str, status: str, sampling_rate: int):
        if not self.enabled:
            return
        payload = {
            "type": "camera_status",
            "camera_id": camera_id,
            "data": {
                "source": source,
                "status": status,
                "sampling_rate": sampling_rate
            }
        }
        self.queue.put(payload)

    def _worker_loop(self):
        while self.is_running:
            try:
                task = self.queue.get(timeout=1.0)
                if task is None:
                    continue
                    
                if task.get("type") == "camera_status":
                    firebase_client.update_camera_status(task["camera_id"], task["data"])
                    self.queue.task_done()
                    continue

                event_dict = task["event"]
                frame = task.get("frame")
                retries = task.get("retries", 0)

                try:
                    # 1. Upload snapshot if we have a frame
                    if frame is not None and not event_dict.get("snapshot_url"):
                        _, buffer = cv2.imencode('.jpg', frame)
                        image_bytes = buffer.tobytes()
                        public_url = firebase_client.upload_snapshot(event_dict["event_id"], image_bytes)
                        event_dict["snapshot_url"] = public_url

                    # 2. Sync event document
                    firebase_client.sync_event(event_dict)
                    
                except Exception as e:
                    logger.error(f"Sync failed for event {event_dict.get('event_id')}: {e}")
                    if retries < self.max_retries:
                        # Exponential backoff (2, 4, 8 seconds)
                        backoff = 2 ** (retries + 1)
                        logger.info(f"Retrying event {event_dict.get('event_id')} in {backoff} seconds...")
                        time.sleep(backoff)
                        task["retries"] = retries + 1
                        self.queue.put(task)
                    else:
                        logger.error(f"Event {event_dict.get('event_id')} failed after {self.max_retries} retries. Dropped.")

                self.queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Unexpected error in SyncEngine worker: {e}")

sync_engine = SyncEngine()
