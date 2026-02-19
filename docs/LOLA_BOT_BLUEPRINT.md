# 🎯 LOLA BOT - TECHNICAL BLUEPRINT
## Documento de Transferencia de Contexto para Agentes IA

> **Propósito:** Este documento contiene TODO el contexto necesario para que un agente IA (como Antigravity) entienda el sistema completo de lola_bot sin necesidad de explorar el código.

---

## 📋 ÍNDICE RÁPIDO

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Stack Tecnológico Completo](#3-stack-tecnológico-completo)
4. [Infraestructura y Servicios](#4-infraestructura-y-servicios)
5. [Flujo de Usuario](#5-flujo-de-usuario)
6. [Estructura del Código](#6-estructura-del-código)
7. [Configuración y Variables](#7-configuración-y-variables)
8. [Documentos Clave](#8-documentos-clave)

---

## 1. RESUMEN EJECUTIVO

### ¿Qué es Lola Bot?

**Lola Bot** es un sistema de comercio conversacional impulsado por **Gemini AI** que simula una vendedora de contenido digital llamada "Lola Jiménez" (22 años, Querétaro, México). El sistema convierte leads de Tinder en clientes que pagan por contenido fotográfico exclusivo.

### Dominio de Producción
```
🌐 https://lola-jimenez.studio
```

### Repositorio GitHub
```
📦 Gucci-Veloz/lola-jimenez-studio (privado)
```

### Componentes Principales

| Componente | Descripción |
|------------|-------------|
| **Frontend** | Landing page + Chat UI (Next.js 16 static export) |
| **Backend** | API REST + WebSocket (FastAPI + Python 3.11) |
| **Chat AI** | Conversación con Gemini 2.5-Flash |
| **Validación Pagos** | Gemini Vision analiza comprobantes |
| **Storage** | Backblaze B2 (S3-compatible) para contenido |
| **Database** | NeonDB (PostgreSQL managed) |
| **Cache** | Redis para estados de sesión |

---

## 2. ARQUITECTURA DEL SISTEMA

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER JOURNEY                             │
└─────────────────────────────────────────────────────────────────┘

[Tinder] → [Landing Page: lola-jimenez.studio] → [Chat Privado WebSocket]
              ↓                                        ↓
        Galería de fotos                    Conversación con Lola AI
        (credibilidad)                              ↓
                                            [Envía Comprobante]
                                                    ↓
                                          [Gemini Vision valida]
                                                    ↓
                                          [URL firmada 30min]
                                                    ↓
                                          [Descarga contenido]

┌─────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA TÉCNICA                          │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐  WebSocket   ┌──────────────┐   API    ┌──────────────┐
│   Frontend   │◄────────────►│   Backend    │◄────────►│   External   │
│  (Next.js)   │              │  (FastAPI)   │          │   Services   │
└──────────────┘              └──────────────┘          └──────────────┘
                                    │
                      ┌─────────────┼─────────────┐
                      ↓             ↓             ↓
              ┌──────────┐   ┌────────┐   ┌───────────┐
              │PostgreSQL│   │ Redis  │   │Backblaze  │
              │  (Neon)  │   │(Cache) │   │ B2 (CDN)  │
              └──────────┘   └────────┘   └───────────┘
                                   ↑
                      ┌────────────┴────────────┐
                      │     Gemini AI API       │
                      │  - 2.5-flash (texto)    │
                      │  - Vision (comprobantes)│
                      └─────────────────────────┘
```

---

## 3. STACK TECNOLÓGICO COMPLETO

### 🐍 Backend (Python)

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Python | 3.11 | Runtime principal |
| FastAPI | 0.104.0+ | Framework web ASGI |
| Uvicorn | 0.24.0+ | Servidor ASGI |
| asyncpg | 0.29.0+ | PostgreSQL async driver |
| redis | 5.0.0+ | Cliente Redis |
| google-generativeai | 0.3.0+ | Gemini API SDK |
| boto3 | 1.34.0+ | S3/B2 storage client |
| Pillow | 10.0.0+ | Procesamiento de imágenes |
| websockets | 12.0+ | WebSocket support |
| httpx/aiohttp | - | HTTP async clients |
| cryptography | 41.0.0+ | Seguridad/encriptación |

### ⚛️ Frontend (Next.js)

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Next.js | 16 | Framework React |
| TypeScript | - | Tipado estático |
| Tailwind CSS | - | Estilos |
| Iconify | - | Iconos (Solar Icons) |

### 🎨 Paleta de Colores

| Color | Hex | Uso |
|-------|-----|-----|
| Primary | `#E91E63` | Fucsia - acentos principales |
| Secondary | `#9C27B0` | Violeta - gradientes |
| Accent | `#FFB6C1` | Rosa Bubblegum - detalles |

---

## 4. INFRAESTRUCTURA Y SERVICIOS

### 🚂 Railway (Hosting Principal)

```yaml
Proyecto: lola-jimenez-studio
Tipo: Dockerfile deployment
Dominio: lola-jimenez.studio
Start Command: uvicorn api.run_fastapi:app --host 0.0.0.0 --port ${PORT}
Health Check: /health
```

**Archivos de configuración:**
- `railway.json` - Configuración de build y deploy
- `railway.toml` - Configuración alternativa (mayor prioridad)
- `Dockerfile` - Multi-stage build (python-builder → production)

### 🐘 NeonDB (PostgreSQL)

```yaml
Provider: Neon (serverless PostgreSQL)
Version: 16+
Connection: Via DATABASE_URL environment variable
Pool: asyncpg con 10-50 conexiones
```

**Tablas principales:**
- `users` - Usuarios (web + legacy Telegram)
- `conversations` - Contexto de Tinder (JSONB)
- `messages` - Historial de chat
- `payments` - Registro de pagos y validaciones
- `conversation_state_backup` - Respaldo de Redis

### 📦 Backblaze B2 (Object Storage)

```yaml
Endpoint: https://s3.us-west-004.backblazeb2.com
Bucket: lola-content
Protocolo: S3-compatible (boto3)
CDN: Integrado en B2
URLs: Firmadas con expiración 30 minutos
```

### 🔴 Redis (Cache)

```yaml
Ubicación: Railway o local
Memoria: 256MB max
Policy: allkeys-lru
TTL default: 24 horas para estados
```

**Keys principales:**
- `conversation_state:{user_id}` - Estado FSM (JSON)
- `message_buffer:{user_id}` - Buffer de mensajes (List)
- `rate_limit:{user_id}:{endpoint}` - Rate limiting (String)

### 🤖 Google Gemini API

```yaml
Modelo Conversación: gemini-2.5-flash
Modelo Vision: gemini-2.5-pro (mayor precisión)
Rate Limit Free Tier: 15 RPM
Pricing: $0.075/1M input, $0.30/1M output
```

### 📱 Telegram (Notificaciones Admin)

```yaml
Propósito: Alertar a Guus (admin) sobre eventos importantes
- Pagos recibidos
- Validaciones dudosas
- Errores del sistema
```

---

## 5. FLUJO DE USUARIO

### Flujo Completo de Conversión

```
1. TINDER
   ├── Usuario chatea con "Lola" en Tinder
   ├── Lola comparte link: lola-jimenez.studio/chat/{user_id}
   └── Contexto Tinder se guarda en PostgreSQL (JSONB)

2. LANDING PAGE
   ├── Usuario visita la web
   ├── Ve galería de fotos profesionales (credibilidad)
   └── Click en "Chat Privado"

3. WEBSOCKET CONNECTION
   ├── Frontend abre: wss://lola-jimenez.studio/ws/{user_id}
   ├── Backend NO envía mensaje automático
   └── Espera que usuario escriba primero

4. CONVERSACIÓN AI
   ├── MessageBuffer agrupa mensajes (3s delay)
   ├── CoreHandler construye prompt:
   │   ├── Personalidad (LOLA_FLASH.md - 174 líneas)
   │   ├── Contexto temporal (hora Querétaro)
   │   ├── Historial Tinder (si existe)
   │   └── Historial chat privado
   ├── Gemini 2.5-Flash genera respuesta
   └── Respuesta via WebSocket al frontend

5. VALIDACIÓN DE PAGO
   ├── Usuario envía foto de comprobante
   ├── StateMachine verifica estado = ESPERANDO_PAGO
   ├── PaymentValidator:
   │   ├── Envía a Gemini Vision
   │   ├── Extrae: monto, método, referencia
   │   ├── Calcula pHash (detectar duplicados)
   │   └── Threshold: confidence >= 0.75
   └── Si válido: FSM → PAGO_APROBADO

6. ENTREGA DE CONTENIDO
   ├── ContentDeliveryService genera URL firmada
   ├── Backblaze B2 con expiración 30 min
   ├── Usuario descarga contenido
   └── TelegramNotifier alerta al admin
```

### Máquina de Estados (FSM)

```
INICIO → CONVERSANDO → ESPERANDO_PAGO → VALIDANDO_COMPROBANTE
                              ↓
                        PAGO_APROBADO → ENTREGANDO_PRODUCTO → COMPLETADO
                                                                  ↓
                                                          (permite upselling)
                                                                  ↓
                                                             CONVERSANDO

Estado terminal: BLOQUEADO (red flags, requiere intervención manual)
```

---

## 6. ESTRUCTURA DEL CÓDIGO

### Árbol de Directorios Principal

```
lola_bot/
├── api/
│   ├── run_fastapi.py          # Entry point principal (uvicorn)
│   ├── endpoints/               # Endpoints REST
│   └── websocket/               # WebSocket manager
│
├── core/
│   ├── core_handler.py          # 🧠 Cerebro del bot (589 líneas)
│   └── state_machine.py         # FSM de conversación
│
├── services/
│   ├── payment_validator.py     # Validación con Gemini Vision
│   ├── content_delivery.py      # URLs firmadas B2
│   ├── message_buffer_optimized.py  # Buffer 3s
│   ├── telegram_notifier.py     # Alertas admin
│   ├── backblaze_b2.py          # Storage client
│   ├── error_handler.py         # Retry + circuit breaker
│   └── security.py              # Encriptación, rate limiting
│
├── database/
│   └── database_pool.py         # asyncpg connection pool
│
├── storage/
│   └── redis_store.py           # Estado de sesión Redis
│
├── frontend/                    # Next.js 16 (static export)
│
├── docs/
│   └── LOLA_FLASH.md            # 🎭 Personalidad de Lola (174 líneas)
│
├── config/
│   └── database_schema.sql      # Schema PostgreSQL
│
├── railway.json                 # Config Railway (watchPatterns, deploy)
├── railway.toml                 # Config Railway alternativa
├── Dockerfile                   # Multi-stage build
├── requirements.txt             # Python dependencies
└── TECHNICAL_SYSTEM_SPECIFICATION.md  # Doc técnico completo
```

### Componentes Clave del Core

| Archivo | Propósito | Líneas |
|---------|-----------|--------|
| `core/core_handler.py` | Orquestador principal - procesa texto, audio, imágenes | ~589 |
| `core/state_machine.py` | FSM con transiciones validadas | ~12,530 bytes |
| `services/payment_validator.py` | Gemini Vision + pHash | ~16,888 bytes |
| `services/message_buffer_optimized.py` | Agrupa mensajes rápidos | ~10,532 bytes |
| `docs/LOLA_FLASH.md` | System prompt de Lola | 296 líneas |

---

## 7. CONFIGURACIÓN Y VARIABLES

### Variables de Entorno Requeridas

```bash
# === DATABASE ===
DATABASE_URL="postgresql://user:pass@host:5432/db"

# === AI SERVICE ===
GEMINI_API_KEY="tu-api-key"
GEMINI_MODEL="gemini-2.5-flash"  # ⚠️ NO usar gemini-2.5-pro para chat

# === STORAGE (Backblaze B2) ===
B2_ENDPOINT_URL="https://s3.us-west-004.backblazeb2.com"
B2_KEY_ID="xxx"
B2_APPLICATION_KEY="xxx"
B2_BUCKET_NAME="lola-content"

# === NOTIFICATIONS ===
TELEGRAM_BOT_TOKEN="xxx:yyy"
TELEGRAM_CHAT_ID="5283574209"  # ID de Guus (admin)

# === REDIS (opcional) ===
REDIS_URL="redis://localhost:6379"
```

### railway.json (Configuración Actual)

```json
{
    "build": {
        "builder": "DOCKERFILE",
        "dockerfilePath": "Dockerfile",
        "watchPatterns": [
            "**/*.py",
            "requirements.txt",
            "Dockerfile",
            "docs/LOLA_FLASH.md",
            "frontend/**/*"
        ]
    },
    "deploy": {
        "startCommand": "uvicorn api.run_fastapi:app --host 0.0.0.0 --port ${PORT}",
        "healthcheckPath": "/health",
        "healthcheckTimeout": 30
    }
}
```

### Dockerfile (Multi-Stage)

```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim AS python-builder
# ... compila wheels

# Stage 2: Production
FROM python:3.11-slim
# ... instala wheels, copia código
# CACHE_BUST para forzar rebuild
ARG CACHE_BUST=20251217_2008
CMD ["sh", "-c", "uvicorn api.run_fastapi:app --host 0.0.0.0 --port ${PORT}"]
```

---

## 8. DOCUMENTOS CLAVE

### Documentación Existente en el Repo

| Documento | Propósito | Ubicación |
|-----------|-----------|-----------|
| `TECHNICAL_SYSTEM_SPECIFICATION.md` | Especificación técnica completa (43KB) | raíz |
| `GEMINI.md` | Railway Expert System Prompt | raíz |
| `docs/LOLA_FLASH.md` | Personalidad de Lola | docs/ |
| `DEPLOY_README.md` | Guía de deployment | raíz |
| `README.md` | README del proyecto | raíz |
| `ROADMAP.md` | Roadmap del proyecto | raíz |

### Productos y Precios

| Tipo | Precio MXN | Descripción |
|------|-----------|-------------|
| Sin cara - Lencería | $200 | Nivel básico |
| Sin cara - Topless | $500 | Nivel medio |
| Sin cara - Íntimo | $750 | Nivel premium |
| Con cara - Lencería | $350 | Solo clientes recurrentes |
| Con cara - Topless | $600 | Solo clientes recurrentes |

### Métodos de Pago

```
OXXO: 4217 4701 9534 8913
CLABE: 728969000044136159
```

---

## 🔑 CONTEXTO CRÍTICO PARA AGENTES IA

### Lo que un agente DEBE saber:

1. **Modelo correcto**: Usar `gemini-2.5-flash` para chat, NO `gemini-2.5-pro` (excepto validación de pagos)

2. **Cache Railway**: Si cambios no aplican, verificar:
   - Docker layer cache
   - Nixpacks cache  
   - Railway build cache
   - Variable `CACHE_BUST` en Dockerfile

3. **Debugging Railway**: Usar `railway logs` para runtime, `railway logs --build` para build

4. **FSM es estricto**: No se puede saltar estados (ej: no entregar contenido sin validar pago)

5. **MessageBuffer 3s**: Los mensajes se agrupan antes de enviar a Gemini

6. **Frontend es static**: Next.js exporta archivos estáticos, FastAPI los sirve

7. **Admin = Guus**: Todas las notificaciones van a Telegram de Guus

---

## 📞 INFORMACIÓN DE CONTACTO

- **Proyecto**: lola_bot / lola-jimenez.studio
- **Owner**: Guus (gusta en Linux Ubuntu)
- **Empresa**: Stafems
- **Path local**: `/home/gusta/Projects/Negocios/Stafems/lola_bot`

---

*Blueprint generado: 2026-01-18*
*Versión: 1.0*
