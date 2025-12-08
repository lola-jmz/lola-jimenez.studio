"""
Herramienta MCP: get_conversion_metrics
Obtiene métricas de conversión del Bot Lola por rango de fechas
"""

import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


async def get_conversion_metrics(date_range: str, db) -> Dict:
    """
    Obtiene métricas de conversión para un rango de fechas.
    
    Args:
        date_range: Rango en formato "YYYY-MM-DD:YYYY-MM-DD"
        db: Conexión a base de datos
        
    Returns:
        Dict con métricas de conversión y revenue
    """
    logger.info(f"📊 Calculando métricas de conversión para {date_range}")
    
    # Parsear fechas
    try:
        start_date_str, end_date_str = date_range.split(":")
        start_date = datetime.strptime(start_date_str.strip(), "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str.strip(), "%Y-%m-%d")
    except ValueError as e:
        return {
            "error": f"Formato de fecha inválido: {date_range}. Use 'YYYY-MM-DD:YYYY-MM-DD'",
            "example": "2025-11-01:2025-11-28"
        }
    
    # Asegurar que end_date incluya todo el día
    end_date = end_date.replace(hour=23, minute=59, second=59)
    
    # 1. Métricas generales
    general_metrics = await get_general_metrics(db, start_date, end_date)
    
    # 2. Métricas por producto
    product_metrics = await get_product_metrics(db, start_date, end_date)
    
    # 3. Tendencias temporales
    trends = await get_temporal_trends(db, start_date, end_date)
    
    # 4. Tiempo promedio a conversión
    avg_conversion_time = await get_average_conversion_time(db, start_date, end_date)
    
    result = {
        "period": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "days": (end_date - start_date).days + 1
        },
        "metrics": general_metrics,
        "by_product": product_metrics,
        "trends": trends,
        "average_time_to_conversion_hours": avg_conversion_time
    }
    
    logger.info(f"✅ Métricas calculadas: {general_metrics['total_users']} users, {general_metrics['conversion_rate']}% conversión")
    return result


async def get_general_metrics(db, start_date: datetime, end_date: datetime) -> Dict:
    """Obtiene métricas generales de conversión"""
    
    query = """
        WITH users_in_period AS (
            SELECT DISTINCT user_id
            FROM users
            WHERE created_at BETWEEN $1 AND $2
        ),
        paid_users AS (
            SELECT DISTINCT u.user_id
            FROM users u
            JOIN payments p ON u.user_id = p.user_id
            WHERE u.created_at BETWEEN $1 AND $2
              AND p.status = 'completed'
              AND p.is_validated = TRUE
        )
        SELECT 
            (SELECT COUNT(*) FROM users_in_period) as total_users,
            (SELECT COUNT(*) FROM paid_users) as paid_users,
            COALESCE(
                ROUND(
                    100.0 * (SELECT COUNT(*) FROM paid_users) / 
                    NULLIF((SELECT COUNT(*) FROM users_in_period), 0),
                    2
                ),
                0
            ) as conversion_rate
    """
    
    row = await db.fetchrow(query, start_date, end_date)
    
    # Calcular revenue total
    revenue_query = """
        SELECT COALESCE(SUM(amount), 0) as total_revenue,
               COALESCE(AVG(amount), 0) as avg_revenue
        FROM payments
        WHERE status = 'completed'
          AND is_validated = TRUE
          AND created_at BETWEEN $1 AND $2
    """
    
    revenue_row = await db.fetchrow(revenue_query, start_date, end_date)
    
    total_users = row["total_users"] or 0
    paid_users = row["paid_users"] or 0
    total_revenue = float(revenue_row["total_revenue"]) if revenue_row["total_revenue"] else 0.0
    avg_revenue = float(revenue_row["avg_revenue"]) if revenue_row["avg_revenue"] else 0.0
    
    # ARPU (Average Revenue Per User) - considerando todos los usuarios
    arpu = round(total_revenue / total_users, 2) if total_users > 0 else 0.0
    
    # ARPPU (Average Revenue Per Paying User)
    arppu = round(total_revenue / paid_users, 2) if paid_users > 0 else 0.0
    
    return {
        "total_users": total_users,
        "paid_users": paid_users,
        "conversion_rate": float(row["conversion_rate"]) if row["conversion_rate"] else 0.0,
        "total_revenue": round(total_revenue, 2),
        "average_revenue_per_user": arpu,
        "average_revenue_per_paying_user": arppu
    }


