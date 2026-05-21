"""BlueprintAgent — builds Blueprint (graph + SVG) from ProcessingPipeline + InspectionPlan."""
import time
from dataclasses import asdict

from agents.base_agent import BaseAgent
from agents.models import (
    AgentResult,
    Blueprint,
    BlueprintEdge,
    BlueprintNode,
    InspectionItem,
    InspectionPlan,
    ProcessingPipeline,
)
from agents.prompts.blueprint_prompt import build_blueprint_prompt
from backend.services.ai_adapter.base import BaseAIAdapter

_PREPROCESSING_TYPES = frozenset({
    "color_space", "denoise", "gaussian_blur", "bilateral_filter",
    "normalize", "resize", "grayscale", "clahe", "equalize_hist",
})

_NODE_COLORS = {
    "preprocessing": "#4ade80",
    "feature": "#60a5fa",
    "inspection": "#facc15",
    "decision": "#f87171",
}

_SVG_BG = "#1a1a1a"
_SVG_TEXT = "#f5f5f5"
_NODE_W = 180
_NODE_H = 50
_H_PAD = 24
_STAGE_H = 130
_TOP_PAD = 70
_SVG_W = 800

_FALLBACK_DESCRIPTION = "파이프라인 기반 비전 검사 알고리즘"


def _block_node_type(block_type: str) -> str:
    bt = block_type.lower()
    if bt in _PREPROCESSING_TYPES or any(bt.startswith(p) for p in _PREPROCESSING_TYPES):
        return "preprocessing"
    return "feature"


def _build_nodes(
    pipeline: ProcessingPipeline,
    inspection_plan: InspectionPlan,
) -> tuple[list[BlueprintNode], list[BlueprintNode], list[BlueprintNode], BlueprintNode]:
    pre_nodes: list[BlueprintNode] = []
    feat_nodes: list[BlueprintNode] = []

    for block in pipeline.blocks:
        if _block_node_type(block.block_type) == "preprocessing":
            pre_nodes.append(BlueprintNode(
                node_id=f"pre_{block.block_id}",
                node_type="preprocessing",
                label=block.block_type,
                params=dict(block.params),
            ))
        else:
            feat_nodes.append(BlueprintNode(
                node_id=f"feat_{block.block_id}",
                node_type="feature",
                label=block.block_type,
                params=dict(block.params),
            ))

    insp_nodes: list[BlueprintNode] = [
        BlueprintNode(
            node_id=f"insp_{item.item_id}",
            node_type="inspection",
            label=item.name,
            params={"category": item.category},
        )
        for item in inspection_plan.items
    ]

    decision_node = BlueprintNode(
        node_id="decision",
        node_type="decision",
        label="Pass / Fail",
        params={},
    )
    return pre_nodes, feat_nodes, insp_nodes, decision_node


def _build_edges(
    pre_nodes: list[BlueprintNode],
    feat_nodes: list[BlueprintNode],
    insp_nodes: list[BlueprintNode],
    insp_items: list[InspectionItem],
    decision_node: BlueprintNode,
) -> list[BlueprintEdge]:
    edges: list[BlueprintEdge] = []

    # Sequential edges within preprocessing
    for i in range(len(pre_nodes) - 1):
        edges.append(BlueprintEdge(source_id=pre_nodes[i].node_id, target_id=pre_nodes[i + 1].node_id))

    # Sequential edges within feature
    for i in range(len(feat_nodes) - 1):
        edges.append(BlueprintEdge(source_id=feat_nodes[i].node_id, target_id=feat_nodes[i + 1].node_id))

    # Preprocessing → Feature
    if pre_nodes and feat_nodes:
        edges.append(BlueprintEdge(source_id=pre_nodes[-1].node_id, target_id=feat_nodes[0].node_id))

    # Determine entry point into inspection stage
    entry_node: BlueprintNode | None = feat_nodes[-1] if feat_nodes else (pre_nodes[-1] if pre_nodes else None)

    # item_id → node_id mapping for depends_on resolution
    item_id_to_nid = {item.item_id: node.node_id for item, node in zip(insp_items, insp_nodes)}

    # Inspection edges respecting depends_on
    for item, node in zip(insp_items, insp_nodes):
        if item.depends_on:
            for dep_id in item.depends_on:
                if dep_id in item_id_to_nid:
                    edges.append(BlueprintEdge(source_id=item_id_to_nid[dep_id], target_id=node.node_id))
        elif entry_node:
            edges.append(BlueprintEdge(source_id=entry_node.node_id, target_id=node.node_id))

    # Terminal inspection nodes (not referenced by any other item's depends_on) → decision
    depended_ids = {dep for item in insp_items for dep in item.depends_on}
    if insp_nodes:
        for item, node in zip(insp_items, insp_nodes):
            if item.item_id not in depended_ids:
                edges.append(BlueprintEdge(source_id=node.node_id, target_id=decision_node.node_id))
    elif entry_node:
        edges.append(BlueprintEdge(source_id=entry_node.node_id, target_id=decision_node.node_id))

    return edges


def _layout_stage(nodes: list[BlueprintNode], y_center: float) -> list[tuple[float, float]]:
    n = len(nodes)
    if n == 0:
        return []
    total_w = n * _NODE_W + (n - 1) * _H_PAD
    start_cx = (_SVG_W - total_w) / 2 + _NODE_W / 2
    return [(start_cx + i * (_NODE_W + _H_PAD), y_center) for i in range(n)]


