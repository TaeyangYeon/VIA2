import pytest
import httpx
from backend.main import app


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_stores():
    from backend.services import roi_store, config_store, directives_store
    roi_store.clear()
    config_store.reset()
    directives_store.reset()
    yield
    roi_store.clear()
    config_store.reset()
    directives_store.reset()


# ── ROI Model: validation ─────────────────────────────────────────────────────

def test_roi_model_valid_coordinates_accepted():
    from backend.models.roi import ROICoordinates
    roi = ROICoordinates(x1=0, y1=0, x2=100, y2=100)
    assert roi.x1 == 0
    assert roi.y1 == 0
    assert roi.x2 == 100
    assert roi.y2 == 100


def test_roi_model_x1_equal_x2_raises_validation_error():
    from pydantic import ValidationError
    from backend.models.roi import ROICoordinates
    with pytest.raises(ValidationError):
        ROICoordinates(x1=50, y1=0, x2=50, y2=100)


def test_roi_model_x1_greater_than_x2_raises_validation_error():
    from pydantic import ValidationError
    from backend.models.roi import ROICoordinates
    with pytest.raises(ValidationError):
        ROICoordinates(x1=100, y1=0, x2=50, y2=100)


def test_roi_model_y1_equal_y2_raises_validation_error():
    from pydantic import ValidationError
    from backend.models.roi import ROICoordinates
    with pytest.raises(ValidationError):
        ROICoordinates(x1=0, y1=50, x2=100, y2=50)


def test_roi_model_y1_greater_than_y2_raises_validation_error():
    from pydantic import ValidationError
    from backend.models.roi import ROICoordinates
    with pytest.raises(ValidationError):
        ROICoordinates(x1=0, y1=100, x2=100, y2=50)


def test_roi_model_negative_x1_raises_validation_error():
    from pydantic import ValidationError
    from backend.models.roi import ROICoordinates
    with pytest.raises(ValidationError):
        ROICoordinates(x1=-1, y1=0, x2=100, y2=100)


def test_roi_model_negative_y1_raises_validation_error():
    from pydantic import ValidationError
    from backend.models.roi import ROICoordinates
    with pytest.raises(ValidationError):
        ROICoordinates(x1=0, y1=-5, x2=100, y2=100)


def test_roi_model_negative_x2_raises_validation_error():
    from pydantic import ValidationError
    from backend.models.roi import ROICoordinates
    with pytest.raises(ValidationError):
        ROICoordinates(x1=-10, y1=0, x2=-5, y2=100)


def test_roi_model_all_zero_except_positive_x2_y2_is_valid():
    from backend.models.roi import ROICoordinates
    roi = ROICoordinates(x1=0, y1=0, x2=1, y2=1)
    assert roi.x1 == 0


# ── ROI Store ─────────────────────────────────────────────────────────────────

def test_roi_store_initially_returns_none():
    from backend.services import roi_store
    assert roi_store.get() is None


def test_roi_store_set_and_get_returns_roi():
    from backend.services import roi_store
    from backend.models.roi import ROICoordinates
    roi = ROICoordinates(x1=10, y1=20, x2=300, y2=400)
    roi_store.set(roi)
    result = roi_store.get()
    assert result is not None
    assert result.x1 == 10
    assert result.y1 == 20
    assert result.x2 == 300
    assert result.y2 == 400


def test_roi_store_clear_resets_to_none():
    from backend.services import roi_store
    from backend.models.roi import ROICoordinates
    roi_store.set(ROICoordinates(x1=0, y1=0, x2=10, y2=10))
    roi_store.clear()
    assert roi_store.get() is None


# ── ROI API endpoints ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_roi_when_not_set_returns_null():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/roi")
    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_post_roi_valid_coordinates_returns_200():
    payload = {"x1": 10, "y1": 20, "x2": 300, "y2": 400}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/roi", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["x1"] == 10
    assert data["y1"] == 20
    assert data["x2"] == 300
    assert data["y2"] == 400


@pytest.mark.asyncio
async def test_post_roi_persists_and_get_returns_it():
    payload = {"x1": 5, "y1": 10, "x2": 640, "y2": 480}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post("/api/roi", json=payload)
        response = await client.get("/api/roi")
    data = response.json()
    assert data["x1"] == 5
    assert data["x2"] == 640


