"""TeXtured — favicon de page : une marque géométrique lisible à 16 px, sur une tuile aux couleurs de la page.

Une marque, c'est deux ou trois formes simples en une ou deux couleurs (pas de mini-illustration), décrites en
primitives sur une grille de 32 × 32 (traits de 2,8 unités au moins, soit 1,4 px à 16 px) : ("t", points, épaisseur)
polyligne à bouts ronds, ("f", points) polygone plein, ("d", x, y, r) disque, ("c", x, y, r, épaisseur) cercle ; un
dernier élément « a » met la primitive à l'accent, « f » l'évide (couleur de la tuile). Les mêmes primitives donnent
le SVG du favicon et, sans dépendance, le PNG de l'écran d'accueil (apple-touch-icon) et le repli 32 px des
navigateurs sans favicon SVG.

Le défaut d'une page : la marque de son motif de couverture s'il y en a une (aux couleurs de la couverture), sinon
celle du motif que désignent les mots de son en-tête, à l'encre de la page ; le losange si rien ne parle. Un cours
entier porte le favicon de son accueil.

    icone: onde                # une marque (python3 icone.py : la liste), ou un nom de motif (« semis » → onde)
    icone: lettre              # l'initiale du titre court (« icone: lettre Ω » : une autre lettre)
    icone: anneau claire rond  # teinte (claire, encre, sombre) et forme (carre, rond, nu)
    icone: https://…/icone.svg # une adresse
    icone: non                 # pas de favicon
    ::: icone                  # un dessin : <svg viewBox="0 0 32 32">, couleurs currentColor, var(--ca), var(--cf)
"""
import base64
import html
import math
import re
import struct
import sys
import zlib
from collections import Counter

import couverture
from motifs import ALIAS, CATALOGUE, sans_accents


# ---------- outils de dessin ----------

def T(pts, w=3, role="g"):
    return ("t", [tuple(map(float, p)) for p in pts], w, role)


def F(pts, role="g"):
    return ("f", [tuple(map(float, p)) for p in pts], role)


def D(x, y, r, role="g"):
    return ("d", x, y, r, role)


def C(x, y, r, w=2.6, role="g"):
    return ("c", x, y, r, w, role)


def courbe(f, x0, x1, k=24):
    return [(x0 + (x1 - x0) * i / k, f(x0 + (x1 - x0) * i / k)) for i in range(k + 1)]


def arc(cx, cy, r, a0, a1, k=24):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / k)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / k)))
            for i in range(k + 1)]


def ellipse(cx, cy, rx, ry, rot=0.0, k=36):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(cx + rx * math.cos(t) * c - ry * math.sin(t) * s, cy + rx * math.cos(t) * s + ry * math.sin(t) * c)
            for t in (2 * math.pi * i / k for i in range(k + 1))]


def rect(x, y, l, h, role="g"):
    return F([(x, y), (x + l, y), (x + l, y + h), (x, y + h)], role)


# ---------- marques ----------
# Des marques géométriques simples, deux ou trois formes, une ou deux couleurs, lisibles à 16 px : pas de
# mini-illustration. Chaque motif de couverture renvoie à la marque qui reprend sa structure.

