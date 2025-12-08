# High-Level Design (HLD) - Bot Lola
**Proyecto:** Sistema de Chat Web para Venta de Contenido Digital  
**Fecha:** Noviembre 2025  
**Versión:** 1.0

---

## 1. VISIÓN GENERAL

Bot Lola es un sistema de ventas conversacional basado en web que permite a usuarios interactuar con un chatbot con personalidad definida, realizar compras de contenido digital, y recibir el producto mediante un flujo automatizado.

**Objetivo Principal:** Convertir leads fríos (Tinder) en clientes pagados mediante un portafolio web atractivo + chat privado.

---

## 2. ARQUITECTURA DEL SISTEMA

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO (Navegador)                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              FRONTEND (Lovable - HTML/CSS/JS)                │
│  • Portafolio visual (galería de fotos)                     │
│  • Botón "Chat Privado"                                      │
│  • Interfaz de chat (WebSocket)                              │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTPS/WSS
                        ▼
┌─────────────────────────────────────────────────────────────┐
│           BACKEND (FastAPI + Uvicorn)                        │
│                                                               │
│  run_fastapi.py                                              │
│  ├── API REST                                                │
│  │   └── GET /api/history/{user_id}                         │
│  │   └── POST /api/payment/validate                         │
│  │                                                            │
│  ├── WebSocket                                               │
│  │   └── WS /ws/{user_id}                                   │
│  │                                                            │
│  └── CoreHandler (Cerebro)                                   │
│      ├── Lógica de conversación                             │
│      ├── Máquina de estados (FSM)                           │
│      └── Integración con Gemini AI                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ PostgreSQL  │ │    Redis    │ │  Gemini AI  │
│   (Estado   │ │  (Sesiones) │ │  (Texto +   │
│ Permanente) │ │             │ │   Visión)   │
└─────────────┘ └─────────────┘ └─────────────┘
                                        │
                                        ▼
                                ┌─────────────┐
                                │   Oracle    │
                                │   Cloud +   │
                                │ Pushr CDN   │
                                │ (Imágenes)  │
                                └─────────────┘
