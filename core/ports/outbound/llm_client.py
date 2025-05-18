#core/ports/outbound/llm_client.py

from abc import ABC, abstractmethod
from typing import Dict

class ILLMClientPort(ABC):
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        model_name: str, 
        temperature: float,
        top_p: float,
        frequency_penalty: float,
        presence_penalty: float
    ) -> str:
        """Generate response using LLM"""