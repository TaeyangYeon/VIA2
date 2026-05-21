"""Tests for ParameterSheetGenerator — TDD Red phase."""
import pytest
from dataclasses import asdict

from agents.models import (
    Blueprint,
    BlueprintEdge,
    BlueprintNode,
    InspectionItem,
    InspectionPlan,
    PipelineBlock,
    ProcessingPipeline,
)
from agents.parameter_sheet import (
    ParameterEntry,
    NodeParameterSheet,
    ParameterSheetGenerator,
)


# ── helpers ─────────────────────────────────────────────────────────────────

def _pre_node(block_id: str, block_type: str, params: dict = None) -> BlueprintNode:
    return BlueprintNode(
        node_id=f"pre_{block_id}",
        node_type="preprocessing",
        label=block_type,
        params=params or {},
    )


def _feat_node(block_id: str, block_type: str, params: dict = None) -> BlueprintNode:
    return BlueprintNode(
        node_id=f"feat_{block_id}",
        node_type="feature",
        label=block_type,
        params=params or {},
    )


def _insp_node(item_id: int, name: str, category: str) -> BlueprintNode:
    return BlueprintNode(
        node_id=f"insp_{item_id}",
        node_type="inspection",
        label=name,
        params={"category": category},
    )


def _decision_node() -> BlueprintNode:
    return BlueprintNode(
        node_id="decision",
        node_type="decision",
        label="Pass / Fail",
        params={},
    )


def _simple_blueprint() -> Blueprint:
    nodes = [
        _pre_node("b1", "grayscale"),
        _feat_node("b2", "otsu"),
        _insp_node(1, "Hole Detection", "blob"),
        _decision_node(),
    ]
    return Blueprint(nodes=nodes, edges=[])


def _simple_pipeline() -> ProcessingPipeline:
    return ProcessingPipeline(
        pipeline_id="pipe-001",
        blocks=[
            PipelineBlock(block_id="b1", block_type="grayscale", params={}),
            PipelineBlock(block_id="b2", block_type="otsu", params={}),
        ],
    )


def _simple_plan() -> InspectionPlan:
    return InspectionPlan(
        items=[InspectionItem(item_id=1, name="Hole Detection", category="blob")],
        inspection_purpose="불량 검출",
    )


# ── ParameterEntry dataclass ─────────────────────────────────────────────────

def test_parameter_entry_creation():
    entry = ParameterEntry(
        name="kernel_size",
        value=5,
        mathematical_description="5×5 가우시안 커널",
    )
    assert entry.name == "kernel_size"
    assert entry.value == 5
    assert entry.mathematical_description == "5×5 가우시안 커널"


def test_parameter_entry_default_unit_is_none():
    entry = ParameterEntry(name="threshold", value=127, mathematical_description="고정 임계값")
    assert entry.unit is None


def test_parameter_entry_with_unit():
    entry = ParameterEntry(name="sigma", value=1.5, mathematical_description="σ=1.5", unit="px")
    assert entry.unit == "px"


def test_parameter_entry_value_can_be_float():
    entry = ParameterEntry(name="clip_limit", value=2.0, mathematical_description="CLAHE 계수 2.0")
    assert entry.value == 2.0


def test_parameter_entry_value_can_be_tuple():
    entry = ParameterEntry(name="tile_grid_size", value=(8, 8), mathematical_description="8×8 타일")
    assert entry.value == (8, 8)


# ── NodeParameterSheet dataclass ─────────────────────────────────────────────

def test_node_parameter_sheet_creation():
    sheet = NodeParameterSheet(
        node_id="pre_b1",
        node_name="grayscale",
        node_type="preprocessing",
        parameters=[],
        algorithm_summary="RGB→그레이스케일 단일 채널 변환",
    )
    assert sheet.node_id == "pre_b1"
    assert sheet.node_name == "grayscale"
    assert sheet.node_type == "preprocessing"
    assert sheet.parameters == []
    assert "그레이스케일" in sheet.algorithm_summary


def test_node_parameter_sheet_with_parameters():
    params = [
        ParameterEntry(name="kernel_size", value=5, mathematical_description="5×5 커널"),
    ]
    sheet = NodeParameterSheet(
        node_id="feat_b1",
        node_name="gaussian_fine",
        node_type="preprocessing",
        parameters=params,
        algorithm_summary="가우시안 필터",
    )
    assert len(sheet.parameters) == 1
    assert sheet.parameters[0].name == "kernel_size"