@pytest.mark.asyncio
async def test_post_roi_x1_equal_x2_returns_422():
    payload = {"x1": 100, "y1": 0, "x2": 100, "y2": 200}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/roi", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_roi_x1_greater_than_x2_returns_422():
    payload = {"x1": 200, "y1": 0, "x2": 100, "y2": 200}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/roi", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_roi_y1_greater_than_y2_returns_422():
    payload = {"x1": 0, "y1": 300, "x2": 100, "y2": 100}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/roi", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_roi_negative_x1_returns_422():
    payload = {"x1": -1, "y1": 0, "x2": 100, "y2": 100}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/roi", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_roi_clears_and_get_returns_null():
    payload = {"x1": 0, "y1": 0, "x2": 100, "y2": 100}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post("/api/roi", json=payload)
        await client.delete("/api/roi")
        response = await client.get("/api/roi")
    assert response.json() is None


@pytest.mark.asyncio
async def test_delete_roi_returns_200():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete("/api/roi")
    assert response.status_code == 200


# ── Config Model: default values ──────────────────────────────────────────────

def test_config_model_default_mode_is_inspection():
    from backend.models.config import InspectionConfig
    config = InspectionConfig()
    assert config.mode == "inspection"


def test_config_model_default_max_iteration_is_3():
    from backend.models.config import InspectionConfig
    config = InspectionConfig()
    assert config.max_iteration == 3


def test_config_model_default_success_criteria_fields_are_none():
    from backend.models.config import InspectionConfig
    config = InspectionConfig()
    assert config.success_criteria.accuracy is None
    assert config.success_criteria.fp_rate is None
    assert config.success_criteria.fn_rate is None
    assert config.success_criteria.coord_error is None


def test_config_model_mode_align_is_valid():
    from backend.models.config import InspectionConfig
    config = InspectionConfig(mode="align")
    assert config.mode == "align"


def test_config_model_invalid_mode_raises_validation_error():
    from pydantic import ValidationError
    from backend.models.config import InspectionConfig
    with pytest.raises(ValidationError):
        InspectionConfig(mode="unknown")


def test_config_model_max_iteration_1_is_valid():
    from backend.models.config import InspectionConfig
    config = InspectionConfig(max_iteration=1)
    assert config.max_iteration == 1


def test_config_model_max_iteration_10_is_valid():
    from backend.models.config import InspectionConfig
    config = InspectionConfig(max_iteration=10)
    assert config.max_iteration == 10


def test_config_model_max_iteration_0_raises_validation_error():
    from pydantic import ValidationError
    from backend.models.config import InspectionConfig
    with pytest.raises(ValidationError):
        InspectionConfig(max_iteration=0)


def test_config_model_max_iteration_11_raises_validation_error():
    from pydantic import ValidationError
    from backend.models.config import InspectionConfig
    with pytest.raises(ValidationError):
        InspectionConfig(max_iteration=11)


def test_config_model_accuracy_1_0_is_valid():
    from backend.models.config import InspectionConfig, SuccessCriteria
    config = InspectionConfig(success_criteria=SuccessCriteria(accuracy=1.0))
    assert config.success_criteria.accuracy == 1.0


def test_config_model_accuracy_above_1_raises_validation_error():
    from pydantic import ValidationError
    from backend.models.config import InspectionConfig, SuccessCriteria
    with pytest.raises(ValidationError):
        InspectionConfig(success_criteria=SuccessCriteria(accuracy=1.1))


def test_config_model_accuracy_below_0_raises_validation_error():
    from pydantic import ValidationError
    from backend.models.config import InspectionConfig, SuccessCriteria
    with pytest.raises(ValidationError):
        InspectionConfig(success_criteria=SuccessCriteria(accuracy=-0.1))


def test_config_model_fp_rate_0_0_is_valid():
    from backend.models.config import InspectionConfig, SuccessCriteria
    config = InspectionConfig(success_criteria=SuccessCriteria(fp_rate=0.0))
    assert config.success_criteria.fp_rate == 0.0


def test_config_model_coord_error_0_is_valid():
    from backend.models.config import InspectionConfig, SuccessCriteria
    config = InspectionConfig(success_criteria=SuccessCriteria(coord_error=0.0))
    assert config.success_criteria.coord_error == 0.0


def test_config_model_coord_error_negative_raises_validation_error():
    from pydantic import ValidationError
    from backend.models.config import InspectionConfig, SuccessCriteria
    with pytest.raises(ValidationError):
        InspectionConfig(success_criteria=SuccessCriteria(coord_error=-1.0))


