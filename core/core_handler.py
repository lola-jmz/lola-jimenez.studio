#!/usr/bin/env python3
"""
core_handler.py

El cerebro desacoplado del Bot Lola.
Contiene toda la lógica de negocio central, separada de la API (FastAPI/WebSocket).
Maneja el estado, genera respuestas de IA e interactúa con los servicios.
"""

import asyncio
import os
import logging
import datetime
from typing import Optional, Dict, Any, List

# Dependencia para la zona horaria
# Asegúrate de añadir 'pytz' a tu requirements.txt
try:
    import pytz
except ImportError:
    print("Error: 'pytz' no está instalado. Ejecuta: pip install pytz")
    raise

# Imports de la API de Gemini
try:
    import google.generativeai as genai
except ImportError:
    print("Error: 'google.generativeai' no está instalado. Ejecuta: pip install google-generativeai")
    raise

# Imports de los módulos de tu proyecto
from database.database_pool import DatabasePool, ConversationRepository
from core.state_machine import ConversationManager, EventType, ConversationState
from services.security import SecurityManager
from services.payment_validator import PaymentValidator
from services.telegram_notifier import TelegramNotifier
# Audio transcription temporarily disabled for Railway deployment
# from services.audio_transcriber import AudioTranscriber
AudioTranscriber = None  # Placeholder when disabled
from services.error_handler import async_retry, with_fallback, gemini_rate_limiter
from services.content_delivery import ContentDeliveryService
from storage.redis_store import RedisStateStore

logger = logging.getLogger(__name__)


def calculate_typing_delay(text: str) -> float:
    """
    Calcula delay realista basado en longitud de texto.
    Velocidad humana: ~40-50 palabras/minuto en móvil = ~1.2s por palabra.
    
    Returns:
        Delay en segundos (mínimo 1.5s, máximo 15s)
    """
    import random
    word_count = len(text.split())
    
    # Tiempo de escritura: 1.2s por palabra
    typing_time = word_count * 1.2
    
    # Tiempo de pensamiento inicial: 1-3s
    thinking_time = random.uniform(1.0, 3.0)
    
    # Variación natural ±20%
    variation = random.uniform(0.8, 1.2)
    
    total_delay = (thinking_time + typing_time) * variation
    
    # Límites razonables
    return max(1.5, min(total_delay, 15.0))


