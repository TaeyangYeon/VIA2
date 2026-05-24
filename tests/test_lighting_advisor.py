"""Tests for LightingAdvisor — pure rule-based lighting recommendations."""
import pytest

from agents.lighting_advisor import LightingAdvisor


@pytest.fixture
def advisor():
    return LightingAdvisor()


def test_empty_scene_context_returns_empty_list(advisor):
    result = advisor.generate_recommendations({})
    assert result == []


def test_all_safe_values_returns_empty_list(advisor):
    scene = {
        "surface_type": "plastic",
        "reflection_level": 0.3,
        "lighting_uniformity": 0.8,
        "illumination_type": "diffuse",
        "contrast": 0.7,
        "has_shadow_region": False,
        "noise_level": 0.1,
    }
    result = advisor.generate_recommendations(scene)
    assert result == []


# ── surface_type == "metal" ───────────────────────────────────────────────────

def test_metal_surface_triggers_polarization(advisor):
    scene = {"surface_type": "metal"}
    result = advisor.generate_recommendations(scene)
    cats = [r["category"] for r in result]
    assert "polarization" in cats


def test_metal_surface_recommendation_structure(advisor):
    scene = {"surface_type": "metal"}
    result = advisor.generate_recommendations(scene)
    rec = next(r for r in result if r["category"] == "polarization")
    assert "suggestion" in rec
    assert "reason" in rec
    assert rec["priority"] in ("high", "medium", "low")


def test_non_metal_surface_no_polarization(advisor):
    scene = {"surface_type": "plastic"}
    result = advisor.generate_recommendations(scene)
    assert all(r["category"] != "polarization" for r in result)


# ── reflection_level > 0.6 ────────────────────────────────────────────────────

def test_high_reflection_triggers_diffuse_lighting(advisor):
    scene = {"reflection_level": 0.7}
    result = advisor.generate_recommendations(scene)
    assert len(result) >= 1
    priorities = [r["priority"] for r in result]
    assert "high" in priorities


def test_reflection_at_boundary_not_triggered(advisor):
    scene = {"reflection_level": 0.6}
    result = advisor.generate_recommendations(scene)
    # 0.6 is NOT > 0.6, should not trigger
    assert all(r.get("reason", "").find("reflection") == -1 or
               "High reflection" not in r.get("reason", "") for r in result)


def test_high_reflection_recommendation_is_high_priority(advisor):
    scene = {"reflection_level": 0.9}
    result = advisor.generate_recommendations(scene)
    reflection_recs = [r for r in result if "reflection" in r.get("reason", "").lower()
                       or "diffuse" in r.get("suggestion", "").lower()]
    assert any(r["priority"] == "high" for r in reflection_recs)


# ── lighting_uniformity < 0.5 ─────────────────────────────────────────────────

def test_low_uniformity_triggers_uniform_light(advisor):
    scene = {"lighting_uniformity": 0.3}
    result = advisor.generate_recommendations(scene)
    assert len(result) >= 1
    assert any("uniform" in r["suggestion"].lower() or
               "ring" in r["suggestion"].lower() or
               "dome" in r["suggestion"].lower() for r in result)


def test_low_uniformity_is_high_priority(advisor):
    scene = {"lighting_uniformity": 0.2}
    result = advisor.generate_recommendations(scene)
    assert any(r["priority"] == "high" for r in result)


def test_uniformity_at_boundary_not_triggered(advisor):
    scene = {"lighting_uniformity": 0.5}
    result = advisor.generate_recommendations(scene)
    # 0.5 is NOT < 0.5, should not trigger uniformity rule
    assert result == []


# ── illumination_type == "spot" ───────────────────────────────────────────────

def test_spot_illumination_triggers_wider_coverage(advisor):
    scene = {"illumination_type": "spot"}
    result = advisor.generate_recommendations(scene)
    assert len(result) >= 1
    assert any("wider" in r["suggestion"].lower() or
               "coverage" in r["suggestion"].lower() for r in result)


