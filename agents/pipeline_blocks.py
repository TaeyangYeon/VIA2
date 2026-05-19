"""Pipeline Block Library — rule-based block definitions for image processing."""
from dataclasses import dataclass
from typing import Callable

from agents.models import ImageDiagnosis


@dataclass
class BlockDefinition:
    name: str
    category: str
    when: Callable[[ImageDiagnosis], bool]
    params: dict
    description: str


def _always_true(_: ImageDiagnosis) -> bool:
    return True


BLOCK_REGISTRY: dict[str, "BlockDefinition"] = {b.name: b for b in [
    # ── color_space ───────────────────────────────────────────────────────────
    BlockDefinition(
        name="grayscale",
        category="color_space",
        when=_always_true,
        params={},
        description="기본 그레이스케일 변환",
    ),
    BlockDefinition(
        name="hsv_s",
        category="color_space",
        when=lambda d: d.color_discriminability > 0.3,
        params={},
        description="HSV 채도(S) 채널 — 색상 구분성 높을 때 적합",
    ),
    BlockDefinition(
        name="hsv_v",
        category="color_space",
        when=lambda d: d.color_discriminability > 0.2,
        params={},
        description="HSV 명도(V) 채널 — 색상 정보 활용",
    ),
    BlockDefinition(
        name="lab_l",
        category="color_space",
        when=lambda d: d.lighting_uniformity > 0.3,
        params={},
        description="LAB 밝기(L) 채널 — 불균일 조명에 강인",
    ),
    BlockDefinition(
        name="ycrcb_cr",
        category="color_space",
        when=lambda d: d.color_discriminability > 0.4 and d.dominant_channel_ratio < 0.5,
        params={},
        description="YCrCb Cr 채널 — 색상 구분성 높고 채널 편중 낮을 때",
    ),
    # ── denoise ───────────────────────────────────────────────────────────────
    BlockDefinition(
        name="gaussian_fine",
        category="denoise",
        when=lambda d: d.noise_level > 5.0,
        params={"kernel_size": [3, 5], "sigma": [0.5, 1.0]},
        description="가우시안 미세 스무딩 — 약한 노이즈 제거",
    ),
    BlockDefinition(
        name="gaussian_mid",
        category="denoise",
        when=lambda d: d.noise_level > 15.0,
        params={"kernel_size": [5, 7, 9], "sigma": [1.0, 1.5, 2.0]},
        description="가우시안 중간 스무딩 — 중간 노이즈 제거",
    ),
    BlockDefinition(
        name="bilateral",
        category="denoise",
        when=lambda d: d.noise_level > 10.0 and d.edge_sharpness > 0.1,
        params={"d": [5, 7, 9], "sigma_color": [50, 75, 100], "sigma_space": [50, 75, 100]},
        description="양방향 필터 — 엣지 보존하며 노이즈 제거",
    ),
    BlockDefinition(
        name="median",
        category="denoise",
        when=lambda d: d.noise_level > 20.0,
        params={"kernel_size": [3, 5, 7]},
        description="미디언 필터 — 솔트앤페퍼 노이즈 제거",
    ),
    BlockDefinition(
        name="nlmeans",
        category="denoise",
        when=lambda d: d.noise_level > 30.0,
        params={"h": [5, 10, 15], "template_window_size": [7], "search_window_size": [21]},
        description="Non-local Means — 강한 노이즈 제거",
    ),
    BlockDefinition(
        name="clahe",
        category="denoise",
        when=lambda d: d.lighting_uniformity > 0.25,
        params={"clip_limit": [1.0, 2.0, 3.0, 4.0], "tile_grid_size": [(8, 8), (16, 16)]},
        description="CLAHE — 불균일 조명 대비 향상",
    ),
    # ── threshold ─────────────────────────────────────────────────────────────
    BlockDefinition(
        name="otsu",
        category="threshold",
        when=lambda d: d.contrast > 0.15,
        params={},
        description="Otsu 이진화 — 높은 대비에 적합",
    ),
    BlockDefinition(
        name="adaptive_mean",
        category="threshold",
        when=lambda d: d.lighting_uniformity > 0.2,
        params={"block_size": [7, 11, 15, 21], "c": [2, 5, 10]},
        description="적응형 평균 이진화 — 불균일 조명 대응",
    ),
    BlockDefinition(
        name="adaptive_gauss",
        category="threshold",
        when=lambda d: d.lighting_uniformity > 0.2 and d.noise_level > 10.0,
        params={"block_size": [7, 11, 15, 21], "c": [2, 5, 10]},
        description="적응형 가우시안 이진화 — 불균일 조명 + 노이즈 동시 대응",
    ),
    BlockDefinition(
        name="dynamic_threshold",
        category="threshold",
        when=lambda d: d.contrast < 0.15,
        params={"offset": [-10, -5, 0, 5, 10]},
        description="동적 임계값 — 낮은 대비 보정",
    ),
    # ── morphology ────────────────────────────────────────────────────────────
    BlockDefinition(
        name="erosion",
        category="morphology",
        when=lambda d: d.edge_density > 0.1,
        params={"kernel_size": [3, 5, 7], "iterations": [1, 2]},
        description="침식 — 밝은 노이즈 및 얇은 돌출 제거",
    ),
    BlockDefinition(
        name="dilation",
        category="morphology",
        when=lambda d: d.edge_density > 0.05,
        params={"kernel_size": [3, 5, 7], "iterations": [1, 2]},
        description="팽창 — 어두운 노이즈 및 얇은 구멍 채움",
    ),
    BlockDefinition(
        name="opening",
        category="morphology",
        when=lambda d: d.noise_level > 10.0,
        params={"kernel_size": [3, 5, 7]},
        description="열림 — 작은 전경 노이즈 제거",
    ),
    BlockDefinition(
        name="closing",
        category="morphology",
        when=lambda d: d.edge_density > 0.05,
        params={"kernel_size": [3, 5, 7]},
        description="닫힘 — 작은 구멍 및 균열 채움",
    ),
    BlockDefinition(
        name="tophat",
        category="morphology",
        when=lambda d: d.lighting_uniformity > 0.3,
        params={"kernel_size": [5, 9, 15, 21]},
        description="탑햇 변환 — 밝은 세부 구조 추출",
    ),
    BlockDefinition(
        name="blackhat",
        category="morphology",
        when=lambda d: d.lighting_uniformity > 0.3,
        params={"kernel_size": [5, 9, 15, 21]},
        description="블랙햇 변환 — 어두운 세부 구조 추출",
    ),
    BlockDefinition(
        name="morph_gradient",
        category="morphology",
        when=lambda d: d.edge_density > 0.1,
        params={"kernel_size": [3, 5]},
        description="모폴로지 그래디언트 — 윤곽 강조",
    ),
    # ── edge ──────────────────────────────────────────────────────────────────
    BlockDefinition(
        name="canny",
        category="edge",
        when=lambda d: d.edge_sharpness > 0.05,
        params={"low_threshold": [30, 50, 80], "high_threshold": [100, 150, 200]},
        description="Canny 엣지 — 날카로운 엣지 검출",
    ),
    BlockDefinition(
        name="sobel",
        category="edge",
        when=lambda d: d.edge_sharpness > 0.03,
        params={"ksize": [3, 5]},
        description="Sobel 엣지 — 방향성 그래디언트 검출",
    ),
    BlockDefinition(
        name="laplacian",
        category="edge",
        when=lambda d: d.noise_level < 15.0 and d.edge_sharpness > 0.05,
        params={"ksize": [3, 5]},
        description="Laplacian 엣지 — 낮은 노이즈 환경의 엣지 검출",
    ),
    BlockDefinition(
        name="scharr",
        category="edge",
        when=lambda d: d.edge_sharpness > 0.03,
        params={},
        description="Scharr 엣지 — 고정밀 방향 그래디언트",
    ),
]}


def get_matching_blocks(
    diagnosis: ImageDiagnosis,
    category: str | None = None,
) -> list[BlockDefinition]:
    """Return blocks whose when() is True; optionally filter by category."""
    blocks = [b for b in BLOCK_REGISTRY.values() if b.when(diagnosis)]
    if category is not None:
        blocks = [b for b in blocks if b.category == category]
    return blocks


def get_block(name: str) -> BlockDefinition | None:
    """Look up a block by name; returns None if not found."""
    return BLOCK_REGISTRY.get(name)


def get_all_blocks() -> list[BlockDefinition]:
    """Return all registered blocks."""
    return list(BLOCK_REGISTRY.values())


def get_blocks_by_category(category: str) -> list[BlockDefinition]:
    """Return all blocks in the given category."""
    return [b for b in BLOCK_REGISTRY.values() if b.category == category]
