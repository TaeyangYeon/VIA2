"""BaseAgent abstract class for all VIA2 agents."""
from abc import ABC, abstractmethod

from backend.services.logger import get_agent_logger
from agents.models import AgentResult


class BaseAgent(ABC):
    def __init__(self, name: str, directive: str = "") -> None:
        self.name = name
        self.directive = directive
        self._logger = get_agent_logger(name)

    @property
    def logger(self):
        return self._logger

    def _log(self, level: str, message: str, **extra) -> None:
        getattr(self._logger, level)(message, **extra)

    @abstractmethod
    async def run(self, **kwargs) -> AgentResult:
        ...
