# Bot de Telegram "María" - Vendedora de Imágenes Digitales

Bot de Telegram inteligente que vende imágenes digitales de forma conversacional usando IA.

## Características

- **Conversación Natural**: Usa Gemini 2.5 Flash para interacciones humanas
- **Transcripción de Audio**: Soporta mensajes de voz con faster-whisper (local, sin costo)
- **Validación de Pagos**: Analiza comprobantes con Gemini Vision
- **Alta Concurrencia**: Diseñado para 150+ usuarios simultáneos
- **Resiliencia**: Retry logic, circuit breakers, y error handling robusto
- **Seguridad**: Encriptación, validación de entrada, rate limiting
- **Optimizado**: Connection pooling con asyncpg, latencia <100ms

## Stack Tecnológico

- **Python 3.12+**
- **PostgreSQL 16+** (base de datos)
- **python-telegram-bot** (Telegram API)
- **Google Gemini 2.5 Flash** (LLM + Vision)
- **faster-whisper** (transcripción de audio local)
- **asyncpg** (connection pooling)
- **cryptography** (seguridad)

## Arquitectura

```
lola_bot/
├── bot_optimized.py           # Bot principal con toda la lógica
├── database_pool.py           # Connection pooling para PostgreSQL
├── state_machine.py           # FSM para gestión de estados
├── message_buffer_optimized.py # Buffer thread-safe de mensajes
├── error_handler.py           # Retry logic y circuit breakers
├── security.py                # Encriptación, validación, rate limiting
├── audio_transcriber.py       # Transcripción con faster-whisper
├── payment_validator.py       # Validación de comprobantes con Gemini Vision
├── config/
│   └── database_schema.sql   # Schema de PostgreSQL
├── LOLA.md                   # Personalidad del bot (NO MODIFICAR)
├── requirements.txt           # Dependencias
├── .env                       # Credenciales (NO COMMITEAR)
└── .env.example               # Template de configuración
```

## Instalación

### 1. Requisitos Previos

- Python 3.12 o superior
- PostgreSQL 16 o superior
- ffmpeg (para procesamiento de audio)

#### Instalar Python 3.12

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip

# macOS
brew install python@3.12

# Verificar instalación
python3 --version
```

#### Instalar PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql@16

# Iniciar servicio
sudo systemctl start postgresql  # Linux
brew services start postgresql@16  # macOS
```

#### Instalar ffmpeg

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### 2. Clonar y Configurar Proyecto

```bash
# Clonar repositorio (si aplica) o navegar al directorio
cd telegram_bot

# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configurar Base de Datos

```bash
# Crear usuario y base de datos
sudo -u postgres psql

# En el shell de PostgreSQL:
CREATE USER maria_bot WITH PASSWORD 'tu_password_seguro';
CREATE DATABASE maria_bot OWNER maria_bot;
GRANT ALL PRIVILEGES ON DATABASE maria_bot TO maria_bot;
\q

# Aplicar schema
psql -U maria_bot -d maria_bot -f config/database_schema.sql
```

### 4. Configurar Variables de Entorno

```bash
# Copiar template
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

**Obtener credenciales:**

