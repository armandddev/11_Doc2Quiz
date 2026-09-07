from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseModelEndpoint(ABC):
    """Interface minimale : generate() ou chat()"""
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str: ...

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]: ...