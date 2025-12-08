"""
Buffer de mensajes optimizado con:
- Thread-safety mediante locks
- Gestión eficiente de memoria
- Límites configurables
- Métricas de performance
"""

"""
OPTIMIZACIÓN DE TIMING (2025-12-03):
- Configurado en 3.0s para mejorar experiencia de usuario
- 3.0s es suficiente para agrupar mensajes rápidos
- Reduce latencia percibida sin sacrificar agrupación
- Basado en resultados exitosos de implementación Telegram
"""

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Representa un mensaje individual"""
    text: str
    timestamp: datetime
    message_type: str = "text"  # text, audio, image
    metadata: Dict = field(default_factory=dict)


@dataclass
class BufferMetrics:
    """Métricas del buffer para monitoreo"""
    total_messages_processed: int = 0
    total_consolidations: int = 0
    average_messages_per_consolidation: float = 0.0
    max_messages_in_buffer: int = 0
    average_wait_time_seconds: float = 0.0


class MessageBuffer:
    """
    Buffer de mensajes thread-safe con consolidación automática.
    
    Evita responder a cada mensaje individual cuando el usuario
    envía múltiples mensajes seguidos. En su lugar, espera un breve
    momento y consolida todos los mensajes en una sola respuesta.
    
    Características:
    - Thread-safe con asyncio.Lock
    - Límite de memoria por usuario
    - Métricas de performance
    - Timeout automático
    """
    
    def __init__(
        self,
        wait_seconds: float = 3.0,
        max_messages_per_user: int = 50,
        max_message_length: int = 4096,
        callback: Optional[Callable] = None
    ):
        """
        Args:
            wait_seconds: Tiempo de espera antes de consolidar
            max_messages_per_user: Máximo de mensajes en buffer por usuario
            max_message_length: Longitud máxima de texto consolidado
            callback: Función async a llamar con mensajes consolidados
        """
        self.wait_seconds = wait_seconds
        self.max_messages_per_user = max_messages_per_user
        self.max_message_length = max_message_length
        self.callback = callback
        
        # Buffers por usuario (usando deque para eficiencia)
        self.buffers: Dict[int, deque] = defaultdict(
            lambda: deque(maxlen=max_messages_per_user)
        )
        
        # Locks por usuario para thread-safety
        self.locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
        
        # Timers activos
        self.timers: Dict[int, asyncio.Task] = {}
        
        # Métricas
        self.metrics = BufferMetrics()
    
    async def add_message(
        self,
        user_id: int,
        text: str,
        message_type: str = "text",
        metadata: Optional[Dict] = None
    ):
        """
        Añade mensaje al buffer de un usuario.
        
        Thread-safe: múltiples llamadas concurrentes no causarán race conditions.
        """
        async with self.locks[user_id]:
            # Crear mensaje
            message = Message(
                text=text,
                timestamp=datetime.now(),
                message_type=message_type,
                metadata=metadata or {}
            )
            
            # Añadir al buffer
            self.buffers[user_id].append(message)
            
            # Actualizar métricas
            self.metrics.total_messages_processed += 1
            current_buffer_size = len(self.buffers[user_id])
            if current_buffer_size > self.metrics.max_messages_in_buffer:
                self.metrics.max_messages_in_buffer = current_buffer_size
            
            # Cancelar timer anterior si existe
            if user_id in self.timers and not self.timers[user_id].done():
                self.timers[user_id].cancel()
                logger.debug(f"Usuario {user_id}: timer cancelado, nuevo mensaje recibido")
            
            # Crear nuevo timer
            self.timers[user_id] = asyncio.create_task(
                self._process_after_delay(user_id)
            )
            
            logger.debug(
                f"Usuario {user_id}: mensaje añadido. "
                f"Buffer size: {len(self.buffers[user_id])}"
            )
    
    async def _process_after_delay(self, user_id: int):
        """
        Espera N segundos y procesa todos los mensajes del buffer.
        """
        try:
            await asyncio.sleep(self.wait_seconds)
            
            async with self.locks[user_id]:
                # Obtener y limpiar buffer
                messages = list(self.buffers[user_id])
                self.buffers[user_id].clear()
                
                if not messages:
                    return
                
                # Consolidar mensajes
                consolidated = self._consolidate_messages(messages)
                
                # Actualizar métricas
                self.metrics.total_consolidations += 1
                self.metrics.average_messages_per_consolidation = (
                    self.metrics.total_messages_processed / 
                    self.metrics.total_consolidations
                )
                
                logger.info(
                    f"Usuario {user_id}: consolidando {len(messages)} mensajes"
                )
                
                # Ejecutar callback si está definido
                if self.callback:
                    await self.callback(user_id, consolidated, messages)
        
        except asyncio.CancelledError:
            logger.debug(f"Usuario {user_id}: timer cancelado")
        
        except Exception as e:
            logger.error(f"Error procesando buffer de usuario {user_id}: {e}")
    
    def _consolidate_messages(self, messages: List[Message]) -> str:
        """
        Consolida múltiples mensajes en uno solo.
        
        Estrategias:
        - Mensajes de texto: separa con saltos de línea
        - Audios transcritos: marca como [Audio]
        - Limita longitud total
        """
        parts = []
        total_length = 0
        
        for msg in messages:
            # Prefijo según tipo
            if msg.message_type == "audio":
                prefix = "[🎤 Audio]: "
            else:
                prefix = ""
            
            text = f"{prefix}{msg.text}"
            
            # Verificar límite de longitud
            if total_length + len(text) > self.max_message_length:
                parts.append(f"\n[...{len(messages) - len(parts)} mensajes adicionales truncados]")
                break
            
            parts.append(text)
            total_length += len(text)
        
        return "\n".join(parts)
    
    async def flush_user_buffer(self, user_id: int):
        """
        Fuerza el procesamiento inmediato del buffer de un usuario.
        Útil para situaciones donde no queremos esperar el delay.
        """
        async with self.locks[user_id]:
            # Cancelar timer si existe
            if user_id in self.timers and not self.timers[user_id].done():
                self.timers[user_id].cancel()
            
            # Procesar inmediatamente
            if self.buffers[user_id]:
                await self._process_after_delay(user_id)
    
    def get_buffer_size(self, user_id: int) -> int:
        """Retorna número de mensajes pendientes en buffer de usuario"""
        return len(self.buffers[user_id])
    
    def get_metrics(self) -> BufferMetrics:
        """Retorna métricas del buffer"""
        return self.metrics
    
    async def cleanup_inactive_users(self, inactive_threshold_hours: int = 24):
        """
        Limpia buffers de usuarios inactivos para liberar memoria.
        
        Args:
            inactive_threshold_hours: Horas de inactividad antes de limpiar
        """
        threshold = datetime.now() - timedelta(hours=inactive_threshold_hours)
        users_to_remove = []
        
        for user_id, buffer in self.buffers.items():
            if not buffer:
                users_to_remove.append(user_id)
                continue
            
            # Verificar último mensaje
            last_message_time = buffer[-1].timestamp
            if last_message_time < threshold:
                users_to_remove.append(user_id)
        
        # Limpiar
        for user_id in users_to_remove:
            async with self.locks[user_id]:
                del self.buffers[user_id]
                del self.locks[user_id]
                if user_id in self.timers:
                    self.timers[user_id].cancel()
                    del self.timers[user_id]
        
        if users_to_remove:
            logger.info(f"Limpiados {len(users_to_remove)} buffers inactivos")


# === EJEMPLO DE USO ===

async def mock_callback(user_id: int, consolidated_text: str, messages: List[Message]):
    """Callback simulado que se llamaría con los mensajes consolidados"""
    print(f"\n{'='*60}")
    print(f"🤖 Procesando mensajes de usuario {user_id}")
    print(f"📊 Total de mensajes: {len(messages)}")
    print(f"{'='*60}")
    print(f"📝 Texto consolidado:\n{consolidated_text}")
    print(f"{'='*60}\n")


async def test_buffer():
    """Test del buffer de mensajes"""
    buffer = MessageBuffer(
        wait_seconds=2.0,
        callback=mock_callback
    )
    
    user_id = 12345
    
    # Simular usuario enviando múltiples mensajes seguidos
    print("Usuario envía 4 mensajes rápidos...")
    await buffer.add_message(user_id, "Hola!")
    await asyncio.sleep(0.2)
    await buffer.add_message(user_id, "Quiero comprar")
    await asyncio.sleep(0.3)
    await buffer.add_message(user_id, "una imagen premium")
    await asyncio.sleep(0.1)
    await buffer.add_message(user_id, "¿cuánto cuesta?")
    
    # Esperar a que se procese
    await asyncio.sleep(3)
    
    # Métricas
    metrics = buffer.get_metrics()
    print(f"\n📈 Métricas del buffer:")
    print(f"  - Mensajes procesados: {metrics.total_messages_processed}")
    print(f"  - Consolidaciones: {metrics.total_consolidations}")
    print(f"  - Promedio mensajes/consolidación: {metrics.average_messages_per_consolidation:.2f}")
    print(f"  - Max mensajes en buffer: {metrics.max_messages_in_buffer}")


if __name__ == "__main__":
    asyncio.run(test_buffer())
