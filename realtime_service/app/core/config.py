from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    default_frame_sampling: int = 3
    model_name: str = "yolov8n.pt"

    # Firebase Settings
    firebase_enabled: bool = False
    firebase_credentials_path: str = "serviceAccountKey.json"
    firebase_storage_bucket: str = ""
    
    node_id: str = "local-node-1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
