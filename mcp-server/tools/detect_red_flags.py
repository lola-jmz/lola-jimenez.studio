"""
Herramienta MCP: detect_red_flags
Detecta comportamientos sospechosos y calcula score de riesgo
"""

import logging
from typing import Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def detect_red_flags(user_id: str, db, cache) -> Dict:
    """
    Detecta red flags y calcula score de riesgo para un usuario.
    
    Args:
        user_id: ID del usuario a analizar
        db: Conexión a base de datos
        cache: Conexión a Redis
        
    Returns:
        Dict con score de riesgo y red flags detectados
    """
    try:
        user_id_int = int(user_id)
    except ValueError:
        return {"error": f"user_id inválido: {user_id}. Debe ser un número."}
    
    logger.info(f"🚨 Detectando red flags para user {user_id}")
    
    # 1. Obtener información del usuario
    user_query = """
        SELECT user_id, username, abuse_score, is_blocked, 
               created_at, last_activity
        FROM users
        WHERE user_id = $1
    """
    user_row = await db.fetchrow(user_query, user_id_int)
    
    if not user_row:
        return {"error": f"Usuario {user_id} no encontrado"}
    
    # 2. Analizar mensajes del usuario
    messages_query = """
        SELECT message, created_at
        FROM messages
        WHERE user_id = $1
          AND is_bot = FALSE
        ORDER BY created_at DESC
        LIMIT 100
    """
    messages = await db.fetch(messages_query, user_id_int)
    
    # 3. Verificar pagos
    payments_query = """
        SELECT payment_id, amount, status, is_validated, 
               created_at, validated_at
        FROM payments
        WHERE user_id = $1
        ORDER BY created_at DESC
    """
    payments = await db.fetch(payments_query, user_id_int)
    
    # 4. Detectar red flags
    red_flags = []
    risk_score = 0
    
    # Flag 1: Abuse score alto
    if user_row["abuse_score"] > 50:
        severity = "CRITICAL" if user_row["abuse_score"] > 80 else "HIGH"
        red_flags.append({
            "type": "HIGH_ABUSE_SCORE",
            "severity": severity,
            "description": f"Abuse score de {user_row['abuse_score']} (threshold: 50)",
            "risk_points": 30 if severity == "CRITICAL" else 20
        })
        risk_score += 30 if severity == "CRITICAL" else 20
    
    # Flag 2: Usuario bloqueado
    if user_row["is_blocked"]:
        red_flags.append({
            "type": "USER_BLOCKED",
            "severity": "CRITICAL",
            "description": "Usuario está bloqueado en el sistema",
            "risk_points": 100
        })
        risk_score = 100  # Automáticamente máximo riesgo
    
    # Flag 3: Análisis de mensajes
    message_flags, message_risk = await analyze_message_patterns(messages)
    red_flags.extend(message_flags)
    risk_score += message_risk
    
    # Flag 4: Análisis de pagos
    payment_flags, payment_risk = await analyze_payment_patterns(payments)
    red_flags.extend(payment_flags)
    risk_score += payment_risk
    
    # Flag 5: Comportamiento temporal
    temporal_flags, temporal_risk = await analyze_temporal_behavior(messages, user_row)
    red_flags.extend(temporal_flags)
    risk_score += temporal_risk
    
    # Limitar score a 100
    risk_score = min(risk_score, 100)
    
    # Determinar nivel de riesgo
    if risk_score >= 75:
        risk_level = "CRITICAL"
    elif risk_score >= 50:
        risk_level = "HIGH"
    elif risk_score >= 25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    # Generar patrones de comportamiento
    behavioral_patterns = generate_behavioral_patterns(messages, payments)
    
    # Generar recomendaciones
    recommendations = generate_recommendations(risk_level, red_flags)
    
    result = {
        "user_id": user_id_int,
        "username": user_row["username"],
        "risk_score": risk_score,
        "risk_level": risk_level,
        "red_flags": red_flags,
        "red_flags_count": len(red_flags),
        "behavioral_patterns": behavioral_patterns,
        "recommendations": recommendations,
        "analysis_timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"✅ Red flags detectados: {len(red_flags)}, Risk score: {risk_score}/100 ({risk_level})")
    return result


async def analyze_message_patterns(messages) -> tuple[List[Dict], int]:
    """Analiza patrones sospechosos en mensajes"""
    red_flags = []
    risk_points = 0
    
    if not messages:
        return red_flags, risk_points
    
    # Crear texto combinado para análisis
    all_messages = [msg["message"] for msg in messages]
    combined_text = " ".join(all_messages).lower()
    
    # Patrón 1: Solicitudes de información personal
    personal_info_keywords = [
        "donde vives", "dónde vives", "tu dirección", "tu direccion",
        "que universidad", "qué universidad", "donde estudias", "dónde estudias",
        "tu nombre completo", "apellido", "telefono", "teléfono"
    ]
    personal_info_count = sum(1 for kw in personal_info_keywords if kw in combined_text)
    
    if personal_info_count >= 3:
        red_flags.append({
            "type": "PERSONAL_INFO_REQUESTS",
            "count": personal_info_count,
            "severity": "HIGH",
            "description": f"Solicitó información personal {personal_info_count} veces",
            "risk_points": 25
        })
        risk_points += 25
    
    # Patrón 2: Insistencia en encuentros físicos
    meeting_keywords = [
        "vernos", "conocernos", "salir juntos", "encuentro", 
        "reunirnos", "en persona", "cita", "te invito"
    ]
    meeting_count = sum(1 for kw in meeting_keywords if kw in combined_text)
    
    if meeting_count >= 3:
        severity = "CRITICAL" if meeting_count >= 5 else "HIGH"
        risk_pts = 30 if meeting_count >= 5 else 20
        red_flags.append({
            "type": "INSISTENCE_ON_MEETING",
            "count": meeting_count,
            "severity": severity,
            "description": f"Insistió en encuentro físico {meeting_count} veces",
            "risk_points": risk_pts
        })
        risk_points += risk_pts
    
    # Patrón 3: Lenguaje abusivo/ofensivo
    abusive_keywords = [
        "puta", "perra", "zorra", "estúpida", "estupida", 
        "idiota", "pendeja", "culera", "pinche"
    ]
    abusive_count = sum(1 for kw in abusive_keywords if kw in combined_text)
    
    if abusive_count > 0:
        red_flags.append({
            "type": "ABUSIVE_LANGUAGE",
            "count": abusive_count,
            "severity": "CRITICAL",
            "description": "Uso de lenguaje abusivo u ofensivo",
            "risk_points": 40
        })
        risk_points += 40
    
    # Patrón 4: Spam / Mensajes repetitivos
    if len(messages) > 20:
        # Verificar si hay muchos mensajes idénticos
        unique_messages = set(all_messages)
        repetition_ratio = 1 - (len(unique_messages) / len(all_messages))
        
        if repetition_ratio > 0.5:  # Más del 50% son repetidos
            red_flags.append({
                "type": "SPAM_DETECTED",
                "severity": "MEDIUM",
                "description": f"Patrón de spam detectado ({repetition_ratio*100:.0f}% mensajes repetidos)",
                "risk_points": 15
            })
            risk_points += 15
    
    # Patrón 5: Amenazas o extorsión
    threat_keywords = ["voy a reportar", "denunciar", "abogado", "policía", "policia", "demanda"]
    threat_count = sum(1 for kw in threat_keywords if kw in combined_text)
    
    if threat_count > 0:
        red_flags.append({
            "type": "THREATS_DETECTED",
            "count": threat_count,
            "severity": "CRITICAL",
            "description": "Posibles amenazas o extorsión detectadas",
            "risk_points": 35
        })
        risk_points += 35
    
    return red_flags, risk_points


async def analyze_payment_patterns(payments) -> tuple[List[Dict], int]:
    """Analiza patrones sospechosos en pagos"""
    red_flags = []
    risk_points = 0
    
    if not payments:
        return red_flags, risk_points
    
    # Patrón 1: Pagos pendientes sin validar (posible fraude)
    pending_payments = [p for p in payments if p["status"] == "pending" and not p["is_validated"]]
    
    if len(pending_payments) >= 3:
        red_flags.append({
            "type": "MULTIPLE_PENDING_PAYMENTS",
            "count": len(pending_payments),
            "severity": "HIGH",
            "description": f"{len(pending_payments)} pagos pendientes sin validar (posible fraude)",
            "risk_points": 20
        })
        risk_points += 20
    
    # Patrón 2: Disputas de pago
    failed_payments = [p for p in payments if p["status"] == "failed"]
    
    if len(failed_payments) >= 2:
        red_flags.append({
            "type": "FAILED_PAYMENTS",
            "count": len(failed_payments),
            "severity": "MEDIUM",
            "description": f"{len(failed_payments)} pagos fallidos",
            "risk_points": 10
        })
        risk_points += 10
    
    # Patrón 3: Tiempo excesivo sin validación
    for payment in payments:
        if payment["status"] == "pending" and not payment["is_validated"]:
            time_pending = datetime.now(payment["created_at"].tzinfo) - payment["created_at"]
            
            if time_pending.days > 7:  # Más de 7 días
                red_flags.append({
                    "type": "LONG_PENDING_PAYMENT",
                    "severity": "MEDIUM",
                    "description": f"Pago pendiente por {time_pending.days} días sin validar",
                    "risk_points": 15
                })
                risk_points += 15
                break  # Solo reportar el primero
    
    return red_flags, risk_points


async def analyze_temporal_behavior(messages, user_row) -> tuple[List[Dict], int]:
    """Analiza comportamiento temporal sospechoso"""
    red_flags = []
    risk_points = 0
    
    if not messages or len(messages) < 5:
        return red_flags, risk_points
    
    # Patrón 1: Mensajes en ráfaga (muchos mensajes en poco tiempo)
    recent_messages = [m for m in messages if (datetime.now(m["created_at"].tzinfo) - m["created_at"]).total_seconds() < 3600]
    
    if len(recent_messages) >= 15:  # 15+ mensajes en 1 hora
        red_flags.append({
            "type": "MESSAGE_BURST",
            "count": len(recent_messages),
            "severity": "MEDIUM",
            "description": f"{len(recent_messages)} mensajes en la última hora (comportamiento obsesivo)",
            "risk_points": 15
        })
        risk_points += 15
    
    # Patrón 2: Cuenta muy nueva con actividad intensa
    account_age = datetime.now(user_row["created_at"].tzinfo) - user_row["created_at"]
    
    if account_age.days < 1 and len(messages) > 30:
        red_flags.append({
            "type": "NEW_ACCOUNT_HIGH_ACTIVITY",
            "severity": "MEDIUM",
            "description": f"Cuenta nueva ({account_age.seconds//3600}h) con {len(messages)} mensajes",
            "risk_points": 10
        })
        risk_points += 10
    
    return red_flags, risk_points


def generate_behavioral_patterns(messages, payments) -> Dict:
    """Genera resumen de patrones de comportamento"""
    
    message_count = len(messages)
    
    # Frecuencia de mensajes
    if message_count == 0:
        frequency = "Sin actividad"
    elif message_count < 10:
        frequency = "Baja actividad"
    elif message_count < 30:
        frequency = "Actividad normal"
    elif message_count < 50:
        frequency = "Actividad alta"
    else:
        frequency = f"Actividad muy alta ({message_count} mensajes)"
    
    # Calcular si hay actividad en última hora
    if messages:
        recent = any((datetime.now(m["created_at"].tzinfo) - m["created_at"]).total_seconds() < 3600 for m in messages)
    else:
        recent = False
    
    # Analizar spam
    if messages:
        unique_msgs = len(set(m["message"] for m in messages))
        spam_detected = (unique_msgs / len(messages)) < 0.5 if len(messages) > 10 else False
    else:
        spam_detected = False
    
    # Analizar lenguaje abusivo (simplificado)
    abusive_keywords = ["puta", "perra", "idiota", "pendeja"]
    abusive_language = False
    if messages:
        combined = " ".join(m["message"] for m in messages).lower()
        abusive_language = any(kw in combined for kw in abusive_keywords)
    
    return {
        "message_frequency": frequency,
        "recent_activity": recent,
        "spam_detected": spam_detected,
        "abusive_language": abusive_language,
        "total_payments": len(payments),
        "completed_payments": len([p for p in payments if p["status"] == "completed"])
    }


def generate_recommendations(risk_level: str, red_flags: List[Dict]) -> List[str]:
    """Genera recomendaciones basadas en nivel de riesgo"""
    recommendations = []
    
    if risk_level == "CRITICAL":
        recommendations.append("🚨 BLOQUEAR USUARIO INMEDIATAMENTE")
        recommendations.append("Revisar manualmente todos los pagos pendientes")
        recommendations.append("Considerar reporte a autoridades si hay amenazas")
    
    elif risk_level == "HIGH":
        recommendations.append("⚠️ Activar Fase de Protección inmediatamente")
        recommendations.append("NO procesar pagos sin validación manual exhaustiva")
        recommendations.append("Monitorear actividad de cerca")
    
    elif risk_level == "MEDIUM":
        recommendations.append("⚡ Aumentar nivel de vigilancia")
        recommendations.append("Validar manualmente cualquier pago")
        recommendations.append("Considerar bloqueo temporal si persisten red flags")
    
    else:  # LOW
        recommendations.append("✅ Usuario de bajo riesgo")
        recommendations.append("Continuar operación normal")
    
    # Recomendaciones específicas por tipo de flag
    flag_types = [f["type"] for f in red_flags]
    
    if "ABUSIVE_LANGUAGE" in flag_types:
        recommendations.append("🛑 Prioridad: Aplicar políticas de tolerancia cero a abuso")
    
    if "INSISTENCE_ON_MEETING" in flag_types:
        recommendations.append("🔒 Mantener estrictamente política de solo contenido digital")
    
    if "PERSONAL_INFO_REQUESTS" in flag_types:
        recommendations.append("🤐 NO revelar ninguna información personal adicional")
    
    return recommendations
