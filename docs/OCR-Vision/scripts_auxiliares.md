# Scripts Auxiliares y Ejemplos Rápidos
## DeepSeek-OCR + FastAPI

---

## 1. Setup Rápido (CLI)

### setup.sh
```bash
#!/bin/bash

echo "🚀 Setup DeepSeek-OCR + FastAPI"

# 1. Crear venv
python3 -m venv venv_deepseek
source venv_deepseek/bin/activate

# 2. Actualizar pip
pip install --upgrade pip setuptools wheel

# 3. Instalar PyTorch CPU (crítico hacerlo primero)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 4. Instalar dependencias FastAPI
pip install fastapi uvicorn python-multipart pydantic python-dotenv websockets loguru

# 5. Instalar DeepSeek + transformers
pip install transformers pillow numpy huggingface-hub

# 6. Crear directorio models y descargar modelo
mkdir -p models

python << 'EOF'
from huggingface_hub import snapshot_download
import os

# Descargar modelo (este paso toma ~5-10 minutos)
print("📥 Descargando DeepSeek-OCR... (esto puede tomar un tiempo)")
snapshot_download(
    repo_id="deepseek-ai/DeepSeek-OCR",
    cache_dir="./models",
    local_files_only=False
)
print("✅ Modelo descargado correctamente")
EOF

# 7. Crear requirements.txt
pip freeze > requirements.txt

echo "✅ Setup completado"
echo "Para ejecutar: source venv_deepseek/bin/activate && uvicorn main_api:app --reload"
```

---

## 2. Test Script - Validar Setup

### test_installation.py
```python
#!/usr/bin/env python3
"""
Test script para verificar que todo está instalado correctamente
Ejecutar: python test_installation.py
"""

import sys
from pathlib import Path

def test_imports():
    """Verificar imports críticos"""
    print("📦 Verificando importes...")
    
    try:
        import torch
        print(f"  ✓ PyTorch {torch.__version__}")
    except ImportError as e:
        print(f"  ✗ PyTorch: {e}")
        return False
    
    try:
        import transformers
        print(f"  ✓ Transformers {transformers.__version__}")
    except ImportError as e:
        print(f"  ✗ Transformers: {e}")
        return False
    
    try:
        from PIL import Image
        print(f"  ✓ PIL (Pillow)")
    except ImportError as e:
        print(f"  ✗ PIL: {e}")
        return False
    
    try:
        import fastapi
        print(f"  ✓ FastAPI")
    except ImportError as e:
        print(f"  ✗ FastAPI: {e}")
        return False
    
    try:
        import websockets
        print(f"  ✓ WebSockets")
    except ImportError as e:
        print(f"  ✗ WebSockets: {e}")
        return False
    
    return True

def test_pytorch_cpu():
    """Verificar que PyTorch usa CPU"""
    print("\n🔧 Verificando PyTorch CPU...")
    import torch
    
    print(f"  CPU disponible: {torch.cpu.is_available()}")
    print(f"  CUDA disponible: {torch.cuda.is_available()}")
    print(f"  Device: {torch.device('cpu')}")
    
    return True

def test_model_loading():
    """Verificar que se puede cargar el modelo"""
    print("\n🤖 Verificando carga de modelo...")
    
    model_path = Path("./models")
    
    if not model_path.exists():
        print(f"  ⚠ Directorio models no existe")
        print(f"  Ejecuta: mkdir -p models")
        return False
    
    # Verificar si el modelo ya está descargado
    deepseek_model = model_path / "models--deepseek-ai--DeepSeek-OCR"
    if deepseek_model.exists():
        print(f"  ✓ Modelo encontrado en {deepseek_model}")
        return True
    else:
        print(f"  ⚠ Modelo no descargado aún")
        print(f"  Primera carga tomará ~5-10 minutos")
        print(f"  Se descargará automáticamente al ejecutar main_api.py")
        return True

def test_fastapi_imports():
    """Verificar imports específicos de FastAPI"""
    print("\n🌐 Verificando FastAPI específico...")
    
    try:
        from fastapi import FastAPI, WebSocket
        print("  ✓ FastAPI core imports")
    except ImportError as e:
        print(f"  ✗ FastAPI core: {e}")
        return False
    
    try:
        from pydantic import BaseModel
        print("  ✓ Pydantic models")
    except ImportError as e:
        print(f"  ✗ Pydantic: {e}")
        return False
    
    return True

def main():
    print("=" * 50)
    print("DeepSeek-OCR Installation Test")
    print("=" * 50)
    
    all_pass = True
    
    if not test_imports():
        all_pass = False
    
    if not test_pytorch_cpu():
        all_pass = False
    
    if not test_fastapi_imports():
        all_pass = False
    
    if not test_model_loading():
        all_pass = False
    
    print("\n" + "=" * 50)
    if all_pass:
        print("✅ Todo verificado correctamente")
        print("\nPuedes ejecutar:")
        print("  python -m uvicorn main_api:app --reload")
        print("\nDocumentación en: http://localhost:8000/docs")
        return 0
    else:
        print("❌ Hay problemas con la instalación")
        print("\nIntenta ejecutar nuevamente setup.sh")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## 3. CLI Testing

### test_ocr.py
```python
#!/usr/bin/env python3
"""
Script para testear OCR sin FastAPI
Útil para debugging local
"""

