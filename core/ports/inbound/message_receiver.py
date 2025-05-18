#core/ports/inbound/mesagge_receiver.py
from abc import ABC, abstractmethod
from core.domain.entities import Message, Conversation, EndUser
from typing import Tuple

class IMessageReceiverPort(ABC):
    @abstractmethod
    async def handle_new_message(
        self, 
        channel: str,
        external_id: str,
        business_id: str,
        message_content: str,
        metadata: dict = {}
    ) -> Tuple[EndUser, Conversation, Message]:
        """Procesa un nuevo mensaje de cualquier canal"""
        pass
