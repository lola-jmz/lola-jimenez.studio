# 🚀 Guía de Deploy - Bot Lola en Railway

Esta guía documenta el proceso completo de deployment del Bot Lola en Railway con dominio personalizado.

---

## 📋 Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Servicios Externos](#servicios-externos)
3. [Configuración de GitHub](#configuración-de-github)
4. [Deploy en Railway](#deploy-en-railway)
5. [Configuración de Redis](#configuración-de-redis)
6. [Variables de Entorno](#variables-de-entorno)
7. [Dominio Personalizado](#dominio-personalizado)
8. [Verificación](#verificación)
9. [Troubleshooting](#troubleshooting)
10. [Comandos Útiles](#comandos-útiles)

---

## 📦 Requisitos Previos

### Herramientas Necesarias
- **Node.js:** v20.19.5+
- **Railway CLI:** Instalado globalmente
  ```bash
  npm install -g @railway/cli
  ```
- **Git:** Configurado con cuenta GitHub
- **curl:** Para verificaciones

### Cuentas Necesarias
- ✅ GitHub (repositorio privado)
- ✅ Railway (trial gratuito de 30 días)
- ✅ Neon PostgreSQL (plan gratuito)
- ✅ Backblaze B2 (10 GB gratuitos)
- ✅ 123REG (dominios `.studio`)
- ✅ Google AI Studio (API Key de Gemini)

---

## 🌐 Servicios Externos

### 1. Neon PostgreSQL

**Dashboard:** https://console.neon.tech

**Configuración:**
- Database: `neondb`
- Region: `us-west-2`
- Connection pooling: Habilitado

**String de conexión:**
```
postgresql://neondb_owner:***@ep-floral-hall-af0ewhy1-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require
```

**Tablas creadas:**
- `users` (usuarios de WhatsApp)
- `conversations` (historial de conversaciones)
- `payments` (pagos validados)
- `media_files` (metadata de archivos)
- `redis_backup` (respaldo de estado Redis)

---

### 2. Backblaze B2

**Dashboard:** https://secure.backblaze.com/b2_buckets.htm

**Bucket:**
- Nombre: `lola-content`
- Type: Private
- Region: `us-west-004`
- Lifecycle: Keep all versions
- Endpoint: `s3.us-west-004.backblazeb2.com`

**Application Key:**
- Crear en: Application Keys → Add New
- Capabilities: Read/Write
- Guardar: `keyID` y `applicationKey`

---

### 3. Google AI Studio

**Dashboard:** https://aistudio.google.com/apikey

**API Key:**
- Crear nueva API Key
- Modelo usado: `gemini-2.5-flash`
- Guardar para variable `GEMINI_API_KEY`

---

### 4. Dominio (123REG)

**Dashboard:** https://account.123-reg.co.uk/products

**Dominios adquiridos:**
- `lola-jimenez.studio` ✅ (configurado)
- `vorn-arq.studio` (disponible)
- `agnt-pyme.studio` (disponible)

---

## 🔧 Configuración de GitHub

### 1. Crear Repositorio Privado

```bash
cd /home/gusta/Projects/Negocios/Stafems/lola_bot

# Inicializar git si no existe
git init

# Crear repositorio en GitHub (privado)
# Nombre: lola-jimenez-studio
# Visibilidad: Private

# Añadir remote
git remote add origin https://github.com/Gucci-Veloz/lola-jimenez-studio.git

# Primer commit
git add .
git commit -m "Initial commit: Bot Lola production ready"
git branch -M main
git push -u origin main
```

### 2. Archivo `.gitignore`

Asegurar que `.env` esté ignorado:
```gitignore
.env
.env.local
__pycache__/
*.pyc
venv/
node_modules/
```

---

## 🚂 Deploy en Railway

### 1. Login en Railway CLI

```bash
railway login
```

Se abrirá navegador para autenticación.

### 2. Crear Proyecto

**Opción A: Desde CLI**
```bash
railway init
```

**Opción B: Desde Dashboard**
1. Ir a https://railway.app/new
2. "Empty Project"
3. Nombrar: `lola-jimenez-studio`

### 3. Conectar GitHub Repo

**Desde Railway Dashboard:**
1. Settings → Source
2. "Connect Repo"
3. Seleccionar: `Gucci-Veloz/lola-jimenez-studio`
4. Root Directory: `/`

### 4. Configurar Build

**Builder:** Dockerfile (detectado automáticamente)

**Dockerfile Path:** `Dockerfile` (en raíz)

**Port:** `8080` (definido en código)

**Metal Build Environment:** Habilitado (opcional para builds más rápidos)

---

## 🔴 Configuración de Redis

### 1. Añadir Servicio Redis

**Desde Railway Dashboard:**
1. Click en "+ New"
2. "Database" → "Add Redis"
3. Esperar a que se despliegue (~30 segundos)

**Resultado:**
- Servicio: `Redis`
- URL interna: `redis.railway.internal:6379`
- URL externa: `redis://default:***@redis.railway.internal:6379`

### 2. Conectar a Aplicación Principal

**Copiar REDIS_URL:**
1. Click en servicio Redis
2. Variables → `REDIS_URL`
3. Copiar valor completo

**Añadir a servicio principal:**
1. Click en servicio `lola-jimenez-studio`
2. Variables → "+ New Variable"
3. Key: `REDIS_URL`
4. Value: `redis://default:***@redis.railway.internal:6379`

**Re-deploy:**
```bash
railway up --detach
```

---

## 🔐 Variables de Entorno

### Variables Requeridas

**Desde Railway Dashboard → Variables:**

```bash
# Base de Datos PostgreSQL (Neon)
DATABASE_URL=postgresql://neondb_owner:***@ep-floral-hall-af0ewhy1-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require

# Redis (Railway Internal)
REDIS_URL=redis://default:***@redis.railway.internal:6379

# Backblaze B2
B2_KEY_ID=your_key_id
B2_APPLICATION_KEY=your_application_key
B2_BUCKET_NAME=lola-content
B2_ENDPOINT=https://s3.us-west-004.backblazeb2.com

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# WhatsApp Business (Meta)
META_PHONE_NUMBER_ID=your_phone_number_id
META_VERIFY_TOKEN=your_verify_token
META_ACCESS_TOKEN=your_access_token

# Configuración Aplicación
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Verificar Variables

```bash
railway variables
```

---

## 🌍 Dominio Personalizado

### 1. Obtener IP de Railway

```bash
# Obtener dominio Railway
railway domain

# Output ejemplo:
# lola-jimenez-studio-production.up.railway.app

# Obtener IP
dig +short lola-jimenez-studio-production.up.railway.app A
```

**IP Railway:** `66.33.22.201` (puede variar)

### 2. Configurar DNS en 123REG

**Dashboard:** https://account.123-reg.co.uk/products

**Pasos:**
1. Click en dominio `lola-jimenez.studio`
2. "Manage DNS"
3. **ELIMINAR** registro "Parked" si existe
4. **Añadir** registro A:
   - Type: `A`
   - Name: `@` (dominio raíz)
   - Value: `66.33.22.201` (IP de Railway)
   - TTL: `1/2 Hour` (1800 segundos)
5. Guardar cambios

### 3. Añadir Dominio en Railway

**Dashboard Railway:**
1. Service → Settings → Networking
2. "+ Custom Domain"
3. Ingresar: `lola-jimenez.studio`
4. Railway validará automáticamente

### 4. Verificar DNS Propagación

```bash
dig +short lola-jimenez.studio A
# Debe devolver: 66.33.22.201
```

**Tiempo de propagación:** 5-30 minutos

### 5. Esperar Certificado SSL

Railway genera certificado SSL automáticamente usando Let's Encrypt.

**Estado en Railway:**
- "Certificate Authority is validating challenges" → En proceso
- "Active" → Certificado listo

**Tiempo estimado:** 5-15 minutos después de DNS propagado

---

## ✅ Verificación

### 1. Health Check

**URL Railway:**
```bash
curl https://lola-jimenez-studio-production.up.railway.app/health
# Esperado: {"status":"ok"}
```

**URL Personalizada (cuando SSL esté listo):**
```bash
curl https://lola-jimenez.studio/health
# Esperado: {"status":"ok"}
```

### 2. Verificar Logs

```bash
cd /home/gusta/Projects/Negocios/Stafems/lola_bot
railway logs --tail 50
```

**Logs esperados:**
```
✅ PostgreSQL conectado
✅ Conexión a Redis establecida
✅ Redis conectado con respaldo PostgreSQL
✅ BackblazeB2Client inicializado para bucket: lola-content
✅ Personalidad de Lola cargada desde LOLA_FLASH.md
✅ LolaCoreHandler inicializado
🎉 Bot Lola - Backend listo y operativo
```

### 3. Verificar SSL

```bash
openssl s_client -connect lola-jimenez.studio:443 -servername lola-jimenez.studio < /dev/null 2>/dev/null | openssl x509 -noout -dates -issuer
```

**Esperado:**
```
notBefore=Dec XX XX:XX:XX 2025 GMT
notAfter=Mar XX XX:XX:XX 2026 GMT
issuer=C = US, O = Let's Encrypt, CN = R12
```

### 4. Verificar Servicios

**PostgreSQL:**
```bash
railway run python -c "from database.database_pool import DatabasePool; pool = DatabasePool(); print('✅ PostgreSQL OK')"
```

**Redis:**
```bash
railway run python -c "import redis; r = redis.from_url('redis://default:***@redis.railway.internal:6379'); r.ping(); print('✅ Redis OK')"
```

**Backblaze B2:**
- Dashboard → Browse Files → Bucket `lola-content`
- Debe estar accesible (0 bytes inicial es normal)

---

## 🛠️ Troubleshooting

### Problema: "No linked project found"

**Error:**
```bash
railway logs
# No linked project found. Run railway link
```

**Solución:**
```bash
cd /home/gusta/Projects/Negocios/Stafems/lola_bot
railway link
# Seleccionar proyecto correcto
```

---

### Problema: Redis no conecta

**Error en logs:**
```
redis.exceptions.ConnectionError
```

**Verificar:**
1. Variable `REDIS_URL` configurada en Railway
2. Valor correcto: `redis://default:***@redis.railway.internal:6379`
3. Servicio Redis en estado "Active"

**Solución:**
```bash
railway variables --set "REDIS_URL=redis://default:***@redis.railway.internal:6379"
railway up --detach
```

---

### Problema: SSL no se activa

**Error:**
```bash
curl: (60) SSL: no alternative certificate subject name matches...
```

**Causas posibles:**
1. DNS no propagado correctamente
2. Validación Let's Encrypt en proceso (esperar 5-15 min)
3. Registro DNS incorrecto

**Verificaciones:**
```bash
# 1. Verificar DNS
dig +short lola-jimenez.studio A
# Debe devolver IP de Railway

# 2. Verificar en Railway Dashboard
# Settings → Networking → Dominio debe mostrar "Active"

# 3. Esperar y verificar periódicamente
curl -I https://lola-jimenez.studio/health 2>&1 | grep -E "HTTP|curl:"
```

**Si después de 30 min sigue fallando:**
1. Eliminar dominio en Railway
2. Verificar registro DNS en 123REG
3. Volver a añadir dominio en Railway

---

### Problema: Build falla

**Error común:**
```
ERROR: failed to solve: failed to compute cache key
```

**Soluciones:**
1. Verificar `Dockerfile` en repositorio
2. Verificar `.dockerignore` no excluye archivos críticos
3. Re-trigger build manualmente en Railway

---

### Problema: LOLA_FLASH.md no se carga

**Error en logs:**
```
WARNING - No se pudo cargar personalidad desde LOLA_FLASH.md
```

**Verificar:**
1. Archivo existe en raíz del proyecto
2. Incluido en `Dockerfile`:
   ```dockerfile
   COPY LOLA_FLASH.md .
   ```

**Solución:**
```bash
git add LOLA_FLASH.md
git commit -m "Fix: Include LOLA_FLASH.md in Docker build"
git push
# Railway re-deployeará automáticamente
```

---

## 📝 Comandos Útiles

### Railway CLI

```bash
# Login
railway login

# Linkear proyecto
railway link

# Ver variables
railway variables

# Set variable
railway variables --set "KEY=value"

# Deploy
railway up --detach

# Logs en tiempo real
railway logs

# Status del servicio
railway status

# Abrir en navegador
railway open

# Ejecutar comando en Railway
railway run <command>
```

### Verificación de Servicios

```bash
# Health check local
curl http://localhost:8080/health

# Health check Railway
curl https://lola-jimenez-studio-production.up.railway.app/health

# Health check dominio personalizado
curl https://lola-jimenez.studio/health

# Headers completos
curl -I https://lola-jimenez.studio/health

# Verificar SSL
curl -v https://lola-jimenez.studio/health 2>&1 | grep "SSL"

# DNS lookup
dig +short lola-jimenez.studio A
nslookup lola-jimenez.studio
```

### Git

```bash
# Status
git status

# Commit y push
git add .
git commit -m "mensaje"
git push

# Ver remotes
git remote -v

# Ver último commit
git log -1
```

### Docker (local testing)

```bash
# Build imagen
docker build -t lola-bot .

# Ejecutar local
docker run -p 8080:8080 --env-file .env lola-bot

# Ver logs
docker logs <container_id>
```

---

## 📊 Arquitectura Final

```
Usuario (WhatsApp)
    ↓
Meta Webhook → lola-jimenez.studio (Railway)
    ↓
FastAPI Backend (Puerto 8080)
    ├─→ PostgreSQL (Neon) - Base de datos principal
    ├─→ Redis (Railway) - Estado y caché
    └─→ Backblaze B2 - Storage de imágenes
    └─→ Gemini AI - Procesamiento de lenguaje
```

---

## 🔑 URLs y Recursos

### Production

| Servicio | URL |
|----------|-----|
| **Backend** | https://lola-jimenez.studio |
| **Health Check** | https://lola-jimenez.studio/health |
| **Railway URL** | https://lola-jimenez-studio-production.up.railway.app |

### Dashboards

| Servicio | Dashboard |
|----------|-----------|
| **Railway** | https://railway.app/project/6ee74e18-193a-4ec3-b1c3-d402d6bed2db |
| **Neon PostgreSQL** | https://console.neon.tech |
| **Backblaze B2** | https://secure.backblaze.com/b2_buckets.htm |
| **123REG** | https://account.123-reg.co.uk/products |
| **GitHub Repo** | https://github.com/Gucci-Veloz/lola-jimenez-studio |
| **Google AI Studio** | https://aistudio.google.com/apikey |

---

## 📚 Recursos Adicionales

### Documentación Oficial
- [Railway Docs](https://docs.railway.app/)
- [Neon Docs](https://neon.tech/docs/)
- [Backblaze B2 Docs](https://www.backblaze.com/docs/cloud-storage)
- [Gemini API Docs](https://ai.google.dev/docs)

### Troubleshooting Externo
- [Railway Status](https://status.railway.app/)
- [Let's Encrypt Status](https://letsencrypt.status.io/)
- [DNS Checker](https://dnschecker.org/)

---

## 🎯 Checklist de Deploy

### Pre-Deploy
- [ ] Code en GitHub (repositorio privado)
- [ ] `.env` en `.gitignore`
- [ ] `Dockerfile` correcto
- [ ] `LOLA_FLASH.md` en raíz
- [ ] PostgreSQL en Neon configurado
- [ ] Backblaze B2 bucket creado
- [ ] Gemini API Key obtenida

### Deploy Railway
- [ ] Proyecto Railway creado
- [ ] GitHub repo conectado
- [ ] Variables de entorno configuradas
- [ ] Redis añadido y conectado
- [ ] Build exitoso
- [ ] Health check funciona

### Dominio Personalizado
- [ ] IP de Railway obtenida
- [ ] DNS configurado en 123REG (registro A)
- [ ] DNS propagado (verificado con `dig`)
- [ ] Dominio añadido en Railway
- [ ] SSL activo (Let's Encrypt)
- [ ] HTTPS funciona correctamente

### Verificación Final
- [ ] Logs sin errores
- [ ] PostgreSQL conectado
- [ ] Redis conectado
- [ ] Backblaze B2 accesible
- [ ] Gemini AI funcional
- [ ] Health check: `200 OK`
- [ ] Dominio personalizado funciona
- [ ] SSL/HTTPS activo

---

**Creado:** 09-Dic-2025  
**Última actualización:** 09-Dic-2025  
**Versión:** 1.0  
**Autor:** Guus + Gemini CLI (Antigravity)