```

---

## 3. COMPONENTES PRINCIPALES

### 3.1 Frontend (Lovable)
**Responsabilidad:** Interfaz de usuario y experiencia visual.

**Funcionalidades:**
- Portafolio de creador (Brand-Harmony con personalidad Lola)
- Botón CTA "Chat Privado"
- Cliente WebSocket para chat en tiempo real
- Carga de historial de conversaciones

**Tecnologías:** React, TypeScript, Tailwind CSS, WebSocket API

---

### 3.2 Backend (FastAPI)
**Archivo Principal:** `run_fastapi.py`

#### 3.2.1 API REST
**Endpoints:**
- `GET /api/history/{user_id}` - Recuperar historial de conversación
- `POST /api/payment/validate` - Validar comprobante de pago

#### 3.2.2 WebSocket Server
**Endpoint:** `WS /ws/{user_id}`
- Conexión bidireccional persistente
- Envío/recepción de mensajes en tiempo real
- Gestión de múltiples conexiones concurrentes

#### 3.2.3 CoreHandler (Cerebro)
**Archivo Nuevo:** `core_handler.py`

**Responsabilidades:**
- Procesar mensajes del usuario
- Ejecutar lógica de negocio (FSM)
- Interactuar con Gemini AI
- Coordinar validación de pagos
- Entregar contenido digital

**Diseño Clave:** Desacoplado de transporte (WebSocket/HTTP)

**Parámetros de Inicialización:**
```python
CoreHandler(
    sender_callback: Callable,      # Función para enviar mensajes
    buffer_wait_seconds: float,     # 5.0 para web
    conversation_manager: ConversationManager,
    security_manager: SecurityManager,
    payment_validator: PaymentValidator
)
```

---

### 3.3 Módulos Reutilizables (Ya Existentes)

#### ✅ Sin Cambios Necesarios
- **database_pool.py** - Pool de conexiones PostgreSQL (asyncpg)
- **state_machine.py** - FSM para flujo de conversación
- **security.py** - Rate limiting, validación de inputs
- **payment_validator.py** - Integración con Gemini Vision
- **error_handler.py** - Gestión de errores
- **message_buffer_optimized.py** - Buffer de mensajes (5s para web)

#### 🔄 Requiere Adaptación
- **bot_optimized.py** - Extraer lógica de negocio → `core_handler.py`
- **audio_transcriber.py** - Decisión pendiente sobre voz en web

---

### 3.4 Base de Datos (PostgreSQL)

**DB Existente:** `maria_bot`

**Tablas Actuales:**
- `users` - Información de usuarios
- `conversations` - Sesiones de conversación
- `messages` - Historial de mensajes
- `payments` - Registro de pagos
- `audit_log` - Logs de auditoría

**Cambio Requerido:** Añadir columna `user_identifier VARCHAR(255)` para soportar usuarios web (sin afectar datos existentes de Telegram).

---

### 3.5 Redis
**Propósito:** Almacenamiento en caché de estado de sesiones.

**Uso:**
- Estado de conversación activa
- Rate limiting distribuido
- Caché de respuestas frecuentes

**Implementación:** `RedisStateStore` wrapper para `ConversationManager`

---

### 3.6 Gemini AI
**Funciones:**
1. **Generación de Respuestas:** Texto conversacional basado en personalidad Lola
2. **Visión:** Validación de comprobantes de pago (imágenes)

**Configuración:** Ya integrado en `payment_validator.py`

---

### 3.7 Oracle Cloud + Pushr CDN
**Flujo de Entrega de Contenido:**
```
Pago Validado → CoreHandler solicita contenido → 
Oracle Cloud genera URL firmada → 
Pushr CDN sirve imagen → 
Usuario recibe contenido privado
```

**Pendiente:** Implementar en Fase C

---

## 4. FLUJOS PRINCIPALES

### 4.1 Flujo de Conversación Inicial
```
1. Usuario visita lola-jimenez.studio
2. Ve portafolio (galería de fotos)
3. Hace click en "Chat Privado"
4. Frontend genera user_id único (UUID)
5. Abre WebSocket: ws://domain/ws/{user_id}
6. CoreHandler recibe conexión
7. Envía mensaje de bienvenida (personalidad Lola)
8. Usuario responde
9. CoreHandler procesa con FSM + Gemini
10. Responde según estado de conversación
```

### 4.2 Flujo de Compra y Validación
```
1. Usuario expresa interés en comprar
2. CoreHandler transiciona FSM a estado "AWAITING_PAYMENT"
3. Envía instrucciones de pago
4. Usuario envía captura de comprobante (imagen)
5. Frontend envía imagen vía WebSocket
6. CoreHandler llama a payment_validator.py
7. Gemini Vision valida comprobante
8. Si válido:
   - Actualiza tabla payments
   - Genera URL de contenido (Oracle + Pushr)
   - Envía link al usuario
9. Si inválido:
   - Solicita comprobante válido
