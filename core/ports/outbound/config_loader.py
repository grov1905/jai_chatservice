#core/ports/outbound/config_loader.py

from abc import ABC, abstractmethod
from typing import Dict

class IConfigLoaderPort(ABC):
    @abstractmethod
    async def load_bot_config(self, business_id: str) -> Dict:
        """Load bot configuration from external service"""
    
    @abstractmethod
    async def load_bot_template(self, business_id: str, template_type: str) -> Dict:
        """Load bot response template"""
    
    @abstractmethod
    async def load_chunk_settings(self, business_id: str, entity_type: str) -> Dict:
        """Load chunking settings"""