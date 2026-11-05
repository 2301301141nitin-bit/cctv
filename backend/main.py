import os
from fastapi import FastAPI, File, UploadFile, Depends, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
from io import BytesIO
from PIL import Image

import models
from database import engine, get_db
import ai_engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="CCTV Analysis Tool API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static/videos", exist_ok=True)
os.makedirs("static/frames", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/upload/")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Save video to disk
    video_path = f"static/videos/{file.filename}"
    with open(video_path, "wb") as buffer:
        buffer.write(await file.read())
        
    # Save to database
    db_video = models.Video(filename=file.filename, filepath=video_path)
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    
    # Process in background
    background_tasks.add_task(ai_engine.extract_and_index_video, video_path, db_video.id)
    
    return {"message": "Video uploaded successfully and is being processed", "video_id": db_video.id}

@app.get("/videos/")
def get_videos(db: Session = Depends(get_db)):
    videos = db.query(models.Video).all()
    return videos

@app.post("/search/text/")
async def search_text(query: str = Form(...)):
    results = ai_engine.search_by_text(query)
    # Ensure static paths have leading slash for frontend
    for r in results:
        r["filepath"] = f"/{r['filepath']}"
    return results

@app.post("/search/image/")
async def search_image(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image = Image.open(BytesIO(image_bytes))
    results = ai_engine.search_by_image(image)
    # Ensure static paths have leading slash for frontend
    for r in results:
        r["filepath"] = f"/{r['filepath']}"
    return results
