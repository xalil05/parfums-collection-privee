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
