#!/usr/bin/env python3
"""
run_fastapi.py

Punto de entrada del servidor FastAPI + WebSockets.
Backend web para Bot Lola.
"""

import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

# Imports locales
from database.database_pool import DatabasePool, ConversationRepository
from core.state_machine import ConversationManager
from core.core_handler import LolaCoreHandler
from services.security import SecurityManager
from services.payment_validator import PaymentValidator
# HybridPaymentValidator disabled for Railway deployment (requires easyocr)
# Audio transcription temporarily disabled for Railway deployment
# from services.audio_transcriber import AudioTranscriber
from services.content_delivery import ContentDeliveryService
from storage.redis_store import RedisStateStore
from api.websocket.connection_manager import ConnectionManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración desde .env
DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Instancias globales (compartidas entre requests)
db_pool: DatabasePool = None
redis_store: RedisStateStore = None
core_handler: LolaCoreHandler = None
connection_manager: ConnectionManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida del servidor.
    Inicializa recursos al arrancar, los libera al cerrar.
    """
    global db_pool, redis_store, core_handler, connection_manager
    
    logger.info("🚀 Iniciando Bot Lola - Backend FastAPI...")
    
    # 1. Conectar a PostgreSQL
    db_pool = DatabasePool(DATABASE_URL)
    await db_pool.initialize()
    logger.info("✅ PostgreSQL conectado")
    
    # 2. Conectar a Redis con respaldo PostgreSQL
    redis_store = RedisStateStore(
        redis_url=REDIS_URL,
        db_pool=db_pool.pool  # NUEVO: Activar respaldo automático
    )
    await redis_store.connect()
    logger.info("✅ Redis conectado con respaldo PostgreSQL")
    
    # 3. Inicializar servicios
    conversation_manager = ConversationManager()
    security_manager = SecurityManager()
    payment_validator = PaymentValidator(
        gemini_api_key=GEMINI_API_KEY,
        db_pool=db_pool.pool  # For anti-fraude P-Hash
    )
    content_delivery = ContentDeliveryService()  # Uses Backblaze B2 from env vars
    logger.info("✅ PaymentValidator (Gemini Vision) inicializado")
    
    # 3.5. Inicializar Telegram Notifier (opcional)
    telegram_notifier = None
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        from services.telegram_notifier import TelegramNotifier
        telegram_notifier = TelegramNotifier(
            bot_token=TELEGRAM_BOT_TOKEN,
            chat_id=TELEGRAM_CHAT_ID
        )
        logger.info("✅ Telegram Notifier habilitado")
    else:
        logger.warning("⚠️ Telegram Notifier no configurado (variables faltantes)")
    
    # 4. Inicializar CoreHandler (cerebro del bot)
    core_handler = LolaCoreHandler(
        db_pool=db_pool,
        conversation_manager=conversation_manager,
        security_manager=security_manager,
        payment_validator=payment_validator,
        content_delivery=content_delivery,
        redis_store=redis_store,
        gemini_api_key=GEMINI_API_KEY,
        audio_transcriber=None,  # Disabled for Railway
        telegram_notifier=telegram_notifier  # Optional
    )
    logger.info("✅ LolaCoreHandler inicializado")
    
    # 5. Inicializar ConnectionManager (WebSocket)
    connection_manager = ConnectionManager()
    logger.info("✅ ConnectionManager inicializado")
    
    logger.info("🎉 Bot Lola - Backend listo y operativo")
    
    yield  # Servidor corriendo
    
    # Cleanup al cerrar
    logger.info("🛑 Cerrando Bot Lola...")
    await db_pool.close()
    await redis_store.disconnect()
    logger.info("✅ Recursos liberados")


# Crear aplicación FastAPI
app = FastAPI(
    title="Bot Lola API",
    description="Backend para chat privado de Lola Jiménez",
    version="2.0.0",
    lifespan=lifespan
)

# Configurar CORS (permitir frontend React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://lola-jimenez.studio", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar archivos estáticos del frontend Next.js (exportación estática)
frontend_path = Path(__file__).parent.parent / "frontend"
logger.info(f"🔍 DEBUG - Frontend path: {frontend_path}, exists: {frontend_path.exists()}")
if frontend_path.exists():
    # Montar _next para recursos de exportación estática
    next_path = frontend_path / "out" / "_next"
    if next_path.exists():
        app.mount("/_next", StaticFiles(directory=str(next_path)), name="next_static")
        logger.info(f"✅ Mounted /_next from {next_path}")
    
    # Montar images desde public/images (Next.js no copia /public a /out en static export)
    images_path = frontend_path / "public" / "images"
    logger.info(f"🔍 DEBUG - Images path: {images_path}, exists: {images_path.exists()}")
    if images_path.exists():
        image_files = list(images_path.glob("*.webp"))
        logger.info(f"🔍 DEBUG - Found {len(image_files)} .webp files: {[f.name for f in image_files]}")
        app.mount("/images", StaticFiles(directory=str(images_path)), name="images")
        logger.info(f"✅ Mounted /images from {images_path}")
    else:
        logger.error(f"❌ Images directory NOT FOUND: {images_path}")
    
    # Montar public para assets públicos
    public_path = frontend_path / "public"
    if public_path.exists():
        app.mount("/public", StaticFiles(directory=str(public_path)), name="public")
        logger.info(f"✅ Mounted /public from {public_path}")


# ==================== ENDPOINTS REST ====================

@app.get("/")
async def root():
    """Servir frontend Next.js (exportación estática)"""
    static_index = Path(__file__).parent.parent / "frontend" / "out" / "index.html"
    
    # Si existe el HTML estático, servirlo
    if static_index.exists():
        return FileResponse(static_index)
    
    # Fallback a respuesta JSON si no hay frontend
    return {"status": "ok", "message": "Bot Lola API v2.0", "note": "Frontend not built"}


@app.get("/health")
async def health():
    """Health check endpoint for Railway"""
    return {"status": "ok"}


@app.get("/api/health")
async def health_check():
    """Health check detallado"""
    redis_ok = await redis_store.health_check()
    
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected" if redis_ok else "error",
        "active_connections": len(connection_manager.get_active_users())
    }


@app.get("/api/history/{user_identifier}")
async def get_conversation_history(user_identifier: str, limit: int = 20):
    """
    Obtiene historial de conversación de un usuario.

    Args:
        user_identifier: Identificador único del usuario web
        limit: Número máximo de mensajes a retornar
    """
    try:
        repo = ConversationRepository(db_pool)

        # Obtener o crear user_id numérico desde user_identifier
        user_id = await repo.get_or_create_user_by_identifier(user_identifier)

        # Obtener historial con user_id numérico
        history = await repo.get_conversation_history(user_id, limit)

        return {
            "user_identifier": user_identifier,
            "messages": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Error obteniendo historial de {user_identifier}: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo historial")


# ==================== ENDPOINT WEBSOCKET ====================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    Endpoint WebSocket para chat en tiempo real.
    
    Protocolo JSON:
    - Recibe: {"type": "text|image", "content": "..."}
    - Envía: {"type": "text|image", "content": "...", "url": "...", "caption": "..."}
    
    Args:
        user_id: UUID único del usuario (generado por frontend)
    """
    await connection_manager.connect(websocket, user_id)
    
    try:
        # NO enviar mensaje automático - Lola espera que el usuario inicie
        # (Fix ERROR-C1: mensaje proactivo rompía naturalidad)
        
        # Loop principal: recibir y procesar mensajes
        while True:
            # Recibir mensaje como JSON
            try:
                data = await websocket.receive_json()
                msg_type = data.get("type", "text")
                content = data.get("content", "")
            except Exception:
                # Fallback: si no es JSON válido, intentar como texto plano
                raw_data = await websocket.receive_text()
                msg_type = "text"
                content = raw_data
            
            logger.info(f"Mensaje [{msg_type}] recibido de {user_id}: {str(content)[:50]}...")
            
            if msg_type == "text":
                # Procesar mensaje de texto normal
                response = await core_handler.process_text_message(user_id, content)
                
                # Detectar si la respuesta incluye una URL de contenido (entrega de producto)
                if "lola-content" in response or "b2.backblazeb2.com" in response:
                    # Extraer URL de la respuesta
                    import re
                    url_match = re.search(r'https://[^\s]+', response)
                    if url_match:
                        image_url = url_match.group(0)
                        # Enviar texto primero
                        caption = response.replace(image_url, "").strip()
                        await connection_manager.send_personal_message(
                            message="mira lo que tengo para ti 😏",
                            user_id=user_id,
                            msg_type="text"
                        )
                        # Luego enviar imagen inline
                        await connection_manager.send_personal_message(
                            message=caption,
                            user_id=user_id,
                            msg_type="image",
                            image_url=image_url,
                            caption="espero te guste 🫣"
                        )
                    else:
                        # No hay URL, enviar como texto normal
                        await connection_manager.send_personal_message(response, user_id)
                else:
                    # Respuesta de texto normal
                    await connection_manager.send_personal_message(response, user_id)
            
            elif msg_type == "image":
                # Usuario envió imagen (probablemente comprobante de pago)
                image_data = content  # Base64 o URL de la imagen
                
                # Guardar imagen temporalmente para validación
                import base64
                import tempfile
                import os
                
                try:
                    # Decodificar base64 y guardar como archivo temporal
                    if image_data.startswith("data:image"):
                        # Formato data URL: data:image/jpeg;base64,/9j/4AAQ...
                        image_data = image_data.split(",")[1]
                    
                    image_bytes = base64.b64decode(image_data)
                    
                    # Crear archivo temporal
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                        tmp_file.write(image_bytes)
                        temp_path = tmp_file.name
                    
                    logger.info(f"Imagen guardada temporalmente: {temp_path}")
                    
                    # Procesar imagen como comprobante de pago
                    response = await core_handler.process_photo_message(user_id, temp_path)
                    
                    # Limpiar archivo temporal
                    os.unlink(temp_path)
                    
                    # Aplicar delay realista (igual que texto)
                    import asyncio
                    from core.core_handler import calculate_typing_delay
                    delay = calculate_typing_delay(response)
                    logger.info(f"Aplicando delay realista para imagen: {delay}s")
                    await asyncio.sleep(delay)
                    
                    # Enviar respuesta
                    await connection_manager.send_personal_message(response, user_id)
                    
                except Exception as e:
                    logger.error(f"Error procesando imagen de {user_id}: {e}")
                    await connection_manager.send_personal_message(
                        "Ay, no pude ver bien tu imagen. Intenta de nuevo porfa 📸",
                        user_id
                    )
            else:
                # Tipo no reconocido
                logger.warning(f"Tipo de mensaje no reconocido: {msg_type}")
                await connection_manager.send_personal_message(
                    "No entendí eso haha, mejor escríbeme 💬",
                    user_id
                )
    
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id)
        logger.info(f"Usuario {user_id} desconectado normalmente")
    
    except Exception as e:
        logger.error(f"Error en WebSocket de {user_id}: {e}")
        connection_manager.disconnect(user_id)


# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    import uvicorn
    
    # Configuración de Uvicorn
    uvicorn.run(
        "run_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload en desarrollo
        log_level="info"
    )
