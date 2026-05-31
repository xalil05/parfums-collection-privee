#!/usr/bin/env python3
"""
Génération du visuel WhatsApp — Parfums Collection Privée.
Produit whatsapp-status.jpg avec catégories Homme/Femme/Mixte en colonnes.
"""

import json
import os
import datetime
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

from db import load_db, Database, Parfum

DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(DIR, "whatsapp-status.jpg")


# --- Polices (avec fallback) ---

def _find_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Trouve une police avec fallback vers les polices système."""
    candidates = {
        "DejaVuSerif-Bold": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        ],
        "DejaVuSerif": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        ],
        "DejaVuSans-Bold": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ],
        "DejaVuSans": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ],
    }
    paths = candidates.get(name, [])
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    # Fallback ultime : police par défaut Pillow
    return ImageFont.load_default()


def _charger_polices() -> dict[str, ImageFont.FreeTypeFont]:
    """Charge toutes les polices nécessaires."""
    return {
        "titre": _find_font("DejaVuSerif-Bold", 82),
        "sous_titre": _find_font("DejaVuSerif", 32),
        "titre_categorie": _find_font("DejaVuSerif-Bold", 44),
        "nom_parfum": _find_font("DejaVuSans-Bold", 34),
        "nom_marque": _find_font("DejaVuSans-Bold", 22),
        "badge": _find_font("DejaVuSans-Bold", 24),
        "footer": _find_font("DejaVuSans", 20),
        "footer_bold": _find_font("DejaVuSans-Bold", 22),
    }


def _dessiner_section(
    draw: ImageDraw.ImageDraw,
    titre: str,
    items: list[Parfum],
    x: int,
    y_start: int,
    polices: dict,
    largeur_colonne: int = 420,
    hauteur_ligne: int = 72,
) -> int:
    """Dessine une section de parfums. Retourne le y après la section + gap."""
    y = y_start
    # Titre de section
    draw.text((x, y), titre, fill="#1a1a2e", font=polices["titre_categorie"])
    y += 58

    for p in items:
        # Marque (en petit, doré)
        draw.text((x, y), p["marque"].upper(), fill="#d4af37", font=polices["nom_marque"])
        y += 30
        # Nom du parfum
        bbox = draw.textbbox((0, 0), p["nom"], font=polices["nom_parfum"])
        nw = bbox[2] - bbox[0]
        draw.text((x, y), p["nom"], fill="#1a1a2e", font=polices["nom_parfum"])
        # Badge si stock bas
        if p["stock"] <= 2:
            texte_badge = f' ⚡ x{p["stock"]}'
            draw.text(
                (x + nw + 16, y + 4),
                texte_badge,
                fill="#e17055",
                font=polices["badge"],
            )
        y += hauteur_ligne

    return y + 60  # gap après la section


def generate(output_path: str = OUTPUT) -> str:
    """
    Génère l'image whatsapp-status.jpg avec catégories séparées en colonnes.
    
    Disposition :
      Colonne gauche (x=70) : HOMME → MIXTE
      Colonne droite  (x=560) : FEMME
    """
    db = load_db()
    parfums = db["parfums"]
    dispos = [p for p in parfums if p["stock"] > 0]
    hommes = [p for p in dispos if p["categorie"] == "Homme"]
    femmes = [p for p in dispos if p["categorie"] == "Femme"]
    mixtes = [p for p in dispos if p["categorie"] == "Mixte"]

    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    polices = _charger_polices()

    # Fond : gradient doux du haut vers le bas
    for y in range(320):
        r = int(15 + (20 - 15) * y / 320)
        g = int(15 + (25 - 15) * y / 320)
        b = int(25 + (40 - 15) * y / 320)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Ligne décorative sous l'en-tête
    draw.line([(0, 320), (W, 320)], fill=(212, 175, 55), width=3)

    # Titre principal
    titre = "✦ COLLECTION PRIVÉE ✦"
    bbox = draw.textbbox((0, 0), titre, font=polices["titre"])
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, 45), titre, fill="#d4af37", font=polices["titre"])

    # Ligne décorative sous le titre
    draw.line([(W // 2 - 60, 128), (W // 2 + 60, 128)], fill=(212, 175, 55), width=2)

    # Sous-titre
    ss = "PARFUMERIE DE LUXE"
    bbox = draw.textbbox((0, 0), ss, font=polices["sous_titre"])
    sw = bbox[2] - bbox[0]
    draw.text(((W - sw) // 2, 150), ss, fill="#c0b8a8", font=polices["sous_titre"])

    # Compteur
    compteur = f"{len(dispos)} PARFUMS DISPONIBLES"
    bbox = draw.textbbox((0, 0), compteur, font=polices["sous_titre"])
    cw = bbox[2] - bbox[0]
    draw.text(((W - cw) // 2, 202), compteur, fill="#d4af37", font=polices["sous_titre"])

    # Sections : colonne gauche (Homme + Mixte) et colonne droite (Femme)
    cx1, cx2 = 70, 560
    sy = 372

    y1 = _dessiner_section(draw, "HOMME", hommes, cx1, sy, polices)
    y1 = _dessiner_section(draw, "UNISEXE", mixtes, cx1, y1, polices)
    _dessiner_section(draw, "FEMME", femmes, cx2, sy, polices)

    # Footer
    fy = 1840
    draw.line([(100, fy), (W - 100, fy)], fill=(212, 175, 55), width=2)

    f1 = "Disponibilité sous réserve de vente"
    bbox = draw.textbbox((0, 0), f1, font=polices["footer"])
    fw = bbox[2] - bbox[0]
    draw.text(((W - fw) // 2, fy + 20), f1, fill="#aaa", font=polices["footer"])

    f2 = "@collection.privee"
    bbox = draw.textbbox((0, 0), f2, font=polices["footer_bold"])
    f2w = bbox[2] - bbox[0]
    draw.text(((W - f2w) // 2, fy + 54), f2, fill="#d4af37", font=polices["footer_bold"])

    # Sauvegarde
    img.save(output_path, "JPEG", quality=97)
    print(f"🖼️  Visuel généré : {output_path}")
    return output_path
