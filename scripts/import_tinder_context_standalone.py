#!/usr/bin/env python3
"""
Import Tinder Context - Lola Bot (Standalone Version)
Parsea conversaciones de Tinder en formato natural y las inserta en PostgreSQL
No requiere dependencias del proyecto - funciona de manera independiente
"""

import sys
import re
import asyncio
import os
import json
from datetime import datetime, timezone

try:
    import asyncpg
except ImportError:
    print("❌ Error: asyncpg no está instalado")
    print("Instala con: pip install asyncpg")
    sys.exit(1)


class TinderContextImporter:
    """Importa contexto de Tinder desde texto natural a la base de datos"""
    
    def __init__(self):
        # Obtener credenciales desde variables de entorno o usar defaults
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:Stafems@localhost:5432/maria_bot')
    
    def parse_tinder_text(self, text: str) -> dict:
        """
        Parsea texto en formato natural a estructura de datos
        
        Formato esperado:
        === CONTEXTO TINDER: Nombre ===
        USER_ID: 999
        
        [Usuario]: mensaje
        [Lola]: respuesta
        
        === FIN CONTEXTO ===
        """
        result = {
            "user_name": None,
            "user_id": None,
            "messages": []
        }
        
        # Extraer nombre del usuario
        name_match = re.search(r'=== CONTEXTO TINDER: (.+?) ===', text)
        if name_match:
            result["user_name"] = name_match.group(1).strip()
        
        # Extraer USER_ID
        id_match = re.search(r'USER_ID:\s*(\d+)', text)
        if id_match:
            result["user_id"] = int(id_match.group(1))
        
        # Extraer mensajes
        # Patrón: [Nombre]: mensaje
        message_pattern = r'\[(.+?)\]:\s*(.+?)(?=\n\[|===|$)'
        matches = re.finditer(message_pattern, text, re.DOTALL)
        
        for match in matches:
            sender = match.group(1).strip()
            content = match.group(2).strip()
            
            # Determinar si es Lola o el usuario
            is_lola = sender.lower() == "lola"
            
            result["messages"].append({
                "sender": sender,
                "content": content,
                "is_bot": is_lola
            })
        
        return result
    
    async def import_to_database(self, parsed_data: dict) -> str:
        """
        Importa datos parseados a la base de datos
        
        Returns:
            conversation_id (UUID string)
        """
        if not parsed_data["user_id"]:
            raise ValueError("USER_ID no encontrado en el texto")
        
        if not parsed_data["messages"]:
            raise ValueError("No se encontraron mensajes para importar")
        
        user_id = parsed_data["user_id"]
        user_name = parsed_data["user_name"] or "Usuario"
        
        # Conectar a la base de datos
        conn = await asyncpg.connect(self.db_url)
        
        try:
            # 1. Crear o actualizar usuario
            await conn.execute("""
                INSERT INTO users (user_id, username, first_name, created_at, updated_at, last_activity)
                VALUES ($1, $2, $3, NOW(), NOW(), NOW())
                ON CONFLICT (user_id) DO UPDATE 
                SET username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    updated_at = NOW(),
                    last_activity = NOW()
            """, user_id, user_name.lower(), user_name)
            
            # 2. Crear nueva conversación
            conversation_id = await conn.fetchval("""
                INSERT INTO conversations (user_id, state, context, started_at, updated_at)
                VALUES ($1, 'INITIAL', $2, NOW(), NOW())
                RETURNING conversation_id
            """, user_id, json.dumps({
                "tinder_history": parsed_data["messages"],
                "tinder_metadata": {
                    "imported_at": datetime.now(timezone.utc).isoformat(),
                    "user_name": user_name,
                    "message_count": len(parsed_data["messages"])
                }
            }))
            
            # 3. Insertar mensajes en tabla messages
            for msg in parsed_data["messages"]:
                await conn.execute("""
                    INSERT INTO messages (
                        user_id, 
                        conversation_id, 
                        message, 
                        is_bot, 
                        message_type, 
                        metadata,
                        created_at
                    )
                    VALUES ($1, $2, $3, $4, 'text', $5, NOW())
                """, user_id, conversation_id, msg["content"], msg["is_bot"], json.dumps({
                    "source": "tinder_import",
                    "sender_name": msg["sender"]
                }))
            
            # 4. Log en audit_log
            await conn.execute("""
                INSERT INTO audit_log (user_id, event_type, event_data, created_at)
                VALUES ($1, 'tinder_import', $2, NOW())
            """, user_id, json.dumps({
                "conversation_id": str(conversation_id),
                "messages_imported": len(parsed_data["messages"]),
                "user_name": user_name
            }))
            
            return str(conversation_id)
            
        finally:
            await conn.close()

    async def process_file(self, file_path: str) -> dict:
        """Procesa un archivo de texto con contexto de Tinder"""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        parsed = self.parse_tinder_text(text)
        conversation_id = await self.import_to_database(parsed)
        
        return {
            "success": True,
            "user_id": parsed["user_id"],
            "user_name": parsed["user_name"],
            "conversation_id": conversation_id,
            "messages_imported": len(parsed["messages"])
        }


async def main():
    """Punto de entrada principal"""
    if len(sys.argv) < 2:
        print("Uso: python import_tinder_context_standalone.py <archivo_texto.txt>")
        print("\nO usa modo interactivo:")
        print("python import_tinder_context_standalone.py --interactive")
        sys.exit(1)
    
    try:
        importer = TinderContextImporter()
        
        if sys.argv[1] == "--interactive":
            # Modo interactivo: pega el texto directamente
            print("=== MODO INTERACTIVO ===")
            print("Pega el texto de la conversación de Tinder.")
            print("Cuando termines, escribe una línea con solo: FIN")
            print()
            
            lines = []
            while True:
                line = input()
                if line.strip() == "FIN":
                    break
                lines.append(line)
            
            text = "\n".join(lines)
            parsed = importer.parse_tinder_text(text)
            conversation_id = await importer.import_to_database(parsed)
            
            print(f"\n✅ Importación exitosa!")
            print(f"   User ID: {parsed['user_id']}")
            print(f"   Nombre: {parsed['user_name']}")
            print(f"   Conversation ID: {conversation_id}")
            print(f"   Mensajes: {len(parsed['messages'])}")
            
        else:
            # Modo archivo
            file_path = sys.argv[1]
            result = await importer.process_file(file_path)
            
            print(f"\n✅ Importación exitosa!")
            print(f"   User ID: {result['user_id']}")
            print(f"   Nombre: {result['user_name']}")
            print(f"   Conversation ID: {result['conversation_id']}")
            print(f"   Mensajes: {result['messages_imported']}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
