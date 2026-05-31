#!/usr/bin/env python3
"""
Génération du catalogue HTML — Parfums Collection Privée.
Produit un fichier catalogue.html responsive avec catégories séparées.
"""

import os
import datetime
from typing import Optional
from db import load_db, Database, Parfum

DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(DIR, "catalogue.html")


def _badge_html(p: Parfum) -> str:
    """Génère le badge de statut pour un parfum."""
    if p["stock"] <= 0:
        return '<span class="bdg bdg-rup">RUPTURE</span>'
    elif p["stock"] <= 2:
        return f'<span class="bdg bdg-bas">Stock bas ({p["stock"]})</span>'
    else:
        return f'<span class="bdg bdg-ok">{p["stock"]} en stock</span>'


def _card_html(p: Parfum) -> str:
    """Génère une carte HTML pour un parfum."""
    badge = _badge_html(p)
    cls = " c-rup" if p["stock"] <= 0 else ""
    prix = f"<span class='c-prix'>€{p['prix']}</span>" if p.get("prix") else ""

    return f"""\
    <div class="c{cls}">
      <div class="c-bdg">{badge}</div>
      <div class="c-hd">
        <span class="mq">{p['marque']}</span>
        <span class="tp">{p['type']} · {p['ml']}ml</span>
      </div>
      <div class="c-tl">{p['nom']}</div>
      {prix}
      <div class="c-nt">{p['notes']}</div>
      <div class="c-ft">
        <span class="st">{'x' + str(p['stock']) if p['stock'] > 0 else 'ÉPUISÉ'}</span>
      </div>
    </div>"""


def _section_html(titre: str, items: list[Parfum]) -> str:
    """Génère une section (titre + grille de cartes)."""
    if not items:
        return ""
    tri = sorted(items, key=lambda x: (-x["stock"], x["marque"]))
    cartes = "\n".join(_card_html(p) for p in tri)
    return f"""\
    <div class="sec">
      <h2>{titre}</h2>
    </div>
    <div class="grid">
{cartes}
    </div>"""


def _css() -> str:
    """Styles CSS complets."""
    return """\
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Inter,sans-serif;background:#0a0a0f;color:#e8e0d4}
.header{background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);padding:40px 20px;text-align:center;border-bottom:1px solid rgba(212,175,55,0.2)}
.header h1{font-family:'Playfair Display',serif;font-size:2.8em;color:#d4af37;letter-spacing:4px}
.header .sub{font-size:.9em;color:#a0998e;margin-top:8px;letter-spacing:6px;text-transform:uppercase}
.stats{display:flex;justify-content:center;gap:40px;padding:20px;background:rgba(26,26,46,0.8);border-bottom:1px solid rgba(212,175,55,0.1);flex-wrap:wrap}
.s-item{text-align:center}
.s-val{font-family:'Playfair Display',serif;font-size:1.8em;color:#d4af37;font-weight:700}
.s-lbl{font-size:.75em;color:#6b6360;text-transform:uppercase;letter-spacing:2px}
.s-rup .s-val{color:#ff4757}
.s-bas .s-val{color:#ffa502}
.alerts{max-width:1200px;margin:20px auto;padding:0 20px}
.alert{padding:12px 20px;border-radius:8px;margin-bottom:8px;font-size:.9em}
.alert-rup{background:rgba(255,71,87,0.1);border:1px solid rgba(255,71,87,0.3);color:#ff6b81}
.alert-bas{background:rgba(255,165,2,0.1);border:1px solid rgba(255,165,2,0.3);color:#ffa502}
.sec{max-width:1200px;margin:30px auto 15px;padding:0 20px}
.sec h2{font-family:'Playfair Display',serif;font-size:1.5em;color:#d4af37;border-bottom:1px solid rgba(212,175,55,0.2);padding-bottom:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;max-width:1200px;margin:0 auto;padding:0 20px 40px}
.c{background:linear-gradient(145deg,#1a1a2e,#16213e);border:1px solid rgba(212,175,55,0.15);border-radius:12px;padding:20px;transition:all .3s;position:relative}
.c:hover{transform:translateY(-4px);border-color:rgba(212,175,55,0.4);box-shadow:0 8px 30px rgba(212,175,55,0.1)}
.c.rup{opacity:.6;border-color:rgba(255,71,87,0.3)}
.c-bdg{position:absolute;top:12px;right:12px}
.bdg{font-size:.7em;padding:3px 8px;border-radius:20px;font-weight:600}
.bdg-rup{background:rgba(255,71,87,0.2);color:#ff6b81;border:1px solid rgba(255,71,87,0.3)}
.bdg-bas{background:rgba(255,165,2,0.2);color:#ffa502;border:1px solid rgba(255,165,2,0.3)}
.bdg-ok{background:rgba(46,213,115,0.2);color:#2ed573;border:1px solid rgba(46,213,115,0.3)}
.c-hd{display:flex;justify-content:space-between;font-size:.75em;color:#888;margin-bottom:4px}
.mq{color:#a0998e}
.c-tl{font-family:'Playfair Display',serif;font-size:1.2em;color:#e8e0d4;margin:4px 0;font-weight:600}
.c-prix{color:#d4af37;font-weight:600;font-size:.95em;margin:4px 0}
.c-nt{font-size:.8em;color:#6b6360;margin:6px 0;line-height:1.4}
.c-ft{display:flex;justify-content:space-between;align-items:center;margin-top:8px;padding-top:8px;border-top:1px solid rgba(212,175,55,0.1)}
.st{font-size:.8em;color:#d4af37;font-weight:600}
footer{text-align:center;padding:20px;color:#6b6360;font-size:.8em}
@media(max-width:600px){.header h1{font-size:2em}.stats{gap:20px}.grid{grid-template-columns:1fr}}
"""


