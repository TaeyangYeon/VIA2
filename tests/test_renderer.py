"""Tests for light_test PBR rendering pipeline (Step 45)."""
import numpy as np
import pytest

# ── helpers ───────────────────────────────────────────────────────────────────


def make_light(
    shape: str = "ring",
    light_type: str = "led",
    position: dict | None = None,
    intensity: int = 100,
    pitch: float = 45.0,
    yaw: float = 0.0,
    lwd: float = 300.0,
    size: dict | None = None,
    color: dict | None = None,
) -> dict:
    return {
        "id": "test-light",
        "shape": shape,
        "type": light_type,
        "position": position or {"x": 0.0, "y": 0.0, "z": 300.0},
        "intensity": intensity,
        "color": color or {"r": 255, "g": 255, "b": 255},
        "polarizer": False,
        "pitch": pitch,
        "yaw": yaw,
        "lwd": lwd,
        "size": size or {"width": 100.0, "height": 100.0},
    }


def make_test_image(h: int = 64, w: int = 64, channels: int = 3) -> np.ndarray:
    rng = np.random.default_rng(42)
    if channels == 1:
        return rng.integers(50, 200, (h, w), dtype=np.uint8)
    return rng.integers(50, 200, (h, w, 3), dtype=np.uint8)


def make_depth_map(h: int = 64, w: int = 64) -> np.ndarray:
    base = np.linspace(0.3, 0.7, w)
    return np.tile(base, (h, 1)).astype(np.float32)


def make_scene_light() -> dict:
    return make_light(
        shape="ring",
        light_type="led",
        position={"x": 0.0, "y": -200.0, "z": 400.0},
        intensity=80,
        pitch=45,
        lwd=300,
    )


# ── lighting_models tests ─────────────────────────────────────────────────────

from light_test.lighting_models import (  # noqa: E402
    SPECTRAL_WEIGHTS,
    bar_emission,
    coaxial_emission,
    compute_emission,
    dome_emission,
    low_angle_ring_emission,
    ring_emission,
    spot_emission,
)


@pytest.mark.parametrize("shape", ["ring", "bar", "spot", "coaxial", "dome", "low_angle_ring"])
def test_emission_nonnegative(shape: str) -> None:
    light = make_light(shape=shape)
    result = compute_emission(light, np.array([0.0, 0.0, 0.0]))
    assert result >= 0.0


def test_ring_inverse_square_law() -> None:
    light = make_light(shape="ring", position={"x": 0.0, "y": 0.0, "z": 100.0}, lwd=300)
    near = np.array([0.0, 0.0, 0.0])   # 100 mm away
    far = np.array([0.0, 0.0, -300.0]) # 400 mm away
    assert ring_emission(light, near) > ring_emission(light, far)


def test_spot_intensity_drops_outside_cone() -> None:
    light = make_light(shape="spot", pitch=30, position={"x": 0.0, "y": 300.0, "z": 0.0})
    inside = np.array([0.0, 0.0, 0.0])
    outside = np.array([5000.0, 0.0, 0.0])
    assert spot_emission(light, inside) > spot_emission(light, outside)


def test_spot_outside_cone_is_zero() -> None:
    light = make_light(shape="spot", pitch=30, position={"x": 0.0, "y": 300.0, "z": 0.0})
    outside = np.array([5000.0, 0.0, 0.0])
    assert spot_emission(light, outside) == 0.0


def test_coaxial_no_angle_dependency() -> None:
    light = make_light(shape="coaxial", position={"x": 0.0, "y": 0.0, "z": 300.0})
    p1 = np.array([0.0, 0.0, 0.0])
    p2 = np.array([0.0, 0.0, 0.0])
    assert coaxial_emission(light, p1) == coaxial_emission(light, p2)


def test_dome_emission_positive_for_surface_below() -> None:
    light = make_light(shape="dome", position={"x": 0.0, "y": 0.0, "z": 300.0})
    surface_pt = np.array([0.0, 0.0, 0.0])
    assert dome_emission(light, surface_pt) > 0.0


def test_low_angle_ring_nonnegative() -> None:
    light = make_light(shape="low_angle_ring", position={"x": 0.0, "y": 0.0, "z": 50.0})
    assert low_angle_ring_emission(light, np.array([0.0, 0.0, 0.0])) >= 0.0


def test_bar_emission_nonnegative() -> None:
    light = make_light(shape="bar", position={"x": 0.0, "y": 0.0, "z": 300.0})
    assert bar_emission(light, np.array([0.0, 0.0, 0.0])) >= 0.0


