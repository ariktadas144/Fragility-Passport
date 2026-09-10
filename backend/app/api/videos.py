"""Video registration. Kept deliberately thin — there's no dedicated
video_service.py in this project, since there's no business logic here
beyond a plain database read/write (the interesting logic, resolving a
video from a detection, already lives in event_service._get_or_create_video)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.security import require_api_key
from app.database.database import get_db
from app.models.video import Video

router = APIRouter(prefix="/videos", tags=["videos"])


class VideoCreate(BaseModel):
    filename: str
    dock: str | None = None
    source_clip_ref: str | None = None
    duration_seconds: float | None = None
    fps: float | None = None


class VideoRead(VideoCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str


@router.post("", response_model=VideoRead, dependencies=[Depends(require_api_key)])
def create_video(payload: VideoCreate, db: Session = Depends(get_db)):
    video = Video(**payload.model_dump(), status="uploaded")
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.get("", response_model=list[VideoRead])
def list_videos(db: Session = Depends(get_db)):
    return db.query(Video).order_by(Video.uploaded_at.desc()).all()


@router.get("/{video_id}", response_model=VideoRead)
def get_video(video_id: int, db: Session = Depends(get_db)):
    video = db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
    return video
