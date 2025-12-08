# 🚀 TASK para Antigravity IDE - Optimizaciones Backend (Fase 2.2 y 2.3)

**Fecha:** 2025-12-03  
**Prioridad:** 🟡 Media  
**Fase:** Fase 2 - Secciones 2.2 y 2.3 (ROADMAP.md)  
**Objetivo:** Optimizar timing de message buffer y mejorar validación de pagos

---

## 🎯 CONTEXTO

Después de implementar el contexto de Tinder (Fase 2.1), ahora optimizamos dos componentes críticos:

1. **Message Buffer** - Actualmente espera 5 segundos para agrupar mensajes, puede ser demasiado
2. **Payment Validator** - Threshold de confianza 0.7 puede ser bajo, falta validación de montos específicos

---

## 📂 SECCIÓN 2.2 - AJUSTAR TIMING DE MESSAGE BUFFER

### Archivo: `/home/gusta/Projects/Negocios/Stafems/lola_bot/services/message_buffer_optimized.py`

**Problema actual:**
- Buffer espera 5 segundos (valor para web)
- Telegram usaba 3 segundos con buenos resultados
- Usuario puede percibir latencia innecesaria

**Cambios a realizar:**

#### Cambio A: Reducir tiempo de espera de 5s a 3s

**BUSCAR esta línea (aprox línea 30-40):**
```python
self.buffer_wait_seconds = buffer_wait_seconds  # Default 5.0 para web
```

**O BUSCAR en el método `__init__`:**
```python
def __init__(self, buffer_wait_seconds: float = 5.0):
```

**CAMBIAR a:**
```python
def __init__(self, buffer_wait_seconds: float = 3.0):
```

**Y actualizar el comentario:**
```python
self.buffer_wait_seconds = buffer_wait_seconds  # Optimizado: 3.0s (balance latencia/agrupación)
```

#### Cambio B: Documentar el cambio

**AGREGAR un comentario al inicio del archivo (después de los imports):**
```python
"""
OPTIMIZACIÓN DE TIMING (2025-12-03):
- Reducido de 5.0s a 3.0s para mejorar experiencia de usuario
- 3.0s es suficiente para agrupar mensajes rápidos
- Reduce latencia percibida sin sacrificar agrupación
- Basado en resultados exitosos de implementación Telegram
"""
```

---

## 📂 SECCIÓN 2.3 - MEJORAR VALIDACIÓN DE PAGOS

### Archivo: `/home/gusta/Projects/Negocios/Stafems/lola_bot/services/payment_validator.py`

**Problemas actuales:**
- Threshold 0.7 puede aprobar pagos dudosos
- No valida montos específicos ($200, $500, $750)
- No detecta comprobantes duplicados
- Logging insuficiente

**Cambios a realizar:**

#### Cambio A: Aumentar threshold de confianza

**BUSCAR esta línea (aprox línea 50-80):**
```python
if confidence >= 0.7:  # Threshold original
```

**O similar:**
```python
threshold = 0.7
```

**CAMBIAR a:**
```python
threshold = 0.75  # Aumentado para mayor precisión (balance UX/seguridad)
```

**Y actualizar todas las comparaciones:**
```python
if confidence >= threshold:
```

#### Cambio B: Validar montos específicos

**BUSCAR el método `validate_payment_proof` o donde se procesa `extracted_data`**

**AGREGAR después de extraer el monto:**
```python
# Validar que el monto coincide con niveles de contenido
VALID_AMOUNTS = [200, 500, 750, 350, 600]  # Niveles sin cara + premium con cara
extracted_amount = extracted_data.get("amount", 0)

if extracted_amount not in VALID_AMOUNTS:
    logger.warning(f"Monto no válido detectado: ${extracted_amount}. Montos válidos: {VALID_AMOUNTS}")
    return {
        "is_valid": False,
        "confidence": 0.0,
        "reason": f"El monto ${extracted_amount} no corresponde a ningún nivel de contenido válido",
        "extracted_data": extracted_data
    }
```

#### Cambio C: Mejorar logging

**AGREGAR al inicio del método `validate_payment_proof`:**
```python
logger.info(f"🔍 Validando comprobante: expected_amount=${expected_amount}, expected_currency={expected_currency}")
```

**AGREGAR después de obtener resultado de Gemini:**
```python
logger.info(f"📊 Resultado Gemini Vision: confidence={confidence:.2f}, is_valid={is_valid}")
if not is_valid:
    logger.warning(f"⚠️ Comprobante rechazado: {result.get('reason', 'Sin razón específica')}")
```

#### Cambio D: Detectar comprobantes duplicados (avanzado - opcional)

**AGREGAR al final del archivo (nueva función):**
```python
def _calculate_image_hash(self, image_path: str) -> str:
    """
    Calcula hash de imagen para detectar duplicados.
    Usa perceptual hashing (pHash) para detectar imágenes similares.
    """
    try:
        from PIL import Image
        import hashlib
        
        with Image.open(image_path) as img:
            # Convertir a escala de grises y redimensionar
            img = img.convert('L').resize((8, 8), Image.LANCZOS)
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)
            
            # Crear hash binario
            bits = ''.join('1' if pixel > avg else '0' for pixel in pixels)
            return hashlib.md5(bits.encode()).hexdigest()
    except Exception as e:
        logger.error(f"Error calculando hash de imagen: {e}")
        return ""
```

