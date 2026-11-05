import json
import time
import uuid
import math
from typing import List, Dict, Tuple, Any
from collections import defaultdict
from shapely.geometry import Point, Polygon
from app.models.schemas import FrameEvent, Detection
from app.models.events import ComplexEvent

class TrackerState:
    def __init__(self):
        self.first_seen: float = time.time()
        self.last_seen: float = time.time()
        self.zone_entry_times: Dict[str, float] = {} # zone_name -> timestamp
        self.last_positions: List[Tuple[float, float]] = [] # (cx, cy)
        
class EventEngine:
    def __init__(self, rules_path: str = "app/core/rules.json"):
        self.rules_path = rules_path
        self.rules = self._load_rules()
        self.state: Dict[str, Dict[int, TrackerState]] = defaultdict(lambda: defaultdict(TrackerState))
        self.cooldowns: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float)) # cam_id -> {rule_name: last_triggered_time}

    def _load_rules(self) -> dict:
        try:
            with open(self.rules_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load rules: {e}")
            return {"cameras": {}}

    def process(self, frame_event: FrameEvent) -> List[ComplexEvent]:
        events = []
        cam_rules = self.rules.get("cameras", {}).get(frame_event.camera_id, {})
        if not cam_rules:
            return events

        # Cleanup old states (if object not seen for 5 seconds)
        current_time = frame_event.timestamp
        active_ids = {d.track_id for d in frame_event.detections if d.track_id is not None}
        cam_state = self.state[frame_event.camera_id]
        
        for tid in list(cam_state.keys()):
            if current_time - cam_state[tid].last_seen > 5.0:
                del cam_state[tid]

        # Precompute centers for detections
        centers = {}
        for d in frame_event.detections:
            if d.track_id is not None:
                cx = (d.bbox.x1 + d.bbox.x2) / 2.0
                cy = (d.bbox.y1 + d.bbox.y2) / 2.0
                centers[d.track_id] = (cx, cy)
                
                # Update tracker state
                if d.track_id not in cam_state:
                    cam_state[d.track_id].first_seen = current_time
                cam_state[d.track_id].last_seen = current_time
                cam_state[d.track_id].last_positions.append((cx, cy))
                if len(cam_state[d.track_id].last_positions) > 30: # Keep last 30 frames
                    cam_state[d.track_id].last_positions.pop(0)

        # 1. Restricted Zone Entry
        for rule in cam_rules.get("restricted_zones", []):
            poly = Polygon(rule["polygon"])
            for d in frame_event.detections:
                if d.track_id is not None and d.class_name in rule["target_classes"]:
                    pt = Point(centers[d.track_id])
                    if poly.contains(pt):
                        # Check cooldown
                        if self._can_trigger(frame_event.camera_id, rule["name"], rule["cooldown_seconds"], current_time):
                            events.append(self._create_event(frame_event, rule, "Restricted Zone Entry", [d.track_id]))
                            self._set_cooldown(frame_event.camera_id, rule["name"], current_time)
                            
        # 2. Loitering
        for rule in cam_rules.get("loitering", []):
            poly = Polygon(rule["polygon"])
            for d in frame_event.detections:
                if d.track_id is not None and d.class_name in rule["target_classes"]:
                    pt = Point(centers[d.track_id])
                    if poly.contains(pt):
                        if rule["name"] not in cam_state[d.track_id].zone_entry_times:
                            cam_state[d.track_id].zone_entry_times[rule["name"]] = current_time
                        
                        time_in_zone = current_time - cam_state[d.track_id].zone_entry_times[rule["name"]]
                        if time_in_zone >= rule["threshold_seconds"]:
                            if self._can_trigger(frame_event.camera_id, rule["name"], rule["cooldown_seconds"], current_time):
                                events.append(self._create_event(frame_event, rule, "Loitering", [d.track_id], {"time_in_zone": time_in_zone}))
                                self._set_cooldown(frame_event.camera_id, rule["name"], current_time)
                    else:
                        # Reset if outside zone
                        cam_state[d.track_id].zone_entry_times.pop(rule["name"], None)

        # 3. Group Detection (Simple proximity check)
        for rule in cam_rules.get("group_detection", []):
            people = [d for d in frame_event.detections if d.track_id is not None and d.class_name == "person"]
            # Find clusters (very naive approach for Phase 2)
            clusters = []
            visited = set()
            for p1 in people:
                if p1.track_id in visited:
                    continue
                cluster = [p1]
                visited.add(p1.track_id)
                for p2 in people:
                    if p2.track_id not in visited:
                        c1 = centers[p1.track_id]
                        c2 = centers[p2.track_id]
                        dist = math.hypot(c1[0]-c2[0], c1[1]-c2[1])
                        if dist <= rule["max_distance"]:
                            cluster.append(p2)
                            visited.add(p2.track_id)
                clusters.append(cluster)
            
            for cluster in clusters:
                if len(cluster) >= rule["min_people"]:
                    # Need to check persistence for the group (approximation: just check if the oldest person in group has been around long enough)
                    # For a robust system, we would track cluster IDs, but for now we'll trigger if conditions are met and cooldown allows.
                    if self._can_trigger(frame_event.camera_id, rule["name"], rule["cooldown_seconds"], current_time):
                        track_ids = [p.track_id for p in cluster]
                        events.append(self._create_event(frame_event, rule, "Group Detection", track_ids, {"group_size": len(cluster)}))
                        self._set_cooldown(frame_event.camera_id, rule["name"], current_time)

        # 4. Abandoned Object
        for rule in cam_rules.get("abandoned_object", []):
            poly = Polygon(rule["polygon"])
            for d in frame_event.detections:
                if d.track_id is not None and d.class_name in rule["target_classes"]:
                    pt = Point(centers[d.track_id])
                    if poly.contains(pt):
                        if rule["name"] not in cam_state[d.track_id].zone_entry_times:
                            cam_state[d.track_id].zone_entry_times[rule["name"]] = current_time
                        
                        time_in_zone = current_time - cam_state[d.track_id].zone_entry_times[rule["name"]]
                        if time_in_zone >= rule["threshold_seconds"]:
                            if self._can_trigger(frame_event.camera_id, rule["name"], rule["cooldown_seconds"], current_time):
                                events.append(self._create_event(frame_event, rule, "Abandoned Object", [d.track_id], {"time_abandoned": time_in_zone}))
                                self._set_cooldown(frame_event.camera_id, rule["name"], current_time)
                    else:
                        cam_state[d.track_id].zone_entry_times.pop(rule["name"], None)
                        
        return events

    def _can_trigger(self, cam_id: str, rule_name: str, cooldown: float, current_time: float) -> bool:
        last_time = self.cooldowns[cam_id][rule_name]
        return (current_time - last_time) >= cooldown

    def _set_cooldown(self, cam_id: str, rule_name: str, current_time: float):
        self.cooldowns[cam_id][rule_name] = current_time

    def _create_event(self, frame_event: FrameEvent, rule: dict, event_type: str, entity_ids: List[int], metadata: dict = None) -> ComplexEvent:
        return ComplexEvent(
            event_id=str(uuid.uuid4()),
            camera_id=frame_event.camera_id,
            timestamp=frame_event.timestamp,
            event_type=event_type,
            severity=rule.get("severity", "medium"),
            confidence=1.0, # Could aggregate tracking confidence
            risk_score=0.8 if rule.get("severity") == "high" else 0.5,
            entity_ids=entity_ids,
            metadata=metadata or {}
        )
