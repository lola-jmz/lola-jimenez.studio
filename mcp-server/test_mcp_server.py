#!/usr/bin/env python3
"""
Script de testing para el MCP Server de Bot Lola.
Valida que todas las conexiones y herramientas funcionen correctamente.
"""

import asyncio
import sys
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Importar módulos del MCP Server
try:
    from config import Config, db, cache, gemini, initialize_all, close_all
    from tools import (
        analyze_conversation,
        test_personality_prompt,
        get_conversion_metrics,
        detect_red_flags,
        export_training_data
    )
except ImportError as e:
    logger.error(f"❌ Error importando módulos: {e}")
    logger.error("Ejecuta desde el directorio mcp-server/")
    sys.exit(1)


class TestResults:
    """Contenedor para resultados de tests"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def add_pass(self, name: str, message: str = ""):
        self.passed += 1
        self.tests.append({"name": name, "status": "✅ PASS", "message": message})
        logger.info(f"✅ {name}: OK {message}")
    
    def add_fail(self, name: str, error: str):
        self.failed += 1
        self.tests.append({"name": name, "status": "❌ FAIL", "message": error})
        logger.error(f"❌ {name}: FAILED - {error}")
    
    def summary(self):
        total = self.passed + self.failed
        logger.info("\n" + "="*60)
        logger.info("RESUMEN DE TESTS")
        logger.info("="*60)
        for test in self.tests:
            logger.info(f"{test['status']} {test['name']}")
            if test['message']:
                logger.info(f"    {test['message']}")
        logger.info("="*60)
        logger.info(f"Total: {total} tests | ✅ Passed: {self.passed} | ❌ Failed: {self.failed}")
        logger.info("="*60)
        
        return self.failed == 0


async def test_postgresql_connection(results: TestResults):
    """Test 1: Conexión a PostgreSQL"""
    try:
        # Intentar query simple
        result = await db.fetchval("SELECT 1")
        
        if result == 1:
            # Verificar que existen las tablas necesarias
            tables = await db.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                  AND table_name IN ('users', 'conversations', 'messages', 'payments', 'audit_log')
            """)
            
            table_names = [t["table_name"] for t in tables]
            
            if len(table_names) == 5:
                results.add_pass("PostgreSQL Connection", f"5 tablas encontradas")
            else:
                results.add_fail("PostgreSQL Connection", f"Solo {len(table_names)} tablas encontradas: {table_names}")
        else:
            results.add_fail("PostgreSQL Connection", "Health check retornó valor inesperado")
    
    except Exception as e:
        results.add_fail("PostgreSQL Connection", str(e))


async def test_redis_connection(results: TestResults):
    """Test 2: Conexión a Redis"""
    try:
        # Intentar ping
        await cache.client.ping()
        
        # Test set/get
        test_key = "mcp_test_key"
        test_value = "test_value_123"
        
        await cache.set(test_key, test_value, ex=10)
        retrieved = await cache.get(test_key)
        
        if retrieved == test_value:
            await cache.delete(test_key)
            results.add_pass("Redis Connection", "SET/GET funcionando")
        else:
            results.add_fail("Redis Connection", f"GET retornó '{retrieved}' en vez de '{test_value}'")
    
    except Exception as e:
        results.add_fail("Redis Connection", str(e))


async def test_gemini_client(results: TestResults):
    """Test 3: Cliente Gemini AI"""
    try:
        if not gemini.model:
            results.add_fail("Gemini Client", "Cliente no inicializado (falta GEMINI_API_KEY?)")
            return
        
        # Test generación de respuesta simple
        response = await gemini.generate_response(
            prompt="Di solo 'OK'",
            system_instruction="Responde exactamente lo que te piden"
        )
        
        if response and len(response) > 0:
            results.add_pass("Gemini Client", f"Respuesta generada: '{response[:50]}...'")
        else:
            results.add_fail("Gemini Client", "No se generó respuesta")
    
    except Exception as e:
        results.add_fail("Gemini Client", str(e))


async def test_analyze_conversation(results: TestResults):
    """Test 4: Herramienta analyze_conversation"""
    try:
        # Buscar un user_id existente
        user_row = await db.fetchrow("SELECT user_id FROM users LIMIT 1")
        
        if not user_row:
            results.add_fail("analyze_conversation", "No hay usuarios en la BD para probar")
            return
        
        user_id = str(user_row["user_id"])
        
        result = await analyze_conversation(user_id, db, cache)
        
        if "error" in result:
            results.add_fail("analyze_conversation", result["error"])
        elif "user_info" in result and "message_history" in result:
            msg_count = len(result["message_history"])
            results.add_pass("analyze_conversation", f"Analizó user {user_id} ({msg_count} mensajes)")
        else:
            results.add_fail("analyze_conversation", "Formato de respuesta incorrecto")
    
    except Exception as e:
        results.add_fail("analyze_conversation", str(e))