def test_node_parameter_sheet_to_dict_returns_dict():
    sheet = NodeParameterSheet(
        node_id="pre_b1",
        node_name="grayscale",
        node_type="preprocessing",
        parameters=[],
        algorithm_summary="그레이스케일",
    )
    result = sheet.to_dict()
    assert isinstance(result, dict)


def test_node_parameter_sheet_to_dict_has_all_keys():
    sheet = NodeParameterSheet(
        node_id="pre_b1",
        node_name="grayscale",
        node_type="preprocessing",
        parameters=[],
        algorithm_summary="그레이스케일",
    )
    d = sheet.to_dict()
    assert "node_id" in d
    assert "node_name" in d
    assert "node_type" in d
    assert "parameters" in d
    assert "algorithm_summary" in d


def test_node_parameter_sheet_to_dict_parameters_is_list_of_dicts():
    entry = ParameterEntry(name="k", value=3, mathematical_description="3×3 커널")
    sheet = NodeParameterSheet(
        node_id="feat_b1",
        node_name="otsu",
        node_type="feature",
        parameters=[entry],
        algorithm_summary="오츠 이진화",
    )
    d = sheet.to_dict()
    assert isinstance(d["parameters"], list)
    assert isinstance(d["parameters"][0], dict)
    assert d["parameters"][0]["name"] == "k"


def test_node_parameter_sheet_to_dict_values_match():
    sheet = NodeParameterSheet(
        node_id="pre_b1",
        node_name="grayscale",
        node_type="preprocessing",
        parameters=[],
        algorithm_summary="그레이스케일",
    )
    d = sheet.to_dict()
    assert d["node_id"] == "pre_b1"
    assert d["node_name"] == "grayscale"
    assert d["node_type"] == "preprocessing"
    assert d["algorithm_summary"] == "그레이스케일"


# ── ParameterSheetGenerator — basic interface ────────────────────────────────

def test_generator_instantiation():
    gen = ParameterSheetGenerator()
    assert gen is not None


def test_generator_has_generate_method():
    gen = ParameterSheetGenerator()
    assert callable(gen.generate)


def test_generate_returns_list():
    gen = ParameterSheetGenerator()
    result = gen.generate(_simple_blueprint(), _simple_pipeline(), _simple_plan())
    assert isinstance(result, list)


def test_generate_returns_list_of_node_parameter_sheets():
    gen = ParameterSheetGenerator()
    result = gen.generate(_simple_blueprint(), _simple_pipeline(), _simple_plan())
    for item in result:
        assert isinstance(item, NodeParameterSheet)


def test_generate_count_matches_blueprint_node_count():
    gen = ParameterSheetGenerator()
    bp = _simple_blueprint()
    result = gen.generate(bp, _simple_pipeline(), _simple_plan())
    assert len(result) == len(bp.nodes)


def test_generate_node_ids_match_blueprint():
    gen = ParameterSheetGenerator()
    bp = _simple_blueprint()
    result = gen.generate(bp, _simple_pipeline(), _simple_plan())
    result_ids = {s.node_id for s in result}
    blueprint_ids = {n.node_id for n in bp.nodes}
    assert result_ids == blueprint_ids


# ── Preprocessing nodes — color space ───────────────────────────────────────

def test_grayscale_node_type_is_preprocessing():
    node = _pre_node("b1", "grayscale")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p", blocks=[PipelineBlock(block_id="b1", block_type="grayscale", params={})]
    )
    plan = _simple_plan()
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, plan)
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    assert pre_sheet.node_type == "preprocessing"


def test_grayscale_algorithm_summary_mentions_grayscale():
    node = _pre_node("b1", "grayscale")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p", blocks=[PipelineBlock(block_id="b1", block_type="grayscale", params={})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    assert "그레이스케일" in pre_sheet.algorithm_summary


def test_hsv_s_algorithm_summary_mentions_hsv_and_saturation():
    node = _pre_node("b1", "hsv_s")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p", blocks=[PipelineBlock(block_id="b1", block_type="hsv_s", params={})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    assert "HSV" in pre_sheet.algorithm_summary
    assert "채도" in pre_sheet.algorithm_summary


