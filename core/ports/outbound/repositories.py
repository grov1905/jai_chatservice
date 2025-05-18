#core/ports/outbound/repositories.py
from abc import ABC, abstractmethod
from core.domain.entities import EndUser, Conversation, Message
from typing import Optional,List
from uuid import UUID

class IEndUserRepository(ABC):
    @abstractmethod
    async def get_by_external_id(
        self, 
        external_id: str, 
        channel: str, 
        business_id: str
    ) -> Optional[EndUser]:
        pass
    
    @abstractmethod
    async def create(self, end_user: EndUser) -> EndUser:
        pass

class IConversationRepository(ABC):
    @abstractmethod
    async def get_active_by_user(
        self, 
        end_user_id: UUID, 
        business_id: str,
        threshold_minutes: int = 30
    ) -> Optional[Conversation]:
        pass
    
    @abstractmethod
    async def create(self, conversation: Conversation) -> Conversation:
        pass
    
    @abstractmethod
    async def close_conversation(self, conversation_id: UUID) -> None:
        pass

class IMessageRepository(ABC):
    @abstractmethod
    async def create(self, message: Message) -> Message:
        pass

    @abstractmethod
    async def get_by_conversation(self, conversation_id: UUID) -> List[Message]:
        pass