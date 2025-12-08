# Validación de Comprobantes - Guía de Testing Manual

## 🚀 Inicio Rápido

### 1. Iniciar el Backend

```bash
cd /home/gusta/Projects/Negocios/Stafems/lola_bot/api
python run_fastapi_basic.py
```

El servidor debería mostrar:
```
🚀 Bot Lola - Servidor CON GEMINI AI
📍 WebSocket: ws://localhost:8000/ws/{user_id}
📍 Health:    http://localhost:8000/api/health
```

### 2. Iniciar el Frontend

```bash
cd /home/gusta/Projects/Negocios/Stafems/lola_bot/frontend
npm run dev
```

Abrir: `http://localhost:3000`

## ✅ Checklist de Verificación

### Backend - run_fastapi_basic.py

- [x] Importa `PaymentValidator`
- [x] Método `process_image_base64()` implementado
- [x] WebSocket endpoint acepta `type: "image"`
- [x] Validación de tamaño (5 MB)
- [x] Conversión Base64 → BytesIO → archivo temporal
- [x] Integración con Gemini Vision
- [x] Respuestas según personalidad de Lola
- [x] Logs detallados con emojis

### Frontend - useWebSocket.ts

- [x] Método `sendImage(file: File)` implementado
- [x] Validación de tamaño (5 MB)
- [x] Conversión a Base64
- [x] Estado `isUploading`
- [x] Envío con `type: "image"`

### Frontend - lola-jimenez-studio-landing-page.tsx

- [x] Input file oculto (`accept="image/*"`)
- [x] Botón "📎" para adjuntar
- [x] Icono spinner durante upload (`isUploading`)
- [x] Deshabilitar controles durante upload

## 🧪 Tests Manuales

### Test 1: Mensaje de Texto Normal

1. Abrir chat privado
2. Escribir "hola"
3. **Esperado:** Lola responde con su personalidad

### Test 2: Adjuntar Imagen Válida

1. Preparar imagen de comprobante de pago (< 5 MB)
2. Click en botón "📎"
3. Seleccionar imagen
4. **Esperado:**
   - Mensaje: "[Imagen enviada: comprobante de pago]"
   - Lola: "dame un sec, estoy viendo tu comprobante..."
   - Luego una de estas respuestas:
     - ✅ "perfecto. ahí quedó registrado. te mando tu contenido"
     - ⚠️ "uff no logro ver bien los datos. me mandas otra captura más clara?"
     - ❌ "mmm esa imagen no se ve bien. te sale la transferencia completa?"

### Test 3: Imagen Muy Grande (> 5 MB)

1. Intentar adjuntar imagen > 5 MB
2. **Esperado:**
   - Alert: "La imagen es muy pesada. El límite es 5 MB."

### Test 4: Archivo No-Imagen

1. Intentar adjuntar PDF o documento
2. **Esperado:**
   - Lola: "mmm esa imagen no se ve bien..."

## 🔍 Logs Esperados en Backend

Al recibir una imagen:
```
🖼️  [IMAGE] test-user: Recibida imagen (12345 caracteres)
🖼️  Procesando imagen de usuario test-user
📊 Tamaño de imagen: 123456 bytes (1.18 MB)
✅ Imagen válida - Formato: JPEG, Tamaño: (1080, 1920)
💾 Imagen guardada temporalmente en: /tmp/tmpXXXXXX.jpg
🔍 Iniciando validación con Gemini Vision...
📋 Resultado de validación: {'is_valid': True, 'confidence': 0.85, ...}
✓ Válido: True | Confianza: 0.85 | Fraude: []
✅ COMPROBANTE VÁLIDO - Monto: 200.0
🗑️  Archivo temporal eliminado: /tmp/tmpXXXXXX.jpg
📤 Lola → test-user: perfecto. ahí quedó registrado...
```

## 🐛 Troubleshooting

### Error: "GEMINI_API_KEY no encontrado"
```bash
cd /home/gusta/Projects/Negocios/Stafems/lola_bot
cat .env | grep GEMINI_API_KEY
```

### Error: "ModuleNotFoundError: No module named 'PIL'"
```bash
source venv/bin/activate
pip install Pillow
```

### Error: WebSocket desconecta inmediatamente
- Verificar que el servidor está corriendo
- Verificar puerto 8000 no esté ocupado
- Revisar logs del servidor

### Frontend no conecta
- Verificar `ws://localhost:8000` en consola del navegador
- Verificar CORS configurado correctamente

## 📊 Estadísticas Esperadas

Tras procesar 5 imágenes:
```python
from services.payment_validator import payment_validator
stats = payment_validator.get_stats()
print(stats)
# {
#   'total_validations': 5,
#   'valid_count': 3,
#   'invalid_count': 2,
#   'error_count': 0,
#   'valid_rate': 0.6,
#   ...
# }
```

## 🎯 Criterios de Éxito

- [ ] Backend recibe y procesa imágenes sin errores
- [ ] Validación con Gemini Vision funciona correctamente
- [ ] Respuestas de Lola son coherentes con su personalidad
- [ ] UI muestra loading state durante procesamiento
- [ ] Límite de 5 MB se valida correctamente
- [ ] Logs son claros y útiles para debugging
