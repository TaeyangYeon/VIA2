from fastapi import APIRouter, File, HTTPException, UploadFile
from typing import Optional

from backend.models.image import ImageMetadata
from backend.services import image_store
from backend.services.image_validator import validate_content_type, validate_filename

router = APIRouter()


@router.post("/images/upload", status_code=201)
async def upload_image(file: UploadFile = File(...)) -> ImageMetadata:
    result = validate_filename(file.filename or "")
    if not result.is_valid:
        raise HTTPException(status_code=422, detail=result.error)

    if not validate_content_type(file.content_type):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid content type: {file.content_type}",
        )

    content = await file.read()
    return image_store.add(
        file_content=content,
        filename=file.filename,
        label=result.label,
        index=result.index,
    )


@router.get("/images")
async def list_images(group: Optional[str] = None) -> list[ImageMetadata]:
    if group is not None:
        return image_store.get_by_group(group)
    return image_store.get_all()


@router.delete("/images")
async def clear_images():
    image_store.clear_all()
    return {"message": "All images cleared"}


@router.get("/images/{image_id}")
async def get_image(image_id: str) -> ImageMetadata:
    metadata = image_store.get_by_id(image_id)
    if metadata is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return metadata


@router.delete("/images/{image_id}")
async def delete_image(image_id: str):
    if not image_store.delete_by_id(image_id):
        raise HTTPException(status_code=404, detail="Image not found")
    return {"message": "Image deleted"}
