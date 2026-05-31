#!/usr/bin/env python3
"""
Génération d'images — Parfums Collection Privée.
Multi-format support : WhatsApp, Instagram, Facebook, Twitter, OG Card.
"""

import json
import os
import datetime
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

from db import load_db, Database, Parfum

DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(DIR, "whatsapp-status.jpg")


# ============================================================
#  FORMATS DISPONIBLES
# ============================================================

FORMATS = {
    "whatsapp-status": {
        "name": "WhatsApp Status",
        "w": 1080, "h": 1920,
        "ratio": "9:16",
        "desc": "Idéal pour statut WhatsApp et stories Instagram",
        "colors": {"bg_top": (15, 15, 25), "bg_bot": (20, 25, 40), "gold": (212, 175, 55)},
        "layout": "2cols",
        "sizes": {
            "titre": 82, "sous_titre": 32, "titre_cat": 44,
            "nom": 34, "marque": 22, "badge": 24, "footer": 20, "footer_bold": 22,
            "header_ht": 320, "fh_enTete": 45, "sy": 372, "cx1": 70, "cx2": 560,
            "fh_ligne": 72, "gap": 60, "fy": 1840,
        },
    },
    "instagram-square": {
        "name": "Instagram Carré",
        "w": 1080, "h": 1080,
        "ratio": "1:1",
        "desc": "Publication Instagram (feed)",
        "colors": {"bg_top": (15, 15, 25), "bg_bot": (20, 25, 40), "gold": (212, 175, 55)},
        "layout": "compact",
        "sizes": {
            "titre": 56, "sous_titre": 24, "titre_cat": 32,
            "nom": 26, "marque": 16, "badge": 18, "footer": 14, "footer_bold": 16,
            "header_ht": 200, "fh_enTete": 30, "sy": 240, "cx1": 50, "cx2": 560,
            "fh_ligne": 50, "gap": 40, "fy": 1020,
        },
    },
    "instagram-story": {
        "name": "Instagram Story",
        "w": 1080, "h": 1920,
        "ratio": "9:16",
        "desc": "Story Instagram (identique WhatsApp)",
        "colors": {"bg_top": (15, 15, 25), "bg_bot": (20, 25, 40), "gold": (212, 175, 55)},
        "layout": "2cols",
        "sizes": {
            "titre": 82, "sous_titre": 32, "titre_cat": 44,
            "nom": 34, "marque": 22, "badge": 24, "footer": 20, "footer_bold": 22,
            "header_ht": 320, "fh_enTete": 45, "sy": 372, "cx1": 70, "cx2": 560,
            "fh_ligne": 72, "gap": 60, "fy": 1840,
        },
    },
    "facebook-post": {
        "name": "Facebook Post",
        "w": 1200, "h": 630,
        "ratio": "~2:1",
        "desc": "Partage Facebook / lien riche",
        "colors": {"bg_top": (15, 15, 25), "bg_bot": (20, 25, 40), "gold": (212, 175, 55)},
        "layout": "compact",
        "sizes": {
            "titre": 42, "sous_titre": 20, "titre_cat": 24,
            "nom": 20, "marque": 13, "badge": 14, "footer": 11, "footer_bold": 13,
            "header_ht": 140, "fh_enTete": 20, "sy": 160, "cx1": 40, "cx2": 610,
            "fh_ligne": 38, "gap": 30, "fy": 580,
        },
    },
    "twitter-banner": {
        "name": "X / Twitter Banner",
        "w": 1500, "h": 500,
        "ratio": "3:1",
        "desc": "Bannière X / Twitter",
        "colors": {"bg_top": (15, 15, 25), "bg_bot": (20, 25, 40), "gold": (212, 175, 55)},
        "layout": "banner",
        "sizes": {
            "titre": 36, "sous_titre": 18, "titre_cat": 22,
            "nom": 18, "marque": 12, "badge": 13, "footer": 10, "footer_bold": 12,
            "header_ht": 110, "fh_enTete": 15, "sy": 125, "cx1": 40, "cx2": 760,
            "fh_ligne": 32, "gap": 25, "fy": 450,
        },
    },
    "og-card": {
        "name": "OG Card / Link Preview",
        "w": 1200, "h": 675,
        "ratio": "16:9",
        "desc": "Aperçu lien (Open Graph) — sites, réseaux",
        "colors": {"bg_top": (15, 15, 25), "bg_bot": (20, 25, 40), "gold": (212, 175, 55)},
        "layout": "banner",
        "sizes": {
            "titre": 42, "sous_titre": 20, "titre_cat": 24,
            "nom": 20, "marque": 13, "badge": 14, "footer": 11, "footer_bold": 13,
            "header_ht": 150, "fh_enTete": 20, "sy": 170, "cx1": 40, "cx2": 610,
            "fh_ligne": 38, "gap": 30, "fy": 620,
        },
    },
    "linkedin-post": {
        "name": "LinkedIn Post",
        "w": 1200, "h": 627,
        "ratio": "~1.9:1",
        "desc": "Publication LinkedIn",
        "colors": {"bg_top": (15, 15, 25), "bg_bot": (20, 25, 40), "gold": (212, 175, 55)},
        "layout": "compact",
        "sizes": {
            "titre": 42, "sous_titre": 20, "titre_cat": 24,
            "nom": 20, "marque": 13, "badge": 14, "footer": 11, "footer_bold": 13,
            "header_ht": 140, "fh_enTete": 20, "sy": 160, "cx1": 40, "cx2": 610,
            "fh_ligne": 38, "gap": 30, "fy": 580,
        },
    },
    "pinterest-pin": {
        "name": "Pinterest Pin",
        "w": 1000, "h": 1500,
        "ratio": "2:3",
        "desc": "Pin Pinterest (vertical)",
        "colors": {"bg_top": (15, 15, 25), "bg_bot": (20, 25, 40), "gold": (212, 175, 55)},
        "layout": "2cols",
        "sizes": {
            "titre": 72, "sous_titre": 28, "titre_cat": 38,
            "nom": 30, "marque": 18, "badge": 20, "footer": 16, "footer_bold": 18,
            "header_ht": 280, "fh_enTete": 38, "sy": 320, "cx1": 60, "cx2": 510,
            "fh_ligne": 62, "gap": 50, "fy": 1430,
        },
    },
    "youtube-thumbnail": {
        "name": "YouTube Miniature",
        "w": 1280, "h": 720,
        "ratio": "16:9",
        "desc": "Miniature YouTube",
        "colors": {"bg_top": (15, 15, 25), "bg_bot": (20, 25, 40), "gold": (212, 175, 55)},
        "layout": "banner",
        "sizes": {
            "titre": 46, "sous_titre": 22, "titre_cat": 26,
            "nom": 22, "marque": 14, "badge": 15, "footer": 12, "footer_bold": 14,
            "header_ht": 160, "fh_enTete": 22, "sy": 180, "cx1": 45, "cx2": 660,
            "fh_ligne": 40, "gap": 30, "fy": 660,
        },
    },
}


