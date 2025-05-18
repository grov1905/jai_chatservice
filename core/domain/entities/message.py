#core/domain/entities/message.py
from pydantic import BaseModel, UUID4,Field,validator
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

class SenderType(str, Enum):
    USER = "user"
    BOT = "bot"
    AGENT = "agent"

class Message(BaseModel):
    id: UUID4
    conversation_id: UUID4
    sender_type: SenderType
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None  # Campo opcional

    @validator('metadata', pre=True)
    def normalize_metadata(cls, v):
        """Convierte {} a None y asegura que sea dict o None"""
        if v == {}:
            return None
        return v if isinstance(v, dict) else None

    class Config:
        from_attributes = True