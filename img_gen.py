#!/usr/bin/env python3
"""
Génération d'images — Parfums Collection Privée.
Deux modes :
  - Pillow : dessin 100% manuel (mode "pillow", défaut)
  - IA : fond généré par IA + overlay texte

Moteur de layout dynamique : les polices, colonnes et espacements
s'adaptent automatiquement aux dimensions du format choisi.
"""

import json, os, datetime, math, io
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

from db import load_db, Database, Parfum

DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(DIR, "whatsapp-status.jpg")

# ============================================================
#  CREDENTIALS IA (chargés depuis ai_config.json)
# ============================================================
_AI_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_config.json")
_CLOUDFLARE_ACCOUNT = ""
_CLOUDFLARE_TOKEN = ""
_HF_TOKEN = ""

def _load_credentials():
    global _CLOUDFLARE_ACCOUNT, _CLOUDFLARE_TOKEN, _HF_TOKEN
    if not os.path.exists(_AI_CONFIG_PATH):
        return False
    try:
        with open(_AI_CONFIG_PATH) as f:
            cfg = json.load(f)
        _CLOUDFLARE_ACCOUNT = cfg.get("cloudflare", {}).get("account_id", "")
        _CLOUDFLARE_TOKEN = cfg.get("cloudflare", {}).get("api_token", "")
        _HF_TOKEN = cfg.get("huggingface", {}).get("api_token", "")
        return bool(_CLOUDFLARE_ACCOUNT and _CLOUDFLARE_TOKEN and _HF_TOKEN)
    except Exception:
        return False

_load_credentials()

MODELS = {
    "pillow": {"name": "Pillow (dessin manuel)", "desc": "Pas d'IA, texte sur fond dégradé"},
    "custom": {"name": "Mon fond", "desc": "Utilise ton propre fond (upload depuis le dashboard)"},
    "cloudflare": {"name": "Cloudflare SDXL", "desc": "IA gratuite, ~10-20 img/jour, bonne qualité"},
    "huggingface": {"name": "Hugging Face FLUX", "desc": "IA gratuite, FLUX.1-schnell, excellente qualité"},
    "pollinations": {"name": "Pollinations", "desc": "IA gratuite, illimité, qualité standard"},
}

CUSTOM_BG_PATH = os.path.join(DIR, "custom-bg.jpg")


# ============================================================
#  FORMATS DISPONIBLES
# ============================================================
FORMATS = {
    "whatsapp-status":  {"name": "WhatsApp Status", "w": 1080, "h": 1920, "ratio": "9:16",  "desc": "Status WhatsApp et stories Instagram"},
    "instagram-square": {"name": "Instagram Carré",  "w": 1080, "h": 1080, "ratio": "1:1",  "desc": "Publication Instagram feed"},
    "instagram-story":  {"name": "Instagram Story",  "w": 1080, "h": 1920, "ratio": "9:16",  "desc": "Story Instagram"},
    "facebook-post":    {"name": "Facebook Post",    "w": 1200, "h": 630,  "ratio": "~2:1", "desc": "Partage Facebook"},
    "twitter-banner":   {"name": "X Banner",         "w": 1500, "h": 500,  "ratio": "3:1",  "desc": "Bannière X / Twitter"},
    "linkedin-post":    {"name": "LinkedIn Post",    "w": 1200, "h": 627,  "ratio": "~1.9:1", "desc": "Publication LinkedIn"},
    "pinterest-pin":    {"name": "Pinterest Pin",    "w": 1000, "h": 1500, "ratio": "2:3",  "desc": "Pin Pinterest"},
    "youtube-thumbnail":{"name": "YouTube Miniature", "w": 1280, "h": 720,  "ratio": "16:9", "desc": "Miniature YouTube"},
    "og-card":          {"name": "OG Card",          "w": 1200, "h": 675,  "ratio": "16:9", "desc": "Aperçu lien Open Graph"},
}


# ============================================================
#  POLICES
# ============================================================

