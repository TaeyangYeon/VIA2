"""Material Look-Up Table for DINOv2-based material classification.

reference_features are 384-dim zero vectors (DINOv2-small output size).
They will be populated from real Colab DINOv2 outputs at Step 45.
"""

MATERIAL_LUT: dict = {
    "metal": {
        "reference_features": [0.0] * 384,
        "specular": 0.9,
        "diffuse": 0.3,
        "roughness": 0.1,
    },
    "plastic": {
        "reference_features": [0.0] * 384,
        "specular": 0.5,
        "diffuse": 0.6,
        "roughness": 0.3,
    },
    "glass": {
        "reference_features": [0.0] * 384,
        "specular": 0.95,
        "diffuse": 0.1,
        "roughness": 0.02,
    },
    "rubber": {
        "reference_features": [0.0] * 384,
        "specular": 0.1,
        "diffuse": 0.7,
        "roughness": 0.8,
    },
    "ceramic": {
        "reference_features": [0.0] * 384,
        "specular": 0.6,
        "diffuse": 0.5,
        "roughness": 0.2,
    },
    "wood": {
        "reference_features": [0.0] * 384,
        "specular": 0.15,
        "diffuse": 0.8,
        "roughness": 0.6,
    },
    "fabric": {
        "reference_features": [0.0] * 384,
        "specular": 0.05,
        "diffuse": 0.9,
        "roughness": 0.9,
    },
    "paper": {
        "reference_features": [0.0] * 384,
        "specular": 0.1,
        "diffuse": 0.85,
        "roughness": 0.7,
    },
}
