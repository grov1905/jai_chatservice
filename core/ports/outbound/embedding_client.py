#core/ports/outbound/embedding_client.py

from abc import ABC, abstractmethod
from typing import List

class IEmbeddingClientPort(ABC):
    @abstractmethod
    async def vectorize_text(
        self, 
        text: str, 
        model_name: str, 
        embedding_dim: int
    ) -> List[float]:
        """Vectorize text using embedding model"""