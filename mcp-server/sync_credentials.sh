#!/bin/bash
# Script para copiar credenciales del .env principal del proyecto Lola Bot al MCP Server

set -e

PROJECT_ENV="/home/gusta/Projects/Negocios/Stafems/lola_bot/.env"
MCP_ENV="/home/gusta/Projects/Negocios/Stafems/lola_bot/mcp-server/.env"

echo "📋 Copiando credenciales del proyecto principal al MCP Server..."

if [ ! -f "$PROJECT_ENV" ]; then
    echo "❌ Error: No se encontró $PROJECT_ENV"
    exit 1
fi

# Leer variables del .env principal
echo "📖 Leyendo credenciales de $PROJECT_ENV..."

# Extraer valores (evitando comentarios y líneas vacías)
DATABASE_URL=$(grep "^DATABASE_URL=" "$PROJECT_ENV" | cut -d '=' -f 2- | tr -d '"')
GEMINI_API_KEY=$(grep "^GEMINI_API_KEY=" "$PROJECT_ENV" | cut -d '=' -f 2- | tr -d '"')

# Crear .env del MCP Server
echo "✍️  Creando $MCP_ENV..."

cat > "$MCP_ENV" << EOF
# PostgreSQL Database
DATABASE_URL=$DATABASE_URL

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Gemini AI
GEMINI_API_KEY=$GEMINI_API_KEY
GEMINI_MODEL=gemini-2.5-pro

# MCP Server
MCP_SERVER_NAME=lola-bot-analysis
MCP_SERVER_VERSION=1.0.0
EOF

echo "✅ Credenciales copiadas exitosamente!"
echo ""
echo "Credenciales configuradas:"
echo "  - DATABASE_URL: ${DATABASE_URL:0:30}..."
echo "  - GEMINI_API_KEY: ${GEMINI_API_KEY:0:20}..."
echo "  - GEMINI_MODEL: gemini-2.5-pro"
echo ""
echo "🚀 Ahora puedes ejecutar: cd mcp-server && source venv/bin/activate && python3 test_mcp_server.py"
