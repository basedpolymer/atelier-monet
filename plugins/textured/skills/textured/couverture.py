"""TeXtured — couverture de document, sur demande (« couverture: » dans l'en-tête, ou --couverture).

Un portrait 2:3 : aplat tiré de l'encre de la page (« tirage: »), titre en Latin Modern Sans gras capitales, ligne en
italique, illustration générative liée au document, fiche de laboratoire remplie par le document, pied
« AUTEUR · ANNÉE  /  N MOTS ». Le même objet sert partout, ses tailles étant en cqi : vignette à côté du titre (avec une
épaisseur de pages proportionnelle à la longueur), première page du PDF à fond perdu, image de partage (--apercu).

Les motifs (dessins génératifs, rangés par domaine avec les mots du sujet qui les appellent) sont dans motifs.py. Quatre
places : haut (titre, illustration cadrée, fiche), bas (illustration, puis titre au tiers bas), plein (illustration à
fond perdu sur le haut, titre dessous), fond (motif sur toute la couverture, titre dans un cartouche). Un bloc
« ::: couverture » remplace l'illustration (SVG carré) ou la couverture entière (SVG 200 × 300).

    python3 couverture.py --catalogue [--court]  # le catalogue des motifs, en Markdown (--court : pour couverture.md)
    python3 couverture.py "sujet du document"  # les motifs qui conviennent, du meilleur au moins bon
"""
import hashlib
import html
import math
import random
import re
import sys
from collections import Counter

from motifs import ALIAS, CATALOGUE, DOMAINE, MOTIFS, n, sans_accents, scores

# encres de risographie : celle de la couverture quand la page n'a pas de « tirage: »
ENCRES = ("#ff48b0", "#f15060", "#ff6c2f", "#ffb511", "#ffe800", "#00a95c", "#00838a", "#0078bf", "#3255a4", "#3d5588",
          "#765ba7", "#9d7ad2", "#914e72", "#a75154", "#68724d", "#407060", "#bb8b41", "#82d8d5", "#5ec8e5")
CREME, NOIR, NUIT = (0.961, 0.941, 0.902), (0.098, 0.090, 0.086), (0.075, 0.075, 0.078)
# chasse des capitales de Latin Modern Sans gras (millièmes de cadratin) : taille du titre
CHASSE = {**dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", (733, 733, 703, 794, 642, 611, 733, 794, 331, 519, 764, 581, 978, 794,
                                                    794, 703, 794, 703, 611, 733, 764, 733, 1039, 733, 733, 672))),
          "Œ": 1069, "Æ": 947, " ": 367, "-": 367, "'": 306, "’": 306, ":": 306, ",": 306, ".": 306, "&": 831, "?": 519,
          "!": 367, "(": 428, ")": 428, "/": 550, "«": 550, "»": 550, **{c: 550 for c in "0123456789"}}
TEXTES = {
    "fr": {"mots": "mots", "sections": "Sections", "figures": "Figures", "formules": "Formules", "exercices": "Exercices",
           "lecture": "Lecture", "min": "min", "mille": "\u202f", "mot": "mot"},
    "en": {"mots": "words", "sections": "Sections", "figures": "Figures", "formules": "Equations", "exercices": "Exercises",
           "lecture": "Reading", "min": "min", "mille": ",", "mot": "word"},
}
PROTEGE = re.compile(r"<(script|style|pre|textarea|code)\b[^>]*>.*?</\1\s*>", re.S | re.I)
MOT = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*|\d+(?:[.,]\d+)*")
VIDES = set("comme toujours chaque pendant depuis encore partir plusieurs autres ensuite également lorsque quelques "
            "beaucoup pourquoi cependant certains certaines without between through should because however within "
            "another before after these those their there where which other about always".split())


# ---------- couleurs ----------

def rgb(h):
    h = h.lstrip("#")
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h[:3])
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def hexa(c):
    return "#" + "".join(f"{round(max(0, min(1, v)) * 255):02x}" for v in c)


