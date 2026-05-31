#!/usr/bin/env python3
"""
Dashboard Web — Collection Privée
Serveur Flask avec API REST pour la gestion des parfums.

Usage :
  python3 app.py              # Démarrer le serveur (port 5000 par défaut)
  python3 app.py --port 8080  # Port personnalisé
  python3 app.py --host 0.0.0.0  # Accessible depuis le réseau local
"""

import os
import sys
import json
import datetime
import shutil
from pathlib import Path
from typing import Optional

from flask import Flask, render_template, request, jsonify, send_from_directory

# --- Configuration ---
DIR = Path(__file__).parent.resolve()
DB_PATH = DIR / "parfums.json"
TEMPLATES = DIR / "templates"
STATIC = DIR / "static"

app = Flask(
    __name__,
    template_folder=str(TEMPLATES),
    static_folder=str(STATIC),
)

# Créer les dossiers si besoin
TEMPLATES.mkdir(exist_ok=True)
STATIC.mkdir(exist_ok=True)


# ============================================================
#  COUCHE DONNÉES (copiée depuis db.py pour autonomie)
# ============================================================

def load_db() -> dict:
    """Charge la base JSON."""
    try:
        with open(DB_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"_meta": {"titre": "PARFUMS COLLECTION PRIVÉE"}, "parfums": [], "archive": []}
    except json.JSONDecodeError:
        return {"_meta": {"titre": "PARFUMS COLLECTION PRIVÉE", "erreur": "JSON corrompu"}, "parfums": [], "archive": []}


