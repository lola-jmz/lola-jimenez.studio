#!/usr/bin/env python3
"""
redis_store.py

Wrapper de Redis para almacenamiento de estado distribuido.
Permite que múltiples instancias de FastAPI compartan estado de conversaciones.
"""

import json
import logging
from typing import Optional, Dict, Any
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisStateStore:
    """
    Gestor de estado distribuido usando Redis.
    Reemplaza el estado en memoria del ConversationManager para escalabilidad.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379", ttl_seconds: int = 86400, db_pool = None):
        """
        Inicializa el cliente Redis.
        
        Args:
            redis_url: URL de conexión a Redis
            ttl_seconds: Tiempo de vida de las claves (default: 24 horas)
            db_pool: Pool de conexiones asyncpg para respaldo en PostgreSQL (opcional)
        """
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self.db_pool = db_pool  # NUEVO: Para respaldo en PostgreSQL
        self.client: Optional[redis.Redis] = None
        logger.info(f"RedisStateStore configurado para: {redis_url}")
        self.redis_available = False  # Se establece en connect()
        if db_pool:
            logger.info("✅ Respaldo PostgreSQL habilitado")

    async def connect(self):
        """Establece conexión con Redis (opcional - fallback a PostgreSQL si falla)"""
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.client.ping()
            self.redis_available = True
            logger.info("✅ Conexión a Redis establecida")
        except Exception as e:
            logger.warning(f"⚠️ Redis no disponible ({e}). Usando solo PostgreSQL.")
            self.redis_available = False
            self.client = None

    async def disconnect(self):
        """Cierra la conexión con Redis"""
        if self.client:
            await self.client.close()
            logger.info("Conexión a Redis cerrada")

    async def get_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado de conversación de un usuario.
        NUEVO: Intenta recuperar desde PostgreSQL si Redis no está disponible o falla.
        
        Args:
            user_id: ID único del usuario (UUID string)
            
        Returns:
            Dict con el estado o None si no existe
        """
        try:
            # Si Redis está disponible, intentar primero
            if self.redis_available and self.client:
                key = f"conversation_state:{user_id}"
                data = await self.client.get(key)
                
                if data:
                    return json.loads(data)
            
            # Fallback a PostgreSQL
            logger.info(f"🔍 No encontrado en Redis (o Redis no disponible), buscando en PostgreSQL: {user_id}")
            return await self.restore_from_postgres(user_id)
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de {user_id}: {e}")
            return await self.restore_from_postgres(user_id)  # Fallback en error

    async def set_state(self, user_id: str, state_data: Dict[str, Any]):
        """
        Guarda el estado de conversación de un usuario.
        NUEVO: También guarda respaldo asíncrono en PostgreSQL.
        
        Args:
            user_id: ID único del usuario
            state_data: Diccionario con el estado (debe ser JSON-serializable)
        """
        try:
            # 1. Guardar en Redis (si está disponible)
            if self.redis_available and self.client:
                key = f"conversation_state:{user_id}"
                await self.client.setex(
                    key,
                    self.ttl_seconds,
                    json.dumps(state_data)
                )
                logger.debug(f"✅ Estado guardado en Redis: {user_id}")
            
            # 2. Respaldo en PostgreSQL (siempre)
            if self.db_pool:
                await self._backup_to_postgres(user_id, state_data)
                
        except Exception as e:
            logger.error(f"Error guardando estado de {user_id}: {e}")
            # Intentar solo PostgreSQL si Redis falla
            if self.db_pool:
                await self._backup_to_postgres(user_id, state_data)

    async def delete_state(self, user_id: str):
        """Elimina el estado de un usuario (útil para reiniciar conversación)"""
        try:
            if self.redis_available and self.client:
                key = f"conversation_state:{user_id}"
                await self.client.delete(key)
                logger.info(f"Estado de {user_id} eliminado de Redis")
        except Exception as e:
            logger.error(f"Error eliminando estado de {user_id}: {e}")

    async def get_metadata(self, user_id: str, key: str) -> Optional[Any]:
        """
        Obtiene un valor de metadata específico del estado del usuario.
        
        Args:
            user_id: ID del usuario
            key: Clave de metadata (ej: "expected_amount", "product_level")
            
        Returns:
            Valor de la metadata o None
        """
        state = await self.get_state(user_id)
        if state and "metadata" in state:
            return state["metadata"].get(key)
        return None

    async def set_metadata(self, user_id: str, key: str, value: Any):
        """
        Guarda un valor de metadata en el estado del usuario.
        
        Args:
            user_id: ID del usuario
            key: Clave de metadata
            value: Valor a guardar (debe ser JSON-serializable)
        """
        state = await self.get_state(user_id)
        if not state:
            state = {"metadata": {}}
        
        if "metadata" not in state:
            state["metadata"] = {}
        
        state["metadata"][key] = value
        await self.set_state(user_id, state)

    async def health_check(self) -> bool:
        """Verifica que Redis esté operativo (o retorna False si no hay Redis)"""
        if not self.redis_available or not self.client:
            logger.info("Health check: Redis no disponible, usando solo PostgreSQL")
            return False
        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check falló: {e}")
            return False

    # === NUEVOS MÉTODOS DE RESPALDO ===

    async def _backup_to_postgres(self, user_id: str, state_data: Dict[str, Any]):
        """
        Guarda respaldo del estado en PostgreSQL.
        ESTRATEGIA: UPSERT - Actualiza si existe, inserta si no existe.
        
        Args:
            user_id: ID único del usuario
            state_data: Estado completo de conversación
        """
        try:
            query = """
                INSERT INTO conversation_state_backup (user_id, state_data, created_at, updated_at)
                VALUES ($1, $2, NOW(), NOW())
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    state_data = EXCLUDED.state_data,
                    updated_at = NOW()
            """
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(query, user_id, json.dumps(state_data))
                
            logger.debug(f"💾 Respaldo PostgreSQL guardado: {user_id}")
            
        except Exception as e:
            # NO fallar si el respaldo falla, solo log warning
            logger.warning(f"⚠️ Respaldo PostgreSQL falló para {user_id}: {e}")

    async def restore_from_postgres(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Restaura estado desde PostgreSQL si Redis no lo tiene.
        Útil cuando Redis se reinicia o pierde datos.
        
        Args:
            user_id: ID único del usuario
            
        Returns:
            Estado recuperado o None
        """
        try:
            if not self.db_pool:
                logger.warning("No hay pool PostgreSQL configurado")
                return None
                
            query = """
                SELECT state_data 
                FROM conversation_state_backup 
                WHERE user_id = $1 
                ORDER BY updated_at DESC 
                LIMIT 1
            """
            
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval(query, user_id)
                
            if result:
                logger.info(f"♻️ Estado restaurado desde PostgreSQL: {user_id}")
                return json.loads(result)
                
            return None
            
        except Exception as e:
            logger.error(f"Error restaurando desde PostgreSQL: {e}")
            return None
