# Lola Jiménez Studio
Plataforma web conversacional diseñada para la venta de contenido digital cerrado. Integra un frontend interactivo en Next.js con un backend reactivo en FastAPI, orquestando una máquina de estados para ventas, validando comprobantes automáticamente vía Gemini Vision OCR, y habilitando una entrega segura y expirante usando Backblaze B2.

## Stack Tecnológico

| Capa | Tecnología | Versión/Detalle |
|---|---|---|
| Frontend | Next.js (React) | 16.0.3 (Static Export) con Tailwind v4 y Framer Motion |
| Backend | FastAPI (Python) | 0.104.0 (Uvicorn, WebSockets) |
| Base de Datos | PostgreSQL (Neon) | Conexión usando `asyncpg` con pooling y retry logic |
| Cache & Estado | Redis | Módulo asíncrono; Respaldo automático upsert en PostgreSQL |
| Storage | Backblaze B2 | Protocolo S3 compatible, URLs generadas firmadas con TTL temporal |
| Inteligencia Artificial | Google Gemini AI | Generación de lenguaje (gemini-2.5-flash) y OCR para comprobantes |
| Deploy | Railway | Contenedor Dockerizado unificado (Backend Sirviendo Next.js Estático) |

## Arquitectura General
El proyecto usa el patrón de "Client-Server" con un flujo de embudo interactivo mediante Socket en tiempo real:
1. **Conexión Tiempo Real**: Frontend escrito en Next.js se enlaza con el Backend manejado por un `ConnectionManager` asíncrono (WebSockets).
2. **Máquina de Estados**: Manejada usando `ConversationManager` que evalúa las intenciones y eventos (inicio, conversando, esperando pago, comprobando pago, entregando). Permite bloqueo ante actividad sospechosa (FSM).
3. **Core Lógico y Prompting**: El `LolaCoreHandler` inyecta en Gemini AI la historia reciente, contextos climáticos/de zona local y una robusta personalidad documentada (Lola), aislando el código transaccional de la Inteligencia Artificial.
4. **Validación de Pago Automatizada**: `PaymentValidator` implementa prevención de captura duplicada con pHash y evalúa la imagen del cheque con un prompt OCR con Gemini Vision (buscando método y correspondencia de montos).
5. **Entrega de Contenido**: `ContentDeliveryService` llama a B2, sube y enlaza URLS encriptadas seguras a la que se integran notificaciones de reporte local vía admin para Telegram.

## Estructura del Proyecto
```text
/home/gusta/Projects/Negocios/Stafems/lola_bot/
├── api/
│   └── run_fastapi.py            # Entry point central, levanta Uvicorn y expone REST y WebSockets
├── core/
│   ├── core_handler.py           # Administrador unificado para procesamiento natural del bot
│   └── state_machine.py          # Definición transicional de los estados conversacionales
├── database/
│   └── database_pool.py          # Wrapper transaccional asincrónico directo contra PostgreSQL
├── docs/
│   └── LOLA_FLASH.md             # Tono de la personalidad, guías operativas e integrales para Gemini
├── frontend/
│   ├── app/                      # Entry point jerárquico Next.js (layout.tsx, page.tsx)
│   ├── components/               # Elementos funcionales (ej. lola-jimenez-studio-landing-page.tsx)
│   └── package.json              # Dependencias de npm / bun / pnpm
├── services/
│   ├── content_delivery.py       # Controlador de Backblaze B2
│   ├── error_handler.py          # Circuit breakers asíncronos y backoffs exponenciales globales
│   ├── payment_validator.py      # Gestor de evaluación visual de transferencias bancarias / OXXO
│   ├── security.py               # Encriptación Fernet, Throttling (Limits) y Sanitización input strings
│   └── telegram_notifier.py      # Integración Telegram-bot para alertas al staff / vendedor real  
├── storage/
│   └── redis_store.py            # Orquestador del tracking efímero de status, montos y metadatos
├── Dockerfile                    # Multi-stage build empacando assets de front y librerias PIP
├── railway.json                  # Set de comandos automáticos a nivel orquestación Railway
└── requirements.txt              # Instalador de librerías para la base de FastAPI local (boto3, asyncpg, etc.)
```

