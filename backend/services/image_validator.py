import re
from dataclasses import dataclass

_FILENAME_RE = re.compile(
    r"^(ok|ng)_([1-9]\d*)\.(png|jpg|jpeg|bmp|tiff)$",
    re.IGNORECASE,
)

_VALID_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/bmp",
    "image/tiff",
    "image/x-bmp",
}


@dataclass
class ValidationResult:
    is_valid: bool
    label: str | None = None
    index: int | None = None
    error: str | None = None


def validate_filename(filename: str) -> ValidationResult:
    match = _FILENAME_RE.match(filename)
    if not match:
        return ValidationResult(is_valid=False, error=f"Invalid filename: {filename}")
    return ValidationResult(
        is_valid=True,
        label=match.group(1).upper(),
        index=int(match.group(2)),
    )


def validate_content_type(content_type: str | None) -> bool:
    return content_type in _VALID_MIME_TYPES