def _marques():
    G = {}
    G["losange"] = [T([(16, 4.5), (27.5, 16), (16, 27.5), (4.5, 16), (16, 4.5)], 3.2), D(16, 16, 3.2, "a")]
    G["anneau"] = [C(16, 16, 10, 3.4), D(16, 16, 3.8, "a")]
    G["anneaux"] = [C(16, 16, 11, 2.8), C(16, 16, 5.4, 2.8, "a")]
    G["arc"] = [T(arc(16, 16, 10, -90, 180), 3.6), D(16, 6, 3.2, "a")]
    G["onde"] = [T(courbe(lambda x: 16 + 6 * math.sin((x - 5) / 22 * 2.6 * math.pi), 5, 27), 3.4, "a"), D(16, 6.5, 2.4), D(16, 25.5, 2.4)]
    G["ondes"] = [T(courbe(lambda x: 11 + 4 * math.sin((x - 5) / 22 * 2.4 * math.pi), 5, 27), 3), T(courbe(lambda x: 21 + 4 * math.sin((x - 5) / 22 * 2.4 * math.pi), 5, 27), 3, "a")]
    G["points"] = [D(8.5, 23.5, 2.6), D(15, 16.5, 3.8), D(23, 8.5, 5.2, "a")]
    G["grille"] = [rect(5.5, 5.5, 9.4, 9.4), rect(17.1, 5.5, 9.4, 9.4), rect(5.5, 17.1, 9.4, 9.4), rect(17.1, 17.1, 9.4, 9.4, "a")]
    G["damier"] = [rect(5 + 7.6 * i, 5 + 7.6 * j, 6.4, 6.4, "a" if (i, j) == (1, 1) else "g") for i in range(3) for j in range(3) if (i + j) % 2 == 0]
    G["barres"] = [rect(6, 15, 5, 12), rect(13.5, 6, 5, 21, "a"), rect(21, 11, 5, 16)]
    G["triangle"] = [F([(16, 4.5), (28, 26.5), (4, 26.5)]), D(16, 19.5, 3.6, "a")]
    G["quarts"] = [T(arc(5, 5, 11, 0, 90), 3.6), T(arc(27, 27, 11, 180, 270), 3.6, "a")]
    G["etoile"] = [T([(16 + 11 * math.cos(math.radians(a)), 16 + 11 * math.sin(math.radians(a))),
                      (16 - 11 * math.cos(math.radians(a)), 16 - 11 * math.sin(math.radians(a)))], 3) for a in (90, 30, -30)] + [D(16, 16, 3.4, "a")]
    G["disques"] = [D(12, 16, 8.4), D(21, 16, 7, "a")]
    G["demi"] = [F(arc(16, 16, 11, 90, 270, 18)), F(arc(16, 16, 11, -90, 90, 18), "a")]
    G["escalier"] = [T([(5, 26), (5, 20), (11, 20), (11, 14), (17, 14), (17, 8), (24, 8)], 3.2), D(25.5, 8, 3.2, "a")]
    G["eventail"] = [T([(6, 16), (27, 6)], 2.8), T([(6, 16), (27, 16)], 2.8), T([(6, 16), (27, 26)], 2.8), D(6.5, 16, 4, "a")]
    G["sablier"] = [F([(4.5, 6), (16, 16), (4.5, 26)]), F([(27.5, 6), (16, 16), (27.5, 26)], "a")]
    G["hexagone"] = [T([(16 + 11 * math.cos(math.radians(60 * k - 90)), 16 + 11 * math.sin(math.radians(60 * k - 90))) for k in range(7)], 3),
                     D(16, 16, 3.6, "a")]
    G["carre"] = [T([(6, 6), (26, 6), (26, 26), (6, 26), (6, 6)], 3.2), rect(12.5, 12.5, 7, 7, "a")]
    G["chevrons"] = [T([(17, 6), (8, 16), (17, 26)], 3.4), T([(25, 6), (16, 16), (25, 26)], 3.4, "a")]
    G["spirale"] = [T([(16 + (1.5 + 1.75 * t) * math.cos(t * 1.15), 16 + (1.5 + 1.75 * t) * math.sin(t * 1.15)) for t in (i / 8 for i in range(48))], 2.8),
                    D(16 + (1.5 + 1.75 * 6) * math.cos(6 * 1.15), 16 + (1.5 + 1.75 * 6) * math.sin(6 * 1.15), 3.2, "a")]
    G["tirets"] = [T([(6, 13), (13, 6)], 3.2), T([(8, 24), (24, 8)], 3.2, "a"), T([(19, 26), (26, 19)], 3.2)]
    G["croix"] = [T([(16, 5), (16, 27)], 3.6), T([(5, 16), (27, 16)], 3.6, "a")]
    G["lune"] = [D(16, 16, 11), D(20.5, 11.5, 8, "f"), D(23, 23, 3, "a")]
    return G


