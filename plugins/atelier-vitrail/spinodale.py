"""Décomposition spinodale d'un mélange binaire symétrique (équation de Cahn-Hilliard), pour la scène (hooks/scene.ts) :
quelques instants d'une même trempe, de la modulation naissante aux domaines qui grossissent.

    python3 plugins/atelier-vitrail/spinodale.py        (réécrit le bloc SPINODALE de hooks/scene.ts)

    dc/dt = lap( c^3 - c - kappa lap c )      c = +1 : phase riche en A, c = -1 : phase riche en B

Schéma spectral semi-implicite, périodique, sur la grille des caractères : une cellule fait CHAR = 8,4 px de large et
LIGNE px de haut, d'où un pas vertical plus grand que l'horizontal pour que les domaines restent isotropes à l'écran.
Le champ est découpé en disque, comme vu au microscope. Chaque cellule devient un niveau : A, a, ., b, B (de c = +1 à
c = -1), ou une espace hors du disque.
"""
import re
import sys
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
SCENE = Path(__file__).resolve().parent / "hooks/scene.ts"

CHAR, LIGNE = 8.4, 11.0
COLONNES, RANGS = 33, 25
RAYON = 136.0                       # px, rayon du champ
KAPPA = 0.22                        # longueur d'onde la plus rapide : 2 pi sqrt(2 kappa) ~ 4 cellules
INSTANTS = (0, 3, 6, 12, 30, 80, 240)
DT = 0.05


def simule():
    rng = np.random.default_rng(59)
    c = 0.04 * rng.standard_normal((RANGS, COLONNES))
    kx = 2 * np.pi * np.fft.fftfreq(COLONNES, d=1.0)
    ky = 2 * np.pi * np.fft.fftfreq(RANGS, d=LIGNE / CHAR)
    k2 = kx[None, :] ** 2 + ky[:, None] ** 2
    stab = 2.0
    denominateur = 1 + DT * (KAPPA * k2 ** 2 + stab * k2)
    t, sortie = 0.0, []
    for cible in INSTANTS:
        while t < cible - 1e-9:
            ch = np.fft.fft2(c)
            ch = (ch * (1 + DT * stab * k2) - DT * k2 * np.fft.fft2(c ** 3 - c)) / denominateur
            c = np.fft.ifft2(ch).real
            t += DT
        sortie.append((cible, c.copy()))
    return sortie


def niveaux(c):
    cx, cy = (COLONNES - 1) / 2, (RANGS - 1) / 2
    rangs = []
    for i in range(RANGS):
        rang = ""
        for j in range(COLONNES):
            if np.hypot((j - cx) * CHAR, (i - cy) * LIGNE) > RAYON:
                rang += " "
                continue
            v = c[i, j]
            rang += "A" if v > .55 else "a" if v > .2 else "." if v >= -.2 else "b" if v >= -.55 else "B"
        rangs.append(rang.rstrip())
    return rangs


def main():
    lignes = ["// spinodale : début (généré par spinodale.py, Cahn-Hilliard ; ne pas modifier à la main)",
              "const SPINODALE: ReadonlyArray<readonly [number, readonly string[]]> = ["]
    for t, c in simule():
        lignes.append(f"  [{t}, [")
        lignes += [f"    '{r}'," for r in niveaux(c)]
        lignes.append("  ]],")
    lignes += ["]", "// spinodale : fin"]
    bloc = "\n".join(lignes)
    if "--voir" in sys.argv:
        print(bloc)
        return
    s = SCENE.read_text(encoding="utf-8")
    neuf = re.sub(r"// spinodale : début.*?// spinodale : fin", lambda m: bloc, s, flags=re.S)
    if neuf == s and bloc not in s:
        raise SystemExit("repères « // spinodale : début » … « // spinodale : fin » introuvables dans hooks/scene.ts")
    SCENE.write_text(neuf, encoding="utf-8")
    print(f"scene.ts : {len(INSTANTS)} instants de la décomposition spinodale")


if __name__ == "__main__":
    main()
