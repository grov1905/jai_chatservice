# api/endpoints/chat.py
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket
from infrastructure.adapters.inbound.websocket_adapter import WebSocketAdapter
from infrastructure.adapters.inbound.twilio_adapter import TwilioWhatsAppAdapter
from infrastructure.adapters.inbound.telegram_adapter import TelegramAdapter
import json
    

from fastapi.responses import JSONResponse
from infrastructure.config.di import (
    get_websocket_adapter,
    get_twilio_adapter,
    get_telegram_adapter
)
import logging

router = APIRouter(tags=["Chat"])
logger = logging.getLogger(__name__)

# --- WebSocket de Desarrollo (Opcional) ---
@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    adapter: WebSocketAdapter = Depends(get_websocket_adapter)
):
    """
    Endpoint WS local para pruebas (no usar en producción con WebFlux).
    Simula el comportamiento esperado por WebFlux.
    """
    await websocket.accept()
    try:
        while True:
            # 1. Recibe mensaje en formato WebFlux
            data = await websocket.receive_json()
            # Asegura que metadata sea un diccionario
            if 'metadata' not in data or data['metadata'] is None:
                data['metadata'] = {}

            # 2. Procesa usando el mismo adapter
            response = await adapter._process_message(json.dumps(data))
            logger.info(f"response : {response}")

            # 3. Devuelve respuesta enstr(e) formato WebFlux
            await websocket.send_json(response)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()

# --- Webhooks (Sin cambios) ---
@router.post("/webhooks/twilio")
async def twilio_webhook(
    request: Request,
    adapter: TwilioWhatsAppAdapter = Depends(get_twilio_adapter)
):
    """Maneja mensajes de WhatsApp vía Twilio (sin cambios)"""
    try:
        form_data = await request.form()
        return await adapter.handle_webhook(form_data)
    except Exception as e:
        logger.error(f"Twilio error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhooks/telegram")
async def telegram_webhook(
    update: dict,
    adapter: TelegramAdapter = Depends(get_telegram_adapter)
):
    """Maneja mensajes de Telegram (sin cambios)"""
    try:
        return await adapter.handle_update(update)
    except Exception as e:
        logger.error(f"Telegram error: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(e)}
        )

@router.get("/health")
async def health_check():
    """Endpoint de salud (sin cambios)"""
    return {"status": "healthy", "service": "chat_adapter"}