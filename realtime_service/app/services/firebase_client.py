import logging
import firebase_admin
from firebase_admin import credentials, firestore, storage
from app.core.config import settings

logger = logging.getLogger(__name__)

class FirebaseClient:
    def __init__(self):
        self.enabled = settings.firebase_enabled
        self.db = None
        self.bucket = None
        
        if self.enabled:
            try:
                cred = credentials.Certificate(settings.firebase_credentials_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': settings.firebase_storage_bucket
                })
                self.db = firestore.client()
                self.bucket = storage.bucket()
                logger.info("Firebase client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase: {e}")
                self.enabled = False

    def upload_snapshot(self, event_id: str, image_bytes: bytes, content_type: str = 'image/jpeg') -> str:
        """Uploads an image snapshot to Firebase Storage and returns the public URL."""
        if not self.enabled or not self.bucket:
            return ""
        try:
            blob = self.bucket.blob(f"snapshots/{settings.node_id}/{event_id}.jpg")
            blob.upload_from_string(image_bytes, content_type=content_type)
            blob.make_public()
            return blob.public_url
        except Exception as e:
            logger.error(f"Failed to upload snapshot for event {event_id}: {e}")
            raise

    def sync_event(self, event_dict: dict):
        """Syncs a complex event to Firestore."""
        if not self.enabled or not self.db:
            return
        try:
            event_id = event_dict.get("event_id")
            event_dict["node_id"] = settings.node_id
            event_dict["operator_feedback"] = "pending"
            
            # Convert timestamp float to Firestore Timestamp if needed, but float works fine for basic sync
            # firebase_admin handles basic types well.
            
            self.db.collection("events").document(event_id).set(event_dict)
            logger.info(f"Successfully synced event {event_id} to Firebase.")
        except Exception as e:
            logger.error(f"Failed to sync event {event_dict.get('event_id')}: {e}")
            raise

    def update_camera_status(self, camera_id: str, status_data: dict):
        """Syncs the camera status under the node document."""
        if not self.enabled or not self.db:
            return
        try:
            doc_ref = self.db.collection("nodes").document(settings.node_id).collection("cameras").document(camera_id)
            doc_ref.set(status_data, merge=True)
            
            # Also update node heartbeat
            self.db.collection("nodes").document(settings.node_id).set({
                "status": "online",
                "last_heartbeat": firestore.SERVER_TIMESTAMP
            }, merge=True)
        except Exception as e:
            logger.error(f"Failed to update camera status for {camera_id}: {e}")
            # Do not raise here, camera status is low priority compared to events

firebase_client = FirebaseClient()
