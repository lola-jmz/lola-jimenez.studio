#!/usr/bin/env python3
"""
MCP Server para análisis de conversaciones de Bot Lola.

Expone herramientas MCP para:
- Analizar conversaciones de usuarios
- Probar variantes de personalidad
- Obtener métricas de conversión
- Detectar red flags
- Exportar datos de entrenamiento

Uso:
    python server.py
"""

import asyncio
import logging
import sys
import json
from typing import Any, Dict

# Configurar logging
# IMPORTANTE: Los logs van a stderr para no interferir con la comunicación MCP por stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Importar configuración y herramientas
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
    logger.error(f"Error importando módulos: {e}")
    logger.error("Asegúrate de estar en el directorio correcto y tener todas las dependencias instaladas")
    sys.exit(1)

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    import mcp.server.stdio
except ImportError:
    logger.error("MCP SDK no instalado. Ejecuta: pip install mcp")
    sys.exit(1)


# Crear servidor MCP
app = Server(Config.MCP_SERVER_NAME)


# === REGISTRAR HERRAMIENTAS MCP ===

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Lista todas las herramientas disponibles"""
    return [
        Tool(
            name="analyze_conversation",
            description="Analiza la conversación de un usuario específico, incluyendo historial de mensajes, "
                        "red flags detectados, sugerencias de personalidad y métricas de engagement",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "ID del usuario a analizar (número)"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="test_personality_prompt",
            description="Prueba una variante de personalidad de Lola comparando respuestas generadas "
                        "con el prompt original vs una versión modificada",
            inputSchema={
                "type": "object",
                "properties": {
                    "variant_text": {
                        "type": "string",
                        "description": "Modificación propuesta a la personalidad (ej: 'usa más emojis')"
                    },
                    "test_messages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de mensajes de prueba del usuario"
                    }
                },
                "required": ["variant_text", "test_messages"]
            }
        ),
        Tool(
            name="get_conversion_metrics",
            description="Obtiene métricas de conversión y revenue para un rango de fechas específico",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_range": {
                        "type": "string",
                        "description": "Rango de fechas en formato YYYY-MM-DD:YYYY-MM-DD (ej: 2025-11-01:2025-11-28)"
                    }
                },
                "required": ["date_range"]
            }
        ),
        Tool(
            name="detect_red_flags",
            description="Detecta comportamientos sospechosos de un usuario y calcula su score de riesgo (0-100)",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "ID del usuario a analizar (número)"
                    }
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="export_training_data",
            description="Exporta conversaciones exitosas en formato JSONL para fine-tuning de Gemini AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "filters": {
                        "type": "object",
                        "description": "Criterios de filtrado",
                        "properties": {
                            "only_successful_conversions": {
                                "type": "boolean",
                                "description": "Solo exportar conversaciones que resultaron en venta"
                            },
                            "min_messages": {
                                "type": "integer",
                                "description": "Mínimo de mensajes en la conversación"
                            },
                            "date_range": {
                                "type": "string",
                                "description": "Rango de fechas (YYYY-MM-DD:YYYY-MM-DD)"
                            },
                            "exclude_blocked_users": {
                                "type": "boolean",
                                "description": "Excluir usuarios bloqueados"
                            }
                        }
                    }
                },
                "required": ["filters"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Ejecuta una herramienta MCP"""
    
    logger.info(f"🔧 Ejecutando herramienta: {name}")
    
    try:
        result = None
        
        if name == "analyze_conversation":
            user_id = arguments.get("user_id")
            result = await analyze_conversation(user_id, db, cache)
        
        elif name == "test_personality_prompt":
            variant_text = arguments.get("variant_text")
            test_messages = arguments.get("test_messages", [])
            result = await test_personality_prompt(variant_text, test_messages, gemini, Config)
        
        elif name == "get_conversion_metrics":
            date_range = arguments.get("date_range")
            result = await get_conversion_metrics(date_range, db)
        
        elif name == "detect_red_flags":
            user_id = arguments.get("user_id")
            result = await detect_red_flags(user_id, db, cache)
        
        elif name == "export_training_data":
            filters = arguments.get("filters", {})
            result = await export_training_data(filters, db, Config)
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Herramienta desconocida: {name}"})
            )]
        
        # Convertir resultado a JSON
        result_json = json.dumps(result, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Herramienta {name} ejecutada correctamente")
        
        return [TextContent(
            type="text",
            text=result_json
        )]
    
    except Exception as e:
        logger.error(f"❌ Error ejecutando {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name,
                "traceback": str(e.__traceback__)
            })
        )]


async def main():
    """Punto de entrada principal del servidor MCP"""
    
    logger.info(f"🚀 Iniciando {Config.MCP_SERVER_NAME} v{Config.MCP_SERVER_VERSION}")
    
    try:
        # Inicializar conexiones
        await initialize_all()
        
        # Ejecutar servidor MCP
        logger.info("📡 Servidor MCP listo para recibir conexiones...")
        
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    
    except KeyboardInterrupt:
        logger.info("⚠️  Servidor interrumpido por usuario")
    
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
    
    finally:
        # Cerrar conexiones
        await close_all()
        logger.info("👋 Servidor MCP cerrado correctamente")


if __name__ == "__main__":
    asyncio.run(main())
