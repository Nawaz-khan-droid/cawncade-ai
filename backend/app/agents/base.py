"""
Base Agent class.
All agents (Researcher, Verifier, Synthesizer) inherit from this.
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """
    Abstract base class for CAWNCADE agents.
    Each agent is independently testable.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def execute(self, *args, **kwargs) -> dict:
        """
        Execute the agent's primary task.
        Each agent must return a structured dict result.
        """
        raise NotImplementedError

    def validate_input(self, data: Any, required_keys: list[str]) -> bool:
        """Validate that required keys exist in the input data."""
        if not isinstance(data, dict):
            return False
        return all(key in data for key in required_keys)

    def safe_get(self, data: dict, key: str, default=None):
        """Safely get a value from a dict."""
        if isinstance(data, dict):
            return data.get(key, default)
        return default