def test_non_spot_illumination_no_coverage_suggestion(advisor):
    scene = {"illumination_type": "diffuse"}
    result = advisor.generate_recommendations(scene)
    assert result == []


# ── contrast < 0.3 ────────────────────────────────────────────────────────────

def test_low_contrast_triggers_contrast_suggestion(advisor):
    scene = {"contrast": 0.2}
    result = advisor.generate_recommendations(scene)
    assert len(result) >= 1
    assert any("contrast" in r["suggestion"].lower() or
               "angle" in r["category"] or
               "coaxial" in r["suggestion"].lower() for r in result)


def test_contrast_at_boundary_not_triggered(advisor):
    scene = {"contrast": 0.3}
    result = advisor.generate_recommendations(scene)
    assert result == []


# ── has_shadow_region == True ─────────────────────────────────────────────────

def test_shadow_region_triggers_shadow_reduction(advisor):
    scene = {"has_shadow_region": True}
    result = advisor.generate_recommendations(scene)
    assert len(result) >= 1
    assert any("shadow" in r["suggestion"].lower() or
               "multi-angle" in r["suggestion"].lower() or
               "dome" in r["suggestion"].lower() for r in result)


def test_no_shadow_region_no_shadow_suggestion(advisor):
    scene = {"has_shadow_region": False}
    result = advisor.generate_recommendations(scene)
    assert result == []


# ── noise_level > 0.3 ─────────────────────────────────────────────────────────

def test_high_noise_triggers_intensity_suggestion(advisor):
    scene = {"noise_level": 0.5}
    result = advisor.generate_recommendations(scene)
    assert len(result) >= 1
    assert any(r["category"] == "intensity" for r in result)


def test_high_noise_recommendation_is_low_priority(advisor):
    scene = {"noise_level": 0.5}
    result = advisor.generate_recommendations(scene)
    intensity_recs = [r for r in result if r["category"] == "intensity"]
    assert all(r["priority"] == "low" for r in intensity_recs)


def test_noise_at_boundary_not_triggered(advisor):
    scene = {"noise_level": 0.3}
    result = advisor.generate_recommendations(scene)
    assert result == []


# ── Multiple issues simultaneously ───────────────────────────────────────────

def test_multiple_issues_returns_multiple_recommendations(advisor):
    scene = {
        "surface_type": "metal",
        "reflection_level": 0.8,
        "lighting_uniformity": 0.2,
        "noise_level": 0.5,
    }
    result = advisor.generate_recommendations(scene)
    assert len(result) >= 3


def test_all_issues_triggers_all_rules(advisor):
    scene = {
        "surface_type": "metal",
        "reflection_level": 0.9,
        "lighting_uniformity": 0.1,
        "illumination_type": "spot",
        "contrast": 0.1,
        "has_shadow_region": True,
        "noise_level": 0.8,
    }
    result = advisor.generate_recommendations(scene)
    assert len(result) == 7


# ── Recommendation structure validation ──────────────────────────────────────

def test_all_recommendations_have_required_keys(advisor):
    scene = {
        "surface_type": "metal",
        "reflection_level": 0.9,
        "lighting_uniformity": 0.1,
        "illumination_type": "spot",
        "contrast": 0.1,
        "has_shadow_region": True,
        "noise_level": 0.8,
    }
    result = advisor.generate_recommendations(scene)
    for rec in result:
        assert "category" in rec
        assert "suggestion" in rec
        assert "reason" in rec
        assert "priority" in rec
        assert rec["priority"] in ("high", "medium", "low")
        assert rec["category"] in (
            "light_type", "light_shape", "polarization",
            "color_filter", "intensity", "angle"
        )


def test_missing_fields_uses_safe_defaults(advisor):
    # Only surface_type provided — others default to safe values
    result = advisor.generate_recommendations({"surface_type": "metal"})
    assert any(r["category"] == "polarization" for r in result)
    # No high-reflection recommendation without reflection_level field
    assert not any("diffuse" in r["suggestion"].lower() for r in result)
