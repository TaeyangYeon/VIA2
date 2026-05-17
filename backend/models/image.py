from datetime import datetime
from pydantic import BaseModel


class ImageMetadata(BaseModel):
    id: str
    original_filename: str
    label: str
    index: int
    file_size: int
    upload_timestamp: datetime
    file_path: str
    group: str
