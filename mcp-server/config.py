"""
Configuración centralizada para el MCP Server de Bot Lola.
Maneja conexiones a PostgreSQL, Redis y Gemini AI.
"""

import os
import asyncpg
import redis.asyncio as redis
import google.generativeai as genai
from typing import Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()


class Config:
    """Configuración global del MCP Server"""
    
    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:Stafems@localhost:5432/maria_bot"
    )
    
    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    
    # Gemini AI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
    
    # MCP Server
    MCP_SERVER_NAME = os.getenv("MCP_SERVER_NAME", "lola-bot-analysis")
    MCP_SERVER_VERSION = os.getenv("MCP_SERVER_VERSION", "1.0.0")
    
    # Paths
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOLA_PROMPT_PATH = os.path.join(PROJECT_ROOT, "docs", "LOLA.md")
    EXPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
    
    @classmethod
    def validate(cls):
        """Valida que la configuración esté completa"""
        if not cls.GEMINI_API_KEY:
            logger.warning("⚠️  GEMINI_API_KEY no configurada. La herramienta test_personality no funcionará.")
        
        if not os.path.exists(cls.LOLA_PROMPT_PATH):
            logger.warning(f"⚠️  No se encontró LOLA.md en {cls.LOLA_PROMPT_PATH}")
        
        logger.info(f"✅ Configuración cargada: {cls.MCP_SERVER_NAME} v{cls.MCP_SERVER_VERSION}")


class DatabaseConnection:
    """Pool de conexiones a PostgreSQL"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Inicializa el connection pool"""
        try:
            logger.info("Inicializando PostgreSQL connection pool...")
            self.pool = await asyncpg.create_pool(
                dsn=Config.DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            
            # Health check
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    logger.info("✅ PostgreSQL conectado correctamente")
                else:
                    raise Exception("Health check falló")
        
        except Exception as e:
            logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            raise
    
    async def close(self):
        """Cierra el connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ PostgreSQL connection pool cerrado")
    
    async def execute(self, query: str, *args):
        """Ejecuta query sin retorno de datos"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        """Ejecuta query que retorna múltiples filas"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """Ejecuta query que retorna una fila"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args):
        """Ejecuta query que retorna un solo valor"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)


class RedisConnection:
    """Conexión a Redis para cache"""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Inicializa conexión a Redis"""
        try:
            logger.info("Inicializando conexión a Redis...")
            self.client = await redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                password=Config.REDIS_PASSWORD,
                decode_responses=True
            )
            
            # Health check
            await self.client.ping()
            logger.info("✅ Redis conectado correctamente")
        
        except Exception as e:
            logger.error(f"❌ Error conectando a Redis: {e}")
            raise
    
    async def close(self):
        """Cierra conexión a Redis"""
        if self.client:
            await self.client.close()
            logger.info("✅ Redis connection cerrada")
    
    async def get(self, key: str):
        """Obtiene valor de cache"""
        return await self.client.get(key)
    
    async def set(self, key: str, value: str, ex: int = 3600):
        """Guarda valor en cache con TTL"""
        return await self.client.set(key, value, ex=ex)
    
    async def delete(self, key: str):
        """Elimina clave de cache"""
        return await self.client.delete(key)


class GeminiClient:
    """Cliente para Gemini AI"""
    
    def __init__(self):
        self.model = None
    
    def initialize(self):
        """Inicializa cliente Gemini"""
        try:
            if not Config.GEMINI_API_KEY:
                logger.warning("⚠️  GEMINI_API_KEY no configurada, GeminiClient no disponible")
                return
            
            logger.info("Inicializando Gemini AI client...")
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
            logger.info("✅ Gemini AI client inicializado")
        
        except Exception as e:
            logger.error(f"❌ Error inicializando Gemini: {e}")
            raise
    
    async def generate_response(self, prompt: str, system_instruction: str = "") -> str:
        """Genera respuesta con Gemini"""
        if not self.model:
            raise Exception("Gemini client no inicializado")
        
        try:
            # Combinar system instruction con prompt
            full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
            
            response = await self.model.generate_content_async(full_prompt)
            return response.text
        
        except Exception as e:
            logger.error(f"❌ Error generando respuesta con Gemini: {e}")
            raise


# Instancias globales
db = DatabaseConnection()
cache = RedisConnection()
gemini = GeminiClient()


async def initialize_all():
    """Inicializa todas las conexiones"""
    Config.validate()
    await db.initialize()
    await cache.initialize()
    gemini.initialize()
    logger.info("🚀 Todas las conexiones inicializadas correctamente")


async def close_all():
    """Cierra todas las conexiones"""
    await db.close()
    await cache.close()
    logger.info("👋 Todas las conexiones cerradas correctamente")