def save_db(db: dict) -> None:
    """Sauvegarde avec backup auto."""
    bkp = str(DB_PATH).replace(".json", f"-{datetime.date.today().isoformat()}.json")
    if not os.path.exists(bkp):
        shutil.copy2(DB_PATH, bkp)
    db.setdefault("_meta", {})
    db["_meta"]["total_parfums"] = len(db.get("parfums", []))
    db["_meta"]["total_stock"] = sum(p["stock"] for p in db.get("parfums", []))
    db["_meta"]["date_maj"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    db["_meta"]["derniere_modif"] = "Dashboard · " + datetime.datetime.now().strftime("%H:%M")
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def valider_parfum(data: dict) -> Optional[str]:
    """Valide les champs d'un parfum. Retourne None si OK, un message d'erreur sinon."""
    required = {"id", "nom", "stock", "marque", "type", "ml", "categorie"}
    missing = required - set(data.keys())
    if missing:
        return f"Champs obligatoires manquants : {', '.join(sorted(missing))}"
    if not data["id"].strip():
        return "L'ID ne peut pas être vide"
    if not data["nom"].strip():
        return "Le nom ne peut pas être vide"
    try:
        stock = int(data["stock"])
        if stock < 0:
            return "Le stock ne peut pas être négatif"
    except (ValueError, TypeError):
        return "Le stock doit être un nombre entier"
    try:
        ml = int(data.get("ml", 0))
        if ml <= 0:
            return "Le volume (ml) doit être un nombre positif"
    except (ValueError, TypeError):
        return "Le volume (ml) doit être un nombre entier"
    if data["categorie"] not in ("Homme", "Femme", "Mixte"):
        return "Catégorie invalide. Choisir Homme, Femme ou Mixte"
    return None


# ============================================================
#  ROUTES API
# ============================================================

@app.route("/")
def index():
    """Page principale du dashboard."""
    return render_template("dashboard.html")


@app.route("/api/stats")
def api_stats():
    """Statistiques globales."""
    db = load_db()
    parfums = db.get("parfums", [])
    total_stock = sum(p["stock"] for p in parfums)
    en_rupture = [p for p in parfums if p["stock"] <= 0]
    stock_bas = [p for p in parfums if 0 < p["stock"] <= 2]
    total_valeur = sum(p.get("prix", 0) * p["stock"] for p in parfums if p["stock"] > 0)
    return jsonify({
        "total_parfums": len(parfums),
        "total_stock": total_stock,
        "en_rupture": len(en_rupture),
        "stock_bas": len(stock_bas),
        "total_valeur": total_valeur,
        "date_maj": db.get("_meta", {}).get("date_maj", ""),
        "hommes": len([p for p in parfums if p["categorie"] == "Homme"]),
        "femmes": len([p for p in parfums if p["categorie"] == "Femme"]),
        "mixtes": len([p for p in parfums if p["categorie"] == "Mixte"]),
        "en_rupture_liste": [{"id": p["id"], "nom": p["nom"], "marque": p["marque"]} for p in en_rupture],
        "stock_bas_liste": [{"id": p["id"], "nom": p["nom"], "marque": p["marque"], "stock": p["stock"]} for p in stock_bas],
    })


@app.route("/api/parfums")
def api_liste_parfums():
    """Liste complète des parfums."""
    db = load_db()
    return jsonify(db.get("parfums", []))


@app.route("/api/parfums/<parfum_id>")
def api_parfum(parfum_id: str):
    """Détail d'un parfum."""
    db = load_db()
    for p in db.get("parfums", []):
        if p["id"] == parfum_id:
            return jsonify(p)
    return jsonify({"error": "Parfum introuvable"}), 404


@app.route("/api/parfums", methods=["POST"])
def api_ajouter_parfum():
    """Ajouter un nouveau parfum."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données JSON requises"}), 400

    # Validation
    erreur = valider_parfum(data)
    if erreur:
        return jsonify({"error": erreur}), 400

    # Vérifier ID unique
    db = load_db()
    for p in db.get("parfums", []):
        if p["id"] == data["id"]:
            return jsonify({"error": f"Un parfum avec l'ID '{data['id']}' existe déjà"}), 409

    nouveau = {
        "id": data["id"],
        "nom": data["nom"],
        "marque": data.get("marque", ""),
        "type": data.get("type", "EDP"),
        "ml": int(data.get("ml", 100)),
        "stock": int(data["stock"]),
        "prix": float(data.get("prix", 0)),
        "notes": data.get("notes", ""),
        "categorie": data.get("categorie", "Mixte"),
    }
    db["parfums"].append(nouveau)
    save_db(db)
    return jsonify({"success": True, "parfum": nouveau}), 201


@app.route("/api/parfums/<parfum_id>", methods=["PUT"])
def api_modifier_parfum(parfum_id: str):
    """Modifier un parfum existant."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données JSON requises"}), 400

    db = load_db()
    for idx, p in enumerate(db.get("parfums", [])):
        if p["id"] == parfum_id:
            # Mise à jour partielle (seulement les champs fournis)
            for field in ("nom", "marque", "type", "notes", "categorie"):
                if field in data:
                    db["parfums"][idx][field] = data[field]
            for field in ("ml", "stock"):
                if field in data:
                    try:
                        db["parfums"][idx][field] = int(data[field])
                    except (ValueError, TypeError):
                        return jsonify({"error": f"Le champ '{field}' doit être un nombre entier"}), 400
            if "prix" in data:
                try:
                    db["parfums"][idx]["prix"] = float(data["prix"])
                except (ValueError, TypeError):
                    return jsonify({"error": "Le prix doit être un nombre"}), 400
            if "stock" in data and db["parfums"][idx]["stock"] < 0:
                return jsonify({"error": "Le stock ne peut pas être négatif"}), 400

            save_db(db)
            return jsonify({"success": True, "parfum": db["parfums"][idx]})

    return jsonify({"error": "Parfum introuvable"}), 404


@app.route("/api/parfums/<parfum_id>", methods=["DELETE"])
def api_supprimer_parfum(parfum_id: str):
    """Supprimer (archiver) un parfum."""
    db = load_db()
    for idx, p in enumerate(db.get("parfums", [])):
        if p["id"] == parfum_id:
            archive = db.setdefault("archive", [])
            archive.append({**p, "raison_archive": "Supprimé via dashboard", "date_archive": datetime.datetime.now().isoformat()})
            db["parfums"].pop(idx)
            save_db(db)
            return jsonify({"success": True, "message": f"{p['nom']} archivé"})

    return jsonify({"error": "Parfum introuvable"}), 404


@app.route("/api/parfums/<parfum_id>/sell", methods=["POST"])
def api_vendre(parfum_id: str):
    """Vendre (décrémenter le stock)."""
    data = request.get_json() or {}
    qty = int(data.get("quantite", 1))
    if qty <= 0:
        return jsonify({"error": "La quantité doit être positive"}), 400

    db = load_db()
    for p in db.get("parfums", []):
        if p["id"] == parfum_id:
            if p["stock"] < qty:
                return jsonify({"error": f"Stock insuffisant : {p['stock']} disponible(s), {qty} demandé(s)"}), 400
            p["stock"] -= qty
            save_db(db)
            return jsonify({"success": True, "parfum": p, "vendu": qty})

    return jsonify({"error": "Parfum introuvable"}), 404


