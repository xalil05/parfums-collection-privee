# Collection Privée — Système de Gestion des Parfums

Système de gestion de stock pour la vente de parfums **Collection Privée**.

## 🚀 Démarrage rapide

```bash
pip install -r requirements.txt
python3 main.py
```

Cela affiche le résumé des stocks, génère le **catalogue HTML** et le **visuel WhatsApp**.

### Dashboard Web

```bash
python3 app.py
# → http://localhost:5000
```

Pour un accès réseau local :
```bash
python3 app.py --host 0.0.0.0 --port 8080
```

Le dashboard permet de :
- 📊 Voir les statistiques en temps réel (stocks, valeur, ruptures)
- ➕ Ajouter des parfums via formulaire
- ✏️ Modifier les parfums existants
- 🗑️ Archiver les parfums (pas de perte de données)
- ➖ Vendre / ➕ Réapprovisionner en 1 clic
- 🔍 Rechercher et filtrer par catégorie
- ⚠️ Alertes visuelles pour les stocks bas et ruptures

## 📁 Structure du projet

```
├── app.py              # Serveur Flask (dashboard web)
├── db.py               # Couche d'accès aux données (CRUD JSON)
├── cli.py              # Interface en ligne de commande
├── html_gen.py         # Génération du catalogue HTML
├── img_gen.py          # Génération du visuel WhatsApp (catégories séparées)
├── main.py             # Point d'entrée principal (CLI)
├── update.py           # Alias rétrocompatible → cli.py
├── update-visuel.py    # Générateur du visuel (moderne ou legacy)
├── parfums.json        # Base de données (stock, prix, statut)
├── requirements.txt    # Dépendances Python
├── template-reference.jpg  # Template legacy pour fond d'image
├── templates/          # Templates HTML du dashboard
│   └── dashboard.html  #   → Interface web de gestion
├── catalogue.html      # Catalogue HTML généré (gitignored)
└── whatsapp-status.jpg # Visuel généré (gitignored)
```

## 📋 Commandes

| Commande | Action |
|----------|--------|
| `python3 main.py` | Résumé + catalogue + visuel |
| `python3 main.py --summary` | Résumé du stock uniquement |
| `python3 main.py --catalogue` | Générer le catalogue HTML uniquement |
| `python3 main.py --visuel` | Générer le visuel WhatsApp uniquement |
| `python3 main.py --set <id> <valeur>` | Fixer le stock d'un parfum |
| `python3 main.py --add <id> <quantité>` | Ajouter du stock |
| `python3 main.py --sell <id>` | Vendre 1 unité |
| `python3 main.py --ajouter <id> <nom> <marque> <type> <ml> <stock> <cat>` | Ajouter un parfum |
| `python3 update-visuel.py` | Visuel moderne (recommandé) |
| `python3 update-visuel.py --legacy` | Visuel avec template-reference.jpg |

### Exemples

```bash
# Voir l'état des stocks
python3 main.py --summary

# Ajouter 5 unités d'Oud Bouquet
python3 main.py --add oud-bouquet 5

# Vendre un Scandal Homme
python3 main.py --sell scandal-homme

# Ajouter un nouveau parfum
python3 main.py --ajouter new-id "Nouveau Parfum" "Marque" "EDP" 100 10 "Homme"
```

## 📦 Structure des données (parfums.json)

```json
{
  "id": "oud-bouquet",
  "nom": "Oud Bouquet",
  "marque": "Lattafa",
  "type": "EDP",
  "ml": 100,
  "stock": 3,
  "prix": 0,
  "notes": "Oud, Rose, Épices, Cuir",
  "categorie": "Mixte"
}
```

**Champs :**
- `id` — Identifiant unique (slug)
- `nom` — Nom du parfum
- `marque` — Marque
- `type` — EDP, EDT, Extrait...
- `ml` — Volume en ml
- `stock` — Quantité en stock
- `prix` — Prix de vente (0 = non défini)
- `notes` — Notes olfactives
- `categorie` — Homme / Femme / Mixte

## 🖼️ Visuels

Deux modes de génération d'image :
1. **Moderne** (défaut) : fond dégradé bleu-nuit, catégories Homme/Femme/Mixte en colonnes, polices DejaVu avec fallback automatique
2. **Legacy** (`--legacy`) : utilise `template-reference.jpg` comme fond + superposition du texte

Le visuel est optimisé pour **WhatsApp Status** (1080×1920 px, format 9:16).

## 🔧 Dépendances

- Python ≥ 3.8
- Pillow ≥ 10.0 (génération d'images)
- Flask ≥ 3.0 (dashboard web)

Les polices DejaVu sont incluses par défaut dans la plupart des distributions Linux.
En cas d'absence, installer avec : `apt install fonts-dejavu-core` (Debian/Ubuntu)
ou `dnf install dejavu-fonts` (Fedora) ou `pacman -S ttf-dejavu` (Arch).

## 🔗 Catalogue en ligne

Le catalogue HTML peut être hébergé sur GitHub Pages.

## 📄 Licence

Usage interne — Collection Privée
