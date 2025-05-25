# main.py
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from infrastructure.config.database import init_db
from infrastructure.config.di import get_websocket_adapter
from infrastructure.config.di import get_message_receiver
from api.endpoints.chat import router as chat_router
import grpc
from concurrent import futures
from proto import chat_pb2_grpc
from infrastructure.adapters.inbound.grpc_server import ChatServiceServicer 
 
# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="JAI ChatService",
    description="Core de Chatbot Omnicanal",
    version="1.0.0"
)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir endpoints REST (webhooks)
app.include_router(chat_router, prefix="/api/v1")

# Agregar esta función

async def start_grpc_server():
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.so_reuseport', 1),
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024)
        ]
    )
    message_receiver = get_message_receiver()
    chat_pb2_grpc.add_ChatServiceServicer_to_server(
        ChatServiceServicer(message_receiver), server)
    
    listen_addr = '[::]:50051'
    # Cambiar a 0.0.0.0 explícitamente
    server.add_insecure_port(listen_addr)
    await server.start()
    logger.info(f"gRPC server started on {listen_addr}")
    #await server.wait_for_termination()  # Esto mantendrá el servidor corriendo
    return server


@app.on_event("startup")
async def startup_event():
    """Inicialización del servicio"""
    global grpc_server
    try:
        # 1. Base de datos
        init_db()
        logger.info("Base de datos inicializada")
        
        # 2. Iniciar servidor gRPC
        grpc_server = await start_grpc_server()
        logger.info("Servidor gRPC iniciado")

        # 3. Cliente WebSocket para WebFlux
        websocket_adapter = get_websocket_adapter()

        # Tarea en segundo plano para conexión persistente
        asyncio.create_task(
            websocket_adapter.connect(),
            name="webflux_ws_connection"
        ) 

        logger.info("Servicio iniciado completamente")

    except Exception as e:
        logger.error(f"Error en startup: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al apagar"""
    try:
        if grpc_server:
            await grpc_server.stop(grace=5)
            logger.info("Servidor gRPC detenido")
        
        logger.info("Servicio apagado correctamente")
    except Exception as e:
        logger.error(f"Error en shutdown: {str(e)}")

# Health Check adicional
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "services": {
            "database": "active",
            "webflux_connection": "active"
        }
    }

# Punto de entrada principal
if __name__ == "__main__":
    # Para desarrollo local
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )