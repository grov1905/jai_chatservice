# infrastructure/adapters/outbound/fastapi_context.py
import httpx
from typing import List, Dict
from core.ports.outbound import IContextRetrieverPort
import logging

class FastAPIContextRetrieverAdapter(IContextRetrieverPort):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    async def retrieve_document_context(
        self, 
        vector: List[float], 
        business_id: str,
        top_k: int,
        min_similarity: float
    ) -> List[Dict]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings/search/",
                    json={
                        "vector": vector,
                        "top_k": top_k,
                        "min_similarity": min_similarity,
                        "business_id": business_id
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error retrieving context: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving context: {e}")
            raise