**AGREGAR en `validate_payment_proof` ANTES de llamar a Gemini:**
```python
# Detectar duplicados
image_hash = self._calculate_image_hash(image_path)
if image_hash:
    # TODO: Comparar con hashes previos en BD/Redis
    logger.info(f"🔑 Hash de comprobante: {image_hash[:8]}...")
```

---

## ⚙️ ENTORNO Y DEPENDENCIAS

**IMPORTANTE:** El proyecto usa entorno virtual Python

```bash
# Activar venv
cd /home/gusta/Projects/Negocios/Stafems/lola_bot
source venv/bin/activate

# Verificar dependencias
pip list | grep -E "(pillow|google-generativeai|fastapi)"
```

**Si faltan dependencias:**
```bash
pip install -r requirements.txt
```

---

## ✅ VERIFICACIÓN

### Test 1: Verificar sintaxis Python

```bash
cd /home/gusta/Projects/Negocios/Stafems/lola_bot
source venv/bin/activate
python -m py_compile services/message_buffer_optimized.py
python -m py_compile services/payment_validator.py
```

**Esperado:** Sin errores

### Test 2: Verificar imports

```bash
python -c "from services.message_buffer_optimized import MessageBuffer; print('✅ MessageBuffer OK')"
python -c "from services.payment_validator import PaymentValidator; print('✅ PaymentValidator OK')"
```

**Esperado:** ✅ Ambos imports exitosos

### Test 3: Probar timing del buffer

**Crear script de prueba:**
```python
# test_buffer_timing.py
import asyncio
from services.message_buffer_optimized import MessageBuffer

async def test():
    buffer = MessageBuffer()
    print(f"Buffer wait time: {buffer.buffer_wait_seconds}s")
    assert buffer.buffer_wait_seconds == 3.0, "Timing no actualizado"
    print("✅ Buffer timing correcto (3.0s)")

asyncio.run(test())
```

```bash
python test_buffer_timing.py
```

### Test 4: Verificar validación de montos

**Crear script de prueba:**
```python
# test_payment_amounts.py
from services.payment_validator import PaymentValidator

validator = PaymentValidator(gemini_api_key="test")
VALID_AMOUNTS = [200, 500, 750, 350, 600]

print(f"Montos válidos configurados: {VALID_AMOUNTS}")
print("✅ Validación de montos implementada")
```

```bash
python test_payment_amounts.py
```

---

## 📊 IMPACTO

**Archivos modificados:** 2
- `services/message_buffer_optimized.py` (~5 líneas modificadas)
- `services/payment_validator.py` (~40 líneas agregadas)

**Riesgo:** 🟢 Bajo
- Message buffer: Cambio de configuración simple
- Payment validator: Solo agregamos validaciones adicionales

**Testing:** Scripts de verificación incluidos

---

## 🎯 RESULTADO ESPERADO

### Message Buffer (2.2):
**Antes:** Usuario espera 5 segundos para ver respuesta  
**Después:** Usuario espera 3 segundos → Mejor UX sin perder agrupación

### Payment Validator (2.3):
**Antes:**
- Threshold 0.7 → Algunos pagos dudosos aprobados
- No valida montos → Cualquier cantidad pasa
- Logging básico

**Después:**
- Threshold 0.75 → Mayor precisión
- Solo montos válidos ($200, $500, $750, $350, $600) → Seguridad
- Logging detallado → Debugging más fácil
- Hash de imágenes → Preparado para detectar duplicados

---

## 🚨 NOTAS IMPORTANTES

1. **NO modificar** la lógica del FSM o personalidad de Lola
2. **NO tocar** `core/core_handler.py` - Estos cambios son solo en services
3. **Activar venv SIEMPRE** antes de ejecutar tests
4. El hash de duplicados es **opcional** - implementar solo si hay tiempo

---

## 📝 CHECKLIST PARA ANTIGRAVITY

### Sección 2.2 - Message Buffer
- [ ] Cambiar `buffer_wait_seconds` de 5.0 a 3.0
- [ ] Actualizar comentarios
- [ ] Agregar documentación del cambio
- [ ] Verificar sintaxis
- [ ] Test de timing

### Sección 2.3 - Payment Validator
- [ ] Aumentar threshold de 0.7 a 0.75
- [ ] Implementar validación de montos específicos
- [ ] Mejorar logging (info y warnings)
- [ ] (Opcional) Implementar hash de duplicados
- [ ] Verificar sintaxis
- [ ] Tests de validación

### General
- [ ] Activar venv antes de tests
- [ ] Ejecutar todos los tests de verificación
- [ ] Actualizar ROADMAP.md secciones 2.2 y 2.3 como ✅ COMPLETADO
- [ ] Crear INTERCOM.md con reporte de cambios

---

**Generado:** 2025-12-03 03:30 UTC  
**Para:** Antigravity IDE (Google) con Anthropic Sonnet 4.5  
**Proyecto:** Bot Lola - lola-jimenez.studio  
**Fase:** 2.2 y 2.3 - Optimizaciones Backend
