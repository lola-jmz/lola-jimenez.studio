# =============================================================================
# Dockerfile - Lola Jiménez Studio
# =============================================================================
# Multi-stage build para imagen optimizada
# =============================================================================

FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependencias del sistema para compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y crear wheels
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# =============================================================================
# Imagen final
# =============================================================================
FROM python:3.11-slim

WORKDIR /app

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash appuser

# Instalar dependencias del sistema (runtime only)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copiar wheels pre-compilados e instalar
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# Copiar código de la aplicación
COPY --chown=appuser:appuser . .

# Cambiar a usuario no-root
USER appuser

# Variables de entorno por defecto
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

# Exponer puerto (Railway usa $PORT)
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

# Comando de inicio
CMD ["sh", "-c", "uvicorn api.run_fastapi:app --host 0.0.0.0 --port ${PORT}"]