## Variables de Entorno
`DATABASE_URL` — Connection string completo para la base de datos PostgreSQL (Neon).
`B2_ENDPOINT_URL` — Cadena principal del Endpoint tipo S3 referenciando Backblaze.
`B2_KEY_ID` — Identificador autorizado del proyecto Storage (Backblaze).
`B2_APPLICATION_KEY` — Token secreto a utilizar para emitir links en Backblaze.
`B2_BUCKET_NAME` — Identificador del cubo del cloud storage.
`GEMINI_API_KEY` — Token maestro para autorizar requests de predicción NLP y Visual via Google Gen AI.
`GEMINI_MODEL` — Estipulación del modelo genérico por default (gemini-1.5-flash o 2.5).
`REDIS_URL` — Protocolo URL dirigido a la instancia de Redis (`redis://...`).
`ENVIRONMENT` — Denotador del ecosistema habilitado (`development`, `staging`, `production`).
`PORT` — Variable base asignada por Uvicorn (y externalmente por Railway).
`LOG_LEVEL` — Nivel de debugging global.
`URL_EXPIRATION_MINUTES` — Periodo temporal en el cual se invalidan los links de redención final.
`SECRET_KEY` — String randomizado utilizado al inicializar criptografías como Fernet.
`PRODUCT_LEVELS` — Agrupamiento CSV base de niveles del sistema fotográfico cerrado.
`TELEGRAM_BOT_TOKEN` — Llave de autorización expuesta por BotFather.
`TELEGRAM_CHAT_ID` — ID numérico de sesión única para notificar los eventos al administrador.

## Cómo correr el proyecto localmente
1. Clonar el repositorio y copiar su configuración base: `cp .env.example .env` (llenando los secrets primarios de Backblaze, Neon PgSQL, y Gemini).
2. Estipular las bases temporales de memoria: correr instancias locales funcionales o remotas de Redis DB. 
3. Entorno de desarrollo intermedio (Backend): 
   - Generar y abrir entorno `virtualenv`.
   - `pip install -r requirements.txt` (ignorando `faster-whisper` en dependencias).
4. Pre-Caché del Frontend:
   - Ingresa al root frontend (`cd frontend/`).
   - Satisface dependencias (`npm install`).
   - Sirve estáticos duros en Next 16 usando `npm run build`. El compendio final se albergará en `out/`.
5. Run unificado:
   - Desde la raíz principal, ejecuta `python api/run_fastapi.py` (o `uvicorn api.run_fastapi:app`).
   - Esta instrucción levantará el backend y montará la capeta `./frontend/out` al mismo puerto 8000 para acceso estricto y unificado.

## Deploy
El proyecto integra el empaquetamiento final en Railway mediante el uso integral del archivo `railway.json` sobre el `Dockerfile`. Esta arquitectura de stages doble construye los wheels y corre el apt installer en Docker aislando una cuenta non-root asíncrona que expone Uvicorn amarrada a un único proceso final compartiendo puerto web y REST api simultáneamente, permitiendo ser desplegada en Railway de manera 360 y resiliente bajo retries configurados.

## Estado del Proyecto
Actualmente configurado y funcional de punta a punta: El pipeline de React con prevención "anti zoom & blur filter", fluye exitosamente al WebSocket del `run_fastapi.py`. La persistencia transaccional y Redis guardan los historiales. Gemini 2.5 atiende de acuerdo al documento `LOLA_FLASH.md` e inyecta menús interactivos mediante etiquetas `[IMG:MENU_...]`. Paralelamente, la carga de fotos valida con Vision y retorna (sin errores fatales) entregando URL temporales mediante Backblaze B2, lo anterior resguardado por validadores de SPAM y fallos `async_retry`.
