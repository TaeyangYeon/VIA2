from pydantic import BaseModel


class AgentDirectives(BaseModel):
    orchestrator: str = ""
    spec: str = ""
    image_analysis: str = ""
    depth: str = ""
    material: str = ""
    pipeline_composer: str = ""
    vision_judge: str = ""
    inspection_plan: str = ""
    test: str = ""
