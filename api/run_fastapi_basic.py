#!/usr/bin/env python3
"""
run_fastapi_basic.py

Servidor básico de prueba para WebSocket.
Ahora con soporte para validación de imágenes de comprobantes.
"""

import json
import logging
import os
import base64
from io import BytesIO
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# Importar PaymentValidator
from services.payment_validator import PaymentValidator

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Cargar personalidad de Lola
LOLA_PROMPT_PATH = Path(__file__).parent.parent / "docs" / "LOLA_FLASH.md"
with open(LOLA_PROMPT_PATH, "r", encoding="utf-8") as f:
    LOLA_SYSTEM_PROMPT = f.read()

logger.info("✅ Personalidad de Lola cargada desde LOLA.md")

# Inicializar PaymentValidator
payment_validator = PaymentValidator(
    gemini_api_key=GEMINI_API_KEY,
    expected_amount=None  # Se define dinámicamente
)
logger.info("✅ PaymentValidator inicializado")

# Crear aplicación FastAPI
app = FastAPI(
    title="Bot Lola API (Gemini AI)",
    description="Servidor con Gemini AI para respuestas naturales",
    version="1.1.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://lola-jimenez.studio"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Gestor simple de conexiones
class SimpleConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.conversation_history: dict[str, list] = {}  # Historial por usuario
        
        # Configurar modelo Gemini
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",  # Optimizado para conversación (75% más barato)
            system_instruction=LOLA_SYSTEM_PROMPT
        )

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
        # Inicializar historial si es nuevo usuario
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        logger.info(f"✅ Usuario {user_id} conectado. Total: {len(self.active_connections)}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"❌ Usuario {user_id} desconectado")

    async def send_message(self, user_id: str, content: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json({"content": content})
    
    async def process_image_base64(self, user_id: str, base64_image: str) -> str:
        """Procesa una imagen en Base64 y valida el comprobante de pago"""
        try:
            logger.info(f"🖼️  Procesando imagen de usuario {user_id}")
            
            # 1. Decodificar Base64
            try:
                # Remover prefijo data:image si existe
                if "," in base64_image:
                    base64_image = base64_image.split(",")[1]
                
                image_bytes = base64.b64decode(base64_image)
                logger.info(f"📊 Tamaño de imagen: {len(image_bytes)} bytes ({len(image_bytes)/1024/1024:.2f} MB)")
            except Exception as e:
                logger.error(f"Error decodificando Base64: {e}")
                return "mmm esa imagen no se ve bien. me la mandas de nuevo?"
            
            # 2. Validar tamaño (5 MB máximo)
            MAX_SIZE = 5 * 1024 * 1024  # 5 MB
            if len(image_bytes) > MAX_SIZE:
                logger.warning(f"Imagen muy grande: {len(image_bytes)} bytes")
                return "uff esa imagen está muy pesada. mándame una más ligera porfa."
            
            # 3. Validar que sea una imagen válida
            try:
                image = Image.open(BytesIO(image_bytes))
                image.verify()  # Verificar que no esté corrupta
                logger.info(f"✅ Imagen válida - Formato: {image.format}, Tamaño: {image.size}")
            except Exception as e:
                logger.error(f"Imagen inválida o corrupta: {e}")
                return "mmm esa imagen no se ve bien. te sale la transferencia completa?"
            
            # 4. Guardar temporalmente en BytesIO para PaymentValidator
            # PaymentValidator espera un path, así que creamos archivo temporal
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(image_bytes)
                tmp_path = tmp_file.name
            
            logger.info(f"💾 Imagen guardada temporalmente en: {tmp_path}")
            
            # 5. Validar con PaymentValidator
            try:
                logger.info("🔍 Iniciando validación con Gemini Vision...")
                validation_result = payment_validator.validate_payment_proof(
                    image_path=tmp_path,
                    expected_amount=None,  # No validamos monto específico por ahora
                    expected_currency="MXN"
                )
                
                logger.info(f"📋 Resultado de validación: {validation_result}")
                
                # 6. Interpretar resultado y responder como Lola
                is_valid = validation_result.get("is_valid", False)
                confidence = validation_result.get("confidence", 0.0)
                extracted_data = validation_result.get("extracted_data", {})
                fraud_indicators = validation_result.get("fraud_indicators", [])
                
                logger.info(f"✓ Válido: {is_valid} | Confianza: {confidence:.2f} | Fraude: {fraud_indicators}")
                
                # Respuestas según personalidad de Lola
                if is_valid and confidence >= 0.7:
                    # VÁLIDO - Respuesta positiva
                    amount = extracted_data.get("amount", "N/A")
                    logger.info(f"✅ COMPROBANTE VÁLIDO - Monto: {amount}")
                    return "perfecto. ahí quedó registrado. te mando tu contenido"
                
                elif is_valid and confidence < 0.7:
                    # BAJA CONFIANZA - Pedir otra imagen
                    logger.warning(f"⚠️ BAJA CONFIANZA ({confidence:.2f}) - Solicitando nueva imagen")
                    return "uff no logro ver bien los datos. me mandas otra captura más clara?"
                
                else:
                    # INVÁLIDO - Rechazar
                    reason = validation_result.get("reason", "No se pudo leer")
                    logger.warning(f"❌ COMPROBANTE INVÁLIDO - Razón: {reason}")
                    return "mmm esa imagen no se ve bien. te sale la transferencia completa?"
            
            finally:
                # 7. Limpiar archivo temporal
                try:
                    os.unlink(tmp_path)
                    logger.info(f"🗑️  Archivo temporal eliminado: {tmp_path}")
                except:
                    pass
        
        except Exception as e:
            logger.error(f"❌ Error procesando imagen: {e}", exc_info=True)
            return "ay perdón, tuve un problema viendo tu imagen. me la mandas de nuevo?"
    
    async def generate_response(self, user_id: str, user_message: str) -> str:
        """Genera respuesta de Lola usando Gemini AI"""
        try:
            # Agregar mensaje del usuario al historial
            self.conversation_history[user_id].append({
                "role": "user",
                "parts": [user_message]
            })
            
            # Generar respuesta con Gemini
            chat = self.model.start_chat(history=self.conversation_history[user_id][:-1])
            response = chat.send_message(user_message)
            lola_response = response.text
            
            # Agregar respuesta de Lola al historial
            self.conversation_history[user_id].append({
                "role": "model",
                "parts": [lola_response]
            })
            
            return lola_response
            
        except Exception as e:
            logger.error(f"Error generando respuesta Gemini: {e}")
            return "uff perdón, me trabé un momento haha. repite eso?"



manager = SimpleConnectionManager()


# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot Lola API con Gemini AI"}


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "mode": "gemini_ai",
        "active_connections": len(manager.active_connections),
        "model": "gemini-2.5-pro"
    }


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    Endpoint WebSocket para chat en tiempo real.
    Soporta mensajes de texto e imágenes (Base64).
    """
    await manager.connect(websocket, user_id)
    
    try:
        # NO enviar mensaje automático - esperar que el usuario escriba primero
        # (El usuario ya conoce a Lola desde Tinder)
        # welcome = await manager.generate_response(user_id, "hola")
        # await manager.send_message(user_id, welcome)
        
        while True:
            # Recibir mensaje JSON
            data = await websocket.receive_json()
            
            # Determinar tipo de mensaje
            message_type = data.get("type", "text")
            
            if message_type == "text":
                # Procesar mensaje de texto
                user_message = data.get("content", "")
                logger.info(f"📩 [TEXT] {user_id}: {user_message[:100]}")
                
                # Generar respuesta con Gemini AI
                lola_response = await manager.generate_response(user_id, user_message)
                
                await manager.send_message(user_id, lola_response)
                logger.info(f"📤 Lola → {user_id}: {lola_response[:100]}")
            
            elif message_type == "image":
                # Procesar imagen Base64
                base64_image = data.get("content", "")
                logger.info(f"🖼️  [IMAGE] {user_id}: Recibida imagen ({len(base64_image)} caracteres)")
                
                # Enviar mensaje de "validando..."
                await manager.send_message(user_id, "dame un sec, estoy viendo tu comprobante...")
                
                # Procesar imagen
                lola_response = await manager.process_image_base64(user_id, base64_image)
                
                await manager.send_message(user_id, lola_response)
                logger.info(f"📤 Lola → {user_id}: {lola_response}")
            
            else:
                logger.warning(f"⚠️ Tipo de mensaje desconocido: {message_type}")
                await manager.send_message(user_id, "ay no entendí qué me mandaste haha")
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"Usuario {user_id} desconectado normalmente")
    
    except Exception as e:
        logger.error(f"Error WebSocket {user_id}: {e}", exc_info=True)
        manager.disconnect(user_id)



# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*50)
    print("🚀 Bot Lola - Servidor CON GEMINI AI")
    print("="*50)
    print("📍 WebSocket: ws://localhost:8000/ws/{user_id}")
    print("📍 Health:    http://localhost:8000/api/health")
    print("🤖 Personalidad: docs/LOLA.md")
    print("="*50 + "\n")
    
    uvicorn.run(
        "run_fastapi_basic:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
