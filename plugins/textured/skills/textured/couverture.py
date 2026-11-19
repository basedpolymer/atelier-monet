"""TeXtured — couverture de document, sur demande (« couverture: » dans l'en-tête, ou --couverture).

Un portrait 2:3 : aplat tiré de l'encre de la page (« tirage: »), titre en Latin Modern Sans gras capitales, ligne en
italique, illustration générative liée au document, fiche de laboratoire remplie par le document, pied
« AUTEUR · ANNÉE  /  N MOTS ». Le même objet sert partout, ses tailles étant en cqi : vignette à côté du titre (avec une
épaisseur de pages proportionnelle à la longueur), première page du PDF à fond perdu, image de partage (--apercu).

Un motif est une fonction (r, d) → éléments SVG dans le carré 0 0 200 200 : r est un random.Random dont la graine vient
du titre (même document, même couverture ; un nombre dans « couverture: » en tire une autre), d les mesures du
document. Couleurs : currentColor (encre), var(--ca) (accent), var(--cd) (trait doux), var(--cf) (fond).
"""
import hashlib
import html
import math
import random
import re
import unicodedata
from collections import Counter, defaultdict

ENCRE, ACC, DOUX, FOND = "currentColor", "var(--ca)", "var(--cd)", "var(--cf)"
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


# ---------- outils ----------

def n(x, k=1):
    s = f"{x:.{k}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def sans_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def points(pts, diam, couleur):
    """Points ronds : sous-chemins de longueur nulle à bouts ronds, un seul <path> par diamètre."""
    if not pts:
        return ""
    return (f'<path d="{"".join(f"M{n(x)} {n(y)}h0" for x, y in pts)}" stroke="{couleur}" '
            f'stroke-width="{n(diam)}" stroke-linecap="round"/>')


def trace(pts):
    return "M" + "L".join(f"{n(x)} {n(y)}" for x, y in pts)


def lisse(p):
    """Courbe fermée passant par les points (Catmull-Rom → Bézier)."""
    m, d = len(p), f"M{n(p[0][0])} {n(p[0][1])}"
    for i in range(m):
        p0, p1, p2, p3 = p[i - 1], p[i], p[(i + 1) % m], p[(i + 2) % m]
        d += (f"C{n(p1[0] + (p2[0] - p0[0]) / 6)} {n(p1[1] + (p2[1] - p0[1]) / 6)} "
              f"{n(p2[0] - (p3[0] - p1[0]) / 6)} {n(p2[1] - (p3[1] - p1[1]) / 6)} {n(p2[0])} {n(p2[1])}")
    return d + "Z"


def carres(cases, cote):
    return "".join(f"M{n(x)} {n(y)}h{n(cote)}v{n(cote)}h-{n(cote)}z" for x, y in cases)


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


def palette(encre, teinte):
    """Fond, texte, accent et trait doux de la couverture, tirés de l'encre. claire : pastel de l'encre, texte noir,
    accent à l'encre ; encre : aplat de l'encre, texte noir ou crème, accent en réserve (le papier) ; sombre : nuit
    teintée de l'encre, texte crème, accent à l'encre éclaircie."""
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
    elif teinte == "sombre":
        fond, texte, accent = teinte_de(e, .25, min(c * .3, .035)), CREME, e
        while contraste(accent, fond) < 3.4:
            accent = melange(accent, CREME, .12)
    else:
        fond, texte, accent = teinte_de(e, .915, min(c * .45, .065)), melange(NOIR, e, .08), e
        while contraste(accent, fond) < 2.4:
            accent = melange(accent, NOIR, .12)
    return {"cf": hexa(fond), "ce": hexa(texte), "ca": hexa(accent), "cd": hexa(melange(fond, texte, .42))}


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


# ---------- motifs ----------

def semis(r, d):
    """Semis de points traversé d'une onde pointillée : signal, mesure, bruit."""
    a, lam, phi, y0 = r.uniform(24, 42), r.uniform(85, 150), r.uniform(0, 2 * math.pi), r.uniform(84, 116)
    onde = lambda x: y0 + a * math.sin(2 * math.pi * x / lam + phi)
    tailles = {1.6: [], 2.5: [], 3.4: []}
    for i in range(1, 20):
        for j in range(1, 20):
            x, y = i * 10 + r.uniform(-1.8, 1.8), j * 10 + r.uniform(-1.8, 1.8)
            if abs(y - onde(x)) > 10:
                tailles[r.choice((1.6, 1.6, 2.5, 3.4))].append((x, y))
    seconde = [(x, onde(x) + 13 * math.sin(x / 8)) for x in range(4, 197, 3)]
    return [points(p, t, ENCRE) for t, p in tailles.items()] + [
        f'<path d="{trace(seconde)}" stroke="{DOUX}" stroke-width="0.9" stroke-dasharray="2 3"/>',
        f'<path d="{trace([(x, onde(x)) for x in range(4, 197, 2)])}" stroke="{ACC}" stroke-width="4.2" '
        f'stroke-dasharray="0 6.6" stroke-linecap="round"/>']


def arcs(r, d):
    """Cercles qui se referment case après case : progression, apprentissage."""
    c = r.choice((3, 4, 5))
    pas, total, depart, expo = 184 / c, c * c, math.radians(r.choice((-90, 0, 90, 180))), r.choice((1, 1.4, .75))
    rayon, out = pas * .34, []
    for k in range(total):
        x, y, f = 8 + pas * (k % c + .5), 8 + pas * (k // c + .5), (k / (total - 1)) ** expo
        out.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(rayon)}" stroke="{DOUX}" stroke-width="0.6" stroke-dasharray="0 3.2"/>')
        x0, y0 = x + rayon * math.cos(depart), y + rayon * math.sin(depart)
        if f >= .999:
            out.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(rayon)}" stroke="{ACC}" stroke-width="3.2"/>')
        elif f > .004:
            a1 = depart + 2 * math.pi * f
            out.append(f'<path d="M{n(x0)} {n(y0)}A{n(rayon)} {n(rayon)} 0 {int(f > .5)} 1 '
                       f'{n(x + rayon * math.cos(a1))} {n(y + rayon * math.sin(a1))}" stroke="{ENCRE}" stroke-width="2.3"/>')
        else:
            out.append(points([(x0, y0)], 3.6, ENCRE))
    return out


