#!/usr/bin/env python3
"""
UPDATE.PY — Version legacy (rétrocompatible)
Délègue toutes les opérations aux modules refactorisés.

Usage : python3 update.py [commandes]
Voir python3 update.py --help
"""

from cli import main

if __name__ == "__main__":
    main()
