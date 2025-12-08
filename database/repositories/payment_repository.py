"""
payment_repository.py

Repositorio para operaciones de pagos en PostgreSQL.
Maneja consultas relacionadas con comprobantes de pago y hashes.
"""

import logging
from typing import Optional, Dict, Any
import asyncpg

logger = logging.getLogger(__name__)


class PaymentRepository:
    """
    Repositorio para gestionar pagos en la base de datos.
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Args:
            db_pool: Pool de conexiones asyncpg
        """
        self.pool = db_pool
        logger.info("✅ PaymentRepository inicializado")

    async def find_payment_by_hash(self, image_hash: str) -> Optional[str]:
        """
        Busca si un hash de imagen ya existe en pagos previos.
        
        Args:
            image_hash: Hash MD5 de la imagen de comprobante
            
        Returns:
            Hash existente o None si no se encontró
        """
        query = """
            SELECT payment_image_hash 
            FROM payments 
            WHERE payment_image_hash = $1 
            LIMIT 1
        """
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval(query, image_hash)
                
            if result:
                logger.info(f"🔍 Hash duplicado encontrado: {image_hash[:8]}...")
                return result
            else:
                logger.debug(f"✅ Hash único (no duplicado): {image_hash[:8]}...")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error buscando hash en BD: {e}")
            # En caso de error, no bloquear el flujo
            return None

    async def save_payment_hash(
        self,
        user_id: int,
        image_hash: str,
        payment_data: Dict[str, Any]
    ) -> bool:
        """
        Guarda el hash de un comprobante de pago en la BD.
        
        Args:
            user_id: ID del usuario
            image_hash: Hash de la imagen
            payment_data: Datos extraídos del comprobante
            
        Returns:
            True si se guardó exitosamente
        """
        query = """
            UPDATE payments 
            SET payment_image_hash = $1
            WHERE user_id = $2
            AND payment_status = 'pending'
            ORDER BY created_at DESC
            LIMIT 1
        """
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(query, image_hash, user_id)
                
            logger.info(f"💾 Hash guardado para user_id {user_id}: {image_hash[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando hash: {e}")
            return False
