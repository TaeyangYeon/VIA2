from fastapi import APIRouter

from backend.models.config import InspectionConfig
from backend.services import config_store

router = APIRouter()


def _build_warnings(config: InspectionConfig) -> list[str]:
    warnings = []
    sc = config.success_criteria
    if sc.accuracy is not None and sc.accuracy > 0.99:
        warnings.append("Accuracy above 99% is extremely difficult to achieve with rule-based methods")
    if sc.fp_rate is not None and sc.fp_rate < 0.005:
        warnings.append("FP rate below 0.5% may require deep learning approaches")
    if sc.fn_rate is not None and sc.fn_rate < 0.005:
        warnings.append("FN rate below 0.5% may require deep learning approaches")
    if sc.coord_error is not None and sc.coord_error < 0.5:
        warnings.append("Coordinate error below 0.5px may require sub-pixel algorithms or hardware upgrade")
    return warnings


@router.get("/config")
async def get_config() -> InspectionConfig:
    return config_store.get()


@router.post("/config")
async def save_config(config: InspectionConfig):
    config_store.update(config)
    result = config.model_dump()
    warnings = _build_warnings(config)
    if warnings:
        result["warnings"] = warnings
    else:
        result["warnings"] = []
    return result
