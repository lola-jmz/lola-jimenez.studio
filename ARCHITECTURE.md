# Arquitectura — Lola Jiménez Studio

## Diagrama de Capas

```mermaid
graph TD
    subgraph Frontend [Capa de Presentación - Next.js]
        A1[Landing Page Component]
        A2[useWebSocket Hook]
        A3[ImageWithBlur Component]
    end

    subgraph Backend [Capa de API - FastAPI]
        B1[run_fastapi.py]
        B2[ConnectionManager]
    end

    subgraph Core [Capa de Negocio]
        C1[LolaCoreHandler]
        C2[ConversationManager / StateMachine]
    end

    subgraph Services [Capa de Servicios]
        S1[PaymentValidator]
        S2[ContentDeliveryService]
        S3[TelegramNotifier]
        S4[SecurityManager]
        S5[ErrorHandler y Retry Logic]
    end

    subgraph Data [Capa de Datos]
        D1[DatabasePool asyncpg]
        D2[RedisStateStore]
    end

    subgraph External [Servicios Externos]
        E1[Google Gemini API]
        E2[PostgreSQL Neon]
        E3[Backblaze B2]
        E4[Telegram API]
    end

    A1 <-->|WebSocket| B1
    A2 <-->|JSON Stream| B2
    B1 --> B2
    B1 --> C1
    
    C1 --> C2
    C1 --> S1
    C1 --> S2
    C1 --> S4
    C1 --> S3
    
    C2 --> D2
    C2 --> D1
    
    D1 --> E2
    D2 --> E2
    
    S1 --> E1
    S1 --> D1
    S2 --> E3
    S3 --> E4
```

## Componentes del Backend
* `api/run_fastapi.py`: Entry point global, levanta la app FastAPI, entrega recursos estáticos `next_static` y expone Socket web a un `websocket_endpoint`. Responsabilidad: Orquestar el entorno unificado de la red.
* `core/core_handler.py` (`LolaCoreHandler`): Administrador de flujo natural. Escucha strings puros, inyecta estado temporal (como horários y historiales) y comanda interacciones. Responsabilidad: Gestionar respuestas de IA correctas e intercepción de fotos.
* `core/state_machine.py` (`ConversationManager`): Control de Máquina de Estados Finita; provee transiciones para prevenir saltos irregulares. Responsabilidad: Validar lógicamente en qué fase de venta habita el usuario.
* `services/payment_validator.py` (`PaymentValidator`): Motor anti-fraude operado por IA Vision. Responsabilidad: Confirmar hashes de fotos duplicadas comprobando contra BD y realizar validaciones complejas de transferencias.
* `services/content_delivery.py` (`ContentDeliveryService`): Manager de entrega final que genera URLs con time-to-live temporales. Responsabilidad: Comunicación confiable con Backblaze.
* `storage/redis_store.py` (`RedisStateStore`): Abstracción asíncrona de almacenamiento tipo memoria principal con sub-conexiones de respaldo PG. Responsabilidad: Leer / Grabar metadata vital rápidamente de cara a solicitudes concurrentes directas.
* `database/database_pool.py` (`DatabasePool`): Repositorio madre de asyncpg encapsulando pools reactivos. Responsabilidad: Leer UUIDs, gestionar queries manualmente y recuperar respaldos de historial.

## Flujo Principal: Mensaje de Texto

```mermaid
sequenceDiagram
    actor Usuario
    participant Frontend
    participant API as run_fastapi
    participant Core as LolaCoreHandler
    participant FSM as ConversationManager
    participant Repos as PostgreSQL/Redis
    participant IA as Gemini API

    Usuario->>Frontend: Digita mensaje "texto"
    Frontend->>API: Envia JSON ({type: text, content: ...})
    API->>Core: Llama process_text_message(user_id, msj)
    Core->>Repos: Guarda mensaje de usuario limpio
    Core->>FSM: Lee estado (INICIO o CONVERSANDO)
    Core->>FSM: Ejecuta evento MENSAJE_RECIBIDO
    Core->>Repos: Solicita los últimos N historiales del usuario
    Core->>IA: Elabora Prompt incluyendo (Historial + Persistencia local + Roles)
    IA-->>Core: Genera Respuesta Textual "Lola" + (Opcionalmente Tags [IMG:***])
    Core->>Repos: Graba la respuesta bot final
    Core-->>API: Transmite respuesta final (después de aplicar typing-delay virtual)
    API-->>Frontend: Retorna Eventos Websocket Text / Image-Flyer
    Frontend-->>Usuario: Dibuja burbujas en UI
```

## Flujo de Validación de Pago

