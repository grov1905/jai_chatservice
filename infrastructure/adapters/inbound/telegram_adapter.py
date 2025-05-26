# infrastructure/adapters/inbound/telegram_adapter.py
import os
import aiohttp
from typing import Dict, Any
from core.ports.inbound import IMessageReceiverPort
import logging

logger = logging.getLogger(__name__)

class TelegramAdapter:
    def __init__(self, message_receiver: IMessageReceiverPort):
        self.message_receiver = message_receiver
    
    def _get_bot_token(self, business_id: str) -> str:
        """Obtiene el token del bot para un negocio específico"""
        token_key = f"TELEGRAM_TOKEN_{business_id}"
        #logger.info(f"Token key: {token_key}")
        token = os.getenv(token_key)

        if not token:
            raise ValueError(f"Token de Telegram no configurado para negocio: {business_id}")
        #logger.info(f"Token de Telegram: {token}")
        return token
    
    async def handle_update(self, update: Dict[str, Any], business_id: str) -> Dict[str, str]:
        """
        Procesa un update de Telegram para un negocio específico
        """
        try:
            # Extraer información del mensaje
            message = update.get("message", {})
            callback_query = update.get("callback_query", {})
            
            # Determinar si es mensaje o callback
            if message:
                message_content = message.get("text", "")
                chat = message.get("chat", {})
                user = message.get("from", {})
                external_id = str(chat.get("id", ""))
                username = user.get("username", "")
                first_name = user.get("first_name", "")
                last_name = user.get("last_name", "")
            elif callback_query:
                message_content = callback_query.get("data", "")
                chat = callback_query.get("message", {}).get("chat", {})
                user = callback_query.get("from", {})
                external_id = str(chat.get("id", ""))
                username = user.get("username", "")
                first_name = user.get("first_name", "")
                last_name = user.get("last_name", "")
            else:
                return {"error": "Tipo de update no soportado"}
            
            # Crear metadata similar a WhatsApp
            metadata = {
                "telegram_data": update,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "chat_type": chat.get("type", "private"),
                "business_id": business_id
            }
            
            logger.info(f"Telegram webhook - Business: {business_id}, Chat ID: {external_id}")
            
            # Procesar mensaje usando el use case
            message = await self.message_receiver.handle_new_message(
                channel="telegram",
                external_id=external_id,
                business_id=business_id,
                message_content=message_content,
                metadata=metadata
            )

            end_user, conversation, message = message

            #logger.info(f"message: {message.content}")
            logger.info(f"Telegram webhook - Business: {business_id}, Chat ID: {external_id} - Mensaje procesado")
            # Si hay respuesta del bot, enviarla
            if hasattr(message, 'content') and message.content:
                await self._send_message(
                    business_id=business_id,
                    chat_id=external_id,
                    text=message.content
                )
            
            return {"status": "success", "message": "Procesado correctamente"}
            
        except Exception as e:
            logger.error(f"Error en Telegram webhook: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _send_message(self, business_id: str, chat_id: str, text: str):
        """
        Envía un mensaje a través de la API de Telegram
        """
        try:
            token = self._get_bot_token(business_id)
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"  # Permite formato HTML
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error enviando mensaje Telegram: {error_text}")
                    else:
                        logger.info(f"Mensaje enviado exitosamente a chat {chat_id}")
                        
        except Exception as e:
            logger.error(f"Error enviando mensaje Telegram: {str(e)}")
    
    async def send_message_external(self, business_id: str, chat_id: str, text: str):
        """
        Método público para enviar mensajes desde otros servicios
        """
        await self._send_message(business_id, chat_id, text)