1. **TELEGRAM_BOT_TOKEN**: Habla con [@BotFather](https://t.me/BotFather) en Telegram
   - Envía `/newbot` y sigue las instrucciones
   - Guarda el token que te proporciona

2. **GEMINI_API_KEY**: Visita [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Crea una API key
   - Guárdala en `.env`

3. **ADMIN_USER_ID**: Tu user ID de Telegram
   - Habla con [@userinfobot](https://t.me/userinfobot)
   - Copia tu ID numérico

4. **DATABASE_URL**: Formato `postgresql://usuario:password@host:puerto/bd`
   - Ejemplo: `postgresql://maria_bot:tu_password@localhost:5432/maria_bot`

5. **ENCRYPTION_KEY**: Genera una clave de encriptación
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

### 5. Ejecutar el Bot

```bash
# Activar entorno virtual (si no está activado)
source venv/bin/activate

# Ejecutar bot
python bot_optimized.py
```

El bot mostrará:
```
🚀 Inicializando Bot María...
✅ Bot María inicializado correctamente
🚀 Bot María iniciando...
```

## Uso

### Comandos del Bot

- `/start` - Iniciar conversación
- `/help` - Ver ayuda
- `/reset` - Reiniciar conversación

### Flujo de Conversación

1. Usuario inicia con `/start`
2. María saluda y pregunta qué necesita
3. Usuario describe qué imagen busca
4. María recomienda imágenes y persuade
5. Usuario acepta comprar
6. María solicita comprobante de pago
7. Usuario envía imagen del comprobante
8. María valida automáticamente
9. Si válido, entrega la imagen
10. Conversación finaliza

### Tipos de Mensajes Soportados

- **Texto**: Conversación normal
- **Audio/Voz**: Transcripción automática con faster-whisper
- **Imágenes**: Validación de comprobantes de pago con Gemini Vision

## Testing

### Tests Automáticos

Los tests se ejecutan automáticamente después de editar archivos `.py` (configurado en hooks).

```bash
# Ejecutar tests manualmente
pytest

# Con cobertura
pytest --cov=.

# Test específico
pytest test_bot.py -v
```

### Tests de Módulos Individuales

Cada módulo tiene tests integrados:

```bash
# Test database pool
python database_pool.py

# Test audio transcriber
python audio_transcriber.py

# Test payment validator
python payment_validator.py

# Test state machine
python state_machine.py
```

## Monitoreo

### Métricas del Connection Pool

```python
from database_pool import DatabasePool

pool = DatabasePool(dsn="...")
await pool.initialize()

metrics = pool.get_metrics()
print(f"Queries ejecutados: {metrics.total_queries_executed}")
print(f"Tiempo promedio: {metrics.average_query_time_ms}ms")
```

### Health Check de Base de Datos

```python
is_healthy = await pool.health_check()
if not is_healthy:
    logger.error("Base de datos no saludable")
```

### Estadísticas de Transcripción

```python
from audio_transcriber import AudioTranscriber

transcriber = AudioTranscriber()
stats = transcriber.get_stats()
print(f"Transcripciones: {stats['total_transcriptions']}")
```

## Troubleshooting

### Error: "Faltan variables de entorno requeridas"

Verifica que `.env` tiene todas las variables necesarias:
```bash
cat .env
```

### Error: "asyncpg.exceptions.InvalidCatalogNameError"

La base de datos no existe. Créala:
```bash
sudo -u postgres createdb maria_bot
psql -U maria_bot -d maria_bot -f config/database_schema.sql
```

### Error: "faster-whisper no está instalado"

Reinstala dependencias:
```bash
pip install -r requirements.txt
```

### Bot no responde

1. Verifica que el bot esté ejecutándose
2. Revisa los logs en la terminal
3. Verifica que el token de Telegram sea correcto
4. Prueba con `/start`

### Transcripción de audio lenta

El modelo "base" de faster-whisper es un balance. Si necesitas más velocidad:
```python
transcriber = AudioTranscriber(model_size="tiny")
```

## Despliegue en Producción

### Docker Compose (Recomendado)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: maria_bot
      POSTGRES_USER: maria_bot
      POSTGRES_PASSWORD: tu_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./config/database_schema.sql:/docker-entrypoint-initdb.d/schema.sql
    ports:
      - "5432:5432"

  bot:
    build: .
    depends_on:
      - postgres
    env_file:
      - .env
    volumes:
      - ./MARÍA.md:/app/MARÍA.md:ro
    restart: unless-stopped

volumes:
  postgres_data:
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y ffmpeg postgresql-client

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot_optimized.py"]
```

### Desplegar

```bash
docker-compose up -d
```

## Seguridad

- ✅ **NUNCA** commitear `.env` al repositorio
- ✅ Usar `.env.example` como referencia
- ✅ Rotar API keys periódicamente
- ✅ Usar passwords fuertes para PostgreSQL
- ✅ Habilitar SSL para conexiones de BD en producción
- ✅ Configurar firewall para limitar acceso a PostgreSQL
- ✅ Hacer backups regulares de la base de datos

## Backups

```bash
# Backup de base de datos
pg_dump -U maria_bot maria_bot > backup_$(date +%Y%m%d).sql

# Restaurar backup
psql -U maria_bot maria_bot < backup_20250124.sql
```

## Costos Estimados

- **Infraestructura**: $0/mes (Oracle Cloud Always Free)
- **Gemini API**: $0-20/mes (depende del volumen)
- **faster-whisper**: $0/mes (100% local)
- **Total**: **$0-20/mes** para 150+ usuarios

Ahorro vs usar OpenAI Whisper API: ~$1,800/año

## Roadmap

### Fase 1: Básico ✅
- [x] Bot funcional con texto
- [x] Integración con Gemini
- [x] Base de datos PostgreSQL
- [x] Estado y buffer de mensajes

### Fase 2: Audio 🔄
- [x] Transcripción con faster-whisper
- [ ] Testing de audio en producción

### Fase 3: Pagos 🔄
- [x] Validación de comprobantes
- [ ] Sistema de scoring
- [ ] Aprobación manual para casos dudosos

### Fase 4: Entrega 📅
- [ ] Integración con Oracle Object Storage
- [ ] Sistema de entrega automática
- [ ] Gestión de catálogo de imágenes

### Fase 5: Monitoring 📅
- [ ] Prometheus/Grafana
- [ ] Alertas automáticas
- [ ] Dashboard de métricas

## Contribuir

1. Fork el proyecto
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m "Añade nueva funcionalidad"`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Abre un Pull Request

## Licencia

MIT License - Consulta el archivo LICENSE para más detalles

## Soporte

- **Issues**: Abre un issue en GitHub
- **Documentación**: Lee `EVALUACION_COMPLETA_BOT_MARIA.md` para detalles técnicos
- **Personalidad**: Lee `MARÍA.md` para entender el personaje del bot

## Créditos

Desarrollado siguiendo las mejores prácticas de:
- Arquitectura de microservicios
- Clean Code
- Principios SOLID
- Diseño orientado al dominio (DDD)

---

**Made with ❤️ for María, la mejor vendedora virtual**
