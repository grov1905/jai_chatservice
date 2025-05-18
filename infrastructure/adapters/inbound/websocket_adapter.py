# infrastructure/adapters/inbound/websocket_adapter.py
import logging
import asyncio
import json
from websockets import connect, WebSocketClientProtocol
from core.ports.inbound import IMessageReceiverPort
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import os
from jose import jwt

logger = logging.getLogger(__name__)

class WebSocketAdapter:
    def __init__(
        self,
        message_receiver: IMessageReceiverPort,
        webflux_url: str = os.getenv("WS_WEBFLUX_URL", "ws://webflux:8080/ws/chat"),
        reconnect_delay: int = int(os.getenv("RECONNECT_DELAY_SECONDS", "5"))  # Valor por defecto 5
        
    ):
        self.message_receiver = message_receiver
        self.webflux_url = webflux_url
        self.reconnect_delay = reconnect_delay
        self.connection: Optional[WebSocketClientProtocol] = None

    def _generate_jwt(self):
        """Genera token JWT para autenticación"""
        now = datetime.utcnow()
        payload = {
            "sub": "chatservice",
            "iss": os.getenv("JWT_ISSUER"),
            "aud": os.getenv("WEBFLUX_JWT_AUDIENCE"),
            "iat": now,
            "exp": now + timedelta(minutes=int(os.getenv("JWT_EXPIRE_MINUTES"))),
            "roles": ["SERVICE"]
        }
        return jwt.encode(
            payload,
            os.getenv("JWT_SECRET"),
            algorithm=os.getenv("JWT_ALGORITHM")
        )
    
    async def connect(self):
        """Conexión con autenticación JWT"""
        while True:
            try:
                token = self._generate_jwt()
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Sec-WebSocket-Protocol": "access_token"
                }
                
                logger.info(f"Conectando a {self.webflux_url} con JWT...")
                async with connect(
                    self.webflux_url,
                    extra_headers=headers,
                    ping_interval=30,
                    ping_timeout=90,
                    close_timeout=10
                ) as self.connection:
                    await self._listen_messages()

            except Exception as e:
                logger.error(f"Error de conexión: {str(e)}. Reconectando en {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)

    async def _listen_messages(self):
        """Escucha mensajes entrantes"""
        try:
            async for message in self.connection:
                await self._process_message(message)
        except Exception as e:
            logger.error(f"Error en listener: {str(e)}")
            raise

    async def _process_message(self, message: str):
        """Procesa un mensaje entrante"""
        try:
            data = json.loads(message)
           # meta=data.get('metadata')

            response = await self.message_receiver.handle_new_message(
                channel=data["channel"],
                external_id=data["external_id"],
                business_id=data["business_id"],
                message_content=data["content"],
                metadata=data.get("metadata", {}) or {}
            )
            
            # Desempaquetamos la tupla response
            end_user, conversation, user_message = response
            #logger.info(f'end_user: {end_user}')
            #logger.info(f'conversation: {conversation}')
            #logger.info(f'message: {user_message}')
            response =  {
                    "external_id": data["external_id"],
                    "end_user_id": str(end_user.id),
                    "conversation_id": str(conversation.id),  # Convertir UUID a string
                    "content": user_message.content if user_message else "No se recibió respuesta del bot",
                    "metadata": {
                        "user_id": str(end_user.id),
                        "message_id": str(user_message.id)
                    }
                }
            
            return response
        
            """await self._send_response(
                {
                    "type": "bot_response",
                    "sessionId": data["external_id"],
                    "content": user_message.content if user_message else "No se recibió respuesta del bot",
                    "conversationId": str(conversation.id),  # Convertir UUID a string
                    "metadata": {
                        "user_id": str(end_user.id),
                        "message_id": str(user_message.id)
                    }
                }
            )
            """
        except json.JSONDecodeError:
            logger.error("Mensaje JSON inválido de WebFlux")
        except KeyError as e:
            logger.error(f"Falta campo requerido: {str(e)}")
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")

    async def _send_response(self, response: Dict[str, Any]):
        """Envía respuesta a WebFlux"""
        logger.info(f'response: {response}')
        if self.connection:
            try:
                await self.connection.send(json.dumps(response))
                logger.debug("Respuesta enviada a WebFlux")
            except Exception as e:
                logger.error(f"Error enviando respuesta: {str(e)}")