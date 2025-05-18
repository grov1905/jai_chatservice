#core/domain/entities/conversation.py
from pydantic import BaseModel, UUID4,Field,validator
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class ChannelType(str, Enum):
    WEB = "websocket"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    FACEBOOK="facebook"
    INSTAGRAM="instagram"
    SMS = "sms"

class Conversation(BaseModel):
    id: UUID4
    end_user_id: UUID4
    business_id: UUID4
    channel: ChannelType
    started_at: datetime
    ended_at: datetime | None = None
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None  # Campo opcional

    @validator('metadata', pre=True)
    def normalize_metadata(cls, v):
        """Convierte {} a None y asegura que sea dict o None"""
        if v == {}:
            return None
        return v if isinstance(v, dict) else None

    class Config:
        from_attributes = True