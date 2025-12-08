"""
Herramienta MCP: analyze_conversation
Analiza las conversaciones de un usuario con Bot Lola
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


async def analyze_conversation(user_id: str, db, cache) -> Dict:
    """
    Analiza la conversación de un usuario específico.
    
    Args:
        user_id: ID del usuario a analizar
        db: Conexión a base de datos
        cache: Conexión a Redis
        
    Returns:
        Dict con análisis completo de la conversación
    """
    try:
        user_id_int = int(user_id)
    except ValueError:
        return {"error": f"user_id inválido: {user_id}. Debe ser un número."}
    
    # Verificar cache primero
    cache_key = f"analysis:{user_id}"
    cached_result = await cache.get(cache_key)
    if cached_result:
        logger.info(f"✅ Análisis encontrado en cache para user {user_id}")
        return json.loads(cached_result)
    
    logger.info(f"🔍 Analizando conversación para user {user_id}")
    
    # 1. Obtener información del usuario
    user_query = """
        SELECT user_id, username, first_name, last_name, 
               has_paid, total_purchases, abuse_score,
               is_blocked, created_at, last_activity
        FROM users
        WHERE user_id = $1
    """
    user_row = await db.fetchrow(user_query, user_id_int)
    
    if not user_row:
        return {"error": f"Usuario {user_id} no encontrado en la base de datos"}
    
    user_info = {
        "user_id": user_row["user_id"],
        "username": user_row["username"],
        "first_name": user_row["first_name"],
        "last_name": user_row["last_name"],
        "has_paid": user_row["has_paid"],
        "total_purchases": user_row["total_purchases"],
        "abuse_score": user_row["abuse_score"],
        "is_blocked": user_row["is_blocked"],
        "created_at": user_row["created_at"].isoformat() if user_row["created_at"] else None,
        "last_activity": user_row["last_activity"].isoformat() if user_row["last_activity"] else None
    }
    
    # 2. Obtener estado de conversación actual
    conversation_query = """
        SELECT conversation_id, state, context, selected_product_id,
               started_at, updated_at, ended_at
        FROM conversations
        WHERE user_id = $1
        ORDER BY updated_at DESC
        LIMIT 1
    """
    conv_row = await db.fetchrow(conversation_query, user_id_int)
    
    conversation_state = None
    if conv_row:
        conversation_state = {
            "conversation_id": str(conv_row["conversation_id"]),
            "state": conv_row["state"],
            "context": conv_row["context"],
            "selected_product_id": conv_row["selected_product_id"],
            "started_at": conv_row["started_at"].isoformat() if conv_row["started_at"] else None,
            "updated_at": conv_row["updated_at"].isoformat() if conv_row["updated_at"] else None,
            "ended_at": conv_row["ended_at"].isoformat() if conv_row["ended_at"] else None
        }
    
    # 3. Obtener historial de mensajes
    messages_query = """
        SELECT message, is_bot, message_type, metadata, created_at
        FROM messages
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 50
    """
    messages_rows = await db.fetch(messages_query, user_id_int)
    
    message_history = [
        {
            "message": row["message"],
            "is_bot": row["is_bot"],
            "message_type": row["message_type"],
            "metadata": row["metadata"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None
        }
        for row in messages_rows
    ]
    
    # Ordenar cronológicamente (más antiguo primero)
    message_history.reverse()
    
    # 4. Detectar red flags en los mensajes
    red_flags = await detect_red_flags_in_messages(message_history, user_info)
    
    # 5. Generar sugerencias de personalidad
    personality_suggestions = await generate_personality_suggestions(message_history, user_info)
    
    # 6. Calcular métricas de engagement
    engagement_metrics = await calculate_engagement_metrics(messages_rows, user_info)
    
    # Construir resultado
    result = {
        "user_info": user_info,
        "conversation_state": conversation_state,
        "message_history": message_history,
        "red_flags": red_flags,
        "personality_suggestions": personality_suggestions,
        "engagement_metrics": engagement_metrics,
        "analysis_timestamp": datetime.now().isoformat()
    }
    
    # Guardar en cache por 10 minutos
    await cache.set(cache_key, json.dumps(result), ex=600)
    
    logger.info(f"✅ Análisis completado para user {user_id}")
    return result


async def detect_red_flags_in_messages(messages: List[Dict], user_info: Dict) -> List[Dict]:
    """Detecta red flags en el historial de mensajes"""
    red_flags = []
    
    # Keywords sospechosas
    personal_info_keywords = ["dónde", "donde", "vives", "universidad", "uni ", "estudias", "dirección", "direccion"]
    meeting_keywords = ["vernos", "conocernos", "salir", "encuentro", "reunirnos", "cita"]
    aggressive_keywords = ["puta", "perra", "estúpida", "estupida", "idiota", "pendeja"]
    
    user_messages = [m for m in messages if not m["is_bot"]]
    
    # Contar menciones de info personal
    personal_info_count = sum(
        1 for msg in user_messages
        if any(keyword in msg["message"].lower() for keyword in personal_info_keywords)
    )
    
    if personal_info_count >= 3:
        red_flags.append({
            "type": "PERSONAL_INFO_REQUESTS",
            "count": personal_info_count,
            "severity": "HIGH",
            "description": f"Usuario preguntó {personal_info_count} veces por información personal (ubicación/universidad)"
        })
    
    # Contar insistencia en encuentros
    meeting_count = sum(
        1 for msg in user_messages
        if any(keyword in msg["message"].lower() for keyword in meeting_keywords)
    )
    
    if meeting_count >= 2:
        red_flags.append({
            "type": "INSISTENCE_ON_MEETING",
            "count": meeting_count,
            "severity": "MEDIUM" if meeting_count < 4 else "HIGH",
            "description": f"Usuario insistió {meeting_count} veces en encuentro físico"
        })
    
    # Detectar lenguaje abusivo
    aggressive_count = sum(
        1 for msg in user_messages
        if any(keyword in msg["message"].lower() for keyword in aggressive_keywords)
    )
    
    if aggressive_count > 0:
        red_flags.append({
            "type": "ABUSIVE_LANGUAGE",
            "count": aggressive_count,
            "severity": "CRITICAL",
            "description": "Usuario utilizó lenguaje abusivo/ofensivo"
        })
    
    # Verificar abuse_score del usuario
    if user_info["abuse_score"] > 50:
        red_flags.append({
            "type": "HIGH_ABUSE_SCORE",
            "severity": "HIGH",
            "description": f"Usuario tiene abuse_score de {user_info['abuse_score']} (threshold: 50)"
        })
    
    return red_flags


async def generate_personality_suggestions(messages: List[Dict], user_info: Dict) -> List[str]:
    """Genera sugerencias para ajustar la personalidad de Lola"""
    suggestions = []
    
    if len(messages) == 0:
        return ["No hay mensajes para analizar"]
    
    user_messages = [m for m in messages if not m["is_bot"]]
    bot_messages = [m for m in messages if m["is_bot"]]
    
    # Si hay muchos mensajes pero no ha pagado
    if len(messages) > 20 and not user_info["has_paid"]:
        suggestions.append("⚠️ Conversación larga sin conversión. Considerar fase de filtrado más agresiva.")
    
    # Si el usuario responde rápido
    if len(user_messages) > 10:
        suggestions.append("✅ Usuario altamente comprometido (10+ mensajes). Fase de conversión apropiada.")
    
    # Si usuario ya pagó
    if user_info["has_paid"]:
        suggestions.append("💰 Cliente existente. Activar fase de upselling para contenido premium.")
    
    # Analizar tono del usuario (básico)
    user_text = " ".join([m["message"] for m in user_messages[-5:]])  # Últimos 5 mensajes
    
    if any(word in user_text.lower() for word in ["jaja", "haha", "lol", "😂", "😅"]):
        suggestions.append("😊 Usuario receptivo al humor. Mantener tono amigable actual.")
    
    if any(word in user_text.lower() for word in ["precio", "cuánto", "cuanto", "costo", "pagar"]):
        suggestions.append("💵 Usuario interesado en transacción. Activar fase de conversión directa.")
    
    return suggestions if suggestions else ["✅ Interacción normal, sin ajustes necesarios."]


async def calculate_engagement_metrics(messages_rows, user_info: Dict) -> Dict:
    """Calcula métricas de engagement del usuario"""
    if len(messages_rows) == 0:
        return {
            "total_messages": 0,
            "user_messages": 0,
            "bot_messages": 0,
            "average_response_time_minutes": None,
            "last_interaction": None
        }
    
    total_messages = len(messages_rows)
    user_messages = [m for m in messages_rows if not m["is_bot"]]
    bot_messages = [m for m in messages_rows if m["is_bot"]]
    
    # Calcular tiempo de respuesta promedio (simplificado)
    response_times = []
    for i in range(1, len(messages_rows)):
        if messages_rows[i]["is_bot"] and not messages_rows[i-1]["is_bot"]:
            time_diff = messages_rows[i]["created_at"] - messages_rows[i-1]["created_at"]
            response_times.append(time_diff.total_seconds() / 60)  # minutos
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else None
    
    return {
        "total_messages": total_messages,
        "user_messages": len(user_messages),
        "bot_messages": len(bot_messages),
        "average_response_time_minutes": round(avg_response_time, 2) if avg_response_time else None,
        "last_interaction": user_info["last_activity"],
        "conversation_duration_hours": calculate_conversation_duration(messages_rows)
    }


def calculate_conversation_duration(messages_rows) -> Optional[float]:
    """Calcula duración total de la conversación en horas"""
    if len(messages_rows) < 2:
        return None
    
    first_msg = messages_rows[-1]["created_at"]  # Más antiguo
    last_msg = messages_rows[0]["created_at"]    # Más reciente
    
    duration_seconds = (last_msg - first_msg).total_seconds()
    return round(duration_seconds / 3600, 2)  # horas
