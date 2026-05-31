#!/usr/bin/env python3
"""
Interface CLI — Parfums Collection Privée.
Point d'entrée pour la gestion des stocks.
"""

import argparse
import sys
import json

from db import load_db, set_stock, add_stock, sell, add_parfum, display_summary
from html_gen import generate as generate_html
from img_gen import generate as generate_image


def build_parser() -> argparse.ArgumentParser:
    """Construit le parseur d'arguments CLI."""
    p = argparse.ArgumentParser(
        prog="collection-privee",
        description="Gestion des stocks — Parfums Collection Privée",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python3 main.py                     # Afficher le stock + générer catalogue + visuel
  python3 main.py --set scandal-homme 5     # Fixer le stock
  python3 main.py --add oud-bouquet 3       # Ajouter du stock
  python3 main.py --sell scandal-homme 1    # Vendre (décrémenter)
  python3 main.py --ajouter --id x --nom "Nouveau Parfum" --stock 5
  python3 main.py --catalogue              # Générer seulement le catalogue
  python3 main.py --visuel                 # Générer seulement le visuel
        """,
    )

    # Opérations de stock
    p.add_argument("--set", nargs=2, metavar=("ID", "VALEUR"),
                   help="Fixer le stock d'un parfum")
    p.add_argument("--add", nargs=2, metavar=("ID", "QUANTITÉ"),
                   help="Ajouter du stock à un parfum")
    p.add_argument("--sell", nargs="?", const=1, metavar=("ID"),
                   help="Vendre 1 unité (ou --sell ID QTT)")
    p.add_argument("--ajouter", nargs=7,
                   metavar=("ID", "NOM", "MARQUE", "TYPE", "ML", "STOCK", "CATÉGORIE"),
                   help="Ajouter un nouveau parfum: --ajouter id nom marque type ml stock catégorie")

    # Actions
    p.add_argument("--catalogue", action="store_true",
                   help="Générer uniquement le catalogue HTML")
    p.add_argument("--visuel", action="store_true",
                   help="Générer uniquement le visuel WhatsApp")
    p.add_argument("--summary", action="store_true",
                   help="Afficher uniquement le résumé du stock")

    return p


def handle_ajouter(args: list[str]) -> str:
    """Parse --ajouter avec 7 arguments positionnels."""
    pid, nom, marque, typ, ml_str, stock_str, categorie = args
    try:
        stock = int(stock_str)
        ml = int(ml_str)
    except ValueError:
        return "❌ Erreur : STOCK et ML doivent être des nombres entiers"
    if stock < 0:
        return "❌ Erreur : le stock ne peut pas être négatif"
    if ml <= 0:
        return "❌ Erreur : le volume (ML) doit être positif"

    data = {
        "id": pid,
        "nom": nom,
        "marque": marque,
        "type": typ,
        "ml": ml,
        "stock": stock,
        "categorie": categorie,
    }
    return add_parfum(data)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        # Opérations de stock
        if args.set:
            pid, val_str = args.set
            try:
                val = int(val_str)
            except ValueError:
                print("❌ Erreur : la valeur doit être un nombre entier")
                sys.exit(1)
            print(set_stock(pid, val))

        elif args.add:
            pid, qty_str = args.add
            try:
                qty = int(qty_str)
            except ValueError:
                print("❌ Erreur : la quantité doit être un nombre entier")
                sys.exit(1)
            print(add_stock(pid, qty))

        elif args.sell:
            # --sell peut être juste ID (vendu 1) ou ID + quantité
            if isinstance(args.sell, str):
                print(sell(args.sell, 1))
            elif isinstance(args.sell, list):
                pid = args.sell[0]
                qty = int(args.sell[1]) if len(args.sell) > 1 else 1
                print(sell(pid, qty))

        elif args.ajouter:
            print(handle_ajouter(args.ajouter))

        # Actions spécifiques
        elif args.catalogue:
            generate_html()

        elif args.visuel:
            generate_image()

        elif args.summary:
            print(display_summary())

        else:
            # Par défaut : résumé + catalogue + visuel
            print(display_summary())
            print()
            generate_html()
            print()
            generate_image()

    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