class LolaCoreHandler:
    """
    El cerebro de Lola. Esta clase no sabe nada sobre Telegram o WebSockets.
    Solo recibe entradas y retorna salidas (respuestas de texto).
    """

    def __init__(
        self,
        db_pool: DatabasePool,
        conversation_manager: ConversationManager,
        security_manager: SecurityManager,
        payment_validator: PaymentValidator,
        content_delivery: ContentDeliveryService,
        redis_store: RedisStateStore,
        gemini_api_key: str,
        audio_transcriber: Optional[Any] = None,  # Optional: disabled for Railway
        telegram_notifier: Optional[TelegramNotifier] = None  # Optional: para notificaciones de pago
    ):
        """
        Inicializa el handler con todos los servicios necesarios (Inyección de Dependencias).
        """
        self.db_pool = db_pool
        self.conversation_manager = conversation_manager
        self.security_manager = security_manager
        self.payment_validator = payment_validator
        self.audio_transcriber = audio_transcriber
        self.content_delivery = content_delivery
        self.redis_store = redis_store
        self.gemini_api_key = gemini_api_key
        self.telegram_notifier = telegram_notifier

        # Repositorio para operaciones de BD
        self.conversation_repo = ConversationRepository(self.db_pool)
        
        # Cargar la personalidad de LOLA.md
        self.lola_personality = self._load_lola_personality()
        
        # Configurar el modelo Gemini
        try:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')  # Optimizado para conversación (75% más barato)
            logger.info("✅ Modelo Generativo de Gemini Flash (Lola) inicializado.")
        except Exception as e:
            logger.error(f"❌ Error fatal inicializando Gemini: {e}")
            raise

        logger.info("✅ LolaCoreHandler (Cerebro del Bot) inicializado correctamente.")

    def quick_intent_detection(self, message: str) -> Optional[str]:
        """Detecta intenciones básicas ANTES de llamar a Gemini"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["cuanto", "costo", "precio", "comprar", "cuánto", "vale"]):
            logger.info("🎯 Quick intent: PRODUCT_INQUIRY")
            return "PRODUCT_INQUIRY"
        
        if any(word in message_lower for word in ["ok", "dale", "sí", "si", "sale", "va"]):
            logger.info("🎯 Quick intent: CONFIRMATI ON")
            return "CONFIRMATION"
        
        if any(word in message_lower for word in ["caro", "mucho", "no tengo"]):
            logger.info("🎯 Quick intent: OBJECTION")
            return "OBJECTION"
        
        return None

    def _load_lola_personality(self) -> str:
        """Carga el archivo LOLA_FLASH.md con la personalidad del bot"""
        try:
            # Ruta relativa al archivo de personalidad
            with open("docs/LOLA_FLASH.md", "r", encoding="utf-8") as f:
                personality = f.read()
                logger.info("✅ Personalidad de Lola cargada desde LOLA_FLASH.md")
                return personality
        except FileNotFoundError:
            logger.error("❌❌❌ FATAL: docs/LOLA_FLASH.md no encontrado. El bot no tendrá personalidad.")
            return """
            ERROR: Personalidad no encontrada.
            Responde únicamente: 'Ay, la vdd no te entendí nada haha'
            """

    # --- LÓGICA DE TIEMPO REAL (LA NUEVA FUNCIONALIDAD) ---

    def _get_time_of_day_es(self, hour: int) -> str:
        """Helper para obtener el momento del día en español."""
        if 5 <= hour < 12:
            return "la mañana"
        elif 12 <= hour < 20:
            return "la tarde"
        elif 20 <= hour < 24:
            return "la noche"
        else: # 0 a 4
            return "la madrugada"

    def _get_current_time_context(self) -> str:
        """
        Genera el string de contexto de tiempo real para Lola en Querétaro.
        """
        try:
            # Zona horaria de Querétaro (usa 'America/Mexico_City' que es la correcta para Qro)
            tz_queretaro = pytz.timezone('America/Mexico_City')
            now = datetime.datetime.now(tz_queretaro)

            dias_es = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
            dia_semana = dias_es[now.weekday()]
            hora_actual_str = now.strftime('%I:%M %p') # Formato 12-horas (ej. 03:15 PM)
            momento_del_dia = self._get_time_of_day_es(now.hour)

            return (
                f"CONTEXTO DE TIEMPO REAL: Son las {hora_actual_str} "
                f"del {dia_semana} por {momento_del_dia} en Querétaro."
            )
        except Exception as e:
            logger.warning(f"Error generando contexto de tiempo: {e}. Usando fallback.")
            return "CONTEXTO DE TIEMPO REAL: No disponible."

    async def _load_tinder_context(self, user_id: int) -> str:
        """
        Carga el contexto de conversación previa de Tinder si existe.
        Retorna un string formateado para incluir en el prompt de Gemini.
        
        Args:
            user_id: ID numérico del usuario
            
        Returns:
            String con el contexto de Tinder formateado, o string vacío si no hay contexto
        """
        try:
            tinder_context = await self.conversation_repo.get_tinder_context(user_id)
            
            if not tinder_context:
                return ""
            
            history = tinder_context.get("history", [])
            metadata = tinder_context.get("metadata", {})
            
            if not history:
                return ""
            
            # Formatear el historial de Tinder para el prompt
            formatted_history = "CONTEXTO PREVIO DE TINDER:\n"
            formatted_history += f"(Tuviste {len(history)} mensajes previos con este usuario en Tinder)\n\n"
            
            # Incluir los últimos 10 mensajes del historial de Tinder
            recent_messages = history[-10:] if len(history) > 10 else history
            
            for msg in recent_messages:
                sender = msg.get("sender", "Usuario")
                content = msg.get("content", "")
                is_bot = msg.get("is_bot", False)
                
                if is_bot:
                    formatted_history += f"Lola (tú): {content}\n"
                else:
                    formatted_history += f"{sender}: {content}\n"
            
            formatted_history += "\n(Instrucción: Este usuario ya te conoce desde Tinder. "
            formatted_history += "Reconócelo naturalmente y continúa la conversación. "
            formatted_history += "NO vuelvas a presentarte. Ya sabe quién eres y por qué estás aquí.)\n"
            
            logger.info(f"✅ Contexto de Tinder cargado para user_id {user_id}: {len(history)} mensajes")
            return formatted_history
            
        except Exception as e:
            logger.warning(f"Error cargando contexto de Tinder para user_id {user_id}: {e}")
            return ""

    # --- MANEJADORES DE ENTRADA (Llamados por la API/WebSocket) ---

    async def process_text_message(self, user_identifier: str, message_text: str) -> str:
        """
        Procesa un mensaje de texto entrante.
        Esta es la función principal de chat.

        Args:
            user_identifier: Identificador único del usuario (string para web)
            message_text: Contenido del mensaje
        """
        # 0. Obtener o crear user_id numérico para BD
        user_id = await self.conversation_repo.get_or_create_user_by_identifier(user_identifier)

        # 1. Validar y Sanitizar (lógica de security.py)
        is_valid, validation_error = self.security_manager.validate_user_input(message_text)
        if not is_valid:
            logger.warning(f"Usuario {user_identifier} envió mensaje inválido: {validation_error}")
            return "Oye no me hables así. Mejor la dejamos aquí." # Respuesta de Fase Protección

        sanitized_text = self.security_manager.sanitize_input(message_text)

        # 2. Guardar mensaje del usuario (con user_id numérico)
        await self.conversation_repo.save_message(user_id, sanitized_text, is_bot=False)

        # 3. Obtener estado actual (conversation_manager usa user_identifier)
        current_state = self.conversation_manager.get_state(user_identifier)

        # 4. Decidir acción basada en el estado
        response_text = ""
        if current_state in [ConversationState.INICIO, ConversationState.CONVERSANDO]:
            self.conversation_manager.handle_event(user_identifier, EventType.MENSAJE_RECIBIDO)
            quick_intent = self.quick_intent_detection(sanitized_text)
            response_text = await self._generate_lola_response(user_identifier, sanitized_text, quick_intent)
            
            # 🔥 FIX v2: Detección ROBUSTA de datos de pago
            # Activar el estado ESPERANDO_PAGO *solo* cuando Lola da los números reales
            response_normalized = response_text.replace(" ", "").replace("-", "").lower()
            CLABE_PARTIAL = "44136159"  # Últimos 8 dígitos de CLABE
            OXXO_PARTIAL = "95348913"   # Últimos 8 dígitos de tarjeta Oxxo
            
            has_payment_data = (
                CLABE_PARTIAL in response_normalized or
                OXXO_PARTIAL in response_normalized
            )
            
            should_transition_to_payment = False
            if has_payment_data:
                should_transition_to_payment = True
                
                # 🔥 FIX BUG 3: Extraer monto de la respuesta de Lola y guardarlo
                import re
                amount_match = re.search(r'\$\s?(\d+)', response_text)
                if amount_match:
                    detected_amount = float(amount_match.group(1))
                    await self.redis_store.set_metadata(user_identifier, "expected_amount", detected_amount)
                    logger.info(f"💰 expected_amount actualizado dinámicamente a: {detected_amount}")
                
                logger.info(f"🎯 PAGO DETECTADO en respuesta de Lola para {user_identifier}")
                logger.info(f"📝 Trigger encontrado en: {response_text[:100]}...")
        
        elif current_state == ConversationState.ESPERANDO_PAGO:
            # El usuario está hablando en lugar de enviar el comprobante.
            # Lola le recuerda, como en LOLA.md.
            response_text = "estaba esperando el comprobante haha. si sí te animas me avisas."
        
        elif current_state == ConversationState.PAGO_RECHAZADO:
            response_text = "noup, el comprobante no pasó. quieres intentar con otro?"

        else:
            # Fallback
            response_text = "Ay, la vdd no te entendí nada haha"

        # 5. Guardar respuesta de Lola
        await self.conversation_repo.save_message(user_id, response_text, is_bot=True)
        
        # 6. Aplicar delay realista antes de retornar (Fix ERROR-C8)
        # Simula el tiempo que tardaría una persona real en escribir
        delay = calculate_typing_delay(response_text)
        logger.info(f"Aplicando delay realista: {delay:.1f}s para {len(response_text.split())} palabras")
        await asyncio.sleep(delay)
        
        # 🔥 FIX BUG 1: Mover la transición de estado AQUÍ, DESPUÉS del delay.
        # Así aseguramos que el mensaje del Oxxo/CLABE fue procesado en su estado original.
        if current_state in [ConversationState.INICIO, ConversationState.CONVERSANDO] and should_transition_to_payment:
            self.conversation_manager.handle_event(user_identifier, EventType.SOLICITAR_PAGO)
            new_state = self.conversation_manager.get_state(user_identifier)
            logger.info(f"🎯 Estado cambiado (diferido): CONVERSANDO → {new_state.value}")
        
        return response_text

    @with_fallback(fallback_value="Ay, no pude escuchar bien tu audio haha. mejor escríbeme.")
    async def process_audio_message(self, user_identifier: str, audio_path: str) -> str:
        """
        Procesa un mensaje de audio entrante.

        Args:
            user_identifier: Identificador único del usuario
            audio_path: Ruta al archivo de audio
        """
        # Verificar si la transcripción de audio está disponible
        if self.audio_transcriber is None:
            logger.warning(f"Transcripción de audio desactivada. Usuario: {user_identifier}")
            return "Ay, las notas de voz están desactivadas por ahora haha. mejor escríbeme. 💬"
        
        # 0. Obtener user_id numérico
        user_id = await self.conversation_repo.get_or_create_user_by_identifier(user_identifier)

        # 1. Transcribir (lógica de audio_transcriber.py)
        logger.info(f"Transcribiendo audio para usuario {user_identifier}...")
        transcription = self.audio_transcriber.transcribe(audio_path)
        logger.info(f"Transcripción: {transcription}")

        # 2. Guardar transcripción (como si fuera un mensaje de usuario)
        await self.conversation_repo.save_message(
            user_id,
            f"[Audio]: {transcription}",
            is_bot=False
        )

        # 3. Procesar el texto transcrito como un mensaje normal
        return await self.process_text_message(user_identifier, transcription)

    async def process_photo_message(self, user_identifier: str, photo_path: str) -> str:
        """
        Procesa una imagen entrante (asume que es un comprobante de pago).

        Args:
            user_identifier: Identificador único del usuario
            photo_path: Ruta al archivo de imagen
        """
        # 0. Obtener user_id numérico
        user_id = await self.conversation_repo.get_or_create_user_by_identifier(user_identifier)

        current_state = self.conversation_manager.get_state(user_identifier)
        
        # 📊 LOGGING DETALLADO para diagnóstico
        logger.info(f"📸 IMAGEN RECIBIDA de {user_identifier}")
        logger.info(f"📊 Estado actual: {current_state.value}")

        # 1. Verificar si estamos esperando un pago
        if current_state not in [ConversationState.ESPERANDO_PAGO, ConversationState.PAGO_RECHAZADO]:
            logger.warning(f"⚠️ RECHAZADO: Estado '{current_state.value}' no acepta comprobantes. Se requiere 'esperando_pago'.")
            return "haha gracias por la foto. pero no estoy esperando un comprobante ahora."

        # 2. Validar que la imagen sea segura (lógica de security.py)
        is_valid_image, error = self.security_manager.validate_image_file(photo_path)
        if not is_valid_image:
            logger.warning(f"Usuario {user_identifier} envió imagen inválida: {error}")
            return f"Ay, esa imagen se ve rara o está dañada. Intenta con otra porfa."

        # 3. Actualizar estado a "Validando"
        self.conversation_manager.handle_event(user_identifier, EventType.IMAGEN_RECIBIDA)
        # TODO: Tu API/WebSocket debería enviar un mensaje de "Validando..." aquí

        # 4. Validar el comprobante (lógica de payment_validator.py)
        validation_result = await self._validate_payment_proof(photo_path, user_identifier)
        
        # 4.5. Notificar a Guus via Telegram (si está configurado)
        if self.telegram_notifier:
            try:
                confidence = validation_result.get("confidence", 0.0)
                expected_amount = await self.redis_store.get_metadata(user_identifier, "expected_amount") or 200
                extracted_data = validation_result.get("extracted_data", {})
                
                # Subir imagen a Backblaze para compartir URL
                image_url = None
                try:
                    from pathlib import Path
                    filename = f"comprobantes/comprobante_{user_identifier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    # TODO: Implementar upload_file en content_delivery si no existe
                    # image_url = await self.content_delivery.upload_file(photo_path, filename)
                    logger.info(f"📸 Comprobante guardado localmente: {photo_path}")
                except Exception as e:
                    logger.warning(f"No se pudo subir comprobante a Backblaze: {e}")
                
                # Enviar notificación
                await self.telegram_notifier.notify_payment_received(
                    user_identifier=user_identifier,
                    amount=expected_amount,
                    image_url=image_url,
                    confidence=confidence,
                    extracted_data=extracted_data
                )
                logger.info(f"📱 Notificación Telegram enviada para {user_identifier}")
            except Exception as e:
                logger.error(f"Error enviando notificación Telegram: {e}")
                # No bloquear el flujo si falla Telegram

        # 5. Reaccionar al resultado
        if validation_result["is_valid"]:
            # APROBADO
            self.conversation_manager.handle_event(user_identifier, EventType.COMPROBANTE_VALIDO)
            await self.conversation_repo.mark_payment_completed(user_id, validation_result.get("extracted_data", {}))

            # Entregar producto
            product_response = await self._deliver_product(user_identifier, user_id)
            return f"✅ ¡Listo! Pago confirmado.\n\n{product_response}"
        
        else:
            # RECHAZADO
            self.conversation_manager.handle_event(user_identifier, EventType.COMPROBANTE_INVALIDO)
            reason = validation_result.get("reason", "No se pudo leer bien")
            return f"❌ Híjole, no pude validar el comprobante. Razón: {reason}. Porfa intenta con una foto más clara."

    # --- LÓGICA DE IA (Respuesta de Chat) ---

    def _build_conversation_context(self, history: list) -> str:
        """Construye contexto de conversación para el prompt (igual que en bot_optimized.py)"""
        if not history:
            return "Esta es la primera interacción."
        
        context_lines = []
        # Últimos 10 mensajes, en orden cronológico (reverse)
        for msg in reversed(history[:10]):  
            role = "Tú" if msg["is_bot"] else "Usuario"
            context_lines.append(f"{role}: {msg['message']}")
        
        return "\n".join(context_lines)

    @async_retry(max_attempts=3, delay=1, backoff=2)
    async def _generate_lola_response(
        self,
        user_identifier: str,
        user_message: str,
        quick_intent: Optional[str] = None  # NUEVO: Inten ción rápida detectada
    ) -> str:
        """
        Genera respuesta usando Gemini API, AHORA CON CONTEXTO DE TIEMPO.

        Args:
            user_identifier: Identificador único del usuario
            user_message: Mensaje del usuario
        """
        await gemini_rate_limiter.acquire()

        # 0. Obtener user_id numérico para BD
        user_id = await self.conversation_repo.get_or_create_user_by_identifier(user_identifier)

        # 1. Obtener historial (lógica de database_pool.py)
        history = await self.conversation_repo.get_conversation_history(
            user_id=user_id,
            limit=20 # Límite de mensajes para el historial
        )
        context_history = self._build_conversation_context(history)

        # 2. OBTENER CONTEXTO DE TIEMPO REAL
        time_context = self._get_current_time_context()
        
        # 3. OBTENER CONTEXTO DE TINDER (NUEVA FUNCIONALIDAD)
        tinder_context = await self._load_tinder_context(user_id)
        
        # 4. AÑADIR HINT DE INTENCIÓN SI FUE DETECTADA
        context_hint = f"\n[INTENT_DETECTED: {quick_intent}]" if quick_intent else ""
        
        # 5. Construir el prompt completo
        full_prompt = f"""
{self.lola_personality}

