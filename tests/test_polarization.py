"""Tests for color lighting and polarization simulation (Step 46)."""
import numpy as np
import pytest

from light_test.polarization import (
    apply_color_lighting,
    apply_lens_polarization,
    apply_light_polarization,
    compute_histogram,
    is_grayscale_image,
)
from light_test.renderer import PBRRenderer


# ── helpers ───────────────────────────────────────────────────────────────────


def _gray_rendered(v: float = 0.5, h: int = 16, w: int = 16) -> np.ndarray:
    return np.full((h, w, 3), v, dtype=np.float32)


def _make_light(
    shape: str = "ring",
    intensity: float = 100.0,
    color: dict | None = None,
    polarizer_enabled: bool = False,
    polarizer_angle: float | None = None,
) -> dict:
    light: dict = {
        "id": "t",
        "shape": shape,
        "type": "led",
        "position": {"x": 0.0, "y": 0.0, "z": 300.0},
        "intensity": intensity,
        "color": color or {"r": 255, "g": 255, "b": 255},
        "polarizer": False,
        "pitch": 45.0,
        "lwd": 300.0,
    }
    if polarizer_enabled:
        light["polarizer_enabled"] = True
    if polarizer_angle is not None:
        light["polarizer_angle"] = polarizer_angle
    return light


def _make_pbr_image(h: int = 32, w: int = 32) -> np.ndarray:
    rng = np.random.default_rng(7)
    return rng.integers(50, 200, (h, w, 3), dtype=np.uint8)


def _make_depth(h: int = 32, w: int = 32) -> np.ndarray:
    base = np.linspace(0.3, 0.7, w)
    return np.tile(base, (h, 1)).astype(np.float32)


# ── apply_color_lighting ──────────────────────────────────────────────────────


def test_apply_color_lighting_white_lights_unchanged() -> None:
    """All-white lights must leave the image unchanged."""
    img = _gray_rendered(0.5)
    lights = [_make_light(color={"r": 255, "g": 255, "b": 255})]
    result = apply_color_lighting(img, lights)
    np.testing.assert_allclose(result, img, atol=1e-5)


def test_apply_color_lighting_red_tint() -> None:
    """A pure-red light must zero out G and B channels."""
    img = _gray_rendered(0.8)
    lights = [_make_light(color={"r": 255, "g": 0, "b": 0})]
    result = apply_color_lighting(img, lights)
    assert float(result[:, :, 0].mean()) > 0.5  # R preserved
    assert float(result[:, :, 1].max()) < 1e-5  # G → 0
    assert float(result[:, :, 2].max()) < 1e-5  # B → 0


def test_apply_color_lighting_multi_light_weighted() -> None:
    """Intensity-weighted average: red@100 + blue@100 = 50% R, 0 G, 50% B."""
    img = _gray_rendered(1.0)
    lights = [
        _make_light(intensity=100.0, color={"r": 255, "g": 0, "b": 0}),
        _make_light(intensity=100.0, color={"r": 0, "g": 0, "b": 255}),
    ]
    result = apply_color_lighting(img, lights)
    np.testing.assert_allclose(result[:, :, 0], 0.5, atol=1e-5)  # R = 0.5
    np.testing.assert_allclose(result[:, :, 1], 0.0, atol=1e-5)  # G = 0
    np.testing.assert_allclose(result[:, :, 2], 0.5, atol=1e-5)  # B = 0.5


def test_apply_color_lighting_no_lights_unchanged() -> None:
    img = _gray_rendered(0.4)
    result = apply_color_lighting(img, [])
    np.testing.assert_allclose(result, img, atol=1e-5)


def test_apply_color_lighting_output_clipped_to_01() -> None:
    img = np.ones((8, 8, 3), dtype=np.float32)
    lights = [_make_light(color={"r": 255, "g": 255, "b": 255})]
    result = apply_color_lighting(img, lights)
    assert float(result.max()) <= 1.0
    assert float(result.min()) >= 0.0


# ── is_grayscale_image ────────────────────────────────────────────────────────


def test_is_grayscale_true() -> None:
    """Image with identical RGB channels is grayscale."""
    val = np.full((8, 8), 128, dtype=np.uint8)
    img = np.stack([val, val, val], axis=-1)
    assert is_grayscale_image(img) is True


def test_is_grayscale_false() -> None:
    """Image with distinct channels is not grayscale."""
    img = np.zeros((8, 8, 3), dtype=np.uint8)
    img[:, :, 0] = 200
    img[:, :, 1] = 100
    img[:, :, 2] = 50
    assert is_grayscale_image(img) is False


