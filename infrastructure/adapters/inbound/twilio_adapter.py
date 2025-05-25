# CAMBIO MÍNIMO 2: infrastructure/adapters/inbound/twilio_adapter.py
from fastapi import Request, HTTPException
from core.ports.inbound import IMessageReceiverPort
from typing import Dict, Any, Optional
import os
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

class TwilioWhatsAppAdapter:
    def __init__(self, message_receiver: IMessageReceiverPort):
        self.message_receiver = message_receiver
        # Variables de entorno globales (una sola cuenta Twilio)
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.default_whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        
        if not self.account_sid or not self.auth_token:
            raise ValueError("TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN son requeridos")
            
        self.client = Client(self.account_sid, self.auth_token)
        logger.info(f"TwilioWhatsAppAdapter inicializado")

    # CAMBIO: Agregar parámetro whatsapp_from
    async def handle_webhook(self, 
                        form_data: Dict[str, Any], 
                        business_id: str, 
                        whatsapp_from: str = None) -> Dict[str, str]:
        """
        Maneja el webhook de Twilio con business_id y número específico
        """
        try:
            message_content = form_data.get("Body", "")
            external_id = form_data.get("From", "")
            message_sid = form_data.get("MessageSid", "")
            
            if not message_content.strip():
                return {"status": "ignored", "reason": "empty_message"}
                
            if not external_id:
                raise HTTPException(status_code=400, detail="From field is required")

            external_id = external_id.replace(" ", "+")  # Eliminar espacios si existen
            if not external_id.startswith("whatsapp:+"):
                external_id = f"whatsapp:+{external_id.split(':')[-1].lstrip('+')}"


            clean_phone = external_id.replace("whatsapp:", "")
            
            metadata = {
                "phone_number": clean_phone,
                "original_from": external_id,
                "message_sid": message_sid,
                "channel": "whatsapp",
                "platform": "twilio",
                "business_id": business_id,
                "whatsapp_from": whatsapp_from,  # NUEVO: Incluir número del negocio
                "twilio_data": dict(form_data)
            }
            
            logger.info(f"Procesando mensaje - Business: {business_id}, From: {clean_phone}, Business Number: {whatsapp_from}")
            
            message = await self.message_receiver.handle_new_message(
                channel="whatsapp",
                external_id=external_id,
                business_id=business_id,
                message_content=message_content,
                metadata=metadata
            )
            
            end_user, conversation, message = message

            # CAMBIO: Usar el número específico del negocio para responder
            if message and message.content:
                business_number = whatsapp_from or self.default_whatsapp_from
                await self.send_whatsapp_message(clean_phone, message.content, from_number=business_number)
            
            return {
                "status": "success", 
                "response": message.content if message else "Mensaje procesado",
                "business_id": business_id,
                "whatsapp_from": whatsapp_from
            }
            
        except Exception as e:
            logger.error(f"Error procesando webhook de Twilio: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    # CAMBIO: Agregar parámetro from_number
    async def send_whatsapp_message(self, to_phone: str, message_content: str, from_number: str = None) -> bool:
        """
        Envía mensaje de WhatsApp usando número específico del negocio
        """
        try:
            if not to_phone.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_phone}"
            else:
                to_number = to_phone
            
            # Usar número específico del negocio o el default
            send_from = from_number or self.default_whatsapp_from
                
            message = self.client.messages.create(
                body=message_content,
                from_=send_from,  # CAMBIO: Usar número del negocio
                to=to_number
            )
            
            logger.info(f"Mensaje enviado exitosamente - SID: {message.sid}, From: {send_from}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando mensaje de WhatsApp: {str(e)}")
            return False

    def validate_webhook(self, request_url: str, form_data: Dict[str, Any], signature: str) -> bool:
        try:
            from twilio.request_validator import RequestValidator
            validator = RequestValidator(self.auth_token)
            return validator.validate(request_url, form_data, signature)
        except ImportError:
            logger.warning("twilio request validator no disponible - saltando validación")
            return True
        except Exception as e:
            logger.error(f"Error validando webhook: {str(e)}")
            return False

# CONFIGURACIÓN EN TWILIO CONSOLE:
"""
Una sola cuenta Twilio con múltiples números:

Número 1 (Restaurante):
- Número: +1-415-555-1111
- Webhook: https://tuapp.com/webhooks/twilio?business_id=restaurante_pizza&whatsapp_from=whatsapp:+14155551111

Número 2 (Clínica):
- Número: +1-415-555-2222  
- Webhook: https://tuapp.com/webhooks/twilio?business_id=clinica_dental&whatsapp_from=whatsapp:+14155552222

Número 3 (Tienda):
- Número: +1-415-555-3333
- Webhook: https://tuapp.com/webhooks/twilio?business_id=tienda_ropa&whatsapp_from=whatsapp:+14155553333
"""