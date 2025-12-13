"""
Servicio de notificaciones Telegram para alertas de pago.
Envía mensajes al Telegram de Guus cuando llegue un comprobante pendiente.
"""

import os
import logging
import httpx
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Servicio para enviar notificaciones a Telegram"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Args:
            bot_token: Token del bot de Telegram (obtener de @BotFather)
            chat_id: Chat ID de Guus (obtener enviando /start al bot)
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        logger.info(f"✅ TelegramNotifier inicializado (chat_id: {chat_id})")
    
    async def notify_payment_received(
        self,
        user_identifier: str,
        amount: float,
        image_url: Optional[str] = None,
        confidence: Optional[float] = None,
        extracted_data: Optional[dict] = None
    ) -> bool:
        """
        Notifica a Guus de un nuevo comprobante recibido.
        
        Args:
            user_identifier: ID del usuario
            amount: Monto esperado del pago
            image_url: URL de Backblaze del comprobante (opcional)
            confidence: Score de confianza de Gemini (opcional)
            extracted_data: Datos extraídos del comprobante (opcional)
        
        Returns:
            True si se envió correctamente
        """
        try:
            # Timestamp actual
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Construir mensaje
            mensaje = f"""🔔 *PAGO PENDIENTE VALIDACIÓN*

*Fecha:* {now}
*Usuario:* `{user_identifier}`
*Monto esperado:* ${amount:.2f} MXN
"""
            
            # Añadir confianza de Gemini si disponible
            if confidence is not None:
                emoji = "✅" if confidence > 0.75 else "⚠️"
                mensaje += f"{emoji} *Confianza Gemini:* {confidence:.0%}\n"
            
            # Añadir datos extraídos si disponibles
            if extracted_data:
                extracted_amount = extracted_data.get("amount")
                if extracted_amount:
                    mensaje += f"💵 *Monto detectado:* ${extracted_amount:.2f}\n"
                
                payment_method = extracted_data.get("payment_method")
                if payment_method:
                    mensaje += f"💳 *Método:* {payment_method}\n"
                
                reference = extracted_data.get("reference_number")
                if reference:
                    mensaje += f"🔑 *Referencia:* `{reference}`\n"
            
            # Añadir URL del comprobante si disponible
            if image_url:
                mensaje += f"\n📸 [Ver comprobante]({image_url})\n"
            
            mensaje += "\n⏰ *Revisar en horario disponible*"
            
            # Enviar mensaje
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": mensaje,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": False
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Notificación Telegram enviada para {user_identifier}")
                    return True
                else:
                    logger.error(f"❌ Error Telegram API: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error enviando notificación Telegram: {e}")
            return False
    
    async def notify_payment_approved(
        self,
        user_identifier: str,
        amount: float,
        product_level: str
    ) -> bool:
        """
        Notifica a Guus de un pago aprobado automáticamente.
        
        Args:
            user_identifier: ID del usuario
            amount: Monto del pago
            product_level: Nivel de producto entregado
        
        Returns:
            True si se envió correctamente
        """
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            mensaje = f"""✅ *PAGO APROBADO*

*Fecha:* {now}
*Usuario:* `{user_identifier}`
*Monto:* ${amount:.2f} MXN
*Producto:* {product_level}

💰 ¡Nueva venta procesada automáticamente!
"""
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": mensaje,
                        "parse_mode": "Markdown"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Notificación de pago aprobado enviada para {user_identifier}")
                    return True
                else:
                    logger.error(f"❌ Error en Telegram API: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error enviando notificación de pago aprobado: {e}")
            return False


# === EJEMPLO DE USO ===

async def test_notifier():
    """Test del notificador de Telegram"""
    print("\n=== Test TelegramNotifier ===\n")
    
    # Configurar (obtener de .env en producción)
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("⚠️  Configura TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en .env")
        return
    
    # Inicializar notifier
    notifier = TelegramNotifier(bot_token, chat_id)
    
    # Test 1: Notificación de pago recibido
    result1 = await notifier.notify_payment_received(
        user_identifier="test_user_123",
        amount=200.0,
        confidence=0.85,
        extracted_data={
            "amount": 200.0,
            "payment_method": "OXXO",
            "reference_number": "1234567890"
        },
        image_url="https://example.com/comprobante.jpg"
    )
    print(f"Test 1 (pago recibido): {'✅ PASS' if result1 else '❌ FAIL'}")
    
    # Test 2: Notificación de pago aprobado
    result2 = await notifier.notify_payment_approved(
        user_identifier="test_user_123",
        amount=200.0,
        product_level="feet"
    )
    print(f"Test 2 (pago aprobado): {'✅ PASS' if result2 else '❌ FAIL'}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_notifier())