```

### 4.3 Flujo de Recuperación de Historial
```
1. Usuario regresa a chat (URL única)
2. Frontend extrae user_id de URL
3. Llama GET /api/history/{user_id}
4. Backend consulta PostgreSQL
5. Retorna mensajes previos
6. Frontend muestra historial
7. Usuario continúa conversación
```

---

## 5. DECISIONES TÉCNICAS CLAVE

### 5.1 ¿Por qué FastAPI?
- Soporte nativo de WebSockets
- Alto rendimiento (asíncrono)
- Documentación automática (OpenAPI)
- Ecosistema Python compatible con código existente

### 5.2 ¿Por qué Redis?
- Estado compartido entre múltiples instancias de servidor
- Baja latencia para sesiones activas
- Expiración automática de datos (TTL)

### 5.3 ¿Por qué NO migrar base de datos?
- Riesgo alto de corrupción de datos
- Solución más segura: añadir columna `user_identifier` (no destructivo)
- Mantener `user_id BIGINT` para compatibilidad futura

### 5.4 ¿Por qué Pushr CDN?
- Oracle Cloud no tiene CDN incorporado
- Pushr ofrece capa de protección para contenido privado
- URLs firmadas con expiración

---

## 6. FASES DE IMPLEMENTACIÓN

### Fase A: Infraestructura (1 semana)
**Tareas:**
1. Comprar dominio lola-jimenez.studio
2. Configurar Oracle Cloud Always Free
3. Registrarse en pushr.io
4. Instalar Redis localmente

**Criterio de Éxito:** Servicios externos activos y accesibles.

---

### Fase B: Backend Core (1-2 semanas)
**Tareas:**
1. Renombrar LORE.md → LOLA.md
2. Crear `core_handler.py` (extraer lógica de bot_optimized.py)
3. Crear `run_fastapi.py` con endpoints básicos
4. Implementar WebSocket server
5. Conectar a PostgreSQL existente
6. Integrar Redis para estado

**Criterio de Éxito:** Chat funcional localmente (sin frontend).

---

### Fase C: Integración Final (1 semana)
**Tareas:**
1. Ajustar frontend Lovable para conectar a FastAPI
2. Implementar flujo de pago completo
3. Integrar Oracle + Pushr para entrega de contenido
4. Testing end-to-end
5. Deploy a producción

**Criterio de Éxito:** Sistema completo operando en lola-jimenez.studio.

---

## 7. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Corrupción de BD al modificar esquema | Media | Crítico | NO migrar tipos. Añadir columnas sin destruir datos existentes. |
| Estado de sesión no compartido | Alta | Alto | Usar Redis como backend de estado distribuido. |
| Latencia en validación de pagos | Baja | Medio | Usar Gemini AI con timeout configurado. Caché de resultados. |
| URLs de contenido expuestas | Media | Crítico | Pushr CDN con URLs firmadas y expiración. |
| Sobrecarga de WebSockets | Baja | Medio | Rate limiting en Redis. Límite de conexiones por IP. |

---

## 8. REQUISITOS DEL SISTEMA

### Producción
- **Servidor:** Linux (Ubuntu 22.04+)
- **Python:** 3.12+
- **PostgreSQL:** 16+
- **Redis:** 7+
- **RAM:** 2GB mínimo
- **CPU:** 2 cores mínimo
- **Ancho de banda:** 100 Mbps

### Desarrollo (Local)
- **SO:** Linux (actual del usuario)
- **Python:** 3.12 (instalado)
- **PostgreSQL:** 16 (instalado)
- **Redis:** Pendiente de instalación
- **Dependencias Python:** requirements.txt existente

---

## 9. PRÓXIMOS PASOS INMEDIATOS

1. **Usuario:** Comprar dominio + Oracle Cloud + Pushr
2. **Claude-Code:** Crear `core_handler.py` extrayendo lógica de `bot_optimized.py`
3. **Gemini CLI:** Generar `run_fastapi.py` con estructura básica
4. **Usuario:** Instalar Redis localmente
5. **Validación:** Probar chat básico localmente

---

## 10. ESTADO DE IMPLEMENTACIÓN

### ✅ Fase B Completada (100%)
Los siguientes componentes críticos han sido implementados y están funcionales:

1. **core/core_handler.py** - Cerebro del bot con lógica desacoplada
2. **api/run_fastapi.py** - Servidor FastAPI + WebSockets + Uvicorn
3. **api/websocket/connection_manager.py** - Gestor de conexiones WebSocket
4. **storage/redis_store.py** - Wrapper de Redis para estado distribuido
5. **services/content_delivery.py** - Integración Oracle + Pushr CDN

**Fecha de completación:** Noviembre 2025

---

## 11. CONCLUSIÓN

El sistema Bot Lola reutiliza 80% del código existente (módulos auxiliares, base de datos, lógica de negocio) y añade una capa de API web moderna con FastAPI. La arquitectura desacoplada permite evolucionar el frontend y backend independientemente, manteniendo la lógica de negocio centralizada en `CoreHandler`.

**Ventaja Clave:** Cambio de canal (Telegram → Web) sin reescribir lógica de negocio.

**Tiempo Estimado Total:** 3-4 semanas desde inicio de Fase A hasta producción.

---

**Documento generado para:** Guus (Usuario con TDAH)
**Estilo:** Conciso, visual, actionable
**Última actualización:** Noviembre 2025 - Fase B Completada ✅
