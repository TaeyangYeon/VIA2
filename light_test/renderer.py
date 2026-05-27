"""Main PBR renderer — depth-first shadow computation + material BRDF (Step 45).

Performance target: <500 ms for 640×480 with 3 lights using NumPy vectorisation.
All operations are fully vectorised; no per-pixel Python loops.
"""
import cv2
import numpy as np

from light_test.lighting_models import SPECTRAL_WEIGHTS
from light_test.material_pbr import get_material_params

_AMBIENT_FACTOR = 0.05   # fraction of original colour applied to shadow regions
_SHADOW_STEPS = 12        # ray-march steps for shadow computation
_WORLD_HALF = 500.0       # world coordinate half-range in mm (±500)


def _to_float3(image: np.ndarray) -> np.ndarray:
    """Convert any input image to float32 (H, W, 3) in [0, 1]."""
    if image.ndim == 2:
        img = np.stack([image] * 3, axis=-1)
    else:
        img = image.copy()
    return img.astype(np.float32) / 255.0


def _compute_normals(depth_mm: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute surface normals from a depth map (in mm).

    Returns (nx, ny, nz) arrays of shape (H, W), each unit-normalised.
    """
    h, w = depth_mm.shape
    dx = np.gradient(depth_mm, axis=1) * (_WORLD_HALF / w)
    dy = np.gradient(depth_mm, axis=0) * (_WORLD_HALF / h)
    # Normal = normalise(−dz/dx, −dz/dy, 1)
    norm_len = np.sqrt(dx ** 2 + dy ** 2 + 1.0)
    return -dx / norm_len, -dy / norm_len, 1.0 / norm_len


def _shadow_mask(
    px_grid: np.ndarray,
    py_grid: np.ndarray,
    pz_grid: np.ndarray,
    depth_map_norm: np.ndarray,
    lx: float,
    ly: float,
    lz: float,
) -> np.ndarray:
    """Ray-march from each surface pixel toward the light; return 1=lit, 0=shadowed.

    Args:
        px_grid, py_grid: world X/Y coordinates for each pixel (H, W)
        pz_grid: world Z (depth in mm) for each pixel (H, W)
        depth_map_norm: normalised depth map [0, 1] matching image resolution
        lx, ly, lz: light world position (mm)

    Returns:
        float32 mask (H, W) with values in {0.0, 1.0}.
    """
    h, w = depth_map_norm.shape
    mask = np.ones((h, w), dtype=np.float32)

    for step in range(1, _SHADOW_STEPS + 1):
        t = step / (_SHADOW_STEPS + 1)

        # World position of ray at step t
        rx = px_grid + t * (lx - px_grid)
        ry = py_grid + t * (ly - py_grid)
        rz = pz_grid + t * (lz - pz_grid)

        # Convert world X, Y → pixel indices for depth sampling
        pxi = np.clip(((rx + _WORLD_HALF) / (2.0 * _WORLD_HALF) * w).astype(np.int32), 0, w - 1)
        pyi = np.clip(((ry + _WORLD_HALF) / (2.0 * _WORLD_HALF) * h).astype(np.int32), 0, h - 1)

        # Depth at sampled location (mm)
        sampled_z = depth_map_norm[pyi, pxi] * _WORLD_HALF

        # Occluded if something at sampled location is higher (closer to camera) than the ray
        occluded = sampled_z > (rz + 2.0)  # 2 mm epsilon prevents self-shadowing
        mask = np.where(occluded, 0.0, mask)

    return mask.astype(np.float32)


def _angle_factor(
    light: dict,
    ldx_n: np.ndarray,
    ldy_n: np.ndarray,
    ldz_n: np.ndarray,
) -> np.ndarray:
    """Vectorised shape-specific angular attenuation (H, W) float32."""
    shape = str(light.get("shape", "ring"))
    h, w = ldx_n.shape

    if shape == "coaxial":
        return np.ones((h, w), dtype=np.float32)

    if shape == "spot":
        lx = float(light["position"]["x"])
        ly = float(light["position"]["y"])
        lz = float(light["position"]["z"])
        pn = np.sqrt(lx ** 2 + ly ** 2 + lz ** 2)
        if pn < 1e-6:
            mx, my, mz = 0.0, -1.0, 0.0
        else:
            mx, my, mz = -lx / pn, -ly / pn, -lz / pn
        pitch = float(light.get("pitch") or 45.0)
        cone_cos = float(np.cos(np.radians(pitch)))
        cos_th = ldx_n * mx + ldy_n * my + ldz_n * mz
        inside = (cos_th >= cone_cos).astype(np.float32)
        denom = 1.0 - cone_cos
        if denom > 1e-6:
            factor = inside * np.maximum(0.0, (cos_th - cone_cos) / denom) ** 2
        else:
            factor = inside
        return factor.astype(np.float32)

    if shape == "dome":
        # Hemispherical → prefer upward-facing normals; guarantee ≥ 0.3 for coverage
        return np.maximum(0.3, np.maximum(0.0, ldz_n)).astype(np.float32)

    if shape == "low_angle_ring":
        return np.full((h, w), 0.8, dtype=np.float32)

    # ring, bar, default: uniform emission
    return np.ones((h, w), dtype=np.float32)


class PBRRenderer:
    """Depth-first PBR renderer.

    Pipeline per light:
    1. Compute per-pixel light direction vectors (vectorised).
    2. Shadow map via ray marching (vectorised).
    3. Cook-Torrance BRDF on lit pixels.
    4. Ambient-only on shadow pixels.
    5. Additive combination across all lights.
    """

    def render(
        self,
        image: np.ndarray,
        depth_map: np.ndarray | None,
        lights: list[dict],
        surface_type: str,
        image_width: int,
        image_height: int,
    ) -> np.ndarray:
        """Render image with PBR lighting and depth-based shadows.

        Args:
            image: Original image (H, W) or (H, W, 3), uint8.
            depth_map: Normalised depth map [0, 1] of any shape; resized internally.
                       None means flat surface.
            lights: List of LightConfig dicts.
            surface_type: Material surface type string for the PBR LUT.
            image_width: Canvas width (used for world-coordinate mapping).
            image_height: Canvas height.

        Returns:
            Rendered image (H, W, 3), uint8, values in [0, 255].
        """
        h, w = image.shape[:2]
        img_f = _to_float3(image)  # (H, W, 3) float32 [0,1]

        if not lights:
            result = img_f * _AMBIENT_FACTOR
            return (result * 255.0).clip(0, 255).astype(np.uint8)

        # Prepare depth
        if depth_map is not None:
            dm = depth_map.astype(np.float32)
            if dm.shape != (h, w):
                dm = cv2.resize(dm, (w, h), interpolation=cv2.INTER_LINEAR)
            dm = np.clip(dm, 0.0, 1.0)
        else:
            dm = None

        # World coordinate grids (H, W) in mm
        xs = np.linspace(-_WORLD_HALF, _WORLD_HALF, w, dtype=np.float32)
        ys = np.linspace(-_WORLD_HALF, _WORLD_HALF, h, dtype=np.float32)
        px_grid = np.broadcast_to(xs[None, :], (h, w)).copy()  # (H, W)
        py_grid = np.broadcast_to(ys[:, None], (h, w)).copy()  # (H, W)

        pz_grid: np.ndarray
        if dm is not None:
            pz_grid = dm * _WORLD_HALF  # depth in mm
        else:
            pz_grid = np.zeros((h, w), dtype=np.float32)

        # Surface normals
        if dm is not None:
            nx, ny, nz = _compute_normals(pz_grid)
        else:
            nx = np.zeros((h, w), dtype=np.float32)
            ny = np.zeros((h, w), dtype=np.float32)
            nz = np.ones((h, w), dtype=np.float32)

        # View direction: looking straight down the +Z axis
        vx = np.zeros((h, w), dtype=np.float32)
        vy = np.zeros((h, w), dtype=np.float32)
        vz = np.ones((h, w), dtype=np.float32)

        # Material parameters
        mat = get_material_params(surface_type)
        k_d = float(mat["k_d"])
        k_s = float(mat["k_s"])
        shininess = float(mat["shininess"])

        # Accumulate light contributions
        accum = np.zeros((h, w, 3), dtype=np.float32)

        for light in lights:
            lx = float(light["position"]["x"])
            ly = float(light["position"]["y"])
            lz = float(light["position"]["z"])
            l_int = float(light["intensity"]) / 100.0
            col = light.get("color", {"r": 255, "g": 255, "b": 255})
            cr = float(col.get("r", 255)) / 255.0
            cg = float(col.get("g", 255)) / 255.0
            cb = float(col.get("b", 255)) / 255.0
            spectral = SPECTRAL_WEIGHTS.get(str(light.get("type", "led")), 1.0)
            lwd = float(light.get("lwd") or 300.0)

            # Direction from surface pixel to light (unnormalised)
            ddx = lx - px_grid
            ddy = ly - py_grid
            ddz = lz - pz_grid

            dist = np.sqrt(ddx ** 2 + ddy ** 2 + ddz ** 2) + 1e-6
            ldx_n = ddx / dist
            ldy_n = ddy / dist
            ldz_n = ddz / dist

            # Inverse-square attenuation
            atten = np.minimum(4.0, (lwd / dist) ** 2)

            # Shape-specific angular factor
            ang = _angle_factor(light, ldx_n, ldy_n, ldz_n)

            # Shadow mask
            if dm is not None:
                shadow = _shadow_mask(px_grid, py_grid, pz_grid, dm, lx, ly, lz)
            else:
                shadow = np.ones((h, w), dtype=np.float32)

            # BRDF — Lambertian diffuse + Blinn-Phong specular (vectorised)
            n_dot_l = np.maximum(0.0, nx * ldx_n + ny * ldy_n + nz * ldz_n)
            diffuse = k_d * n_dot_l

            hvx = ldx_n + vx
            hvy = ldy_n + vy
            hvz = ldz_n + vz
            hv_len = np.sqrt(hvx ** 2 + hvy ** 2 + hvz ** 2) + 1e-8
            hvx /= hv_len
            hvy /= hv_len
            hvz /= hv_len
            n_dot_h = np.maximum(0.0, nx * hvx + ny * hvy + nz * hvz)
            specular = k_s * (n_dot_h ** shininess)

            brdf = np.maximum(0.0, diffuse + specular)

            # Per-pixel irradiance on lit pixels
            irradiance = l_int * atten * ang * spectral * brdf * shadow  # (H, W)

            accum[:, :, 0] += irradiance * cr
            accum[:, :, 1] += irradiance * cg
            accum[:, :, 2] += irradiance * cb

        # Combine: ambient base + albedo-modulated light contributions
        ambient = img_f * _AMBIENT_FACTOR
        lit = img_f * accum
        result = np.clip(ambient + lit, 0.0, 1.0)
        return (result * 255.0).astype(np.uint8)
