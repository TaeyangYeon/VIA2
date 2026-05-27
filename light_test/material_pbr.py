"""Material PBR parameters and Cook-Torrance BRDF (Step 45).

LUT values follow academic references for machine-vision surface categories.
"""
import numpy as np

# Academic LUT: surface_type → PBR parameters
_MATERIAL_LUT: dict[str, dict] = {
    "metal":   {"k_d": 0.20, "k_s": 0.875, "roughness": 0.30, "shininess": 64.0},
    "plastic": {"k_d": 0.70, "k_s": 0.400, "roughness": 0.30, "shininess": 32.0},
    "glass":   {"k_d": 0.075,"k_s": 0.950, "roughness": 0.05, "shininess": 128.0},
    "rubber":  {"k_d": 0.875,"k_s": 0.035, "roughness": 0.90, "shininess": 4.0},
    "ceramic": {"k_d": 0.60, "k_s": 0.350, "roughness": 0.40, "shininess": 24.0},
    "pcb":     {"k_d": 0.70, "k_s": 0.150, "roughness": 0.50, "shininess": 16.0},
    "default": {"k_d": 0.50, "k_s": 0.300, "roughness": 0.50, "shininess": 16.0},
}


def get_material_params(surface_type: str) -> dict:
    """Return a copy of PBR parameters for the given surface type.

    Falls back to 'default' for unknown types.
    """
    return _MATERIAL_LUT.get(surface_type, _MATERIAL_LUT["default"]).copy()


def cook_torrance_brdf(
    k_d: float,
    k_s: float,
    shininess: float,
    normal: np.ndarray,
    light_dir: np.ndarray,
    view_dir: np.ndarray,
    intensity: float,
) -> float:
    """Simplified Cook-Torrance BRDF (Lambertian diffuse + Blinn-Phong specular).

    Args:
        k_d: diffuse coefficient [0, 1]
        k_s: specular coefficient [0, 1]
        shininess: Phong shininess exponent
        normal: surface normal (need not be unit length)
        light_dir: direction *toward* the light source
        view_dir: direction *toward* the viewer
        intensity: incident light intensity scalar

    Returns:
        Combined pixel intensity (non-negative).
    """
    n = normal / (np.linalg.norm(normal) + 1e-8)
    l = light_dir / (np.linalg.norm(light_dir) + 1e-8)
    v = view_dir / (np.linalg.norm(view_dir) + 1e-8)

    n_dot_l = max(0.0, float(np.dot(n, l)))

    # Lambertian diffuse
    diffuse = k_d * n_dot_l

    # Blinn-Phong specular via half-vector
    h = l + v
    h_len = np.linalg.norm(h)
    if h_len < 1e-8 or n_dot_l == 0.0:
        specular = 0.0
    else:
        h = h / h_len
        n_dot_h = max(0.0, float(np.dot(n, h)))
        specular = k_s * (n_dot_h ** shininess)

    return intensity * max(0.0, diffuse + specular)