GLYPHES = _marques()
# la marque de chaque motif de couverture
MARQUE_DE = {
    "semis": "onde", "arcs": "arc", "anneaux": "anneaux", "reseau": "eventail", "automate": "damier", "trame": "lune",
    "rayures": "tirets", "helice": "ondes", "pavage": "quarts", "flocon": "etoile", "trajectoires": "chevrons", "taches": "disques",
    "pixels": "grille", "colonnes": "barres", "plan": "carre", "lettres": "lettre",
    "pelote": "spirale", "blobs": "anneau", "binodale": "demi", "ternaire": "triangle", "phases": "points", "spherolites": "etoile",
    "masses": "barres", "nodules": "anneau", "fibres": "tirets", "traction": "eventail", "module": "escalier", "rheologie": "tirets",
    "cascade": "points", "dts": "ondes", "arrhenius": "eventail", "semenov": "onde", "mccabe": "escalier", "amortie": "onde",
    "maillage": "triangle", "tangentes": "quarts", "cube": "hexagone", "isoreponses": "anneaux", "pareto": "barres",
    "braises": "triangle", "eventails": "sablier", "panache": "disques", "carreaux": "grille",
}
FORMES = {"carre": "carre", "carree": "carre", "square": "carre", "rond": "rond", "ronde": "rond", "round": "rond", "disque": "rond",
          "nu": "nu", "nue": "nu", "seul": "nu", "bare": "nu"}
POLICE_LETTRE = "system-ui,-apple-system,Segoe UI,Helvetica,Arial,sans-serif"


def marque(nom):
    """Nom d'une marque (« onde »), d'un motif (« semis » → onde) ou alias de motif ; None sinon."""
    if nom in GLYPHES or nom == "lettre":
        return nom
    nom = ALIAS.get(nom, nom)
    return MARQUE_DE.get(nom)


# ---------- choix ----------

def bloc(texte):
    """Le SVG d'un bloc « ::: icone » (Markdown ou HTML), ou None."""
    m = re.search(r"^\s*:{3,}\s*\{?\.?icone\}?\s*$\n(.*?)^\s*:{3,}\s*$", texte or "", re.S | re.M)
    if not m:
        m = re.search(r'<div class="icone"[^>]*>(.*?)</div>', texte or "", re.S)
    if m and "<svg" in m.group(1):
        return m.group(1).strip()
    return None


def lire(valeur, avis):
    """« icone: flocon claire rond » → dict ; adresse ou « non » à part."""
    v = (valeur or "").strip()
    if not v:
        return {}
    if v.lower() in ("non", "no", "aucune", "aucun", "none", "false"):
        return {"aucune": True}
    if re.match(r"(data:|https?:|/|\./|\.\./)", v) or re.search(r"\.(svg|png|ico|jpe?g|gif|webp)([?#].*)?$", v, re.I):
        return {"adresse": v}
    out = {}
    for mot in v.split():
        m = sans_accents(mot.lower())
        if marque(m) or m in ("initiale", "letter"):
            out["glyphe"] = marque(m) or "lettre"
        elif m in couverture.TEINTES:
            out["teinte"] = couverture.TEINTES[m]
        elif m in FORMES:
            out["forme"] = FORMES[m]
        elif re.fullmatch(r"#[0-9a-f]{3,8}", m):
            out["encre"] = mot
        elif out.get("glyphe") == "lettre" and len(mot) <= 2:
            out["lettre"] = mot
        else:
            avis.append(f"icone : « {mot} » inconnu (marques : python3 icone.py, ou un nom de motif ; lettre ; teintes claire, "
                        "encre, sombre ; formes carre, rond, nu ; ou une adresse)")
    return out


