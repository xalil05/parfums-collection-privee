#!/usr/bin/env python3
"""
Mettre à jour le visuel WhatsApp — Parfums Collection Privée.
Version refactorisée : utilise img_gen.generate() avec catégories séparées.
Chemins relatifs, polices avec fallback, gestion d'erreurs.

Usage :
  python3 update-visuel.py                    # Génère avec le nouveau design
  python3 update-visuel.py --legacy           # Utilise template-reference.jpg (ancien)
"""

import os
import sys
import argparse

# Détection du répertoire du projet
DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(DIR, "whatsapp-status.jpg")
TEMPLATE = os.path.join(DIR, "template-reference.jpg")


def generate_legacy() -> str:
    """Version legacy : utilise template-reference.jpg comme fond."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("❌ Pillow n'est pas installé. Faites : pip install Pillow")
        sys.exit(1)

    if not os.path.exists(TEMPLATE):
        print(f"❌ Template introuvable : {TEMPLATE}")
        print("   Basculement vers le nouveau design...")
        return generate_modern()

    import json
    import re

    db_path = os.path.join(DIR, "parfums.json")
    with open(db_path, encoding="utf-8") as f:
        parfums = json.load(f)["parfums"]
    dispos = [p for p in parfums if p["stock"] > 0]

    # Polices avec fallback
    def find_font(name, size):
        fonts = {
            "NotoSerif-Regular": [
                os.path.expanduser("~/.fonts/NotoSerif-Regular.ttf"),
                "/tmp/fonts/NotoSerif-Regular.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            ],
            "NotoSerif-Bold": [
                os.path.expanduser("~/.fonts/NotoSerif-Bold.ttf"),
                "/tmp/fonts/NotoSerif-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            ],
        }
        for path in fonts.get(name, []):
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        return ImageFont.load_default()

    try:
        img = Image.open(TEMPLATE).copy()
    except Exception as e:
        print(f"❌ Impossible d'ouvrir le template : {e}")
        return generate_modern()

    W, H = img.size
    draw = ImageDraw.Draw(img)

    # Polices
    reg = find_font("NotoSerif-Regular", 38)
    title = find_font("NotoSerif-Bold", 46)
    sub = find_font("NotoSerif-Regular", 22)
    ft = find_font("NotoSerif-Regular", 18)

    # En-tête
    overlay = Image.new("RGBA", (W, 190), (0, 0, 0, 180))
    img.paste(overlay, (0, 0), overlay)
    draw.text((W // 2, 50), "COLLECTION PRIVÉE", fill=(255, 255, 255), font=title, anchor="mm")
    draw.text((W // 2, 100), "Parfumerie de Luxe", fill=(200, 200, 200), font=sub, anchor="mm")
    draw.text((W // 2, 140), f"{len(dispos)} parfums disponibles", fill=(150, 200, 150), font=sub, anchor="mm")

    # Liste 2 colonnes
    col1_x, col2_x = 100, 570
    line_h = 105
    start_y = 210
    text_color = (230, 230, 230)

    y = start_y
    for i, p in enumerate(dispos):
        if i == 11:
            y = start_y
        x = col1_x if i < 11 else col2_x
        nom = re.sub(r"^(L'|l'|La\s|la\s|Le\s|le\s|Les\s|les\s)", "", p["nom"])
        draw.text((x, y), nom, fill=text_color, font=reg)
        draw.ellipse([x + 320, y - 5, x + 334, y + 9], fill=(100, 200, 100))
        if i < 11:
            y += line_h

    # Footer
    draw.text((W // 2, 1900), "GENOVA • ITALIA", fill=(180, 180, 180), font=ft, anchor="mm")

    img.save(OUTPUT, "JPEG", quality=92)
    print(f"🖼️  Visuel legacy généré : {OUTPUT}")
    return OUTPUT


def generate_modern() -> str:
    """Version moderne avec catégories séparées (nouveau design)."""
    from img_gen import generate
    return generate(OUTPUT)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Générer le visuel WhatsApp — Collection Privée"
    )
    parser.add_argument("--legacy", action="store_true",
                        help="Utiliser template-reference.jpg (ancien design)")
    args = parser.parse_args()

    try:
        if args.legacy:
            generate_legacy()
        else:
            generate_modern()
    except Exception as e:
        print(f"❌ Erreur : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
