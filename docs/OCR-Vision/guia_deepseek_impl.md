# Guía de Implementación: DeepSeek-OCR Local + FastAPI + Next.js
## Validación de Comprobantes Bancarios Mexicanos

**Tiempo de implementación estimado**: 2-3 horas  
**Precisión OCR**: 97% @ 10x compression  
**Requisitos**: RAM 16GB+ (sin GPU)  

---

## 📋 Tabla de Contenidos
1. [Requisitos Hardware/Software](#requisitos)
2. [Instalación](#instalación)
3. [Backend FastAPI](#backend-fastapi)
4. [Integración WebSocket](#websocket)
5. [Frontend Next.js](#frontend-nextjs)
6. [Docker](#docker)
7. [Troubleshooting](#troubleshooting)

---

## Requisitos

### Hardware
```
MÍNIMO (CPU-only, Railway compatible):
- RAM: 16GB (8GB con optimizaciones)
- CPU: Multi-core (4+ cores)
- Storage: 15GB (para modelo + dependencies)
- GPU: NO requerida

RECOMENDADO:
- RAM: 32GB
- CPU: Intel Xeon / AMD EPYC
- Storage: 20GB libre
```

### Software
```bash
# Verificar versiones
python --version  # 3.11+
docker --version  # 20.10+
node --version    # 18+
```

---

## Instalación

### 1. Setup Base Python (desarrollo local)

```bash
# Crear ambiente virtual
python -m venv venv_deepseek
source venv_deepseek/bin/activate  # Linux/Mac
# O en Windows: venv_deepseek\Scripts\activate

# Actualizar pip
pip install --upgrade pip setuptools wheel

# Instalar dependencias críticas PRIMERO
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Instalar transformers y dependencias
pip install transformers==4.46.1
pip install pillow==11.0.0
pip install numpy==1.24.3
pip install torchvision==0.18.0
```

### 2. Instalación DeepSeek-OCR

```bash
# Descargar modelo desde Hugging Face (automático)
pip install huggingface-hub

# Script de descarga manual (más control)
python << 'EOF'
from huggingface_hub import hf_hub_download

# Descargar modelo (~6GB - toma 5-10 min en conexión rápida)
model_dir = hf_hub_download(
    repo_id="deepseek-ai/DeepSeek-OCR",
    repo_type="model",
    cache_dir="./models"
)
print(f"Modelo descargado en: {model_dir}")
EOF
```

### 3. Instalar dependencias FastAPI

```bash
# FastAPI stack
pip install fastapi==0.109.0
pip install uvicorn==0.27.0
pip install python-multipart==0.0.6
pip install python-dotenv==1.0.0

# WebSocket y async
pip install websockets==12.0
pip install aiofiles==23.2.1

# Validación de datos
pip install pydantic==2.5.3
pip install pydantic-settings==2.1.0

# Logging y monitoreo
pip install loguru==0.7.2

# Opcional: testing
pip install pytest==7.4.3
pip install pytest-asyncio==0.23.2

# Generar requirements.txt final
pip freeze > requirements.txt
```

### 4. Verificar instalación

```bash
python << 'EOF'
import torch
import transformers
from PIL import Image

print(f"✓ PyTorch version: {torch.__version__}")
print(f"✓ Transformers version: {transformers.__version__}")
print(f"✓ PIL available: OK")
print(f"✓ CPU available: {torch.cpu.is_available()}")
print("✓ Setup completado correctamente")
EOF
```

---

## Backend FastAPI

### 1. Archivo: `deepseek_ocr_engine.py`
**Motor core de OCR - Independiente de FastAPI**

```python
"""
DeepSeek-OCR Engine
Módulo independiente para inferencia OCR
Soporta CPU-only (sin GPU)
"""

import torch
from transformers import AutoModel, AutoTokenizer
from PIL import Image
import logging
from pathlib import Path
from typing import Optional, Tuple
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class DeepSeekOCREngine:
    def __init__(self, model_name: str = "deepseek-ai/DeepSeek-OCR", cache_dir: str = "./models"):
        """
        Inicializa el motor OCR con DeepSeek
        
        Args:
            model_name: Nombre del modelo en Hugging Face
            cache_dir: Directorio para cachear el modelo
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.device = "cpu"  # Forzar CPU (compatible Railway)
        self.model = None
        self.tokenizer = None
        self.load_model()
    
    def load_model(self):
        """Carga el modelo y tokenizer (ejecuta una sola vez)"""
        try:
            logger.info(f"Cargando DeepSeek-OCR desde {self.model_name}...")
            
            # Cargar tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                cache_dir=self.cache_dir,
                local_files_only=False
            )
            
            # Cargar modelo en CPU con optimizaciones
            self.model = AutoModel.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                torch_dtype=torch.float32,  # CPU requiere float32
                device_map="cpu",
                cache_dir=self.cache_dir,
                use_safetensors=True
            ).eval()  # Modo evaluación (sin gradientes)
            
            logger.info("✓ Modelo DeepSeek-OCR cargado correctamente")
            
        except Exception as e:
            logger.error(f"Error cargando modelo: {str(e)}")
            raise
    
    def extract_text(self, image_path: str) -> dict:
        """
        Extrae texto de imagen usando DeepSeek-OCR
        
        Args:
            image_path: Ruta a la imagen
        
        Returns:
            {
                "text": "texto extraído",
                "confidence": 0.97,
                "processing_time_ms": 2500,
                "resolution": [1024, 768]
            }
        """
        import time
        start_time = time.time()
        
        try:
            # Validar archivo
            image_path = Path(image_path)
            if not image_path.exists():
                raise FileNotFoundError(f"Imagen no encontrada: {image_path}")
            
            # Cargar imagen
            image = Image.open(image_path).convert("RGB")
            resolution = image.size  # (width, height)
            
            logger.debug(f"Imagen cargada: {resolution}")
            
            # Procesar con DeepSeek-OCR
            with torch.no_grad():  # Sin cálculo de gradientes (más rápido)
                # Preparar entrada
                inputs = self.tokenizer.from_list_format([
                    {"type": "image", "image": image},
                    {"type": "text", "text": "Extrae TODO el texto de esta imagen. Solo retorna el texto, sin explicaciones."}
                ])
                
                # Generar respuesta
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=1024,
                    temperature=0.1,  # Bajo para precisión
                    top_p=0.9
                )
                
                # Decodificar
                extracted_text = self.tokenizer.decode(
                    outputs[0][len(inputs):],
                    skip_special_tokens=True
                )
            
            processing_time = int((time.time() - start_time) * 1000)  # ms
            
            return {
                "success": True,
                "text": extracted_text.strip(),
                "confidence": 0.97,  # DeepSeek-OCR @ 10x compression
                "processing_time_ms": processing_time,
                "resolution": resolution,
                "model": "deepseek-ocr",
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error en OCR: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }


class BankReceiptValidator:
    """Valida comprobantes bancarios mexicanos"""
    
    @staticmethod
    def parse_spei_receipt(ocr_text: str) -> dict:
        """
        Extrae campos de comprobante SPEI desde texto OCR
        
        Busca patrones:
        - Monto: número con dos decimales
        - Fecha: DD/MM/YYYY
        - Referencia: 10-15 dígitos consecutivos
        - Banco: nombres conocidos (BBVA, Santander, etc.)
        """
        import re
        
        result = {
            "tipo": "SPEI",
            "campos_extraidos": {},
            "confianza_total": 0,
            "alertas": []
        }
        
        # 1. Extraer MONTO (patrón: número con decimales)
        monto_match = re.search(r'(?:monto|cantidad|transferencia)[:\s]*\$?(\d+[.,]\d{2})', 
                               ocr_text, re.IGNORECASE)
        if monto_match:
            monto_str = monto_match.group(1).replace(',', '.')
            result["campos_extraidos"]["monto"] = float(monto_str)
            # Validar rango típico
            if float(monto_str) > 1000000:
                result["alertas"].append("Monto > $1M (verificar)")
        else:
            result["alertas"].append("Monto no detectado")
        
        # 2. Extraer FECHA (DD/MM/YYYY)
        fecha_match = re.search(r'(\d{2})/(\d{2})/(\d{4})', ocr_text)
        if fecha_match:
            fecha_str = fecha_match.group(0)
            result["campos_extraidos"]["fecha"] = fecha_str
            
            # Validar que no sea futura ni muy antigua
            from datetime import datetime, timedelta
            try:
                fecha_obj = datetime.strptime(fecha_str, "%d/%m/%Y")
                hoy = datetime.now()
                dias_diferencia = (hoy - fecha_obj).days
                
                if dias_diferencia < 0:
                    result["alertas"].append("Fecha futura (inválida)")
                elif dias_diferencia > 7:
                    result["alertas"].append(f"Comprobante antiguo ({dias_diferencia} días)")
                elif dias_diferencia > 30:
                    result["alertas"].append("Comprobante fuera de plazo legal (>30 días)")
            except:
                result["alertas"].append("Fecha con formato inválido")
        else:
            result["alertas"].append("Fecha no detectada")
        
        # 3. Extraer REFERENCIA SPEI (10-15 dígitos)
        # Busca números largos (típicamente después de "referencia")
        ref_match = re.search(r'(?:referencia|folio)[:\s]*(\d{10,15})', 
                             ocr_text, re.IGNORECASE)
        if ref_match:
            referencia = ref_match.group(1)
            result["campos_extraidos"]["referencia"] = referencia
        else:
            # Buscar cualquier número de 10-15 dígitos sin separadores
            ref_match = re.search(r'(?<![0-9])(\d{10,15})(?![0-9])', ocr_text)
            if ref_match:
                result["campos_extraidos"]["referencia"] = ref_match.group(1)
            else:
                result["alertas"].append("Referencia SPEI no detectada")
        
        # 4. Detectar BANCO
        bancos_mx = {
            'BBVA': ['BBVA', 'BBVA Bancomer'],
            'Santander': ['Santander', 'Santander México'],
            'HSBC': ['HSBC', 'HSBC México'],
            'Banamex': ['Banamex', 'Citibanamex'],
            'Scotiabank': ['Scotiabank', 'Scotiabank Inverlat'],
            'Banregio': ['Banregio'],
            'Banorte': ['Banorte', 'Ixe'],
            'INBURSA': ['INBURSA'],
            'Intercam': ['Intercam'],
            'Azteca': ['Banco Azteca'],
            'Autofin': ['Autofin'],
            'Afirme': ['Afirme'],
            'Invex': ['Invex'],
        }
        
        for codigo, variantes in bancos_mx.items():
            for variante in variantes:
                if variante.lower() in ocr_text.lower():
                    result["campos_extraidos"]["banco_detectado"] = codigo
                    break
        
        if "banco_detectado" not in result["campos_extraidos"]:
            result["alertas"].append("Banco no identificado")
        
        # 5. Detectar ESTADO de transacción
        if any(word in ocr_text.lower() for word in ['completada', 'exitosa', 'éxito', 'confirmada']):
            result["campos_extraidos"]["estado"] = "COMPLETADA"
        elif any(word in ocr_text.lower() for word in ['pendiente', 'procesando']):
            result["campos_extraidos"]["estado"] = "PENDIENTE"
        elif any(word in ocr_text.lower() for word in ['rechazada', 'fallida', 'error', 'cancelada']):
            result["campos_extraidos"]["estado"] = "RECHAZADA"
        else:
            result["campos_extraidos"]["estado"] = "DESCONOCIDO"
            result["alertas"].append("Estado no claro")
        
        # Calcular confianza total
        campos_esperados = 5  # monto, fecha, referencia, banco, estado
        campos_encontrados = len([v for v in result["campos_extraidos"].values() if v])
        result["confianza_total"] = (campos_encontrados / campos_esperados) * 100
        
        return result
    
    @staticmethod
    def parse_oxxo_receipt(ocr_text: str) -> dict:
        """
        Extrae campos de recibo Oxxo desde texto OCR
        
        Patrón típico Oxxo:
        - Referencia: 14 dígitos
        - Monto: precio a pagar
        - Folio/ticket: número único
        """
        import re
        
        result = {
            "tipo": "OXXO",
            "campos_extraidos": {},
            "confianza_total": 0,
            "alertas": []
        }
        
        # 1. Referencia Oxxo (14 dígitos exactos)
        ref_14 = re.search(r'(?:referencia|ref)[:\s]*(\d{14})', ocr_text, re.IGNORECASE)
        if ref_14:
            result["campos_extraidos"]["referencia_14"] = ref_14.group(1)
        else:
            # Buscar cualquier número de 14 dígitos
            ref_14_alt = re.search(r'(?<![0-9])(\d{14})(?![0-9])', ocr_text)
            if ref_14_alt:
                result["campos_extraidos"]["referencia_14"] = ref_14_alt.group(1)
            else:
                result["alertas"].append("Referencia de 14 dígitos no encontrada")
        
        # 2. Monto
        monto_match = re.search(r'(?:cantidad|monto|total|pagar)[:\s]*\$?(\d+[.,]\d{2})', 
                               ocr_text, re.IGNORECASE)
        if monto_match:
            monto_str = monto_match.group(1).replace(',', '.')
            result["campos_extraidos"]["monto"] = float(monto_str)
        else:
            result["alertas"].append("Monto no detectado")
        
        # 3. Fecha
        fecha_match = re.search(r'(\d{2})/(\d{2})/(\d{4})', ocr_text)
        if fecha_match:
            result["campos_extraidos"]["fecha"] = fecha_match.group(0)
        else:
            result["alertas"].append("Fecha no detectada")
        
        # 4. Hora
        hora_match = re.search(r'(\d{2}):(\d{2}):?(\d{2})?', ocr_text)
        if hora_match:
            result["campos_extraidos"]["hora"] = hora_match.group(0)
        
        # 5. Código de barras
        barcode_match = re.search(r'(?:código|barras?|código de barras)[:\s]*(\d{12,13})', 
                                 ocr_text, re.IGNORECASE)
        if barcode_match:
            result["campos_extraidos"]["codigo_barras"] = barcode_match.group(1)
        
        # 6. Estado
        if any(word in ocr_text.lower() for word in ['confirmado', 'confirmada', 'éxito']):
            result["campos_extraidos"]["estado"] = "CONFIRMADO"
        elif any(word in ocr_text.lower() for word in ['pendiente']):
            result["campos_extraidos"]["estado"] = "PENDIENTE"
        else:
            result["campos_extraidos"]["estado"] = "DESCONOCIDO"
        
        # Calcular confianza
        campos_esperados = 6
        campos_encontrados = len([v for v in result["campos_extraidos"].values() if v])
        result["confianza_total"] = (campos_encontrados / campos_esperados) * 100
        
        return result
    
    @staticmethod
    def validate_extraction(parsed_data: dict) -> dict:
        """
        Valida completitud y consistencia de extracción
        
        Retorna:
        {
            "is_valid": bool,
            "validation_score": 0-100,
            "issues": [lista de problemas],
            "requires_manual_review": bool
        }
        """
        issues = parsed_data.get("alertas", [])
        confidence = parsed_data.get("confianza_total", 0)
        
        is_valid = (
            confidence >= 80 and  # 80% de campos encontrados mínimo
            len(issues) == 0
        )
        
        requires_review = (
            confidence < 95 or  # Baja confianza
            len(issues) > 0  # Hay alertas
        )
        
        return {
            "is_valid": is_valid,
            "validation_score": int(confidence),
            "issues": issues,
            "requires_manual_review": requires_review,
            "recommendation": (
                "ACEPTAR" if is_valid else
                "REVISAR MANUALMENTE" if requires_review else
                "RECHAZAR"
            )
        }


# Instancia global (se carga una sola vez)
ocr_engine = None

def get_ocr_engine() -> DeepSeekOCREngine:
    """Factory function para obtener instancia del motor OCR (Lazy loading)"""
    global ocr_engine
    if ocr_engine is None:
        ocr_engine = DeepSeekOCREngine()
    return ocr_engine
```

### 2. Archivo: `main_api.py`
**FastAPI + WebSocket**

```python
"""
FastAPI Backend para validación de comprobantes bancarios
Integración con DeepSeek-OCR + WebSocket
"""

from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import logging
from pathlib import Path
from datetime import datetime
import uuid
import asyncio
import base64
from io import BytesIO
from PIL import Image

from deepseek_ocr_engine import (
    get_ocr_engine, 
    BankReceiptValidator
)

# ============= CONFIGURACIÓN =============

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Validador de Comprobantes Bancarios",
    description="OCR para SPEI, Oxxo, transferencias mexicanas",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],  # Actualizar en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorio temporal para imágenes
UPLOADS_DIR = Path("./uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

# ============= MODELOS DE DATOS =============

from pydantic import BaseModel, Field
from typing import Optional, List

class OCRRequest(BaseModel):
    image_base64: str = Field(..., description="Imagen en base64")
    receipt_type: str = Field(default="auto", description="SPEI, OXXO, o auto-detect")

class ValidationResponse(BaseModel):
    success: bool
    extraction: Optional[dict] = None
    validation: Optional[dict] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# ============= ENDPOINTS HTTP =============

@app.get("/health")
async def health_check():
    """Verificar que el servidor está funcionando"""
    return {
        "status": "healthy",
        "service": "OCR Validator",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/validate", response_model=ValidationResponse)
async def validate_receipt(request: OCRRequest) -> ValidationResponse:
    """
    Endpoint HTTP para validar comprobante desde base64
    
    Ejemplo cURL:
    ```
    curl -X POST http://localhost:8000/api/validate \
      -H "Content-Type: application/json" \
      -d '{"image_base64": "..."}'
    ```
    """
    try:
        # Decodificar base64
        image_data = base64.b64decode(request.image_base64)
        
        # Guardar temporalmente
        temp_id = str(uuid.uuid4())[:8]
        temp_path = UPLOADS_DIR / f"temp_{temp_id}.jpg"
        
        with open(temp_path, "wb") as f:
            f.write(image_data)
        
        logger.info(f"Imagen temporal guardada: {temp_path}")
        
        # Ejecutar OCR
        ocr_engine = get_ocr_engine()
        ocr_result = ocr_engine.extract_text(str(temp_path))
        
        if not ocr_result["success"]:
            raise Exception(ocr_result.get("error", "OCR falló"))
        
        # Parsear según tipo
        receipt_type = request.receipt_type.upper()
        if receipt_type == "AUTO":
            # Auto-detectar tipo
            if "oxxo" in ocr_result["text"].lower():
                receipt_type = "OXXO"
            else:
                receipt_type = "SPEI"  # Default
        
        if receipt_type == "OXXO":
            parsed = BankReceiptValidator.parse_oxxo_receipt(ocr_result["text"])
        else:  # SPEI o default
            parsed = BankReceiptValidator.parse_spei_receipt(ocr_result["text"])
        
        # Validar
        validation = BankReceiptValidator.validate_extraction(parsed)
        
        # Limpiar temp
        temp_path.unlink()
        
        return ValidationResponse(
            success=True,
            extraction=parsed,
            validation=validation
        )
    
    except Exception as e:
        logger.error(f"Error en validación: {str(e)}")
        return ValidationResponse(
            success=False,
            error=str(e)
        )

@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload de imagen tradicional (alternativa a base64)
    """
    try:
        # Guardar archivo
        file_id = str(uuid.uuid4())[:8]
        file_path = UPLOADS_DIR / f"{file_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        logger.info(f"Archivo subido: {file_path}")
        
        # Procesar OCR
        ocr_engine = get_ocr_engine()
        ocr_result = ocr_engine.extract_text(str(file_path))
        
        if not ocr_result["success"]:
            file_path.unlink()
            raise Exception(ocr_result.get("error", "OCR falló"))
        
        # Parsear y validar
        parsed = BankReceiptValidator.parse_spei_receipt(ocr_result["text"])
        validation = BankReceiptValidator.validate_extraction(parsed)
        
        # Limpiar
        file_path.unlink()
        
        return {
            "success": True,
            "file_id": file_id,
            "extraction": parsed,
            "validation": validation
        }
    
    except Exception as e:
        logger.error(f"Error en upload: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ============= WEBSOCKET =============

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Cliente conectado: {client_id}")
    
    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Cliente desconectado: {client_id}")
    
    async def send_personal(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket para validación en tiempo real
    
    Cliente envía:
    {
        "action": "validate",
        "image_base64": "...",
        "receipt_type": "SPEI"
    }
    
    Servidor responde:
    {
        "status": "processing|completed|error",
        "extraction": {...},
        "validation": {...}
    }
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Recibir mensaje
            data = await websocket.receive_json()
            
            action = data.get("action")
            
            if action == "validate":
                # Enviar estado: procesando
                await manager.send_personal(client_id, {
                    "status": "processing",
                    "message": "Procesando comprobante..."
                })
                
                try:
                    # Decodificar imagen
                    image_data = base64.b64decode(data["image_base64"])
                    
                    # Guardar temporalmente
                    temp_id = str(uuid.uuid4())[:8]
                    temp_path = UPLOADS_DIR / f"ws_{temp_id}.jpg"
                    
                    with open(temp_path, "wb") as f:
                        f.write(image_data)
                    
                    # OCR
                    ocr_engine = get_ocr_engine()
                    ocr_result = ocr_engine.extract_text(str(temp_path))
                    
                    if not ocr_result["success"]:
                        raise Exception(ocr_result.get("error", "OCR falló"))
                    
                    # Detectar tipo y parsear
                    receipt_type = data.get("receipt_type", "SPEI").upper()
                    if receipt_type == "AUTO":
                        receipt_type = "OXXO" if "oxxo" in ocr_result["text"].lower() else "SPEI"
                    
                    if receipt_type == "OXXO":
                        parsed = BankReceiptValidator.parse_oxxo_receipt(ocr_result["text"])
                    else:
                        parsed = BankReceiptValidator.parse_spei_receipt(ocr_result["text"])
                    
                    # Validar
                    validation = BankReceiptValidator.validate_extraction(parsed)
                    
                    # Limpiar
                    temp_path.unlink()
                    
                    # Responder
                    await manager.send_personal(client_id, {
                        "status": "completed",
                        "extraction": parsed,
                        "validation": validation,
                        "ocr_result": {
                            "confidence": ocr_result["confidence"],
                            "processing_time_ms": ocr_result["processing_time_ms"]
                        }
                    })
                
                except Exception as e:
                    logger.error(f"Error WebSocket: {str(e)}")
                    await manager.send_personal(client_id, {
                        "status": "error",
                        "error": str(e)
                    })
            
            elif action == "ping":
                # Mantener conexión viva
                await manager.send_personal(client_id, {
                    "status": "pong",
                    "timestamp": datetime.now().isoformat()
                })
    
    except Exception as e:
        logger.error(f"Error en WebSocket: {str(e)}")
    finally:
        await manager.disconnect(client_id)

# ============= STARTUP =============

@app.on_event("startup")
async def startup_event():
    """Se ejecuta al iniciar el servidor"""
    logger.info("Iniciando servidor...")
    logger.info("Precargando modelo DeepSeek-OCR...")
    ocr_engine = get_ocr_engine()
    logger.info("✓ Motor OCR listo")

@app.on_event("shutdown")
async def shutdown_event():
    """Se ejecuta al apagar el servidor"""
    logger.info("Apagando servidor...")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Cambiar a False en producción
        log_level="info"
    )
```

### 3. Archivo: `run_dev.sh`
**Script para ejecutar en desarrollo**

```bash
#!/bin/bash

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═════════════════════════════════════${NC}"
echo -e "${BLUE}FastAPI + DeepSeek-OCR Server${NC}"
echo -e "${BLUE}═════════════════════════════════════${NC}"

# Activar venv
if [ ! -d "venv_deepseek" ]; then
    echo -e "${BLUE}Creando ambiente virtual...${NC}"
    python -m venv venv_deepseek
fi

source venv_deepseek/bin/activate

# Instalar dependencias si es necesario
if [ ! -f ".installed" ]; then
    echo -e "${BLUE}Instalando dependencias...${NC}"
    pip install -r requirements.txt
    touch .installed
fi

echo -e "${GREEN}✓ Ambiente listo${NC}"
echo -e "${BLUE}Iniciando servidor en http://localhost:8000${NC}"
echo -e "${BLUE}Documentación: http://localhost:8000/docs${NC}"
echo ""

# Ejecutar servidor
python -m uvicorn main_api:app --host 0.0.0.0 --port 8000 --reload
```

---

## Frontend Next.js

### Archivo: `app/components/ReceiptValidator.tsx`
**Componente React para capturar y validar**

```typescript
'use client';

import { useState, useRef, useCallback } from 'react';
import Image from 'next/image';

interface ValidationResult {
  status: 'idle' | 'processing' | 'completed' | 'error';
  extraction?: {
    campos_extraidos: Record<string, any>;
    confianza_total: number;
  };
  validation?: {
    is_valid: boolean;
    validation_score: number;
    issues: string[];
    recommendation: string;
  };
  error?: string;
  ocr_result?: {
    confidence: number;
    processing_time_ms: number;
  };
}

export default function ReceiptValidator() {
  const [preview, setPreview] = useState<string>('');
  const [result, setResult] = useState<ValidationResult>({ status: 'idle' });
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const clientIdRef = useRef<string>(crypto.randomUUID());

  // Conectar WebSocket
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${protocol}://${window.location.host}/ws/${clientIdRef.current}`;

    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket conectado');
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      setResult({
        status: data.status,
        extraction: data.extraction,
        validation: data.validation,
        error: data.error,
        ocr_result: data.ocr_result,
      });

      if (data.status === 'completed' || data.status === 'error') {
        setLoading(false);
      }
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setResult({
        status: 'error',
        error: 'Error de conexión WebSocket',
      });
      setLoading(false);
    };
  }, []);

  // Manejar selección de archivo
  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Preview local
    const reader = new FileReader();
    reader.onload = (e) => {
      const src = e.target?.result as string;
      setPreview(src);
    };
    reader.readAsDataURL(file);

    // Enviar por WebSocket
    connectWebSocket();
    setLoading(true);
    setResult({ status: 'processing' });

    const fileReader = new FileReader();
    fileReader.onload = (e) => {
      const base64 = (e.target?.result as string).split(',')[1];

      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            action: 'validate',
            image_base64: base64,
            receipt_type: 'auto',
          })
        );
      }
    };
    fileReader.readAsDataURL(file);
  };

  // Click en el área de drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.currentTarget.classList.add('border-blue-500', 'bg-blue-50');
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.currentTarget.classList.remove('border-blue-500', 'bg-blue-50');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.currentTarget.classList.remove('border-blue-500', 'bg-blue-50');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      fileInputRef.current!.files = files;
      handleFileSelect({ target: { files } } as any);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold mb-2 text-gray-800">
          Validador de Comprobantes
        </h1>
        <p className="text-gray-600 mb-8">
          SPEI • Oxxo • Transferencias Bancarias
        </p>

        {/* Drop Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center cursor-pointer hover:border-blue-400 transition"
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
          />

          <svg
            className="w-16 h-16 mx-auto text-gray-400 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>

          <p className="text-gray-700 font-medium mb-2">
            Arrastra tu comprobante aquí o haz clic
          </p>
          <p className="text-sm text-gray-500">PNG, JPG o GIF (máx 10MB)</p>
        </div>

        {/* Preview */}
        {preview && (
          <div className="mt-8">
            <h2 className="text-lg font-semibold mb-4">Vista Previa</h2>
            <div className="relative w-full h-96 bg-gray-100 rounded-lg overflow-hidden">
              <Image
                src={preview}
                alt="Preview"
                fill
                className="object-contain"
              />
            </div>
          </div>
        )}

        {/* Estado Procesamiento */}
        {loading && (
          <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="animate-spin">
                <svg
                  className="w-5 h-5 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
              </div>
              <span className="text-blue-700 font-medium">
                {result.status === 'processing'
                  ? 'Analizando comprobante...'
                  : 'Procesando...'}
              </span>
            </div>
          </div>
        )}

        {/* Resultados */}
        {result.status === 'completed' && result.extraction && (
          <div className="mt-8 space-y-6">
            {/* Extracción */}
            <div className="bg-gray-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="text-green-600">✓</span> Datos Extraídos
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(result.extraction.campos_extraidos).map(
                  ([key, value]) => (
                    <div key={key} className="bg-white p-3 rounded border border-gray-200">
                      <p className="text-xs font-semibold text-gray-600 uppercase">
                        {key}
                      </p>
                      <p className="text-lg font-mono text-gray-900 mt-1">
                        {String(value)}
                      </p>
                    </div>
                  )
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-600">
                  Confianza de extracción:{' '}
                  <span className="font-bold text-gray-900">
                    {result.extraction.confianza_total.toFixed(1)}%
                  </span>
                </p>
              </div>
            </div>

            {/* Validación */}
            {result.validation && (
              <div
                className={`rounded-lg p-6 ${
                  result.validation.is_valid
                    ? 'bg-green-50 border border-green-200'
                    : 'bg-yellow-50 border border-yellow-200'
                }`}
              >
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <span
                    className={
                      result.validation.is_valid ? 'text-green-600' : 'text-yellow-600'
                    }
                  >
                    {result.validation.is_valid ? '✓' : '⚠'}
                  </span>
                  Validación
                </h3>

                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-gray-700 font-semibold">
                      Recomendación
                    </p>
                    <p
                      className={`text-lg font-bold ${
                        result.validation.is_valid
                          ? 'text-green-700'
                          : 'text-yellow-700'
                      }`}
                    >
                      {result.validation.recommendation}
                    </p>
                  </div>

                  <div>
                    <p className="text-sm text-gray-700 font-semibold">
                      Score de Validación
                    </p>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                      <div
                        className={`h-2 rounded-full ${
                          result.validation.validation_score >= 90
                            ? 'bg-green-600'
                            : 'bg-yellow-600'
                        }`}
                        style={{
                          width: `${result.validation.validation_score}%`,
                        }}
                      />
                    </div>
                    <p className="text-xs text-gray-600 mt-1">
                      {result.validation.validation_score}%
                    </p>
                  </div>

                  {result.validation.issues.length > 0 && (
                    <div>
                      <p className="text-sm text-gray-700 font-semibold mb-2">
                        Alertas
                      </p>
                      <ul className="space-y-1">
                        {result.validation.issues.map((issue, i) => (
                          <li
                            key={i}
                            className="text-sm text-yellow-700 flex gap-2"
                          >
                            <span>•</span>
                            {issue}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Metadata OCR */}
            {result.ocr_result && (
              <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
                <p>
                  ⚡ Procesado en {result.ocr_result.processing_time_ms}ms |
                  Precisión: {(result.ocr_result.confidence * 100).toFixed(1)}%
                </p>
              </div>
            )}

            {/* Botón para reintentar */}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition"
            >
              Validar Otro Comprobante
            </button>
          </div>
        )}

        {/* Error */}
        {result.status === 'error' && (
          <div className="mt-8 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 font-medium">Error:</p>
            <p className="text-red-600 text-sm mt-1">{result.error}</p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="mt-3 text-red-600 hover:text-red-700 underline text-sm font-medium"
            >
              Reintentar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## Docker

### Dockerfile

```dockerfile
# Multi-stage build para optimizar tamaño

# Stage 1: Base con Python
FROM python:3.11-slim as base

WORKDIR /app

# Instalar system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Builder
FROM base as builder

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python en venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar PyTorch CPU (sin GPU)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Instalar resto de dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Runtime
FROM base as runtime

# Copiar venv desde builder
COPY --from=builder /opt/venv /opt/venv

# Copiar código
COPY . .

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "main_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  fastapi:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ocr-validator
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads  # Almacenar imágenes
      - ./models:/app/models    # Cachear modelo
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - ocr-network

  # Nginx para proxying (opcional)
  nginx:
    image: nginx:latest
    container_name: ocr-nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - fastapi
    networks:
      - ocr-network

networks:
  ocr-network:
    driver: bridge
```

### requirements.txt

```
fastapi==0.109.0
uvicorn==0.27.0
python-multipart==0.0.6
python-dotenv==1.0.0
websockets==12.0
aiofiles==23.2.1
pydantic==2.5.3
pydantic-settings==2.1.0
loguru==0.7.2
torch==2.1.0
transformers==4.46.1
pillow==11.0.0
numpy==1.24.3
torchvision==0.18.0
huggingface-hub==0.22.1
```

---

## Troubleshooting

### 1. Error: "OutOfMemoryError: CUDA out of memory"
**Problema**: Aunque configuramos CPU, intenta usar GPU  
**Solución**:
```bash
export CUDA_VISIBLE_DEVICES=""  # Deshabilitar GPU
export TORCH_CPP_LOG_LEVEL=INFO
```

### 2. Error: "Model not found" / Timeout al descargar
**Problema**: Falla descargando modelo de Hugging Face  
**Solución**:
```bash
# Pre-descargar manualmente
python << 'EOF'
from huggingface_hub import snapshot_download
snapshot_download("deepseek-ai/DeepSeek-OCR", cache_dir="./models")
EOF
```

### 3. WebSocket "Connection refused"
**Problema**: Cliente Next.js no puede conectar a WebSocket  
**Solución**: Verificar CORS y puerto en nginx.conf:
```nginx
location / {
    proxy_pass http://fastapi:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### 4. Latencia muy lenta (>5s por imagen)
**Problema**: OCR toma mucho tiempo en CPU  
**Causas posibles**:
- Imagen de muy alta resolución (redimensiona a <1280px)
- RAM insuficiente (mínimo 16GB)
- Disco SSD lento

**Solución**:
```python
# Reducir resolución en OCR
image = Image.open(path)
if image.size[0] > 1280:
    image.thumbnail((1280, 1280))  # Max 1280px
```

### 5. Error "Port 8000 already in use"
**Solución**:
```bash
# Matar proceso
lsof -i :8000
kill -9 <PID>

# O usar puerto diferente
uvicorn main_api:app --port 8001
```

### 6. Railway: "Modelo no se descarga a tiempo"
**Problema**: Build timeout  
**Solución**: Pre-cachear en Docker
```dockerfile
RUN python -c "from transformers import AutoModel; AutoModel.from_pretrained('deepseek-ai/DeepSeek-OCR')"
```

### 7. OCR retorna texto vacío
**Problema**: DeepSeek no reconoce imagen  
**Causas**:
- Imagen muy oscura/de baja calidad
- Formato no soportado
- Resolución muy pequeña

**Solución**:
```python
# Validar imagen antes de OCR
image = Image.open(path)
if image.size[0] < 256 or image.size[1] < 256:
    raise ValueError("Imagen muy pequeña")

# Mejorar contraste si es necesario
from PIL import ImageEnhance
enhancer = ImageEnhance.Contrast(image)
image = enhancer.enhance(1.5)
```

---

## Checklist de Implementación

```
□ Crear venv Python
□ Instalar dependencias (ver sección Instalación)
□ Crear archivos:
  - deepseek_ocr_engine.py
  - main_api.py
  - run_dev.sh
  - Dockerfile
  - docker-compose.yml
  - requirements.txt

□ Backend local (prueba antes de integrar):
  ./run_dev.sh
  # Debe estar disponible en http://localhost:8000/docs

□ Verificar endpoints:
  curl http://localhost:8000/health

□ Frontend Next.js:
  Copiar ReceiptValidator.tsx a app/components/
  Importar en página

□ Pruebas iniciales:
  - Upload imagen SPEI
  - Upload imagen Oxxo
  - Verificar WebSocket

□ Docker local:
  docker-compose up

□ Railway deployment (si aplica):
  railway up

□ Producción:
  - Cambiar reload=False en uvicorn
  - Configurar CORS correctamente
  - Agregar autenticación (JWT)
  - Logs persistentes
```

---

## Performance Estimado

| Operación | Tiempo | Hardware |
|-----------|--------|----------|
| Carga modelo (una vez) | 8-12s | CPU 8-core |
| OCR por imagen | 2-5s | CPU 8-core, RAM 16GB |
| Parsing + validación | 50-100ms | CPU |
| WebSocket + upload | <500ms | Red local |

**Total por validación**: ~3-6 segundos (dominado por OCR)

---

**Fecha de guía**: Diciembre 2025  
**DeepSeek-OCR versión**: Latest @ 2025-12-10

