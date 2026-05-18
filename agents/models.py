"""All data models used across agents. Uses Python dataclasses (not Pydantic)."""
import enum
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentResult:
    status: str
    data: dict
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0


@dataclass
class ImageDiagnosis:
    # Basic optical
    contrast: float
    noise_level: float
    edge_density: float
    lighting_uniformity: float
    illumination_type: str
    noise_frequency: str
    reflection_level: float
    # Material/structure
    surface_type: str
    depth_complexity: float
    has_shadow_region: bool
    # Algorithm selection
    blob_feasibility: float
    blob_count_estimate: int
    color_discriminability: float
    dominant_channel_ratio: float
    structural_regularity: float
    pattern_repetition: float
    # Processing hints
    optimal_color_space: str
    threshold_candidate: float
    edge_sharpness: float


@dataclass
class InspectionItem:
    item_id: int
    name: str
    category: str
    depends_on: list[int] = field(default_factory=list)
    safety_role: bool = False
    success_criteria: dict = field(default_factory=dict)


@dataclass
class InspectionPlan:
    items: list[InspectionItem]
    inspection_purpose: str
    total_items: int = 0

    def __post_init__(self):
        self.total_items = len(self.items)


@dataclass
class JudgementResult:
    visibility_score: float
    separability_score: float
    measurability_score: float
    overall_score: float
    problems: list[str] = field(default_factory=list)
    next_suggestion: str = ""


@dataclass
class AgentDirectives:
    orchestrator: str = ""
    spec: str = ""
    image_analysis: str = ""
    depth: str = ""
    material: str = ""
    pipeline_composer: str = ""
    vision_judge: str = ""
    inspection_plan: str = ""
    test: str = ""


@dataclass
class PipelineBlock:
    block_id: str
    block_type: str
    params: dict = field(default_factory=dict)


@dataclass
class ProcessingPipeline:
    pipeline_id: str
    blocks: list[PipelineBlock]
    quality_score: float = 0.0
    judge_score: float = 0.0
    description: str = ""


@dataclass
class BlueprintNode:
    node_id: str
    node_type: str
    label: str
    params: dict = field(default_factory=dict)


@dataclass
class BlueprintEdge:
    source_id: str
    target_id: str
    label: str = ""


@dataclass
class Blueprint:
    nodes: list[BlueprintNode]
    edges: list[BlueprintEdge]
    svg_content: str = ""
    algorithm_description: str = ""
    parameter_sheet: dict = field(default_factory=dict)


@dataclass
class SceneContext:
    image_diagnosis: ImageDiagnosis
    depth_map: Optional[Any]
    material_map: Optional[Any]
    roi: Optional[dict] = None
    spec: dict = field(default_factory=dict)


class AlgorithmCategory(enum.Enum):
    BLOB = "blob"
    COLOR_FILTER = "color_filter"
    EDGE_DETECTION = "edge_detection"
    TEMPLATE_MATCHING = "template_matching"
    GEOMETRIC = "geometric"


class FailureReason(enum.Enum):
    PIPELINE_BAD_FIT = "pipeline_bad_fit"
    PIPELINE_BAD_PARAMS = "pipeline_bad_params"
    ALGORITHM_WRONG_CATEGORY = "algorithm_wrong_category"
    RUNTIME_ERROR = "runtime_error"
    INSPECTION_PLAN_ISSUE = "inspection_plan_issue"
    SPEC_ISSUE = "spec_issue"


@dataclass
class EvaluationResult:
    passed: bool
    failure_reason: Optional[FailureReason] = None
    metrics: dict = field(default_factory=dict)
    details: str = ""


class DecisionVerdict(enum.Enum):
    RULE_BASED = "rule_based"
    EDGE_LEARNING = "edge_learning"
    DEEP_LEARNING = "deep_learning"
    HARDWARE_IMPROVEMENT = "hardware_improvement"


@dataclass
class DecisionResult:
    verdict: DecisionVerdict
    confidence: float
    reasoning: str
    feature_variability: float = 0.0
    suggestions: list[str] = field(default_factory=list)
