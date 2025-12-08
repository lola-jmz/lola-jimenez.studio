# MCP Server - Bot Lola Analysis Tools

Servidor MCP (Model Context Protocol) para análisis avanzado de conversaciones del Bot Lola. Permite integración con Claude Desktop, Cline, Continue, Windsurf y otras herramientas compatibles con MCP.

## 🎯 Características

- **Análisis de Conversaciones:** Historial completo, red flags, sugerencias de personalidad, métricas de engagement
- **Testing de Personalidad:** Prueba variantes de prompts con Gemini AI
- **Métricas de Conversión:** Revenue, tasas de conversión, tendencias temporales
- **Detección de Red Flags:** Score de riesgo 0-100 con recomendaciones
- **Exportación de Datos:** Formato JSONL para fine-tuning de Gemini

## 📋 Requisitos

- Python 3.12+
- PostgreSQL (base de datos de Bot Lola)
- Redis
- Gemini API Key (para testing de personalidad)

## 🚀 Instalación

### 1. Crear entorno virtual

```bash
cd /home/gusta/Projects/Negocios/Stafems/lola_bot/mcp-server
python -m venv venv
source venv/bin/activate  # En Linux/Mac
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

**Opción A: Sincronizar con el proyecto principal (Recomendado)**

Si ya tienes configurado el Bot Lola, puedes copiar las credenciales automáticamente:

```bash
cd /home/gusta/Projects/Negocios/Stafems/lola_bot/mcp-server
./sync_credentials.sh
```

Este script copia automáticamente:
- `DATABASE_URL` desde el .env principal
- `GEMINI_API_KEY` desde el .env principal
- Configura `GEMINI_MODEL=gemini-2.5-pro`

**Opción B: Configuración manual**

```bash
cp .env.example .env
nano .env  # Editar con tus credenciales
```

**Ejemplo de `.env`:**

```bash
DATABASE_URL=postgresql://postgres:Stafems@localhost:5432/maria_bot
REDIS_HOST=localhost
REDIS_PORT=6379
GEMINI_API_KEY=tu_api_key_de_gemini
GEMINI_MODEL=gemini-2.5-pro
```

### 4. Validar instalación

```bash
python test_mcp_server.py
```

Deberías ver:

```
✅ PostgreSQL Connection: OK
✅ Redis Connection: OK
✅ Gemini Client: OK
✅ analyze_conversation: OK
✅ test_personality_prompt: OK
✅ get_conversion_metrics: OK
✅ detect_red_flags: OK
✅ export_training_data: OK