async def get_product_metrics(db, start_date: datetime, end_date: datetime) -> Dict:
    """Obtiene métricas por producto"""
    
    query = """
        SELECT 
            product_id,
            COUNT(*) as sales_count,
            SUM(amount) as total_revenue,
            AVG(amount) as avg_price
        FROM payments
        WHERE status = 'completed'
          AND is_validated = TRUE
          AND created_at BETWEEN $1 AND $2
          AND product_id IS NOT NULL
        GROUP BY product_id
        ORDER BY total_revenue DESC
    """
    
    rows = await db.fetch(query, start_date, end_date)
    
    products = {}
    for row in rows:
        products[row["product_id"]] = {
            "sales": row["sales_count"],
            "revenue": float(row["total_revenue"]),
            "average_price": round(float(row["avg_price"]), 2)
        }
    
    return products


async def get_temporal_trends(db, start_date: datetime, end_date: datetime) -> Dict:
    """Obtiene tendencias temporales (mejor día, peor día, etc.)"""
    
    # Ventas por día
    daily_query = """
        SELECT 
            DATE(created_at) as sale_date,
            COUNT(*) as sales,
            SUM(amount) as revenue
        FROM payments
        WHERE status = 'completed'
          AND is_validated = TRUE
          AND created_at BETWEEN $1 AND $2
        GROUP BY DATE(created_at)
        ORDER BY revenue DESC
    """
    
    daily_rows = await db.fetch(daily_query, start_date, end_date)
    
    best_day = None
    worst_day = None
    
    if daily_rows:
        best_day_row = daily_rows[0]
        worst_day_row = daily_rows[-1]
        
        best_day = {
            "date": best_day_row["sale_date"].strftime("%Y-%m-%d"),
            "sales": best_day_row["sales"],
            "revenue": float(best_day_row["revenue"])
        }
        
        worst_day = {
            "date": worst_day_row["sale_date"].strftime("%Y-%m-%d"),
            "sales": worst_day_row["sales"],
            "revenue": float(worst_day_row["revenue"])
        }
    
    # Hora pico
    peak_hour = await get_peak_hour(db, start_date, end_date)
    
    return {
        "best_day": best_day,
        "worst_day": worst_day,
        "peak_hour": peak_hour
    }


async def get_peak_hour(db, start_date: datetime, end_date: datetime) -> Optional[str]:
    """Obtiene la hora pico de ventas"""
    
    query = """
        SELECT 
            EXTRACT(HOUR FROM created_at) as hour,
            COUNT(*) as sales
        FROM payments
        WHERE status = 'completed'
          AND is_validated = TRUE
          AND created_at BETWEEN $1 AND $2
        GROUP BY EXTRACT(HOUR FROM created_at)
        ORDER BY sales DESC
        LIMIT 1
    """
    
    row = await db.fetchrow(query, start_date, end_date)
    
    if row and row["hour"] is not None:
        hour = int(row["hour"])
        return f"{hour:02d}:00-{(hour+1):02d}:00"
    
    return None


async def get_average_conversion_time(db, start_date: datetime, end_date: datetime) -> Optional[float]:
    """Calcula tiempo promedio desde registro hasta primera compra"""
    
    query = """
        SELECT 
            AVG(
                EXTRACT(EPOCH FROM (p.created_at - u.created_at)) / 3600
            ) as avg_hours
        FROM users u
        JOIN payments p ON u.user_id = p.user_id
        WHERE u.created_at BETWEEN $1 AND $2
          AND p.status = 'completed'
          AND p.is_validated = TRUE
          AND p.created_at = (
              SELECT MIN(p2.created_at)
              FROM payments p2
              WHERE p2.user_id = u.user_id
                AND p2.status = 'completed'
          )
    """
    
    row = await db.fetchrow(query, start_date, end_date)
    
    if row and row["avg_hours"] is not None:
        return round(float(row["avg_hours"]), 2)
    
    return None
