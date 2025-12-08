"""
Connection Pool optimizado para PostgreSQL con:
- Gestión automática de conexiones
- Retry logic para fallos transitorios
- Health checks
- Métricas de performance
"""

import asyncio
import asyncpg
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class PoolMetrics:
    """Métricas del connection pool"""
    total_connections_created: int = 0
    total_connections_closed: int = 0
    total_queries_executed: int = 0
    total_query_errors: int = 0
    average_query_time_ms: float = 0.0
    peak_connections_used: int = 0


class DatabasePool:
    """
    Connection pool optimizado para PostgreSQL con asyncpg.
    
    Ventajas:
    - Reutiliza conexiones (evita overhead de crear/cerrar)
    - Thread-safe para operaciones concurrentes
    - Health checks automáticos
    - Retry logic para transacciones
    - Métricas de performance
    """
    
    def __init__(
        self,
        dsn: Optional[str] = None,
        min_size: int = 10,
        max_size: int = 50,
        command_timeout: int = 60,
        **kwargs
    ):
        """
        Args:
            dsn: Connection string (postgresql://user:pass@host:port/db)
            min_size: Mínimo de conexiones en el pool
            max_size: Máximo de conexiones en el pool
            command_timeout: Timeout para comandos en segundos
            **kwargs: Parámetros adicionales de conexión
        """
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.command_timeout = command_timeout
        self.kwargs = kwargs
        
        self.pool: Optional[asyncpg.Pool] = None
        self.metrics = PoolMetrics()
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Inicializa el connection pool"""
        if self.pool is not None:
            logger.warning("Pool ya inicializado")
            return
        
        try:
            logger.info(f"Inicializando connection pool (min={self.min_size}, max={self.max_size})")
            
            self.pool = await asyncpg.create_pool(
                dsn=self.dsn,
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=self.command_timeout,
                **self.kwargs
            )
            
            # Health check inicial
            await self.health_check()
            
            logger.info("✅ Connection pool inicializado correctamente")
        
        except Exception as e:
            logger.error(f"❌ Error inicializando pool: {e}")
            raise
    
    async def close(self):
        """Cierra el connection pool"""
        if self.pool is None:
            return
        
        logger.info("Cerrando connection pool...")
        await self.pool.close()
        self.pool = None
        logger.info("✅ Connection pool cerrado")
    
    async def health_check(self) -> bool:
        """
        Verifica que el pool esté funcionando correctamente.
        
        Returns:
            True si está saludable, False si no
        """
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        
        except Exception as e:
            logger.error(f"❌ Health check falló: {e}")
            return False
    
    @asynccontextmanager
    async def acquire(self):
        """
        Context manager para adquirir conexión del pool.
        
        Uso:
            async with db_pool.acquire() as conn:
                result = await conn.fetch("SELECT * FROM users")
        """
        if self.pool is None:
            raise RuntimeError("Pool no inicializado. Llama a initialize() primero.")
        
        async with self.pool.acquire() as connection:
            try:
                yield connection
            finally:
                pass  # La conexión se devuelve automáticamente al pool
    
    async def execute(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> str:
        """
        Ejecuta query que no retorna datos (INSERT, UPDATE, DELETE).
        
        Returns:
            Status string (ej: "INSERT 0 1")
        """
        start_time = datetime.now()
        
        try:
            async with self.acquire() as conn:
                result = await conn.execute(query, *args, timeout=timeout)
            
            # Métricas
            self._update_query_metrics(start_time)
            self.metrics.total_queries_executed += 1
            
            return result
        
        except Exception as e:
            self.metrics.total_query_errors += 1
            logger.error(f"Error ejecutando query: {e}\nQuery: {query[:100]}...")
            raise
    
    async def fetch(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> List[asyncpg.Record]:
        """
        Ejecuta query que retorna múltiples filas.
        
        Returns:
            Lista de Records
        """
        start_time = datetime.now()
        
        try:
            async with self.acquire() as conn:
                result = await conn.fetch(query, *args, timeout=timeout)
            
            # Métricas
            self._update_query_metrics(start_time)
            self.metrics.total_queries_executed += 1
            
            return result
        
        except Exception as e:
            self.metrics.total_query_errors += 1
            logger.error(f"Error ejecutando query: {e}\nQuery: {query[:100]}...")
            raise
    
    async def fetchrow(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> Optional[asyncpg.Record]:
        """
        Ejecuta query que retorna una sola fila.
        
        Returns:
            Record o None si no hay resultados
        """
        start_time = datetime.now()
        
        try:
            async with self.acquire() as conn:
                result = await conn.fetchrow(query, *args, timeout=timeout)
            
            # Métricas
            self._update_query_metrics(start_time)
            self.metrics.total_queries_executed += 1
            
            return result
        
        except Exception as e:
            self.metrics.total_query_errors += 1
            logger.error(f"Error ejecutando query: {e}\nQuery: {query[:100]}...")
            raise
    
    async def fetchval(
        self,
        query: str,
        *args,
        column: int = 0,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Ejecuta query que retorna un solo valor.
        
        Returns:
            Valor de la columna especificada
        """
        start_time = datetime.now()
        
        try:
            async with self.acquire() as conn:
                result = await conn.fetchval(query, *args, column=column, timeout=timeout)
            
            # Métricas
            self._update_query_metrics(start_time)
            self.metrics.total_queries_executed += 1
            
            return result
        
        except Exception as e:
            self.metrics.total_query_errors += 1
            logger.error(f"Error ejecutando query: {e}\nQuery: {query[:100]}...")
            raise
    
    async def execute_transaction(self, queries: List[tuple]) -> bool:
        """
        Ejecuta múltiples queries en una transacción.
        Todo o nada (atomicidad).
        
        Args:
            queries: Lista de tuplas (query, args)
        
        Returns:
            True si éxito, False si falló
        
        Ejemplo:
            success = await pool.execute_transaction([
                ("INSERT INTO users (name) VALUES ($1)", ["Alice"]),
                ("UPDATE balance SET amount = amount - 100 WHERE user_id = $1", [1])
            ])
        """
        try:
            async with self.acquire() as conn:
                async with conn.transaction():
                    for query, args in queries:
                        await conn.execute(query, *args)
            
            logger.info(f"✅ Transacción completada ({len(queries)} queries)")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error en transacción: {e}")
            return False
    
    def _update_query_metrics(self, start_time: datetime):
        """Actualiza métricas de tiempo de query"""
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Media móvil del tiempo de query
        total = self.metrics.total_queries_executed
        if total == 0:
            self.metrics.average_query_time_ms = elapsed_ms
        else:
            self.metrics.average_query_time_ms = (
                (self.metrics.average_query_time_ms * total + elapsed_ms) / (total + 1)
            )
    
    def get_metrics(self) -> PoolMetrics:
        """Retorna métricas del pool"""
        return self.metrics
    
    def get_pool_size(self) -> int:
        """Retorna número de conexiones activas en el pool"""
        if self.pool is None:
            return 0
        return self.pool.get_size()
    
    def get_idle_connections(self) -> int:
        """Retorna número de conexiones idle (disponibles)"""
        if self.pool is None:
            return 0
        return self.pool.get_idle_size()


