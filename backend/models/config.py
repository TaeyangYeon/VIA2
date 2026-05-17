from typing import Literal, Optional
from pydantic import BaseModel, Field


class SuccessCriteria(BaseModel):
    accuracy: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    fp_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    fn_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    coord_error: Optional[float] = Field(default=None, ge=0.0)


class InspectionConfig(BaseModel):
    mode: Literal["inspection", "align"] = "inspection"
    max_iteration: int = Field(default=3, ge=1, le=10)
    success_criteria: SuccessCriteria = Field(default_factory=SuccessCriteria)