def test_hsv_v_algorithm_summary_mentions_hsv_and_value():
    node = _pre_node("b1", "hsv_v")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p", blocks=[PipelineBlock(block_id="b1", block_type="hsv_v", params={})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    assert "HSV" in pre_sheet.algorithm_summary
    assert "명도" in pre_sheet.algorithm_summary


def test_lab_l_algorithm_summary_mentions_lab():
    node = _pre_node("b1", "lab_l")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p", blocks=[PipelineBlock(block_id="b1", block_type="lab_l", params={})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    assert "LAB" in pre_sheet.algorithm_summary


def test_ycrcb_cr_algorithm_summary_mentions_ycrcb():
    node = _pre_node("b1", "ycrcb_cr")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p", blocks=[PipelineBlock(block_id="b1", block_type="ycrcb_cr", params={})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    assert "YCrCb" in pre_sheet.algorithm_summary


# ── Preprocessing nodes — gaussian denoise ──────────────────────────────────

def test_gaussian_fine_kernel_size_description_contains_dimensions():
    node = _pre_node("b1", "gaussian_fine", {"kernel_size": 5, "sigma": 1.0})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="gaussian_fine", params={"kernel_size": 5, "sigma": 1.0})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    param_names = [p.name for p in pre_sheet.parameters]
    assert "kernel_size" in param_names


def test_gaussian_fine_kernel_description_contains_nxn_format():
    node = _pre_node("b1", "gaussian_fine", {"kernel_size": 5, "sigma": 1.0})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="gaussian_fine", params={"kernel_size": 5, "sigma": 1.0})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    k_entry = next(p for p in pre_sheet.parameters if p.name == "kernel_size")
    assert "5×5" in k_entry.mathematical_description


def test_gaussian_fine_sigma_description_contains_sigma_value():
    node = _pre_node("b1", "gaussian_fine", {"kernel_size": 5, "sigma": 1.0})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="gaussian_fine", params={"kernel_size": 5, "sigma": 1.0})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    s_entry = next(p for p in pre_sheet.parameters if p.name == "sigma")
    assert "σ=1.0" in s_entry.mathematical_description


def test_gaussian_mid_kernel_description_contains_nxn():
    node = _pre_node("b1", "gaussian_mid", {"kernel_size": 7, "sigma": 1.5})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="gaussian_mid", params={"kernel_size": 7, "sigma": 1.5})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    k_entry = next(p for p in pre_sheet.parameters if p.name == "kernel_size")
    assert "7×7" in k_entry.mathematical_description


# ── Preprocessing nodes — bilateral ─────────────────────────────────────────

def test_bilateral_algorithm_summary_mentions_edge_preserving():
    node = _pre_node("b1", "bilateral", {"d": 7, "sigma_color": 75, "sigma_space": 75})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="bilateral", params={"d": 7, "sigma_color": 75, "sigma_space": 75})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    assert "양방향" in pre_sheet.algorithm_summary or "엣지" in pre_sheet.algorithm_summary


def test_bilateral_d_description_contains_diameter():
    node = _pre_node("b1", "bilateral", {"d": 7, "sigma_color": 75, "sigma_space": 75})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="bilateral", params={"d": 7, "sigma_color": 75, "sigma_space": 75})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    d_entry = next(p for p in pre_sheet.parameters if p.name == "d")
    assert "7" in d_entry.mathematical_description


# ── Preprocessing nodes — median ─────────────────────────────────────────────

def test_median_kernel_description_contains_median_filter():
    node = _pre_node("b1", "median", {"kernel_size": 5})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="median", params={"kernel_size": 5})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    k_entry = next(p for p in pre_sheet.parameters if p.name == "kernel_size")
    assert "5×5" in k_entry.mathematical_description
    assert "중앙값" in k_entry.mathematical_description


# ── Preprocessing nodes — CLAHE ──────────────────────────────────────────────

def test_clahe_clip_limit_description_contains_value():
    node = _pre_node("b1", "clahe", {"clip_limit": 2.0, "tile_grid_size": (8, 8)})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="clahe", params={"clip_limit": 2.0, "tile_grid_size": (8, 8)})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    cl_entry = next(p for p in pre_sheet.parameters if p.name == "clip_limit")
    assert "2.0" in cl_entry.mathematical_description
    assert "CLAHE" in cl_entry.mathematical_description


