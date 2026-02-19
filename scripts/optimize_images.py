#!/usr/bin/env python3
"""
Optimiza y convierte todas las imágenes del portfolio a WebP.

- Hero:      1200×960  (5:4 horizontal) — se mantiene más ancho
- About:     800×800   (1:1 cuadrado, se mostrará en círculo con CSS)
- Portfolio: 800×1200  (2:3 vertical) — match con aspect ratio de las fotos originales

Uso:
    python3 scripts/optimize_images.py

Requiere: Pillow  (pip install Pillow)
"""

from pathlib import Path
from PIL import Image, ImageOps
import sys

# ─── Configuración ────────────────────────────────────────────
SRC_DIR  = Path(__file__).parent.parent / "frontend" / "public" / "images"
OUT_DIR  = SRC_DIR  # Sobreescribir en el mismo lugar
QUALITY  = 82       # 82 = excelente calidad, ~60% menos peso que original

TARGETS = {
    "hero":        (1200, 960),   # 5:4 horizontal
    "about":       (800,  800),   # 1:1 cuadrado
    "portafolio":  (800,  1200),  # 2:3 vertical (para portafolio-1 al 8)
}

# Extensiones de entrada aceptadas
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"}

# ─── Mapeo de archivos de entrada a nombre de salida ─────────
# Si hay typo en el nombre original (protafolio-5) también se maneja
FILE_MAP = {
    # nombre_base_entrada → (nombre_salida_sin_ext, tipo)
    "hero":          ("hero",         "hero"),
    "about":         ("about",        "about"),
    "portafolio-1":  ("portafolio-1", "portafolio"),
    "portafolio-2":  ("portafolio-2", "portafolio"),
    "portafolio-3":  ("portafolio-3", "portafolio"),
    "portafolio-4":  ("portafolio-4", "portafolio"),
    "portafolio-5":  ("portafolio-5", "portafolio"),
    "protafolio-5":  ("portafolio-5", "portafolio"),  # typo → nombre correcto
    "portafolio-6":  ("portafolio-6", "portafolio"),
    "portafolio-7":  ("portafolio-7", "portafolio"),
    "portafolio-8":  ("portafolio-8", "portafolio"),
}

def smart_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Redimensiona y recorta centrado inteligentemente (sin deformar)."""
    img = ImageOps.exif_transpose(img)  # Corregir orientación EXIF
    orig_w, orig_h = img.size
    target_ratio   = target_w / target_h
    orig_ratio     = orig_w  / orig_h

    if orig_ratio > target_ratio:
        # Original más ancho → ajustar por alto, recortar lados
        new_h = target_h
        new_w = int(orig_w * (target_h / orig_h))
    else:
        # Original más alto → ajustar por ancho, recortar arriba/abajo
        new_w = target_w
        new_h = int(orig_h * (target_w / orig_w))

    img = img.resize((new_w, new_h), Image.LANCZOS)

    # Recorte centrado
    left = (new_w - target_w) // 2
    top  = (new_h - target_h) // 2
    img  = img.crop((left, top, left + target_w, top + target_h))
    return img

def process_image(src: Path, out_name: str, kind: str) -> None:
    target_w, target_h = TARGETS[kind]
    out_path = OUT_DIR / f"{out_name}.webp"

    with Image.open(src) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        orig_size = src.stat().st_size

        processed = smart_crop(img, target_w, target_h)
        processed.save(out_path, "WEBP", quality=QUALITY, method=6)

    new_size = out_path.stat().st_size
    ratio    = (1 - new_size / orig_size) * 100
    print(f"  ✓ {src.name:30s} → {out_path.name:25s}  {orig_size//1024:>6} KB → {new_size//1024:>5} KB  (-{ratio:.0f}%)")

def main():
    print(f"\nOptimizando imágenes en: {SRC_DIR}\n")
    found = 0
    skipped = []

    for src in sorted(SRC_DIR.iterdir()):
        if src.suffix.lower() not in EXTS:
            continue
        stem = src.stem.lower()
        if stem not in FILE_MAP:
            skipped.append(src.name)
            continue

        out_name, kind = FILE_MAP[stem]

        # Si ya es WebP con el nombre correcto y NO es uno de los que cambia, saltar
        if src == OUT_DIR / f"{out_name}.webp" and kind == "portafolio" and out_name == "portafolio-6":
            print(f"  ↩ {src.name:30s}  (conservada tal cual)")
            found += 1
            continue

        process_image(src, out_name, kind)
        found += 1

        # Si la fuente no es WebP o tiene nombre distinto al de salida, borrar el original
        out_path = OUT_DIR / f"{out_name}.webp"
        if src != out_path and src.exists():
            src.unlink()
            print(f"    🗑  original eliminado: {src.name}")

    print(f"\n{'─'*65}")
    print(f"  {found} imagen(es) procesadas.")
    if skipped:
        print(f"  ⚠  Ignorados (no en el mapa): {', '.join(skipped)}")
    print()

if __name__ == "__main__":
    try:
        from PIL import Image, ImageOps
    except ImportError:
        print("ERROR: Pillow no instalado.\nEjecuta: pip install Pillow")
        sys.exit(1)
    main()
