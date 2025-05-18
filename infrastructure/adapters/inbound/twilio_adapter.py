# infrastructure/adapters/inbound/twilio_adapter.py
from fastapi import Request, HTTPException
from core.ports.inbound import IMessageReceiverPort
from typing import Dict, Any

class TwilioWhatsAppAdapter:
    def __init__(self, message_receiver: IMessageReceiverPort):
        self.message_receiver = message_receiver

    async def handle_webhook(self, request: Request) -> Dict[str, str]:
        form_data = await request.form()
        
        # Mapeo de campos específicos de Twilio
        message_content = form_data.get("Body", "")
        external_id = form_data.get("From", "")
        metadata = {
            "phone_number": external_id,
            "twilio_data": dict(form_data)
        }
        
        try:
            message = await self.message_receiver.handle_new_message(
                channel="whatsapp",
                external_id=external_id,
                business_id="business_id_from_config",  # Deberías obtener esto de tu configuración
                message_content=message_content,
                metadata=metadata
            )
            return {"status": "success", "response": message.content}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))