def test_clahe_tile_grid_description_contains_dimensions():
    node = _pre_node("b1", "clahe", {"clip_limit": 2.0, "tile_grid_size": (8, 8)})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="clahe", params={"clip_limit": 2.0, "tile_grid_size": (8, 8)})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    tg_entry = next(p for p in pre_sheet.parameters if p.name == "tile_grid_size")
    assert "8×8" in tg_entry.mathematical_description


# ── Feature nodes — threshold ─────────────────────────────────────────────────

def test_otsu_algorithm_summary_mentions_otsu():
    node = _feat_node("b1", "otsu")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p", blocks=[PipelineBlock(block_id="b1", block_type="otsu", params={})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    assert "오츠" in feat_sheet.algorithm_summary


def test_otsu_algorithm_summary_mentions_automatic():
    node = _feat_node("b1", "otsu")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p", blocks=[PipelineBlock(block_id="b1", block_type="otsu", params={})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    assert "자동" in feat_sheet.algorithm_summary


def test_adaptive_mean_block_size_description_contains_nxn():
    node = _feat_node("b1", "adaptive_mean", {"block_size": 11, "c": 5})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="adaptive_mean", params={"block_size": 11, "c": 5})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    bs_entry = next(p for p in feat_sheet.parameters if p.name == "block_size")
    assert "11×11" in bs_entry.mathematical_description


def test_adaptive_mean_block_size_description_mentions_adaptive():
    node = _feat_node("b1", "adaptive_mean", {"block_size": 11, "c": 5})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="adaptive_mean", params={"block_size": 11, "c": 5})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    bs_entry = next(p for p in feat_sheet.parameters if p.name == "block_size")
    assert "적응형" in bs_entry.mathematical_description


def test_adaptive_mean_c_description_mentions_correction():
    node = _feat_node("b1", "adaptive_mean", {"block_size": 11, "c": 5})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="adaptive_mean", params={"block_size": 11, "c": 5})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    c_entry = next(p for p in feat_sheet.parameters if p.name == "c")
    assert "보정" in c_entry.mathematical_description
    assert "5" in c_entry.mathematical_description


def test_adaptive_gauss_summary_mentions_gaussian():
    node = _feat_node("b1", "adaptive_gauss", {"block_size": 11, "c": 5})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="adaptive_gauss", params={"block_size": 11, "c": 5})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    assert "가우시안" in feat_sheet.algorithm_summary


def test_dynamic_threshold_offset_description_contains_offset():
    node = _feat_node("b1", "dynamic_threshold", {"offset": -5})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="dynamic_threshold", params={"offset": -5})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    off_entry = next(p for p in feat_sheet.parameters if p.name == "offset")
    assert "-5" in off_entry.mathematical_description


# ── Feature nodes — morphology ────────────────────────────────────────────────

def test_erosion_kernel_description_contains_erosion():
    node = _feat_node("b1", "erosion", {"kernel_size": 3, "iterations": 2})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="erosion", params={"kernel_size": 3, "iterations": 2})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    k_entry = next(p for p in feat_sheet.parameters if p.name == "kernel_size")
    assert "3×3" in k_entry.mathematical_description
    assert "침식" in k_entry.mathematical_description


def test_erosion_iterations_description_contains_count():
    node = _feat_node("b1", "erosion", {"kernel_size": 3, "iterations": 2})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="erosion", params={"kernel_size": 3, "iterations": 2})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    it_entry = next(p for p in feat_sheet.parameters if p.name == "iterations")
    assert "2회" in it_entry.mathematical_description


def test_dilation_kernel_description_contains_dilation():
    node = _feat_node("b1", "dilation", {"kernel_size": 5, "iterations": 1})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="dilation", params={"kernel_size": 5, "iterations": 1})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    k_entry = next(p for p in feat_sheet.parameters if p.name == "kernel_size")
    assert "팽창" in k_entry.mathematical_description


def test_opening_kernel_description_contains_opening():
    node = _feat_node("b1", "opening", {"kernel_size": 3})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="opening", params={"kernel_size": 3})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    k_entry = next(p for p in feat_sheet.parameters if p.name == "kernel_size")
    assert "열림" in k_entry.mathematical_description


def test_closing_kernel_description_contains_closing():
    node = _feat_node("b1", "closing", {"kernel_size": 3})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="closing", params={"kernel_size": 3})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    k_entry = next(p for p in feat_sheet.parameters if p.name == "kernel_size")
    assert "닫힘" in k_entry.mathematical_description