def test_is_grayscale_2d() -> None:
    """2-D (H, W) array is always grayscale."""
    img = np.random.default_rng(0).integers(0, 255, (8, 8), dtype=np.uint8)
    assert is_grayscale_image(img) is True


def test_is_grayscale_float_channels_near_identical() -> None:
    v = np.full((8, 8), 0.5, dtype=np.float32)
    img = np.stack([v, v + 0.005, v - 0.005], axis=-1)  # diff < 0.01
    assert is_grayscale_image(img) is True


def test_is_grayscale_float_channels_different() -> None:
    v = np.full((8, 8), 0.5, dtype=np.float32)
    img = np.stack([v, v + 0.1, v], axis=-1)  # diff > 0.01
    assert is_grayscale_image(img) is False


# ── apply_light_polarization ──────────────────────────────────────────────────


def test_light_polarizer_disabled() -> None:
    """No polarizer → transmission 1.0."""
    light = _make_light(shape="ring")
    assert apply_light_polarization(light) == pytest.approx(1.0)


def test_light_polarizer_enabled() -> None:
    """Ideal linear polarizer → 50% transmission."""
    light = _make_light(shape="ring", polarizer_enabled=True)
    assert apply_light_polarization(light) == pytest.approx(0.5)


def test_light_polarizer_spot_angle_0() -> None:
    """Spot at 0° → cos²(0) = 1.0."""
    light = _make_light(shape="spot", polarizer_angle=0.0)
    assert apply_light_polarization(light) == pytest.approx(1.0, abs=1e-6)


def test_light_polarizer_spot_angle_90() -> None:
    """Spot at 90° → cos²(90°) ≈ 0."""
    light = _make_light(shape="spot", polarizer_angle=90.0)
    assert apply_light_polarization(light) == pytest.approx(0.0, abs=1e-6)


def test_light_polarizer_spot_no_angle_returns_1() -> None:
    """Spot with no polarizer_angle → no attenuation."""
    light = _make_light(shape="spot")
    assert apply_light_polarization(light) == pytest.approx(1.0)


def test_light_polarizer_shapes_enabled() -> None:
    """All non-spot shapes with polarizer_enabled return 0.5."""
    for shape in ("ring", "bar", "coaxial", "dome", "low_angle_ring"):
        light = _make_light(shape=shape, polarizer_enabled=True)
        assert apply_light_polarization(light) == pytest.approx(
            0.5
        ), f"Expected 0.5 for shape={shape}"


# ── apply_lens_polarization ───────────────────────────────────────────────────


def _make_spec_diff(h: int = 8, w: int = 8) -> tuple[np.ndarray, np.ndarray]:
    spec = np.full((h, w, 3), 0.4, dtype=np.float32)
    diff = np.full((h, w, 3), 0.3, dtype=np.float32)
    return spec, diff


def test_lens_polarization_metal_0deg() -> None:
    """At 0°, cos²(0) = 1 → specular fully passes, diffuse mildly reduced."""
    spec, diff = _make_spec_diff()
    result = apply_lens_polarization(spec, diff, 0.0, "metal")
    # specular: 0.4 * 1.0 = 0.4; diffuse: 0.3 * (0.5 + 0.5*1) = 0.3
    expected = spec * 1.0 + diff * 1.0
    np.testing.assert_allclose(result, expected, atol=1e-5)


def test_lens_polarization_metal_90deg() -> None:
    """At 90° for metal, specular → 0 (crossed polarizers)."""
    spec, diff = _make_spec_diff()
    result = apply_lens_polarization(spec, diff, 90.0, "metal")
    # specular: 0.4 * cos²(90°) ≈ 0; diffuse: 0.3 * 0.5
    np.testing.assert_allclose(result[:, :, 0], 0.3 * 0.5, atol=1e-5)


def test_lens_polarization_plastic_90deg() -> None:
    """Non-metallic at 90°: 30% specular residual remains."""
    spec, diff = _make_spec_diff()
    result = apply_lens_polarization(spec, diff, 90.0, "plastic")
    # specular: 0.4 * (0.3 + 0.7*0) = 0.4 * 0.3 = 0.12
    # diffuse: 0.3 * 0.5 = 0.15
    np.testing.assert_allclose(result[:, :, 0], 0.12 + 0.15, atol=1e-5)