async def test_personality_variant(results: TestResults):
    """Test 5: Herramienta test_personality_prompt"""
    try:
        if not gemini.model:
            results.add_fail("test_personality_prompt", "Gemini no disponible (skipping)")
            return
        
        variant = "Usa más emojis en tus respuestas"
        test_msgs = ["Hola Lola", "Cuánto cuesta el topless?"]
        
        result = await test_personality_prompt(variant, test_msgs, gemini, Config)
        
        if "error" in result:
            results.add_fail("test_personality_prompt", result["error"])
        elif "comparison" in result and "original_responses" in result:
            results.add_pass("test_personality_prompt", f"Comparó {len(test_msgs)} respuestas")
        else:
            results.add_fail("test_personality_prompt", "Formato de respuesta incorrecto")
    
    except Exception as e:
        results.add_fail("test_personality_prompt", str(e))


async def test_conversion_metrics(results: TestResults):
    """Test 6: Herramienta get_conversion_metrics"""
    try:
        # Rango de últimos 7 días
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        date_range = f"{start_date.strftime('%Y-%m-%d')}:{end_date.strftime('%Y-%m-%d')}"
        
        result = await get_conversion_metrics(date_range, db)
        
        if "error" in result:
            results.add_fail("get_conversion_metrics", result["error"])
        elif "metrics" in result and "total_users" in result["metrics"]:
            total_users = result["metrics"]["total_users"]
            conversion_rate = result["metrics"]["conversion_rate"]
            results.add_pass("get_conversion_metrics", f"{total_users} users, {conversion_rate}% conversión")
        else:
            results.add_fail("get_conversion_metrics", "Formato de respuesta incorrecto")
    
    except Exception as e:
        results.add_fail("get_conversion_metrics", str(e))


async def test_detect_red_flags_tool(results: TestResults):
    """Test 7: Herramienta detect_red_flags"""
    try:
        # Buscar un user_id existente
        user_row = await db.fetchrow("SELECT user_id FROM users LIMIT 1")
        
        if not user_row:
            results.add_fail("detect_red_flags", "No hay usuarios en la BD para probar")
            return
        
        user_id = str(user_row["user_id"])
        
        result = await detect_red_flags(user_id, db, cache)
        
        if "error" in result:
            results.add_fail("detect_red_flags", result["error"])
        elif "risk_score" in result and "risk_level" in result:
            risk_score = result["risk_score"]
            risk_level = result["risk_level"]
            red_flags_count = result.get("red_flags_count", 0)
            results.add_pass("detect_red_flags", f"Score: {risk_score}/100 ({risk_level}), {red_flags_count} flags")
        else:
            results.add_fail("detect_red_flags", "Formato de respuesta incorrecto")
    
    except Exception as e:
        results.add_fail("detect_red_flags", str(e))


async def test_export_training_data_tool(results: TestResults):
    """Test 8: Herramienta export_training_data"""
    try:
        filters = {
            "only_successful_conversions": False,  # Permitir cualquier conversación para test
            "min_messages": 3,
            "exclude_blocked_users": True
        }
        
        result = await export_training_data(filters, db, Config)
        
        if "error" in result:
            # Es OK si no hay datos para exportar
            if "No se encontraron conversaciones" in result["error"]:
                results.add_pass("export_training_data", "No hay conversaciones (esperado en BD vacía)")
            else:
                results.add_fail("export_training_data", result["error"])
        elif "export_path" in result and "stats" in result:
            stats = result["stats"]
            results.add_pass("export_training_data", f"{stats['total_conversations']} conversaciones exportadas")
        else:
            results.add_fail("export_training_data", "Formato de respuesta incorrecto")
    
    except Exception as e:
        results.add_fail("export_training_data", str(e))


async def main():
    """Ejecuta todos los tests"""
    
    logger.info("\n" + "="*60)
    logger.info("MCP SERVER BOT LOLA - TEST SUITE")
    logger.info("="*60 + "\n")
    
    results = TestResults()
    
    try:
        # Inicializar conexiones
        logger.info("Inicializando conexiones...")
        await initialize_all()
        logger.info("")
        
        # Ejecutar tests
        logger.info("Ejecutando tests...\n")
        
        await test_postgresql_connection(results)
        await test_redis_connection(results)
        await test_gemini_client(results)
        await test_analyze_conversation(results)
        await test_personality_variant(results)
        await test_conversion_metrics(results)
        await test_detect_red_flags_tool(results)
        await test_export_training_data_tool(results)
        
        # Mostrar resumen
        logger.info("")
        success = results.summary()
        
        if success:
            logger.info("\n🎉 ¡Todos los tests pasaron! El MCP Server está listo para usar.\n")
            return 0
        else:
            logger.error("\n⚠️  Algunos tests fallaron. Revisa los errores arriba.\n")
            return 1
    
    except Exception as e:
        logger.error(f"\n❌ Error fatal durante tests: {e}", exc_info=True)
        return 1
    
    finally:
        # Cerrar conexiones
        await close_all()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