def melange(a, b, t):
    """t de b dans a."""
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def luminance(c):
    lin = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contraste(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def oklab(c):
    lin = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    l = (0.4122214708 * lin[0] + 0.5363325363 * lin[1] + 0.0514459929 * lin[2]) ** (1 / 3)
    m = (0.2119034982 * lin[0] + 0.6806995451 * lin[1] + 0.1073969566 * lin[2]) ** (1 / 3)
    s = (0.0883024619 * lin[0] + 0.2817188376 * lin[1] + 0.6299787005 * lin[2]) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s, 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def depuis_oklab(L, a, b):
    l, m, s = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3, (L - 0.1055613458 * a - 0.0638541728 * b) ** 3, (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    lin = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
           -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
    return tuple(max(0.0, min(1.0, 12.92 * v if v <= 0.0031308 else 1.055 * max(v, 0) ** (1 / 2.4) - 0.055)) for v in lin)


def teinte_de(c, L, chroma):
    """Même teinte que c, à la clarté L et à la saturation chroma (OKLCH)."""
    _, a, b = oklab(c)
    h = math.hypot(a, b) or 1
    return depuis_oklab(L, a / h * chroma, b / h * chroma)


def tourne(c, degres, L, chroma):
    """La teinte de c tournée de « degres » sur le cercle (OKLCH), à la clarté L et à la saturation chroma."""
    _, a, b = oklab(c)
    h = math.atan2(b, a) + math.radians(degres)
    return depuis_oklab(L, chroma * math.cos(h), chroma * math.sin(h))


def teinte_abs(h, L, chroma):
    """Couleur de teinte h (degrés, OKLCH), clarté L, saturation chroma."""
    return depuis_oklab(L, chroma * math.cos(math.radians(h)), chroma * math.sin(math.radians(h)))


def vif(h, L, chroma):
    """teinte_abs hors de la zone olive : entre 75 et 125°, une teinte assez sombre vire au kaki ; on l'écarte vers
    l'orange (sous 100°) ou vers le vert (au-dessus)."""
    h %= 360
    if 75 <= h <= 125 and L < .72:
        h = 60 if h < 100 else 140
    return teinte_abs(h, L, chroma)


def palette(encre, teinte, mono=False):
    """Fond, texte, accent et trait doux de la couverture, tirés de l'encre. claire : pastel de l'encre, texte noir ;
    encre : aplat de l'encre, texte noir ou crème, accent en réserve (le papier) ; sombre : nuit teintée de l'encre,
    texte crème. Sur claire et sombre : l'accent prend la teinte décalée de 150° (la complémentaire stricte vire au brun),
    saturée ; g1 et g2 bornent le dégradé des motifs en traits, de l'encre à son opposée pâle et peu saturée (l'accent
    reste distinct) ; m1 à m4 sont quatre encres (0, 70, 220 et 290° : aucune sur l'accent) pour les formes pleines.
    mono, ou l'aplat : m1 à m4 valent le texte (un motif qui les écrit lui-même reste d'une encre)."""
    e = rgb(encre)
    c = math.hypot(*oklab(e)[1:])
    if teinte == "encre":
        fond = e
        texte = NOIR if contraste(NOIR, e) >= contraste(CREME, e) else CREME
        accent = CREME if texte == NOIR else teinte_de(e, .9, min(c * .5, .07))
        if contraste(accent, fond) < 1.8:
            # encre claire (jaune, menthe…) : la réserve ne se voit pas, une seconde encre de teinte éloignée la remplace
            h = math.atan2(*reversed(oklab(e)[1:]))
            ecart = lambda x: abs(math.remainder(math.atan2(*reversed(oklab(rgb(x))[1:])) - h, 2 * math.pi))
            accent = rgb(max((x for x in ENCRES if contraste(rgb(x), fond) >= 2), key=lambda x: contraste(rgb(x), fond) * (1 + ecart(x))))
    else:
        h0 = math.degrees(math.atan2(*reversed(oklab(e)[1:])))
        if teinte == "sombre":
            fond, texte = teinte_de(e, .25, min(c * .3, .035)), CREME
            accent = e
            if not mono:
                # en éclaircissant à saturation gardée, jusqu'au contraste voulu
                accent = next((x for x in (vif(h0 + 150, L / 100, .13) for L in range(76, 96, 2)) if contraste(x, fond) >= 3.4),
                              vif(h0 + 150, .94, .08))
            while contraste(accent, fond) < 3.4:
                accent = melange(accent, CREME, .12)
        else:
            fond, texte = teinte_de(e, .915, min(c * .45, .065)), melange(NOIR, e, .08)
            accent = e
            if not mono:
                # en assombrissant à saturation gardée (le mélange au noir donnait du brun), jusqu'au contraste voulu
                accent = next((x for x in (vif(h0 + 150, L / 100, .17) for L in range(64, 30, -2)) if contraste(x, fond) >= 2.4),
                              vif(h0 + 150, .3, .12))
            while contraste(accent, fond) < 2.4:
                accent = melange(accent, NOIR, .12)
    pal = {"cf": hexa(fond), "ce": hexa(texte), "ca": hexa(accent), "cd": hexa(melange(fond, texte, .42))}
    if teinte in ("claire", "sombre") and not mono:
        clair = teinte == "sombre"
        pal["g1"] = hexa(vif(h0, .74 if clair else .5, .12 if clair else .15))
        pal["g2"] = hexa(vif(h0 + 180, .87 if clair else .7, .07 if clair else .08))
        for k, (dh, L) in enumerate(((0, .55), (70, .62), (220, .6), (290, .6)), 1):
            pal[f"m{k}"] = hexa(vif(h0 + dh, L + (.2 if clair else 0), .11 if clair else .15))
    else:
        for k in range(1, 5):
            pal[f"m{k}"] = pal["ce"]
    return pal


# ---------- mesures du document ----------

def texte_brut(fragment):
    t = PROTEGE.sub(" ", fragment)
    t = re.sub(r"\\\[.+?\\\]|\\\(.+?\\\)", " ", t, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", t))


def mesurer(corps, plan, titre, brut=None):
    """Mesures du document : corps transformé (identifiants des sections), brut : texte de l'auteur, pour les mots."""
    brut = corps if brut is None else brut
    texte = texte_brut(brut)
    mots = MOT.findall(texte)
    sections = []
    for niveau, ident, h in plan:
        num = re.search(r'<span class="num">(.*?)</span>', h)
        num = num.group(1) if num else ""
        if niveau == 2:
            sections.append({"id": ident, "num": num, "subs": [], "mots": 0, "exo": False})
        elif sections:
            sections[-1]["subs"].append(num)
    debuts = [corps.find(f'id="{s["id"]}"') for s in sections]
    for k, s in enumerate(sections):
        bout = corps[debuts[k]:debuts[k + 1] if k + 1 < len(sections) else len(corps)]
        s["mots"] = len(MOT.findall(texte_brut(bout)))
        s["exo"] = bool(re.search(r'class="(?:exo|qcm|qnum)\b', bout))
    frequents = Counter(sans_accents(m.lower()) for m in mots if len(m) >= 5 and m.isalpha())
    for v in VIDES:
        frequents.pop(v, None)
    lettres = Counter(c for c in sans_accents(texte.upper()) if "A" <= c <= "Z")
    return {
        "mots": len(mots), "titre": titre, "sections": sections,
        "paragraphes": [k for k in (len(MOT.findall(texte_brut(p))) for p in re.findall(r"<p\b[^>]*>(.*?)</p>", brut, re.S)) if k],
        "figures": len(re.findall(r"<figure\b", corps)) + len(re.findall(r"<table\b", corps)),
        "formules": len(re.findall(r"\\\(|\\\[", corps)),
        "exercices": len(re.findall(r'class="(?:exo|qcm|qnum)\b', corps)),
        "frequents": [m for m, _ in frequents.most_common(30)], "lettres": lettres,
    }


TEINTES = {"claire": "claire", "clair": "claire", "light": "claire", "encre": "encre", "pleine": "encre", "ink": "encre",
           "sombre": "sombre", "nuit": "sombre", "dark": "sombre"}
PLACES = {"haut": "haut", "top": "haut", "bas": "bas", "bottom": "bas", "plein": "plein", "perdu": "plein", "bleed": "plein",
          "fond": "fond", "cartouche": "fond", "poster": "fond"}
# motifs qui font de bonnes textures : quand la place n'est pas dite, ils passent parfois à fond perdu ou en fond
TEXTURES = {"semis", "automate", "pavage", "trajectoires", "taches", "pixels", "anneaux", "pelote", "spherolites", "nodules",
            "fibres", "maillage", "blobs", "phases", "binodale", "braises", "carreaux", "amortie", "isoreponses", "panache",
            "eventails", "tangentes"}
# poids des champs de l'en-tête quand le motif est tiré du sujet
POIDS = (("titre", 3), ("court", 3), ("soustitre", 2), ("surtitre", 2), ("cours", 1.5), ("description", 1))


# ---------- assemblage ----------

def extraire_bloc(corps, classe="couverture"):
    """Bloc « ::: couverture » (un SVG écrit pour ce document) : ôté du corps, rendu à part."""
    m = re.search(rf'<div class="{classe}"[^>]*>', corps)
    if not m:
        return corps, None
    niveau = 1
    for f in re.finditer(r"<(/?)div\b[^>]*>", corps[m.end():]):
        niveau += -1 if f.group(1) else 1
        if niveau == 0:
            dedans = corps[m.end():m.end() + f.start()]
            return corps[:m.start()] + corps[m.end() + f.end():], dedans
    return corps, None


def largeur_titre(mot, t):
    return (sum(CHASSE.get(c, 760) for c in mot) / 1000 + .01 * len(mot)) * t


def lignes_titre(mots, t):
    """Nombre de lignes du titre en capitales au corps t (cqi) sur la largeur utile (84 cqi) ; None si un mot déborde."""
    lignes, courant, utile = 1, 0.0, 84 * .95
    for m in mots:
        w = largeur_titre(m, t)
        if w > utile:
            return None
        if courant and courant + CHASSE[" "] / 1000 * t + w > utile:
            lignes, courant = lignes + 1, w
        else:
            courant += (CHASSE[" "] / 1000 * t if courant else 0) + w
    return lignes


def disposer(place, titre, sous, sur, n_fiche):
    """Corps du titre (cqi) et nombre de cases de fiche gardées. Hauteur totale 150 cqi, largeur utile 84 : le plus
    grand titre (trois lignes au plus, quatre en bas) qui laisse à l'illustration une hauteur suffisante ; la fiche ne
    reste qu'en haut, et si elle coûte peu au titre. À fond perdu, l'illustration mange la marge du haut ; en fond, le
    cartouche ajoute ses marges et l'« illustration » est le motif qu'on voit entre cartouche et pied."""
    mots = titre.upper().split() or ["?"]
    # ligne en italique : 5,4 cqi, chasse moyenne 0,45 cadratin, trois lignes au plus
    l_sous = min(3, math.ceil(len(sous) * .45 * 5.4 / (84 * .9))) if sous else 0
    lignes_max = 4 if place == "bas" else 3
    images = {"plein": (78, 70, 62), "fond": (58, 48, 40)}.get(place, (74, 64, 56))

    def plus_grand(fiche, image_min):
        fixe = 13.5 + 3.2 + (2.8 * 1.25 + 2.2 if sur else 0) + (l_sous * 5.4 * 1.16 + 2.2 if sous else 0)
        fixe += 3.4 * (4 if fiche else 3) + (math.ceil(fiche / 2) * 6.4 - 1 if fiche else 0) + .4
        fixe += {"plein": -7.5, "fond": 14}.get(place, 0)
        for t in [x / 4 for x in range(60, 23, -1)]:
            lignes = lignes_titre(mots, t * (1.1 if place == "fond" else 1))
            if lignes and lignes <= lignes_max and 150 - fixe - lignes * t * .98 >= image_min:
                return t
        return None

    for image_min in images:
        t0 = plus_grand(0, image_min)
        tf = plus_grand(n_fiche, image_min) if n_fiche and place == "haut" else None
        if tf and t0 and tf >= .85 * t0:
            return tf, n_fiche
        if t0:
            return t0, 0
    return 6.0, 0


def chiffre(k, lang):
    return f"{k:,}".replace(",", TEXTES[lang]["mille"])


def mots(k, lang, separateur=" "):
    return f'{chiffre(k, lang)}{separateur}{TEXTES[lang]["mots" if k > 1 else "mot"]}'


def lire_valeur(valeur, avis):
    """« couverture: helice sombre bas 2 » → (motif, teinte, place, variante) ; None pour ce qui n'est pas dit."""
    motif = teinte = place = None
    variante = 0
    for mot in re.split(r"[\s,;]+", sans_accents(valeur.lower())):
        if mot in ("", "oui", "yes", "auto", "true", "mono"):
            continue
        if mot in MOTIFS or mot in ALIAS:
            motif = ALIAS.get(mot, mot)
        elif mot in TEINTES:
            teinte = TEINTES[mot]
        elif mot in PLACES:
            place = PLACES[mot]
        elif mot.isdigit():
            variante = int(mot)
        else:
            proches = [m for m in MOTIFS if m.startswith(mot[:3])][:4]
            avis.append(f"couverture : « {mot} » inconnu ({'motifs proches : ' + ', '.join(proches) + ' ; ' if proches else ''}"
                        "liste : python3 couverture.py --catalogue ; teintes : claire, encre, sombre ; places : haut, bas, "
                        "plein, fond ; un nombre pour un autre tirage)")
    return motif, teinte, place, variante


def classement(meta):
    """Score de chaque motif d'après l'en-tête (titre et court comptent triple, sous-titre et rubrique double)."""
    total = Counter()
    for cle, p in POIDS:
        if meta.get(cle):
            for m, s in scores(meta[cle]).items():
                if s:
                    total[m] += p * s
    return total


def motif_du_sujet(meta, r):
    total = classement(meta)
    meilleur = max(total.values(), default=0)
    return r.choice(sorted(m for m, s in total.items() if s == meilleur) if meilleur else list(MOTIFS))


def graine_de(meta, variante=0):
    titre = (meta.get("court") or meta.get("titre") or "Sans titre").strip()
    return int(hashlib.sha256(f"{titre}|{variante}".encode()).hexdigest()[:12], 16)


def reglages(meta, perso=False, avis=None):
    """Ce que dit « couverture: », le reste tiré du titre (même document, même couverture) : motif, teinte, place,
    variante, encre et graine. Sert à la couverture et au favicon, qui la suit."""
    motif, teinte, place, variante = lire_valeur((meta.get("couverture") or "").strip(), [] if avis is None else avis)
    graine = graine_de(meta, variante)
    r = random.Random(graine)
    tirage = (meta.get("tirage") or "").strip()
    if not re.fullmatch(r"#[0-9a-fA-F]{3,8}", tirage):
        tirage = r.choice(ENCRES)
    teinte = teinte or r.choice(("claire", "claire", "encre", "encre", "sombre"))
    place_tiree = r.choice(("haut", "haut", "bas"))
    motif = "personnel" if perso else motif or motif_du_sujet(meta, r)
    if not place:
        place = place_tiree
        if motif in TEXTURES and random.Random(graine + 3).random() < .4:
            place = random.Random(graine + 5).choice(("plein", "fond"))
    return {"motif": motif, "teinte": teinte, "place": place, "variante": variante, "tirage": tirage, "graine": graine}


def entiere(perso):
    """Le SVG du bloc est-il une couverture entière (portrait, 200 × 300) plutôt qu'une illustration carrée ?"""
    m = re.search(r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', perso or "")
    return bool(m) and float(m.group(2)) > 1.25 * float(m.group(1))


def nettoyer_svg(perso, attributs):
    """Le SVG du bloc, sans le paragraphe que pandoc met parfois autour, avec des attributs ajoutés à sa balise."""
    svg = re.sub(r"^\s*<p>|</p>\s*$", "", perso.strip())
    return re.sub(r"<svg\b", "<svg " + attributs, svg, count=1)


# couleurs du motif (claire et sombre, hors « mono »). Un motif peut DÉCLARER son traitement dans COULEUR :
#   ("multi",)                    ses formes pleines en fill="currentColor" alternent quatre encres (--m1 à --m4) ;
#   ("degrade", sens[, centre])   ses traits en stroke="currentColor" passent en dégradé : sens h (gauche-droite),
#                                 v (haut-bas : une couleur par rangée), d (diagonale), r (rayons, depuis centre (x, y)) ;
#   ("uni",)                      rien ne change (l'accent seul reste complémentaire).
# Un motif non déclaré est classé sur son dessin : au moins 6 formes pleines, quatre encres ; sinon des traits, dégradé
# (en rayons s'il est dans RAYONNANTS, sinon dans un sens tiré de la graine). Un motif peut aussi poser lui-même ses
# encres, élément par élément : fill="var(--m2, currentColor)" (colorier n'y touche pas ; en mono et sur l'aplat,
# --m1 à --m4 valent le texte). Une forme pleine par élément, pas un chemin unique, pour que l'alternance existe.
RAYONNANTS = {"anneaux", "spherolites", "reseau", "flocon", "arcs"}
COULEUR = {
    # rangées empilées : une couleur par rangée
    "amortie": ("degrade", "v"), "dts": ("degrade", "v"), "fibres": ("degrade", "v"), "rheologie": ("degrade", "v"),
    "module": ("degrade", "v"), "helice": ("degrade", "v"),
    # colonnes ou défilement de gauche à droite
    "masses": ("degrade", "h"), "pareto": ("degrade", "h"), "semis": ("degrade", "h"), "trajectoires": ("degrade", "h"),
    "cascade": ("degrade", "h"), "eventails": ("degrade", "h"), "tangentes": ("degrade", "h"),
    # sphères éclairées : la lumière vient d'un coin, pas du centre
    "trame": ("degrade", "d"), "rayures": ("degrade", "d"),
}
SEUIL_MULTI = 6
# sciences exactes (physique et astronomie, Terre et climat, mathématiques, chimie générale)
COULEUR.update({
    # dessinés autour du centre du carré
    **{m: ("degrade", "r", (100, 100)) for m in ("galaxie", "angledor", "hyperbolique", "spirographe", "modulo", "laue", "agregat",
                                                 "brillouin", "entrelacs", "orbitales", "tesseract", "apollonius", "miroir")},
    # centre tiré par le motif : il pose lui-même son dégradé rayonnant (motifs.degrade_centre), colorier n'y touche pas
    **{m: ("uni",) for m in ("circumpolaire", "belousov", "liesegang", "collision", "kepler", "lentille", "rossby")},
    # rangées empilées : une couleur par rangée
    **{m: ("degrade", "v") for m in ("sismogramme", "paquets", "chromato", "raies", "isoclines")},
    # colonnes, de gauche à droite
    **{m: ("degrade", "h") for m in ("galton", "multiplets", "electrode", "ulam")},
    # pavages et formes pleines : quatre encres, même quand les formes sont peu nombreuses
    **{m: ("multi",) for m in ("ising", "penrose", "quatrecouleurs", "orgues", "carottes", "mendeleiev", "plissement", "dunes",
                               "dorsale")},
})
FORMES = re.compile(r'<(path|circle|rect|ellipse|polygon|polyline|line)\b[^>]*>')
SENS = {"h": (10, 100, 190, 100), "v": (100, 10, 100, 190), "d": (10, 190, 190, 10)}
_degrades = [0]


def colorier(svg, couleurs, motif, graine):
    """Le dessin d'un motif, recoloré ; rend (svg, classe à ajouter à la couverture)."""
    regle = COULEUR.get(motif)
    pleines = [m for m in FORMES.finditer(svg) if 'fill="currentColor"' in m.group(0)]
    mode = regle[0] if regle else ("multi" if len(pleines) >= SEUIL_MULTI else "degrade")
    if mode == "uni":
        return svg, ""
    if mode == "multi" and pleines:
        rang = [0]

        def encre(m):
            if 'fill="currentColor"' not in m.group(0):
                return m.group(0)
            rang[0] += 1
            return m.group(0).replace('fill="currentColor"', f'fill="var(--m{(rang[0] - 1) % 4 + 1})"')
        return FORMES.sub(encre, svg), " couv-multi"
    if not any('stroke="currentColor"' in m.group(0) for m in FORMES.finditer(svg)):
        return svg, ""
    _degrades[0] += 1
    ident = f"cdg{_degrades[0]}"
    stops = f'<stop offset="0" stop-color="{couleurs["g1"]}"/><stop offset="1" stop-color="{couleurs["g2"]}"/>'
    sens = regle[1] if regle and len(regle) > 1 else ("r" if motif in RAYONNANTS else "hvd"[graine % 3])
    if sens == "r":
        cx, cy = regle[2] if regle and len(regle) > 2 else (100, 100)
        defs = f'<defs><radialGradient id="{ident}" gradientUnits="userSpaceOnUse" cx="{cx}" cy="{cy}" r="120">{stops}</radialGradient></defs>'
    else:
        x1, y1, x2, y2 = SENS.get(sens, SENS["d"])
        defs = (f'<defs><linearGradient id="{ident}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
                f'{stops}</linearGradient></defs>')
    svg = FORMES.sub(lambda m: m.group(0).replace('stroke="currentColor"', f'stroke="url(#{ident})"'), svg)
    return defs + svg, " couv-degrade"


def composer(meta, d, lang, motif, teinte, place, tirage, graine, perso=None):
    """HTML de la couverture."""
    mono = "mono" in re.split(r"[\s,;]+", sans_accents((meta.get("couverture") or "").lower()))
    L, e, couleurs = TEXTES[lang], html.escape, palette(tirage, teinte, mono)
    titre, r = d["titre"], random.Random(graine + 7)
    d = {**d, "inverse": luminance(rgb(couleurs["ce"])) > luminance(rgb(couleurs["cf"]))}
    sur, sous = meta.get("surtitre", "").strip(), meta.get("soustitre", "").strip()
    annee = re.match(r"\d{4}", meta.get("date", ""))
    annee = annee.group(0) if annee else meta.get("date", "")
    gauche = " · ".join(x for x in (meta.get("auteur", ""), annee) if x)
    longueur = mots(d["mots"], lang, " ")
    pied = f'<p class="couv-pied"><span>{e(gauche)}</span><span>{longueur}</span></p>'
    # épaisseur : une page de tranche par pixel, de 2 (une note) à 14 (un long cours)
    ep = max(2, min(14, round(2 + 2.2 * math.log2(max(d["mots"], 200) / 200))))
    tranche = ",".join(f"{k}px {k}px 0 var(--tr{1 + k % 2})" for k in range(1, ep + 1)) + f",{ep + 1}px {ep + 1}px 0 var(--tr3)"
    style = ";".join(f"--{k}:{v}" for k, v in couleurs.items()) + f";--ep:{tranche}"
    if perso is not None and entiere(perso):
        # couverture entière dessinée : ses textes reprennent l'en-tête par {titre} ({TITRE} en capitales), {soustitre},
        # {surtitre}, {auteur}, {annee}, {mots}
        valeurs = {"titre": titre, "TITRE": titre.upper(), "soustitre": sous, "surtitre": sur, "auteur": meta.get("auteur", ""),
                   "annee": annee, "mots": longueur}
        svg = nettoyer_svg(perso, 'aria-hidden="true" focusable="false" preserveAspectRatio="xMidYMid slice"')
        svg = re.sub(r"\{(titre|TITRE|soustitre|surtitre|auteur|annee|mots)\}", lambda m: e(valeurs[m.group(1)]), svg)
        return (f'<div class="couverture couv-entiere couv-perso couv-{teinte}" aria-hidden="true" style="{style}">'
                f'<div class="couv">{svg}</div></div>\n')
    # à fond perdu ou en fond, une texture est coupée par les bords ; un schéma garde toute sa largeur
    tranche_vue, classe_couleur = "", ""
    if place in ("plein", "fond"):
        tranche_vue = ' preserveAspectRatio="xMidYMid slice"' if motif in TEXTURES or place == "plein" else ' preserveAspectRatio="xMidYMid meet"' 
    if perso is not None:
        dessin = nettoyer_svg(perso, 'aria-hidden="true" focusable="false"' + tranche_vue)
    else:
        rm = random.Random(graine + sum(map(ord, motif)))
        vue = "8 8 184 184" if place == "plein" or (place == "fond" and motif in TEXTURES) else "0 0 200 200"
        corps_svg = "".join(x for x in MOTIFS[motif](rm, d) if x)
        if "g1" in couleurs:
            corps_svg, classe_couleur = colorier(corps_svg, couleurs, motif, graine)
        dessin = (f'<svg viewBox="{vue}"{tranche_vue} aria-hidden="true" focusable="false"><g fill="none" stroke-linecap="round" '
                  'stroke-linejoin="round">' + corps_svg + "</g></svg>")
    # fiche de laboratoire : jusqu'à trois mesures non nulles, puis le temps de lecture, en nombre pair de cases
    fiche = [(L[cle], chiffre(v, lang)) for cle, v in (("sections", len(d["sections"])), ("figures", d["figures"]),
                                                     ("formules", d["formules"]), ("exercices", d["exercices"])) if v][:3]
    if len(fiche) % 2 == 0 and fiche:
        fiche.pop()
    fiche.append((L["lecture"], f"{max(1, round(d['mots'] / 230))} {L['min']}"))
    t, garde = disposer(place, titre, sous, bool(sur) and place != "bas", len(fiche))
    fiche = fiche[:garde]
    p_sur = f'<p class="couv-sur">{e(sur)}</p>' if sur else ""
    p_titre = f'<p class="couv-titre" style="font-size:{n(t, 2)}cqi">{e(titre)}</p>'
    p_sous = f'<p class="couv-sous">{e(sous)}</p>' if sous else ""
    filet_div = '<div class="couv-filet"></div>'
    p_fiche = ('<dl class="couv-fiche">' + "".join(f"<div><dt>{e(a)}</dt><dd>{e(b)}</dd></div>" for a, b in fiche) + "</dl>"
               if fiche else "")
    if place == "haut":
        # illustration toujours cadrée, filet sous le titre une fois sur deux
        filet = filet_div if r.random() < .5 else ""
        parties = [f'<div class="couv-tete">{p_sur}{p_titre}{p_sous}</div>', filet,
                   f'<div class="couv-image couv-cadre">{dessin}</div>', p_fiche, pied]
    elif place == "bas":
        # la ligne en italique passe au-dessus du titre (« of Transport / MODULARITY ») ; cadre deux fois sur cinq
        cadre = " couv-cadre" if r.random() < .4 else ""
        parties = [p_sur, f'<div class="couv-image{cadre}">{dessin}</div>', filet_div,
                   f'<div class="couv-tete">{p_sous}{p_titre}</div>', pied]
    elif place == "plein":
        parties = [f'<div class="couv-image">{dessin}</div>', f'<div class="couv-tete">{p_sur}{p_titre}{p_sous}</div>', pied]
    else:
        parties = [f'<div class="couv-motif">{dessin}</div>', f'<div class="couv-tete">{p_sur}{p_titre}{p_sous}</div>', pied]
    return (f'<div class="couverture couv-{place}{" couv-perso" if perso is not None else ""} couv-{teinte}{classe_couleur}" aria-hidden="true" style="{style}">'
            f'<div class="couv">{"".join(x for x in parties if x)}</div></div>\n')


def preparer(meta, corps, plan_, lang, avis, brut=None):
    """Rend None sans demande ; sinon {"corps", "html", "resume", "motif", "teinte", "tirage"}."""
    valeur = (meta.get("couverture") or "").strip()
    corps, perso = extraire_bloc(corps)
    if (not valeur and perso is None) or valeur.lower() in ("non", "no", "false"):
        return None
    if perso is not None and "<svg" not in perso:
        avis.append('couverture : le bloc « ::: couverture » doit contenir un <svg viewBox="0 0 200 200"> (illustration) '
                    'ou <svg viewBox="0 0 200 300"> (couverture entière)')
        perso = None
    lang = "en" if lang == "en" else "fr"
    g = reglages(meta, perso is not None, avis)
    titre = (meta.get("court") or meta.get("titre") or "Sans titre").strip()
    d = mesurer(corps, plan_, titre, brut)
    nom = "entière" if perso is not None and entiere(perso) else g["motif"]
    return {"corps": corps, "html": composer(meta, d, lang, g["motif"], g["teinte"], g["place"], g["tirage"], g["graine"], perso),
            "resume": f"{nom}, {g['teinte']}, titre en {g['place']}, {mots(d['mots'], lang)}",
            "motif": g["motif"], "teinte": g["teinte"], "tirage": g["tirage"]}


def choisis(choix):
    """« tout », ou des domaines (ou leur début) et des noms de motifs séparés par des virgules → [(domaine, [motifs])] :
    chaque domaine nommé, puis les motifs nommés un à un, rangés sous leur domaine."""
    choix = sans_accents((choix or "tout").strip().lower())
    if choix in ("", "tout", "tous", "oui", "all"):
        return [(dom, list(ms)) for dom, ms in CATALOGUE.items()]
    groupes, noms = [], []
    for mot in (m.strip() for m in re.split(r"[,;]+", choix) if m.strip()):
        dom = next((d for d in CATALOGUE if sans_accents(d.lower()).startswith(mot) or mot in sans_accents(d.lower()).split()), None)
        if dom and mot not in MOTIFS:
            groupes.append((dom, list(CATALOGUE[dom])))
        else:
            noms += [ALIAS.get(m, m) for m in mot.split()]
    noms = [m for m in noms if m in MOTIFS]
    # les motifs nommés un à un, rangés sous leur domaine, dans l'ordre du catalogue
    groupes += [(dom, [m for m in ms if m in noms]) for dom, ms in CATALOGUE.items() if any(m in noms for m in ms)]
    return groupes


def planche(meta, corps, plan_, lang, avis, brut=None, choix=None):
    """La couverture du document dans chaque motif (teintes et places en alternance), rangée par domaine, chacune sous
    la ligne d'en-tête qui la donne : pour choisir. Rend le corps HTML d'une page."""
    lang = "en" if lang == "en" else "fr"
    corps, perso = extraire_bloc(corps)
    g = reglages(meta)
    _, teinte, place, variante = lire_valeur(meta.get("couverture", ""), [])
    titre = (meta.get("court") or meta.get("titre") or "Sans titre").strip()
    d, sortie, k = mesurer(corps, plan_, titre, brut), [], 0
    proposes = [m for m, s in classement(meta).most_common(6) if s]
    e = html.escape
    if proposes:
        sortie.append("<p>D'après l'en-tête : " + ", ".join(f"<code>{m}</code>" for m in proposes) + ".</p>")
    groupes = choisis(choix)
    if perso is not None and "<svg" in perso:
        groupes = [("Votre dessin", ["personnel"] * (1 if entiere(perso) else 4))] + groupes
    for dom, motifs_ in groupes:
        cases = []
        for i, motif in enumerate(motifs_):
            te = teinte or ("claire", "encre", "sombre")[(k + k // 4) % 3]
            pl = place or ("haut", "bas", "plein", "fond")[k % 4]
            if motif == "personnel":
                pl = place or ("haut", "bas", "plein", "fond")[i]
            k += 1
            ligne = f"couverture: {'' if motif == 'personnel' else motif + ' '}{te} {pl}" + (f" {variante}" if variante else "")
            dessin = DOMAINE and next((v[0] for dm in CATALOGUE.values() for m_, v in dm.items() if m_ == motif), "")
            legende = f"<b>{e(motif)}</b>" + (f" — {e(dessin)}" if dessin else "")
            cases.append(f'<div class="couv-case">{composer(meta, d, lang, motif, te, pl, g["tirage"], g["graine"], perso if motif == "personnel" else None)}'
                         f'<p>{legende}</p><p><code>{ligne}</code></p></div>')
        if cases:
            sortie.append(f'<h2 id="{e(re.sub(r"[^a-z]+", "-", sans_accents(dom.lower())).strip("-"))}">{e(dom)}</h2>'
                          f'<div class="large"><div class="etagere">{"".join(cases)}</div></div>')
    return "\n".join(sortie)


def catalogue_md(court=False):
    """Le catalogue des motifs en Markdown, par domaine : nom, dessin, mots du sujet (les six premiers si court)."""
    lignes = []
    for dom, ms in CATALOGUE.items():
        lignes += [f"**{dom}**", "", "| Motif | Dessin | Mots du sujet |", "|---|---|---|"]
        for m, (dessin, mots_) in ms.items():
            liste = [x.strip() for x in mots_.split(",") if x.strip()]
            liste = liste[:6] if court else liste
            lignes.append(f"| `{m}` | {dessin} | {', '.join(liste).replace('*', '…')} |")
        lignes.append("")
    return "\n".join(lignes)


def proposer(sujet, k=6):
    """Les motifs qui conviennent à un sujet, du meilleur au moins bon."""
    total = Counter({m: s for m, s in scores(sujet).items() if s})
    return [(m, s) for m, s in total.most_common(k)]


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--catalogue":
        print(catalogue_md(court="--court" in sys.argv))
    elif len(sys.argv) > 1:
        trouves = proposer(" ".join(sys.argv[1:]))
        if not trouves:
            print("aucun mot du sujet ne désigne un motif : choisir dans le catalogue (--catalogue), ou couverture: oui")
        for m, s in trouves:
            print(f"{m:13} {n(s)}  ({DOMAINE[m]} : {next(v[0] for dm in CATALOGUE.values() for m_, v in dm.items() if m_ == m)})")
    else:
        print(__doc__)
