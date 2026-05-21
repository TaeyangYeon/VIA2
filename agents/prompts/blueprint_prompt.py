"""Prompt builder for BlueprintAgent — returns (system_prompt, user_prompt) for Korean description."""
from agents.models import InspectionPlan, ProcessingPipeline

SYSTEM_PROMPT = """\
당신은 산업 비전 검사 알고리즘 전문가입니다.
주어진 파이프라인 블록과 검사 항목을 보고, 알고리즘의 전체 흐름을 2~4문장의 한국어로 설명하십시오.
코드·JSON·불릿 포인트 없이 설명 텍스트만 출력하십시오.
"""


def build_blueprint_prompt(
    pipeline: ProcessingPipeline,
    inspection_plan: InspectionPlan,
    directive: str | None = None,
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for BlueprintAgent Korean description."""
    parts = ["파이프라인 블록:"]
    for i, block in enumerate(pipeline.blocks, 1):
        if block.params:
            params_str = ", ".join(f"{k}={v}" for k, v in block.params.items())
        else:
            params_str = "없음"
        parts.append(f"  {i}. {block.block_type} (파라미터: {params_str})")

    parts.append("")
    parts.append("검사 항목:")
    for item in inspection_plan.items:
        if item.depends_on:
            deps = ", ".join(str(d) for d in item.depends_on)
            dep_str = f"항목 {deps} 완료 후 검사"
        else:
            dep_str = "독립 검사"
        parts.append(f"  {item.item_id}. {item.name} ({item.category}) - {dep_str}")

    if directive:
        parts.append("")
        parts.append(f"추가 지시사항: {directive}")

    return SYSTEM_PROMPT, "\n".join(parts)
