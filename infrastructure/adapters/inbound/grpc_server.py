# infrastructure/adapters/inbound/grpc_server.py
import grpc
from concurrent import futures
from proto import chat_pb2, chat_pb2_grpc
from core.ports.inbound import IMessageReceiverPort
from infrastructure.config.database import SessionLocal  # Importa SessionLocal directamente

import logging

logger = logging.getLogger(__name__)

class ChatServiceServicer(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self,message_receiver: IMessageReceiverPort):
        # Crea una sesión de DB directamente (sin Depends)
        self.message_receiver = message_receiver  
        self.db = SessionLocal()
    async def ProcessMessage(self, request, context):
        try:
            logger.info(f'channel: {request.channel}')
            logger.info(f'external_id: {request.external_id}')
            logger.info(f'business_id: {request.business_id}')
            logger.info(f'message_content: {request.content}')
            logger.info(f'metadata: {dict(request.metadata)}')

            response = await self.message_receiver.handle_new_message(
                channel=request.channel,
                external_id=request.external_id,
                business_id=request.business_id,
                message_content=request.content,
                metadata=dict(request.metadata)
            )

            end_user, conversation, message = response
            
            self.db.commit()
            return chat_pb2.ChatResponse(
                external_id=request.external_id,
                content=message.content,
                conversation_id=str(conversation.id),
                end_user_id= str(end_user.id)
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"gRPC error: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chat_pb2.ChatResponse()
        finally:
            self.db.close()