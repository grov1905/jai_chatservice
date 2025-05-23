#core/use_cases/receive_message.py
import logging
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Tuple
from core.domain.entities import EndUser, Conversation, Message
from core.ports.inbound import IMessageReceiverPort
from core.ports.outbound import (
    IConfigLoaderPort,
    IEmbeddingClientPort,
    IContextRetrieverPort,
    ILLMClientPort,
    IEndUserRepository,
    IConversationRepository,
    IMessageRepository
)

logger = logging.getLogger(__name__)

class ReceiveMessageUseCase(IMessageReceiverPort):
    def __init__(
        self,
        config_loader: IConfigLoaderPort,
        embedding_client: IEmbeddingClientPort,
        context_retriever: IContextRetrieverPort,
        llm_client: ILLMClientPort,
        end_user_repo: IEndUserRepository,
        conversation_repo: IConversationRepository,
        message_repo: IMessageRepository
    ):
        self.config_loader = config_loader
        self.embedding_client = embedding_client
        self.context_retriever = context_retriever
        self.llm_client = llm_client
        self.end_user_repo = end_user_repo
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.logger = logging.getLogger(__name__)
        self.identified_channels = {
            'whatsapp', 
            'telegram', 
            'facebook', 
            'instagram'
        }

    async def handle_new_message(
        self, 
        channel: str,
        external_id: str,
        business_id: str,
        message_content: str,
        metadata: dict = {}
    ) -> Tuple[EndUser, Conversation, Message]:
        # 1. Get or create EndUser
        logger.info("# 1. Get or create EndUser")

        end_user = await self._get_or_create_end_user(
            external_id, channel, business_id, metadata
        )
        
        # 2. Get or create Conversation
        logger.info("#2. Get or create Conversation")

        conversation = await self._get_or_create_conversation(
            end_user.id, business_id, channel
        )
        
        # 3. Create and save Message
        logger.info("3. Create and save Message")

        message = Message(
            id=uuid4(),
            conversation_id=conversation.id,
            sender_type="user",
            content=message_content,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
        await self.message_repo.create(message)
        
        # 4. Process message and generate response
        logger.info("4. Process message and generate response")
        message=await self._process_message(message, business_id)

        return end_user, conversation, message
    
    async def _get_or_create_end_user(
        self, 
        external_id: str, 
        channel: str, 
        business_id: str,
        metadata: dict
    ) -> EndUser:
        logger.info(f"channel: {channel}")
        normalized_id = self._normalize_external_id(external_id, channel)
        normalized_id = external_id
        logger.info(f'normalized_id: {normalized_id}')
        end_user = await self.end_user_repo.get_by_external_id(
            normalized_id, channel, business_id
        )
        
        if not end_user:
            is_anonymous = channel not in self.identified_channels

            new_user = EndUser(
                id=uuid4(),
                business_id=business_id,
                external_id=normalized_id,
                channel=channel,
                phone_number=metadata.get("phone_number"),
                metadata={
                    **metadata,
                    "is_anonymous": is_anonymous,
                    "original_external_id": external_id
                }
            )
            end_user = await self.end_user_repo.create(new_user)
        
        return end_user
    
    async def _get_or_create_conversation(
        self, 
        end_user_id: str, 
        business_id: str,
        channel: str
    ) -> Conversation:
        # Check for active conversation within threshold
        conversation = await self.conversation_repo.get_active_by_user(
            end_user_id, business_id
        )
        
        if not conversation:
            new_conversation = Conversation(
                id=uuid4(),
                end_user_id=end_user_id,
                business_id=business_id,
                channel=channel,
                started_at=datetime.utcnow(),
                is_active=True
            )
            conversation = await self.conversation_repo.create(new_conversation)
        
        return conversation
    
    async def _process_message(self, message: Message, business_id: str) -> Message:
        try:
            # 1. Load bot configuration
            bot_config = await self.config_loader.load_bot_config(business_id)
            """  chunk_settings = await self.config_loader.load_chunk_settings(
                business_id, "message"
            )  """
            
            # 2. Vectorize message
            vector = await self.embedding_client.vectorize_text(
                message.content,
                bot_config["embedding_model_name"]
            )
            
            # 3. Retrieve relevant context
            context = await self.context_retriever.retrieve_document_context(
                vector,
                business_id,
                bot_config["search_top_k"],
                bot_config["search_min_similarity"]
            )
            
            # 4. Get response template
            template = await self.config_loader.load_bot_template(
                business_id, "other"
            )


            logger.info(f"Generate response: ")
            # 5. Generate response
            prompt_template=template["prompt_template"]
            model_namerar=bot_config["llm_model_name"]
            temperaturerar=template["temperature"]
            top_prar=template["top_p"]
            frequency_penaltyrar=template["frequency_penalty"]
            presence_penaltyrar=template["presence_penalty"]


            promptrar=self._build_prompt(message.content, context, prompt_template)
            logger.info(f"promptrar: {promptrar}")

            response = await self.llm_client.generate_response(
                prompt=promptrar,
                model_name=model_namerar,
                temperature=temperaturerar,
                top_p=top_prar,
                frequency_penalty=frequency_penaltyrar,
                presence_penalty=presence_penaltyrar
            )

          #  logger.info(f"response llma: {response}")

            # 6. Save and return bot response
            bot_message = Message(
                id=uuid4(),
                conversation_id=message.conversation_id,
                sender_type="bot",
                content=response,
                timestamp=datetime.utcnow()
            )
            await self.message_repo.create(bot_message)

            

            return bot_message
        
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            raise
    
    def _build_prompt(self, message: str, context: dict, prompt_template: str) -> str:
        # 1. Extrae los resultados del contexto
        results = context.get('results', [])
        
        # 2. Valida la estructura
        if not isinstance(results, list):
            self.logger.error(f"Invalid context format: {context}")
            raise ValueError("Context must contain a 'results' list")
        
        # 3. Construye el string de contexto
        context_str = "\n".join([
            str(item.get('content', '')) 
            for item in results 
            if isinstance(item, dict)
        ])
        
        self.logger.info(f"Context str: {context_str}")
        
        # 4. Formatea el prompt final
        try:
            return prompt_template.format(
                message=message,
                context=context_str
            )
        except KeyError as e:
            self.logger.error(f"Missing key in prompt template: {e}")
            raise ValueError("Invalid prompt template format") from e
    
    def _normalize_external_id(self, external_id: str, channel: str) -> str:
        """Normaliza IDs solo para canales en identified_channels"""
        # Primero normaliza el nombre del canal (minúsculas, sin espacios)
        normalized_channel = channel.lower().strip()
    
        # Solo procesa si está en la lista blanca
        if normalized_channel in self.identified_channels:
            logger.info(f'esta en la lista: {normalized_channel}')
            # Verifica si ya tiene el prefijo
            if not external_id.startswith(f"{normalized_channel}:"):
                logger.info(f'no viene con prefijo: {external_id}')
                external_id=f"{normalized_channel}:{external_id}"
                #return f"{normalized_channel}:{external_id}"

        # Para cualquier otro caso, devuelve el original
        return external_id