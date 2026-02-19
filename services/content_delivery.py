#!/usr/bin/env python3
"""
content_delivery.py

Servicio de entrega de contenido digital usando Backblaze B2.
Genera URLs firmadas con expiración para proteger contenido privado.
"""

import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from services.backblaze_b2 import BackblazeB2Client, get_b2_client_from_env

logger = logging.getLogger(__name__)


class ContentDeliveryService:
    """
    Gestor de entrega de contenido digital.
    Integra Backblaze B2 para URLs seguras con expiración.
    """

    def __init__(
        self,
        b2_client: Optional[BackblazeB2Client] = None,
        url_expiration_minutes: int = 30
    ):
        """
        Inicializa el servicio de entrega de contenido.
        
        Args:
            b2_client: Cliente de Backblaze B2 (si no se proporciona, se crea desde env vars)
            url_expiration_minutes: Minutos de validez de URLs firmadas (default: 30)
                                    NOTA: Reducido de 24h para prevenir piratería
        """
        if b2_client:
            self.b2_client = b2_client
        else:
            try:
                self.b2_client = get_b2_client_from_env()
            except ValueError as e:
                logger.warning(f"⚠️ No se pudo inicializar B2 client: {e}")
                self.b2_client = None
        
        self.url_expiration_minutes = url_expiration_minutes
        
        if self.b2_client:
            logger.info("✅ ContentDeliveryService inicializado con Backblaze B2")
        else:
            logger.warning("⚠️ ContentDeliveryService sin B2 - funcionalidad limitada")

    async def get_product_url(
        self,
        user_id: str,
        product_level: str
    ) -> Optional[str]:
        """
        Genera URL firmada para el contenido del usuario.
        
        Args:
            user_id: ID del usuario comprador
            product_level: Nivel de producto (ej: "lingerie", "topless", "intimate")
            
        Returns:
            URL firmada del contenido o None si falla
        """
        try:
            # Obtener path del archivo en B2
            object_key = await self.get_product_mapping(product_level)
            
            if not object_key:
                logger.error(f"❌ No existe mapeo para nivel: {product_level}")
                return None
            
            if not self.b2_client:
                logger.error("❌ B2 client no disponible")
                return None
            
            # Generar URL firmada con expiración
            expiration_seconds = self.url_expiration_minutes * 60
            signed_url = self.b2_client.get_presigned_url(
                object_key,
                expiration=expiration_seconds
            )
            
            if signed_url:
                expiration_time = datetime.now() + timedelta(minutes=self.url_expiration_minutes)
                logger.info(f"✅ URL generada para {user_id} - Nivel: {product_level}")
                logger.info(f"⏰ URL expira en {self.url_expiration_minutes} min: {expiration_time.isoformat()}")
                return signed_url
            else:
                logger.error(f"❌ No se pudo generar URL firmada para: {object_key}")
                return None
            
        except Exception as e:
            logger.error(f"❌ Error generando URL de producto: {e}")
            return None

    async def deliver_content(
        self,
        user_id: str,
        product_level: str,
        delivery_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Entrega contenido al usuario y registra la transacción.
        
        Args:
            user_id: ID del usuario
            product_level: Nivel de producto comprado
            delivery_metadata: Metadata adicional (ej: monto pagado, método)
            
        Returns:
            Dict con url, expiration y metadata
        """
        try:
            url = await self.get_product_url(user_id, product_level)
            
            if not url:
                return {
                    "success": False,
                    "error": "No se pudo generar URL de contenido"
                }
            
            expiration = datetime.now() + timedelta(minutes=self.url_expiration_minutes)
            
            return {
                "success": True,
                "url": url,
                "product_level": product_level,
                "expires_at": expiration.isoformat(),
                "expires_in_minutes": self.url_expiration_minutes,
                "metadata": delivery_metadata or {}
            }
            
        except Exception as e:
            logger.error(f"❌ Error entregando contenido a {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def upload_content(
        self,
        file_path: str,
        product_level: str,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Sube contenido al bucket de B2.
        
        Args:
            file_path: Ruta local del archivo
            product_level: Nivel de producto para determinar path en bucket
            content_type: MIME type del archivo
            
        Returns:
            URL del archivo subido o None si falla
        """
        if not self.b2_client:
            logger.error("❌ B2 client no disponible para upload")
            return None
        
        try:
            object_key = f"products/{product_level}/{os.path.basename(file_path)}"
            
            result = self.b2_client.upload_file(
                file_path,
                object_key,
                content_type=content_type
            )
            
            if result:
                logger.info(f"✅ Contenido subido: {object_key}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error subiendo contenido: {e}")
            return None

    async def get_product_mapping(self, product_level: str) -> Optional[str]:
        """
        Mapea nivel de producto a archivo en Backblaze B2.

        Convenciones de product_level:
          - "lenceria_01", "lenceria_02"          → sin cara
          - "bubis_01", "bubis_02"                → sin cara
          - "micuerpo_01", "micuerpo_02"          → sin cara
          - "intima_01", "intima_02", "intima_03" → sin cara
          - Mismos con sufijo "_cara"             → con cara

        También acepta tiers genéricos (elige variante 01 por defecto):
          - "lenceria", "bubis", "micuerpo", "intima"
          - "lenceria_cara", "bubis_cara", "micuerpo_cara", "intima_cara"
        """
        mapping: dict[str, str] = {
            # ── SIN CARA ─────────────────────────────────────────────
            "lenceria_01":   "products/sin_cara/Lenceria_01_sin_cara.webp",
            "lenceria_02":   "products/sin_cara/Lenceria_02_sin_cara.webp",
            "bubis_01":      "products/sin_cara/Bubis_01_sin_cara.webp",
            "bubis_02":      "products/sin_cara/Bubis_02_sin_cara.webp",
            "micuerpo_01":   "products/sin_cara/MiCuerpo_01_sin_cara.webp",
            "micuerpo_02":   "products/sin_cara/MiCuerpo_02_sin_cara.webp",
            "intima_01":     "products/sin_cara/Intima_01_sin_cara.webp",
            "intima_02":     "products/sin_cara/Intima_02_sin_cara.webp",
            "intima_03":     "products/sin_cara/Intima_03_sin_cara.webp",
            # ── CON CARA ─────────────────────────────────────────────
            "lenceria_01_cara":  "products/con_cara/Lenceria_01_con_cara.webp",
            "lenceria_02_cara":  "products/con_cara/Lenceria_02_con_cara.webp",
            "bubis_01_cara":     "products/con_cara/Bubis_01_con_cara.webp",
            "bubis_02_cara":     "products/con_cara/Bubis_02_con_cara.webp",
            "micuerpo_01_cara":  "products/con_cara/MiCuerpo_01_con_cara.webp",
            "micuerpo_02_cara":  "products/con_cara/MiCuerpo_02_con_cara.webp",
            "intima_01_cara":    "products/con_cara/Intima_01_con_cara.webp",
            "intima_02_cara":    "products/con_cara/Intima_02_con_cara.webp",
            "intima_03_cara":    "products/con_cara/Intima_03_con_cara.webp",
            # ── ALIASES (tier genérico → variante _01) ───────────────
            "lenceria":      "products/sin_cara/Lenceria_01_sin_cara.webp",
            "bubis":         "products/sin_cara/Bubis_01_sin_cara.webp",
            "topless":       "products/sin_cara/Bubis_01_sin_cara.webp",
            "micuerpo":      "products/sin_cara/MiCuerpo_01_sin_cara.webp",
            "intima":        "products/sin_cara/Intima_01_sin_cara.webp",
            "lenceria_cara": "products/con_cara/Lenceria_01_con_cara.webp",
            "bubis_cara":    "products/con_cara/Bubis_01_con_cara.webp",
            "topless_cara":  "products/con_cara/Bubis_01_con_cara.webp",
            "micuerpo_cara": "products/con_cara/MiCuerpo_01_con_cara.webp",
            "intima_cara":   "products/con_cara/Intima_01_con_cara.webp",
        }

        return mapping.get(product_level.lower())

    async def health_check(self) -> Dict[str, Any]:
        """Verifica conectividad con Backblaze B2"""
        if not self.b2_client:
            return {
                "backblaze_b2": False,
                "error": "B2 client no inicializado"
            }
        
        b2_health = await self.b2_client.health_check()
        
        return {
            "backblaze_b2": b2_health.get("status") == "healthy",
            "details": b2_health
        }