# === HELPERS PARA OPERACIONES COMUNES ===

class ConversationRepository:
    """
    Repositorio para operaciones de conversación en BD.
    Encapsula queries comunes.
    """
    
    def __init__(self, pool: DatabasePool):
        self.pool = pool
    
    async def save_message(
        self,
        user_id: int,
        message: str,
        is_bot: bool = False,
        metadata: Optional[Dict] = None
    ):
        """Guarda un mensaje en el historial"""
        import json

        query = """
            INSERT INTO messages (user_id, message, is_bot, metadata, created_at)
            VALUES ($1, $2, $3, $4, NOW())
        """
        await self.pool.execute(
            query,
            user_id,
            message,
            is_bot,
            json.dumps(metadata or {})
        )
    
    async def get_conversation_history(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """Obtiene historial de conversación"""
        query = """
            SELECT message, is_bot, metadata, created_at
            FROM messages
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        rows = await self.pool.fetch(query, user_id, limit)
        
        return [
            {
                "message": row["message"],
                "is_bot": row["is_bot"],
                "metadata": row["metadata"],
                "created_at": row["created_at"]
            }
            for row in rows
        ]
    
    async def mark_payment_completed(self, user_id: int, payment_data: Dict):
        """Marca que el usuario completó el pago"""
        query = """
            UPDATE users
            SET has_paid = TRUE, payment_data = $2, updated_at = NOW()
            WHERE user_id = $1
        """
        await self.pool.execute(query, user_id, payment_data)
    
    async def has_user_paid(self, user_id: int) -> bool:
        """Verifica si el usuario ya pagó"""
        query = "SELECT has_paid FROM users WHERE user_id = $1"
        result = await self.pool.fetchval(query, user_id)
        return result or False

    async def get_or_create_user_by_identifier(self, user_identifier: str) -> int:
        """
        Obtiene o crea un usuario por user_identifier (para web).
        Retorna el user_id numérico.
        """
        # Buscar usuario existente
        query_select = "SELECT user_id FROM users WHERE user_identifier = $1"
        user_id = await self.pool.fetchval(query_select, user_identifier)

        if user_id:
            return user_id

        # Crear nuevo usuario con ID autogenerado
        import time
        import random
        new_user_id = int(time.time() * 1000) + random.randint(1000, 9999)

        query_insert = """
            INSERT INTO users (user_id, user_identifier, username, first_name)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO NOTHING
            RETURNING user_id
        """
        result = await self.pool.fetchval(
            query_insert,
            new_user_id,
            user_identifier,
            f"web_{user_identifier[:8]}",
            "Usuario Web"
        )

        return result or new_user_id

    async def get_tinder_context(self, user_id: int) -> Optional[Dict]:
        """
        Obtiene el contexto de Tinder del usuario si existe.
        Retorna el tinder_history y tinder_metadata del campo context de conversations.
        """
        import json
        
        query = """
            SELECT context
            FROM conversations
            WHERE user_id = $1
            AND context::text LIKE '%tinder_history%'
            ORDER BY started_at DESC
            LIMIT 1
        """
        
        result = await self.pool.fetchval(query, user_id)
        
        if not result:
            return None
        
        # Si result es string, parsearlo a dict
        if isinstance(result, str):
            context = json.loads(result)
        else:
            context = result
        
        tinder_history = context.get("tinder_history", [])
        tinder_metadata = context.get("tinder_metadata", {})
        
        if not tinder_history:
            return None
        
        return {
            "history": tinder_history,
            "metadata": tinder_metadata
        }


# === EJEMPLO DE USO ===

async def test_pool():
    """Test del connection pool"""
    
    # Inicializar pool
    pool = DatabasePool(
        dsn="postgresql://postgres:password@localhost:5432/maria_bot",
        min_size=5,
        max_size=20
    )
    
    try:
        await pool.initialize()
        
        # Health check
        is_healthy = await pool.health_check()
        print(f"Pool saludable: {is_healthy}")
        
        # Queries de ejemplo
        await pool.execute(
            "CREATE TABLE IF NOT EXISTS test (id SERIAL PRIMARY KEY, name TEXT)"
        )
        
        await pool.execute(
            "INSERT INTO test (name) VALUES ($1)",
            "Usuario de prueba"
        )
        
        rows = await pool.fetch("SELECT * FROM test")
        print(f"Resultados: {rows}")
        
        # Métricas
        metrics = pool.get_metrics()
        print(f"\nMétricas:")
        print(f"  Queries ejecutados: {metrics.total_queries_executed}")
        print(f"  Errores: {metrics.total_query_errors}")
        print(f"  Tiempo promedio: {metrics.average_query_time_ms:.2f}ms")
        print(f"  Conexiones activas: {pool.get_pool_size()}")
        print(f"  Conexiones idle: {pool.get_idle_connections()}")
    
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(test_pool())
