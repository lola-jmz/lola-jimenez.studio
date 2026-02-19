# 🔬 PROMPT DE REVERSE ENGINEERING - LOLA

**Versión:** 1.0  
**Propósito:** Extraer características consistentes de Lola mediante análisis de imágenes en Nano Banana Pro  
**Autor:** Antigravity-Nuevo-Lola  
**Fecha:** 13-Dic-2025 2:55 AM

---

## 📋 INSTRUCCIONES PARA GUUS

### Proceso:
1. Abre Nano Banana Pro: https://www.fofr.ai/nano-banana-pro
2. Selecciona **5 IMÁGENES DIFERENTES** de Lola (mejores/más representativas)
3. Súbelas **UNA POR UNA** (no todas juntas)
4. Para cada imagen, copia y pega el **PROMPT DE ANÁLISIS** completo (abajo)
5. Copia la respuesta JSON en archivos separados (ver sección DÓNDE GUARDAR)

### Tiempo estimado: 15-20 minutos

---

## 🎯 PROMPT DE ANÁLISIS (Copiar esto a Nano Banana Pro)

```
Analyze this photograph in extreme detail and provide a comprehensive JSON reverse engineering of the person shown.

CRITICAL INSTRUCTIONS:
- Be ULTRA PRECISE with physical descriptions
- Use exact color values when possible (Pantone codes, Hex codes, or detailed color names)
- Measure proportions and dimensions as accurately as possible
- Include IMMUTABLE traits (things that never change) and VARIABLE traits (things that can change)
- Focus on CONSISTENCY MARKERS - features that would help identify this same person across different photos

OUTPUT FORMAT - Respond ONLY with valid JSON, no additional text:

{
  "image_metadata": {
    "image_number": "[DEJAR VACÍO - Guus lo llenará como 1, 2, 3, 4, o 5]",
    "analysis_confidence": "[high/medium/low]",
    "image_quality": "[excellent/good/fair/poor]",
    "full_body_visible": true/false,
    "face_clearly_visible": true/false
  },
  
  "character_immutable": {
    "age": {
      "estimated_age": "[número exacto, ej: 22]",
      "age_range": "[ej: 21-23]",
      "confidence": "[high/medium/low]"
    },
    
    "ethnicity": {
      "primary": "[ej: Latin American, European, etc.]",
      "specific_heritage": "[si es identificable, ej: Mexican, Colombian, etc.]",
      "skin_undertone": "[warm/cool/neutral]"
    },
    
    "skin": {
      "tone_description": "[descripción ultra detallada]",
      "pantone_match": "[código Pantone si es posible, ej: 16-1439 TCX Warm Sand]",
      "hex_approximate": "[código hex aproximado, ej: #D4A574]",
      "characteristics": ["ej: smooth", "even texture", "natural glow"]
    },
    
    "hair": {
      "base_color": "[color base exacto]",
      "highlights": "[si hay highlights, describir color y ubicación]",
      "lowlights": "[si hay lowlights]",
      "length": "[ej: mid-back length, shoulder length, etc.]",
      "texture": "[ej: straight, wavy, textured waves, etc.]",
      "style_in_photo": "[ej: loose waves, straight, ponytail, etc.]",
      "volume": "[high/medium/low]",
      "pantone_colors": ["[si es posible identificar Pantone del cabello]"]
    },
    
    "eyes": {
      "color": "[color exacto]",
      "color_detail": "[descripción detallada, ej: deep brown with amber flecks]",
      "shape": "[ej: almond, round, hooded, etc.]",
      "size": "[large/medium/small relative to face]",
      "characteristics": ["ej: expressive", "defined lashes", "natural brow arch"]
    },
    
    "face": {
      "shape": "[ej: oval, heart, square, round, etc.]",
      "proportions": {
        "forehead": "[high/medium/low]",
        "cheekbones": "[prominent/moderate/subtle]",
        "jawline": "[defined/soft/angular]",
        "chin": "[pointed/rounded/square]"
      },
      "distinctive_features": [
        "[ej: high cheekbones]",
        "[ej: defined jawline]",
        "[cualquier marca, lunar, cicatriz visible]"
      ]
    },
    
    "body": {
      "height_estimate": "[si es posible estimar, ej: 165cm / 5'5\"]",
      "build": "[ej: athletic, slender, curvy, petite, etc.]",
      "body_type": "[ej: hourglass, pear, athletic, etc.]",
      "proportions": "[ej: long legs, balanced, etc.]",
      "posture": "[natural posture: upright, relaxed, etc.]"
    },
    
    "distinctive_markers": [
      "[Cualquier rasgo único que ayude a identificar a esta persona]",
      "[ej: specific smile, eyebrow shape, nose profile, etc.]"
    ]
  },
  
  "outfit_visible": {
    "top": {
      "type": "[ej: crop top, blouse, t-shirt, etc.]",
      "color": "[color exacto]",
      "color_hex": "[si es posible]",
      "material": "[si es identificable: cotton, silk, etc.]",
      "style": "[ej: fitted, loose, structured, etc.]",
      "neckline": "[ej: crew neck, v-neck, etc.]",
      "sleeve": "[ej: sleeveless, short sleeve, long sleeve]"
    },
    
    "bottom": {
      "type": "[ej: jeans, skirt, pants, etc.]",
      "color": "[color exacto]",
      "style": "[ej: high-waisted, fitted, wide-leg, etc.]",
      "length": "[si es visible]"
    },
    
    "accessories": [
      "[lista de accesorios visibles: jewelry, bags, etc.]"
    ],
    
    "shoes": {
      "type": "[si son visibles]",
      "color": "[si son visibles]"
    },
    
    "overall_style": "[ej: casual elegant, athleisure, formal, etc.]"
  },
  
  "makeup_visible": {
    "foundation": "[natural/light/medium/full coverage - si es visible]",
    "eyes": {
      "eyeshadow": "[descripción si es visible]",
      "eyeliner": "[yes/no - si es visible]",
      "mascara": "[natural/defined/dramatic]"
    },
    "brows": "[natural/defined/filled]",
    "lips": {
      "color": "[natural/nude/pink/red/etc.]",
      "finish": "[matte/glossy/natural]"
    },
    "overall_look": "[natural/minimal/moderate/glamorous]"
  },
  
  "pose_and_expression": {
    "pose": "[descripción detallada de la pose]",
    "body_angle": "[ej: facing camera, 3/4 turn, profile, etc.]",
    "facial_expression": "[ej: natural smile, serious, playful, etc.]",
    "eye_contact": "[direct to camera/looking away/etc.]",
    "hands_position": "[si son visibles]",
    "overall_mood": "[ej: confident, relaxed, energetic, etc.]"
  },
  
  "environment": {
    "location_type": "[ej: bedroom, gym, outdoor, studio, etc.]",
    "lighting": {
      "type": "[ej: natural window light, artificial, golden hour, etc.]",
      "direction": "[ej: from left, overhead, front-facing, etc.]",
      "quality": "[soft/harsh/diffused/dramatic]",
      "color_temperature": "[warm/cool/neutral]"
    },
    "background": "[descripción del fondo]",
    "mood": "[overall mood of the scene]"
  },
  
  "photography_technical": {
    "camera_angle": "[ej: eye level, low angle, high angle, etc.]",
    "shot_type": "[ej: full body, 3/4 body, waist up, headshot, etc.]",
    "depth_of_field": "[shallow/medium/deep - background blur visible?]",
    "composition": "[ej: centered, rule of thirds, etc.]",
    "aspect_ratio_estimate": "[ej: 2:3 portrait, 16:9, etc.]"
  },
  
  "consistency_notes": {
    "key_identifiers": [
      "[Lista de rasgos MÁS ÚTILES para identificar a esta persona en otras fotos]",
      "[ej: distinctive facial structure, specific hair color/highlights, body proportions]"
    ],
    "comparison_markers": [
      "[Rasgos que serían más fáciles de comparar con otras imágenes]"
    ]
  }
}

REMEMBER: 
- Be as SPECIFIC as possible
- Use measurable/comparable terms
- Focus on IMMUTABLE traits that would be consistent across photos
- Include Pantone/Hex codes when identifiable
- This data will be used to find PATTERNS across multiple images
```

