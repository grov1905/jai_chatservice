# scripts/setup_telegram_webhooks.py
import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

async def setup_webhooks():
    """Configura webhooks para todos los bots de Telegram"""
    
    base_webhook_url = os.getenv("TELEGRAM_WEBHOOK_BASE_URL", "https://tuapp.com/api/v1/webhooks/telegram")
    
    # Buscar todos los tokens configurados
    telegram_tokens = {
        key.replace("TELEGRAM_TOKEN_", "").lower(): value 
        for key, value in os.environ.items() 
        if key.startswith("TELEGRAM_TOKEN_") and value
    }
    
    if not telegram_tokens:
        print("❌ No se encontraron tokens de Telegram configurados")
        return
    
    async with aiohttp.ClientSession() as session:
        for business_id, token in telegram_tokens.items():
            webhook_url = f"{base_webhook_url}?business_id={business_id}"
            api_url = f"https://api.telegram.org/bot{token}/setWebhook"
            
            payload = {
                "url": webhook_url,
                "allowed_updates": ["message", "callback_query"]
            }
            
            try:
                async with session.post(api_url, json=payload) as response:
                    result = await response.json()
                    
                    if result.get("ok"):
                        print(f"✅ Webhook configurado para {business_id}: {webhook_url}")
                    else:
                        print(f"❌ Error configurando {business_id}: {result.get('description')}")
                        
            except Exception as e:
                print(f"❌ Error conectando con {business_id}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(setup_webhooks())



""" Ejecutar el Script de Configuración
bash

python scripts/setup_telegram_webhooks.py

Probar los Bots

Busca cada bot en Telegram: @restaurante_bot, @clinica_bot, etc.
Envía un mensaje
Verifica en los logs que llegue con el business_id correcto 


Verificar Webhooks
bash# Verificar estado de webhooks
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

"""