def choisir(meta, encre, source="", lang="fr"):
    """Le favicon d'une page : rend {"svg", "png" (fonction de la taille, ou None), "resume"} ou None (« icone: non »).
    meta : l'en-tête (celui de l'accueil pour un cours) ; encre : son encre ; source : son texte (blocs ::: icone et
    ::: couverture)."""
    avis = []
    v = lire(meta.get("icone", ""), avis)
    if v.get("aucune"):
        return {"aucune": True, "resume": "aucun", "avis": avis}
    if v.get("adresse"):
        return {"adresse": v["adresse"], "resume": "adresse", "avis": avis}
    encre_page = v.get("encre") or encre or ""
    teinte, glyphe, origine = v.get("teinte"), v.get("glyphe"), "choisi"
    dessin_couv = bool(re.search(r'^\s*:{3,}\s*\{?\.?couverture\b|<div class="couverture"', source or "", re.M))
    voulu = (meta.get("couverture") or "").strip().lower()
    if voulu not in ("non", "no", "false") and (voulu or dessin_couv):
        g = couverture.reglages(dict(meta, tirage=encre_page), perso=dessin_couv)
        encre_page = v.get("encre") or g["tirage"]
        teinte = teinte or g["teinte"]
        if not glyphe and marque(g["motif"]):
            glyphe, origine = marque(g["motif"]), "couverture : " + g["motif"]
    perso = bloc(source)
    if perso and not v.get("glyphe"):
        glyphe, origine = "personnel", "dessin"
    if not glyphe:
        total = couverture.classement(meta)
        meilleur = max(total.values(), default=0)
        if meilleur:
            egaux = sorted(m for m, s in total.items() if s == meilleur)
            m = egaux[couverture.graine_de(meta) % len(egaux)]
            glyphe, origine = marque(m), "sujet : " + m
        else:
            glyphe, origine = "losange", "défaut"
    teinte, encre = teinte or "encre", encre_page or "#6b6b6b"
    forme = v.get("forme", "carre")
    pal = couverture.palette(encre, teinte)
    if forme == "nu":
        pal = dict(pal, ce=couverture.palette(encre, "claire")["ca"], ca=couverture.palette(encre, "claire")["ca"])
    lettre = None
    if glyphe == "lettre":
        lettre = v.get("lettre") or next((c for c in (meta.get("court") or meta.get("titre") or "T") if c.isalnum()), "T")
        lettre = lettre[:2].upper() if len(lettre) == 1 else lettre[:2]
    svg = dessiner(glyphe, pal, forme, perso=perso, lettre=lettre)
    prims = primitives_de(perso) if glyphe == "personnel" and perso else GLYPHES.get(glyphe)
    rendu = (lambda taille, plein=False: png(prims, pal, taille, "carre" if plein else forme)) if prims else None
    return {"svg": svg, "png": rendu, "resume": f"{glyphe if glyphe != 'personnel' else 'dessin'} ({origine}), {teinte}" + (f", {forme}" if forme != "carre" else ""),
            "avis": avis, "glyphe": glyphe, "palette": pal}


# ---------- dessin à soi → primitives (pour le PNG) ----------

def _sous_chemins(d):
    """Sous-chemins (points, fermé) d'un attribut d « M L H V C Q Z » (absolus ou relatifs) ; None si autre chose."""
    jetons = re.findall(r"[A-Za-z]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?", d)
    out, pts, cmd, i, x, y = [], [], None, 0, 0.0, 0.0
    debut = (0.0, 0.0)
    while i < len(jetons):
        if jetons[i].isalpha():
            cmd, i = jetons[i], i + 1
            if cmd in "Zz":
                if pts:
                    out.append((pts, True))
                pts, (x, y) = [], debut
                continue
            if cmd not in "MmLlHhVvCcQq":
                return None
        rel = cmd.islower()
        nb = {"m": 2, "l": 2, "h": 1, "v": 1, "c": 6, "q": 4}[cmd.lower()]
        try:
            v = [float(t) for t in jetons[i:i + nb]]
        except ValueError:
            return None
        if len(v) < nb:
            return None
        i += nb
        c = cmd.lower()
        if c == "m":
            if pts:
                out.append((pts, False))
            x, y = (x + v[0], y + v[1]) if rel else (v[0], v[1])
            pts, debut = [(x, y)], (x, y)
            cmd = "l" if rel else "L"
        elif c in "lhv":
            if c == "l":
                x, y = (x + v[0], y + v[1]) if rel else (v[0], v[1])
            elif c == "h":
                x = x + v[0] if rel else v[0]
            else:
                y = y + v[0] if rel else v[0]
            pts.append((x, y))
        else:
            ctrl = [(x + v[k], y + v[k + 1]) if rel else (v[k], v[k + 1]) for k in range(0, nb, 2)]
            p0 = (x, y)
            for t in (j / 10 for j in range(1, 11)):
                if c == "q":
                    (ax, ay), (bx, by) = ctrl
                    px = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * ax + t * t * bx
                    py = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * ay + t * t * by
                else:
                    (ax, ay), (bx, by), (cx_, cy_) = ctrl
                    px = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * ax + 3 * (1 - t) * t * t * bx + t ** 3 * cx_
                    py = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * ay + 3 * (1 - t) * t * t * by + t ** 3 * cy_
                pts.append((px, py))
            x, y = ctrl[-1]
    if pts:
        out.append((pts, False))
    return out


