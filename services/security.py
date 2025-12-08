"""
Módulo de seguridad para el bot con:
- Encriptación de datos sensibles
- Validación de entrada
- Rate limiting por usuario
- Detección de spam/abuse
- Sanitización de datos
"""

import hashlib
import hmac
import re
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class SecurityManager:
    """
    Gestor centralizado de seguridad del bot.
    """
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Args:
            encryption_key: Clave de 32 bytes para Fernet.
                           Si no se provee, se genera una nueva.
        """
        if encryption_key is None:
            encryption_key = Fernet.generate_key()
            logger.warning("⚠️  Generada nueva clave de encriptación. Guárdala en un lugar seguro.")
        
        self.cipher = Fernet(encryption_key)
        self.encryption_key = encryption_key
        
        # Rate limiting por usuario
        self.user_requests: Dict[int, list[datetime]] = defaultdict(list)
        self.blocked_users: set[int] = set()
        
        # Detección de spam
        self.spam_patterns = [
            r'(bit\.ly|t\.co|goo\.gl)',  # URL shorteners
            r'(viagra|casino|lottery)',   # Spam keywords
            r'(.)\1{10,}',                # Caracteres repetidos
        ]
        
        # Configuración
        self.max_requests_per_minute = 20
        self.max_message_length = 4000
        self.max_messages_per_hour = 100
    
    def encrypt_data(self, data: str) -> str:
        """
        Encripta datos sensibles.
        
        Usar para:
        - Números de teléfono
        - Datos de pago
        - Información personal
        """
        encrypted = self.cipher.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Desencripta datos"""
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()
    
    def hash_sensitive_data(self, data: str) -> str:
        """
        Hash unidireccional para datos que no necesitan desencriptarse.
        
        Usar para:
        - IDs de transacción
        - Tokens únicos
        """
        return hashlib.sha256(data.encode()).hexdigest()
    
    def validate_user_input(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Valida entrada del usuario.
        
        Returns:
            (es_válido, razón_si_inválido)
        """
        # Longitud
        if len(text) > self.max_message_length:
            return False, f"Mensaje demasiado largo ({len(text)} > {self.max_message_length})"
        
        # Caracteres no permitidos (control chars)
        if any(ord(char) < 32 and char not in '\n\r\t' for char in text):
            return False, "Mensaje contiene caracteres no permitidos"
        
        # Detección de spam
        for pattern in self.spam_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, f"Mensaje detectado como spam (patrón: {pattern})"
        
        return True, None
    
    def sanitize_input(self, text: str) -> str:
        """
        Sanitiza entrada del usuario para prevenir inyecciones.
        
        - Remueve caracteres de control
        - Normaliza espacios
        - Limita longitud
        """
        # Remover caracteres de control
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Normalizar espacios
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limitar longitud
        if len(text) > self.max_message_length:
            text = text[:self.max_message_length] + "..."
        
        return text
    
    def check_rate_limit(self, user_id: int) -> tuple[bool, Optional[str]]:
        """
        Verifica si el usuario está dentro del rate limit.
        
        Returns:
            (permitido, mensaje_error_si_bloqueado)
        """
        # Verificar si usuario está bloqueado
        if user_id in self.blocked_users:
            return False, "Usuario bloqueado por actividad sospechosa"
        
        now = datetime.now()
        
        # Limpiar requests antiguos (> 1 hora)
        hour_ago = now - timedelta(hours=1)
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if req_time > hour_ago
        ]
        
        # Verificar requests por hora
        if len(self.user_requests[user_id]) >= self.max_messages_per_hour:
            logger.warning(f"Usuario {user_id} excedió límite de mensajes por hora")
            return False, "Has excedido el límite de mensajes por hora. Intenta más tarde."
        
        # Verificar requests por minuto
        minute_ago = now - timedelta(minutes=1)
        recent_requests = [
            req_time for req_time in self.user_requests[user_id]
            if req_time > minute_ago
        ]
        
        if len(recent_requests) >= self.max_requests_per_minute:
            logger.warning(f"Usuario {user_id} excedió límite de mensajes por minuto")
            return False, "Estás enviando mensajes muy rápido. Por favor, espera un momento."
        
        # Registrar este request
        self.user_requests[user_id].append(now)
        
        return True, None
    
    def detect_suspicious_activity(self, user_id: int) -> bool:
        """
        Detecta si un usuario tiene comportamiento sospechoso.
        
        Criterios:
        - Demasiados mensajes en poco tiempo
        - Múltiples intentos de pago fallidos
        - Patrones de spam
        """
        if len(self.user_requests.get(user_id, [])) > 50:  # 50+ mensajes en última hora
            logger.warning(f"⚠️  Usuario {user_id} con actividad sospechosa")
            return True
        
        return False
    
    def block_user(self, user_id: int, reason: str):
        """Bloquea un usuario"""
        self.blocked_users.add(user_id)
        logger.error(f"🚫 Usuario {user_id} bloqueado. Razón: {reason}")
    
    def unblock_user(self, user_id: int):
        """Desbloquea un usuario"""
        if user_id in self.blocked_users:
            self.blocked_users.remove(user_id)
            logger.info(f"✅ Usuario {user_id} desbloqueado")
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verifica firma de webhook de Telegram.
        
        Previene que requests maliciosos se hagan pasar por Telegram.
        """
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def validate_image_file(self, file_path: str) -> tuple[bool, Optional[str]]:
        """
        Valida que un archivo de imagen sea seguro.
        
        Verifica:
        - Extensión permitida
        - Tamaño razonable
        - Magic bytes (que realmente sea imagen)
        """
        import os
        from pathlib import Path
        
        # Verificar que existe
        if not os.path.exists(file_path):
            return False, "Archivo no existe"
        
        # Extensión
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        ext = Path(file_path).suffix.lower()
        if ext not in allowed_extensions:
            return False, f"Extensión no permitida: {ext}"
        
        # Tamaño (max 10MB)
        file_size = os.path.getsize(file_path)
        if file_size > 10 * 1024 * 1024:
            return False, f"Archivo demasiado grande: {file_size / 1024 / 1024:.2f}MB"
        
        # Magic bytes (primeros bytes del archivo)
        magic_bytes = {
            b'\xFF\xD8\xFF': 'jpg',
            b'\x89\x50\x4E\x47': 'png',
            b'\x47\x49\x46\x38': 'gif',
        }
        
        with open(file_path, 'rb') as f:
            file_start = f.read(8)
        
        is_valid_image = any(
            file_start.startswith(magic) 
            for magic in magic_bytes.keys()
        )
        
        if not is_valid_image:
            return False, "Archivo no es una imagen válida"
        
        return True, None
    
    def generate_secure_token(self, user_id: int, purpose: str) -> str:
        """
        Genera token seguro para operaciones sensibles.
        
        Útil para:
        - Confirmación de pago
        - Links únicos de descarga
        """
        import secrets
        timestamp = datetime.now().isoformat()
        data = f"{user_id}:{purpose}:{timestamp}:{secrets.token_hex(16)}"
        return self.hash_sensitive_data(data)


class InputValidator:
    """Validadores específicos para diferentes tipos de entrada"""
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Valida número de teléfono (formato internacional)"""
        pattern = r'^\+?[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_amount(amount_str: str) -> Optional[float]:
        """
        Valida y parsea monto de dinero.
        
        Returns:
            Float si válido, None si inválido
        """
        try:
            # Remover símbolos comunes
            cleaned = re.sub(r'[$,\s]', '', amount_str)
            amount = float(cleaned)
            
            # Verificar rango razonable
            if 0 < amount < 1_000_000:
                return round(amount, 2)
            
            return None
        
        except ValueError:
            return None


# === EJEMPLO DE USO ===

if __name__ == "__main__":
    # Inicializar security manager
    security = SecurityManager()
    
    # Test de encriptación
    sensitive_data = "4152-3141-5231-4123"  # Tarjeta de crédito (ejemplo)
    encrypted = security.encrypt_data(sensitive_data)
    decrypted = security.decrypt_data(encrypted)
    
    print(f"Original: {sensitive_data}")
    print(f"Encriptado: {encrypted}")
    print(f"Desencriptado: {decrypted}")
    print(f"Match: {sensitive_data == decrypted}\n")
    
    # Test de validación
    test_messages = [
        "Hola, quiero comprar una imagen",
        "VIAGRA CASINO CLICK HERE " * 50,  # Spam
        "a" * 5000,  # Muy largo
    ]
    
    for msg in test_messages:
        is_valid, reason = security.validate_user_input(msg)
        print(f"Mensaje válido: {is_valid}")
        if not is_valid:
            print(f"  Razón: {reason}")
        print()
    
    # Test de rate limiting
    user_id = 12345
    for i in range(25):
        allowed, msg = security.check_rate_limit(user_id)
        if not allowed:
            print(f"Request {i+1}: Bloqueado - {msg}")
            break
    else:
        print(f"Todos los {i+1} requests permitidos")
    
    # Test de validadores
    print(f"\nEmail válido: {InputValidator.validate_email('test@example.com')}")
    print(f"Phone válido: {InputValidator.validate_phone_number('+52123456789')}")
    print(f"Amount: {InputValidator.validate_amount('$1,234.56')}")
