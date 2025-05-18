#core/ports/outbound/context_retriever.py

from abc import ABC, abstractmethod
from typing import List, Dict

class IContextRetrieverPort(ABC):
    @abstractmethod
    async def retrieve_document_context(
        self, 
        vector: List[float], 
        business_id: str,
        top_k: int,
        min_similarity: float
    ) -> List[Dict]:
        """Retrieve relevant document context"""