def test_lens_polarization_diffuse_mild_reduction() -> None:
    """Diffuse only (specular=0) with 90° → half the original."""
    spec = np.zeros((8, 8, 3), dtype=np.float32)
    diff = np.full((8, 8, 3), 0.6, dtype=np.float32)
    result = apply_lens_polarization(spec, diff, 90.0, "plastic")
    np.testing.assert_allclose(result, diff * 0.5, atol=1e-5)


def test_lens_polarization_glass_90deg() -> None:
    """Glass (metallic category) at 90°: specular → 0."""
    spec, diff = _make_spec_diff()
    result = apply_lens_polarization(spec, diff, 90.0, "glass")
    # specular: 0.4 * 0 = 0; diffuse: 0.3 * 0.5
    np.testing.assert_allclose(result[:, :, 0], 0.3 * 0.5, atol=1e-5)


# ── compute_histogram ─────────────────────────────────────────────────────────


def test_histogram_rgb_image() -> None:
    """Color image returns 3 channels: R, G, B."""
    img = np.zeros((16, 16, 3), dtype=np.uint8)
    img[:, :, 0] = 100
    img[:, :, 1] = 150
    img[:, :, 2] = 200
    result = compute_histogram(img)
    assert result["is_grayscale"] is False
    names = [c["name"] for c in result["channels"]]
    assert names == ["R", "G", "B"]
    for ch in result["channels"]:
        assert len(ch["bins"]) == 256


def test_histogram_grayscale() -> None:
    """Grayscale image returns single luminance channel."""
    val = np.full((16, 16), 128, dtype=np.uint8)
    img = np.stack([val, val, val], axis=-1)
    result = compute_histogram(img)
    assert result["is_grayscale"] is True
    assert len(result["channels"]) == 1
    assert result["channels"][0]["name"] == "L"


def test_histogram_bins_sum_to_pixel_count() -> None:
    """Histogram bins should sum to total pixel count."""
    h, w = 20, 30
    img = np.random.default_rng(3).integers(0, 255, (h, w, 3), dtype=np.uint8)
    result = compute_histogram(img)
    for ch in result["channels"]:
        assert sum(ch["bins"]) == h * w


def test_histogram_float_image() -> None:
    """Float32 image in [0, 1] is accepted."""
    img = np.random.default_rng(5).random((16, 16, 3)).astype(np.float32)
    result = compute_histogram(img)
    assert len(result["channels"]) == 3


# ── renderer integration ──────────────────────────────────────────────────────


def _make_renderer_light() -> dict:
    return {
        "id": "r-light",
        "shape": "ring",
        "type": "led",
        "position": {"x": 0.0, "y": -200.0, "z": 400.0},
        "intensity": 80,
        "color": {"r": 255, "g": 255, "b": 255},
        "polarizer": False,
        "pitch": 45.0,
        "lwd": 300.0,
    }


def test_renderer_with_polarization() -> None:
    """Renderer accepts lens_polarizer_angle and returns valid uint8 output."""
    renderer = PBRRenderer()
    img = _make_pbr_image()
    depth = _make_depth()
    result = renderer.render(
        img, depth, [_make_renderer_light()], "metal", 32, 32, lens_polarizer_angle=45.0
    )
    assert result.shape == (32, 32, 3)
    assert result.dtype == np.uint8
    assert int(result.min()) >= 0
    assert int(result.max()) <= 255


def test_renderer_color_lighting() -> None:
    """Render with a red light produces a noticeably red-tinted output."""
    renderer = PBRRenderer()
    img = np.full((32, 32, 3), 128, dtype=np.uint8)
    depth = _make_depth()
    red_light = dict(_make_renderer_light())
    red_light["color"] = {"r": 255, "g": 0, "b": 0}
    result = renderer.render(img, depth, [red_light], "plastic", 32, 32)
    mean_r = float(result[:, :, 0].mean())
    mean_g = float(result[:, :, 1].mean())
    assert mean_r > mean_g, "Red-lit image should have R channel > G channel"


def test_renderer_crossed_lens_polarizer_dims_output() -> None:
    """90° crossed lens polarizer should produce darker output than 0°."""
    renderer = PBRRenderer()
    img = np.full((32, 32, 3), 128, dtype=np.uint8)
    depth = _make_depth()
    lights = [_make_renderer_light()]
    result_0 = renderer.render(img, depth, lights, "metal", 32, 32, lens_polarizer_angle=0.0)
    result_90 = renderer.render(img, depth, lights, "metal", 32, 32, lens_polarizer_angle=90.0)
    assert float(result_0.mean()) > float(result_90.mean())
