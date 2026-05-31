#!/usr/bin/env python3
"""
Collection Privée — Système de Gestion des Parfums
Point d'entrée principal.

Usage :
  python3 main.py                     # Résumé + catalogue + visuel
  python3 main.py --set <id> <val>    # Fixer le stock
  python3 main.py --add <id> <qty>    # Ajouter du stock
  python3 main.py --sell <id>         # Vendre 1 unité
  python3 main.py --catalogue         # Générer le catalogue HTML
  python3 main.py --visuel            # Générer le visuel WhatsApp
"""

from cli import main

if __name__ == "__main__":
    main()