```mermaid
sequenceDiagram
    actor Usuario
    participant Frontend
    participant API as run_fastapi
    participant Core as LolaCoreHandler
    participant FSM as ConversationManager
    participant Validador as PaymentValidator
    participant B2 as ContentDeliveryService
    participant Alerts as TelegramNotifier

    Usuario->>Frontend: Anexa foto de voucher de Banco
    Frontend->>API: Codifica imagen Base64 (type: image)
    API->>Core: Envia archivo procesado mediante process_photo_message
    Core->>FSM: Verifica que el state == ESPERANDO_PAGO
    Core->>FSM: Transiciona virtualmente a VALIDANDO_COMPROBANTE
    Core->>Validador: Pide resolución (validate_payment_proof())
    Validador-->>Core: Devuelve JSON {is_valid: true, amount: X, confidence: %...}
    Core->>Alertas: Emite señal asíncrona notify_payment_received (datos OCR)
    Core->>FSM: Causa Evento de COMPROBANTE_VALIDO --> PAGO_APROBADO
    Core->>B2: Delega provisión final deliver_content()
    B2-->>Core: Responde URL protegida TimeToLive generada desde S3 Backblaze
    Core-->>API: Concatena string "Aprobado [DELIVERY:...]"
    API-->>Frontend: Desempaqueta y envía imagen secreta Web Socket Render 
    Frontend-->>Usuario: Actualiza UI con foto sin blur
```

## Máquina de Estados

```mermaid
stateDiagram-v2
    [*] --> INICIO
    INICIO --> CONVERSANDO : MENSAJE_RECIBIDO
    INICIO --> CONVERSANDO : AUDIO_RECIBIDO
    
    CONVERSANDO --> ESPERANDO_PAGO : SOLICITAR_PAGO
    CONVERSANDO --> CONVERSANDO : MENSAJE_RECIBIDO (Loop cotorreo)
    
    ESPERANDO_PAGO --> VALIDANDO_COMPROBANTE : IMAGEN_RECIBIDA
    ESPERANDO_PAGO --> ESPERANDO_PAGO : MENSAJE_RECIBIDO
    
    VALIDANDO_COMPROBANTE --> PAGO_APROBADO : COMPROBANTE_VALIDO
    VALIDANDO_COMPROBANTE --> PAGO_RECHAZADO : COMPROBANTE_INVALIDO
    
    PAGO_RECHAZADO --> VALIDANDO_COMPROBANTE : IMAGEN_RECIBIDA (Reintento de Voucher)
    
    PAGO_APROBADO --> COMPLETADO : PRODUCTO_ENTREGADO
    
    COMPLETADO --> INICIO : RESETEAR
    
    ERROR --> INICIO : RESETEAR
    
    CONVERSANDO --> BLOQUEADO : BLOQUEAR_USUARIO (Rate limits excedidos o sospechoso)
    VALIDANDO_COMPROBANTE --> ERROR : ERROR_OCURRIDO
```

## Componentes del Frontend
* **`LolaJiménezStudioLandingPage`**: El componente base maestro (JSX). Estructura el renderizado HTML general unificado del sitio web: Hero Screen, Portfolio list y agrupa los Dialogs (Modales) de "ChatPrivado". Funciona interactuando bajo el motor Client Side React (con dependencias de Framer-Motion para animaciones fluidas CSS espaciales).
* **`ImageWithBlur`**: Componente Custom encargado de blindaje visual y anti robo de imágenes del landing, integrando escuchas que bloquean drag actions nativos `.preventDefalt()` y aplican capas borrosas si el Window VisualViewport se expande a escalas prohibidas (Event scale > 1.25).
* **`useWebSocket`**: Hook en `/lib/useWebSocket`. Aísla la inicialización de Socket.IO / WSS. Mantiene en un Array state dinámico las burbujas en cache. Exporta utilitarios `connect`, `disconnect`, `sendText`, y `sendImage` junto al enumerador situativo general.

## Servicios Externos
| Servicio | Uso | Módulo que lo consume | Obligatorio/Opcional |
|---|---|---|---|
| PostgreSQL (Neon) | Almacenaje asertivo universal (identificadores, historial, comprobación anti-pHashes transaccionales duplicados) | `database_pool.py`, Repositorios FSM y Soporte `redis_store.py` | Obligatorio |
| Google Gemini API | Motor de inferencia natural textual (Flash 2.5) e interrogatorio Visión AI avanzado OCR a vauchers | `core_handler.py`, `payment_validator.py` | Obligatorio |
| Backblaze B2 | Receptáculo general de Storage y expositor dinámico (Signed Expire URLs) de redenciones | `content_delivery.py` | Obligatorio |
| Redis Cloud | Operador primario en RAM de las variables efímeras temporales del Chat y metadatos FSM | `redis_store.py` | Opcional |
| Telegram Bot API | Gateway HTTP pasivo de disparo asíncrono hacia el mantenedor ante pagos de alta relevancia percibidos | `telegram_notifier.py` | Opcional |
