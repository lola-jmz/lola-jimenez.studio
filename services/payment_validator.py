"""
Validador de comprobantes de pago usando Gemini Vision.

Analiza imágenes de comprobantes de pago para extraer y validar:
- Monto del pago
- Fecha/hora de transacción
- Método de pago
- Número de referencia
- Legitimidad del comprobante

Usa Gemini Vision API para análisis multimodal.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

try:
    import google.generativeai as genai
    from PIL import Image
except ImportError:
    raise ImportError(
        "Dependencias faltantes. Instala con: "
        "pip install google-generativeai Pillow"
    )

logger = logging.getLogger(__name__)


class PaymentValidator:
    """
    Validador de comprobantes de pago usando Gemini Vision.

    Funcionalidades:
    - Análisis de imágenes de comprobantes
    - Extracción de datos (monto, fecha, referencia)
    - Detección de fraude básica
    - Scoring de confianza
    """

    def __init__(
        self,
        gemini_api_key: str,
        model_name: str = "gemini-2.5-flash",
        expected_amount: Optional[float] = None,
        db_pool = None  # NUEVO: Pool de conexiones PostgreSQL para anti-fraude
    ):
        """
        Args:
            gemini_api_key: API key de Google Gemini
            model_name: Modelo a usar (gemini-1.5-flash optimizado para Vision/OCR)
            expected_amount: Monto esperado del pago (opcional)
            db_pool: Pool de conexiones asyncpg para verificación de hashes
        """
        self.gemini_api_key = gemini_api_key
        self.model_name = model_name
        self.expected_amount = expected_amount
        self.db_pool = db_pool  # NUEVO: Guardar pool para anti-fraude

        # Configurar Gemini
        try:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel(model_name)
            logger.info(f"✅ PaymentValidator inicializado con modelo {model_name}")
        except Exception as e:
            logger.error(f"❌ Error configurando Gemini: {e}")
            raise

        # Estadísticas
        self.stats = {
            "total_validations": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "error_count": 0
        }

    async def validate_payment_proof(  # Ahora async para verificación de hash
        self,
        image_path: str,
        expected_amount: Optional[float] = None,
        expected_currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        Valida un comprobante de pago.

        Args:
            image_path: Path a la imagen del comprobante
            expected_amount: Monto esperado (override del default)
            expected_currency: Moneda esperada

        Returns:
            Dict con:
                - is_valid: bool (True si el comprobante es válido)
                - confidence: float (0-1, confianza de la validación)
                - extracted_data: Dict con datos extraídos
                - reason: str (razón si es inválido)
                - fraud_indicators: list de señales de fraude
        """
        start_time = datetime.now()
        self.stats["total_validations"] += 1
        
        # Logging inicial
        expected = expected_amount or self.expected_amount
        logger.info(f"🔍 Validando comprobante: expected_amount=${expected}, expected_currency={expected_currency}")

        # Validar que el archivo existe
        if not os.path.exists(image_path):
            logger.error(f"Archivo no encontrado: {image_path}")
            self.stats["error_count"] += 1
            return {
                "is_valid": False,
                "confidence": 0.0,
                "reason": "Archivo de imagen no encontrado",
                "extracted_data": {},
                "fraud_indicators": []
            }

        try:
            # Cargar imagen
            image = Image.open(image_path)

            # Detectar duplicados usando P-Hash
            image_hash = self._calculate_image_hash(image_path)
            if image_hash:
                logger.info(f"🔑 Hash calculado: {image_hash[:8]}...")
                
                # ACTIVADO: Verificar hash duplicado en base de datos
                if self.db_pool:
                    try:
                        from database.repositories.payment_repository import PaymentRepository
                        payment_repo = PaymentRepository(db_pool=self.db_pool)
                        
                        existing_hash = await payment_repo.find_payment_by_hash(image_hash)
                        
                        if existing_hash and existing_hash == image_hash:
                            logger.warning(f"⚠️ FRAUDE DETECTADO: Hash duplicado {image_hash[:8]}")
                            self.stats["error_count"] += 1
                            return {
                                "is_valid": False,
                                "confidence": 0.0,
                                "reason": "Este comprobante ya fue utilizado anteriormente",
                                "extracted_data": {},
                                "fraud_indicators": ["duplicate_payment_hash"]
                            }
                        else:
                            logger.info(f"✅ Hash único verificado: {image_hash[:8]}")
                            
                    except Exception as e:
                        logger.warning(f"⚠️ Error verificando hash duplicado: {e}")
                        # Continuar con validación Gemini si falla la verificación
                else:
                    logger.warning("⚠️ db_pool no disponible, omitiendo verificación de hash")
            
            # Construir prompt de análisis
            expected = expected_amount or self.expected_amount
            prompt = self._build_validation_prompt(expected, expected_currency)

            # Analizar con Gemini Vision
            logger.info(f"Analizando comprobante: {image_path}")
            response = self.model.generate_content([prompt, image])

            # Parsear respuesta
            result = self._parse_validation_response(response.text)
            
            # Logging de resultado
            logger.info(f"📊 Resultado Gemini Vision: confidence={result['confidence']:.2f}, is_valid={result['is_valid']}")
            if not result['is_valid']:
                logger.warning(f"⚠️ Comprobante rechazado: {result.get('reason', 'Sin razón específica')}")
            
            # Validar que el monto coincide con niveles de contenido
            VALID_AMOUNTS = [200, 500, 750, 350, 600]  # Niveles sin cara + premium con cara
            extracted_data = result.get("extracted_data", {})
            extracted_amount = extracted_data.get("amount", 0)
            
            if extracted_amount and extracted_amount not in VALID_AMOUNTS:
                logger.warning(f"Monto no válido detectado: ${extracted_amount}. Montos válidos: {VALID_AMOUNTS}")
                return {
                    "is_valid": False,
                    "confidence": 0.0,
                    "reason": f"El monto ${extracted_amount} no corresponde a ningún nivel de contenido válido",
                    "extracted_data": extracted_data,
                    "fraud_indicators": result.get("fraud_indicators", [])
                }

            # Calcular tiempo
            elapsed = (datetime.now() - start_time).total_seconds()

            # Actualizar estadísticas
            if result["is_valid"]:
                self.stats["valid_count"] += 1
            else:
                self.stats["invalid_count"] += 1

            logger.info(
                f"✅ Validación completada en {elapsed:.2f}s | "
                f"Válido: {result['is_valid']} | "
                f"Confianza: {result['confidence']:.2f}"
            )

            return result

        except Exception as e:
            self.stats["error_count"] += 1
            logger.error(f"❌ Error validando comprobante: {e}")

            return {
                "is_valid": False,
                "confidence": 0.0,
                "reason": f"Error en el análisis: {str(e)}",
                "extracted_data": {},
                "fraud_indicators": []
            }

    def _build_validation_prompt(
        self,
        expected_amount: Optional[float],
        expected_currency: str
    ) -> str:
        """
        Construye el prompt para Gemini Vision.

        El prompt está diseñado para extraer datos estructurados.
        """
        prompt = f"""
Analiza esta imagen de comprobante de pago y responde en formato JSON.

TAREA:
1. Determina si es un comprobante de pago legítimo
2. Extrae todos los datos relevantes
3. Identifica señales de fraude o manipulación

FORMATO DE RESPUESTA (JSON):
{{
  "is_valid": true/false,
  "confidence": 0.0-1.0,
  "extracted_data": {{
    "amount": número,
    "currency": "XXX",
    "date": "YYYY-MM-DD",
    "time": "HH:MM:SS",
    "reference_number": "string",
    "payment_method": "string",
    "recipient": "string",
    "bank_or_platform": "string"
  }},
  "fraud_indicators": ["indicador1", "indicador2"],
  "reason": "explicación si es inválido"
}}

CRITERIOS DE VALIDACIÓN:
- ¿Es una imagen clara y legible?
- ¿Contiene información de pago (monto, fecha, referencia)?
- ¿Parece un comprobante real (no editado, no screenshot de baja calidad)?
- ¿El monto coincide con lo esperado?
{f"- Monto esperado: {expected_amount} {expected_currency}" if expected_amount else ""}

SEÑALES DE FRAUDE A DETECTAR:
- Imagen muy borrosa o pixelada
- Texto superpuesto o editado
- Inconsistencias en fuentes o colores
- Falta de logo o elementos oficiales
- Monto o fecha claramente alterados
- Screenshot de otro screenshot
- Información incompleta

IMPORTANTE: Si no puedes leer la imagen o es de mala calidad, marca como inválido.

Responde ÚNICAMENTE con el JSON, sin texto adicional.
"""
        return prompt.strip()

    def _parse_validation_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parsea la respuesta JSON de Gemini.

        Maneja errores de formato y proporciona valores por defecto.
        """
        import json
        import re

        try:
            # Extraer JSON del texto (Gemini a veces añade texto antes/después)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)

                # Validar campos requeridos
                if "is_valid" not in result:
                    result["is_valid"] = False

                if "confidence" not in result:
                    result["confidence"] = 0.5

                if "extracted_data" not in result:
                    result["extracted_data"] = {}

                if "fraud_indicators" not in result:
                    result["fraud_indicators"] = []

                if "reason" not in result:
                    result["reason"] = "No se proporcionó razón"

                return result

            else:
                # No se encontró JSON válido
                logger.warning("Respuesta de Gemini no contiene JSON válido")
                return {
                    "is_valid": False,
                    "confidence": 0.0,
                    "reason": "No se pudo analizar la respuesta del modelo",
                    "extracted_data": {},
                    "fraud_indicators": ["no_json_response"]
                }

        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON: {e}")
            return {
                "is_valid": False,
                "confidence": 0.0,
                "reason": f"Error parseando respuesta: {str(e)}",
                "extracted_data": {},
                "fraud_indicators": ["json_parse_error"]
            }

    def manual_approval_needed(self, validation_result: Dict[str, Any]) -> bool:
        """
        Determina si se necesita aprobación manual.

        Retorna True si:
        - Confianza < 0.7
        - Hay indicadores de fraude
        - Monto no coincide con lo esperado
        """
        confidence = validation_result.get("confidence", 0.0)
        fraud_indicators = validation_result.get("fraud_indicators", [])
        extracted = validation_result.get("extracted_data", {})

        # Verificar confianza
        if confidence < 0.75:  # Aumentado para mayor precisión (balance UX/seguridad)
            return True

        # Verificar indicadores de fraude
        if len(fraud_indicators) > 0:
            return True

        # Verificar monto
        if self.expected_amount is not None:
            extracted_amount = extracted.get("amount")
            if extracted_amount is None or abs(extracted_amount - self.expected_amount) > 1.0:
                return True

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de validaciones"""
        stats = self.stats.copy()

        if stats["total_validations"] > 0:
            stats["valid_rate"] = stats["valid_count"] / stats["total_validations"]
            stats["invalid_rate"] = stats["invalid_count"] / stats["total_validations"]
            stats["error_rate"] = stats["error_count"] / stats["total_validations"]

        return stats

    def reset_stats(self):
        """Reinicia estadísticas"""
        self.stats = {
            "total_validations": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "error_count": 0
        }
        logger.info("Estadísticas reiniciadas")
    
    def _calculate_image_hash(self, image_path: str) -> str:
        """
        Calcula hash de imagen para detectar duplicados.
        Usa perceptual hashing (pHash) para detectar imágenes similares.
        """
        try:
            with Image.open(image_path) as img:
                # Convertir a escala de grises y redimensionar
                img = img.convert('L').resize((8, 8), Image.LANCZOS)
                pixels = list(img.getdata())
                avg = sum(pixels) / len(pixels)
                
                # Crear hash binario
                bits = ''.join('1' if pixel > avg else '0' for pixel in pixels)
                
                import hashlib
                return hashlib.md5(bits.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error calculando hash de imagen: {e}")
            return ""


# === FUNCIONES DE UTILIDAD ===

def validate_image_file(image_path: str) -> tuple[bool, Optional[str]]:
    """
    Valida que un archivo de imagen sea válido.

    Returns:
        (is_valid, error_message)
    """
    if not os.path.exists(image_path):
        return False, "Archivo no encontrado"

    try:
        # Intentar abrir con PIL
        with Image.open(image_path) as img:
            # Verificar formato
            if img.format not in ["JPEG", "PNG", "WEBP", "GIF"]:
                return False, f"Formato no soportado: {img.format}"

            # Verificar tamaño
            width, height = img.size
            if width < 100 or height < 100:
                return False, "Imagen demasiado pequeña"

            if width > 10000 or height > 10000:
                return False, "Imagen demasiado grande"

        return True, None

    except Exception as e:
        return False, f"Error abriendo imagen: {str(e)}"


# === EJEMPLO DE USO ===

async def test_validator():
    """Test del validador de comprobantes"""

    print("\n=== Test PaymentValidator ===\n")

    # Configurar (usar .env en producción)
    api_key = os.getenv("GEMINI_API_KEY", "your_api_key_here")

    if api_key == "your_api_key_here":
        print("⚠️  Configura GEMINI_API_KEY en .env para ejecutar el test")
        return

    # Inicializar validator
    validator = PaymentValidator(
        gemini_api_key=api_key,
        expected_amount=20.0
    )

    # Validar comprobante de prueba
    # image_path = "/path/to/payment_proof.jpg"
    # result = validator.validate_payment_proof(image_path)

    # print(f"\nResultado de validación:")
    # print(f"  Válido: {result['is_valid']}")
    # print(f"  Confianza: {result['confidence']:.2f}")
    # print(f"  Razón: {result.get('reason', 'N/A')}")
    # print(f"  Datos extraídos: {result['extracted_data']}")
    # print(f"  Indicadores de fraude: {result['fraud_indicators']}")

    # Estadísticas
    stats = validator.get_stats()
    print(f"\nEstadísticas:")
    print(f"  Total validaciones: {stats['total_validations']}")
    print(f"  Válidos: {stats['valid_count']}")
    print(f"  Inválidos: {stats['invalid_count']}")
    print(f"  Errores: {stats['error_count']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_validator())