# ── Config Store ──────────────────────────────────────────────────────────────

def test_config_store_returns_default_config():
    from backend.services import config_store
    from backend.models.config import InspectionConfig
    config = config_store.get()
    assert isinstance(config, InspectionConfig)
    assert config.mode == "inspection"
    assert config.max_iteration == 3


def test_config_store_update_and_get_returns_updated():
    from backend.services import config_store
    from backend.models.config import InspectionConfig
    new_config = InspectionConfig(mode="align", max_iteration=5)
    config_store.update(new_config)
    result = config_store.get()
    assert result.mode == "align"
    assert result.max_iteration == 5


def test_config_store_reset_returns_defaults():
    from backend.services import config_store
    from backend.models.config import InspectionConfig
    config_store.update(InspectionConfig(mode="align", max_iteration=7))
    config_store.reset()
    assert config_store.get().mode == "inspection"
    assert config_store.get().max_iteration == 3


# ── Config API: basic endpoints ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_config_returns_200_with_defaults():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "inspection"
    assert data["max_iteration"] == 3


@pytest.mark.asyncio
async def test_post_config_valid_payload_returns_200():
    payload = {"mode": "align", "max_iteration": 5}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/config", json=payload)
    assert response.status_code == 200
    assert response.json()["mode"] == "align"


@pytest.mark.asyncio
async def test_post_config_persists_to_get():
    payload = {"mode": "align", "max_iteration": 7}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post("/api/config", json=payload)
        response = await client.get("/api/config")
    data = response.json()
    assert data["mode"] == "align"
    assert data["max_iteration"] == 7


@pytest.mark.asyncio
async def test_post_config_invalid_mode_returns_422():
    payload = {"mode": "invalid"}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/config", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_config_max_iteration_0_returns_422():
    payload = {"max_iteration": 0}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/config", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_config_max_iteration_11_returns_422():
    payload = {"max_iteration": 11}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/config", json=payload)
    assert response.status_code == 422


# ── Config API: warning logic ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_post_config_accuracy_above_099_triggers_warning():
    payload = {"success_criteria": {"accuracy": 0.995}}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/config", json=payload)
    data = response.json()
    assert "warnings" in data
    assert any("99%" in w or "0.99" in w or "Accuracy" in w for w in data["warnings"])


@pytest.mark.asyncio
async def test_post_config_accuracy_exactly_099_no_warning():
    payload = {"success_criteria": {"accuracy": 0.99}}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/config", json=payload)
    data = response.json()
    warnings = data.get("warnings", [])
    assert not any("Accuracy" in w for w in warnings)


@pytest.mark.asyncio
async def test_post_config_fp_rate_below_0005_triggers_warning():
    payload = {"success_criteria": {"fp_rate": 0.004}}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/config", json=payload)
    data = response.json()
    assert "warnings" in data
    assert any("FP" in w or "fp" in w.lower() for w in data["warnings"])


@pytest.mark.asyncio
async def test_post_config_fp_rate_exactly_0005_no_warning():
    payload = {"success_criteria": {"fp_rate": 0.005}}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/config", json=payload)
    data = response.json()
    warnings = data.get("warnings", [])
    assert not any("FP" in w for w in warnings)


@pytest.mark.asyncio
async def test_post_config_fn_rate_below_0005_triggers_warning():
    payload = {"success_criteria": {"fn_rate": 0.001}}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/config", json=payload)
    data = response.json()
    assert "warnings" in data
    assert any("FN" in w or "fn" in w.lower() for w in data["warnings"])


@pytest.mark.asyncio
async def test_post_config_coord_error_below_05_triggers_warning():
    payload = {"success_criteria": {"coord_error": 0.3}}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/config", json=payload)
    data = response.json()
    assert "warnings" in data
    assert any("coord" in w.lower() or "Coordinate" in w for w in data["warnings"])


@pytest.mark.asyncio
async def test_post_config_coord_error_exactly_05_no_warning():
    payload = {"success_criteria": {"coord_error": 0.5}}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/config", json=payload)
    data = response.json()
    warnings = data.get("warnings", [])
    assert not any("coord" in w.lower() for w in warnings)


