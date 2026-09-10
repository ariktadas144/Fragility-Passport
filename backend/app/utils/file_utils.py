"""Evidence file storage. Frames/clips live on disk under
settings.evidence_dir; the database only ever stores the relative path."""
import shutil
import uuid
from pathlib import Path

from app.config import get_settings


def ensure_evidence_dir() -> Path:
    settings = get_settings()
    settings.evidence_dir.mkdir(parents=True, exist_ok=True)
    return settings.evidence_dir


def save_evidence_file(source_path: str, event_public_id: str) -> str:
    """Copies a file the ML pipeline already wrote to disk (a saved frame or
    clip) into the managed evidence directory, returning the stored path.

    Raises FileNotFoundError if source_path doesn't exist — callers should
    let that surface as a clear error rather than silently skipping evidence.
    """
    src = Path(source_path)
    if not src.exists():
        raise FileNotFoundError(f"Evidence source file not found: {source_path}")

    target_dir = ensure_evidence_dir()
    dest_name = f"{event_public_id}_{uuid.uuid4().hex[:8]}{src.suffix}"
    dest_path = target_dir / dest_name
    shutil.copy2(src, dest_path)
    return str(dest_path)