def _build_svg(
    pre_nodes: list[BlueprintNode],
    feat_nodes: list[BlueprintNode],
    insp_nodes: list[BlueprintNode],
    decision_node: BlueprintNode,
    edges: list[BlueprintEdge],
) -> str:
    stage_groups = [
        (pre_nodes, "preprocessing"),
        (feat_nodes, "feature"),
        (insp_nodes, "inspection"),
        ([decision_node], "decision"),
    ]
    active_stages = [(nodes, nt) for nodes, nt in stage_groups if nodes]

    svg_height = _TOP_PAD + len(active_stages) * _STAGE_H + 50

    # Build node_id → (cx, cy) position map
    pos_map: dict[str, tuple[float, float]] = {}
    y = _TOP_PAD
    for nodes, _ in active_stages:
        for node, (cx, cy) in zip(nodes, _layout_stage(nodes, y)):
            pos_map[node.node_id] = (cx, cy)
        y += _STAGE_H

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_SVG_W}" height="{svg_height}">',
        f'<rect width="{_SVG_W}" height="{svg_height}" fill="{_SVG_BG}"/>',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">',
        f'  <polygon points="0 0, 10 3.5, 0 7" fill="#aaaaaa"/>',
        '</marker></defs>',
    ]

    # Draw edges first (below nodes)
    for edge in edges:
        if edge.source_id not in pos_map or edge.target_id not in pos_map:
            continue
        sx, sy = pos_map[edge.source_id]
        tx, ty = pos_map[edge.target_id]
        x1, y1 = sx, sy + _NODE_H / 2
        x2, y2 = tx, ty - _NODE_H / 2
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#aaaaaa" stroke-width="1.5" marker-end="url(#arrow)"/>'
        )

    # Draw nodes
    for nodes, _ in active_stages:
        for node in nodes:
            cx, cy = pos_map[node.node_id]
            rx = cx - _NODE_W / 2
            ry = cy - _NODE_H / 2
            color = _NODE_COLORS.get(node.node_type, "#888888")
            parts.append(
                f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{_NODE_W}" height="{_NODE_H}" '
                f'rx="8" ry="8" fill="{color}" stroke="#333333" stroke-width="1"/>'
            )
            parts.append(
                f'<text x="{cx:.1f}" y="{cy + 5:.1f}" text-anchor="middle" '
                f'font-size="13" fill="{_SVG_TEXT}" font-family="monospace">{node.label}</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


class BlueprintAgent(BaseAgent):
    def __init__(
        self,
        adapter: BaseAIAdapter,
        model: str = "qwen2.5-coder:7b",
        directive: str = "",
    ) -> None:
        super().__init__(name="blueprint", directive=directive)
        self.adapter = adapter
        self.model = model

    async def run(
        self,
        pipeline: ProcessingPipeline | None = None,
        inspection_plan: InspectionPlan | None = None,
        directive: str | None = None,
        **kwargs,
    ) -> AgentResult:
        if pipeline is None:
            return AgentResult(status="error", data={}, error_message="Pipeline is required")
        if inspection_plan is None:
            return AgentResult(status="error", data={}, error_message="InspectionPlan is required")
        if not pipeline.blocks:
            return AgentResult(status="error", data={}, error_message="Pipeline has no blocks")
        if not inspection_plan.items:
            return AgentResult(status="error", data={}, error_message="InspectionPlan has no items")

        effective_directive = directive if directive is not None else self.directive

        # Deterministic graph + SVG construction (no LLM)
        pre_nodes, feat_nodes, insp_nodes, decision_node = _build_nodes(pipeline, inspection_plan)
        edges = _build_edges(pre_nodes, feat_nodes, insp_nodes, inspection_plan.items, decision_node)
        svg = _build_svg(pre_nodes, feat_nodes, insp_nodes, decision_node, edges)

        # LLM call for Korean description (graceful degradation)
        start = time.monotonic()
        description = _FALLBACK_DESCRIPTION
        try:
            system_prompt, user_prompt = build_blueprint_prompt(
                pipeline=pipeline,
                inspection_plan=inspection_plan,
                directive=effective_directive or None,
            )
            raw = await self.adapter.generate_text(
                user_prompt,
                self.model,
                system_prompt=system_prompt,
            )
            description = raw.strip() or _FALLBACK_DESCRIPTION
        except Exception as exc:
            self._log("warning", "BlueprintAgent LLM call failed, using fallback", error=str(exc))

        elapsed = (time.monotonic() - start) * 1000

        all_nodes = pre_nodes + feat_nodes + insp_nodes + [decision_node]
        blueprint = Blueprint(
            nodes=all_nodes,
            edges=edges,
            svg_content=svg,
            algorithm_description=description,
        )

        self._log("info", "BlueprintAgent completed",
                  node_count=len(all_nodes), edge_count=len(edges))

        return AgentResult(
            status="success",
            data={
                "blueprint": asdict(blueprint),
                "svg": svg,
                "description": description,
                "node_count": len(all_nodes),
                "edge_count": len(edges),
            },
            error_message=None,
            execution_time_ms=elapsed,
        )
