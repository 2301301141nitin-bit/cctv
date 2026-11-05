"""
Unified Configuration Manager
Reads/writes config.json and provides typed access to all settings.
"""
import os
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class CameraConfig(BaseModel):
    id: str = ""
    name: str = "Unnamed Camera"
    source: str = ""
    sampling_rate: int = 3
    enabled: bool = True


class AIConfig(BaseModel):
    realtime_model: str = "yolov8n.pt"
    clip_model: str = "openai/clip-vit-base-patch32"
    targets: List[str] = Field(default_factory=lambda: ["person", "car"])
    confidence: float = 0.25
    frame_sampling: int = 3


class RuleZone(BaseModel):
    name: str = ""
    polygon: List[List[float]] = Field(default_factory=list)
    severity: str = "medium"
    cooldown_seconds: int = 30
    target_classes: List[str] = Field(default_factory=lambda: ["person"])
    threshold_seconds: Optional[int] = None
    min_people: Optional[int] = None
    max_distance: Optional[float] = None
    camera_id: str = ""


class RulesConfig(BaseModel):
    restricted_zones: List[RuleZone] = Field(default_factory=list)
    loitering: List[RuleZone] = Field(default_factory=list)
    group_detection: List[RuleZone] = Field(default_factory=list)
    abandoned_object: List[RuleZone] = Field(default_factory=list)


class FirebaseConfig(BaseModel):
    enabled: bool = False
    credentials_path: str = "serviceAccountKey.json"
    storage_bucket: str = ""
    api_key: str = ""
    auth_domain: str = ""
    project_id: str = ""
    messaging_sender_id: str = ""
    app_id: str = ""


class StaticAnalysisConfig(BaseModel):
    fps_extract: float = 1.0
    batch_size: int = 32


class AlertConfig(BaseModel):
    """Threshold-based alert configuration. Alerts fire only when detection
    confidence meets or exceeds the per-class threshold."""
    enabled: bool = True
    cooldown_seconds: int = 10
    thresholds: Dict[str, float] = Field(default_factory=lambda: {
        "person": 0.6,
        "car": 0.5,
        "weapon": 0.3,
        "knife": 0.3,
        "fire": 0.3,
    })
    popup_enabled: bool = True
    sound_enabled: bool = True


class UnifiedConfig(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    cameras: List[CameraConfig] = Field(default_factory=list)
    ai: AIConfig = Field(default_factory=AIConfig)
    rules: RulesConfig = Field(default_factory=RulesConfig)
    firebase: FirebaseConfig = Field(default_factory=FirebaseConfig)
    static_analysis: StaticAnalysisConfig = Field(default_factory=StaticAnalysisConfig)
    alerts: AlertConfig = Field(default_factory=AlertConfig)


def load_config() -> UnifiedConfig:
    """Load configuration from config.json, creating defaults if missing."""
    cfg = UnifiedConfig()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
            cfg = UnifiedConfig(**data)
        except Exception as e:
            print(f"Warning: Could not parse config.json ({e}), using defaults.")
    # Allow environment variable overrides for cloud hosting
    if "PORT" in os.environ:
        try:
            cfg.server.port = int(os.environ["PORT"])
        except ValueError:
            pass
    if "HOST" in os.environ:
        cfg.server.host = os.environ["HOST"]
    return cfg


def save_config(config: UnifiedConfig):
    """Persist configuration to config.json."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config.model_dump(), f, indent=2)


def get_config() -> UnifiedConfig:
    """Get current configuration (convenience function)."""
    return load_config()