---

## 📁 DÓNDE GUARDAR LOS RESULTADOS

Guus, crea primero esta carpeta con el comando:

```bash
mkdir -p /home/gusta/Projects/Negocios/Stafems/lola_bot/.guus/docs/NANO_BANANA/reverse_engineering_results
```

Después de recibir cada respuesta JSON de Nano Banana Pro, guárdala en:

### Nombres de archivos:
1. `lola_analysis_01.json` (primera imagen)
2. `lola_analysis_02.json` (segunda imagen)
3. `lola_analysis_03.json` (tercera imagen)
4. `lola_analysis_04.json` (cuarta imagen)
5. `lola_analysis_05.json` (quinta imagen)

### Antes de guardar:
1. Copia la respuesta completa de Nano Banana Pro
2. Crea el archivo correspondiente en la carpeta `reverse_engineering_results/`
3. **IMPORTANTE:** En el campo `"image_number"`, reemplaza `[DEJAR VACÍO]` con el número (1, 2, 3, 4, o 5)
4. Verifica que sea JSON válido (debe empezar con `{` y terminar con `}`)
5. Guarda el archivo

---

## ✅ CHECKLIST PARA GUUS

Antes de empezar:
- [ ] Tengo 5 imágenes de Lola seleccionadas (mejores/más representativas)
- [ ] Imágenes muestran a Lola claramente (cara visible, buena calidad)
- [ ] He creado la carpeta `reverse_engineering_results/`

Para cada imagen (repetir 5 veces):
- [ ] Subí imagen a Nano Banana Pro
- [ ] Copié el PROMPT DE ANÁLISIS completo
- [ ] Recibí respuesta JSON
- [ ] Guardé en archivo correspondiente (`lola_analysis_0X.json`)
- [ ] Añadí el `image_number` correcto
- [ ] Verifiqué que sea JSON válido

Después de las 5 imágenes:
- [ ] Notificar a Antigravity que los 5 archivos están listos
- [ ] Antigravity leerá y analizará consistencias

---

## 🎯 QUÉ HAREMOS CON ESTOS DATOS

1. **Antigravity leerá los 5 JSONs**
2. **Identificará CONSISTENCIAS** entre las 5 análisis:
   - ¿Qué rasgos son EXACTAMENTE iguales en todas?
   - ¿Qué rasgos varían y por qué? (ej: ropa, makeup, pose)
3. **Creará el JSON MAESTRO** `lola-character.json` con rasgos INMUTABLES
4. **Diseñará schemas** para ropa, poses, espacios
5. **Generará plan** para Antigravity-externo-Fashion

---

## 🚀 PRÓXIMOS PASOS

1. **Guus:** Ejecuta este proceso con 5 imágenes
2. **Guus:** Guarda los 5 JSONs en la carpeta especificada
3. **Guus:** Notifica a Antigravity cuando esté listo
4. **Antigravity:** Analiza consistencias y diseña plan final

---

**Creado por:** Antigravity-Nuevo-Lola  
**Para:** Guus (Product Owner)  
**Siguiente paso:** Reverse engineering con Nano Banana Pro
