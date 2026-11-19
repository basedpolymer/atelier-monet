#!/usr/bin/env python3
"""Vérification du skill : construit exemple.md et le cours d'exemple dans un dossier temporaire et exige des bilans
propres (« OK », aucune ligne « erreur : » ni « avis : »), avec une couverture et sa planche ; compose chaque motif dans
chaque place et chaque teinte, sur plusieurs tirages ; contrôle favicons et titres d'onglet (le même favicon sur tout le
cours, l'icône d'écran d'accueil d'une page publiée, les clés icone: et onglet:, les dessins sur mesure) ; si un
navigateur Chromium est là, ouvre chaque page à jouets sans interface et exige que leur code ait tourné sans erreur ;
avec --pdf, produit aussi le PDF de exemple.md et celui d'une page à couverture.

    python3 tests/verifier.py [--pdf]

Code de sortie : 0 si tout est propre, 1 sinon.
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(RACINE))
import textured  # noqa: E402
import couverture  # noqa: E402
import icone  # noqa: E402
import motifs  # noqa: E402

echecs = []

ENTIERE = """---
titre: Une couverture entière
court: Essai
soustitre: dessinée à la main
auteur: A. Auteur
date: 2026-11-19
description: Couverture entière dessinée, favicon dessiné, titre d'onglet choisi.
tirage: #765ba7
couverture: claire
onglet: Essai de couverture
url: https://exemple.org/essai.html
---

::: couverture
<svg viewBox="0 0 200 300">
<rect width="200" height="300" fill="var(--cf)"/>
<circle cx="100" cy="110" r="60" fill="var(--ca)"/>
<text x="16" y="250" font-size="24">{TITRE}</text>
<text x="16" y="270" font-size="9" font-weight="400">{auteur} · {annee}</text>
</svg>
:::

::: icone
<svg viewBox="0 0 32 32"><circle cx="16" cy="16" r="9" stroke="currentColor" stroke-width="3"/><circle cx="16" cy="16" r="3" fill="var(--ca)"/></svg>
:::

## Une section

Du texte.

## Une autre

Encore du texte.
"""


def balise(page, motif):
    m = re.search(motif, page)
    return m.group(0) if m else ""


def motifs_et_glyphes():
    """Chaque motif dans chaque place et chaque teinte, sur quelques tirages ; chaque glyphe en SVG et en PNG."""
    d = couverture.mesurer("<p>Un texte de quelques mots pour mesurer.</p>", [], "Essai")
    meta = {"titre": "Essai de couverture", "auteur": "A. Auteur", "date": "2026", "soustitre": "un sous-titre"}
    for nom in motifs.MOTIFS:
        for k, (teinte, place) in enumerate((t, p) for t in ("claire", "encre", "sombre") for p in ("haut", "bas", "plein", "fond")):
            try:
                h = couverture.composer(meta, d, "fr", nom, teinte, place, "#0078bf", 1000 + 37 * k)
                if "<svg" not in h:
                    echecs.append(f"motif {nom} ({teinte}, {place}) : pas de dessin")
            except Exception as x:  # noqa: BLE001
                echecs.append(f"motif {nom} ({teinte}, {place}) : {x!r}")
    sans_mots = [m for m, liste in motifs.INDICES.items() if not liste]
    if sans_mots:
        echecs.append("motifs sans mots du sujet : " + ", ".join(sans_mots))
    pal = couverture.palette("#00a95c", "encre")
    for nom, prims in icone.GLYPHES.items():
        try:
            if not icone.png(prims, pal, 32).startswith(b"\x89PNG") or "<svg" not in icone.dessiner(nom, pal):
                echecs.append(f"glyphe {nom} : rendu vide")
        except Exception as x:  # noqa: BLE001
            echecs.append(f"glyphe {nom} : {x!r}")
    print(f"  {len(motifs.MOTIFS)} motifs × 4 places × 3 teintes, {len(icone.GLYPHES)} marques : "
          f"{'erreur' if any(x.startswith(('motif', 'glyphe')) for x in echecs) else 'ok'}")


def favicons(tmp):
    """Le même favicon sur tout le cours, titres d'onglet, clés icone: et onglet:, dessins sur mesure."""
    pages = {f.name: f.read_text(encoding="utf-8") for f in (tmp / "cours").glob("*.html")}
    icones = {n: balise(p, r'<link rel="icon" type="image/svg\+xml" href="[^"]+">') for n, p in pages.items()}
    if not all(icones.values()) or len(set(icones.values())) != 1:
        echecs.append("cours : favicon absent ou différent d'une page à l'autre")
    if "<title>Chapitre 1 · " not in pages.get("01-flory-huggins.html", ""):
        echecs.append("chapitre : titre d'onglet « Chapitre 1 · … — cours » absent")
    src = tmp / "essai.md"
    src.write_text(ENTIERE, encoding="utf-8")
    lancer([str(src), "-o", str(tmp / "essai.html"), "--icones"])
    page = (tmp / "essai.html").read_text(encoding="utf-8")
    for attendu, quoi in (('class="couverture couv-entiere', "couverture entière"), ("<title>Essai de couverture</title>", "onglet:"),
                          ('property="og:title" content="Essai de couverture"', "og:title"),
                          ('rel="apple-touch-icon" href="data:image/png;base64,', "apple-touch-icon"), ("ESSAI</text>", "{TITRE}")):
        if attendu not in page:
            echecs.append(f"page d'essai : {quoi} absent")
    if "A. Auteur · 2026" not in page:
        echecs.append("page d'essai : {auteur} · {annee} non remplacés")
    if 'class="icone"' in page or "%3Ccircle cx='16' cy='16' r='9'" not in page:
        echecs.append("page d'essai : favicon dessiné (::: icone) absent ou bloc resté dans la page")
    if not (tmp / "essai.icones.html").is_file():
        echecs.append("planche des favicons absente")
    for valeur, attendu in (("icone: lettre", "font-weight='700'"), ("icone: non", None), ("icone: https://exemple.org/i.png", 'href="https://exemple.org/i.png"')):
        f = tmp / "icone.md"
        f.write_text(f"---\ntitre: Essai\ndescription: Essai.\n{valeur}\n---\n\nTexte.\n", encoding="utf-8")
        lancer([str(f), "-o", str(tmp / "icone.html")])
        p = (tmp / "icone.html").read_text(encoding="utf-8")
        if attendu is None and 'rel="icon"' in p:
            echecs.append("icone: non : un favicon est posé")
        elif attendu and attendu not in p:
            echecs.append(f"{valeur} : favicon attendu absent")