---
{time_context}
(Instrucción para ti, IA: Debes usar el 'CONTEXTO DE TIEMPO REAL' para que tus respuestas sean creíbles. 
Ej: Si son las 3 AM, estás despierta haciendo tareas de la uni, no en el gym. 
Si el usuario pregunta 'qué día es hoy', usa esta información.)
---

{tinder_context if tinder_context else ""}
{context_hint}

HISTORIAL DE CONVERSACIÓN RECIENTE:
{context_history}

MENSAJE ACTUAL DEL USUARIO:
{user_message}

Tu respuesta (como Lola):
"""
        
        try:
            # 4. Generar respuesta
            # Usamos generate_content_async para operaciones asíncronas
            response = await self.model.generate_content_async(full_prompt)
            
            # Limpiar la respuesta (Gemini a veces añade 'Tú: ')
            response_text = response.text.strip().lstrip("Tú:").strip()

            # Fallback por si la IA no responde o da una respuesta vacía
            if not response_text:
                return "Ay, la vdd no te entendí nada haha"

            return response_text
        
        except Exception as e:
            logger.error(f"❌ Error generando respuesta de Gemini para {user_identifier}: {e}")
            # Usamos el fallback de LOLA.md
            return "Ay, la vdd no te entendí nada haha"

    # --- LÓGICA DE NEGOCIO (Pagos y Entregas) ---

    @async_retry(max_attempts=3, delay=1, backoff=2)
    async def _validate_payment_proof(self, image_path: str, user_id: str) -> dict:
        """Valida comprobante de pago con Gemini Vision"""
        # Obtener el monto esperado del estado en Redis
        expected_amount = await self.redis_store.get_metadata(user_id, "expected_amount")
        
        if not expected_amount:
            logger.warning(f"No se encontró expected_amount para {user_id}, usando 200 por defecto")
            expected_amount = 200
        
        await gemini_rate_limiter.acquire()
        return await self.payment_validator.validate_payment_proof(  # FIX: await añadido
            image_path,
            expected_amount=expected_amount,
            expected_currency="MXN"
        )

    async def _deliver_product(self, user_identifier: str, user_id: int) -> str:
        """
        Entrega el producto digital al usuario.
        Retorna un mensaje de texto para el usuario.

        Args:
            user_identifier: Identificador único del usuario (para Redis)
            user_id: ID numérico del usuario (para BD)
        """
        try:
            # 1. Obtener el producto que el usuario compró de la metadata
            product_level = await self.redis_store.get_metadata(user_identifier, "product_level")

            if not product_level:
                logger.error(f"No se encontró product_level para {user_identifier}")
                return "Ay, no encuentro qué compraste. Deja lo reviso."

            # 2. Obtener URL del contenido desde content_delivery
            delivery_result = await self.content_delivery.deliver_content(
                user_id=str(user_id),
                product_level=product_level
            )

            if not delivery_result.get("success"):
                logger.error(f"Error entregando producto a {user_identifier}: {delivery_result.get('error')}")
                self.conversation_manager.handle_event(user_identifier, EventType.ERROR_OCURRIDO)
                return "Ay, tuve un problema enviándote tu contenido. Deja lo reviso."

            # 3. Actualizar estado
            self.conversation_manager.handle_event(user_identifier, EventType.PRODUCTO_ENTREGADO)

            # 4. Guardar el enlace en BD
            await self.conversation_repo.save_delivery(
                user_id=user_id,
                product_url=delivery_result["url"],
                expires_at=delivery_result["expires_at"]
            )

            logger.info(f"✅ Producto entregado a usuario {user_identifier}")
            
            # 5. Retornar mensaje con URL empaquetada para el frontend
            return f"listo. espero y sí te haya gustado 🫣. [DELIVERY:{delivery_result['url']}]\n\nsi luego quieres subir de nivel me avisas haha."
        
        except Exception as e:
            logger.error(f"Error entregando producto a usuario {user_id}: {e}")
            self.conversation_manager.handle_event(user_id, EventType.ERROR_OCURRIDO)
            return "Ay, tuve un problema enviándote tu contenido. Deja lo reviso."