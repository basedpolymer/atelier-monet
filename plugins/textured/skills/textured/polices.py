#!/usr/bin/env python3
"""Latin Modern et TeX Gyre Chorus en deux parts chacune, par unicode-range : une base (latin-1, et la ponctuation et
les signes du français : œ Œ ’ “ ” « » – — … € ‰ espaces fines, flèches, signe moins…) et un complément (latin étendu,
grec, symboles). Sur un site (--assets), le navigateur ne charge le complément que si la page en affiche un caractère ;
une page autonome embarque la base seule, ou la police entière si elle a besoin du complément (textured.py lit la plage
dans la feuille).

    python3 polices.py      # assets/polices/<nom>-base.woff2 et <nom>-ext.woff2, puis le bloc « polices » de textured.css

Les fichiers complets (assets/polices/<nom>.woff2) restent la source et sont exportés aussi : d'autres pages les
appellent directement. À relancer si l'un d'eux ou la plage de base change. Dépendances (ce script seulement) :
pip install fonttools brotli.
"""
import re
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ICI = Path(__file__).resolve().parent
POLICES = ICI / "assets" / "polices"
FEUILLE = ICI / "assets" / "textured.css"
# plage de base : le sous-ensemble « latin » des polices web courantes, plus les flèches simples (← → de la navigation
# d'un cours)
BASE = ("U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, "
        "U+20AC, U+2122, U+2190-2193, U+2212, U+2215, U+FEFF, U+FFFD")
# (fichier, famille, graisse, style, affichage) : l'ordre et les règles du bloc « polices » de textured.css
FACES = [
    ("lmroman10-regular", "TX Roman", 400, "normal", "swap"),
    ("lmroman10-bold", "TX Roman", 700, "normal", "swap"),
    ("lmroman10-italic", "TX Roman", 400, "italic", "swap"),
    ("lmroman10-bolditalic", "TX Roman", 700, "italic", "swap"),
    ("lmromanslant10-regular", "TX Penche", 400, None, "swap"),
    ("lmromanslant10-bold", "TX Penche", 700, None, "swap"),
    ("lmsans10-regular", "TX Sans", 400, "normal", "swap"),
    ("lmsans10-bold", "TX Sans", 700, "normal", "swap"),
    ("lmsans10-oblique", "TX Sans", 400, "italic", "swap"),
    ("lmsans10-boldoblique", "TX Sans", 700, "italic", "swap"),
    ("lmmono10-regular", "TX Mono", 400, None, "swap"),
    ("texgyrechorus-mediumitalic", "TX Chorus", None, "italic", "block"),
]


def plages(valeur):
    r = []
    for p in valeur.split(","):
        a, _, b = p.strip()[2:].partition("-")
        r.append((int(a, 16), int(b or a, 16)))
    return r


def ecrire_plage(points):
    """Points de code → « U+0100-017F, U+0192, … » (suites contiguës réunies)."""
    morceaux, points = [], sorted(points)
    i = 0
    while i < len(points):
        j = i
        while j + 1 < len(points) and points[j + 1] == points[j] + 1:
            j += 1
        a, b = points[i], points[j]
        morceaux.append(f"U+{a:04X}" if a == b else f"U+{a:04X}-{b:04X}")
        i = j + 1
    return ", ".join(morceaux)


# fonctions typographiques gardées : celles que le navigateur applique d'office (crénage, ligatures fi, fl…) et les
# chiffres que la feuille demande (tabular-nums) ; ni chiffres elzéviriens, ni ligatures rares, ni fractions
FONCTIONS = ["ccmp", "locl", "mark", "mkmk", "kern", "liga", "clig", "calt", "rlig", "tnum", "lnum", "pnum"]


def sous_ensemble(source, cible, points):
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = FONCTIONS
    options.desubroutinize = True        # le WOFF2 compresse mieux des contours CFF à plat ; les hints restent
    options.name_IDs = ["*"]
    options.name_languages = ["*"]
    options.notdef_outline = True
    options.glyph_names = False
    police = TTFont(source)
    s = subset.Subsetter(options)
    s.populate(unicodes=points)
    s.subset(police)
    police.flavor = "woff2"
    police.save(cible)


def regle(nom, famille, graisse, style, affichage, plage):
    proprietes = [f'font-family: "{famille}"']
    if graisse:
        proprietes.append(f"font-weight: {graisse}")
    if style:
        proprietes.append(f"font-style: {style}")
    proprietes += [f"font-display: {affichage}", f'src: url("polices/{nom}.woff2") format("woff2")', f"unicode-range: {plage}"]
    return "@font-face { " + "; ".join(proprietes) + "; }"


def main():
    base = {p for a, b in plages(BASE) for p in range(a, b + 1)}
    lignes = []
    for nom, famille, graisse, style, affichage in FACES:
        source = POLICES / f"{nom}.woff2"
        carte = set(TTFont(source).getBestCmap())
        dans_base, reste = carte & base, carte - base
        sous_ensemble(source, POLICES / f"{nom}-base.woff2", dans_base)
        lignes.append(regle(f"{nom}-base", famille, graisse, style, affichage, BASE))
        if reste:
            sous_ensemble(source, POLICES / f"{nom}-ext.woff2", reste)
            lignes.append(regle(f"{nom}-ext", famille, graisse, style, affichage, ecrire_plage(reste)))
        else:
            (POLICES / f"{nom}-ext.woff2").unlink(missing_ok=True)
        tailles = [source.stat().st_size] + [(POLICES / f"{nom}-{p}.woff2").stat().st_size
                                             for p in ("base", "ext") if (POLICES / f"{nom}-{p}.woff2").exists()]
        print(f"{nom} : {tailles[0] // 1024} Ko → base {tailles[1] // 1024} Ko ({len(dans_base)} car.)"
              + (f" + complément {tailles[2] // 1024} Ko ({len(reste)} car.)" if len(tailles) > 2 else ""))
    feuille = FEUILLE.read_text(encoding="utf-8")
    debut = feuille.index("/*@ polices */\n") + len("/*@ polices */\n")
    fin = feuille.index("/* polices de repli")
    entete = ("/* Latin Modern en deux parts (polices.py, ne pas modifier à la main) : base (latin-1, ponctuation du français),\n"
              "   complément chargé seulement si la page en affiche un caractère */\n")
    FEUILLE.write_text(feuille[:debut] + entete + "\n".join(lignes) + "\n" + feuille[fin:], encoding="utf-8", newline="\n")
    print(f"bloc « polices » réécrit : {FEUILLE}")


if __name__ == "__main__":
    sys.exit(main())
