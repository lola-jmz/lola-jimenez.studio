"""
payment_validator_local.py - Validador Híbrido (Local + Gemini)
Estrategia:
1. OCR local primero (gratis, ejecuta en CPU)
2. Gemini solo si confianza < 60%
3. Reduce costos ~90%
"""

import re
import logging
import easyocr
import asyncio
from typing import Optional, Dict, Tuple, Any
from .payment_validator import PaymentValidator  # Importamos el validador original para fallback

logger = logging.getLogger(__name__)

class EasyOCRPaymentValidator:
    """
    Validador de comprobantes usando EasyOCR.
    100% local, sin dependencias externas.
    Ejecuta en CPU por defecto para compatibilidad con Railway Free Tier.
    """
    
    BANKS = {
        'BBVA': ['bbva', 'bancomer'],
        'Banamex': ['banamex', 'citibanamex'],
        'Santander': ['santander'],
        'Banorte': ['banorte'],
        'HSBC': ['hsbc'],
        'OXXO': ['oxxo'],
        'Nu': ['nu', 'nubank'],
        'SPEI': ['spei'],
        'Transferencia': ['transferencia', 'enviado'],
    }
    
    def __init__(self, gpu: bool = False):
        logger.info(f"🔄 Inicializando EasyOCR (GPU: {gpu})... esto puede tardar unos segundos.")
        self.reader = easyocr.Reader(['es', 'en'], gpu=gpu)
        logger.info(f"✅ EasyOCR inicializado correctamente.")
    
    def extract_text(self, image_path: str) -> Tuple[str, float]:
        """Extrae texto de imagen"""
        try:
            results = self.reader.readtext(image_path)
            
            if not results:
                return "", 0.0
            
            texts = []
            confidences = []
            
            for (bbox, text, conf) in results:
                texts.append(text)
                confidences.append(conf)
            
            full_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return full_text, avg_confidence
        except Exception as e:
            logger.error(f"❌ Error en EasyOCR extract_text: {e}")
            return "", 0.0
    
    def extract_amount(self, text: str) -> Optional[float]:
        """Extrae monto del texto"""
        # Patrones para encontrar dinero: $100.00, 100.00 MXN, etc.
        patterns = [
            r'\$\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*(?:MXN|pesos|mn)',
            r'MONTO[:\s]*\$?([\d,]+\.?\d*)',
            r'TOTAL[:\s]*\$?([\d,]+\.?\d*)',
            r'IMPORTE[:\s]*\$?([\d,]+\.?\d*)',
            r'CANTIDAD[:\s]*\$?([\d,]+\.?\d*)',
            r'TRANSF[:\s]*\$?([\d,]+\.?\d*)',
        ]
        
        candidates = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                try:
                    # Limpiar comas y convertir a float
                    clean_val = m.replace(',', '').strip()
                    # Evitar puntos al final si existen por error de OCR
                    if clean_val.endswith('.'):
                        clean_val = clean_val[:-1]
                    
                    val = float(clean_val)
                    # Filtro básico: montos creíbles para este contexto (ej. > 10 y < 50000)
                    if 10 <= val <= 50000:
                        candidates.append(val)
                except:
                    continue
        
        # Devolver el monto máximo encontrado (usualmente es el total)
        # Ojo: A veces el saldo disponible aparece y es mayor. 
        # Pero por ahora max() es una heurística decente para comprobantes simples.
        return max(candidates) if candidates else None
    
    def extract_clabe(self, text: str) -> Optional[str]:
        """Extrae CLABE (18 dígitos)"""
        clean_text = text.replace(" ", "").replace("-", "")
        match = re.search(r'(\d{18})', clean_text)
        return match.group(1) if match else None
    
    def extract_bank(self, text: str) -> Optional[str]:
        """Identifica el banco"""
        text_lower = text.lower()
        for bank, patterns in self.BANKS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return bank
        return None
    
    def validate(
        self,
        image_path: str,
        expected_amount: Optional[float] = None,
        tolerance: float = 5.0
    ) -> Dict:
        """Valida comprobante de pago de forma síncrona (CPU blocking)"""
        try:
            text, confidence = self.extract_text(image_path)
            
            # 1. Validación de legibilidad mínima
            if len(text) < 10:
                return {
                    "is_valid": False,
                    "confidence": 0.0,
                    "reason": "No se detectó suficiente texto",
                    "extracted_data": {},
                    "needs_gemini_fallback": True
                }
            
            amount = self.extract_amount(text)
            clabe = self.extract_clabe(text)
            bank = self.extract_bank(text)
            
            # Heurística: Si detectamos monto Y (banco O keywords de pago), es probable comprobante
            is_receipt = (amount is not None) and (bank is not None or "exitos" in text.lower() or "realiz" in text.lower())
            
            if not is_receipt:
                return {
                    "is_valid": False,
                    "confidence": confidence,
                    "reason": "No parece un comprobante válido (falta monto o banco)",
                    "extracted_data": {"text_snippet": text[:50]},
                    "needs_gemini_fallback": confidence < 0.7  # Si el OCR está seguro que no es, no gastemos Gemini
                }
            
            # Validación de monto si se provee
            if expected_amount and amount:
                # Permitir pagos mayores al esperado (tips/propinas o compras múltiples)
                if amount < (expected_amount - tolerance):
                    return {
                        "is_valid": False,
                        "confidence": confidence,
                        "reason": f"Monto insuficiente: ${amount} (Esperaba mínimo ${expected_amount})",
                        "extracted_data": {"amount": amount, "bank": bank, "clabe": clabe},
                        "needs_gemini_fallback": False # OCR leyó bien que el monto NO alcanza, no hace falta Gemini
                    }
            
            return {
                "is_valid": True,
                "confidence": confidence,
                "reason": "Comprobante válido (Local OCR)",
                "extracted_data": {"amount": amount, "bank": bank, "clabe": clabe},
                "needs_gemini_fallback": False
            }
            
        except Exception as e:
            logger.error(f"Error en validate local: {e}")
            return {
                "is_valid": False,
                "confidence": 0.0,
                "reason": f"Error interno OCR: {str(e)}",
                "extracted_data": {},
                "needs_gemini_fallback": True
            }