def test_tophat_summary_mentions_tophat():
    node = _feat_node("b1", "tophat", {"kernel_size": 9})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="tophat", params={"kernel_size": 9})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    assert "탑햇" in feat_sheet.algorithm_summary


def test_blackhat_summary_mentions_blackhat():
    node = _feat_node("b1", "blackhat", {"kernel_size": 9})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="blackhat", params={"kernel_size": 9})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    assert "블랙햇" in feat_sheet.algorithm_summary


def test_morph_gradient_summary_mentions_gradient():
    node = _feat_node("b1", "morph_gradient", {"kernel_size": 3})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="morph_gradient", params={"kernel_size": 3})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    assert "그래디언트" in feat_sheet.algorithm_summary


# ── Feature nodes — edge detection ───────────────────────────────────────────

def test_canny_low_threshold_description_contains_value():
    node = _feat_node("b1", "canny", {"low_threshold": 50, "high_threshold": 150})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="canny", params={"low_threshold": 50, "high_threshold": 150})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    low_entry = next(p for p in feat_sheet.parameters if p.name == "low_threshold")
    assert "50" in low_entry.mathematical_description


def test_canny_high_threshold_description_contains_value():
    node = _feat_node("b1", "canny", {"low_threshold": 50, "high_threshold": 150})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="canny", params={"low_threshold": 50, "high_threshold": 150})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    hi_entry = next(p for p in feat_sheet.parameters if p.name == "high_threshold")
    assert "150" in hi_entry.mathematical_description


def test_canny_summary_mentions_edge_detection():
    node = _feat_node("b1", "canny", {"low_threshold": 50, "high_threshold": 150})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="canny", params={"low_threshold": 50, "high_threshold": 150})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    assert "에지" in feat_sheet.algorithm_summary or "엣지" in feat_sheet.algorithm_summary


def test_sobel_ksize_description_contains_nxn():
    node = _feat_node("b1", "sobel", {"ksize": 3})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="sobel", params={"ksize": 3})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    k_entry = next(p for p in feat_sheet.parameters if p.name == "ksize")
    assert "3×3" in k_entry.mathematical_description
    assert "소벨" in k_entry.mathematical_description


def test_laplacian_ksize_description_contains_laplacian():
    node = _feat_node("b1", "laplacian", {"ksize": 5})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="laplacian", params={"ksize": 5})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    k_entry = next(p for p in feat_sheet.parameters if p.name == "ksize")
    assert "5×5" in k_entry.mathematical_description
    assert "라플라시안" in k_entry.mathematical_description


def test_scharr_summary_mentions_scharr():
    node = _feat_node("b1", "scharr")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="scharr", params={})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    assert "샤르" in feat_sheet.algorithm_summary


# ── Inspection nodes ──────────────────────────────────────────────────────────

def test_inspection_node_type_is_inspection():
    node = _insp_node(1, "Hole Detection", "blob")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    plan = InspectionPlan(
        items=[InspectionItem(item_id=1, name="Hole Detection", category="blob")],
        inspection_purpose="test",
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, _simple_pipeline(), plan)
    insp_sheet = next(s for s in sheets if s.node_id == "insp_1")
    assert insp_sheet.node_type == "inspection"


def test_inspection_node_name_matches_item_name():
    node = _insp_node(1, "Hole Detection", "blob")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    plan = InspectionPlan(
        items=[InspectionItem(item_id=1, name="Hole Detection", category="blob")],
        inspection_purpose="test",
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, _simple_pipeline(), plan)
    insp_sheet = next(s for s in sheets if s.node_id == "insp_1")
    assert "Hole Detection" in insp_sheet.node_name


def test_inspection_algorithm_summary_mentions_item_name():
    node = _insp_node(1, "Hole Detection", "blob")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    plan = InspectionPlan(
        items=[InspectionItem(item_id=1, name="Hole Detection", category="blob")],
        inspection_purpose="test",
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, _simple_pipeline(), plan)
    insp_sheet = next(s for s in sheets if s.node_id == "insp_1")
    assert "Hole Detection" in insp_sheet.algorithm_summary


