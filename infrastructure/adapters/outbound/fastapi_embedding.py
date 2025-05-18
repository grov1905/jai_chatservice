# infrastructure/adapters/outbound/fastapi_embedding.py

import httpx
from typing import List
from core.ports.outbound import IEmbeddingClientPort
import logging

class FastAPIEmbeddingAdapter(IEmbeddingClientPort):
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    async def vectorize_text(
        self, 
        text: str, 
        model_name: str, 
        embedding_dim: int
    ) -> List[float]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/embeddings/generate",
                    json={
                        "texts": [text],
                        "embedding_model": model_name,
                        "embedding_dim": embedding_dim
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return data["embeddings"][0]  # Return first embedding vector
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error vectorizing text: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error vectorizing text: {e}")
            raise