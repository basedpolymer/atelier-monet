#!/usr/bin/env python3
"""Vérification du skill : construit exemple.md et le cours d'exemple dans un dossier temporaire et exige des bilans
propres (« OK », aucune ligne « erreur : » ni « avis : »), avec une couverture et sa planche ; si un navigateur Chromium est là, ouvre chaque page à jouets
sans interface et exige que leur code ait tourné sans erreur ; avec --pdf, produit aussi le PDF de exemple.md.

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

echecs = []


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
        # couverture sur un chapitre (encre et densité héritées de l'accueil) et planche de tous les motifs
        chap = RACINE / "exemples" / "cours" / "01-flory-huggins.md"
        lancer([str(chap), "-o", str(tmp / "couv" / "chapitre.html"), "--couverture", "oui", "--planche"])
        if 'class="couverture ' not in (tmp / "couv" / "chapitre.html").read_text(encoding="utf-8"):
            echecs.append("couverture absente de la page")
        if not (tmp / "couv" / "chapitre.couvertures.html").is_file():
            echecs.append("planche des couvertures absente")
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
