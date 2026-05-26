#!/usr/bin/env python3
"""Mettre à jour le visuel WhatsApp avec le template de référence"""
from PIL import Image, ImageDraw, ImageFont
import json, os, re, shutil

DATA_DIR = "/home/youngkhalil1997/data"
TEMPLATE = os.path.join(DATA_DIR, "template-reference.jpg")
OUTPUT = os.path.join(DATA_DIR, "whatsapp-status.jpg")
FONTS = "/tmp/fonts"

def sans_article(nom):
    return re.sub(r"^(L'|l'|La\s|la\s|Le\s|le\s|Les\s|les\s)", "", nom)

# Charger parfums
with open(os.path.join(DATA_DIR, "parfums.json")) as f:
    parfums = json.load(f)["parfums"]
dispos = [p for p in parfums if p["stock"] > 0]

# Charger template
img = Image.open(TEMPLATE).copy()
W, H = img.size
draw = ImageDraw.Draw(img)

# Polices (identiques au template)
reg = ImageFont.truetype(os.path.join(FONTS, "NotoSerif-Regular.ttf"), 38)
title = ImageFont.truetype(os.path.join(FONTS, "NotoSerif-Bold.ttf"), 46)
sub = ImageFont.truetype(os.path.join(FONTS, "NotoSerif-Regular.ttf"), 22)
ft = ImageFont.truetype(os.path.join(FONTS, "NotoSerif-Regular.ttf"), 18)

# En-tête
overlay = Image.new("RGBA", (W, 190), (0, 0, 0, 180))
img.paste(overlay, (0, 0), overlay)
draw.text((W//2, 50), "COLLECTION PRIVÉE", fill=(255, 255, 255), font=title, anchor="mm")
draw.text((W//2, 100), "Parfumerie de Luxe", fill=(200, 200, 200), font=sub, anchor="mm")
draw.text((W//2, 140), f"{len(dispos)} parfums disponibles", fill=(150, 200, 150), font=sub, anchor="mm")

# Liste 2 colonnes - entreligne 105px
col1_x, col2_x = 100, 570
line_h = 105
start_y = 210
text_color = (230, 230, 230)

y = start_y
for i, p in enumerate(dispos):
    if i == 11:
        y = start_y
    x = col1_x if i < 11 else col2_x
    nom = sans_article(p["nom"])
    draw.text((x, y), nom, fill=text_color, font=reg)
    draw.ellipse([x+320, y-5, x+334, y+9], fill=(100, 200, 100))
    if i < 11:
        y += line_h

# Footer
draw.text((W//2, 1900), "GENOVA • ITALIA", fill=(180, 180, 180), font=ft, anchor="mm")

img.save(OUTPUT, "JPEG", quality=92)
print(f"✅ Visuel mis à jour: {OUTPUT}")
print(f"🧴 {len(dispos)} parfums disponibles")
