# infrastructure/persistence/repositories.py
import logging
from uuid import UUID
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from core.domain.entities import EndUser, Conversation, Message
from sqlalchemy import select
from core.ports.outbound.repositories import (
    IEndUserRepository,
    IConversationRepository,
    IMessageRepository
)
from infrastructure.persistence.models import (
    EndUser as EndUserModel,
    Conversation as ConversationModel,
    Message as MessageModel
)

logger = logging.getLogger(__name__)

@contextmanager
def session_scope(db: Session):
    """Proporciona un scope transaccional alrededor de una serie de operaciones."""
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error en transacción de base de datos: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error inesperado: {str(e)}")
        raise
    finally:
        db.close()

class DatabaseEndUserRepository(IEndUserRepository):
    def __init__(self, db: Session):
        self.db = db

    async def get_by_external_id(
        self, 
        external_id: str, 
        channel: str, 
        business_id: str
    ) -> Optional[EndUser]:
        
        logger.info("get_by_external_id")
        
        try:
            with session_scope(self.db) as db:
                user = db.query(EndUserModel).filter(
                    EndUserModel.external_id == external_id,
                    EndUserModel.channel == channel,
                    EndUserModel.business_id == business_id
                ).first()
                
                if not user:
                    return None
                    
                return EndUser(
                    id=user.id,
                    business_id=user.business_id,
                    external_id=user.external_id,
                    channel=user.channel,
                    name=user.name,
                    phone_number=user.phone_number,
                    metadata=user.metadata
                )
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener usuario por external_id: {str(e)}")
            raise

    async def create(self, end_user: EndUser) -> EndUser:
        try:
            with session_scope(self.db) as db:
                db_user = EndUserModel(
                    id=end_user.id,
                    business_id=end_user.business_id,
                    external_id=end_user.external_id,
                    channel=end_user.channel,
                    name=end_user.name,
                    phone_number=end_user.phone_number,
                    metadata=end_user.metadata
                )
                db.add(db_user)
                return end_user
        except SQLAlchemyError as e:
            logger.error(f"Error al crear usuario: {str(e)}")
            raise

class DatabaseConversationRepository(IConversationRepository):
    def __init__(self, db: Session):
        self.db = db

    async def get_active_by_user(
        self, 
        end_user_id: UUID, 
        business_id: str,
        threshold_minutes: int = 30
    ) -> Optional[Conversation]:
        try:
            with session_scope(self.db) as db:
                threshold_time = datetime.utcnow() - timedelta(minutes=threshold_minutes)
                
                conversation = db.query(ConversationModel).filter(
                    ConversationModel.end_user_id == end_user_id,
                    ConversationModel.business_id == business_id,
                    ConversationModel.is_active == True,
                    ConversationModel.started_at >= threshold_time
                ).order_by(ConversationModel.started_at.desc()).first()
                
                if not conversation:
                    return None
                    
                return Conversation(
                    id=conversation.id,
                    end_user_id=conversation.end_user_id,
                    business_id=conversation.business_id,
                    channel=conversation.channel,
                    started_at=conversation.started_at,
                    ended_at=conversation.ended_at,
                    is_active=conversation.is_active,
                    metadata=conversation.metadata
                )
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener conversación activa: {str(e)}")
            raise

    async def create(self, conversation: Conversation) -> Conversation:
        try:
            with session_scope(self.db) as db:
                db_conv = ConversationModel(
                    id=conversation.id,
                    end_user_id=conversation.end_user_id,
                    business_id=conversation.business_id,
                    channel=conversation.channel,
                    started_at=conversation.started_at,
                    is_active=conversation.is_active,
                    metadata=conversation.metadata
                )
                db.add(db_conv)
                return conversation
        except SQLAlchemyError as e:
            logger.error(f"Error al crear conversación: {str(e)}")
            raise

    async def close_conversation(self, conversation_id: UUID) -> None:
        try:
            with session_scope(self.db) as db:
                conversation = db.query(ConversationModel).filter(
                    ConversationModel.id == conversation_id
                ).first()
                
                if conversation:
                    conversation.is_active = False
                    conversation.ended_at = datetime.utcnow()
        except SQLAlchemyError as e:
            logger.error(f"Error al cerrar conversación: {str(e)}")
            raise

class DatabaseMessageRepository(IMessageRepository):
    def __init__(self, db: Session):
        self.db = db

    async def create(self, message: Message) -> Message:
        try:
            with session_scope(self.db) as db:
                db_msg = MessageModel(
                    id=message.id,
                    conversation_id=message.conversation_id,
                    sender_type=message.sender_type,
                    content=message.content,
                    timestamp=message.timestamp,
                    metadata=message.metadata
                )
                db.add(db_msg)
                return message
        except SQLAlchemyError as e:
            logger.error(f"Error al crear mensaje: {str(e)}")
            raise
    
    async def get_by_conversation(self, conversation_id: UUID) -> List[Message]:
        try:
            with session_scope(self.db) as db:
                messages = db.execute(
                    select(MessageModel)
                    .where(MessageModel.conversation_id == conversation_id)
                    .order_by(MessageModel.timestamp)
                )
                return [message.to_entity() for message in messages.scalars()]
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener mensajes: {str(e)}")
            raise