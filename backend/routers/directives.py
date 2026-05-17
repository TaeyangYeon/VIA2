from fastapi import APIRouter

from backend.models.directives import AgentDirectives
from backend.services import directives_store

router = APIRouter()


@router.get("/directives")
async def get_directives() -> AgentDirectives:
    return directives_store.get()


@router.post("/directives")
async def save_directives(directives: AgentDirectives) -> AgentDirectives:
    return directives_store.update(directives)
