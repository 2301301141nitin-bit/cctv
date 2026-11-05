"""
Static Analysis Router
Migrates backend/main.py routes for video upload, text search, and image search.
Prefix: /api/static-analysis
"""
import os
import sys
from fastapi import APIRouter, File, UploadFile, Depends, BackgroundTasks, Form
from sqlalchemy.orm import Session
from io import BytesIO
from PIL import Image

# Add the backend directory to sys.path so we can import its modules
BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import models
import ai_engine
from database import engine, get_db

# Ensure database tables exist
models.Base.metadata.create_all(bind=engine)

# Ensure static directories exist
os.makedirs(os.path.join(BACKEND_DIR, "static", "videos"), exist_ok=True)
os.makedirs(os.path.join(BACKEND_DIR, "static", "frames"), exist_ok=True)

router = APIRouter(prefix="/api/static-analysis", tags=["Static Analysis"])


@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a video file for AI frame extraction and indexing."""
    video_path = os.path.join(BACKEND_DIR, "static", "videos", file.filename)
    with open(video_path, "wb") as buffer:
        buffer.write(await file.read())

    db_video = models.Video(filename=file.filename, filepath=video_path)
    db.add(db_video)
    db.commit()
    db.refresh(db_video)

    background_tasks.add_task(ai_engine.extract_and_index_video, video_path, db_video.id)

    return {"message": "Video uploaded successfully and is being processed", "video_id": db_video.id}


@router.get("/videos")
def get_videos(db: Session = Depends(get_db)):
    """List all uploaded videos and their processing status."""
    videos = db.query(models.Video).all()
    return videos


@router.post("/search/text")
async def search_text(query: str = Form(...)):
    """Search indexed frames using a text query with CLIP prompt ensembling."""
    results = ai_engine.search_by_text(query)
    for r in results:
        # Convert to web-accessible path
        if "filepath" in r:
            fpath = r["filepath"]
            # Handle absolute paths
            if os.path.isabs(fpath):
                try:
                    rel = os.path.relpath(fpath, BACKEND_DIR)
                except ValueError:
                    rel = fpath
            else:
                rel = fpath
            # Normalize to forward slashes and ensure /backend-static/ prefix
            rel = rel.replace("\\", "/")
            if not rel.startswith("static/"):
                rel = f"static/{rel}"
            r["filepath"] = f"/backend-static/{rel.removeprefix('static/')}"
    return results


@router.post("/search/image")
async def search_image(file: UploadFile = File(...)):
    """Search indexed frames using an image query with CLIP embeddings."""
    image_bytes = await file.read()
    image = Image.open(BytesIO(image_bytes))
    results = ai_engine.search_by_image(image)
    for r in results:
        if "filepath" in r:
            fpath = r["filepath"]
            # Handle absolute paths
            if os.path.isabs(fpath):
                try:
                    rel = os.path.relpath(fpath, BACKEND_DIR)
                except ValueError:
                    rel = fpath
            else:
                rel = fpath
            # Normalize to forward slashes and ensure /backend-static/ prefix
            rel = rel.replace("\\", "/")
            if not rel.startswith("static/"):
                rel = f"static/{rel}"
            r["filepath"] = f"/backend-static/{rel.removeprefix('static/')}"
    return results


@router.get("/index-stats")
def get_index_stats():
    """Get FAISS index statistics."""
    return {
        "total_indexed_frames": ai_engine.index.ntotal,
        "embedding_dim": ai_engine.EMBEDDING_DIM,
        "metadata_entries": len(ai_engine.frame_metadata)
    }
