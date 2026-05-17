import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.models.image import ImageMetadata

_lock = threading.Lock()
_store: dict[str, ImageMetadata] = {}
_upload_dir = Path("data/uploads/")


def configure_upload_dir(path: str | Path) -> None:
    global _upload_dir
    with _lock:
        _upload_dir = Path(path)
        _upload_dir.mkdir(parents=True, exist_ok=True)


def _compute_group(index: int) -> str:
    return "analysis" if index == 1 else "test"


def add(file_content: bytes, filename: str, label: str, index: int) -> ImageMetadata:
    with _lock:
        existing = next(
            (m for m in _store.values() if m.label == label and m.index == index),
            None,
        )
        if existing:
            old_path = Path(existing.file_path)
            if old_path.exists():
                old_path.unlink()
            del _store[existing.id]

        _upload_dir.mkdir(parents=True, exist_ok=True)
        image_id = str(uuid.uuid4())
        file_path = _upload_dir / f"{image_id}_{filename}"

        with open(file_path, "wb") as f:
            f.write(file_content)

        metadata = ImageMetadata(
            id=image_id,
            original_filename=filename,
            label=label,
            index=index,
            file_size=len(file_content),
            upload_timestamp=datetime.now(timezone.utc),
            file_path=str(file_path),
            group=_compute_group(index),
        )
        _store[image_id] = metadata
        return metadata


def get_by_id(image_id: str) -> ImageMetadata | None:
    with _lock:
        return _store.get(image_id)


def get_all() -> list[ImageMetadata]:
    with _lock:
        return list(_store.values())


def get_by_group(group: str) -> list[ImageMetadata]:
    with _lock:
        return [m for m in _store.values() if m.group == group]


def delete_by_id(image_id: str) -> bool:
    with _lock:
        if image_id not in _store:
            return False
        metadata = _store.pop(image_id)
        file_path = Path(metadata.file_path)
        if file_path.exists():
            file_path.unlink()
        return True


def clear_all() -> None:
    with _lock:
        for metadata in _store.values():
            file_path = Path(metadata.file_path)
            if file_path.exists():
                file_path.unlink()
        _store.clear()
