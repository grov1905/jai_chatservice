# infrastructure/adapters/inbound/telegram_adapter.py
from typing import Dict, Any
from core.ports.inbound import IMessageReceiverPort

class TelegramAdapter:
    def __init__(self, message_receiver: IMessageReceiverPort):
        self.message_receiver = message_receiver

    async def handle_update(self, update: Dict[str, Any]) -> Dict[str, str]:
        message = update.get("message", {})
        message_content = message.get("text", "")
        chat = message.get("chat", {})
        external_id = str(chat.get("id", ""))
        metadata = {
            "telegram_data": update,
            "username": chat.get("username")
        }
        
        try:
            response = await self.message_receiver.handle_new_message(
                channel="telegram",
                external_id=external_id,
                business_id="business_id_from_config",
                message_content=message_content,
                metadata=metadata
            )
            return {"response": response}
        except Exception as e:
            return {"error": str(e)}