@app.route("/api/parfums/<parfum_id>/restock", methods=["POST"])
def api_restock(parfum_id: str):
    """Réapprovisionner (ajouter du stock)."""
    data = request.get_json() or {}
    qty = int(data.get("quantite", 1))
    if qty <= 0:
        return jsonify({"error": "La quantité doit être positive"}), 400

    db = load_db()
    for p in db.get("parfums", []):
        if p["id"] == parfum_id:
            p["stock"] += qty
            save_db(db)
            return jsonify({"success": True, "parfum": p, "ajoute": qty})

    return jsonify({"error": "Parfum introuvable"}), 404


@app.route("/api/archive")
def api_archive():
    """Liste des parfums archivés."""
    db = load_db()
    return jsonify(db.get("archive", []))


# ============================================================
#  GÉNÉRATION VISUEL + PROMPTS IA
# ============================================================

@app.route("/api/generate-visuel")
def api_generate_visuel():
    """Génère le visuel dans le format choisi et retourne l'image."""
    fmt = request.args.get("format", "whatsapp-status")
    try:
        from img_gen import generate as generate_image
        path = generate_image(str(DIR / "whatsapp-status.jpg"), format_name=fmt)
        return send_from_directory(str(DIR), "whatsapp-status.jpg", as_attachment=True, download_name=f"collection-privee-{fmt}.jpg")
    except Exception as e:
        return jsonify({"error": f"Erreur génération visuel : {e}"}), 500


@app.route("/api/generate-visuel-preview")
def api_generate_visuel_preview():
    """Génère le visuel dans le format choisi et retourne le chemin."""
    fmt = request.args.get("format", "whatsapp-status")
    try:
        from img_gen import generate as generate_image
        path = generate_image(str(DIR / "whatsapp-status.jpg"), format_name=fmt)
        return jsonify({"success": True, "path": "/api/visual-status", "format": fmt})
    except Exception as e:
        return jsonify({"error": f"Erreur génération visuel : {e}"}), 500


@app.route("/api/visual-status")
def api_visual_status():
    """Retourne l'image générée (statique)."""
    return send_from_directory(str(DIR), "whatsapp-status.jpg", mimetype="image/jpeg")


@app.route("/api/formats")
def api_formats():
    """Liste des formats d'image disponibles."""
    from img_gen import FORMATS
    data = {}
    for key, f in FORMATS.items():
        data[key] = {
            "name": f["name"],
            "w": f["w"],
            "h": f["h"],
            "ratio": f["ratio"],
            "desc": f["desc"],
        }
    return jsonify(data)


