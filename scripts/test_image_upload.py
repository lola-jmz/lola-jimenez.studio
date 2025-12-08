#!/usr/bin/env python3
"""
test_image_upload.py

Script para probar el envío de imágenes al WebSocket
"""

import asyncio
import websockets
import json
import base64
from pathlib import Path

async def test_image_upload():
    """Prueba el envío de una imagen de prueba al WebSocket"""
    
    # Crear una imagen de prueba simple (1x1 pixel PNG transparente)
    # Esto es solo para testing
    test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    
    uri = "ws://localhost:8000/ws/test-user-123"
    
    try:
        print(f"🔗 Conectando a {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✅ Conectado")
            
            # Recibir mensaje de bienvenida
            welcome = await websocket.recv()
            print(f"📩 Mensaje de bienvenida: {welcome}")
            
            # Test 1: Enviar mensaje de texto
            print("\n📝 Test 1: Enviando mensaje de texto...")
            text_message = {
                "type": "text",
                "content": "hola"
            }
            await websocket.send(json.dumps(text_message))
            response = await websocket.recv()
            print(f"📤 Respuesta: {json.loads(response)['content']}")
            
            # Test 2: Enviar imagen
            print("\n🖼️  Test 2: Enviando imagen de prueba...")
            image_message = {
                "type": "image",
                "content": test_image_base64
            }
            await websocket.send(json.dumps(image_message))
            
            # Recibir mensaje de "validando..."
            validating = await websocket.recv()
            print(f"⏳ {json.loads(validating)['content']}")
            
            # Recibir resultado de validación
            result = await websocket.recv()
            print(f"✅ Resultado: {json.loads(result)['content']}")
            
            print("\n🎉 Tests completados exitosamente!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n⚠️  Asegúrate de que el servidor esté corriendo:")
        print("   cd api")
        print("   python run_fastapi_basic.py")

if __name__ == "__main__":
    asyncio.run(test_image_upload())