def generate(catalogue_path: str = OUTPUT) -> str:
    """Génère le fichier catalogue.html et retourne son chemin."""
    db = load_db()
    parfums = db["parfums"]
    meta = db.get("_meta", {})
    total_stock = meta.get("total_stock", sum(p["stock"] for p in parfums))
    en_rupture = [p for p in parfums if p["stock"] <= 0]
    stock_bas = [p for p in parfums if 0 < p["stock"] <= 2]

    # Alertes
    alertes = ""
    for p in en_rupture:
        alertes += f'<div class="alert alert-rup">Rupture: <strong>{p["marque"]} {p["nom"]}</strong></div>\n'
    for p in stock_bas:
        alertes += f'<div class="alert alert-bas">Stock bas: <strong>{p["marque"]} {p["nom"]}</strong> ({p["stock"]} restants)</div>\n'

    # Sections par catégorie
    sections = _section_html("HOMME", [p for p in parfums if p["categorie"] == "Homme"])
    sections += "\n" + _section_html("FEMME", [p for p in parfums if p["categorie"] == "Femme"])
    sections += "\n" + _section_html("MIXTES / UNISEX", [p for p in parfums if p["categorie"] == "Mixte"])

    now = datetime.datetime.now()

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="Catalogue Collection Privée — Parfumerie de Luxe. Découvrez notre sélection de parfums de marques prestigieuses.">
  <meta property="og:title" content="Collection Privée — Catalogue">
  <meta property="og:description" content="Parfumerie de Luxe · {len(parfums)} parfums disponibles">
  <meta property="og:type" content="website">
  <meta name="theme-color" content="#0a0a0f">
  <title>Collection Privée — Parfumerie de Luxe</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🧴</text></svg>">
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>{_css()}</style>
</head>
<body>
  <div class="header">
    <h1>✦ COLLECTION PRIVÉE ✦</h1>
    <div class="sub">Parfumerie de Luxe — Catalogue</div>
  </div>
  <div class="stats">
    <div class="s-item"><div class="s-val">{len(parfums)}</div><div class="s-lbl">Parfums</div></div>
    <div class="s-item"><div class="s-val">{total_stock}</div><div class="s-lbl">Unités en stock</div></div>
    <div class="s-item{' s-rup' if en_rupture else ''}"><div class="s-val">{len(en_rupture)}</div><div class="s-lbl">Ruptures</div></div>
    <div class="s-item{' s-bas' if stock_bas else ''}"><div class="s-val">{len(stock_bas)}</div><div class="s-lbl">Stock bas</div></div>
  </div>
  <div class="alerts">
{alertes}
  </div>
{sections}
  <footer>
    Généré automatiquement le {now.strftime("%d/%m/%Y à %H:%M")}<br>
    Collection Privée — Genova, Italia
  </footer>
</body>
</html>"""

    with open(catalogue_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"📄 Catalogue généré : {catalogue_path}")
    return catalogue_path
