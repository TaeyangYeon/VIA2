from pydantic import BaseModel, model_validator


class ROICoordinates(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int

    @model_validator(mode="after")
    def validate_coordinates(self) -> "ROICoordinates":
        if self.x1 < 0 or self.y1 < 0 or self.x2 < 0 or self.y2 < 0:
            raise ValueError("All ROI coordinates must be non-negative")
        if self.x1 >= self.x2:
            raise ValueError("x1 must be less than x2")
        if self.y1 >= self.y2:
            raise ValueError("y1 must be less than y2")
        return self
