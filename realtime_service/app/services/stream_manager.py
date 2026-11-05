from typing import Dict, List
from app.services.camera_source import CameraSource
from app.models.schemas import CameraResponse

class StreamManager:
    def __init__(self):
        self.cameras: Dict[str, CameraSource] = {}

    def add_camera(self, source: str, sampling_rate: int) -> CameraSource:
        cam = CameraSource(source=source, sampling_rate=sampling_rate)
        cam.start()
        self.cameras[cam.id] = cam
        return cam

    def remove_camera(self, camera_id: str) -> bool:
        cam = self.cameras.pop(camera_id, None)
        if cam:
            cam.stop()
            return True
        return False

    def get_camera(self, camera_id: str) -> CameraSource:
        return self.cameras.get(camera_id)

    def list_cameras(self) -> List[CameraResponse]:
        return [
            CameraResponse(
                id=c.id,
                source=c.source,
                status="running" if c.is_running else "stopped",
                sampling_rate=c.sampling_rate
            ) for c in self.cameras.values()
        ]

    def get_all_latest_events(self) -> List[dict]:
        events = []
        for cam in self.cameras.values():
            if cam.latest_event:
                events.append(cam.latest_event.model_dump())
        return events

# Singleton manager
stream_manager = StreamManager()
