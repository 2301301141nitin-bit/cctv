from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class EventEntity(BaseModel):
    track_id: int
    class_name: str
    confidence: float

class ComplexEvent(BaseModel):
    event_id: str
    camera_id: str
    timestamp: float
    event_type: str
    severity: str
    confidence: float
    risk_score: float
    entity_ids: List[int]
    evidence_reference: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
