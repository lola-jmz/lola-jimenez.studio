# 🚀 TASK para Antigravity IDE - Integración Contexto Tinder

**Fecha:** 2025-12-03  
**Prioridad:** 🔴 Alta  
**Fase:** Fase 2 - Sección 2.1 (ROADMAP.md)  
**Objetivo:** Que Lola "recuerde" conversaciones previas de Tinder cuando responda en el chat privado

---

## 🎯 CONTEXTO DEL PROBLEMA

**Situación actual:**
- Los usuarios vienen desde Tinder al chat privado de `lola-jimenez.studio`
- Ya tuvieron conversación previa con Lola en Tinder
- El sistema guarda ese contexto en la tabla `conversations` campo `context` (JSONB)
- **PERO:** Lola NO usa ese contexto al generar respuestas
- **RESULTADO:** Lola no "recuerda" lo que habló con el usuario en Tinder

**Lo que necesitamos:**
Que cuando Lola genere una respuesta con Gemini AI, incluya en el prompt el historial previo de Tinder.

---

## 📂 ARCHIVOS A MODIFICAR

### 1. `/home/gusta/Projects/Negocios/Stafems/lola_bot/database/database_pool.py`

**Estado:** ✅ YA MODIFICADO

El método `get_tinder_context()` ya fue agregado a la clase `ConversationRepository`.

---

### 2. `/home/gusta/Projects/Negocios/Stafems/lola_bot/core/core_handler.py`

**Estado:** ✅ Método `_load_tinder_context()` YA EXISTE

**CAMBIO PENDIENTE:** Modificar método `_generate_lola_response`

**BUSCAR estas líneas:**
```python
# 2. OBTENER CONTEXTO DE TIEMPO REAL (NUEVA LÓGICA)
time_context = self._get_current_time_context()

# 3. Construir el prompt completo
full_prompt = f"""
{self.lola_personality}

---
{time_context}
(Instrucción para ti, IA: Debes usar el 'CONTEXTO DE TIEMPO REAL' para que tus respuestas sean creíbles. 
Ej: Si son las 3 AM, estás despierta haciendo tareas de la uni, no en el gym. 
Si el usuario pregunta 'qué día es hoy', usa esta información.)
---

HISTORIAL DE CONVERSACIÓN RECIENTE:
{context_history}
```

**REEMPLAZAR con:**
```python
# 2. OBTENER CONTEXTO DE TIEMPO REAL
time_context = self._get_current_time_context()

# 3. OBTENER CONTEXTO DE TINDER (NUEVA FUNCIONALIDAD)
tinder_context = await self._load_tinder_context(user_id)

# 4. Construir el prompt completo
full_prompt = f"""
{self.lola_personality}

---
{time_context}
(Instrucción para ti, IA: Debes usar el 'CONTEXTO DE TIEMPO REAL' para que tus respuestas sean creíbles. 
Ej: Si son las 3 AM, estás despierta haciendo tareas de la uni, no en el gym. 
Si el usuario pregunta 'qué día es hoy', usa esta información.)
---

{tinder_context if tinder_context else ""}

HISTORIAL DE CONVERSACIÓN RECIENTE:
{context_history}
```

**IMPORTANTE:** Solo agregar:
1. La línea que carga el contexto: `tinder_context = await self._load_tinder_context(user_id)`
2. La sección del tinder_context en el prompt (entre time_context y HISTORIAL)

---

## ✅ VERIFICACIÓN

### Test 1: Verificar que el código compila

```bash
cd /home/gusta/Projects/Negocios/Stafems/lola_bot
python -m py_compile core/core_handler.py
python -m py_compile database/database_pool.py
```

**Esperado:** Sin errores

### Test 2: Verificar que Juanito tiene contexto

```bash
psql -U postgres -d maria_bot -c "
SELECT 
    u.user_id, 
    u.username,
    c.context->'tinder_metadata'->>'name' as tinder_name,
    jsonb_array_length(c.context->'tinder_history') as num_messages
FROM users u
JOIN conversations c ON u.user_id = c.user_id
WHERE u.user_id = 999;
"
```

**Esperado:**
```
 user_id | username | tinder_name | num_messages 
---------+----------+-------------+--------------
     999 | Juanito  | Juanito     |           14
```

### Test 3: Iniciar servidor y probar

```bash
cd /home/gusta/Projects/Negocios/Stafems/lola_bot/api
python run_fastapi_basic.py
```

**Verificar en logs:**
```
✅ Contexto de Tinder cargado para user_id 999: 14 mensajes
```

---

## 🎯 RESULTADO ESPERADO

**Antes:**
- Usuario: "Hola Lola, soy Juanito"
- Lola: "holaa qué tal, aquí trabajando en unos proyectos"
- ❌ No reconoce que ya conversaron en Tinder

**Después:**
- Usuario: "Hola Lola, soy Juanito"  
- Lola: "holaa Juanito! qué bueno que llegaste haha, aquí trabajando en unos proyectos"
- ✅ Reconoce nombre porque lo vio en contexto de Tinder
- ✅ Continúa conversación naturalmente

---

## 📊 IMPACTO

- **Archivos modificados:** 1 (core_handler.py - un solo cambio pendiente)
- **Líneas agregadas:** ~5 líneas
- **Riesgo:** 🟢 Bajo (solo agregamos carga de contexto y lo incluimos en prompt)
- **Testing:** Requiere prueba con usuario que tenga contexto de Tinder (Juanito user_id 999)

---

## 🚨 NOTAS IMPORTANTES

1. **NO modificar** `docs/LOLA.md` - Ya tiene las reglas de timing correctas
2. **NO modificar** la lógica del FSM - Solo agregamos contexto al prompt
3. **NO tocar** `api/run_fastapi_basic.py` - El cambio es solo en core_handler.py
4. El contexto de Tinder se carga **automáticamente** si existe

---

## 📝 CHECKLIST PARA ANTIGRAVITY

- [x] Verificar que `get_tinder_context()` existe en `ConversationRepository`
- [x] Verificar que `_load_tinder_context()` existe en `LolaCoreHandler`
- [ ] Modificar `_generate_lola_response()` para incluir `tinder_context`
- [ ] Compilar archivos Python (verificar sintaxis)
- [ ] Ejecutar Test 2 (verificar BD)
- [ ] Iniciar servidor
- [ ] Verificar logs de carga de contexto
- [ ] Marcar sección 2.1 del ROADMAP.md como ✅ COMPLETADO

---

**Generado:** 2025-12-03 03:10 UTC  
**Para:** Antigravity IDE (Google) con Anthropic Sonnet 4.5  
**Proyecto:** Bot Lola - lola-jimenez.studio
