from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    filepath = Column(String)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="processing") # processing, ready, error

    frames = relationship("Frame", back_populates="video", cascade="all, delete-orphan")

class Frame(Base):
    __tablename__ = "frames"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    timestamp = Column(Float) # in seconds
    filepath = Column(String) # path to extracted frame image

    video = relationship("Video", back_populates="frames")
