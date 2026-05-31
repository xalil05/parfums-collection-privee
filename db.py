#!/usr/bin/env python3
"""
Couche d'accès aux données — Parfums Collection Privée
CRUD sur parfums.json avec backup automatique et validation.
"""

import json
import os
import shutil
import datetime
from typing import Any, Optional

# --- Chemins ---
DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DIR, "parfums.json")


# --- Types ---

Parfum = dict[str, Any]
Database = dict[str, Any]


# --- Fonctions internes ---

def _backup(db_path: str) -> None:
    """Crée un backup quotidien si inexistant."""
    today = datetime.date.today().isoformat()
    bkp = db_path.replace(".json", f"-{today}.json")
    if not os.path.exists(bkp):
        shutil.copy2(db_path, bkp)


def _compute_meta(db: Database) -> None:
    """Re-calcule les métadonnées avant sauvegarde."""
    p = db.get("parfums", [])
    db.setdefault("_meta", {})
    db["_meta"]["total_parfums"] = len(p)
    db["_meta"]["total_stock"] = sum(item["stock"] for item in p)
    db["_meta"]["date_maj"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    db["_meta"]["derniere_modif"] = "Mise à jour automatique"


# --- API publique ---

def load_db() -> Database:
    """Charge et retourne la base JSON complète."""
    try:
        with open(DB_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Base de données introuvable : {DB_PATH}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Fichier JSON corrompu : {e}")


def save_db(db: Database) -> None:
    """Sauvegarde la base avec backup auto et mise à jour des métadonnées."""
    _backup(DB_PATH)
    _compute_meta(db)
    try:
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
    except OSError as e:
        raise OSError(f"Impossible d'écrire la base : {e}")


def find_parfum(parfums: list[Parfum], parfum_id: str) -> Optional[Parfum]:
    """Cherche un parfum par son ID. Retourne None si introuvable."""
    for p in parfums:
        if p["id"] == parfum_id:
            return p
    return None


def set_stock(parfum_id: str, nouvelle_valeur: int) -> str:
    """Fixer le stock d'un parfum à une valeur exacte."""
    if nouvelle_valeur < 0:
        raise ValueError("Le stock ne peut pas être négatif")

    db = load_db()
    p = find_parfum(db["parfums"], parfum_id)
    if p is None:
        raise KeyError(f"Parfum introuvable : {parfum_id}")

    ancien = p["stock"]
    p["stock"] = nouvelle_valeur
    save_db(db)
    return f"{p['marque']} — {p['nom']}: {ancien} → {nouvelle_valeur}"


def add_stock(parfum_id: str, quantite: int) -> str:
    """Ajouter (ou retirer si négatif) du stock à un parfum."""
    db = load_db()
    p = find_parfum(db["parfums"], parfum_id)
    if p is None:
        raise KeyError(f"Parfum introuvable : {parfum_id}")

    ancien = p["stock"]
    nouveau = ancien + quantite
    if nouveau < 0:
        raise ValueError(
            f"Stock insuffisant pour {p['nom']} : {ancien} - {abs(quantite)}"
        )
    p["stock"] = nouveau
    save_db(db)
    return f"{p['marque']} — {p['nom']}: {ancien} → {nouveau}"


def sell(parfum_id: str, quantite: int = 1) -> str:
    """Raccourci pour vendre = décrémenter le stock."""
    return add_stock(parfum_id, -quantite)


def add_parfum(data: Parfum) -> str:
    """Ajouter un nouveau parfum à la base."""
    required = {"id", "nom", "stock"}
    missing = required - set(data.keys())
    if missing:
        raise KeyError(f"Champs obligatoires manquants : {', '.join(sorted(missing))}")

    db = load_db()
    if find_parfum(db["parfums"], data["id"]):
        raise KeyError(f"Un parfum avec l'ID '{data['id']}' existe déjà")

    parfum: Parfum = {
        "id": data["id"],
        "nom": data["nom"],
        "marque": data.get("marque", ""),
        "type": data.get("type", "EDP"),
        "ml": data.get("ml", 100),
        "stock": data["stock"],
        "notes": data.get("notes", ""),
        "categorie": data.get("categorie", "Mixte"),
        "prix": data.get("prix", 0),
    }
    db["parfums"].append(parfum)
    save_db(db)
    return f"Ajouté : {parfum['marque']} — {parfum['nom']} x{parfum['stock']}"


def display_summary(db: Optional[Database] = None) -> str:
    """Affiche un résumé textuel du stock."""
    if db is None:
        db = load_db()

    parfums = db.get("parfums", [])
    meta = db.get("_meta", {})
    en_rupture = [p for p in parfums if p["stock"] <= 0]
    stock_bas = [p for p in parfums if 0 < p["stock"] <= 2]

    lignes = [
        "=" * 60,
        f"  {meta.get('titre', 'COLLECTION PRIVÉE')}",
        "=" * 60,
    ]
    for p in parfums:
        statut = (
            "RUPTURE" if p["stock"] <= 0
            else "Bas" if p["stock"] <= 2
            else "OK"
        )
        prix_str = f" €{p['prix']}" if p.get("prix") else ""
        lignes.append(
            f"  [{statut:>8s}] {p['marque']:28s} {p['nom']:25s} x{p['stock']:2d}{prix_str}"
        )
    lignes += [
        "=" * 60,
        f"  {len(parfums)} parfums | {meta.get('total_stock', 0)} unités",
    ]
    if en_rupture:
        lignes.append(f"  Ruptures : {', '.join(p['nom'] for p in en_rupture)}")
    if stock_bas:
        lignes.append(f"  Stock bas : {', '.join(p['nom'] for p in stock_bas)}")
    return "\n".join(lignes)
