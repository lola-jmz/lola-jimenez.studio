"""
Herramienta MCP: test_personality_prompt
Prueba variantes de personalidad de Lola comparando respuestas
"""

import os
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


async def test_personality_prompt(variant_text: str, test_messages: List[str], gemini, config) -> Dict:
    """
    Prueba una variante de prompt de personalidad contra el original.
    
    Args:
        variant_text: Modificación propuesta a la personalidad
        test_messages: Lista de mensajes de prueba del usuario
        gemini: Cliente Gemini AI
        config: Configuración (para obtener ruta de LOLA.md)
        
    Returns:
        Dict con comparación de respuestas originales vs variantes
    """
    logger.info("🧪 Probando variante de personalidad")
    
    # 1. Cargar personalidad original
    try:
        with open(config.LOLA_PROMPT_PATH, "r", encoding="utf-8") as f:
            original_personality = f.read()
    except FileNotFoundError:
        return {
            "error": f"No se encontró LOLA.md en {config.LOLA_PROMPT_PATH}",
            "suggestion": "Verifica que el archivo docs/LOLA.md exista en el proyecto"
        }
    
    # 2. Crear variante modificada
    variant_personality = f"{original_personality}\n\n## MODIFICACIÓN EXPERIMENTAL:\n{variant_text}"
    
    # 3. Generar respuestas con ambas personalidades
    original_responses = []
    variant_responses = []
    
    for user_message in test_messages:
        # Respuesta original
        try:
            original_prompt = f"Eres Lola. Responde a este mensaje:\n\nUsuario: {user_message}"
            original_response = await gemini.generate_response(
                prompt=original_prompt,
                system_instruction=original_personality
            )
            original_responses.append(original_response.strip())
        except Exception as e:
            logger.error(f"Error generando respuesta original: {e}")
            original_responses.append(f"[ERROR: {str(e)}]")
        
        # Respuesta con variante
        try:
            variant_prompt = f"Eres Lola. Responde a este mensaje:\n\nUsuario: {user_message}"
            variant_response = await gemini.generate_response(
                prompt=variant_prompt,
                system_instruction=variant_personality
            )
            variant_responses.append(variant_response.strip())
        except Exception as e:
            logger.error(f"Error generando respuesta variante: {e}")
            variant_responses.append(f"[ERROR: {str(e)}]")
    
    # 4. Analizar diferencias
    comparison = analyze_response_differences(
        test_messages,
        original_responses,
        variant_responses,
        variant_text
    )
    
    result = {
        "test_messages": test_messages,
        "original_responses": original_responses,
        "variant_responses": variant_responses,
        "variant_modification": variant_text,
        "comparison": comparison
    }
    
    logger.info("✅ Prueba de personalidad completada")
    return result


def analyze_response_differences(
    messages: List[str],
    original: List[str],
    variant: List[str],
    variant_text: str
) -> Dict:
    """Analiza las diferencias entre respuestas original y variante"""
    
    # Métricas básicas
    original_lengths = [len(r) for r in original]
    variant_lengths = [len(r) for r in variant]
    
    avg_original_length = sum(original_lengths) / len(original_lengths) if original_lengths else 0
    avg_variant_length = sum(variant_lengths) / len(variant_lengths) if variant_lengths else 0
    
    # Contar emojis
    original_emoji_count = sum(count_emojis(r) for r in original)
    variant_emoji_count = sum(count_emojis(r) for r in variant)
    
    # Análisis de tono (keywords)
    original_tone = analyze_tone(" ".join(original))
    variant_tone = analyze_tone(" ".join(variant))
    
    # Diferencia de longitud
    length_diff_percent = ((avg_variant_length - avg_original_length) / avg_original_length * 100) if avg_original_length > 0 else 0
    
    # Diferencia de emojis
    emoji_diff_percent = ((variant_emoji_count - original_emoji_count) / max(original_emoji_count, 1) * 100)
    
    # Generar observaciones
    observations = []
    
    if abs(length_diff_percent) > 20:
        direction = "más larga" if length_diff_percent > 0 else "más corta"
        observations.append(f"Variant es {abs(length_diff_percent):.1f}% {direction} que original")
    
    if abs(emoji_diff_percent) > 30:
        direction = "más emojis" if emoji_diff_percent > 0 else "menos emojis"
        observations.append(f"Variant usa {abs(emoji_diff_percent):.1f}% {direction}")
    
    if original_tone != variant_tone:
        observations.append(f"Tono cambió de '{original_tone}' a '{variant_tone}'")
    
    # Verificar si mantiene reglas de Lola
    rule_violations = check_lola_rules_violations(variant)
    if rule_violations:
        observations.extend(rule_violations)
    
    # Recomendación
    recommendation = generate_recommendation(
        length_diff_percent,
        emoji_diff_percent,
        original_tone,
        variant_tone,
        rule_violations
    )
    
    return {
        "average_length_original": round(avg_original_length, 1),
        "average_length_variant": round(avg_variant_length, 1),
        "length_difference_percent": round(length_diff_percent, 1),
        "emoji_count_original": original_emoji_count,
        "emoji_count_variant": variant_emoji_count,
        "emoji_difference_percent": round(emoji_diff_percent, 1),
        "tone_original": original_tone,
        "tone_variant": variant_tone,
        "observations": observations,
        "rule_violations": rule_violations,
        "recommendation": recommendation
    }