def test_inspection_category_blob_summary_mentions_blob():
    node = _insp_node(1, "Size Check", "blob")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    plan = InspectionPlan(
        items=[InspectionItem(item_id=1, name="Size Check", category="blob")],
        inspection_purpose="test",
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, _simple_pipeline(), plan)
    insp_sheet = next(s for s in sheets if s.node_id == "insp_1")
    assert "블랍" in insp_sheet.algorithm_summary or "면적" in insp_sheet.algorithm_summary or "blob" in insp_sheet.algorithm_summary.lower()


def test_inspection_success_criteria_appear_as_parameters():
    node = _insp_node(1, "Hole Detection", "blob")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    plan = InspectionPlan(
        items=[InspectionItem(
            item_id=1,
            name="Hole Detection",
            category="blob",
            success_criteria={"min_area": 100, "max_count": 5},
        )],
        inspection_purpose="test",
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, _simple_pipeline(), plan)
    insp_sheet = next(s for s in sheets if s.node_id == "insp_1")
    param_names = [p.name for p in insp_sheet.parameters]
    assert "min_area" in param_names or "max_count" in param_names


def test_inspection_safety_role_reflected_in_summary():
    node = _insp_node(1, "Critical Check", "edge_detection")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    plan = InspectionPlan(
        items=[InspectionItem(
            item_id=1,
            name="Critical Check",
            category="edge_detection",
            safety_role=True,
        )],
        inspection_purpose="test",
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, _simple_pipeline(), plan)
    insp_sheet = next(s for s in sheets if s.node_id == "insp_1")
    # safety_role=True should appear in summary or parameters
    all_text = insp_sheet.algorithm_summary + " ".join(p.mathematical_description for p in insp_sheet.parameters)
    assert "안전" in all_text or "Critical" in all_text or "critical" in all_text.lower()


def test_inspection_edge_detection_category_summary_mentions_edge():
    node = _insp_node(1, "Edge Check", "edge_detection")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    plan = InspectionPlan(
        items=[InspectionItem(item_id=1, name="Edge Check", category="edge_detection")],
        inspection_purpose="test",
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, _simple_pipeline(), plan)
    insp_sheet = next(s for s in sheets if s.node_id == "insp_1")
    assert "에지" in insp_sheet.algorithm_summary or "엣지" in insp_sheet.algorithm_summary or "윤곽" in insp_sheet.algorithm_summary


# ── Decision node ─────────────────────────────────────────────────────────────

def test_decision_node_type_is_decision():
    bp = _simple_blueprint()
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, _simple_pipeline(), _simple_plan())
    dec_sheet = next(s for s in sheets if s.node_id == "decision")
    assert dec_sheet.node_type == "decision"


def test_decision_algorithm_summary_mentions_pass_fail():
    bp = _simple_blueprint()
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, _simple_pipeline(), _simple_plan())
    dec_sheet = next(s for s in sheets if s.node_id == "decision")
    summary_lower = dec_sheet.algorithm_summary
    assert "합격" in summary_lower or "불합격" in summary_lower or "판정" in summary_lower


def test_decision_summary_mentions_inspection_count():
    plan = InspectionPlan(
        items=[
            InspectionItem(item_id=1, name="Check1", category="blob"),
            InspectionItem(item_id=2, name="Check2", category="blob"),
        ],
        inspection_purpose="test",
    )
    nodes = [
        _insp_node(1, "Check1", "blob"),
        _insp_node(2, "Check2", "blob"),
        _decision_node(),
    ]
    bp = Blueprint(nodes=nodes, edges=[])
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, _simple_pipeline(), plan)
    dec_sheet = next(s for s in sheets if s.node_id == "decision")
    assert "2" in dec_sheet.algorithm_summary


# ── Full pipeline test ────────────────────────────────────────────────────────

def test_full_pipeline_produces_complete_parameter_sheet():
    pipeline = ProcessingPipeline(
        pipeline_id="full-001",
        blocks=[
            PipelineBlock(block_id="c1", block_type="grayscale", params={}),
            PipelineBlock(block_id="d1", block_type="gaussian_fine", params={"kernel_size": 5, "sigma": 1.0}),
            PipelineBlock(block_id="t1", block_type="otsu", params={}),
            PipelineBlock(block_id="m1", block_type="erosion", params={"kernel_size": 3, "iterations": 1}),
        ],
    )
    plan = InspectionPlan(
        items=[
            InspectionItem(item_id=1, name="Defect Detection", category="blob", success_criteria={"min_area": 50}),
        ],
        inspection_purpose="결함 검출",
    )
    nodes = [
        _pre_node("c1", "grayscale"),
        _pre_node("d1", "gaussian_fine", {"kernel_size": 5, "sigma": 1.0}),
        _feat_node("t1", "otsu"),
        _feat_node("m1", "erosion", {"kernel_size": 3, "iterations": 1}),
        _insp_node(1, "Defect Detection", "blob"),
        _decision_node(),
    ]
    bp = Blueprint(nodes=nodes, edges=[])
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, plan)

    assert len(sheets) == 6
    types_found = {s.node_type for s in sheets}
    assert "preprocessing" in types_found
    assert "feature" in types_found
    assert "inspection" in types_found
    assert "decision" in types_found