import sys
import argparse
from pathlib import Path
from deepseek_ocr_engine import DeepSeekOCREngine, BankReceiptValidator
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ocr(image_path: str):
    """Test OCR en una imagen"""
    path = Path(image_path)
    
    if not path.exists():
        print(f"❌ Archivo no encontrado: {image_path}")
        return 1
    
    print(f"📸 Procesando: {image_path}")
    print("=" * 50)
    
    # Cargar motor OCR
    print("⏳ Cargando DeepSeek-OCR...")
    engine = DeepSeekOCREngine()
    
    # Extraer texto
    print("🔍 Extrayendo texto...")
    result = engine.extract_text(str(path))
    
    if not result["success"]:
        print(f"❌ Error: {result.get('error')}")
        return 1
    
    print(f"✓ OCR completado en {result['processing_time_ms']}ms")
    print(f"✓ Confianza: {result['confidence']}")
    print(f"✓ Resolución: {result['resolution']}")
    print()
    
    # Mostrar texto extraído
    print("📝 TEXTO EXTRAÍDO:")
    print("-" * 50)
    print(result["text"])
    print("-" * 50)
    print()
    
    # Parsear comprobante
    print("🏦 ANÁLISIS DE COMPROBANTE:")
    print("-" * 50)
    
    # Auto-detectar tipo
    if "oxxo" in result["text"].lower():
        parsed = BankReceiptValidator.parse_oxxo_receipt(result["text"])
        print(f"Tipo: OXXO")
    else:
        parsed = BankReceiptValidator.parse_spei_receipt(result["text"])
        print(f"Tipo: SPEI")
    
    print(f"Confianza: {parsed['confianza_total']:.1f}%")
    print()
    print("Campos extraídos:")
    for key, value in parsed["campos_extraidos"].items():
        print(f"  • {key}: {value}")
    
    if parsed["alertas"]:
        print()
        print("⚠️  Alertas:")
        for alerta in parsed["alertas"]:
            print(f"  • {alerta}")
    
    # Validación
    validation = BankReceiptValidator.validate_extraction(parsed)
    print()
    print("✓ Validación:")
    print(f"  Score: {validation['validation_score']}%")
    print(f"  Válido: {'SÍ' if validation['is_valid'] else 'NO'}")
    print(f"  Recomendación: {validation['recommendation']}")
    print()
    
    return 0

def main():
    parser = argparse.ArgumentParser(
        description="Test OCR con DeepSeek-OCR"
    )
    parser.add_argument(
        "image",
        help="Ruta a la imagen del comprobante"
    )
    
    args = parser.parse_args()
    
    return test_ocr(args.image)

if __name__ == "__main__":
    sys.exit(main())
