"""ParameterSheetGenerator — rule-based, library-agnostic parameter sheet generation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from agents.models import Blueprint, BlueprintNode, InspectionItem, InspectionPlan, ProcessingPipeline


@dataclass
class ParameterEntry:
    name: str
    value: Any
    mathematical_description: str
    unit: Optional[str] = None


@dataclass
class NodeParameterSheet:
    node_id: str
    node_name: str
    node_type: str
    parameters: list[ParameterEntry]
    algorithm_summary: str

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_name": self.node_name,
            "node_type": self.node_type,
            "parameters": [
                {
                    "name": p.name,
                    "value": list(p.value) if isinstance(p.value, tuple) else p.value,
                    "mathematical_description": p.mathematical_description,
                    "unit": p.unit,
                }
                for p in self.parameters
            ],
            "algorithm_summary": self.algorithm_summary,
        }


# ── algorithm summary tables ─────────────────────────────────────────────────

_PREPROCESSING_SUMMARIES: dict[str, str] = {
    "grayscale":     "RGB→그레이스케일 단일 채널 변환",
    "hsv_s":         "RGB→HSV 색공간 변환 후 채도(S) 채널 추출",
    "hsv_v":         "RGB→HSV 색공간 변환 후 명도(V) 채널 추출",
    "lab_l":         "RGB→LAB 색공간 변환 후 밝기(L) 채널 추출",
    "ycrcb_cr":      "RGB→YCrCb 색공간 변환 후 Cr 채널 추출",
    "gaussian_fine": "가우시안 미세 스무딩으로 약한 노이즈 제거",
    "gaussian_mid":  "가우시안 중간 스무딩으로 중간 노이즈 제거",
    "bilateral":     "양방향 필터로 엣지를 보존하며 노이즈 제거",
    "median":        "중앙값 필터로 솔트앤페퍼 노이즈 제거",
    "nlmeans":       "Non-local Means 알고리즘으로 강한 노이즈 제거",
    "clahe":         "CLAHE 알고리즘으로 불균일 조명 대비 향상",
}

_FEATURE_SUMMARIES: dict[str, str] = {
    "otsu":              "오츠 알고리즘에 의한 자동 임계값 이진화",
    "adaptive_mean":     "로컬 영역 적응형 평균 이진화",
    "adaptive_gauss":    "가우시안 가중 적응형 이진화로 불균일 조명 및 노이즈 대응",
    "dynamic_threshold": "동적 임계값으로 낮은 대비 이미지 이진화",
    "erosion":           "형태학적 침식으로 밝은 노이즈 및 돌출 제거",
    "dilation":          "형태학적 팽창으로 어두운 노이즈 및 구멍 채움",
    "opening":           "열림(침식 후 팽창)으로 작은 전경 노이즈 제거",
    "closing":           "닫힘(팽창 후 침식)으로 작은 구멍 및 균열 채움",
    "tophat":            "탑햇 변환으로 밝은 세부 구조 추출",
    "blackhat":          "블랙햇 변환으로 어두운 세부 구조 추출",
    "morph_gradient":    "모폴로지 그래디언트로 윤곽 강조",
    "canny":             "이중 임계값 에지 검출",
    "sobel":             "소벨 미분 필터로 방향성 그래디언트 검출",
    "laplacian":         "라플라시안 이차 미분 필터로 에지 검출",
    "scharr":            "샤르 고정밀 방향성 그래디언트 검출",
}

_CATEGORY_LABELS: dict[str, str] = {
    "blob":              "블랍 분석",
    "edge_detection":    "에지 검출",
    "color_filter":      "색상 필터",
    "template_matching": "템플릿 매칭",
    "geometric":         "기하학적 측정",
}

_CRITERIA_DESCRIPTIONS: dict[str, str] = {
    "min_area":   "최소 면적 기준 {}px²",
    "max_area":   "최대 면적 기준 {}px²",
    "min_count":  "최소 검출 개수 {}",
    "max_count":  "최대 허용 개수 {}",
    "min_length": "최소 길이 기준 {}px",
    "max_length": "최대 길이 기준 {}px",
    "threshold":  "판정 임계값 {}",
    "min_score":  "최소 합격 점수 {}",
    "max_score":  "최대 허용 점수 {}",
}


# ── parameter entry builders ─────────────────────────────────────────────────

def _tile_str(v: Any) -> str:
    if isinstance(v, (list, tuple)) and len(v) == 2:
        return f"{v[0]}×{v[1]}"
    return str(v)


def _make_preprocessing_entries(block_type: str, params: dict) -> list[ParameterEntry]:
    entries: list[ParameterEntry] = []

    if block_type in ("gaussian_fine", "gaussian_mid"):
        if "kernel_size" in params:
            k = params["kernel_size"]
            entries.append(ParameterEntry(
                name="kernel_size", value=k,
                mathematical_description=f"{k}×{k} 가우시안 커널",
            ))
        if "sigma" in params:
            s = params["sigma"]
            entries.append(ParameterEntry(
                name="sigma", value=s,
                mathematical_description=f"σ={s} 가우시안 분포",
            ))

    elif block_type == "bilateral":
        if "d" in params:
            d = params["d"]
            entries.append(ParameterEntry(
                name="d", value=d,
                mathematical_description=f"필터 직경 {d}px",
                unit="px",
            ))
        if "sigma_color" in params:
            sc = params["sigma_color"]
            entries.append(ParameterEntry(
                name="sigma_color", value=sc,
                mathematical_description=f"색상 공간 σ={sc}",
            ))
        if "sigma_space" in params:
            ss = params["sigma_space"]
            entries.append(ParameterEntry(
                name="sigma_space", value=ss,
                mathematical_description=f"좌표 공간 σ={ss}",
            ))

    elif block_type == "median":
        if "kernel_size" in params:
            k = params["kernel_size"]
            entries.append(ParameterEntry(
                name="kernel_size", value=k,
                mathematical_description=f"{k}×{k} 중앙값 필터",
            ))

    elif block_type == "nlmeans":
        if "h" in params:
            h = params["h"]
            entries.append(ParameterEntry(
                name="h", value=h,
                mathematical_description=f"노이즈 강도 파라미터 h={h}",
            ))
        if "template_window_size" in params:
            tw = params["template_window_size"]
            entries.append(ParameterEntry(
                name="template_window_size", value=tw,
                mathematical_description=f"템플릿 윈도우 {tw}×{tw}",
            ))
        if "search_window_size" in params:
            sw = params["search_window_size"]
            entries.append(ParameterEntry(
                name="search_window_size", value=sw,
                mathematical_description=f"탐색 윈도우 {sw}×{sw}",
            ))

    elif block_type == "clahe":
        if "clip_limit" in params:
            cl = params["clip_limit"]
            entries.append(ParameterEntry(
                name="clip_limit", value=cl,
                mathematical_description=f"CLAHE 대비 제한 계수 {cl}",
            ))
        if "tile_grid_size" in params:
            tg = params["tile_grid_size"]
            entries.append(ParameterEntry(
                name="tile_grid_size", value=tg,
                mathematical_description=f"타일 격자 {_tile_str(tg)}",
            ))

    return entries


def _make_feature_entries(block_type: str, params: dict) -> list[ParameterEntry]:
    entries: list[ParameterEntry] = []

    if block_type in ("adaptive_mean", "adaptive_gauss"):
        if "block_size" in params:
            bs = params["block_size"]
            entries.append(ParameterEntry(
                name="block_size", value=bs,
                mathematical_description=f"{bs}×{bs} 로컬 영역 적응형 임계값",
            ))
        if "c" in params:
            c = params["c"]
            entries.append(ParameterEntry(
                name="c", value=c,
                mathematical_description=f"임계값 보정 상수 {c}",
            ))

    elif block_type == "dynamic_threshold":
        if "offset" in params:
            off = params["offset"]
            sign = "+" if off >= 0 else ""
            entries.append(ParameterEntry(
                name="offset", value=off,
                mathematical_description=f"평균 대비 {sign}{off} 오프셋 임계값",
            ))

    elif block_type in ("erosion", "dilation"):
        op_label = "침식" if block_type == "erosion" else "팽창"
        if "kernel_size" in params:
            k = params["kernel_size"]
            entries.append(ParameterEntry(
                name="kernel_size", value=k,
                mathematical_description=f"{k}×{k} {op_label} 커널",
            ))
        if "iterations" in params:
            n = params["iterations"]
            entries.append(ParameterEntry(
                name="iterations", value=n,
                mathematical_description=f"{n}회 반복 형태학적 {op_label}",
            ))

    elif block_type == "opening":
        if "kernel_size" in params:
            k = params["kernel_size"]
            entries.append(ParameterEntry(
                name="kernel_size", value=k,
                mathematical_description=f"{k}×{k} 구조 요소, 열림(침식 후 팽창)",
            ))

    elif block_type == "closing":
        if "kernel_size" in params:
            k = params["kernel_size"]
            entries.append(ParameterEntry(
                name="kernel_size", value=k,
                mathematical_description=f"{k}×{k} 구조 요소, 닫힘(팽창 후 침식)",
            ))

    elif block_type == "tophat":
        if "kernel_size" in params:
            k = params["kernel_size"]
            entries.append(ParameterEntry(
                name="kernel_size", value=k,
                mathematical_description=f"{k}×{k} 구조 요소, 탑햇(원본−열림)",
            ))

    elif block_type == "blackhat":
        if "kernel_size" in params:
            k = params["kernel_size"]
            entries.append(ParameterEntry(
                name="kernel_size", value=k,
                mathematical_description=f"{k}×{k} 구조 요소, 블랙햇(닫힘−원본)",
            ))

    elif block_type == "morph_gradient":
        if "kernel_size" in params:
            k = params["kernel_size"]
            entries.append(ParameterEntry(
                name="kernel_size", value=k,
                mathematical_description=f"{k}×{k} 구조 요소, 모폴로지 그래디언트(팽창−침식)",
            ))

    elif block_type == "canny":
        if "low_threshold" in params:
            low = params["low_threshold"]
            entries.append(ParameterEntry(
                name="low_threshold", value=low,
                mathematical_description=f"하한 임계값 {low}",
            ))
        if "high_threshold" in params:
            high = params["high_threshold"]
            entries.append(ParameterEntry(
                name="high_threshold", value=high,
                mathematical_description=f"상한 임계값 {high}",
            ))

    elif block_type == "sobel":
        if "ksize" in params:
            k = params["ksize"]
            entries.append(ParameterEntry(
                name="ksize", value=k,
                mathematical_description=f"{k}×{k} 소벨 미분 필터",
            ))

    elif block_type == "laplacian":
        if "ksize" in params:
            k = params["ksize"]
            entries.append(ParameterEntry(
                name="ksize", value=k,
                mathematical_description=f"{k}×{k} 라플라시안 이차 미분 필터",
            ))

    return entries


def _make_inspection_entries(item: InspectionItem) -> list[ParameterEntry]:
    entries: list[ParameterEntry] = []
    for key, val in (item.success_criteria or {}).items():
        tmpl = _CRITERIA_DESCRIPTIONS.get(key)
        desc = tmpl.format(val) if tmpl else f"{key}: {val}"
        entries.append(ParameterEntry(name=key, value=val, mathematical_description=desc))
    return entries


# ── generator ────────────────────────────────────────────────────────────────

class ParameterSheetGenerator:
    def generate(
        self,
        blueprint: Blueprint,
        pipeline: ProcessingPipeline,
        inspection_plan: InspectionPlan,
    ) -> list[NodeParameterSheet]:
        item_map: dict[int, InspectionItem] = {
            item.item_id: item for item in inspection_plan.items
        }
        insp_count = sum(1 for n in blueprint.nodes if n.node_type == "inspection")
        return [
            self._process_node(node, item_map, insp_count)
            for node in blueprint.nodes
        ]

    def _process_node(
        self,
        node: BlueprintNode,
        item_map: dict[int, InspectionItem],
        insp_count: int,
    ) -> NodeParameterSheet:
        if node.node_type == "preprocessing":
            return self._preprocessing_sheet(node)
        if node.node_type == "feature":
            return self._feature_sheet(node)
        if node.node_type == "inspection":
            return self._inspection_sheet(node, item_map)
        if node.node_type == "decision":
            return self._decision_sheet(node, insp_count)
        return NodeParameterSheet(
            node_id=node.node_id,
            node_name=node.label,
            node_type=node.node_type,
            parameters=[],
            algorithm_summary=f"{node.label} 처리 노드",
        )

    def _preprocessing_sheet(self, node: BlueprintNode) -> NodeParameterSheet:
        block_type = node.label
        return NodeParameterSheet(
            node_id=node.node_id,
            node_name=block_type,
            node_type="preprocessing",
            parameters=_make_preprocessing_entries(block_type, node.params),
            algorithm_summary=_PREPROCESSING_SUMMARIES.get(block_type, f"{block_type} 전처리"),
        )

    def _feature_sheet(self, node: BlueprintNode) -> NodeParameterSheet:
        block_type = node.label
        return NodeParameterSheet(
            node_id=node.node_id,
            node_name=block_type,
            node_type="feature",
            parameters=_make_feature_entries(block_type, node.params),
            algorithm_summary=_FEATURE_SUMMARIES.get(block_type, f"{block_type} 특징 추출"),
        )

    def _inspection_sheet(
        self,
        node: BlueprintNode,
        item_map: dict[int, InspectionItem],
    ) -> NodeParameterSheet:
        item: InspectionItem | None = None
        try:
            item_id = int(node.node_id.split("_", 1)[1])
            item = item_map.get(item_id)
        except (IndexError, ValueError):
            pass

        if item is not None:
            category_label = _CATEGORY_LABELS.get(item.category, item.category)
            summary = f"{item.name} — {category_label} 기반 검사"
            if item.safety_role:
                summary += " [안전 항목]"
            return NodeParameterSheet(
                node_id=node.node_id,
                node_name=item.name,
                node_type="inspection",
                parameters=_make_inspection_entries(item),
                algorithm_summary=summary,
            )

        return NodeParameterSheet(
            node_id=node.node_id,
            node_name=node.label,
            node_type="inspection",
            parameters=[],
            algorithm_summary=f"{node.label} — 비전 검사",
        )

    def _decision_sheet(self, node: BlueprintNode, insp_count: int) -> NodeParameterSheet:
        return NodeParameterSheet(
            node_id=node.node_id,
            node_name=node.label,
            node_type="decision",
            parameters=[],
            algorithm_summary=f"전체 {insp_count}개 검사 항목의 결과를 종합하여 합격/불합격 판정",
        )