@app.route("/api/prompts")
def api_prompts():
    """Génère des prompts IA pour générateurs d'images."""
    db = load_db()
    parfums = db.get("parfums", [])
    dispos = [p for p in parfums if p["stock"] > 0]
    hommes = [p for p in dispos if p["categorie"] == "Homme"]
    femmes = [p for p in dispos if p["categorie"] == "Femme"]
    mixtes = [p for p in dispos if p["categorie"] == "Mixte"]

    # Extraire les notes dominantes
    toutes_notes = []
    for p in dispos:
        for n in p.get("notes", "").split(","):
            n = n.strip()
            if n and n not in toutes_notes:
                toutes_notes.append(n)
    notes_top = toutes_notes[:5] if toutes_notes else ["Vanille", "Ambre", "Oud"]

    marques = list(set(p["marque"] for p in dispos))
    top_marques = marques[:5]

    def _prompt_vibe(categorie, items, notes):
        items_str = " · ".join(p["nom"] for p in items[:5])
        notes_str = ", ".join(notes)
        return {
            "categorie": categorie,
            "count": len(items),
            "exemples": items_str,
            "notes": notes_str,
        }

    vibes = [
        _prompt_vibe("Homme", hommes, ["Cuir", "Bois", "Ambre", "Poivre", "Cèdre"]),
        _prompt_vibe("Femme", femmes, ["Vanille", "Rose", "Fleur d'oranger", "Tubéreuse", "Patchouli"]),
        _prompt_vibe("Mixte / Unisexe", mixtes, ["Oud", "Ambre", "Musc", "Safran", "Rose"]),
    ]

    # Prompts dédiés
    prompts = {
        "generaux": [
            {
                "plateforme": "Google ImageFX / Imagen",
                "style": "Photorealistic — Fond luxueux",
                "prompt": f"Ultra-realistic perfume collection background, dark mahogany and amber tones, elegant gold arabesque geometric patterns, subtle oud smoke wisps, scattered gold dust particles, velvet texture, warm ambient candlelight, sophisticated luxury fragrance presentation, 8K photorealistic commercial photography, negative space in center for text overlay, no text, no bottles",
            },
            {
                "plateforme": "Midjourney",
                "style": "Artistique — Ambiance orientale",
                "prompt": f"Luxury perfume boutique interior, dark navy and gold color scheme, opulent arabesque patterns, warm amber lighting, floating gold particles, velvet drapes, premium fragrance collection display, soft cinematic bokeh, rich textures, elegant and sophisticated mood --ar 9:16 --style raw --v 6",
            },
            {
                "plateforme": "DALL·E 3",
                "style": "Moderne minimaliste",
                "prompt": f"Minimalist luxury perfume background, dark gradient from navy to black, subtle gold foil geometric accents, elegant minimal composition, soft warm glow from below, premium cosmetic advertising style, clean and sophisticated, negative space for text, 16:9 aspect ratio",
            },
            {
                "plateforme": "Stable Diffusion / FLUX",
                "style": "Sombre & Dramatique",
                "prompt": f"(masterpiece:1.2), (photorealistic:1.3), dark luxury perfume collection, mahogany wood texture, gold leaf accents, smoke wisps, amber glow, velvet background, sophisticated fragrance advertising, 8K, dramatic lighting, rich deep colors, negative space centered, no text",
            },
        ],
        "par_categorie": [
            {
                "categorie": "Homme 💼",
                "prompt": f"Dark and sophisticated men's perfume collection, rich wood textures, leather accents, amber and tobacco tones, black and gold color scheme, masculine elegance, premium fragrance advertising, 8K photorealistic, dramatic chiaroscuro lighting, luxury lifestyle photography, centered composition for text overlay, no perfume bottles",
                "marques": top_marques[:3],
            },
            {
                "categorie": "Femme 👗",
                "prompt": f"Elegant women's luxury perfume collection, soft pink and rose gold tones, floral accents, vanilla and gourmand warmth, silk and velvet textures, feminine sophistication, premium beauty editorial style, soft dreamy lighting, 8K commercial photography, delicate and refined atmosphere, centered composition for text",
                "marques": top_marques[:3],
            },
            {
                "categorie": "Mixte / Unisexe 🔀",
                "prompt": f"Modern unisex luxury fragrance collection, amber and oud tones, warm golden hour lighting, contemporary minimal aesthetic, marble and brass textures, sophisticated and inclusive vibe, premium editorial perfume photography, 8K, balanced masculine and feminine elements, centered negative space for text overlay",
                "marques": top_marques[:3],
            },
        ],
        "whatsapp_status": [
            {
                "plateforme": "Fond pour visuel WhatsApp (9:16)",
                "style": "Luxueux sombre",
                "prompt": f"Luxury perfume background for WhatsApp status, 9:16 vertical format, dark navy to black gradient, elegant golden geometric lines, subtle sparkle particles, warm amber glow at center, premium fragrance advertising style, velvet texture, 8K, sophisticated and exclusive mood, large empty space in center for perfume list text overlay, no perfume bottles, no text",
            },
        ],
        "vibes": vibes,
        "stats": {
            "total_parfums": len(dispos),
            "total_stock": sum(p["stock"] for p in dispos),
            "marques": top_marques,
            "notes_dominantes": notes_top if notes_top else ["Vanille", "Ambre"],
        },
    }

    return jsonify(prompts)


# ============================================================
#  LANCEMENT
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Dashboard Collection Privée")
    parser.add_argument("--host", default="127.0.0.1", help="Adresse d'écoute")
    parser.add_argument("--port", type=int, default=5000, help="Port d'écoute")
    parser.add_argument("--debug", action="store_true", help="Mode debug Flask")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════╗
║  COLLECTION PRIVÉE — DASHBOARD           ║
║  Serveur : http://{args.host}:{args.port}           ║
║  Données : {DB_PATH}  ║
╚══════════════════════════════════════════╝
""")
    app.run(host=args.host, port=args.port, debug=args.debug)