class HybridPaymentValidator:
    """
    Combina OCR local (EasyOCR) con Gemini como fallback.
    Incluye protección contra duplicados (P-Hash) y manejo de DB.
    """
    
    def __init__(
        self,
        gemini_api_key: str,
        confidence_threshold: float = 0.6,
        use_gpu: bool = False,
        db_pool = None
    ):
        self.local_validator = EasyOCRPaymentValidator(gpu=use_gpu)
        self.db_pool = db_pool
        # Mantenemos el validador original para cuando necesitemos la "artillería pesada"
        self.gemini_validator = PaymentValidator(
            gemini_api_key=gemini_api_key, 
            db_pool=db_pool
        )
        self.confidence_threshold = confidence_threshold
        
        self.stats = {
            "total": 0,
            "local_success": 0,
            "gemini_fallback": 0,
            "duplicates_prevented": 0
        }
    
    async def validate_payment_proof(
        self,
        image_path: str,
        expected_amount: Optional[float] = None,
        expected_currency: str = "MXN"
    ) -> Dict:
        """Valida con estrategia híbrida + detección de duplicados"""
        self.stats["total"] += 1
        logger.info(f"🕵️Iniciando validación híbrida para: {image_path}")
        
        # 0. VERIFICACIÓN DE DUPLICADOS (P-Hash)
        # Usamos la lógica del validador original (método privado accesado directamente o reimplementado)
        # Por simplicidad y seguridad, delegamos el cálculo del hash a una función helper aquí o copiamos la lógica.
        # Dado que PaymentValidator tiene la lógica, podemos intentar usarla si es estática, pero es de instancia.
        # Copiaremos la lógica brevemente para evitar dependencias circulares raras o uso de métodos privados.
        try:
            image_hash = self._calculate_image_hash(image_path)
            if image_hash and self.db_pool:
                logger.info(f"🔑 Hash calculado: {image_hash[:8]}...")
                from database.repositories.payment_repository import PaymentRepository
                payment_repo = PaymentRepository(db_pool=self.db_pool)
                
                existing_hash = await payment_repo.find_payment_by_hash(image_hash)
                
                if existing_hash and existing_hash == image_hash:
                    logger.warning(f"⚠️ FRAUDE DETECTADO: Hash duplicado {image_hash[:8]}")
                    self.stats["duplicates_prevented"] += 1
                    return {
                        "is_valid": False,
                        "confidence": 0.0,
                        "reason": "Este comprobante ya fue utilizado anteriormente",
                        "extracted_data": {},
                        "fraud_indicators": ["duplicate_payment_hash"],
                        "needs_gemini_fallback": False
                    }
        except Exception as e:
            logger.warning(f"⚠️ Error verificando hash duplicado: {e}")

        # 1. Intentar OCR local primero
        try:
            loop = asyncio.get_running_loop()
            local_result = await loop.run_in_executor(
                None, 
                lambda: self.local_validator.validate(image_path, expected_amount)
            )
            
            should_use_local = False
            
            if local_result["confidence"] >= self.confidence_threshold:
                if local_result["is_valid"]:
                    should_use_local = True
                elif not local_result.get("needs_gemini_fallback"):
                    should_use_local = True
            
            if should_use_local:
                self.stats["local_success"] += 1
                logger.info(f"✅ Validación LOCAL exitosa (Confianza: {local_result['confidence']:.2f})")
                return local_result
            
            logger.info(f"⚠️ OCR Local insuficiente (Confianza: {local_result['confidence']:.2f}). Cambiando a Gemini...")
            
        except Exception as e:
            logger.error(f"Error crítico en OCR Local: {e}. Pasando a Gemini.")
        
        # 3. Fallback a Gemini
        self.stats["gemini_fallback"] += 1
        return await self.gemini_validator.validate_payment_proof(
            image_path,
            expected_amount=expected_amount,
            expected_currency=expected_currency
        )

    def _calculate_image_hash(self, image_path: str) -> str:
        """Calcula hash perceptual (copiado de PaymentValidator para independencia)"""
        try:
            from PIL import Image
            import hashlib
            with Image.open(image_path) as img:
                img = img.convert('L').resize((8, 8), Image.LANCZOS)
                pixels = list(img.getdata())
                avg = sum(pixels) / len(pixels)
                bits = ''.join('1' if pixel > avg else '0' for pixel in pixels)
                return hashlib.md5(bits.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error calculando hash: {e}")
            return ""
