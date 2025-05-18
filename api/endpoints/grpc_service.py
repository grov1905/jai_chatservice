from concurrent import futures
import grpc
import logging
from typing import Any
from uuid import UUID
from core.domain.entities import EndUser, Conversation, Message
from core.ports.inbound import IMessageReceiverPort
from proto import chat_pb2, chat_pb2_grpc
from google.protobuf.json_format import MessageToDict


class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self, message_receiver: IMessageReceiverPort):
        self.message_receiver = message_receiver
        self.logger = logging.getLogger(__name__)

    async def ProcessMessage(
        self, 
        request: chat_pb2.ChatRequest, 
        context: Any
    ) -> chat_pb2.ChatResponse:
        try:
            self.logger.info(f'request: {request}')
            # Convert metadata to dict
            metadata = dict(request.metadata)
            
            # Handle the message
            end_user, conversation, message = await self.message_receiver.handle_new_message(
                channel=request.channel,
                external_id=request.external_id,
                business_id=request.business_id,
                message_content=request.content,
                metadata=metadata
            )
            
            return chat_pb2.ChatResponse(
                content=message.content,
                conversation_id=str(conversation.id),
                end_user_id=str(end_user.id)
            )
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return chat_pb2.ChatResponse()

def serve(port: int = 50051, message_receiver: IMessageReceiverPort = None):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(
        ChatService(message_receiver), server
    )
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    server.wait_for_termination()