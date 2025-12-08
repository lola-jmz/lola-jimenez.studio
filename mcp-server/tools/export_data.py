"""
Herramienta MCP: export_training_data
Exporta conversaciones exitosas en formato JSONL para fine-tuning de Gemini
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


async def export_training_data(filters: Dict, db, config) -> Dict:
    """
    Exporta conversaciones en formato JSONL para fine-tuning.
    
    Args:
        filters: Criterios de filtrado
            - only_successful_conversions: bool
            - min_messages: int
            - date_range: str (YYYY-MM-DD:YYYY-MM-DD)
            - exclude_blocked_users: bool
        db: Conexión a base de datos
        config: Configuración (para obtener EXPORTS_DIR)
        
    Returns:
        Dict con path del archivo exportado y estadísticas
    """
    logger.info(f"📦 Exportando datos de entrenamiento con filtros: {filters}")
    
    # Parsear filtros
    only_successful = filters.get("only_successful_conversions", True)
    min_messages = filters.get("min_messages", 5)
    date_range = filters.get("date_range", None)
    exclude_blocked = filters.get("exclude_blocked_users", True)
    
    # Parsear rango de fechas si existe
    start_date = None
    end_date = None
    
    if date_range:
        try:
            start_str, end_str = date_range.split(":")
            start_date = datetime.strptime(start_str.strip(), "%Y-%m-%d")
            end_date = datetime.strptime(end_str.strip(), "%Y-%m-%d")
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            return {
                "error": f"Formato de fecha inválido: {date_range}",
                "example": "2025-11-01:2025-11-28"
            }
    
    # 1. Obtener conversaciones que cumplan criterios
    conversations = await get_filtered_conversations(
        db, only_successful, min_messages, start_date, end_date, exclude_blocked
    )
    
    if not conversations:
        return {
            "error": "No se encontraron conversaciones que cumplan los criterios",
            "filters_used": filters
        }
    
    logger.info(f"✅ Encontradas {len(conversations)} conversaciones para exportar")
    
    # 2. Construir datos de entrenamiento en formato JSONL
    training_examples = []
    total_messages = 0
    
    for conv in conversations:
        user_id = conv["user_id"]
        
        # Obtener mensajes de la conversación
        messages = await get_conversation_messages(db, user_id)
        
        if len(messages) < min_messages:
            continue
        
        # Formatear en estilo Gemini (alternando user/model)
        formatted_messages = format_messages_for_gemini(messages)
        
        if formatted_messages:
            training_examples.append({
                "messages": formatted_messages
            })
            total_messages += len(formatted_messages)
    
    # 3. Guardar en archivo JSONL
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"training_data_{timestamp}.jsonl"
    filepath = os.path.join(config.EXPORTS_DIR, filename)
    
    # Asegurar que el directorio existe
    os.makedirs(config.EXPORTS_DIR, exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        for example in training_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    # 4. Calcular estadísticas
    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    
    stats = {
        "total_conversations": len(training_examples),
        "total_messages": total_messages,
        "successful_conversions": len([c for c in conversations if c["has_paid"]]),
        "file_size_mb": round(file_size_mb, 2),
        "filters_applied": filters
    }
    
    result = {
        "export_path": filepath,
        "stats": stats,
        "export_timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"✅ Exportación completada: {filepath} ({file_size_mb:.2f} MB)")
    return result


async def get_filtered_conversations(
    db,
    only_successful: bool,
    min_messages: int,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    exclude_blocked: bool
) -> List[Dict]:
    """Obtiene conversaciones que cumplen criterios de filtrado"""
    
    # Construir query dinámica
    conditions = []
    params = []
    param_count = 0
    
    if only_successful:
        conditions.append("u.has_paid = TRUE")
    
    if exclude_blocked:
        conditions.append("u.is_blocked = FALSE")
    
    if start_date and end_date:
        param_count += 2
        conditions.append(f"u.created_at BETWEEN ${param_count-1} AND ${param_count}")
        params.extend([start_date, end_date])
    
    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    
    query = f"""
        SELECT DISTINCT u.user_id, u.username, u.has_paid
        FROM users u
        WHERE {where_clause}
    """
    
    rows = await db.fetch(query, *params)
    
    # Filtrar por min_messages
    filtered = []
    for row in rows:
        msg_count = await db.fetchval(
            "SELECT COUNT(*) FROM messages WHERE user_id = $1",
            row["user_id"]
        )
        
        if msg_count >= min_messages:
            filtered.append({
                "user_id": row["user_id"],
                "username": row["username"],
                "has_paid": row["has_paid"]
            })
    
    return filtered


async def get_conversation_messages(db, user_id: int) -> List[Dict]:
    """Obtiene todos los mensajes de un usuario ordenados cronológicamente"""
    
    query = """
        SELECT message, is_bot, created_at
        FROM messages
        WHERE user_id = $1
        ORDER BY created_at ASC
    """
    
    rows = await db.fetch(query, user_id)
    
    return [
        {
            "message": row["message"],
            "is_bot": row["is_bot"],
            "created_at": row["created_at"]
        }
        for row in rows
    ]


def format_messages_for_gemini(messages: List[Dict]) -> List[Dict]:
    """
    Formatea mensajes en el formato esperado por Gemini para fine-tuning.
    
    Formato Gemini:
    {
        "messages": [
            {"role": "user", "content": "texto del usuario"},
            {"role": "model", "content": "respuesta de lola"}
        ]
    }
    """
    formatted = []
    
    for msg in messages:
        role = "model" if msg["is_bot"] else "user"
        
        formatted.append({
            "role": role,
            "content": msg["message"]
        })
    
    # Validar que alterne user/model correctamente
    # Gemini espera que empiece con user y alterne
    if not formatted:
        return []
    
    # Si empieza con model, remover primer mensaje
    if formatted[0]["role"] == "model":
        formatted = formatted[1:]
    
    # Si termina con user, remover último mensaje
    if formatted and formatted[-1]["role"] == "user":
        formatted = formatted[:-1]
    
    # Verificar alternancia
    cleaned = []
    expected_role = "user"
    
    for msg in formatted:
        if msg["role"] == expected_role:
            cleaned.append(msg)
            expected_role = "model" if expected_role == "user" else "user"
    
    return cleaned
