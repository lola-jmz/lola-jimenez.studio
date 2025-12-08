# 📁 Estructura del Proyecto - Lola Jiménez Landing Page

**Fecha de generación:** $(date '+%Y-%m-%d %H:%M')
**Plataforma de origen:** reweb.so
**Stack:** Next.js 16 + TypeScript + Tailwind CSS + shadcn/ui

---

## 🌳 Árbol de Archivos

.
├── app
│   ├── favicon.ico
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── components
│   ├── ui
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── separator.tsx
│   └── lola-jimenez-studio-landing-page.tsx
├── lib
│   └── utils.ts
├── public
│   ├── file.svg
│   ├── globe.svg
│   ├── next.svg
│   ├── vercel.svg
│   └── window.svg
├── components.json
├── eslint.config.mjs
├── ESTRUCTURA_PROYECTO.md
├── .gitignore
├── next.config.ts
├── next-env.d.ts
├── package.json
├── package-lock.json
├── postcss.config.mjs
├── README.md
└── tsconfig.json

6 directories, 26 files

---

## 📝 Descripción de Archivos Principales

### /app (Directorio de Next.js App Router)
- `layout.tsx` # Layout raíz - configuración de fonts, metadata global
- `page.tsx` # Página principal - importa y renderiza LolaJiménezStudioLandingPage
- `globals.css` # Variables CSS globales - paleta de colores (#E91E63, #9C27B0, etc.)
- `favicon.ico` # Ícono de pestaña del navegador

### /components (Componentes React)
- `lola-jimenez-studio-landing-page.tsx` # Componente principal de la landing page completa

### /components/ui (Componentes shadcn/ui)
- `button.tsx` # Componente Button - botones con variantes (ghost, default, etc.)
- `card.tsx` # Componente Card - tarjetas con CardContent, CardHeader, etc.
- `input.tsx` # Componente Input - campos de entrada de formulario
- `separator.tsx` # Componente Separator - líneas divisorias

### /lib (Utilidades)
- `utils.ts` # Función cn() para merge de clases Tailwind

### Archivos de Configuración (raíz)
- `package.json` # Dependencias y scripts del proyecto
- `package-lock.json` # Lock de versiones exactas
- `tsconfig.json` # Configuración de TypeScript
- `tailwind.config.ts` # Configuración de Tailwind CSS
- `next.config.ts` # Configuración de Next.js
- `postcss.config.mjs` # Configuración de PostCSS
- `eslint.config.mjs` # Configuración de ESLint
- `components.json` # Configuración de shadcn/ui

---

## 🎨 Paleta de Colores Implementada
```css
--primary: #E91E63       /* Fuchsia - color principal */
--secondary: #9C27B0     /* Violet - color secundario */
--accent: #FFB6C1        /* Bubblegum Pink - acentos */
--card: #F8BBD0          /* Soft Rose - fondos de cards */
--background: #FFFFFF    /* Blanco - fondo principal */
--foreground: #000000    /* Negro - texto principal */
--muted: #D7CCC8         /* Taupe - texto secundario */
```

---

## 🔧 Comandos Útiles
```bash
# Desarrollo
npm run dev

# Build para producción
npm run build

# Lint
npm run lint

# Preview de producción
npm run start
```

---

## 📦 Dependencias Principales

- `next` - Framework React
- `react` / `react-dom` - Biblioteca UI
- `typescript` - Tipado estático
- `tailwindcss` - Estilos utilitarios
- `@iconify/react` - Iconos (solar icons)
- `class-variance-authority` - Variantes de componentes
- `clsx` / `tailwind-merge` - Utilidades de clases

---

## ✅ Estado Actual

- [x] Proyecto Next.js inicializado
- [x] shadcn/ui configurado
- [x] Componentes UI base (Button, Card, Input, Separator)
- [x] Landing page completa generada por reweb.so
- [x] Paleta de colores aplicada
- [ ] Fotos reales de Lola (usando placeholders)
- [ ] WebSocket para Chat Privado
- [ ] Deploy en Vercel

---

**Generado automáticamente para alineación del equipo**
