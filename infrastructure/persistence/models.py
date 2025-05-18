#infrastructure/persistence/models.py
from sqlalchemy import Column, String, Enum, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class EndUser(Base):
    __tablename__ = "chat_end_users"
    __table_args__ = (
        {"comment": "Store end users information from different channels"},
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=False)
    external_id = Column(String(255), nullable=False)
    channel = Column(String(20), nullable=False)
    name = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    custommetadata = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "chat_conversations"
    __table_args__ = (
        {"comment": "Store conversations between end users and the system"},
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    end_user_id = Column(UUID(as_uuid=True), ForeignKey("chat_end_users.id"), nullable=False)
    business_id = Column(UUID(as_uuid=True), nullable=False)
    channel = Column(String(20), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    custommetadata = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        {"comment": "Store all messages in conversations"},
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("chat_conversations.id"), nullable=False)
    sender_type = Column(String(10), nullable=False)
    content = Column(String(4000), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    custommetadata = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime, default=datetime.utcnow)