🎉 ¡Todos los tests pasaron!
```

## 🔧 Configuración en Claude Desktop

### Opción 1: Configuración Manual

Edita el archivo de configuración de Claude Desktop:

```bash
nano ~/.config/claude/mcp_servers.json
```

Agrega la siguiente configuración:

```json
{
  "mcpServers": {
    "lola-bot-analysis": {
      "command": "python",
      "args": [
        "/home/gusta/Projects/Negocios/Stafems/lola_bot/mcp-server/server.py"
      ],
      "env": {
        "PYTHONPATH": "/home/gusta/Projects/Negocios/Stafems/lola_bot/mcp-server"
      }
    }
  }
}
```

### Opción 2: Script de Configuración (Futuro)

```bash
# TODO: Crear script de auto-configuración
./scripts/configure_claude_desktop.sh
```

### Verificar en Claude Desktop

1. Reinicia Claude Desktop
2. Abre una nueva conversación
3. Verifica que aparezca el ícono de herramientas MCP (🔧 o similar)
4. Prueba: "Analiza la conversación del usuario 123456789"

## 📚 Herramientas Disponibles

### 1. `analyze_conversation`

Analiza la conversación completa de un usuario.

**Input:**
```json
{
  "user_id": "123456789"
}
```

**Output:**
```json
{
  "user_info": { ... },
  "conversation_state": { ... },
  "message_history": [ ... ],
  "red_flags": [ ... ],
  "personality_suggestions": [ ... ],
  "engagement_metrics": { ... }
}
```

**Ejemplo en Claude Desktop:**

> "Analiza la conversación del usuario 123456789"

### 2. `test_personality_prompt`

Prueba una variante de personalidad de Lola.

**Input:**
```json
{
  "variant_text": "Usa más emojis y sé más directa con los precios",
  "test_messages": [
    "Hola Lola",
    "Me interesa tu contenido",
    "Cuánto cuesta?"
  ]
}
```

**Output:**
```json
{
  "original_responses": [ ... ],
  "variant_responses": [ ... ],
  "comparison": {
    "length_difference_percent": -15.2,
    "emoji_difference_percent": 40.0,
    "tone_original": "vulnerable",
    "tone_variant": "transactional",
    "recommendation": "..."
  }
}
```

**Ejemplo en Claude Desktop:**

> "Prueba esta variante de personalidad: 'Sé más directa con los precios y usa emojis'. Usa estos mensajes de prueba: 'Hola', 'Qué vendes?', 'Cuánto?'"

### 3. `get_conversion_metrics`

Obtiene métricas de conversión para un rango de fechas.

**Input:**
```json
{
  "date_range": "2025-11-01:2025-11-28"
}
```

**Output:**
```json
{
  "period": {
    "start": "2025-11-01",
    "end": "2025-11-28",
    "days": 28
  },
  "metrics": {
    "total_users": 150,
    "paid_users": 35,
    "conversion_rate": 23.33,
    "total_revenue": 12450.00,
    "average_revenue_per_user": 355.71
  },
  "by_product": { ... },
  "trends": { ... }
}
```

**Ejemplo en Claude Desktop:**

> "Dame las métricas de conversión de noviembre 2025"
> "Cuál fue el revenue del 1 al 15 de noviembre?"

### 4. `detect_red_flags`

Detecta comportamientos sospechosos de un usuario.

**Input:**
```json
{
  "user_id": "123456789"
}
```

**Output:**
```json
{
  "user_id": 123456789,
  "risk_score": 75,
  "risk_level": "HIGH",
  "red_flags": [
    {
      "type": "PERSONAL_INFO_REQUESTS",
      "count": 5,
      "severity": "HIGH",
      "description": "Solicitó información personal 5 veces"
    }
  ],
  "recommendations": [
    "Activar Fase de Protección inmediatamente",
    "NO procesar pagos sin validación manual"
  ]
}
```

**Ejemplo en Claude Desktop:**

> "Analiza si el usuario 123456789 tiene comportamiento sospechoso"
> "Qué tan riesgoso es el usuario 987654321?"

### 5. `export_training_data`

Exporta conversaciones en formato JSONL para fine-tuning.

**Input:**
```json
{
  "filters": {
    "only_successful_conversions": true,
    "min_messages": 5,
    "date_range": "2025-11-01:2025-11-28",
    "exclude_blocked_users": true
  }
}
```

**Output:**
```json
{
  "export_path": "/path/to/exports/training_data_20251128_021230.jsonl",
  "stats": {
    "total_conversations": 35,
    "total_messages": 850,
    "successful_conversions": 35,
    "file_size_mb": 2.4
  }
}
```

**Ejemplo en Claude Desktop:**

> "Exporta las conversaciones exitosas de noviembre para entrenar Gemini"
> "Dame un dataset de entrenamiento con conversaciones de más de 10 mensajes"

## 💡 Ejemplos de Uso

### Análisis Post-Mortem de Conversación

```
Usuario: Analiza la conversación del usuario 123456789

Claude (usando MCP):
📊 Análisis de Conversación - Usuario 123456789

Usuario: @ejemplo_user
Estado: No ha pagado
Red Flags: 2 detectados
- INSISTENCE_ON_MEETING: Insistió 3 veces en encuentro físico
- PERSONAL_INFO_REQUESTS: Preguntó 2 veces por ubicación

Sugerencias:
- Usuario altamente comprometido (25 mensajes)
- Activar Fase de Protección
- Si persiste, considerar bloqueo
```

### Optimización de Personalidad

```
Usuario: Quiero que Lola sea más directa con los precios. Prueba esta variante:
"Menciona el precio inmediatamente cuando el usuario muestre interés"

Claude (usando MCP):
🧪 Prueba de Personalidad

Variante: Precios más directos

Mensaje: "Me interesa tu contenido"

Original: "ah si. pues... tengo de diferentes opciones: pies. lencería provocativa, topless 🫣"
Variante: "tengo pies $150, lencería $200, topless $400 🫣"

