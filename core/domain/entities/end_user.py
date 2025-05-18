#core/domain/entities/end_user.py
from pydantic import BaseModel, UUID4, Field,validator
from typing import Optional, Dict, Any
from enum import Enum

class ChannelType(str, Enum):
    WEB = "websocket"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    FACEBOOK="facebook"
    INSTAGRAM="instagram"
    SMS = "sms"

class EndUser(BaseModel):
    id: UUID4
    business_id: UUID4
    external_id: str
    channel: ChannelType
    name: Optional[str] = None
    phone_number: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # Campo opcional

    @validator('metadata', pre=True)
    def normalize_metadata(cls, v):
        """Convierte {} a None y asegura que sea dict o None"""
        if v == {}:
            return None
        return v if isinstance(v, dict) else None

    class Config:
        from_attributes = True
        extra = "allow"  # Permite campos adicionales