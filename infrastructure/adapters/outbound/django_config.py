#infrastructure/adapters/outbound/django_config.py
import httpx
from typing import Dict
from core.ports.outbound import IConfigLoaderPort
import logging
from datetime import datetime

class DjangoConfigAdapter(IConfigLoaderPort):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    async def load_bot_config(self, business_id: str) -> Dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/bot-settings/by_business/",
                    params={"business_id": business_id},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error loading bot config: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading bot config: {e}")
            raise

    async def load_bot_template(self, business_id: str, template_type: str) -> Dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/bot-templates/by_type/",
                    params={
                        "business_id": business_id,
                        "type": template_type
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                return data[0] if data else {}
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error loading bot template: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading bot template: {e}")
            raise

    async def load_chunk_settings(self, business_id: str, entity_type: str) -> Dict:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/chunking-settings/by_entity/",
                    params={
                        "business_id": business_id,
                        "entity_type": entity_type
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error loading chunk settings: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading chunk settings: {e}")
            raise
        