def lancer(args):
    r = subprocess.run([sys.executable, str(RACINE / "textured.py"), *args], capture_output=True, text=True)
    sortie = r.stdout + r.stderr
    print(sortie.rstrip())
    for ligne in sortie.splitlines():
        if ligne.startswith(("ERREURS ", "textured :")) or ligne.strip().startswith(("erreur :", "avis :")):
            echecs.append(ligne.strip())
    if r.returncode not in (0,):
        echecs.append(f"code de sortie {r.returncode} pour {' '.join(args)}")
    return sortie


def jouets(page, nav, tmp):
    """Ouvre la page sans interface et lit les drapeaux posés par la boîte à outils."""
    r = subprocess.run([nav, "--headless", "--disable-gpu", "--no-first-run", f"--user-data-dir={tmp / ('profil-' + page.stem)}",
                        "--virtual-time-budget=8000", "--dump-dom", page.resolve().as_uri()], capture_output=True, text=True, timeout=180)
    racine = re.search(r"<html[^>]*>", r.stdout)
    attributs = racine.group(0) if racine else ""
    if 'data-cours-pret="1"' not in attributs:
        echecs.append(f"{page.name} : la boîte à outils n'a pas démarré")
    m = re.search(r'data-cours-erreurs="(\d+)"', attributs)
    if m:
        echecs.append(f"{page.name} : {m.group(1)} erreur(s) dans le code des jouets")
    print(f"  jouets de {page.name} : {'erreur' if m or 'data-cours-pret' not in attributs else 'ok'}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pdf", action="store_true", help="produire aussi le PDF de exemple.md")
    o = p.parse_args()
    with tempfile.TemporaryDirectory(prefix="textured-test-", ignore_cleanup_errors=True) as tmp:
        tmp = Path(tmp)
        lancer([str(RACINE / "exemple.md"), "-o", str(tmp / "exemple.html")] + (["--pdf"] if o.pdf else []))
        if o.pdf and not (tmp / "exemple.pdf").is_file():
            echecs.append("exemple.pdf absent")
        lancer([str(RACINE / "exemples" / "cours"), "-o", str(tmp / "cours")])
        motifs_et_glyphes()
        favicons(tmp)
        # couverture sur un chapitre (encre et densité héritées de l'accueil) et planche de tous les motifs
        chap = RACINE / "exemples" / "cours" / "01-flory-huggins.md"
        lancer([str(chap), "-o", str(tmp / "couv" / "chapitre.html"), "--couverture", "oui", "--planche"] + (["--pdf"] if o.pdf else []))
        if o.pdf and not (tmp / "couv" / "chapitre.pdf").is_file():
            echecs.append("PDF de la page à couverture absent")
        planche = (tmp / "couv" / "chapitre.couvertures.html").read_text(encoding="utf-8") if (tmp / "couv" / "chapitre.couvertures.html").is_file() else ""
        n_cases = planche.count('class="couv-case"')
        if n_cases < len(motifs.MOTIFS):
            echecs.append(f"planche : {n_cases} couvertures pour {len(motifs.MOTIFS)} motifs")
        if 'class="couverture ' not in (tmp / "couv" / "chapitre.html").read_text(encoding="utf-8"):
            echecs.append("couverture absente de la page")
        if not (tmp / "couv" / "chapitre.couvertures.html").is_file():
            echecs.append("planche des couvertures absente")
        # étagère : l'accueil d'un cours à couverture montre chaque chapitre en mini-couverture, légère
        import shutil
        shutil.copytree(RACINE / "exemples" / "cours", tmp / "etagere")
        idx = tmp / "etagere" / "index.md"
        idx.write_text(idx.read_text(encoding="utf-8").replace("densite: compacte\n", "densite: compacte\ncouverture: oui\n", 1), encoding="utf-8")
        lancer([str(tmp / "etagere")])
        accueil = (tmp / "etagere" / "index.html").read_text(encoding="utf-8")
        vignettes = re.findall(r'<a class="vignette".*?</a>', accueil, re.S)
        if 'class="chapitres etagere"' not in accueil or len(vignettes) != 2:
            echecs.append(f"étagère : {len(vignettes)} vignette(s) au lieu de 2")
        elif max(len(x.encode()) for x in vignettes) > 14_000:
            echecs.append("étagère : vignette trop lourde")
        nav = textured.navigateur()
        if nav:
            for page in sorted((tmp / "cours").glob("*.html")):
                if 'class="jouet' in page.read_text(encoding="utf-8"):
                    jouets(page, nav, tmp)
        else:
            print("  (pas de navigateur Chromium : jouets non exécutés)")
            if o.pdf:
                echecs.append("--pdf demandé, mais aucun navigateur trouvé")
    if echecs:
        print("\nÉCHEC :")
        for x in echecs:
            print("  " + x)
        return 1
    print("\nTout est propre.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
