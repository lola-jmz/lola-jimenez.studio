"""
Sistema de manejo de errores con retry, circuit breaker y fallbacks
"""
import asyncio
import functools
import logging
from typing import Callable, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Estados del circuit breaker"""
    CLOSED = "closed"      # Funcionando normal
    OPEN = "open"          # Demasiados errores, bloqueado
    HALF_OPEN = "half_open"  # Probando si se recuperó


class CircuitBreaker:
    """
    Implementa patrón Circuit Breaker para prevenir cascadas de fallos.
    
    Si una función falla repetidamente, el circuit breaker "se abre" y 
    retorna errores inmediatamente sin intentar llamar la función, 
    evitando sobrecargar servicios caídos.
    """
    
    def __init__(
        self, 
        failure_threshold: int = 5,  # Errores antes de abrir
        recovery_timeout: int = 60,   # Segundos antes de probar recuperación
        success_threshold: int = 2    # Éxitos para cerrar de nuevo
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Ejecuta función con protección de circuit breaker"""
        
        # Si está abierto, verificar si ya pasó el timeout
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                logger.info(f"Circuit breaker: intentando recuperación para {func.__name__}")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception(f"Circuit breaker abierto para {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Registra éxito"""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info("Circuit breaker: CERRADO después de recuperación exitosa")
                self.state = CircuitState.CLOSED
                self.success_count = 0
    
    def _on_failure(self):
        """Registra fallo"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker: ABIERTO nuevamente tras fallo en recuperación")
            self.state = CircuitState.OPEN
            self.success_count = 0
        
        elif self.failure_count >= self.failure_threshold:
            logger.error(f"Circuit breaker: ABIERTO tras {self.failure_count} fallos")
            self.state = CircuitState.OPEN


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorador para reintentar funciones asíncronas con backoff exponencial.
    
    Args:
        max_attempts: Número máximo de intentos
        delay: Delay inicial en segundos
        backoff: Factor multiplicador del delay (exponencial)
        exceptions: Tupla de excepciones a capturar
    
    Ejemplo:
        @async_retry(max_attempts=3, delay=1, backoff=2)
        async def call_gemini_api(prompt):
            return await gemini.generate(prompt)
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"❌ {func.__name__} falló después de {max_attempts} intentos: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"⚠️  {func.__name__} intento {attempt}/{max_attempts} falló: {e}. "
                        f"Reintentando en {current_delay}s..."
                    )
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff  # Backoff exponencial
            
            # Esto no debería alcanzarse, pero por seguridad
            raise last_exception
        
        return wrapper
    return decorator


def with_fallback(fallback_value: Any = None, log_error: bool = True):
    """
    Decorador para proporcionar valor de fallback si una función falla.
    
    Útil para funciones no críticas donde prefieres un valor por defecto
    en lugar de propagar el error.
    
    Ejemplo:
        @with_fallback(fallback_value="[Audio no disponible]")
        async def transcribe_audio(audio_path):
            return await whisper.transcribe(audio_path)
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(f"Error en {func.__name__}: {e}. Usando fallback: {fallback_value}")
                return fallback_value
        
        return wrapper
    return decorator


class RateLimiter:
    """
    Rate limiter para prevenir sobrecarga de APIs externas.
    
    Limita el número de llamadas por ventana de tiempo.
    """
    
    def __init__(self, max_calls: int, time_window: int):
        """
        Args:
            max_calls: Número máximo de llamadas
            time_window: Ventana de tiempo en segundos
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def acquire(self):
        """Espera si es necesario antes de permitir una llamada"""
        now = datetime.now()
        
        # Limpiar llamadas antiguas
        self.calls = [
            call_time for call_time in self.calls 
            if now - call_time < timedelta(seconds=self.time_window)
        ]
        
        # Si alcanzamos el límite, esperar
        if len(self.calls) >= self.max_calls:
            oldest_call = min(self.calls)
            wait_time = (oldest_call + timedelta(seconds=self.time_window) - now).total_seconds()
            
            if wait_time > 0:
                logger.info(f"Rate limit alcanzado. Esperando {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                # Recursión para limpiar y verificar de nuevo
                return await self.acquire()
        
        # Registrar esta llamada
        self.calls.append(now)


# Instancias globales para reusar
gemini_rate_limiter = RateLimiter(max_calls=60, time_window=60)  # 60 llamadas/minuto
gemini_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)


# === EJEMPLOS DE USO ===

@async_retry(max_attempts=3, delay=1, backoff=2, exceptions=(Exception,))
async def call_gemini_with_retry(prompt: str) -> str:
    """
    Llama a Gemini API con reintentos automáticos.
    Si falla 3 veces, propaga el error.
    """
    # Aplicar rate limiting
    await gemini_rate_limiter.acquire()
    
    # Aplicar circuit breaker
    def _call():
        import google.generativeai as genai
        model = genai.GenerativeModel('gemini-2.5-flash-exp')
        response = model.generate_content(prompt)
        return response.text
    
    return gemini_circuit_breaker.call(_call)


@with_fallback(fallback_value="[Transcripción no disponible]")
@async_retry(max_attempts=2, delay=0.5)
async def transcribe_audio_safe(audio_path: str) -> str:
    """
    Transcribe audio con fallback.
    Si falla después de 2 intentos, retorna mensaje por defecto.
    """
    from faster_whisper import WhisperModel
    model = WhisperModel("small", device="cpu", compute_type="int8")
    
    segments, _ = model.transcribe(audio_path, language="es")
    transcription = " ".join([seg.text for seg in segments])
    
    return transcription.strip()


if __name__ == "__main__":
    # Tests básicos
    async def test_retry():
        attempt = 0
        
        @async_retry(max_attempts=3, delay=0.5)
        async def flaky_function():
            nonlocal attempt
            attempt += 1
            if attempt < 3:
                raise Exception(f"Fallo intento {attempt}")
            return "¡Éxito!"
        
        result = await flaky_function()
        print(f"Resultado: {result}")
        print(f"Intentos necesarios: {attempt}")
    
    asyncio.run(test_retry())
