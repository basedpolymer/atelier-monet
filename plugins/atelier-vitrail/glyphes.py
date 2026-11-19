"""Contours des caractères de la scène (hooks/scene.ts), pour qu'elle soit dessinée en formes et non en texte : rien à
sélectionner, à copier, à traduire ni à lire à voix haute, et la même lettre partout (l'app comme le site).

    python3 plugins/atelier-vitrail/glyphes.py        (réécrit le bloc GLYPHES de hooks/scene.ts)

Police : Latin Modern Mono 10 (GUST Font License, libre de redistribution), celle du skill TeXtured
(plugins/textured/skills/textured/assets/polices/lmmono10-regular.woff2). À 16 px, son chasse est 8,4 px : la grille
de la scène (CHAR = 8.4). Chaque contour est en pixels, origine au début de la ligne de base, y vers le bas.
"""
import re
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

sys.dont_write_bytecode = True
ICI = Path(__file__).resolve().parent
POLICE = ICI.parent / "textured/skills/textured/assets/polices/lmmono10-regular.woff2"
SCENE = ICI / "hooks/scene.ts"
TAILLE = 16


def contours():
    f = TTFont(POLICE)
    k = TAILLE / f["head"].unitsPerEm
    cmap, glyphes = f.getBestCmap(), f.getGlyphSet()
    sortie = {}
    for code in range(33, 127):
        nom = cmap.get(code)
        if not nom:
            continue
        pen = SVGPathPen(glyphes, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        glyphes[nom].draw(TransformPen(pen, (k, 0, 0, -k, 0, 0)))
        d = pen.getCommands()
        if d:
            sortie[chr(code)] = d
    return sortie, glyphes[cmap[ord("o")]].width * k


def main():
    table, chasse = contours()
    assert abs(chasse - 8.4) < .01, chasse
    lignes = ["// glyphes : début (généré par glyphes.py depuis Latin Modern Mono 10, 16 px ; ne pas modifier à la main)",
              "const GLYPHES: Readonly<Record<string, string>> = {"]
    lignes += [f"  {c!r}: '{d}'," for c, d in table.items()]
    lignes += ["}", "// glyphes : fin"]
    bloc = "\n".join(lignes)
    s = SCENE.read_text(encoding="utf-8")
    neuf = re.sub(r"// glyphes : début.*?// glyphes : fin", lambda m: bloc, s, flags=re.S)
    if neuf == s and bloc not in s:
        raise SystemExit("repères « // glyphes : début » … « // glyphes : fin » introuvables dans hooks/scene.ts")
    SCENE.write_text(neuf, encoding="utf-8")
    print(f"scene.ts : {len(table)} glyphes, {len(bloc) // 1024} Ko")


if __name__ == "__main__":
    main()