@pytest.mark.asyncio
async def test_post_config_all_extreme_goals_triggers_all_warnings():
    payload = {
        "success_criteria": {
            "accuracy": 0.999,
            "fp_rate": 0.001,
            "fn_rate": 0.002,
            "coord_error": 0.1,
        }
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/config", json=payload)
    data = response.json()
    assert "warnings" in data
    assert len(data["warnings"]) == 4


@pytest.mark.asyncio
async def test_post_config_no_extreme_goals_no_warnings_field():
    payload = {
        "success_criteria": {
            "accuracy": 0.95,
            "fp_rate": 0.01,
            "fn_rate": 0.01,
            "coord_error": 1.0,
        }
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/config", json=payload)
    data = response.json()
    warnings = data.get("warnings", [])
    assert len(warnings) == 0


@pytest.mark.asyncio
async def test_get_config_has_no_warnings_field():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/config")
    data = response.json()
    assert "warnings" not in data


# ── Directives Model: defaults ────────────────────────────────────────────────

def test_directives_model_default_all_fields_empty_string():
    from backend.models.directives import AgentDirectives
    d = AgentDirectives()
    assert d.orchestrator == ""
    assert d.spec == ""
    assert d.image_analysis == ""
    assert d.depth == ""
    assert d.material == ""
    assert d.pipeline_composer == ""
    assert d.vision_judge == ""
    assert d.inspection_plan == ""
    assert d.test == ""


def test_directives_model_accepts_custom_values():
    from backend.models.directives import AgentDirectives
    d = AgentDirectives(orchestrator="focus on speed", spec="use strict mode")
    assert d.orchestrator == "focus on speed"
    assert d.spec == "use strict mode"
    assert d.image_analysis == ""


# ── Directives Store ──────────────────────────────────────────────────────────

def test_directives_store_returns_default_empty_strings():
    from backend.services import directives_store
    d = directives_store.get()
    assert d.orchestrator == ""
    assert d.test == ""


def test_directives_store_update_and_get_returns_updated():
    from backend.services import directives_store
    from backend.models.directives import AgentDirectives
    directives_store.update(AgentDirectives(orchestrator="be concise"))
    result = directives_store.get()
    assert result.orchestrator == "be concise"
    assert result.spec == ""


def test_directives_store_reset_returns_defaults():
    from backend.services import directives_store
    from backend.models.directives import AgentDirectives
    directives_store.update(AgentDirectives(orchestrator="some directive"))
    directives_store.reset()
    assert directives_store.get().orchestrator == ""


# ── Directives API endpoints ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_directives_returns_200_with_empty_defaults():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/directives")
    assert response.status_code == 200
    data = response.json()
    assert data["orchestrator"] == ""
    assert data["spec"] == ""
    assert data["image_analysis"] == ""
    assert data["depth"] == ""
    assert data["material"] == ""
    assert data["pipeline_composer"] == ""
    assert data["vision_judge"] == ""
    assert data["inspection_plan"] == ""
    assert data["test"] == ""


@pytest.mark.asyncio
async def test_post_directives_saves_and_get_returns_updated():
    payload = {"orchestrator": "prioritize accuracy", "spec": "use JSON output"}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        post_response = await client.post("/api/directives", json=payload)
        assert post_response.status_code == 200
        get_response = await client.get("/api/directives")
    data = get_response.json()
    assert data["orchestrator"] == "prioritize accuracy"
    assert data["spec"] == "use JSON output"
    assert data["image_analysis"] == ""


@pytest.mark.asyncio
async def test_post_directives_partial_update_preserves_other_defaults():
    payload = {"depth": "focus on surface analysis"}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/directives", json=payload)
    data = response.json()
    assert data["depth"] == "focus on surface analysis"
    assert data["orchestrator"] == ""
    assert data["material"] == ""
    assert data["test"] == ""


@pytest.mark.asyncio
async def test_post_directives_all_fields_saved():
    payload = {
        "orchestrator": "a",
        "spec": "b",
        "image_analysis": "c",
        "depth": "d",
        "material": "e",
        "pipeline_composer": "f",
        "vision_judge": "g",
        "inspection_plan": "h",
        "test": "i",
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/directives", json=payload)
    data = response.json()
    assert data["orchestrator"] == "a"
    assert data["spec"] == "b"
    assert data["image_analysis"] == "c"
    assert data["depth"] == "d"
    assert data["material"] == "e"
    assert data["pipeline_composer"] == "f"
    assert data["vision_judge"] == "g"
    assert data["inspection_plan"] == "h"
    assert data["test"] == "i"