def anneaux(r, d):
    """Anneaux concentriques, pleins, pointillés ou ouverts : ondes, diffusion, cycles."""
    cx, cy = 100 + r.uniform(-12, 12), 100 + r.uniform(-12, 12)
    limite, rayon, rangs = min(cx, cy, 200 - cx, 200 - cy) - 3, r.uniform(3, 6), []
    while rayon < limite:
        rangs.append(rayon)
        rayon += r.uniform(4.5, 9.5)
    ka, out = r.randrange(len(rangs) // 3, len(rangs)), []
    for k, rayon in enumerate(rangs):
        w, sorte, extra = r.choice((.6, .9, 1.3, 2.2, 3.4)), r.random(), ""
        if k == ka:
            w = max(w, 2.8)
        elif sorte < .2:
            w, extra = max(w, 1.8), f' stroke-dasharray="0 {n(r.uniform(3.5, 6))}" stroke-linecap="round"'
        elif sorte < .4:
            tour = 2 * math.pi * rayon
            ouvert = tour * r.uniform(.12, .38)
            extra = f' stroke-dasharray="{n(tour - ouvert)} {n(ouvert)}" transform="rotate({r.randrange(360)} {n(cx)} {n(cy)})"'
        out.append(f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(rayon)}" stroke="{ACC if k == ka else ENCRE}" stroke-width="{n(w)}"{extra}/>')
    return out + [points([(cx, cy)], 4.2, ENCRE)]


def reseau(r, d):
    """Réseau radial qui s'évase en lignes, un chemin et un nœud à l'accent : graphes, relations."""
    niveaux = [[(100.0, 100.0, 0, 0.0)]]
    for rayon, nombre in ((26, r.randint(5, 7)), (52, r.randint(10, 14)), (78, r.randint(18, 26))):
        dec, couche = r.uniform(0, 2 * math.pi), []
        for k in range(nombre):
            a = dec + 2 * math.pi * (k + r.uniform(-.2, .2)) / nombre
            rr, prec = rayon + r.uniform(-4, 4), niveaux[-1]
            p = 0 if len(prec) == 1 else min(range(len(prec)), key=lambda i: abs(math.remainder(prec[i][3] - a, 2 * math.pi)))
            couche.append((100 + rr * math.cos(a), 100 + rr * math.sin(a), p, a))
        niveaux.append(couche)
    i, chemin = r.randrange(len(niveaux[-1])), set()
    for lv in range(len(niveaux) - 1, 0, -1):
        chemin.add((lv, i))
        i = niveaux[lv][i][2]
    traits, accent, doux = [], [], []
    for lv in range(1, len(niveaux)):
        couche = niveaux[lv]
        for i, (x, y, p, a) in enumerate(couche):
            px, py = niveaux[lv - 1][p][:2]
            (accent if (lv, i) in chemin else traits).append(f"M{n(px)} {n(py)}L{n(x)} {n(y)}")
            if lv < 3 and r.random() < .35:
                x2, y2 = couche[(i + 1) % len(couche)][:2]
                doux.append(f"M{n(x)} {n(y)}L{n(x2)} {n(y2)}")
            if lv == 3:
                for e in range(r.randint(1, 3)):
                    b = a + r.uniform(-.09, .09)
                    doux.append(f"M{n(x)} {n(y)}L{n(100 + 97 * math.cos(b))} {n(100 + 97 * math.sin(b))}")
    out = [f'<path d="{"".join(doux)}" stroke="{DOUX}" stroke-width="0.8"/>',
           f'<path d="{"".join(traits)}" stroke="{ENCRE}" stroke-width="1.1"/>',
           f'<path d="{"".join(accent)}" stroke="{ACC}" stroke-width="2.6"/>']
    for lv, couche in enumerate(niveaux):
        for i, (x, y, _, _) in enumerate(couche):
            marque = lv == 0 or (lv, i) in chemin
            rayon = 5.2 if (lv == 3 and marque) else (4.4, 3.2, 2.6, 2.1)[lv]
            out.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(rayon)}" fill="{ACC if marque else FOND}" '
                       f'stroke="{ACC if marque else ENCRE}" stroke-width="1.1"/>')
    return out