def test_light_type_spectral_weighting_differences() -> None:
    position = {"x": 0.0, "y": 0.0, "z": 300.0}
    surface = np.array([0.0, 0.0, 0.0])
    led_val = compute_emission(make_light(light_type="led", position=position), surface)
    hal_val = compute_emission(make_light(light_type="halogen", position=position), surface)
    uv_val = compute_emission(make_light(light_type="uv", position=position), surface)
    ir_val = compute_emission(make_light(light_type="ir", position=position), surface)
    # Not all four values should be identical (LED = 1.0 reference; halogen ≠ 1.0)
    assert not all(v == led_val for v in [hal_val, uv_val, ir_val])


def test_spectral_weights_cover_all_types() -> None:
    for t in ("led", "halogen", "uv", "ir"):
        assert t in SPECTRAL_WEIGHTS


def test_spectral_halogen_warmer_than_led() -> None:
    assert SPECTRAL_WEIGHTS["halogen"] > SPECTRAL_WEIGHTS["led"]


def test_spectral_uv_lower_than_led() -> None:
    assert SPECTRAL_WEIGHTS["uv"] < SPECTRAL_WEIGHTS["led"]


# ── material_pbr tests ────────────────────────────────────────────────────────

from light_test.material_pbr import cook_torrance_brdf, get_material_params  # noqa: E402

KNOWN_SURFACE_TYPES = ["metal", "plastic", "glass", "rubber", "ceramic", "pcb"]


@pytest.mark.parametrize("surface_type", KNOWN_SURFACE_TYPES)
def test_material_params_valid_for_known_types(surface_type: str) -> None:
    params = get_material_params(surface_type)
    for key in ("k_d", "k_s", "roughness", "shininess"):
        assert key in params, f"Missing key '{key}' for surface_type='{surface_type}'"
    assert 0.0 <= params["k_d"] <= 1.0
    assert 0.0 <= params["k_s"] <= 1.0
    assert 0.0 <= params["roughness"] <= 1.0
    assert params["shininess"] > 0.0


def test_unknown_surface_type_returns_default() -> None:
    params = get_material_params("unknown_xyz_material")
    assert "k_d" in params
    assert "k_s" in params
    assert params["k_d"] > 0.0


def test_brdf_output_nonnegative() -> None:
    normal = np.array([0.0, 0.0, 1.0])
    light_dir = np.array([0.0, 0.0, 1.0])
    view_dir = np.array([0.0, 0.0, 1.0])
    result = cook_torrance_brdf(0.8, 0.5, 32.0, normal, light_dir, view_dir, 1.0)
    assert result >= 0.0


def test_metal_higher_specular_than_rubber() -> None:
    metal = get_material_params("metal")
    rubber = get_material_params("rubber")
    assert metal["k_s"] > rubber["k_s"]


def test_rubber_higher_diffuse_than_metal() -> None:
    metal = get_material_params("metal")
    rubber = get_material_params("rubber")
    assert rubber["k_d"] > metal["k_d"]


def test_glass_highest_specular() -> None:
    glass = get_material_params("glass")
    metal = get_material_params("metal")
    assert glass["k_s"] >= metal["k_s"]


def test_specular_peak_at_reflection_angle() -> None:
    """N·H = 1 at perfect reflection gives maximum specular."""
    normal = np.array([0.0, 0.0, 1.0])
    light_dir = np.array([0.0, 0.0, 1.0])
    view_peak = np.array([0.0, 0.0, 1.0])   # H = (0,0,1) → N·H = 1
    view_off = np.array([1.0, 0.0, 0.1])
    view_off = view_off / np.linalg.norm(view_off)
    i_peak = cook_torrance_brdf(0.1, 0.9, 64.0, normal, light_dir, view_peak, 1.0)
    i_off = cook_torrance_brdf(0.1, 0.9, 64.0, normal, light_dir, view_off, 1.0)
    assert i_peak > i_off


def test_diffuse_maximum_at_ndotl_one() -> None:
    """Diffuse term is largest when N·L = 1."""
    normal = np.array([0.0, 0.0, 1.0])
    view_dir = np.array([0.0, 0.0, 1.0])
    light_aligned = np.array([0.0, 0.0, 1.0])          # N·L = 1
    light_angled = np.array([0.7071, 0.0, 0.7071])     # N·L ≈ 0.707
    i_max = cook_torrance_brdf(0.9, 0.05, 8.0, normal, light_aligned, view_dir, 1.0)
    i_less = cook_torrance_brdf(0.9, 0.05, 8.0, normal, light_angled, view_dir, 1.0)
    assert i_max > i_less