def primitives_de(svg):
    """Primitives d'un dessin à soi (circle, ellipse, rect, line, polyline, polygon, path droit ou en Bézier), pour en
    tirer un PNG ; None s'il contient autre chose (texte, arcs, transformations, motifs)."""
    role = {"currentcolor": "g", "var(--ca)": "a", "var(--cf)": "f", "var(--cd)": "g"}
    prims = []
    for m in re.finditer(r"<(\w+)\b([^>]*?)/?>", svg):
        tag, a = m.group(1).lower(), dict(re.findall(r'([\w-]+)\s*=\s*["\']([^"\']*)["\']', m.group(2)))
        if tag in ("svg", "g", "defs") or tag.startswith("/"):
            continue
        if tag not in ("circle", "ellipse", "rect", "line", "polyline", "polygon", "path") or "transform" in a:
            return None
        fond, trait_ = role.get(a.get("fill", "none").lower()), role.get(a.get("stroke", "none").lower())
        if a.get("fill", "none").lower() not in ("none", *role) or a.get("stroke", "none").lower() not in ("none", *role):
            return None
        w = float(a.get("stroke-width", 1))
        f = lambda k, d=0.0: float(a.get(k, d))
        if tag == "circle":
            if fond:
                prims.append(D(f("cx"), f("cy"), f("r"), fond))
            if trait_:
                prims.append(C(f("cx"), f("cy"), f("r"), w, trait_))
            continue
        if tag == "ellipse":
            chemins = [(ellipse(f("cx"), f("cy"), f("rx"), f("ry"))[:-1], True)]
        elif tag == "rect":
            x, y, l, h = f("x"), f("y"), f("width"), f("height")
            chemins = [([(x, y), (x + l, y), (x + l, y + h), (x, y + h)], True)]
        elif tag == "line":
            chemins = [([(f("x1"), f("y1")), (f("x2"), f("y2"))], False)]
        elif tag in ("polyline", "polygon"):
            v = [float(t) for t in re.findall(r"-?(?:\d+\.?\d*|\.\d+)", a.get("points", ""))]
            chemins = [(list(zip(v[::2], v[1::2])), tag == "polygon")]
        else:
            chemins = _sous_chemins(a.get("d", ""))
            if chemins is None:
                return None
        for pts, ferme in chemins:
            if len(pts) < 2:
                continue
            if fond:
                prims.append(F(pts, fond))
            if trait_:
                prims.append(T(pts + ([pts[0]] if ferme else []), w, trait_))
    return prims or None


# ---------- SVG ----------

def _n(x):
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _pts(pts):
    return "M" + "L".join(f"{_n(x)} {_n(y)}" for x, y in pts)


def couleur(role, pal):
    return {"g": pal["ce"], "a": pal["ca"], "f": pal["cf"]}[role]


def primitives_svg(prims, pal):
    out = []
    for p in prims:
        k, c = p[0], couleur(p[-1], pal)
        if k == "t":
            if p[2] > .05:
                out.append(f"<path d='{_pts(p[1])}' fill='none' stroke='{c}' stroke-width='{_n(p[2])}' stroke-linecap='round' stroke-linejoin='round'/>")
        elif k == "f":
            out.append(f"<path d='{_pts(p[1])}Z' fill='{c}'/>")
        elif k == "d":
            if p[3] > 0:
                out.append(f"<circle cx='{_n(p[1])}' cy='{_n(p[2])}' r='{_n(p[3])}' fill='{c}'/>")
        elif k == "c":
            if p[3] > 0:
                out.append(f"<circle cx='{_n(p[1])}' cy='{_n(p[2])}' r='{_n(p[3])}' fill='none' stroke='{c}' stroke-width='{_n(p[4])}'/>")
    return "".join(out)


