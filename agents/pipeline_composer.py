"""Pipeline Composer — rule-based composition of candidate image processing pipelines."""
import time

from agents.base_agent import BaseAgent
from agents.models import (
    AgentResult,
    ImageDiagnosis,
    PipelineBlock,
    ProcessingPipeline,
    SceneContext,
)
from agents.pipeline_blocks import BlockDefinition, get_block, get_matching_blocks

_CATEGORY_SEQUENCE = ["color_space", "denoise", "threshold", "morphology", "edge"]

_EXPLORE_MORPH_NAMES = ["opening", "closing"]
_EXPLORE_EDGE_NAMES = ["sobel", "canny"]


def _to_pipeline_block(block_def: BlockDefinition) -> PipelineBlock:
    return PipelineBlock(
        block_id=block_def.name,
        block_type=block_def.category,
        params=dict(block_def.params),
    )


class PipelineComposer(BaseAgent):
    def __init__(self, directive: str = "") -> None:
        super().__init__("pipeline_composer", directive)

    async def run(self, scene_context: SceneContext = None, **kwargs) -> AgentResult:
        t0 = time.monotonic()

        if scene_context is None:
            return AgentResult(
                status="error",
                data={},
                error_message="scene_context is required",
            )
        if scene_context.image_diagnosis is None:
            return AgentResult(
                status="error",
                data={},
                error_message="scene_context.image_diagnosis is required",
            )

        diagnosis = scene_context.image_diagnosis

        matching: dict[str, list[BlockDefinition]] = {
            cat: get_matching_blocks(diagnosis, category=cat)
            for cat in _CATEGORY_SEQUENCE
        }

        # Mandatory fallbacks
        if not matching["color_space"]:
            fb = get_block("grayscale")
            if fb:
                matching["color_space"] = [fb]
        if not matching["threshold"]:
            fb = get_block("dynamic_threshold") or get_block("otsu")
            if fb:
                matching["threshold"] = [fb]

        summary = {cat: len(blocks) for cat, blocks in matching.items()}
        force_clahe = "clahe" in self.directive.lower()
        pipelines = self._compose(matching, diagnosis, force_clahe)

        return AgentResult(
            status="success",
            data={
                "pipelines": pipelines,
                "num_candidates": len(pipelines),
                "matching_blocks_summary": summary,
            },
            execution_time_ms=(time.monotonic() - t0) * 1000.0,
        )

    def _compose(
        self,
        matching: dict[str, list[BlockDefinition]],
        diagnosis: ImageDiagnosis,
        force_clahe: bool,
    ) -> list[ProcessingPipeline]:
        cs_pool = matching["color_space"]
        dn_pool = matching["denoise"]
        th_pool = matching["threshold"]
        morph_pool = matching["morphology"]
        edge_pool = matching["edge"]

        clahe_blk = get_block("clahe")
        needs_clahe = diagnosis.lighting_uniformity > 0.25

        # Exploration blocks for diversity (supplement pools when sparse)
        morph_names = {b.name for b in morph_pool}
        explore_morph: list[BlockDefinition] = [
            b
            for name in _EXPLORE_MORPH_NAMES
            if (b := get_block(name)) and b.name not in morph_names
        ]
        edge_names = {b.name for b in edge_pool}
        explore_edge: list[BlockDefinition] = [
            b
            for name in _EXPLORE_EDGE_NAMES
            if (b := get_block(name)) and b.name not in edge_names
        ]

        ext_morph = morph_pool + explore_morph
        ext_edge = edge_pool + explore_edge

        def at(pool: list, i: int):
            return pool[min(i, len(pool) - 1)] if pool else None

        def pick_dn(idx: int = 0) -> BlockDefinition | None:
            if force_clahe:
                return clahe_blk
            return at(dn_pool, idx)

        seen: set[tuple] = set()
        pipelines: list[ProcessingPipeline] = []

        def emit(cs, dn, th, morph, edge, suffix: str, desc: str) -> None:
            if len(pipelines) >= 5 or not cs or not th:
                return
            blocks_raw = [x for x in [cs, dn, th, morph, edge] if x is not None]
            key = tuple(b.name for b in blocks_raw)
            if key in seen:
                return
            seen.add(key)
            n = len(pipelines) + 1
            pipelines.append(ProcessingPipeline(
                pipeline_id=f"pipe_{n:02d}_{suffix}",
                blocks=[_to_pipeline_block(b) for b in blocks_raw],
                description=desc,
            ))

        cs0 = at(cs_pool, 0)
        th0 = at(th_pool, 0)

        # 1. CLAHE strategy — triggers when lighting is uneven or directive forces it
        if (needs_clahe or force_clahe) and clahe_blk:
            emit(cs0, clahe_blk, th0, None, None,
                 "clahe", f"CLAHE 기반 + {th0.name if th0 else '이진화'}")

        # 2. Basic: first cs + primary denoise + first thresh
        emit(cs0, pick_dn(0), th0, None, None,
             "basic", f"{cs0.name if cs0 else ''} + {th0.name if th0 else ''}")

        # 3. Alt: second cs + second denoise + second thresh
        emit(at(cs_pool, 1), pick_dn(1), at(th_pool, 1), None, None,
             "alt", "대안 색공간 + 이진화")

        # 4. Morphology variant
        emit(cs0, pick_dn(0), th0, at(ext_morph, 0), None,
             "morph", f"{cs0.name if cs0 else ''} + 형태학 처리")

        # 5. Edge variant
        emit(cs0, pick_dn(0), th0, None, at(ext_edge, 0),
             "edge", f"{cs0.name if cs0 else ''} + 엣지 검출")

        # 6. Full: first cs + first dn + second thresh + second morph + second edge
        emit(cs0, pick_dn(0), at(th_pool, 1), at(ext_morph, 1), at(ext_edge, 1),
             "full", "전체 파이프라인")

        # 7. Alt color-space + morphology
        emit(at(cs_pool, 1), pick_dn(0), th0, at(ext_morph, 1), None,
             "alt_morph", "대안 색공간 + 형태학")

        # 8. Third color-space + edge
        emit(at(cs_pool, 2), pick_dn(0), th0, None, at(ext_edge, 1),
             "alt3", "세 번째 색공간 + 엣지")

        # Ensure minimum 3 by adding fill variants when options are sparse
        extra = 0
        while len(pipelines) < 3 and extra < 10:
            m = at(ext_morph, extra % max(len(ext_morph), 1))
            e = at(ext_edge, extra % max(len(ext_edge), 1))
            emit(cs0, pick_dn(0), th0, m, None, f"fill_m{extra}", "형태학 채움 파이프라인")
            if len(pipelines) < 3:
                emit(cs0, pick_dn(0), th0, None, e, f"fill_e{extra}", "엣지 채움 파이프라인")
            extra += 1

        return pipelines