def _find_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Trouve une police avec fallback multi-distro."""
    candidates = {
        "Serif-Bold": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        ],
        "Serif": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/TTF/DejaVuSerif.ttf",
        ],
        "Sans-Bold": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ],
        "Sans": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ],
    }
    for path in candidates.get(name, []):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# ============================================================
#  MOTEUR DE LAYOUT DYNAMIQUE
# ============================================================

class LayoutEngine:
    """
    Calcule automatiquement :
    - Nombre de colonnes (selon ratio de l'image)
    - Tailles de police (selon W, H)
    - Hauteur de ligne (selon espace disponible)
    - Espacement (selon densité d'items)
    """

    def __init__(self, W: int, H: int, nb_items: int):
        self.W = W
        self.H = H
        self.nb_items = nb_items
        self.ratio = W / H

        # Nombre de colonnes selon le ratio
        if self.ratio >= 2.5:      # Banner X (3:1) → 4 colonnes
            self.ncols = 4
        elif self.ratio >= 1.7:    # Facebook, YouTube → 3 colonnes
            self.ncols = 3
        elif self.ratio >= 1.2:    # LinkedIn (1.9:1) → 3 colonnes
            self.ncols = 3
        elif self.ratio >= 0.6:    # 1:1, 9:16 → 2 colonnes
            self.ncols = 2
        else:                      # Pinterest (2:3) → 2 colonnes
            self.ncols = 2

        # Si trop peu d'items, réduire le nombre de colonnes
        max_ncols = min(self.ncols, nb_items)
        self.ncols = max(1, max_ncols)

        # Hauteurs relatives
        self.header_pct = 0.18 if self.ratio < 1.0 else 0.22 if self.ratio < 2.0 else 0.30
        self.footer_pct = 0.07 if self.ratio < 1.0 else 0.10 if self.ratio < 2.0 else 0.14

        self.header_h = int(H * self.header_pct)
        self.footer_h = int(H * self.footer_pct)

        # Espace disponible pour la liste
        self.avail_y = H - self.header_h - self.footer_h
        # Marge horizontale
        self.margin_x = int(W * 0.04)
        # Largeur de colonne
        if self.ncols > 1:
            self.gap_x = int(W * 0.03)
            self.col_w = (W - 2 * self.margin_x - (self.ncols - 1) * self.gap_x) // self.ncols
        else:
            self.gap_x = 0
            self.col_w = W - 2 * self.margin_x

        # Items par colonne (équilibré)
        self.per_col = math.ceil(nb_items / self.ncols)

        # Hauteur max dispo par item
        self.max_item_h = self.avail_y // self.per_col

        # Font sizes : calculées à partir des dimensions
        # Référence : 1080×1920 → titre=82
        scale_w = W / 1080
        scale_h = H / 1920
        scale = min(scale_w, scale_h)  # Facteur d'échelle général

        # Tailles de police
        self.font_titre = max(20, int(82 * scale))
        self.font_sstitre = max(12, int(32 * scale))
        self.font_cat = max(16, int(44 * scale))
        self.font_nom = max(12, int(34 * scale))
        self.font_marque = max(10, int(22 * scale))
        self.font_badge = max(10, int(24 * scale))
        self.font_footer = max(8, int(20 * scale))
        self.font_footer_bold = max(10, int(22 * scale))

        # Hauteur de ligne pour chaque item
        # Au moins assez grand pour nom + marque
        min_item_h = int(self.font_marque * 2 + self.font_nom * 1.4)
        self.item_h = max(min_item_h, self.max_item_h)
        # Si item_h est trop grand, on réduit les fontes
        if self.item_h > min_item_h * 3:
            self.item_h = min_item_h * 2
            # On réduit proportions
            factor = math.sqrt(min_item_h * 2 / self.max_item_h)
            self.font_nom = max(10, int(self.font_nom * factor))
            self.font_marque = max(8, int(self.font_marque * factor))

        # Espacement vertical entre catégories
        self.gap_y = max(8, int(40 * scale))

        # Position de départ Y
        self.start_y = self.header_h + int(H * 0.02)

    def get_fonts(self) -> dict:
        return {
            "titre": _find_font("Serif-Bold", self.font_titre),
            "sstitre": _find_font("Serif", self.font_sstitre),
            "cat": _find_font("Serif-Bold", self.font_cat),
            "nom": _find_font("Sans-Bold", self.font_nom),
            "marque": _find_font("Sans-Bold", self.font_marque),
            "badge": _find_font("Sans-Bold", self.font_badge),
            "footer": _find_font("Sans", self.font_footer),
            "footer_bold": _find_font("Sans-Bold", self.font_footer_bold),
        }

    def column_x(self, col_idx: int) -> int:
        """Retourne la position X du début d'une colonne."""
        return self.margin_x + col_idx * (self.col_w + self.gap_x)


# ============================================================
#  DESSIN : EN-TÊTE
# ============================================================

def _draw_header(draw, W, layout, gold):
    """Dessine l'en-tête gradué + titre."""
    # Gradient d'en-tête
    for y in range(layout.header_h):
        progress = y / layout.header_h
        r = int(15 + (20 - 15) * progress)
        g = int(15 + (25 - 15) * progress)
        b = int(25 + (40 - 25) * progress)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Ligne dorée
    draw.line([(0, layout.header_h), (W, layout.header_h)], fill=gold, width=max(1, int(3 * W/1080)))

    # Titre principal
    titre = "✦ COLLECTION PRIVÉE ✦"
    bbox = draw.textbbox((0, 0), titre, font=layout.get_fonts()["titre"])
    tw = bbox[2] - bbox[0]
    tx = (W - tw) // 2
    ty = int(layout.header_h * 0.18)
    draw.text((tx, ty), titre, fill="#d4af37", font=layout.get_fonts()["titre"])

    # Ligne décorative sous le titre
    mid_y = ty + layout.font_titre + int(10 * W/1080)
    line_len = max(40, int(120 * W/1080))
    draw.line([(W//2 - line_len//2, mid_y), (W//2 + line_len//2, mid_y)], fill=gold, width=max(1, int(2 * W/1080)))

    # Sous-titre
    ss = "PARFUMERIE DE LUXE"
    bbox = draw.textbbox((0, 0), ss, font=layout.get_fonts()["sstitre"])
    sw = bbox[2] - bbox[0]
    draw.text(((W - sw) // 2, mid_y + int(8 * W/1080)), ss, fill="#c0b8a8", font=layout.get_fonts()["sstitre"])


# ============================================================
#  REDISTRIBUTION ÉQUILIBRÉE DES ITEMS DANS LES COLONNES
# ============================================================

def _distribuer_colonnes(hommes, femmes, mixtes, ncols):
    """
    Distribue TOUS les items de façon équilibrée entre les colonnes
    (sans respecter les catégories).
    """
    tous = []
    for p in sorted(hommes, key=lambda x: (-x["stock"], x["nom"])):
        tous.append({"parfum": p, "cat": "HOMME"})
    for p in sorted(femmes, key=lambda x: (-x["stock"], x["nom"])):
        tous.append({"parfum": p, "cat": "FEMME"})
    for p in sorted(mixtes, key=lambda x: (-x["stock"], x["nom"])):
        tous.append({"parfum": p, "cat": "MIXTE"})

    # Distribution équilibrée (round-robin)
    colonnes = [[] for _ in range(ncols)]
    for i, item in enumerate(tous):
        colonnes[i % ncols].append(item)
    return colonnes


# ============================================================
#  DESSIN : LISTE PARFUMS
# ============================================================

def _draw_liste(draw, layout, hommes, femmes, mixtes, gold):
    """Dessine la liste des parfums avec layout adaptatif."""
    fonts = layout.get_fonts()
    colonnes = _distribuer_colonnes(hommes, femmes, mixtes, layout.ncols)

    for col_idx, items in enumerate(colonnes):
        if not items:
            continue
        x = layout.column_x(col_idx)
        y = layout.start_y
        col_w = layout.col_w
        prev_cat = None

        for item in items:
            p = item["parfum"]
            cat = item["cat"]

            # Titre de catégorie (uniquement si changement)
            if cat != prev_cat:
                draw.text((x, y), cat, fill="#d4af37", font=fonts["cat"])
                y += layout.font_cat + int(6 * layout.W/1080)
                prev_cat = cat

            # Marque
            draw.text((x, y), p["marque"].upper(), fill="#d4af37", font=fonts["marque"])
            y += layout.font_marque + int(4 * layout.W/1080)

            # Nom + badge stock bas
            nom = p["nom"]
            bbox = draw.textbbox((0, 0), nom, font=fonts["nom"])
            nw = bbox[2] - bbox[0]

            # Tronquer si dépasse la colonne
            if nw > col_w - 40:
                while nw > col_w - 40 and len(nom) > 3:
                    nom = nom[:-1]
                    bbox = draw.textbbox((0, 0), nom, font=fonts["nom"])
                    nw = bbox[2] - bbox[0]
                nom += "…"

            draw.text((x, y), nom, fill="#e8e0d4", font=fonts["nom"])

            if p["stock"] <= 2:
                badge = f' ⚡x{p["stock"]}'
                draw.text((x + nw + int(12 * layout.W/1080), y + int(4 * layout.W/1080)),
                          badge, fill="#e17055", font=fonts["badge"])

            y += layout.item_h


# ============================================================
#  DESSIN : PIED DE PAGE
# ============================================================

def _draw_footer(draw, W, H, layout, gold):
    """Dessine le footer."""
    fy = H - layout.footer_h
    line_y = fy + int(layout.footer_h * 0.10)
    draw.line([(int(50 * W/1080), line_y), (W - int(50 * W/1080), line_y)], fill=gold, width=max(1, int(2 * W/1080)))

    f1 = "Disponibilité sous réserve de vente"
    bbox = draw.textbbox((0, 0), f1, font=layout.get_fonts()["footer"])
    fw = bbox[2] - bbox[0]
    draw.text(((W - fw) // 2, line_y + int(12 * W/1080)), f1, fill="#aaa", font=layout.get_fonts()["footer"])

    f2 = "@collection.privee"
    bbox = draw.textbbox((0, 0), f2, font=layout.get_fonts()["footer_bold"])
    f2w = bbox[2] - bbox[0]
    draw.text(((W - f2w) // 2, line_y + int(int(32 * W/1080))), f2, fill="#d4af37", font=layout.get_fonts()["footer_bold"])


# ============================================================
#  GÉNÉRATION IA : FOND
# ============================================================

def _generate_ai_background(model: str, prompt: str, W: int, H: int) -> Optional[str]:
    """
    Génère un fond via l'IA choisie.
    Retourne le chemin de l'image ou None en cas d'échec.
    Pour le modèle 'custom', retourne le chemin du fond uploadé s'il existe.
    """
    import requests, tempfile

    if model == "pillow":
        return None  # Pas d'IA, dessin manuel

    # Modèle "custom" = utiliser le fond uploadé par l'utilisateur
    if model == "custom":
        if os.path.exists(CUSTOM_BG_PATH):
            return CUSTOM_BG_PATH
        return None

    native_w, native_h = 1024, 1024  # Taille native

    if model == "cloudflare":
        url = (f"https://api.cloudflare.com/client/v4/accounts/"
               f"{_CLOUDFLARE_ACCOUNT}/ai/run/"
               f"@cf/stabilityai/stable-diffusion-xl-base-1.0")
        headers = {"Authorization": f"Bearer {_CLOUDFLARE_TOKEN}", "Content-Type": "application/json"}
        payload = {"prompt": prompt, "width": native_w, "height": native_h}
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                path = os.path.join(DIR, ".cache_bg.png")
                with open(path, "wb") as f:
                    f.write(resp.content)
                return path
        except Exception:
            return None

    elif model == "huggingface":
        url = ("https://router.huggingface.co/hf-inference/models/"
               "black-forest-labs/FLUX.1-schnell")
        headers = {"Authorization": f"Bearer {_HF_TOKEN}", "Content-Type": "application/json"}
        payload = {"inputs": prompt, "parameters": {"width": native_w, "height": native_h}}
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=90)
            if resp.status_code == 200:
                path = os.path.join(DIR, ".cache_bg.png")
                with open(path, "wb") as f:
                    f.write(resp.content)
                return path
        except Exception:
            return None

    elif model == "pollinations":
        url = (f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
               f"?width={native_w}&height={native_h}&nologo=true")
        try:
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200:
                path = os.path.join(DIR, ".cache_bg.png")
                with open(path, "wb") as f:
                    f.write(resp.content)
                return path
        except Exception:
            return None

    return None


# ============================================================
#  GÉNÉRATION PRINCIPALE
# ============================================================

def generate(output_path: str = OUTPUT, format_name: str = "whatsapp-status",
             model: str = "pillow", ai_prompt: str = "") -> str:
    """
    Génère une image avec le format et le modèle spécifiés.

    Args:
        output_path: Chemin de sortie
        format_name: Clé dans FORMATS
        model: "pillow" | "cloudflare" | "huggingface" | "pollinations"
        ai_prompt: Prompt pour l'IA (ignoré si model="pillow")
    """
    fmt = FORMATS.get(format_name)
    if not fmt:
        fmt = FORMATS["whatsapp-status"]

    db = load_db()
    parfums = db["parfums"]
    dispos = [p for p in parfums if p["stock"] > 0]
    hommes = [p for p in dispos if p["categorie"] == "Homme"]
    femmes = [p for p in dispos if p["categorie"] == "Femme"]
    mixtes = [p for p in dispos if p["categorie"] == "Mixte"]

    W, H = fmt["w"], fmt["h"]
    gold = (212, 175, 55)
    layout = LayoutEngine(W, H, len(dispos))

    # --- Fond : IA ou Pillow ---
    bg_path = None
    if model != "pillow":
        if not ai_prompt:
            # Prompt par défaut selon le format
            if format_name in ("whatsapp-status", "instagram-story", "pinterest-pin", "instagram-square"):
                ai_prompt = ("Luxury perfume background, dark navy and black gradient, "
                            "elegant golden geometric lines, subtle sparkle particles, "
                            "warm amber glow, velvet texture, premium fragrance advertising, "
                            "negative space in center, no text, no bottles")
            elif format_name in ("twitter-banner", "facebook-post", "linkedin-post"):
                ai_prompt = ("Luxury perfume banner, dark gold and mahogany tones, "
                            "elegant arabesque patterns, warm amber lighting, "
                            "premium fragrance advertising, 8K, no text, no bottles")
            else:
                ai_prompt = ("Luxury perfume background, dark elegant tones, "
                            "gold accents, sophisticated atmosphere, "
                            "negative space, no text, no bottles")

        bg_path = _generate_ai_background(model, ai_prompt, W, H)

    # --- Création de l'image ---
    if bg_path and os.path.exists(bg_path):
        try:
            bg = Image.open(bg_path).convert("RGB")
            bg = bg.resize((W, H), Image.LANCZOS)
            img = bg
        except Exception:
            img = Image.new("RGB", (W, H), (15, 15, 25))
    else:
        # Fallback : fond dégradé progressive
        img = Image.new("RGB", (W, H), (15, 15, 25))
        gradient = ImageDraw.Draw(img)
        for y in range(H):
            progress = y / H
            r = int(15 + (25 - 15) * progress)
            g = int(15 + (30 - 15) * progress)
            b = int(20 + (45 - 20) * progress)
            gradient.line([(0, y), (W, y)], fill=(r, g, b))

    draw = ImageDraw.Draw(img)

    # --- Overlay semi-transparent pour lisibilité ---
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    # Top overlay
    for y in range(layout.header_h + 30):
        alpha = max(0, min(200, int(200 * (1 - y / (layout.header_h + 30)))))
        overlay_draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    # Bottom overlay
    bottom_start = H - layout.footer_h - 30
    for y in range(bottom_start, H):
        alpha = max(0, min(200, int(200 * (y - bottom_start) / (H - bottom_start))))
        overlay_draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    # Central subtle overlay
    for y in range(layout.header_h + 30, H - layout.footer_h - 30):
        if y % 2 == 0:  # 1 ligne sur 2 pour économie
            overlay_draw.line([(0, y), (W, y)], fill=(0, 0, 0, 30))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # --- Header + liste + footer ---
    _draw_header(draw, W, layout, gold)
    _draw_liste(draw, layout, hommes, femmes, mixtes, gold)
    _draw_footer(draw, W, H, layout, gold)

    # --- Sauvegarde ---
    img.save(output_path, "JPEG", quality=95)
    model_label = MODELS.get(model, {}).get("name", model)
    print(f"🖼️  Visuel généré [{fmt['name']}] [{model_label}] : {output_path} ({W}×{H})")
    return output_path


# ============================================================
#  CLI
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Générer un visuel Collection Privée")
    parser.add_argument("--format", default="whatsapp-status", choices=list(FORMATS.keys()), help="Format d'image")
    parser.add_argument("--model", default="pillow", choices=list(MODELS.keys()), help="Modèle de génération")
    parser.add_argument("--prompt", default="", help="Prompt IA (ignoré si model=pillow)")
    parser.add_argument("--output", default=OUTPUT, help="Chemin de sortie")
    args = parser.parse_args()
    generate(args.output, args.format, args.model, args.prompt)