```

**Uso**:
```bash
python test_ocr.py ./comprobante.jpg
```

---

## 4. API Testing

### test_api.py
```python
#!/usr/bin/env python3
"""
Test HTTP API endpoints
Ejecutar después de iniciar FastAPI: python test_api.py
"""

import requests
import base64
import json
from pathlib import Path

API_URL = "http://localhost:8000"

def test_health():
    """Test endpoint health"""
    print("🏥 Testing /health...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_validate_http(image_path: str):
    """Test HTTP POST endpoint"""
    print(f"\n📮 Testing /api/validate con {image_path}...")
    
    path = Path(image_path)
    if not path.exists():
        print(f"  ❌ Archivo no encontrado: {image_path}")
        return False
    
    # Leer imagen como base64
    with open(path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()
    
    payload = {
        "image_base64": image_b64,
        "receipt_type": "auto"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/api/validate",
            json=payload,
            timeout=30
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Success: {result.get('success')}")
            
            if result.get('extraction'):
                print(f"  Confianza: {result['extraction'].get('confianza_total')}%")
                print(f"  Campos: {list(result['extraction'].get('campos_extraidos', {}).keys())}")
            
            if result.get('validation'):
                print(f"  Recomendación: {result['validation'].get('recommendation')}")
            
            return True
        else:
            print(f"  Error: {response.text}")
            return False
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_upload(image_path: str):
    """Test upload endpoint"""
    print(f"\n📤 Testing /api/upload con {image_path}...")
    
    path = Path(image_path)
    if not path.exists():
        print(f"  ❌ Archivo no encontrado: {image_path}")
        return False
    
    try:
        with open(path, "rb") as f:
            files = {"file": f}
            response = requests.post(
                f"{API_URL}/api/upload",
                files=files,
                timeout=30
            )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Success: {result.get('success')}")
            print(f"  File ID: {result.get('file_id')}")
            return True
        else:
            print(f"  Error: {response.text}")
            return False
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("=" * 50)
    print("FastAPI Endpoint Tests")
    print("=" * 50)
    print("\n⚠️  Asegúrate de que FastAPI está ejecutándose:")
    print("   python -m uvicorn main_api:app --reload")
    print()
    
    # Test health
    if not test_health():
        print("\n❌ No se puede conectar a FastAPI")
        print("   Inicia el servidor primero")
        return 1
    
    # Test con imagen de ejemplo
    test_image = Path("./test_image.jpg")
    
    if test_image.exists():
        test_validate_http(str(test_image))
        test_upload(str(test_image))
    else:
        print(f"\n⚠️  No hay imagen de prueba ({test_image})")
        print("   Crea una imagen de comprobante bancario para probar")
    
    print("\n✅ Tests completados")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
```

**Uso**:
```bash
python -m uvicorn main_api:app --reload &
python test_api.py
```

---

## 5. WebSocket Testing

### test_websocket.py
```python
#!/usr/bin/env python3
"""
Test WebSocket connection
"""

import asyncio
import base64
import json
from pathlib import Path
import websockets
import uuid

async def test_websocket(image_path: str):
    """Test WebSocket validation"""
    
    path = Path(image_path)
    if not path.exists():
        print(f"❌ Archivo no encontrado: {image_path}")
        return
    
    # Leer imagen como base64
    with open(path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()
    
    client_id = str(uuid.uuid4())[:8]
    uri = f"ws://localhost:8000/ws/{client_id}"
    
    print(f"🔌 Conectando a WebSocket: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Conectado")
            
            # Enviar validación
            print("📤 Enviando imagen para validación...")
            message = {
                "action": "validate",
                "image_base64": image_b64,
                "receipt_type": "auto"
            }
            
            await websocket.send(json.dumps(message))
            
            # Recibir respuestas
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                
                status = data.get("status")
                print(f"\n📨 Respuesta: {status}")
                
                if status == "processing":
                    print(f"   {data.get('message')}")
                
                elif status == "completed":
                    extraction = data.get("extraction", {})
                    validation = data.get("validation", {})
                    ocr = data.get("ocr_result", {})
                    
                    print(f"   Confianza: {extraction.get('confianza_total')}%")
                    print(f"   Score validación: {validation.get('validation_score')}%")
                    print(f"   Recomendación: {validation.get('recommendation')}")
                    print(f"   Tiempo OCR: {ocr.get('processing_time_ms')}ms")
                    break
                
                elif status == "error":
                    print(f"   ❌ Error: {data.get('error')}")
                    break
    
    except Exception as e:
        print(f"❌ Error WebSocket: {e}")

async def main():
    print("=" * 50)
    print("WebSocket Test")
    print("=" * 50)
    
    # Buscar imagen de test
    test_images = list(Path(".").glob("*.jpg")) + list(Path(".").glob("*.png"))
    
    if test_images:
        await test_websocket(str(test_images[0]))
    else:
        print("❌ No hay imágenes JPG/PNG en el directorio")

if __name__ == "__main__":
    asyncio.run(main())
```

**Uso**:
```bash
python test_websocket.py
```

---

## 6. Docker Quick Start

### docker-build.sh
```bash
#!/bin/bash

echo "🐳 Building Docker image..."

# Build
docker build -t deepseek-ocr:latest .

if [ $? -eq 0 ]; then
    echo "✅ Build exitoso"
    echo ""
    echo "Para ejecutar:"
    echo "  docker run -p 8000:8000 deepseek-ocr:latest"
    echo ""
    echo "O con docker-compose:"
    echo "  docker-compose up"
else
    echo "❌ Build falló"
    exit 1
fi
```

### docker-run.sh
```bash
#!/bin/bash

echo "🐳 Iniciando contenedor..."

docker run \
    --name ocr-validator \
    -p 8000:8000 \
    -v $(pwd)/uploads:/app/uploads \
    -v $(pwd)/models:/app/models \
    -e PYTHONUNBUFFERED=1 \
    deepseek-ocr:latest

echo ""
echo "Servidor disponible en: http://localhost:8000"
echo "Documentación: http://localhost:8000/docs"
```

---

## 7. Railway Deployment

### .env.production
```
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### railway.json
```json
{
  "build": {
    "builder": "dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn main_api:app --host 0.0.0.0 --port $PORT"
  }
}
```

### Deploy script
```bash
#!/bin/bash

echo "🚀 Deploying to Railway..."

# Requiere: railway CLI instalado
# Instalar: npm i -g @railway/cli

railway login
railway init
railway up

echo "✅ Deployment completado"
echo "URL: $(railway status)"
```

---

## 8. Monitoreo y Logs

### monitor.py
```python
#!/usr/bin/env python3
"""
Monitor de performance del servidor
"""

import subprocess
import json
import time
import requests
from datetime import datetime

API_URL = "http://localhost:8000"

def monitor_health():
    """Check health endpoint"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except:
        pass
    return {"status": "unhealthy"}

def monitor_process():
    """Check if process is running"""
    try:
        result = subprocess.run(
            ["lsof", "-i", ":8000"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True
    except:
        pass
    return False

def main():
    print("📊 Server Monitor")
    print("=" * 50)
    
    while True:
        print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
        
        # Check process
        if monitor_process():
            print("✓ FastAPI process running")
        else:
            print("❌ FastAPI process NOT running")
        
        # Check health
        health = monitor_health()
        print(f"✓ Health: {health['status']}")
        
        time.sleep(10)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMonitor detenido")
```

---

## Quick Reference

```bash
# Setup completo (primera vez)
./setup.sh

# Verificar instalación
python test_installation.py

# Ejecutar servidor en desarrollo
source venv_deepseek/bin/activate
uvicorn main_api:app --reload

# Testear OCR local
python test_ocr.py ./comprobante.jpg

# Testear API HTTP
python test_api.py

# Testear WebSocket
python test_websocket.py

# Docker
docker-compose up

# Monitor de servidor
python monitor.py

# Limpiar ambiente
rm -rf venv_deepseek uploads/ models/
```

**Fecha**: Diciembre 2025

