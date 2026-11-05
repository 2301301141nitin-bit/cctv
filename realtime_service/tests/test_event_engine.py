import pytest
import time
from app.services.event_engine import EventEngine
from app.models.schemas import FrameEvent, Detection, BBox

@pytest.fixture
def mock_rules(tmp_path):
    import json
    rules = {
        "cameras": {
            "test_cam": {
                "restricted_zones": [
                    {
                        "name": "Test Zone",
                        "polygon": [[0, 0], [10, 0], [10, 10], [0, 10]],
                        "severity": "high",
                        "cooldown_seconds": 10,
                        "target_classes": ["person"]
                    }
                ],
                "loitering": [
                    {
                        "name": "Test Loitering",
                        "polygon": [[0, 0], [10, 0], [10, 10], [0, 10]],
                        "threshold_seconds": 2,
                        "severity": "medium",
                        "cooldown_seconds": 10,
                        "target_classes": ["person"]
                    }
                ],
                "group_detection": [
                    {
                        "name": "Test Group",
                        "min_people": 2,
                        "max_distance": 5,
                        "threshold_seconds": 1,
                        "severity": "low",
                        "cooldown_seconds": 10
                    }
                ]
            }
        }
    }
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(json.dumps(rules))
    return str(rules_file)

def create_mock_event(timestamp: float, x: float, y: float, track_id: int, class_name: str = "person") -> FrameEvent:
    return FrameEvent(
        camera_id="test_cam",
        frame_index=1,
        timestamp=timestamp,
        detections=[
            Detection(
                track_id=track_id,
                class_name=class_name,
                confidence=0.9,
                bbox=BBox(x1=x-1, y1=y-1, x2=x+1, y2=y+1) # Center is exactly (x, y)
            )
        ]
    )

def test_restricted_zone_entry(mock_rules):
    engine = EventEngine(rules_path=mock_rules)
    
    # Person outside zone
    event1 = create_mock_event(time.time(), 20, 20, track_id=1)
    res = engine.process(event1)
    assert len(res) == 0
    
    # Person inside zone
    event2 = create_mock_event(time.time() + 1, 5, 5, track_id=1)
    res = engine.process(event2)
    assert len(res) == 1
    assert res[0].event_type == "Restricted Zone Entry"
    assert res[0].entity_ids == [1]

def test_loitering(mock_rules):
    engine = EventEngine(rules_path=mock_rules)
    start_time = time.time()
    
    # Enter zone
    res = engine.process(create_mock_event(start_time, 5, 5, track_id=1))
    # Should trigger restricted zone entry, but NOT loitering yet
    assert len(res) == 1
    assert res[0].event_type == "Restricted Zone Entry"
    
    # Still in zone, but threshold not met
    res = engine.process(create_mock_event(start_time + 1.0, 5, 5, track_id=1))
    assert len(res) == 0 # Cooldown for restricted zone prevents re-trigger, loitering not ready
    
    # Loitering threshold met
    res = engine.process(create_mock_event(start_time + 2.5, 5, 5, track_id=1))
    assert len(res) == 1
    assert res[0].event_type == "Loitering"

def test_group_detection(mock_rules):
    engine = EventEngine(rules_path=mock_rules)
    
    # Two people close to each other
    event = FrameEvent(
        camera_id="test_cam",
        frame_index=1,
        timestamp=time.time(),
        detections=[
            Detection(track_id=1, class_name="person", confidence=0.9, bbox=BBox(x1=10, y1=10, x2=12, y2=12)),
            Detection(track_id=2, class_name="person", confidence=0.9, bbox=BBox(x1=13, y1=13, x2=15, y2=15)), # Distance is roughly 4.2
            Detection(track_id=3, class_name="person", confidence=0.9, bbox=BBox(x1=100, y1=100, x2=102, y2=102)) # Far away
        ]
    )
    
    res = engine.process(event)
    assert len(res) == 1
    assert res[0].event_type == "Group Detection"
    assert set(res[0].entity_ids) == {1, 2}
