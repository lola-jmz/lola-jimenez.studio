# IMPORTAR CONTEXTO DE TINDER - Lola Bot

## 🎯 Propósito

Este documento explica cómo importar conversaciones de Tinder a la base de datos de Lola Bot para que el bot tenga contexto previo de los usuarios.

## 📋 Formato de Texto Natural

Cuando Guus pegue texto de conversación de Tinder, debe seguir este formato:

```
=== CONTEXTO TINDER: NombreUsuario ===
USER_ID: 999

[NombreUsuario]: primer mensaje del usuario
[Lola]: respuesta de lola
[NombreUsuario]: siguiente mensaje
[Lola]: otra respuesta

=== FIN CONTEXTO ===
```

### Reglas del Formato

1. **Cabecera obligatoria:** `=== CONTEXTO TINDER: NombreUsuario ===`
2. **USER_ID obligatorio:** `USER_ID: 999` (número entero)
3. **Mensajes:** Formato `[Emisor]: contenido`
   - `[Lola]` para mensajes del bot
   - `[NombreUsuario]` para mensajes del usuario
4. **Pie obligatorio:** `=== FIN CONTEXTO ===`

## 🚀 Uso del Script

### Opción 1: Modo Interactivo (Recomendado)

```bash
cd /home/gusta/Projects/Negocios/Stafems/lola_bot
source venv/bin/activate
python scripts/import_tinder_context.py --interactive
```

**Flujo:**
1. Se abre el prompt interactivo
2. Pega el texto de la conversación
3. Escribe `FIN` cuando termines
4. El script procesa e importa automáticamente

### Opción 2: Desde Archivo

Si el texto está en un archivo `.txt`:

```bash
cd /home/gusta/Projects/Negocios/Stafems/lola_bot
source venv/bin/activate
python scripts/import_tinder_context.py ruta/al/archivo.txt
```

## 📊 Qué Hace el Script

1. **Parsea el texto natural:**
   - Extrae USER_ID
   - Extrae nombre del usuario
   - Identifica cada mensaje y su emisor

2. **Inserta en la base de datos:**
   - Crea/actualiza usuario en tabla `users`
   - Crea nueva conversación en tabla `conversations`
   - Guarda contexto en campo JSONB `conversations.context`
   - Inserta todos los mensajes en tabla `messages` con metadata `source: "tinder_import"`
   - Registra evento en `audit_log`

3. **Retorna confirmación:**
   - User ID
   - Nombre
   - Conversation ID (UUID)
   - Cantidad de mensajes importados

## 🔧 Integración con Core Handler

Una vez importado, el `CoreHandler` debe:

1. Al recibir primer mensaje del usuario:
   ```python
   conversation = await get_conversation(user_id)
   tinder_history = conversation.context.get("tinder_history", [])
   ```

2. Cargar contexto previo:
   ```python
   if tinder_history:
       # Resumir o usar directamente en prompt de Gemini
       context_summary = f"Conversación previa en Tinder: {len(tinder_history)} mensajes"
   ```

3. Responder con contexto:
   - Lola ya "conoce" al usuario
   - No repite preguntas ya hechas en Tinder
   - Continúa conversación naturalmente

## 📝 Ejemplo Completo

**Input (texto que Guus pega):**

```
=== CONTEXTO TINDER: Juanito ===
USER_ID: 999

[Juanito]: hola linda como estas
[Lola]: holaa bien y tu
[Juanito]: todo bien. que haces
[Lola]: aqui en la uni estudiando
[Juanito]: ah que estudias
[Lola]: negocios digitales

=== FIN CONTEXTO ===
```

**Output (confirmación del script):**

```
✅ Importación exitosa!
   User ID: 999
   Nombre: Juanito
   Conversation ID: 550e8400-e29b-41d4-a716-446655440000
   Mensajes: 6
```

**Resultado en BD:**

- **users:** `user_id=999, username=juanito, first_name=Juanito`
- **conversations:** `conversation_id=uuid, user_id=999, context={tinder_history: [...]}`
- **messages:** 6 registros con `metadata.source="tinder_import"`
- **audit_log:** Evento `tinder_import` registrado

## ⚠️ Notas Importantes

### Para Claude Desktop (Futuras Conversaciones)

Cuando Guus te pida importar contexto de Tinder:

1. **Verifica el formato** del texto que pegó
2. **Valida** que tenga USER_ID y mensajes
3. **Ejecuta** el script en modo interactivo
4. **Confirma** el resultado a Guus
5. **Documenta** en `testing-notes.md` si es parte de testing

### Troubleshooting

**Error: "USER_ID no encontrado"**
- Verifica que el texto tenga la línea `USER_ID: 999`

**Error: "No se encontraron mensajes"**
- Verifica formato `[Emisor]: mensaje`
- Asegúrate de tener al menos un mensaje

**Error de conexión a BD:**
- Verifica que PostgreSQL esté corriendo
- Verifica credenciales en `.env`

## 🔄 Workflow Completo de Testing

Para testing de Lola con MCP:

1. **Importar contexto:** `python scripts/import_tinder_context.py --interactive`
2. **Usar MCP tools:** `analyze_conversation(user_id=999)`
3. **Probar respuestas:** `test_personality_prompt(messages=[...])`
4. **Validar red flags:** `detect_red_flags(user_id=999)`
5. **Documentar:** Actualizar `testing-notes.md`

## 🎓 Para Desarrolladores

El script está en: `/home/gusta/Projects/Negocios/Stafems/lola_bot/scripts/import_tinder_context.py`

**Clase principal:** `TinderContextImporter`

**Métodos:**
- `parse_tinder_text(text)` - Parsea texto a dict
- `import_to_database(parsed_data)` - Inserta en BD
- `process_file(file_path)` - Procesa archivo

**Formato interno (parsed_data):**
```python
{
    "user_name": "Juanito",
    "user_id": 999,
    "messages": [
        {"sender": "Juanito", "content": "hola", "is_bot": False},
        {"sender": "Lola", "content": "holaa", "is_bot": True}
    ]
}
```

---

**Última actualización:** 2025-12-02  
**Autor:** Claude Desktop (CTO)  
**Versión:** 1.0