# ============================================================
#  POLICES
# ============================================================

def _find_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Trouve une police avec fallback vers les polices système."""
    candidates = {
        "DejaVuSerif-Bold": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",    # Ubuntu/Debian
            "/usr/share/fonts/dejavu/DejaVuSerif-Bold.ttf",              # Fedora
            "/usr/share/fonts/TTF/DejaVuSerif-Bold.ttf",                 # Arch
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",          # fallback
        ],
        "DejaVuSerif": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/TTF/DejaVuSerif.ttf",
        ],
        "DejaVuSans-Bold": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ],
        "DejaVuSans": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ],
    }
    paths = candidates.get(name, [])
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _charger_polices(fmt: dict) -> dict[str, ImageFont.FreeTypeFont]:
    """Charge les polices adaptées à la taille du format."""
    sz = fmt["sizes"]
    return {
        "titre": _find_font("DejaVuSerif-Bold", sz["titre"]),
        "sous_titre": _find_font("DejaVuSerif", sz["sous_titre"]),
        "titre_categorie": _find_font("DejaVuSerif-Bold", sz["titre_cat"]),
        "nom_parfum": _find_font("DejaVuSans-Bold", sz["nom"]),
        "nom_marque": _find_font("DejaVuSans-Bold", sz["marque"]),
        "badge": _find_font("DejaVuSans-Bold", sz["badge"]),
        "footer": _find_font("DejaVuSans", sz["footer"]),
        "footer_bold": _find_font("DejaVuSans-Bold", sz["footer_bold"]),
    }


# ============================================================
#  DESSIN
# ============================================================

def _dessiner_section(
    draw: ImageDraw.ImageDraw,
    titre: str,
    items: list[Parfum],
    x: int,
    y_start: int,
    polices: dict,
    hauteur_ligne: int = 72,
) -> int:
    """Dessine une section de parfums. Retourne le y après la section + gap."""
    y = y_start
    draw.text((x, y), titre, fill="#1a1a2e", font=polices["titre_categorie"])
    y += 58

    for p in items:
        draw.text((x, y), p["marque"].upper(), fill="#d4af37", font=polices["nom_marque"])
        y += 30
        bbox = draw.textbbox((0, 0), p["nom"], font=polices["nom_parfum"])
        nw = bbox[2] - bbox[0]
        draw.text((x, y), p["nom"], fill="#1a1a2e", font=polices["nom_parfum"])
        if p["stock"] <= 2:
            texte_badge = f' ⚡ x{p["stock"]}'
            draw.text((x + nw + 16, y + 4), texte_badge, fill="#e17055", font=polices["badge"])
        y += hauteur_ligne

    return y + 60  # gap


# ============================================================
#  GÉNÉRATION PRINCIPALE
# ============================================================

def generate(output_path: str = OUTPUT, format_name: str = "whatsapp-status") -> str:
    """
    Génère une image avec le format spécifié.
    
    Args:
        output_path: Chemin de sortie
        format_name: Clé dans FORMATS (ex: "whatsapp-status", "instagram-square", etc.)
    
    Returns:
        Chemin de l'image générée
    """
    fmt = FORMATS.get(format_name)
    if not fmt:
        print(f"⚠️  Format '{format_name}' inconnu, utilisation du défaut")
        fmt = FORMATS["whatsapp-status"]

    db = load_db()
    parfums = db["parfums"]
    dispos = [p for p in parfums if p["stock"] > 0]
    hommes = [p for p in dispos if p["categorie"] == "Homme"]
    femmes = [p for p in dispos if p["categorie"] == "Femme"]
    mixtes = [p for p in dispos if p["categorie"] == "Mixte"]

    W, H = fmt["w"], fmt["h"]
    sz = fmt["sizes"]
    col = fmt["colors"]

    img = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    polices = _charger_polices(fmt)

    # Fond : gradient du haut vers le bas
    bg_top, bg_bot = col["bg_top"], col["bg_bot"]
    for y in range(sz["header_ht"]):
        r = int(bg_top[0] + (bg_bot[0] - bg_top[0]) * y / sz["header_ht"])
        g = int(bg_top[1] + (bg_bot[1] - bg_top[1]) * y / sz["header_ht"])
        b = int(bg_top[2] + (bg_bot[2] - bg_top[2]) * y / sz["header_ht"])
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    draw.line([(0, sz["header_ht"]), (W, sz["header_ht"])], fill=col["gold"], width=3)

    # Titre principal
    titre = "✦ COLLECTION PRIVÉE ✦"
    bbox = draw.textbbox((0, 0), titre, font=polices["titre"])
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, sz["fh_enTete"]), titre, fill="#d4af37", font=polices["titre"])

    # Ligne décorative
    mid_y = sz["fh_enTete"] + 83
    draw.line([(W // 2 - 60, mid_y), (W // 2 + 60, mid_y)], fill=col["gold"], width=2)

    # Sous-titre
    ss = "PARFUMERIE DE LUXE"
    bbox = draw.textbbox((0, 0), ss, font=polices["sous_titre"])
    sw = bbox[2] - bbox[0]
    draw.text(((W - sw) // 2, mid_y + 22), ss, fill="#c0b8a8", font=polices["sous_titre"])

    # Compteur
    compteur = f"{len(dispos)} PARFUMS DISPONIBLES"
    bbox = draw.textbbox((0, 0), compteur, font=polices["sous_titre"])
    cw = bbox[2] - bbox[0]
    draw.text(((W - cw) // 2, mid_y + 74), compteur, fill="#d4af37", font=polices["sous_titre"])

    # Layout : 2 colonnes ou compact
    cx1, cx2 = sz["cx1"], sz["cx2"]
    sy = sz["sy"]

    y1 = _dessiner_section(draw, "HOMME", hommes, cx1, sy, polices, sz["fh_ligne"])
    y1 = _dessiner_section(draw, "UNISEXE", mixtes, cx1, y1, polices, sz["fh_ligne"])
    _dessiner_section(draw, "FEMME", femmes, cx2, sy, polices, sz["fh_ligne"])

    # Footer
    fy = sz["fy"]
    draw.line([(100, fy), (W - 100, fy)], fill=col["gold"], width=2)

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
    print(f"🖼️  Visuel généré [{format_name}] : {output_path} ({W}×{H})")
    return output_path