def count_emojis(text: str) -> int:
    """Cuenta emojis en un texto (aproximado)"""
    emoji_chars = ["😊", "🫣", "🙈", "😂", "😅", "🫤", "💸", "💰", "❤️", "🔥", "✨"]
    return sum(text.count(emoji) for emoji in emoji_chars)


def analyze_tone(text: str) -> str:
    """Analiza el tono general del texto"""
    text_lower = text.lower()
    
    # Keywords por categoría
    vulnerable_keywords = ["uff", "apurada", "uni", "pagar", "ayudar", "mamá", "abuela", "no tengo"]
    transactional_keywords = ["precio", "pago", "transferencia", "oxxo", "cuenta", "nivel"]
    friendly_keywords = ["haha", "chance", "la neta", "ok", "qué onda"]
    protective_keywords = ["no hago", "solo digital", "no puedo", "mejor lo dejamos"]
    
    vulnerable_score = sum(1 for kw in vulnerable_keywords if kw in text_lower)
    transactional_score = sum(1 for kw in transactional_keywords if kw in text_lower)
    friendly_score = sum(1 for kw in friendly_keywords if kw in text_lower)
    protective_score = sum(1 for kw in protective_keywords if kw in text_lower)
    
    scores = {
        "vulnerable": vulnerable_score,
        "transactional": transactional_score,
        "friendly": friendly_score,
        "protective": protective_score
    }
    
    max_tone = max(scores, key=scores.get)
    
    if scores[max_tone] == 0:
        return "neutral"
    
    return max_tone


def check_lola_rules_violations(responses: List[str]) -> List[str]:
    """Verifica violaciones a las reglas de Lola"""
    violations = []
    combined_text = " ".join(responses)
    
    # Regla: Nunca usar "jaja" (solo "haha")
    if "jaja" in combined_text.lower():
        violations.append("⚠️ REGLA VIOLADA: Usa 'jaja' en vez de 'haha'")
    
    # Regla: Nunca usar "pa" o "pa'" (solo "para")
    if " pa " in combined_text.lower() or " pa'" in combined_text.lower():
        violations.append("⚠️ REGLA VIOLADA: Usa 'pa' o 'pa'' en vez de 'para' completo")
    
    # Regla: No usar signos de apertura ¿ o ¡
    if "¿" in combined_text or "¡" in combined_text:
        violations.append("⚠️ REGLA VIOLADA: Usa signos de apertura (¿ o ¡)")
    
    # Regla: Respuestas deben ser cortas (menos de 3 frases típicamente)
    long_responses = [r for r in responses if r.count(".") > 3 or len(r) > 200]
    if long_responses:
        violations.append(f"⚠️ REGLA VIOLADA: {len(long_responses)} respuestas son muy largas (>3 frases)")
    
    return violations


def generate_recommendation(
    length_diff: float,
    emoji_diff: float,
    tone_orig: str,
    tone_var: str,
    violations: List[str]
) -> str:
    """Genera recomendación basada en el análisis"""
    
    if violations:
        return "❌ NO RECOMENDADO: La variante viola reglas fundamentales de personalidad de Lola. Revisar compliance antes de usar."
    
    if abs(length_diff) < 10 and abs(emoji_diff) < 20:
        return "✅ CAMBIOS MENORES: La variante es muy similar al original. Seguro para probar en producción."
    
    if tone_orig == "vulnerable" and tone_var == "transactional":
        return "⚠️ PRECAUCIÓN: Cambio de tono vulnerable a transaccional puede reducir empatía y conversión. Probar con A/B test."
    
    if tone_orig == "transactional" and tone_var == "friendly":
        return "✅ POTENCIAL MEJORA: Cambio a tono más amigable podría aumentar engagement. Recomendado para testing."
    
    if abs(length_diff) > 30:
        return "⚠️ PRECAUCIÓN: Cambio significativo en longitud de respuestas. Verificar que mantenga eficiencia de Lola."
    
    return "ℹ️ NEUTRAL: Cambios detectados pero sin indicadores claros de mejora o deterioro. Requiere testing con usuarios reales."