def dessiner(glyphe, pal, forme="carre", perso=None, lettre=None):
    """Le SVG du favicon (texte), tuile comprise."""
    tuile = {"carre": f"<rect width='32' height='32' rx='7' fill='{pal['cf']}'/>",
             "rond": f"<circle cx='16' cy='16' r='16' fill='{pal['cf']}'/>", "nu": ""}[forme]
    if glyphe == "personnel" and perso:
        dedans = re.sub(r"^.*?<svg\b[^>]*>|</svg>\s*$", "", perso.strip(), flags=re.S)
        dedans = (dedans.replace("currentColor", pal["ce"]).replace("var(--ca)", pal["ca"]).replace("var(--cf)", pal["cf"])
                  .replace("var(--cd)", couverture.hexa(couverture.melange(couverture.rgb(pal["cf"]), couverture.rgb(pal["ce"]), .42))))
        corps = f"<g fill='none' stroke-linecap='round' stroke-linejoin='round'>{dedans.replace(chr(34), chr(39))}</g>"
    elif glyphe == "lettre":
        taille = 21 if len(lettre or "") < 2 else 15
        corps = (f"<text x='16' y='{_n(16 + taille * .36)}' text-anchor='middle' font-family='{POLICE_LETTRE}' font-weight='700' "
                 f"font-size='{taille}' fill='{pal['ce']}'>{html.escape(lettre or 'T', quote=False)}</text>")
    else:
        corps = primitives_svg(GLYPHES[glyphe], pal)
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>{tuile}{corps}</svg>"


def uri_svg(svg):
    return ("data:image/svg+xml," + svg.replace("%", "%25").replace("#", "%23").replace("<", "%3C").replace(">", "%3E")
            .replace('"', "'").replace("&", "%26"))


# ---------- PNG (sans dépendance) ----------

def _dist_seg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / l2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _couverture(p, s, taille):
    """{pixel: couverture} d'une primitive : distance au bord, lissée sur un pixel ; segment par segment (chaque
    segment dans sa boîte), intérieur des polygones par lignes de balayage."""
    cov, k = {}, p[0]

    def poser(i, v):
        if v > cov.get(i, 0.0):
            cov[i] = v

    def boite(x0, y0, x1, y1):
        return (range(max(0, int(y0 * s) - 1), min(taille, int(y1 * s) + 2)),
                range(max(0, int(x0 * s) - 1), min(taille, int(x1 * s) + 2)))

    if k in ("d", "c"):
        cx, cy, r = p[1], p[2], p[3]
        w = p[4] / 2 if k == "c" else 0
        lignes, cols = boite(cx - r - w, cy - r - w, cx + r + w, cy + r + w)
        for py in lignes:
            y = (py + .5) / s
            for px in cols:
                d = math.hypot((px + .5) / s - cx, y - cy) - r
                d = abs(d) - w if k == "c" else d
                v = .5 - d * s
                if v > 0:
                    poser(py * taille + px, min(1.0, v))
        return cov
    pts = p[1]
    if k == "t":
        w = p[2] / 2
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            lignes, cols = boite(min(ax, bx) - w, min(ay, by) - w, max(ax, bx) + w, max(ay, by) + w)
            for py in lignes:
                y = (py + .5) / s
                for px in cols:
                    v = .5 - (_dist_seg((px + .5) / s, y, ax, ay, bx, by) - w) * s
                    if v > 0:
                        poser(py * taille + px, min(1.0, v))
        return cov
    # polygone : intérieur par balayage (centre des pixels), puis bord lissé par la distance aux arêtes
    m = len(pts)
    ys = [q[1] for q in pts]
    for py in range(max(0, int(min(ys) * s) - 1), min(taille, int(max(ys) * s) + 2)):
        y = (py + .5) / s
        xs = sorted(pts[i][0] + (y - pts[i][1]) * (pts[(i + 1) % m][0] - pts[i][0]) / (pts[(i + 1) % m][1] - pts[i][1])
                    for i in range(m) if (pts[i][1] > y) != (pts[(i + 1) % m][1] > y))
        for a, b in zip(xs[::2], xs[1::2]):
            for px in range(max(0, int(a * s - .5) + 1), min(taille, int(b * s - .5) + 1)):
                cov[py * taille + px] = 1.0
    proche = {}
    for i in range(m):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % m]
        lignes, cols = boite(min(ax, bx) - 1 / s, min(ay, by) - 1 / s, max(ax, bx) + 1 / s, max(ay, by) + 1 / s)
        for py in lignes:
            y = (py + .5) / s
            for px in cols:
                d = _dist_seg((px + .5) / s, y, ax, ay, bx, by) * s
                j = py * taille + px
                if d < 1 and d < proche.get(j, 9):
                    proche[j] = d
    for j, d in proche.items():
        cov[j] = max(0.0, min(1.0, .5 + d if j in cov else .5 - d))
    return cov


