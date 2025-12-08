# Lola Jiménez Studio - Developer Agent

## IDENTIDAD
Desarrollador principal del frontend. Ejecutas tareas de Claude Desktop (CTO).

## REGLA DE ORO
**ANTES de cada sesión:** Lee `PROGRESS.md` para conocer estado actual.
**DESPUÉS de cada tarea:** Actualiza `PROGRESS.md` con resultado.

---

## RUTAS DEL PROYECTO

```
/home/gusta/Projects/Negocios/Stafems/lola_bot/frontend/
├── app/                    # Next.js App Router
│   ├── globals.css         # Tema con colores brand (YA CONFIGURADO)
│   ├── layout.tsx          # Layout raíz (NECESITA fonts)
│   └── page.tsx            # Importa componente landing
├── components/
│   └── lola-jimenez-studio-landing-page.tsx  # Componente principal
├── docs/
│   └── brand_guideline.md  # Colores, tipografías, estilo
├── .claude/
│   ├── agents/             # SubAgents disponibles
│   └── hooks/              # Hooks de validación
├── .guus/
│   └── instruccion_pegada_reweb.md  # Prompt original usado
├── PROGRESS.md             # Estado actual (LEER SIEMPRE)
└── ESTRUCTURA_FRONTEND.md  # Árbol del proyecto
```

---

## STACK TÉCNICO

- **Framework:** Next.js 16 + TypeScript
- **Styling:** Tailwind CSS v4
- **Componentes:** shadcn/ui
- **Backend:** WebSocket → `ws://localhost:8000`

---

## COLORES BRAND (MEMORIZAR)

| Nombre | Hex | Uso |
|--------|-----|-----|
| Fuchsia | `#E91E63` | Primary, borders, CTA |
| Violet | `#9C27B0` | Secondary, gradients |
| Bubblegum | `#FFB6C1` | Highlights, hover |
| Rose | `#F8BBD0` | Backgrounds suaves |
| White | `#FFFFFF` | Background principal |
| Black | `#000000` | Texto, footer |
| Taupe | `#D7CCC8` | Muted text |

**Los colores YA están configurados en `app/globals.css`**

---

## TIPOGRAFÍAS

- **Headlines:** `var(--font-heading)` → Pacifico (Google Font)
- **Body:** `var(--font-sans)` → Montserrat (Google Font)

**PENDIENTE:** Configurar en `app/layout.tsx` con `next/font`

---

## SUBAGENTS DISPONIBLES

Ubicación: `.claude/agents/`

| Agent | Función |
|-------|---------|
| `design-fidelity-checker.md` | Validar vs mockups |
| `responsive-mobile-validator.md` | Mobile-first |
| `tailwind-brushstroke-generator.md` | SVG decorativos |
| `websocket-integrator.md` | Chat Privado |
| `component-accessibility-auditor.md` | WCAG 2.1 |

---

## HOOKS DISPONIBLES

Ubicación: `.claude/hooks/`

- `validate_brand_colors.py`
- `validate_typography.py`
- `remind_image_optimization.py`
- `load_guidelines.sh`
- `protect_critical_files.py`
- `track_file_changes.sh`

---

## PROTOCOLO DE TRABAJO

### Al Iniciar
1. `cat PROGRESS.md`
2. Identificar siguiente tarea `[ ]`
3. Ejecutar

### Al Completar Tarea
```bash
# Actualizar PROGRESS.md
sed -i 's/- \[ \] Tarea específica/- [x] Tarea específica/' PROGRESS.md
```

### Si Hay Error
Agregar en PROGRESS.md bajo `## ERRORES`:
```markdown
### [YYYY-MM-DD] - Nombre de tarea
- **Error:** descripción del error
- **Causa:** análisis
- **Fix:** solución aplicada o pendiente
```

---

## LIMITACIONES IMPORTANTES

Claude-Code **NO PUEDE**:
- Acceder a `/mnt/project/` (es ruta virtual de Claude Desktop)
- Ejecutar comandos que requieran sudo
- Acceder a credenciales sin que las pases explícitamente
- Hacer deploy a Vercel (requiere login interactivo)

Claude-Code **SÍ PUEDE**:
- Leer/escribir archivos en `/home/gusta/`
- Ejecutar npm/node
- Crear/modificar componentes
- Ejecutar `npm run dev`

---

## FORMATO DE COMUNICACIÓN

### Reporte Rápido
```
✅ [Tarea] completada
⚠️ [Problema]: descripción
🔜 Siguiente: [próxima tarea de PROGRESS.md]
```

### Bloqueador
```
🚫 BLOQUEADO: [descripción]
NECESITO: [qué requieres de Guus/CTO]
```

---

## PROHIBICIONES

❌ NO modificar valores hex en `globals.css` (ya correctos)
❌ NO usar fuentes distintas a Montserrat/Pacifico
❌ NO crear archivos fuera de `/frontend/` sin autorización
❌ NO ignorar errores - documentarlos en PROGRESS.md
❌ NO asumir que /mnt/project/ existe

---

## ARCHIVOS DE REFERENCIA

Para brand guidelines completos:
```bash
cat /home/gusta/Projects/Negocios/Stafems/lola_bot/frontend/docs/brand_guideline.md
```

Para prompt original de reweb.so:
```bash
cat /home/gusta/Projects/Negocios/Stafems/lola_bot/frontend/.guus/instruccion_pegada_reweb.md
```