Análisis:
- Variante es 30% más corta
- Tono cambió de "vulnerable" a "transactional"
- ⚠️ ADVERTENCIA: Puede reducir calidez y conversión

Recomendación: Probar con A/B test antes de aplicar
```

### Análisis de Métricas

```
Usuario: Dame las métricas de todo noviembre

Claude (usando MCP):
📈 Métricas de Conversión - Noviembre 2025

Período: 2025-11-01 a 2025-11-30 (30 días)

General:
- Total usuarios: 150
- Usuarios que pagaron: 35
- Tasa de conversión: 23.33%
- Revenue total: $12,450.00
- ARPU: $83.00

Mejor día: 2025-11-15 ($850 revenue)
Peor día: 2025-11-03 ($120 revenue)
Hora pico: 20:00-22:00

Top productos:
1. Nivel 2 Topless: $4,800 (12 ventas)
2. Nivel 1 Lencería: $3,000 (15 ventas)
```

## 🛠️ Desarrollo y Testing

### Ejecutar servidor localmente

```bash
python server.py
```

El servidor esperará conexiones MCP por stdin/stdout.

### Ejecutar tests

```bash
python test_mcp_server.py
```

### Estructura del Proyecto

```
mcp-server/
├── server.py              # Servidor MCP principal
├── config.py              # Configuración y conexiones
├── requirements.txt       # Dependencias
├── .env.example          # Template de variables
├── .env                  # Variables (no commited)
├── test_mcp_server.py    # Suite de tests
├── README.md             # Esta documentación
├── tools/
│   ├── __init__.py
│   ├── analyze_conversation.py
│   ├── test_personality.py
│   ├── get_metrics.py
│   ├── detect_red_flags.py
│   └── export_data.py
└── exports/              # Archivos JSONL exportados
    └── training_data_*.jsonl
```

## 🔒 Seguridad

> **⚠️ IMPORTANTE**
> - El MCP Server tiene acceso completo a la base de datos de producción
> - NO compartir el archivo `.env` (contiene credenciales)
> - Los archivos exportados pueden contener datos sensibles
> - Solo otorgar acceso a personal autorizado

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'mcp'"

```bash
pip install mcp
```

### Error: "Connection refused" (PostgreSQL)

Verifica que PostgreSQL esté corriendo:

```bash
sudo systemctl status postgresql
```

### Error: "Connection refused" (Redis)

Verifica que Redis esté corriendo:

```bash
sudo systemctl status redis
```

### Error: "GEMINI_API_KEY no configurada"

La herramienta `test_personality_prompt` requiere Gemini API Key. Las demás herramientas funcionan sin ella.

Obtén tu API key en: https://aistudio.google.com/app/apikey

### Claude Desktop no detecta el servidor

1. Verifica que la ruta en `mcp_servers.json` sea correcta
2. Reinicia Claude Desktop completamente
3. Revisa los logs de Claude Desktop (ubicación depende del OS)

### "No se encontraron conversaciones"

Es normal si la base de datos está vacía o no hay conversaciones que cumplan los filtros.

## 📖 Documentación Adicional

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Bot Lola - Documentación del Proyecto](../README.md)
- [Personalidad de Lola](../docs/LOLA.md)

## 🚧 Roadmap

Funcionalidades planeadas para futuras versiones:

- [ ] Dashboard web para visualizar métricas
- [ ] Alertas en tiempo real de red flags críticos
- [ ] Análisis de sentimiento con ML
- [ ] Predicción de conversión
- [ ] A/B testing automático de personalidad
- [ ] Integración con Telegram para notificaciones

## 📝 Changelog

### v1.0.0 (2025-11-28)

- ✅ Implementación inicial
- ✅ 5 herramientas MCP funcionales
- ✅ Conexión a PostgreSQL, Redis, Gemini
- ✅ Suite de tests completa
- ✅ Documentación completa

## 👥 Soporte

Para preguntas o issues:

1. Revisa la sección Troubleshooting
2. Ejecuta `python test_mcp_server.py` para diagnosticar
3. Contacta al equipo de desarrollo

---

**Desarrollado para Bot Lola** | Noviembre 2025
