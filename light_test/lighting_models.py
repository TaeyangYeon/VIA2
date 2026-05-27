"""Light shape emission models for PBR rendering (Step 45)."""
import numpy as np

SPECTRAL_WEIGHTS: dict[str, float] = {
    "led": 1.0,      # neutral reference
    "halogen": 1.2,  # warm bias → higher perceived output
    "uv": 0.7,       # short wavelength → lower visual efficiency
    "ir": 0.8,       # long wavelength → lower visual efficiency
}


def _get_position(light: dict) -> np.ndarray:
    p = light["position"]
    return np.array([float(p["x"]), float(p["y"]), float(p["z"])], dtype=np.float64)


def _get_lwd(light: dict) -> float:
    return float(light.get("lwd") or 300.0)


def _spectral_weight(light: dict) -> float:
    return SPECTRAL_WEIGHTS.get(str(light.get("type", "led")), 1.0)


def _base_factors(light: dict, surface_point: np.ndarray) -> tuple[float, np.ndarray, float]:
    """Return (base_intensity, direction_from_light_to_surface, distance_mm)."""
    pos = _get_position(light)
    diff = surface_point.astype(np.float64) - pos
    dist = float(np.linalg.norm(diff))
    if dist < 1.0:
        dist = 1.0
    dir_to_surf = diff / dist
    lwd = _get_lwd(light)
    intensity = float(light["intensity"]) / 100.0
    atten = (lwd / dist) ** 2
    base = intensity * atten * _spectral_weight(light)
    return base, dir_to_surf, dist


def ring_emission(light: dict, surface_point: np.ndarray) -> float:
    """Uniform annular emission with inverse-square-law attenuation."""
    base, _, _ = _base_factors(light, surface_point)
    return max(0.0, base)


def bar_emission(light: dict, surface_point: np.ndarray) -> float:
    """Linear bar emission — find closest point on bar, apply attenuation."""
    pos = _get_position(light)
    size = light.get("size") or {"width": 100.0, "height": 10.0}
    bar_half = float(size.get("width", 100.0)) / 2.0

    # Bar extends ±bar_half along the X axis from its center
    offset_x = float(surface_point[0]) - pos[0]
    closest_x = float(np.clip(offset_x, -bar_half, bar_half))
    closest_point = np.array([pos[0] + closest_x, pos[1], pos[2]], dtype=np.float64)

    diff = surface_point.astype(np.float64) - closest_point
    dist = float(np.linalg.norm(diff))
    if dist < 1.0:
        dist = 1.0

    lwd = _get_lwd(light)
    intensity = float(light["intensity"]) / 100.0
    atten = (lwd / dist) ** 2
    return max(0.0, intensity * atten * _spectral_weight(light))


def spot_emission(light: dict, surface_point: np.ndarray) -> float:
    """Cone-shaped spot emission — falls to zero outside the pitch half-angle."""
    base, dir_to_surf, _ = _base_factors(light, surface_point)

    pos = _get_position(light)
    pos_norm = float(np.linalg.norm(pos))
    if pos_norm < 1e-6:
        main_dir = np.array([0.0, -1.0, 0.0])  # default: pointing down
    else:
        main_dir = -pos / pos_norm  # from light toward scene origin

    pitch = float(light.get("pitch") or 45.0)
    cone_cos = float(np.cos(np.radians(pitch)))

    cos_theta = float(np.dot(dir_to_surf, main_dir))
    if cos_theta < cone_cos:
        return 0.0

    denom = 1.0 - cone_cos
    factor = ((cos_theta - cone_cos) / denom) ** 2 if denom > 1e-6 else 1.0
    return max(0.0, base * factor)


def coaxial_emission(light: dict, surface_point: np.ndarray) -> float:
    """On-axis uniform emission — no angular dependency, pure inverse-square law."""
    base, _, _ = _base_factors(light, surface_point)
    return max(0.0, base)


def dome_emission(light: dict, surface_point: np.ndarray) -> float:
    """Hemispherical diffuse emission — always positive for surfaces below the dome."""
    base, _, _ = _base_factors(light, surface_point)
    return max(0.0, base * 0.5)


def low_angle_ring_emission(light: dict, surface_point: np.ndarray) -> float:
    """Grazing-angle ring emission — like ring but emphasises lateral incidence."""
    base, _, _ = _base_factors(light, surface_point)
    return max(0.0, base * 0.8)


def compute_emission(light: dict, surface_point: np.ndarray) -> float:
    """Dispatch to the appropriate shape emission function."""
    shape = str(light.get("shape", "ring"))
    dispatch = {
        "ring": ring_emission,
        "bar": bar_emission,
        "spot": spot_emission,
        "coaxial": coaxial_emission,
        "dome": dome_emission,
        "low_angle_ring": low_angle_ring_emission,
    }
    fn = dispatch.get(shape, ring_emission)
    return fn(light, surface_point)
