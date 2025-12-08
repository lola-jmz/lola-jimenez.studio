# Brand Guidelines - Lola Jiménez Studio

## Paleta de Colores (EXACTOS)

### Primary
- **Fuchsia/Magenta:** `#E91E63`
- **Violet Purple:** `#9C27B0`

### Secondary
- **Bubblegum Pink:** `#FFB6C1`
- **Soft Rose:** `#F8BBD0`

### Neutrals
- **Pure White:** `#FFFFFF`
- **Jet Black:** `#000000`
- **Warm Taupe:** `#D7CCC8`

---

## Tipografía

### Headlines & Logo
- **Primary:** Brush Script MT
- **Fallback Google Font:** Pacifico
- **CSS Variable:** `var(--font-heading)`

### Body & UI
- **Primary:** Montserrat
- **Weights:** 400, 600, 700
- **CSS Variable:** `var(--font-sans)`

---

## Elementos Visuales

### Brushstrokes
- Pinceladas diagonales en fuchsia (#E91E63) y violet (#9C27B0)
- Usados como frames decorativos detrás de imágenes y títulos
- Estilo: orgánico, artístico, no perfecto

### Glassmorphism (Iconos)
- Background: `bg-white/10 backdrop-blur-md`
- Border: `border border-white/20`
- Brushstroke detrás como decoración

### Gradientes
- Hero: `from-[#E91E63] to-[#9C27B0]` (diagonal)
- Botones: mismo gradiente
- Secciones: sutiles de white a soft rose

### Frames de Portfolio
- Border 4px alternando #E91E63 (impares) y #9C27B0 (pares)
- Efecto brushstroke pintado alrededor

---

## Estilo Visual

### Personalidad
- Moderno y juvenil con sofisticación
- Femenino pero no infantil
- Artístico y vibrante
- Confianza y calidez

### Elementos Decorativos
- Corazones (💟)
- Pinceladas artísticas
- Formas orgánicas suaves

### Sombras
- Pronunciadas para profundidad
- shadow-xl, shadow-2xl
- Color-tinted en hover (rgba del color primario)

---

## Componentes Clave

### Botón CTA "Chat Privado 💟"
- Background: Gradiente #E91E63 → #9C27B0
- Color: #FFFFFF
- Border-radius: rounded-full
- Shadow: 2xl con efecto 3D
- Posición mobile: fixed bottom, z-50
- Posición desktop: static, centrado

### Header
- Transparente → blanco sólido on scroll
- Logo en #E91E63
- Altura: h-20

### Footer
- Background: #000000 a #1a1a1a
- Texto: #FFFFFF
- Links hover: #E91E63
- Iconos hover: #FFB6C1

---

## Responsive

### Prioridades Mobile-First
1. CTA sticky siempre visible
2. Touch targets mínimo 44x44px
3. Texto legible sin zoom
4. Imágenes optimizadas

### Breakpoints
- sm: 640px
- md: 768px
- lg: 1024px
- xl: 1280px

---

## Referencias de Imágenes

Las imágenes de mockup están en:
`/home/gusta/Projects/Negocios/Stafems/lola_bot/frontend/lola_landing/`

> **NOTA:** Si esta carpeta no existe, las imágenes originales están 
> en el proyecto de Claude Desktop y deben copiarse manualmente.

### Archivos de Referencia
- `Logo_Lola.jpg` - Logo principal
- `Favicon_Lola.jpg` - Favicon
- `Paleta_Colores_Lola.jpg` - Colores
- `Header_LandingPage_Lola.jpg` - Header design
- `Sobre__Mí__LandingPage_Lola.jpg` - About section
- `Portafolio_LandingPage_Lola.jpg` - Portfolio grid
- `BotónCTA_LandingPage_LOLA.jpg` - CTA button
- `VersiónMóvil_LandingPage_Lola.jpg` - Mobile layout
- `Iconos_LandingPage_Lola.jpg` - Icon set
- `Footer_LandingPage_Lola.jpg` - Footer design