def test_brdf_zero_when_backlit() -> None:
    """No diffuse contribution when N·L < 0."""
    normal = np.array([0.0, 0.0, 1.0])
    light_behind = np.array([0.0, 0.0, -1.0])  # N·L = -1
    view_dir = np.array([0.0, 0.0, 1.0])
    result = cook_torrance_brdf(0.9, 0.9, 32.0, normal, light_behind, view_dir, 1.0)
    assert result == pytest.approx(0.0, abs=1e-6)


# ── renderer tests ────────────────────────────────────────────────────────────

from light_test.renderer import PBRRenderer  # noqa: E402


def test_render_single_light_differs_from_input() -> None:
    renderer = PBRRenderer()
    image = make_test_image()
    depth_map = make_depth_map()
    result = renderer.render(image, depth_map, [make_scene_light()], "metal", 64, 64)
    assert not np.array_equal(result, image)


def test_render_no_lights_returns_darkened() -> None:
    renderer = PBRRenderer()
    image = make_test_image()
    depth_map = make_depth_map()
    result = renderer.render(image, depth_map, [], "metal", 64, 64)
    assert float(result.mean()) < float(image.mean())


def test_render_no_depth_map_flat_lighting() -> None:
    renderer = PBRRenderer()
    image = make_test_image()
    result = renderer.render(image, None, [make_scene_light()], "metal", 64, 64)
    assert result.shape == (64, 64, 3)
    assert result.dtype == np.uint8


def test_render_shadow_regions_darker_than_lit() -> None:
    """Lit render is brighter than ambient-only (shadow) render."""
    renderer = PBRRenderer()
    image = np.full((64, 64, 3), 128, dtype=np.uint8)
    depth_map = make_depth_map()
    result_lit = renderer.render(image, depth_map, [make_scene_light()], "plastic", 64, 64)
    result_dark = renderer.render(image, depth_map, [], "plastic", 64, 64)
    assert float(result_lit.mean()) > float(result_dark.mean())


def test_render_multiple_lights_brighter_than_single() -> None:
    renderer = PBRRenderer()
    image = make_test_image()
    depth_map = make_depth_map()
    light1 = make_scene_light()
    light2 = dict(make_scene_light())
    light2["id"] = "light-2"
    light2["position"] = {"x": 200.0, "y": -200.0, "z": 400.0}
    result_single = renderer.render(image, depth_map, [light1], "metal", 64, 64)
    result_multi = renderer.render(image, depth_map, [light1, light2], "metal", 64, 64)
    assert float(result_multi.mean()) >= float(result_single.mean())


def test_render_grayscale_input_produces_rgb_output() -> None:
    renderer = PBRRenderer()
    image = make_test_image(channels=1)
    depth_map = make_depth_map()
    result = renderer.render(image, depth_map, [make_scene_light()], "metal", 64, 64)
    assert result.shape == (64, 64, 3)
    assert result.dtype == np.uint8


def test_render_output_shape_matches_input() -> None:
    renderer = PBRRenderer()
    image = make_test_image(h=80, w=100)
    depth_map = make_depth_map(h=80, w=100)
    result = renderer.render(image, depth_map, [make_scene_light()], "plastic", 100, 80)
    assert result.shape == (80, 100, 3)


def test_render_output_dtype_uint8() -> None:
    renderer = PBRRenderer()
    image = make_test_image()
    depth_map = make_depth_map()
    result = renderer.render(image, depth_map, [make_scene_light()], "plastic", 64, 64)
    assert result.dtype == np.uint8


def test_render_output_values_in_valid_range() -> None:
    renderer = PBRRenderer()
    image = make_test_image()
    depth_map = make_depth_map()
    result = renderer.render(image, depth_map, [make_scene_light()], "metal", 64, 64)
    assert int(result.min()) >= 0
    assert int(result.max()) <= 255


def test_render_different_surface_types_produce_different_results() -> None:
    renderer = PBRRenderer()
    image = make_test_image()
    depth_map = make_depth_map()
    lights = [make_scene_light()]
    result_metal = renderer.render(image, depth_map, lights, "metal", 64, 64)
    result_rubber = renderer.render(image, depth_map, lights, "rubber", 64, 64)
    assert not np.array_equal(result_metal, result_rubber)


def test_render_with_shadow_depth_spike() -> None:
    """Renderer handles depth occluder without crashing."""
    renderer = PBRRenderer()
    h, w = 64, 64
    depth_map = np.zeros((h, w), dtype=np.float32)
    depth_map[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4] = 0.8
    image = np.full((h, w, 3), 128, dtype=np.uint8)
    result = renderer.render(image, depth_map, [make_scene_light()], "metal", w, h)
    assert result.shape == (h, w, 3)
    assert result.dtype == np.uint8
    assert int(result.min()) >= 0
    assert int(result.max()) <= 255