def automate(r, d):
    """Automate cellulaire élémentaire né d'une seule case, une génération à l'accent : calcul, règles, émergence."""
    regle, cote = r.choice((90, 30, 150, 22, 126, 18, 182)), 33
    pas, lignes = 184 / cote, [[int(i == cote // 2) for i in range(cote)]]
    for _ in range(cote - 1):
        p = [0] + lignes[-1] + [0]
        lignes.append([(regle >> (4 * p[i] + 2 * p[i + 1] + p[i + 2])) & 1 for i in range(cote)])
    ka, cases = r.randrange(cote // 3, cote - 2), {ENCRE: [], ACC: []}
    for j, ligne in enumerate(lignes):
        for i, v in enumerate(ligne):
            if v:
                cases[ACC if j in (0, ka) else ENCRE].append((8 + i * pas, 8 + j * pas))
    return [f'<path d="{carres(c, pas * .84)}" fill="{k}"/>' for k, c in cases.items() if c]


def trame(r, d):
    """Sphère en trame de points et son orbite : volume, lumière, astronomie."""
    cx, cy, rayon = 96 + r.uniform(-5, 5), 96 + r.uniform(-5, 5), r.uniform(62, 70)
    lx, ly = r.uniform(-.7, -.3), r.uniform(-.75, -.45)
    norme = math.sqrt(lx * lx + ly * ly + .36)
    lx, ly, lz = lx / norme, ly / norme, .6 / norme
    classes, pas, y, rang = defaultdict(list), 5.4, cy - rayon, 0
    while y <= cy + rayon:
        x = cx - rayon + (pas / 2 if rang % 2 else 0)
        while x <= cx + rayon:
            dx, dy = (x - cx) / rayon, (y - cy) / rayon
            if dx * dx + dy * dy < .985:
                b = max(0.0, dx * lx + dy * ly + math.sqrt(1 - dx * dx - dy * dy) * lz)
                classes[round((.5 + 4.3 * ((b if d["inverse"] else 1 - b) ** 1.3)) * 2) / 2].append((x, y))
            x += pas
        y, rang = y + pas * .866, rang + 1
    ang, rx, ry = r.uniform(-26, -10), min(rayon * 1.42, 94), rayon * .3
    orbite = lambda bas: (f'<path d="M{n(cx - rx)} {n(cy)}A{n(rx)} {n(ry)} 0 0 {int(not bas)} {n(cx + rx)} {n(cy)}" '
                          f'transform="rotate({n(ang)} {n(cx)} {n(cy)})" ')
    t = r.uniform(.15, .85) * math.pi
    lune = (cx + rx * math.cos(t), cy + ry * math.sin(t))
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    lune = (cx + (lune[0] - cx) * ca - (lune[1] - cy) * sa, cy + (lune[0] - cx) * sa + (lune[1] - cy) * ca)
    return ([orbite(False) + f'stroke="{ACC}" stroke-width="1" stroke-dasharray="2 2.6"/>']
            + [points(p, t, ENCRE) for t, p in sorted(classes.items())]
            + [orbite(True) + f'stroke="{ACC}" stroke-width="2.2"/>', points([lune], 9, ACC)])


def rayures(r, d):
    """Sphère de rayures, plus épaisses dans l'ombre, et son ombre portée : forme, matière."""
    cx, cy, rayon, pas = 100, 92 + r.uniform(-4, 4), r.uniform(60, 68), r.choice((4.4, 5.2, 6))
    bande, out, y = r.uniform(.3, .7), [], cy - rayon + pas / 2
    while y < cy + rayon:
        demi, t = math.sqrt(rayon * rayon - (y - cy) ** 2), (y - cy + rayon) / (2 * rayon)
        t = 1 - t if d["inverse"] else t
        out.append(f'<path d="M{n(cx - demi)} {n(y)}H{n(cx + demi)}" stroke="{ACC if abs(t - bande) < .05 else ENCRE}" '
                   f'stroke-width="{n(.35 + pas * .7 * t ** 1.5, 2)}"/>')
        y += pas
    sol, ombre = cy + rayon + 13, []
    for k in range(-2, 3):
        demi = rayon * .82 * math.sqrt(1 - (k / 3) ** 2)
        ombre.append(f"M{n(cx - demi + 8)} {n(sol + k * 2.6)}h{n(2 * demi)}")
    return ([f'<g transform="rotate({n(r.uniform(-24, 24))} {cx} {n(cy)})">'] + out + ["</g>"]
            + [f'<path d="{"".join(ombre)}" stroke="{DOUX}" stroke-width="1.1"/>'])


def helice(r, d):
    """Double hélice de points reliés par des barreaux : biologie, chimie, ADN."""
    tours, ampl, longueur = r.uniform(2.2, 3.3), r.uniform(24, 31), 172
    total, brins, barreaux = int(tours * 22), ([], []), []
    for k in range(total + 1):
        t = k / total
        for b in (0, 1):
            a = 2 * math.pi * tours * t + b * math.pi
            brins[b].append((100 + ampl * math.sin(a), 14 + longueur * t, math.cos(a)))
        if k % 2 == 0:
            barreaux.append(f"M{n(brins[0][-1][0])} {n(brins[0][-1][1])}L{n(brins[1][-1][0])} {n(brins[1][-1][1])}")
    out = [f'<g transform="rotate({n(r.uniform(-36, 36))} 100 100)">',
           f'<path d="{"".join(barreaux)}" stroke="{DOUX}" stroke-width="0.9"/>']
    for devant in (False, True):
        for b, couleur in ((0, ENCRE), (1, ACC)):
            classes = defaultdict(list)
            for x, y, z in brins[b]:
                if (z >= 0) == devant:
                    classes[round((2.2 + 3.6 * (z + 1) / 2) * 2) / 2].append((x, y))
            out += [points(p, t, couleur) for t, p in classes.items()]
    return out + ["</g>"]


def pavage(r, d):
    """Pavage de Truchet : quarts de cercle qui se raccordent en méandres : géométrie, combinatoire."""
    c = r.choice((7, 8, 9, 10))
    s = 184 / c
    h, encre, accent, quarts = s / 2, [], [], []
    for i in range(c):
        for j in range(c):
            x, y = 8 + i * s, 8 + j * s
            if r.random() < .5:
                arcs_ = (f"M{n(x + h)} {n(y)}A{n(h)} {n(h)} 0 0 1 {n(x)} {n(y + h)}"
                         f"M{n(x + s)} {n(y + h)}A{n(h)} {n(h)} 0 0 0 {n(x + h)} {n(y + s)}")
                coin = f"M{n(x)} {n(y)}H{n(x + h)}A{n(h)} {n(h)} 0 0 1 {n(x)} {n(y + h)}Z"
            else:
                arcs_ = (f"M{n(x + h)} {n(y)}A{n(h)} {n(h)} 0 0 0 {n(x + s)} {n(y + h)}"
                         f"M{n(x)} {n(y + h)}A{n(h)} {n(h)} 0 0 1 {n(x + h)} {n(y + s)}")
                coin = f"M{n(x + s)} {n(y)}V{n(y + h)}A{n(h)} {n(h)} 0 0 1 {n(x + h)} {n(y)}Z"
            (accent if r.random() < .07 else encre).append(arcs_)
            if r.random() < .14:
                quarts.append(coin)
    return [f'<path d="{"".join(quarts)}" fill="{DOUX}"/>', f'<path d="{"".join(encre)}" stroke="{ENCRE}" stroke-width="1.7"/>',
            f'<path d="{"".join(accent)}" stroke="{ACC}" stroke-width="3"/>']


def flocon(r, d):
    """Flocon à six branches et son reflet tourné : symétrie, cristaux, froid."""
    rayon, bras = r.uniform(78, 88), []
    bras.append(f"M0 0H{n(rayon)}")
    for _ in range(r.randint(3, 5)):
        t = r.uniform(.22, .86)
        l, x = (1.05 - t) * rayon * r.uniform(.3, .62), t * rayon
        dx, dy = l * .5, l * .866
        bras.append(f"M{n(x)} 0l{n(dx)} {n(dy)}M{n(x)} 0l{n(dx)} {n(-dy)}")
        if l > 22 and r.random() < .6:
            bras.append(f"M{n(x + dx * .5)} {n(dy * .5)}h{n(l * .35)}M{n(x + dx * .5)} {n(-dy * .5)}h{n(l * .35)}")
    trait, forme = "".join(bras), "".join(bras[:1] + bras[1::2])
    w, cote = r.choice((1.8, 2.4, 3)), r.uniform(8, 13)
    hexagone = " ".join(f"{n(cote * math.cos(math.pi * k / 3))},{n(cote * math.sin(math.pi * k / 3))}" for k in range(6))
    return (['<g transform="translate(100 100)">', '<g transform="rotate(30) scale(.58)">']
            + [f'<path d="{forme}" transform="rotate({60 * k})" stroke="{DOUX}" stroke-width="2"/>' for k in range(6)]
            + ["</g>"] + [f'<path d="{trait}" transform="rotate({60 * k})" stroke="{ENCRE}" stroke-width="{w}"/>' for k in range(6)]
            + [f'<polygon points="{hexagone}" fill="{ACC}"/>',
               points([(rayon * math.cos(math.pi * k / 3), rayon * math.sin(math.pi * k / 3)) for k in range(6)], 6, ACC), "</g>"])


def trajectoires(r, d):
    """Trajectoires de particules dans un champ, trois à l'accent : mouvement, dynamique, flux."""
    p, f, tourb = [r.uniform(0, 6.3) for _ in range(4)], [r.uniform(.012, .03) for _ in range(3)], r.uniform(.8, 1.6)
    champ = lambda x, y: (tourb * (math.sin(x * f[0] + p[0]) + math.cos(y * f[1] + p[1]))
                          + .7 * math.sin((x - y) * f[2] + p[2]) + p[3])
    accents, out, tetes = set(r.sample(range(44), 3)), [], {ENCRE: [], ACC: []}
    for k in range(44):
        x, y = r.uniform(12, 188), r.uniform(12, 188)
        pts = [(x, y)]
        for _ in range(r.randint(14, 30)):
            a = champ(x, y)
            x, y = x + 4.4 * math.cos(a), y + 4.4 * math.sin(a)
            if not (6 < x < 194 and 6 < y < 194):
                break
            pts.append((x, y))
        if len(pts) < 5:
            continue
        couleur = ACC if k in accents else ENCRE
        out.append(f'<path d="{trace(pts)}" stroke="{couleur}" stroke-width="{1.5 if couleur == ENCRE else 2.3}" '
                   f'stroke-dasharray="0 4.4" stroke-linecap="round"/>')
        tetes[couleur].append(pts[-1])
    return out + [points(tetes[ENCRE], 3.6, ENCRE), points(tetes[ACC], 5.2, ACC)]


def colonnes(r, d):
    """Le document en colonnes de texte, une par section (à défaut, par paragraphe), hauteur selon le nombre de mots ;
    la plus longue surlignée : rapport, comparaison, structure."""
    noms = None
    if len(d["sections"]) >= 3:
        valeurs, noms = [s["mots"] for s in d["sections"]], [s["num"] for s in d["sections"]]
    elif len(d["paragraphes"]) >= 4:
        valeurs = d["paragraphes"]
    else:
        valeurs = [r.randint(20, 100) for _ in range(r.randint(6, 12))]
    if len(valeurs) > 24:
        paquet = math.ceil(len(valeurs) / 24)
        valeurs, noms = [sum(valeurs[i:i + paquet]) for i in range(0, len(valeurs), paquet)], None
    m, interligne = len(valeurs), 3.6
    fente, haut, base = 184 / m, (146 if noms else 166), (174 if noms else 188)
    largeur, vmax = fente * .62, max(valeurs) or 1
    ia, out, encre, accent = valeurs.index(vmax), [], [], []
    for i, v in enumerate(valeurs):
        x, k = 8 + fente * i + (fente - largeur) / 2, max(1, round(haut * v / vmax / interligne))
        if i == ia:
            out.append(f'<rect x="{n(x - 2.4)}" y="{n(base - k * interligne - 2.4)}" width="{n(largeur + 4.8)}" '
                       f'height="{n(k * interligne + 2.4)}" fill="{ACC}"/>')
        encre.append("".join(f"M{n(x)} {n(base - interligne * (j + .5))}h{n(largeur * (r.uniform(.45, .9) if j == k - 1 else 1))}"
                             for j in range(k)))
    out.append(f'<path d="{"".join(encre)}" stroke="{ENCRE}" stroke-width="{n(min(1.7, interligne * .48))}"/>')
    out.append(f'<path d="M8 {n(base + 1.6)}H192" stroke="{ENCRE}" stroke-width="1.2"/>')
    if noms and m <= 14:
        out.append('<g fill="currentColor" font-size="8" text-anchor="middle">' + "".join(
            f'<text x="{n(8 + fente * (i + .5))}" y="{n(base + 12)}">{html.escape(t)}</text>' for i, t in enumerate(noms)) + "</g>")
    return out


def plan(r, d):
    """Organigramme du plan : sections, sous-sections ; cases surlignées pour les sections à exercices (sinon la plus
    longue) ; sans sous-sections, les cases pendent d'autant plus que la section est longue : cours, structure."""
    secs = d["sections"]
    if len(secs) < 2:
        secs = [{"num": str(i + 1), "subs": [f"{i + 1}.{j + 1}" for j in range(r.randint(0, 3))], "exo": r.random() < .3,
                 "mots": r.random()} for i in range(r.randint(3, 5))]
    secs = secs[:8]
    k = len(secs)
    ecart = 5 if k > 5 else 8
    w, h = min(36, (184 - ecart * (k - 1)) / k), 15
    total = k * w + (k - 1) * ecart
    x0, profondeur = 100 - total / 2, max(min(len(s["subs"]), 6) for s in secs)
    vmax = max(s["mots"] for s in secs) or 1
    hauteur = (lambda s: h) if profondeur else (lambda s: h + 70 * s["mots"] / vmax)
    haut = 18 + 12 + 10 + (profondeur and h + 7 + profondeur * 17 or max(hauteur(s) for s in secs))
    y0 = (200 - haut) / 2
    yb, yc = y0 + 18 + 12, y0 + 18 + 12 + 10
    surligne = {i for i, s in enumerate(secs) if s.get("exo")} or {max(range(k), key=lambda i: secs[i]["mots"])}
    traits = [f"M100 {n(y0 + 18)}V{n(yb)}M{n(x0 + w / 2)} {n(yb)}H{n(x0 + total - w / 2)}"]
    boites, textes = [], []
    boites.append(f'<rect x="70" y="{n(y0)}" width="60" height="18" rx="1.5" fill="{FOND}" stroke="{ENCRE}" stroke-width="1.3"/>')
    boites.append(f'<path d="M100 {n(y0 + 4.5)}l4.5 4.5-4.5 4.5-4.5-4.5z" fill="{ACC}"/>')
    for i, s in enumerate(secs):
        x = x0 + i * (w + ecart)
        traits.append(f"M{n(x + w / 2)} {n(yb)}V{n(yc)}")
        boites.append(f'<rect x="{n(x)}" y="{n(yc)}" width="{n(w)}" height="{n(hauteur(s))}" rx="1" '
                      f'fill="{ACC if i in surligne else FOND}" stroke="{ENCRE}" stroke-width="1.2"/>')
        if w >= 12:
            textes.append(f'<text x="{n(x + w / 2)}" y="{n(yc + 10.2)}">{html.escape(s["num"] or str(i + 1))}</text>')
        subs = s["subs"][:6]
        if subs:
            rail, sw = x + 3.5, w - 7
            traits.append(f"M{n(rail)} {n(yc + h)}V{n(yc + h + 7 + (len(subs) - 1) * 17 + 5.5)}")
            for j, num in enumerate(subs):
                sy = yc + h + 7 + j * 17
                traits.append(f"M{n(rail)} {n(sy + 5.5)}H{n(x + 7)}")
                boites.append(f'<rect x="{n(x + 7)}" y="{n(sy)}" width="{n(sw)}" height="11" rx="1" fill="{FOND}" '
                              f'stroke="{ENCRE}" stroke-width="0.9"/>')
                if sw >= 14:
                    textes.append(f'<text x="{n(x + 7 + sw / 2)}" y="{n(sy + 7.8)}" font-size="5.6" font-weight="400">{html.escape(num)}</text>')
    return ([f'<path d="{"".join(traits)}" stroke="{ENCRE}" stroke-width="1.1"/>'] + boites
            + ['<g fill="currentColor" font-size="7.5" text-anchor="middle">' + "".join(textes) + "</g>"])


def lettres(r, d):
    """Grille de lettres où se croisent un mot du titre et un mot fréquent du document : langue, vocabulaire."""
    taille, cote, o = 10, 18, 10
    base = lambda s: "".join(c for c in sans_accents(s.upper()) if "A" <= c <= "Z")
    candidats = sorted({base(m) for m in re.split(r"[\s'’-]+", d["titre"])}, key=len, reverse=True)
    m1 = next((m for m in candidats if 3 <= len(m) <= taille), (candidats[0][:taille] if candidats and candidats[0] else "TEXTURED"))
    grille = [[None] * taille for _ in range(taille)]
    l1, c1 = r.randrange(taille), r.randrange(taille - len(m1) + 1)
    for i, ch in enumerate(m1):
        grille[l1][c1 + i] = ch
    vertical = None
    for m2 in (base(m) for m in d["frequents"]):
        if not (4 <= len(m2) <= taille) or m2 == m1:
            continue
        essais = [(i, j) for i, a in enumerate(m1) for j, b in enumerate(m2) if a == b and 0 <= l1 - j and l1 - j + len(m2) <= taille]
        if essais:
            i, j = r.choice(essais)
            vertical = (l1 - j, c1 + i, m2)
            for k, ch in enumerate(m2):
                grille[l1 - j + k][c1 + i] = ch
            break
    poids = d["lettres"] or Counter("ETAOINSRHLDCUMFPGWYBVKXJQZ")
    tirage = list(poids.keys()), list(poids.values())
    out = [f'<rect x="{n(o + c1 * cote + 1.5)}" y="{n(o + l1 * cote + 1.5)}" width="{n(len(m1) * cote - 3)}" '
           f'height="{n(cote - 3)}" rx="{n((cote - 3) / 2)}" fill="{ACC}"/>']
    if vertical:
        lv, cv, m2 = vertical
        out.append(f'<rect x="{n(o + cv * cote + 1.5)}" y="{n(o + lv * cote + 1.5)}" width="{n(cote - 3)}" '
                   f'height="{n(len(m2) * cote - 3)}" rx="{n((cote - 3) / 2)}" stroke="{ENCRE}" stroke-width="1.4"/>')
    lettres_, mots_ = [], []
    for li in range(taille):
        for ci in range(taille):
            ch = grille[li][ci]
            t = f'<text x="{n(o + (ci + .5) * cote)}" y="{n(o + (li + .5) * cote + 3.9)}">{ch or r.choices(*tirage)[0]}</text>'
            if ch:
                mots_.append((t, li == l1 and c1 <= ci < c1 + len(m1)))
            else:
                lettres_.append(t)
    return out + ['<g fill="currentColor" font-size="11" text-anchor="middle" font-weight="400">' + "".join(lettres_) + "</g>",
                  f'<g fill="{FOND}" font-size="11" text-anchor="middle">' + "".join(t for t, h in mots_ if h) + "</g>",
                  '<g fill="currentColor" font-size="11" text-anchor="middle">' + "".join(t for t, h in mots_ if not h) + "</g>"]


def taches(r, d):
    """Grille de taches organiques, certaines à noyau, une ou deux à l'accent : cellules, vivant, écologie."""
    c = r.choice((4, 5, 5, 6))
    s, out = 184 / c, []
    accents = set(r.sample(range(c * c), r.choice((1, 2))))
    for k in range(c * c):
        cx, cy = 8 + s * (k % c + .5) + r.uniform(-.08, .08) * s, 8 + s * (k // c + .5) + r.uniform(-.08, .08) * s
        rayon, m, dec = s * .36 * r.uniform(.72, 1.08), r.randint(6, 9), r.uniform(0, 2 * math.pi)
        pts = [(cx + rayon * (1 + .3 * r.uniform(-1, 1)) * math.cos(dec + 2 * math.pi * i / m),
                cy + rayon * (1 + .3 * r.uniform(-1, 1)) * math.sin(dec + 2 * math.pi * i / m)) for i in range(m)]
        if k in accents:
            out.append(f'<path d="{lisse(pts)}" fill="{ACC}"/>')
        elif r.random() < .24:
            out.append(f'<path d="{lisse(pts)}" stroke="{ENCRE}" stroke-width="1.4"/>')
        else:
            out.append(f'<path d="{lisse(pts)}" fill="{ENCRE}"/>')
            if r.random() < .3:
                out.append(points([(cx + r.uniform(-.2, .2) * rayon, cy + r.uniform(-.2, .2) * rayon)], rayon * .45, FOND))
    return out


def pixels(r, d):
    """Planche de petits glyphes de pixels symétriques, numérotés, un à l'accent : numérique, écran, jeu."""
    c = r.choice((3, 4))
    fente, out = 184 / c, {ENCRE: [], ACC: []}
    px = fente / 7.4
    accent, numeros = r.randrange(c * c), []
    for k in range(c * c):
        ox, oy = 8 + fente * (k % c) + (fente - 5 * px) / 2, 8 + fente * (k // c) + (fente - 5 * px) / 2 - px * .4
        bits = [[r.random() < .5 for _ in range(3)] for _ in range(5)]
        bits[2][2] = bits[2][2] or not any(map(any, bits))
        out[ACC if k == accent else ENCRE] += [(ox + j * px, oy + i * px) for i in range(5) for j in range(5) if bits[i][min(j, 4 - j)]]
        numeros.append(f'<text x="{n(ox + 2.5 * px)}" y="{n(oy + 5 * px + px * 1.15)}">{k + 1:02d}</text>')
    return ([f'<path d="{carres(v, px * .9)}" fill="{k}"/>' for k, v in out.items() if v]
            + [f'<g fill="{DOUX}" font-size="{n(px * .72)}" text-anchor="middle">' + "".join(numeros) + "</g>"])


MOTIFS = {f.__name__: f for f in (semis, arcs, anneaux, reseau, automate, trame, rayures, helice, pavage, flocon,
                                   trajectoires, colonnes, plan, lettres, taches, pixels)}
ALIAS = {"helix": "helice", "points": "semis", "onde": "semis", "spheres": "trame", "sphere": "trame", "graphe": "reseau",
         "truchet": "pavage", "organigramme": "plan", "mots": "lettres", "cellules": "taches", "grille": "pixels"}
# motif tiré du sujet quand « couverture: » ne le nomme pas (titre, rubrique, sous-titre, description)
INDICES = {
    "helice": r"\badn\b|\bdna\b|g[eè]ne|g[ée]n[ée]ti|prot[ée]in|biolog|mol[ée]cul|chimi|enzym",
    "reseau": r"r[ée]seau|graphe|graph\b|relation|social|internet|network|connexion",
    "automate": r"automate|algorithm|calcul|informati|programm|logique|turing|comput|software",
    "trame": r"sph[eè]re|plan[eè]te|astro|soleil|optique|lumi[eè]re|globe|planet|light|orbit",
    "flocon": r"cristal|glace|neige|sym[ée]tri|fractal|crystal|snow",
    "trajectoires": r"mouvement|trajectoir|dynamique|m[ée]canique|[ée]coulement|fluide|particul|conflit|motion|flow\b|flux",
    "semis": r"\bonde|signal|fr[ée]quence|vibration|acousti|bruit|statisti|mesure|spectr|wave|noise",
    "anneaux": r"diffusion|propagation|\bcycle|cercle|ripple|circle|radioacti",
    "taches": r"cellul|bact[ée]ri|tissu|organism|[ée]colog|biodivers|vivant|\bcells?\b|ecolog|d[ée]mixtion|spinodal",
    "lettres": r"langue|linguisti|vocabulaire|lexique|grammaire|[ée]criture|traduction|\bwords?\b|language|vocab",
    "pavage": r"g[ée]om[ée]tri|pavage|combinatoire|topolog|tiling|geometr",
    "colonnes": r"rapport|bilan|comparaison|budget|donn[ée]es|r[ée]sultats|report|survey|\bdata\b",
    "plan": r"\bcours\b|chapitre|programme|syllabus|organisation|m[ée]thode|course",
    "arcs": r"croissance|progression|apprentissage|[ée]volution|d[ée]veloppement|growth|progress",
    "pixels": r"\bjeux?\b|[ée]cran|num[ée]rique|pixel|\bgames?\b|screen|digital",
    "rayures": r"volume|mati[eè]re|mat[ée]riau|polym[eè]re|material|polymer",
}
TEINTES = {"claire": "claire", "clair": "claire", "light": "claire", "encre": "encre", "pleine": "encre", "ink": "encre",
           "sombre": "sombre", "nuit": "sombre", "dark": "sombre"}


# ---------- assemblage ----------

def extraire_bloc(corps):
    """Bloc « ::: couverture » (un SVG écrit pour ce document) : ôté du corps, rendu à part."""
    m = re.search(r'<div class="couverture"[^>]*>', corps)
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
    grand titre (trois lignes au plus en haut, quatre en bas) qui laisse à l'illustration une hauteur suffisante ; la
    fiche ne reste que si elle coûte peu au titre."""
    mots = titre.upper().split() or ["?"]
    # ligne en italique : 5,4 cqi, chasse moyenne 0,45 cadratin, trois lignes au plus
    l_sous = min(3, math.ceil(len(sous) * .45 * 5.4 / (84 * .9))) if sous else 0

    def plus_grand(fiche, image_min):
        fixe = 13.5 + 3.2 + (2.8 * 1.25 + 2.2 if sur else 0) + (l_sous * 5.4 * 1.16 + 2.2 if sous else 0)
        fixe += 3.4 * (4 if fiche else 3) + (math.ceil(fiche / 2) * 6.4 - 1 if fiche else 0) + .4
        for t in [x / 4 for x in range(60, 23, -1)]:
            lignes = lignes_titre(mots, t)
            if lignes and lignes <= (3 if place == "haut" else 4) and 150 - fixe - lignes * t * .98 >= image_min:
                return t
        return None

    for image_min in (74, 64, 56):
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
        if mot in ("", "oui", "yes", "auto", "true"):
            continue
        if mot in MOTIFS or mot in ALIAS:
            motif = ALIAS.get(mot, mot)
        elif mot in TEINTES:
            teinte = TEINTES[mot]
        elif mot in ("haut", "bas", "top", "bottom"):
            place = {"top": "haut", "bottom": "bas"}.get(mot, mot)
        elif mot.isdigit():
            variante = int(mot)
        else:
            avis.append(f"couverture : « {mot} » inconnu (motifs : {', '.join(MOTIFS)} ; teintes : claire, encre, sombre ; "
                        "haut, bas ; un nombre pour un autre tirage)")
    return motif, teinte, place, variante


def motif_du_sujet(meta, r):
    sujet = sans_accents(" ".join(meta.get(k, "") for k in ("titre", "court", "surtitre", "soustitre", "description")).lower())
    scores = {m: len(re.findall(sans_accents(motif), sujet)) for m, motif in INDICES.items()}
    meilleur = max(scores.values())
    return r.choice([m for m, s in scores.items() if s == meilleur] if meilleur else list(MOTIFS))


def composer(meta, d, lang, motif, teinte, place, tirage, graine, perso=None):
    """HTML de la couverture."""
    L, e, couleurs = TEXTES[lang], html.escape, palette(tirage, teinte)
    titre, r = d["titre"], random.Random(graine + 7)
    d = {**d, "inverse": luminance(rgb(couleurs["ce"])) > luminance(rgb(couleurs["cf"]))}
    if perso is not None:
        dessin = re.sub(r"<svg\b", '<svg aria-hidden="true" focusable="false"', re.sub(r"^\s*<p>|</p>\s*$", "", perso.strip()), count=1)
    else:
        rm = random.Random(graine + sum(map(ord, motif)))
        dessin = ('<svg viewBox="0 0 200 200" aria-hidden="true" focusable="false"><g fill="none" stroke-linecap="round" '
                  'stroke-linejoin="round">' + "".join(x for x in MOTIFS[motif](rm, d) if x) + "</g></svg>")
    sur, sous = meta.get("surtitre", "").strip(), meta.get("soustitre", "").strip()
    # fiche de laboratoire : jusqu'à trois mesures non nulles, puis le temps de lecture, en nombre pair de cases
    fiche = [(L[cle], chiffre(v, lang)) for cle, v in (("sections", len(d["sections"])), ("figures", d["figures"]),
                                                     ("formules", d["formules"]), ("exercices", d["exercices"])) if v][:3]
    if len(fiche) % 2 == 0 and fiche:
        fiche.pop()
    fiche.append((L["lecture"], f"{max(1, round(d['mots'] / 230))}\u202f{L['min']}"))
    t, garde = disposer(place, titre, sous, bool(sur) and place == "haut", len(fiche))
    fiche = fiche[:garde]
    p_sur = f'<p class="couv-sur">{e(sur)}</p>' if sur else ""
    p_titre = f'<p class="couv-titre" style="font-size:{n(t, 2)}cqi">{e(titre)}</p>'
    p_sous = f'<p class="couv-sous">{e(sous)}</p>' if sous else ""
    annee = re.match(r"\d{4}", meta.get("date", ""))
    gauche = " · ".join(x for x in (meta.get("auteur", ""), annee.group(0) if annee else meta.get("date", "")) if x)
    longueur = mots(d["mots"], lang, "\u00a0")
    pied = f'<p class="couv-pied"><span>{e(gauche)}</span><span>{longueur}</span></p>'
    # en haut : illustration toujours cadrée, filet sous le titre une fois sur deux ; en bas : filet entre les deux
    cadre, filet = (True, r.random() < .5) if place == "haut" else (r.random() < .4, True)
    image = f'<div class="couv-image{" couv-cadre" if cadre else ""}">{dessin}</div>'
    filet = '<div class="couv-filet"></div>' if filet else ""
    p_fiche = ('<dl class="couv-fiche">' + "".join(f"<div><dt>{e(a)}</dt><dd>{e(b)}</dd></div>" for a, b in fiche) + "</dl>"
               if fiche else "")
    if place == "haut":
        parties = [f'<div class="couv-tete">{p_sur}{p_titre}{p_sous}</div>', filet, image, p_fiche, pied]
    else:  # la ligne en italique passe au-dessus du titre (« of Transport / MODULARITY »)
        parties = [p_sur, image, filet, f'<div class="couv-tete">{p_sous}{p_titre}</div>', pied]
    # épaisseur : une page de tranche par pixel, de 2 (une note) à 14 (un long cours)
    ep = max(2, min(14, round(2 + 2.2 * math.log2(max(d["mots"], 200) / 200))))
    tranche = ",".join(f"{k}px {k}px 0 var(--tr{1 + k % 2})" for k in range(1, ep + 1)) + f",{ep + 1}px {ep + 1}px 0 var(--tr3)"
    style = ";".join(f"--{k}:{v}" for k, v in couleurs.items()) + f";--ep:{tranche}"
    return (f'<div class="couverture couv-{place} couv-{teinte}" aria-hidden="true" style="{style}">'
            f'<div class="couv">{"".join(x for x in parties if x)}</div></div>\n')


def preparer(meta, corps, plan_, lang, avis, brut=None):
    """Rend None sans demande ; sinon {"corps", "html", "resume"}. Pose meta["tirage"] s'il manque, pour que la page et
    sa couverture partagent l'encre."""
    valeur = (meta.get("couverture") or "").strip()
    corps, perso = extraire_bloc(corps)
    if (not valeur and perso is None) or valeur.lower() in ("non", "no", "false"):
        return None
    if perso is not None and "<svg" not in perso:
        avis.append('couverture : le bloc « ::: couverture » doit contenir un <svg viewBox="0 0 200 200">')
        perso = None
    lang = "en" if lang == "en" else "fr"
    motif, teinte, place, variante = lire_valeur(valeur, avis)
    titre = (meta.get("court") or meta.get("titre") or "Sans titre").strip()
    graine = int(hashlib.sha256(f"{titre}|{variante}".encode()).hexdigest()[:12], 16)
    r = random.Random(graine)
    tirage = (meta.get("tirage") or "").strip()
    if not re.fullmatch(r"#[0-9a-fA-F]{3,8}", tirage):
        tirage = r.choice(ENCRES)
        if not meta.get("tirage"):
            meta["tirage"] = tirage
    teinte = teinte or r.choice(("claire", "claire", "encre", "encre", "sombre"))
    place = place or r.choice(("haut", "haut", "bas"))
    motif = "personnel" if perso is not None else motif or motif_du_sujet(meta, r)
    d = mesurer(corps, plan_, titre, brut)
    return {"corps": corps, "html": composer(meta, d, lang, motif, teinte, place, tirage, graine, perso),
            "resume": f"{motif}, {teinte}, titre en {place}, {mots(d['mots'], lang)}"}


def planche(meta, corps, plan_, lang, avis, brut=None):
    """La couverture du document dans chaque motif (teintes et places en alternance), chacune sous la ligne d'en-tête
    qui la donne : pour choisir. Rend le corps HTML d'une page."""
    lang = "en" if lang == "en" else "fr"
    corps, _ = extraire_bloc(corps)
    titre = (meta.get("court") or meta.get("titre") or "Sans titre").strip()
    _, teinte, place, variante = lire_valeur(meta.get("couverture", ""), [])
    graine = int(hashlib.sha256(f"{titre}|{variante}".encode()).hexdigest()[:12], 16)
    tirage = (meta.get("tirage") or "").strip()
    if not re.fullmatch(r"#[0-9a-fA-F]{3,8}", tirage):
        tirage = random.Random(graine).choice(ENCRES)
    d, cases = mesurer(corps, plan_, titre, brut), []
    for k, motif in enumerate(MOTIFS):
        te = teinte or ("claire", "encre", "sombre")[k % 3]
        pl = place or ("haut", "bas")[k // 3 % 2]
        ligne = f"couverture: {motif} {te} {pl}" + (f" {variante}" if variante else "")
        cases.append(f'<div class="couv-case">{composer(meta, d, lang, motif, te, pl, tirage, graine)}'
                     f'<p><code>{ligne}</code></p></div>')
    return f'<div class="large"><div class="etagere">{"".join(cases)}</div></div>'
