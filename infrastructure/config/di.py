#infrastructure/config/di.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from infrastructure.config.database import SessionLocal
from infrastructure.config.database import get_db
from infrastructure.adapters.outbound  import (
    DjangoConfigAdapter,
    FastAPIEmbeddingAdapter,
    FastAPIContextRetrieverAdapter,
    OpenAIClientAdapter
)
from infrastructure.persistence.repositories import (
    DatabaseEndUserRepository,
    DatabaseConversationRepository,
    DatabaseMessageRepository
)
from core.use_cases.receive_message import ReceiveMessageUseCase
from core.ports.outbound import (
    IConfigLoaderPort,
    IEmbeddingClientPort,
    IContextRetrieverPort,
    ILLMClientPort,
    IEndUserRepository,
    IConversationRepository,
    IMessageRepository
)
from core.ports.inbound import ( IMessageReceiverPort )
from infrastructure.adapters.inbound import (
    TwilioWhatsAppAdapter,
    TelegramAdapter,
    WebSocketAdapter
)
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

def get_config_loader() -> IConfigLoaderPort:
    return DjangoConfigAdapter(os.getenv("DJANGO_API_URL"))

def get_embedding_client() -> IEmbeddingClientPort:
    return FastAPIEmbeddingAdapter(os.getenv("FASTAPI_EMBEDDING_URL"))

def get_context_retriever() -> IContextRetrieverPort:
    return FastAPIContextRetrieverAdapter(os.getenv("FASTAPI_CONTEXT_URL"))

def get_llm_client() -> ILLMClientPort:
    return OpenAIClientAdapter(os.getenv("OPENAI_API_KEY"))

def get_end_user_repository(db: Session = Depends(get_db)) -> IEndUserRepository:
    return DatabaseEndUserRepository(db)

def get_conversation_repository(db: Session = Depends(get_db)) -> IConversationRepository:
    return DatabaseConversationRepository(db)

def get_message_repository(db: Session = Depends(get_db)) -> IMessageRepository:
    return DatabaseMessageRepository(db)

def get_message_use_case(
    config_loader: IConfigLoaderPort = Depends(get_config_loader),
    embedding_client: IEmbeddingClientPort = Depends(get_embedding_client),
    context_retriever: IContextRetrieverPort = Depends(get_context_retriever),
    llm_client: ILLMClientPort = Depends(get_llm_client),
    end_user_repo: IEndUserRepository = Depends(get_end_user_repository),
    conversation_repo: IConversationRepository = Depends(get_conversation_repository),
    message_repo: IMessageRepository = Depends(get_message_repository)
) -> ReceiveMessageUseCase:
    return ReceiveMessageUseCase(
        config_loader=config_loader,
        embedding_client=embedding_client,
        context_retriever=context_retriever,
        llm_client=llm_client,
        end_user_repo=end_user_repo,
        conversation_repo=conversation_repo,
        message_repo=message_repo
    )

def get_twilio_adapter(
    message_receiver: IMessageReceiverPort = Depends(get_message_use_case)
) -> TwilioWhatsAppAdapter:
    """
    Crea una instancia del adaptador de Twilio con validación de configuración
    """
    # Validar que las variables de entorno estén configuradas
    required_vars = ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Variables de entorno faltantes para Twilio: {missing_vars}")
    logger.info("Inicializando TwilioWhatsAppAdapter")
    return TwilioWhatsAppAdapter(message_receiver)

def get_telegram_adapter(
    message_receiver: IMessageReceiverPort = Depends(get_message_use_case)
) -> TelegramAdapter:
    """
    Valida que al menos un token de Telegram esté configurado
    """
    # Buscar tokens de Telegram en variables de entorno
    telegram_tokens = {
        key: value for key, value in os.environ.items() 
        if key.startswith("TELEGRAM_TOKEN_") and value
    }
    
    if not telegram_tokens:
        logger.warning("No se encontraron tokens de Telegram configurados")
    else:
        logger.info(f"Tokens de Telegram configurados para: {list(telegram_tokens.keys())}")
    
    return TelegramAdapter(message_receiver)

def get_websocket_adapter(
    message_receiver: ReceiveMessageUseCase = Depends(get_message_use_case)
) -> WebSocketAdapter:
    return WebSocketAdapter(
        message_receiver=message_receiver,
        webflux_url=os.getenv("WEBFLUX_WS_URL", "ws://webflux:8080/ws/chat")
    )
# --- NUEVA FUNCIÓN AGREGADA ---
def get_message_receiver(db: Session = None) -> IMessageReceiverPort:
    """
    Obtiene el message receiver para uso con gRPC.
    Versión alternativa que no depende del sistema de inyección de FastAPI.
    """
    """Versión modificada para gRPC que no depende de FastAPI."""
    db = db or SessionLocal()
    #if db is None:
    #        db = SessionLocal()  # Crea una nueva sesión si no se proporciona
    try:
        return ReceiveMessageUseCase(
            config_loader=get_config_loader(),
            embedding_client=get_embedding_client(),
            context_retriever=get_context_retriever(),
            llm_client=get_llm_client(),
            end_user_repo=get_end_user_repository(db),
            conversation_repo=get_conversation_repository(db),
            message_repo=get_message_repository(db)
        )
    except Exception:
        if db: db.close()  # Limpieza segura
        raise