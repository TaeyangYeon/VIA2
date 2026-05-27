"""Color lighting and polarization simulation (Step 46)."""
import numpy as np


def apply_color_lighting(rendered: np.ndarray, lights: list[dict]) -> np.ndarray:
    """Multiply rendered image by intensity-weighted average light color.

    White lights (255,255,255) leave the image unchanged.
    """
    if not lights:
        return rendered.copy()

    total_weight = 0.0
    wr, wg, wb = 0.0, 0.0, 0.0

    for light in lights:
        intensity = float(light.get("intensity", 100.0))
        col = light.get("color", {"r": 255, "g": 255, "b": 255})
        r = float(col.get("r", 255)) / 255.0
        g = float(col.get("g", 255)) / 255.0
        b = float(col.get("b", 255)) / 255.0
        wr += r * intensity
        wg += g * intensity
        wb += b * intensity
        total_weight += intensity

    if total_weight < 1e-8:
        return rendered.copy()

    cr = wr / total_weight
    cg = wg / total_weight
    cb = wb / total_weight

    result = rendered.copy().astype(np.float32)
    result[:, :, 0] *= cr
    result[:, :, 1] *= cg
    result[:, :, 2] *= cb

    return np.clip(result, 0.0, 1.0).astype(np.float32)


def is_grayscale_image(image: np.ndarray) -> bool:
    """Return True if image is effectively grayscale (all channels near-identical)."""
    if image.ndim == 2:
        return True
    if image.ndim == 3 and image.shape[2] == 3:
        if image.dtype == np.uint8:
            threshold = 0.01 * 255.0
        else:
            threshold = 0.01
        ch0 = image[:, :, 0].astype(np.float32)
        ch1 = image[:, :, 1].astype(np.float32)
        ch2 = image[:, :, 2].astype(np.float32)
        return bool(
            float(np.max(np.abs(ch0 - ch1))) <= threshold
            and float(np.max(np.abs(ch0 - ch2))) <= threshold
        )
    return False


def apply_light_polarization(light: dict) -> float:
    """Return polarization transmission factor for a single light.

    - spot shape: uses polarizer_angle (degrees) → cos²(θ) per Malus's law
    - other shapes: polarizer_enabled True → 0.5; False → 1.0
    """
    shape = str(light.get("shape", "ring"))

    if shape == "spot":
        if "polarizer_angle" not in light:
            return 1.0
        angle_deg = float(light["polarizer_angle"])
        angle_rad = float(np.radians(angle_deg))
        return float(np.cos(angle_rad) ** 2)

    if light.get("polarizer_enabled", False):
        return 0.5
    return 1.0


def apply_lens_polarization(
    specular_component: np.ndarray,
    diffuse_component: np.ndarray,
    lens_angle_deg: float,
    surface_type: str,
) -> np.ndarray:
    """Apply Malus's law for the lens-side analyzer.

    Metal/glass: specular is linearly polarized → full cos²(θ) attenuation.
    Other materials: 30% unpolarized residual → 0.3 + 0.7·cos²(θ).
    Diffuse: always unpolarized → 0.5 + 0.5·cos²(θ).
    """
    angle_rad = float(np.radians(lens_angle_deg))
    cos2 = float(np.cos(angle_rad) ** 2)

    if surface_type in ("metal", "glass"):
        attenuated_specular = specular_component * cos2
    else:
        attenuated_specular = specular_component * (0.3 + 0.7 * cos2)

    attenuated_diffuse = diffuse_component * (0.5 + 0.5 * cos2)
    return (attenuated_specular + attenuated_diffuse).astype(np.float32)


def compute_histogram(image: np.ndarray) -> dict:
    """Compute per-channel histogram with 256 bins.

    Returns {"channels": [{"name": ..., "bins": [...]}], "is_grayscale": bool}.
    """
    is_gray = is_grayscale_image(image)

    if image.dtype in (np.float32, np.float64):
        img_u8 = (np.clip(image, 0.0, 1.0) * 255.0).astype(np.uint8)
    else:
        img_u8 = image.astype(np.uint8)

    if is_gray:
        lum = img_u8[:, :, 0] if img_u8.ndim == 3 else img_u8
        hist, _ = np.histogram(lum.ravel(), bins=256, range=(0, 255))
        channels = [{"name": "L", "bins": hist.tolist()}]
    else:
        channels = []
        for i, name in enumerate(("R", "G", "B")):
            hist, _ = np.histogram(img_u8[:, :, i].ravel(), bins=256, range=(0, 255))
            channels.append({"name": name, "bins": hist.tolist()})

    return {"channels": channels, "is_grayscale": is_gray}