def png(prims, pal, taille=180, forme="carre"):
    """PNG du favicon : chaque pixel prend la couverture de chaque primitive d'après sa distance au bord (lissage d'un
    pixel). forme « carre » : tuile pleine à coins droits (l'écran d'accueil arrondit lui-même) ; « rond » : disque
    sur blanc ; « nu » : glyphe sur blanc."""
    s = taille / 32
    blanc = (1.0, 1.0, 1.0)
    fond = blanc if forme in ("nu", "rond") else couverture.rgb(pal["cf"])
    r_, g_, b_ = [fond[0]] * (taille * taille), [fond[1]] * (taille * taille), [fond[2]] * (taille * taille)
    if forme == "rond":
        prims = [("d", 16, 16, 16, "f")] + list(prims)
    for p in prims:
        if (p[0] == "t" and p[2] <= .05) or (p[0] in ("d", "c") and p[3] <= 0):
            continue
        c = couverture.rgb(couleur(p[-1], pal))
        for j, v in _couverture(p, s, taille).items():
            r_[j] += (c[0] - r_[j]) * v
            g_[j] += (c[1] - g_[j]) * v
            b_[j] += (c[2] - b_[j]) * v
    octets = bytearray()
    for y in range(taille):
        octets.append(0)
        for j in range(y * taille, (y + 1) * taille):
            octets += bytes((round(min(1.0, max(0.0, r_[j])) * 255), round(min(1.0, max(0.0, g_[j])) * 255),
                             round(min(1.0, max(0.0, b_[j])) * 255)))

    def morceau(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)

    return (b"\x89PNG\r\n\x1a\n" + morceau(b"IHDR", struct.pack(">IIBBBBB", taille, taille, 8, 2, 0, 0, 0))
            + morceau(b"IDAT", zlib.compress(bytes(octets), 9)) + morceau(b"IEND", b""))


def uri_png(donnees):
    return "data:image/png;base64," + base64.b64encode(donnees).decode()


# ---------- planche ----------

def planche(encre, teinte="encre"):
    """Corps HTML d'une page : chaque marque à 16, 32 et 64 px, sur une barre d'onglets claire et une sombre, avec les
    motifs de couverture qui y renvoient."""
    pal = couverture.palette(encre, teinte)
    e = html.escape
    cases = []
    for nom in list(GLYPHES) + ["lettre"]:
        svg = uri_svg(dessiner(nom, pal, lettre="T" if nom == "lettre" else None))
        tailles = "".join(f'<img src="{e(svg)}" width="{t}" height="{t}" alt="">' for t in (16, 32, 64))
        motifs_ = [m for m, g in MARQUE_DE.items() if g == nom]
        cases.append(f'<div class="ico-case"><div class="ico-barre">{tailles}</div><div class="ico-barre ico-nuit">{tailles}</div>'
                     f'<p><code>icone: {nom}</code>' + (f"<br>{e(', '.join(motifs_))}" if motifs_ else "") + "</p></div>")
    return f'<div class="large"><div class="ico-planche">{"".join(cases)}</div></div>'


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--png":
        nom, sortie = sys.argv[2], sys.argv[3]
        open(sortie, "wb").write(png(GLYPHES[nom], couverture.palette(sys.argv[4] if len(sys.argv) > 4 else "#0078bf", "encre"), 180))
    else:
        print("Marques de favicon (icone: nom) : " + ", ".join(GLYPHES) + ", lettre")
        print("Un nom de motif vaut sa marque :")
        for dom, ms in CATALOGUE.items():
            print(f"  {dom.lower()} : " + ", ".join(f"{m} → {MARQUE_DE.get(m, '?')}" for m in ms))