def test_full_pipeline_all_summaries_non_empty():
    bp = _simple_blueprint()
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, _simple_pipeline(), _simple_plan())
    for sheet in sheets:
        assert len(sheet.algorithm_summary) > 0, f"Empty summary for {sheet.node_id}"


def test_full_pipeline_to_dict_serializable():
    bp = _simple_blueprint()
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, _simple_pipeline(), _simple_plan())
    import json
    for sheet in sheets:
        d = sheet.to_dict()
        # Should serialize to JSON without error
        json_str = json.dumps(d, ensure_ascii=False)
        assert len(json_str) > 0


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_unknown_block_type_does_not_raise():
    node = _feat_node("b1", "unknown_block_xyz", {"some_param": 42})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="unknown_block_xyz", params={"some_param": 42})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    feat_sheet = next(s for s in sheets if s.node_id == "feat_b1")
    assert feat_sheet is not None
    assert len(feat_sheet.algorithm_summary) > 0


def test_empty_params_block_does_not_raise():
    node = _pre_node("b1", "gaussian_fine", {})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="gaussian_fine", params={})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    assert pre_sheet is not None


def test_inspection_item_missing_success_criteria_does_not_raise():
    node = _insp_node(1, "Check", "blob")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    plan = InspectionPlan(
        items=[InspectionItem(item_id=1, name="Check", category="blob", success_criteria={})],
        inspection_purpose="test",
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, _simple_pipeline(), plan)
    insp_sheet = next(s for s in sheets if s.node_id == "insp_1")
    assert insp_sheet is not None


def test_inspection_node_without_matching_plan_item_does_not_raise():
    # node_id="insp_999" but plan has item_id=1 — graceful degradation
    node = BlueprintNode(
        node_id="insp_999",
        node_type="inspection",
        label="Unknown Item",
        params={"category": "blob"},
    )
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, _simple_pipeline(), _simple_plan())
    insp_sheet = next(s for s in sheets if s.node_id == "insp_999")
    assert insp_sheet is not None
    assert len(insp_sheet.algorithm_summary) > 0


def test_empty_blueprint_nodes_returns_empty_list():
    bp = Blueprint(nodes=[], edges=[])
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, _simple_pipeline(), _simple_plan())
    assert sheets == []


def test_node_name_in_sheet_matches_blueprint_label():
    node = _pre_node("b1", "grayscale")
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, _simple_pipeline(), _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    assert pre_sheet.node_name == "grayscale"


def test_nlmeans_h_description_contains_noise_parameter():
    node = _pre_node("b1", "nlmeans", {"h": 10, "template_window_size": 7, "search_window_size": 21})
    bp = Blueprint(nodes=[node, _decision_node()], edges=[])
    pipeline = ProcessingPipeline(
        pipeline_id="p",
        blocks=[PipelineBlock(block_id="b1", block_type="nlmeans", params={"h": 10, "template_window_size": 7, "search_window_size": 21})]
    )
    gen = ParameterSheetGenerator()
    sheets = gen.generate(bp, pipeline, _simple_plan())
    pre_sheet = next(s for s in sheets if s.node_id == "pre_b1")
    h_entry = next(p for p in pre_sheet.parameters if p.name == "h")
    assert "10" in h_entry.mathematical_description


def test_to_dict_unit_field_present():
    entry = ParameterEntry(name="clip_limit", value=2.0, mathematical_description="2.0", unit=None)
    sheet = NodeParameterSheet(
        node_id="pre_b1",
        node_name="clahe",
        node_type="preprocessing",
        parameters=[entry],
        algorithm_summary="CLAHE",
    )
    d = sheet.to_dict()
    assert "unit" in d["parameters"][0]
