"""TeXtured — motifs de couverture : un motif est une fonction (r, d) → éléments SVG dans le carré 0 0 200 200.

r est un random.Random dont la graine vient du titre (même document, même dessin ; un nombre dans « couverture: » en
tire un autre), d les mesures du document (mots, sections, paragraphes, figures, formules, exercices, mots fréquents,
lettres ; « inverse » : texte plus clair que le fond). Couleurs : currentColor (encre), var(--ca) (accent), var(--cd)
(trait doux), var(--cf) (fond, pour évider) ; rien en dur, la teinte de la couverture les fixe. Le groupe qui reçoit
les éléments a fill="none" et des bouts ronds : un trait n'a qu'à donner stroke, une forme pleine fill.

CATALOGUE (en fin de fichier) range les motifs par domaine, avec leur dessin et les mots du sujet qui les appellent ;
couverture.md n'en garde qu'une ligne par domaine, écrite à la main (lue à chaque couverture : rester bref) ; le
détail : python3 couverture.py --catalogue, ou textured.py --motifs sans sujet.
"""
import cmath
import html
import math
import re
import unicodedata
from collections import Counter, defaultdict

ENCRE, ACC, DOUX, FOND = "currentColor", "var(--ca)", "var(--cd)", "var(--cf)"


# ---------- outils ----------

def sans_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def n(x, k=1):
    s = f"{x:.{k}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


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


# ---------- formes générales et document ----------

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
    fente, haut, base = 184 / m, 166, 188
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
    boites = []
    boites.append(f'<rect x="70" y="{n(y0)}" width="60" height="18" rx="1.5" fill="{FOND}" stroke="{ENCRE}" stroke-width="1.3"/>')
    boites.append(f'<path d="M100 {n(y0 + 4.5)}l4.5 4.5-4.5 4.5-4.5-4.5z" fill="{ACC}"/>')
    for i, s in enumerate(secs):
        x = x0 + i * (w + ecart)
        traits.append(f"M{n(x + w / 2)} {n(yb)}V{n(yc)}")
        boites.append(f'<rect x="{n(x)}" y="{n(yc)}" width="{n(w)}" height="{n(hauteur(s))}" rx="1" '
                      f'fill="{ACC if i in surligne else FOND}" stroke="{ENCRE}" stroke-width="1.2"/>')
        subs = s["subs"][:6]
        if subs:
            rail, sw = x + 3.5, w - 7
            traits.append(f"M{n(rail)} {n(yc + h)}V{n(yc + h + 7 + (len(subs) - 1) * 17 + 5.5)}")
            for j, num in enumerate(subs):
                sy = yc + h + 7 + j * 17
                traits.append(f"M{n(rail)} {n(sy + 5.5)}H{n(x + 7)}")
                boites.append(f'<rect x="{n(x + 7)}" y="{n(sy)}" width="{n(sw)}" height="11" rx="1" fill="{FOND}" '
                              f'stroke="{ENCRE}" stroke-width="0.9"/>')
    return [f'<path d="{"".join(traits)}" stroke="{ENCRE}" stroke-width="1.1"/>'] + boites


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
    """Planche de petits glyphes de pixels symétriques, un à l'accent : numérique, écran, jeu."""
    c = r.choice((3, 4))
    fente, out = 184 / c, {ENCRE: [], ACC: []}
    px = fente / 7.4
    accent = r.randrange(c * c)
    for k in range(c * c):
        ox, oy = 8 + fente * (k % c) + (fente - 5 * px) / 2, 8 + fente * (k // c) + (fente - 5 * px) / 2 - px * .4
        bits = [[r.random() < .5 for _ in range(3)] for _ in range(5)]
        bits[2][2] = bits[2][2] or not any(map(any, bits))
        out[ACC if k == accent else ENCRE] += [(ox + j * px, oy + i * px) for i in range(5) for j in range(5) if bits[i][min(j, 4 - j)]]
    return [f'<path d="{carres(v, px * .9)}" fill="{k}"/>' for k, v in out.items() if v]


# ---------- outils des motifs dessinés ----------

def trait(pts, couleur=ENCRE, w=1.2, extra=""):
    return f'<path d="{trace(pts)}" stroke="{couleur}" stroke-width="{n(w, 2)}"{extra}/>'


def plein(pts, couleur=ENCRE, extra=""):
    return f'<path d="{trace(pts)}Z" fill="{couleur}"{extra}/>'


def disque(x, y, rayon, fond, bord=None, w=1.2):
    s = f' stroke="{bord}" stroke-width="{n(w, 2)}"' if bord else ""
    return f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(rayon)}" fill="{fond}"{s}/>'


def cercle(x, y, rayon, couleur=ENCRE, w=1.2, extra=""):
    return f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(rayon)}" stroke="{couleur}" stroke-width="{n(w, 2)}"{extra}/>'


def boite(x, y, l, h, fond=FOND, bord=ENCRE, w=1.2, rx=0):
    a = f' rx="{n(rx)}"' if rx else ""
    s = f' stroke="{bord}" stroke-width="{n(w, 2)}"' if bord else ""
    return f'<rect x="{n(x)}" y="{n(y)}" width="{n(l)}" height="{n(h)}"{a} fill="{fond}"{s}/>'


def morceaux(pts, x0=8, y0=8, x1=192, y1=192):
    """Chemin d'une courbe échantillonnée, coupée là où elle sort du rectangle."""
    d, dedans = [], False
    for x, y in pts:
        if x0 <= x <= x1 and y0 <= y <= y1:
            d.append(("L" if dedans else "M") + f"{n(x)} {n(y)}")
            dedans = True
        else:
            dedans = False
    return "".join(d)


def semis_dans(test, pas, x0=8, y0=8, x1=192, y1=192, decale=True):
    """Points d'une trame régulière (rangs décalés) qui passent le test."""
    out, y, rang = [], y0, 0
    while y <= y1:
        x = x0 + (pas / 2 if decale and rang % 2 else 0)
        while x <= x1:
            if test(x, y):
                out.append((x, y))
            x += pas
        y, rang = y + pas * (.866 if decale else 1), rang + 1
    return out


def bissection(f, a, b, k=40):
    fa = f(a)
    for _ in range(k):
        m = (a + b) / 2
        if (f(m) > 0) == (fa > 0):
            a, fa = m, f(m)
        else:
            b = m
    return (a + b) / 2


# ---------- motifs tirés des sujets, en abstraction ----------
# Le sujet ne donne que la structure : pas d'objet dessiné, pas d'axe, pas de texte. Chaque motif doit rester beau si
# on ignore d'où il vient.

# ---------- matière et polymères ----------

def pelote(r, d):
    """Marche aléatoire continue, persistante, qui s'enroule sans jamais se fermer ; ses deux bouts et son rayon de
    giration à l'accent, sur un semis clair : polymère, conformation, chaîne."""
    pts, a, x, y = [], r.uniform(0, 2 * math.pi), 100.0, 100.0
    pas = r.uniform(1.6, 2)
    for _ in range(r.randint(900, 1300)):
        a += r.gauss(0, .3)
        dx, dy = x - 100, y - 100
        rho = math.hypot(dx, dy)
        if rho > 40:
            a += math.remainder(math.atan2(-dy, -dx) - a, 2 * math.pi) * min(.35, (rho - 40) / 160)
        x, y = x + pas * math.cos(a), y + pas * math.sin(a)
        pts.append((x, y))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    e = min(1.0, 172 / max(max(xs) - min(xs), max(ys) - min(ys)))
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    pts = [(100 + (p[0] - cx) * e, 100 + (p[1] - cy) * e) for p in pts]
    gx, gy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
    rg = math.sqrt(sum((p[0] - gx) ** 2 + (p[1] - gy) ** 2 for p in pts) / len(pts))
    fond = [(x_, y_) for x_ in range(12, 190, 9) for y_ in range(12, 190, 9)]
    return [points(fond, 1.3, DOUX), cercle(gx, gy, rg, ACC, 1.8, ' stroke-dasharray="0 4.4"'), trait(pts, ENCRE, 1.5),
            points([pts[0], pts[-1]], 7.5, ACC)]


def binodale(r, d):
    """Champ de points mêlés (encre et accent) en haut ; vers le bas, une brèche s'ouvre et chaque couleur se range
    de son côté, plus serrée au bord de la brèche : démixtion, miscibilité, séparation de phases."""
    xc, yc = r.uniform(76, 124), r.uniform(30, 58)
    largeur, expo = r.uniform(30, 46), r.uniform(.45, .65)
    w = lambda y: largeur * ((y - yc) / (192 - yc)) ** expo if y > yc else 0
    classes = defaultdict(list)
    for x, y in semis_dans(lambda x, y: True, 5.4, 8, 8, 192, 192):
        x, y = x + r.uniform(-1, 1), y + r.uniform(-1, 1)
        if y <= yc + 4:
            classes[(r.choice((ENCRE, ACC)), 1.8)].append((x, y))
            continue
        cote = -1 if x < xc else 1
        delta, wy = abs(x - xc), w(y)
        if delta < wy:
            x = xc + cote * (wy + (wy - delta) * .45)
        prof = min(1.0, (y - yc) / (192 - yc) * 1.6)
        pres = max(0.0, 1 - (abs(x - xc) - wy) / 40)
        diam = round(1.8 + 2.2 * prof * pres, 1)
        melange = r.random() < .5 * (1 - prof)
        classes[(r.choice((ENCRE, ACC)) if melange else (ENCRE if cote < 0 else ACC), diam)].append((x, y))
    return [points(p, t, c) for (c, t), p in sorted(classes.items(), key=lambda k: (k[0][1], k[0][0]))]


def ternaire(r, d):
    """Trame triangulaire de points dont la taille suit trois dégradés, un par sommet ; une région à l'accent :
    trois constituants, solvant et non-solvant."""
    A, B, C = (8, 186.0), (192, 186.0), (100, 186 - 92 * math.sqrt(3))
    pas = r.choice((6.4, 7.2, 8))
    k = int(184 / pas)
    sa, sb, sc = r.uniform(.6, 1.4), r.uniform(.6, 1.4), r.uniform(.6, 1.4)
    cx, cy, rr = r.uniform(.15, .45), r.uniform(.15, .45), r.uniform(.12, .2)
    classes = defaultdict(list)
    for i in range(k + 1):
        for j in range(k + 1 - i):
            a, b = i / k, j / k
            c = max(0.0, 1 - a - b)
            x, y = a * A[0] + b * B[0] + c * C[0], a * A[1] + b * B[1] + c * C[1]
            t = max(a ** sa, b ** sb, c ** sc)
            diam = round(1.2 + 4 * t ** 1.6, 1)
            accent = (b - cx) ** 2 + (c - cy) ** 2 < rr ** 2
            classes[(ACC if accent else ENCRE, diam)].append((x, y))
    return [points(p, t, c) for (c, t), p in classes.items()]


def phases(r, d):
    """Trois textures (réseau régulier, tirets, semis épars) qui se partagent le carré le long de trois frontières
    laissées vides, réunies en un point à l'accent : états de la matière, changements de phase."""
    xt, yt = r.uniform(70, 96), r.uniform(116, 140)
    xc, yc = r.uniform(156, 182), r.uniform(28, 52)
    penche = r.uniform(4, 14) * (-1 if r.random() < .25 else 1)
    subl = lambda x: 196 - (196 - yt) * (max(0.0, x - 4) / (xt - 4)) ** 2.2
    vap = lambda x: yt - (yt - yc) * ((x - xt) / (xc - xt)) ** 1.5
    fus = lambda y: xt + penche * (yt - y) / (yt - 4)

    def region(x, y):
        if x <= xt:
            bas = subl(x)
        elif x <= xc:
            bas = vap(x)
        else:
            return "super" if y < yc else "gaz"
        if y > bas:
            return "gaz"
        return "solide" if x < fus(y) else "liquide"

    def net(x, y, z):
        return all(region(x + dx, y + dy) == z for dx, dy in ((-4.5, 0), (4.5, 0), (0, -4.5), (0, 4.5)))

    sol = semis_dans(lambda x, y: region(x, y) == "solide" and net(x, y, "solide"), 6.4, 8, 8, 192, 192, decale=False)
    sup = semis_dans(lambda x, y: region(x, y) == "super" and net(x, y, "super"), 5, 8, 8, 192, 192)
    gaz = [(x, y) for x, y in ((r.uniform(8, 192), r.uniform(8, 192)) for _ in range(1400)) if region(x, y) == "gaz" and net(x, y, "gaz")][:150]
    liq = [f"M{n(x)} {n(y)}h{n(r.uniform(2.5, 5))}" for x, y in semis_dans(
        lambda x, y: region(x, y) == "liquide" and net(x, y, "liquide") and region(x + 8, y) == "liquide", 7, 8, 8, 192, 192)]
    return [points(sol, 2.8, ENCRE), points(sup, 1.6, DOUX), points(gaz, 2, ENCRE),
            f'<path d="{"".join(liq)}" stroke="{ENCRE}" stroke-width="1.4"/>', points([(xt, yt)], 8, ACC), points([(xc, yc)], 4.6, ACC)]


def spherolites(r, d):
    """Sphérolites : lamelles rayonnantes qui se rencontrent en frontières droites, croix de Malte de la lumière
    polarisée : cristallisation, semi-cristallin, morphologie."""
    centres = []
    k = r.randint(3, 6)
    for _ in range(500):
        if len(centres) == k:
            break
        p = (r.uniform(24, 176), r.uniform(24, 176))
        if all(math.dist(p, q) > 54 for q in centres):
            centres.append(p)

    def portee(i, a):
        ux, uy = math.cos(a), math.sin(a)
        cx, cy = centres[i]
        t = min((194 - cx) / ux if ux > 1e-9 else (6 - cx) / ux if ux < -1e-9 else 1e9,
                (194 - cy) / uy if uy > 1e-9 else (6 - cy) / uy if uy < -1e-9 else 1e9)
        for j, (qx, qy) in enumerate(centres):
            s = ux * (qx - cx) + uy * (qy - cy)
            if j != i and s > 0:
                t = min(t, ((qx - cx) ** 2 + (qy - cy) ** 2) / (2 * s))
        return t - 1.4

    ia, traits = r.randrange(len(centres)), {ENCRE: [], DOUX: [], ACC: []}
    for i, (cx, cy) in enumerate(centres):
        m = r.randint(66, 96)
        for j in range(m):
            a = 2 * math.pi * (j + r.uniform(-.3, .3)) / m
            clair = math.sin(2 * a) ** 2 > .42
            cle = (ACC if i == ia else ENCRE) if clair else DOUX
            t, r0 = portee(i, a), r.uniform(2.5, 6)
            if t > r0:
                traits[cle].append(f"M{n(cx + r0 * math.cos(a))} {n(cy + r0 * math.sin(a))}L{n(cx + t * math.cos(a))} {n(cy + t * math.sin(a))}")
            if r.random() < .35 and t > 30:
                s, b = t * r.uniform(.3, .65), a + r.choice((-1, 1)) * r.uniform(.05, .1)
                t2 = portee(i, b)
                traits[cle].append(f"M{n(cx + s * math.cos(a))} {n(cy + s * math.sin(a))}L{n(cx + t2 * math.cos(b))} {n(cy + t2 * math.sin(b))}")
    largeur = {ENCRE: 1.05, DOUX: .7, ACC: 1.3}
    return ([f'<path d="{"".join(v)}" stroke="{k_}" stroke-width="{largeur[k_]}"/>' for k_, v in traits.items() if v]
            + [points(centres, 4, ENCRE)])


def blobs(r, d):
    """Chaîne de blobs : une pelote vue à l'échelle de la longueur de corrélation, chaque blob une petite marche
    aléatoire, un blob à l'accent : régimes de concentration, semi-dilué, polyélectrolytes."""
    R, meilleurs = r.uniform(9, 12), []
    for _ in range(8):
        centres, a = [(r.uniform(24, 70), r.uniform(30, 170))], r.uniform(-.7, .7)
        for _ in range(70):
            choix = None
            for _ in range(14):
                b = a + r.uniform(-1.2, 1.2)
                x, y = centres[-1][0] + 2 * R * math.cos(b), centres[-1][1] + 2 * R * math.sin(b)
                if not (8 + R < x < 192 - R and 8 + R < y < 192 - R):
                    continue
                ecart = min((math.dist((x, y), c) for c in centres[:-1]), default=99)
                if choix is None or ecart > choix[0]:
                    choix = (ecart, x, y, b)
            if choix is None or choix[0] < 1.75 * R:
                break
            _, x, y, a = choix
            centres.append((x, y))
        if len(centres) > len(meilleurs):
            meilleurs = centres
        if len(meilleurs) > 26:
            break
    centres, chaine = meilleurs, []
    for k, (cx, cy) in enumerate(centres):
        if k + 1 < len(centres):
            but = ((cx + centres[k + 1][0]) / 2, (cy + centres[k + 1][1]) / 2)
        else:
            px, py = centres[k - 1] if k else (cx - 1, cy)
            u = math.dist((cx, cy), (px, py)) or 1
            but = (cx + (cx - px) / u * R * .7, cy + (cy - py) / u * R * .7)
        p = chaine[-1] if chaine else (cx - R * .6, cy)
        if not chaine:
            chaine.append(p)
        m = r.randint(6, 8)
        for i in range(m):
            a = r.uniform(0, 2 * math.pi)
            x = p[0] + (but[0] - p[0]) / (m - i) + R * .5 * math.cos(a)
            y = p[1] + (but[1] - p[1]) / (m - i) + R * .5 * math.sin(a)
            dx, dy = x - cx, y - cy
            if math.hypot(dx, dy) > R * .9 and i < m - 1:
                f = R * .9 / math.hypot(dx, dy)
                x, y = cx + dx * f, cy + dy * f
            p = (x, y) if i < m - 1 else but
            chaine.append(p)
    ka = r.randrange(len(centres))
    return ([disque(*centres[ka], R, ACC)]
            + [disque(cx, cy, R, FOND, DOUX, 1.3) for k, (cx, cy) in enumerate(centres) if k != ka]
            + [trait(chaine, ENCRE, 1.5), points(chaine, 2.6, ENCRE), points([chaine[0], chaine[-1]], 5, ENCRE)])


def nodules(r, d):
    """Particules cœur-écorce dispersées dans une matrice : renforcement au choc, mélanges, latex, émulsions."""
    parts = []
    for _ in range(3000):
        if len(parts) >= 60:
            break
        rr = min(15.0, max(3.0, r.lognormvariate(1.9, .42)))
        x, y = r.uniform(8 + rr, 192 - rr), r.uniform(8 + rr, 192 - rr)
        if all(math.dist((x, y), (a, b)) > rr + c + 3.2 for a, b, c in parts):
            parts.append((x, y, rr))
    matrice = semis_dans(lambda x, y: all(math.dist((x, y), (a, b)) > c + 2.2 for a, b, c in parts), 6.2, 10, 10, 190, 190)
    out = [points(matrice, 1.3, DOUX)]
    for x, y, rr in parts:
        sorte = r.random()
        if rr < 5 or sorte < .25:
            out.append(disque(x, y, rr, ENCRE))
        elif sorte < .8:
            out += [disque(x, y, rr, ENCRE), disque(x, y, rr * .62, ACC)]
        else:
            out += [disque(x, y, rr, ENCRE), disque(x, y, rr * .74, FOND), disque(x, y, rr * .52, ACC), disque(x, y, rr * .22, ENCRE)]
    return out


def masses(r, d):
    """Barres fines en cloche sur une échelle logarithmique, une ou deux bosses, la barre de la moyenne en masse à
    l'accent : distribution des masses molaires, polydispersité."""
    mu, sig = r.uniform(4.3, 5.5), r.uniform(.22, .4)
    pics = [(mu, sig, 1.0)]
    if r.random() < .35:
        pics.append((mu + r.choice((-1, 1)) * r.uniform(.7, 1.05), sig * r.uniform(.55, .85), r.uniform(.3, .6)))
    lo, hi, nb, base = 2.8, 7.2, r.choice((40, 48, 56)), 182
    X = lambda l: 12 + 176 * (l - lo) / (hi - lo)
    ls = [lo + (hi - lo) * (k + .5) / nb for k in range(nb)]
    w = [sum(a * math.exp(-(l - m) ** 2 / (2 * s * s)) for m, s, a in pics) for l in ls]
    tot, wmax = sum(w), max(w)
    lmw = math.log10(sum(v * 10 ** l for l, v in zip(ls, w)) / tot)
    ia = min(range(nb), key=lambda k: abs(ls[k] - lmw))
    barres = {ENCRE: [], ACC: []}
    for k, (l, v) in enumerate(zip(ls, w)):
        h = 150 * v / wmax * r.uniform(.93, 1.07)
        if h > 1.2:
            barres[ACC if k == ia else ENCRE].append(f"M{n(X(l))} {base}V{n(base - h)}")
    return [f'<path d="{"".join(v)}" stroke="{c}" stroke-width="{n(176 / nb * .56, 2)}" stroke-linecap="butt"/>' for c, v in barres.items() if v]


def fibres(r, d):
    """Tirets courts alignés en haut et en bas, en travers au milieu, entre deux filets : composites, renforts,
    orientation, injection."""
    haut, bas, fib = 22, 178, []
    for _ in range(4000):
        if len(fib) >= 150:
            break
        x, y = r.uniform(14, 186), r.uniform(haut + 7, bas - 7)
        if all(math.dist((x, y), q[:2]) > 9 for q in fib):
            s = abs(y - 100) / 78
            a = r.gauss(0, .14) if s > .5 else math.pi / 2 + r.gauss(0, .3) if s < .28 else r.uniform(0, math.pi)
            fib.append((x, y, a, r.uniform(5.5, 7.5)))
    traits = {ENCRE: [], ACC: []}
    for x, y, a, l in fib:
        dx, dy = l * math.cos(a), l * math.sin(a)
        traits[ACC if r.random() < .07 else ENCRE].append(f"M{n(x - dx)} {n(y - dy)}L{n(x + dx)} {n(y + dy)}")
    return ([f'<path d="{"".join(v)}" stroke="{k}" stroke-width="2.1"/>' for k, v in traits.items() if v]
            + [trait([(8, haut), (192, haut)], ENCRE, 2.6), trait([(8, bas), (192, bas)], ENCRE, 2.6)])


# ---------- mécanique et rhéologie ----------

def rheologie(r, d):
    """Faisceau de courbes qui partent à plat puis plongent toutes à la même pente, sur une grille de points ; une
    courbe à l'accent ponctuée de ronds : rhéologie, viscosité, écoulement."""
    X = lambda lg: 8 + 184 * (lg + 2) / 6
    Y = lambda le: 188 - 176 * le / 5.4
    nn, k = r.uniform(.22, .5), r.randint(9, 13)
    ka, out = r.randrange(k), [points([(X(i), Y(j)) for i in range(-2, 5) for j in range(0, 6)], 1.8, DOUX)]
    pas = 4.2 / k
    for i in range(k):
        le0 = .7 + i * pas + r.uniform(-.06, .06)
        lam = le0 - 3.2 + r.uniform(-.25, .25)
        f = lambda lg: le0 + (nn - 1) / 2 * math.log10(1 + 10 ** (2 * (lam + lg)))
        pts = [(X(lg), Y(f(lg))) for lg in (-2 + 6 * s / 120 for s in range(121))]
        if i == ka:
            out.append(f'<path d="{morceaux(pts)}" stroke="{ACC}" stroke-width="3"/>')
            mes = [(X(lg), Y(f(lg))) for lg in (-1.75 + .5 * s for s in range(12))]
            out.append("".join(disque(x, y, 3, FOND, ACC, 1.6) for x, y in mes if 12 < x < 190 and 12 < y < 188))
        else:
            out.append(f'<path d="{morceaux(pts)}" stroke="{ENCRE}" stroke-width="1.3"/>')
    return out


def module(r, d):
    """Marches descendantes en faisceau (une falaise et son plateau), et sous elles une cloche en aplat d'accent :
    viscoélasticité, transition vitreuse, analyse mécanique dynamique."""
    X = lambda t: 8 + 184 * t
    tg, larg, haut, cao = r.uniform(.32, .5), r.uniform(.03, .05), r.uniform(26, 36), r.uniform(96, 116)
    hp, k = r.uniform(60, 80), r.randint(4, 7)

    def ep(t, dt):
        return haut + (cao - haut) / (1 + math.exp(-(t - tg - dt) / larg))

    td = lambda t: 190 - hp * math.exp(-((t - tg - .03) / (larg * 2.1)) ** 2)
    ts = [i / 150 for i in range(151)]
    out = [plein([(X(0), 190)] + [(X(t), td(t)) for t in ts] + [(X(1), 190)], ACC)]
    for i in range(k):
        dt = .028 * (i - (k - 1) / 2)
        pts = [(X(t), ep(t, dt) + 3.5 * i) for t in ts]
        out += [trait(pts, FOND, 5), trait(pts, ENCRE, 2.4 if i == k // 2 else 1.3)]
    return out


def traction(r, d):
    """Faisceau de courbes issues d'un même coin : montée raide, bosse, palier, remontée ; chacune finit sur un point,
    une à l'accent : mécanique des matériaux, essais, rupture."""
    k, out = r.randint(8, 12), []
    ka = r.randrange(k)
    for i in range(k):
        f = i / (k - 1)
        sy, e0, ey = .3 + .45 * f + r.uniform(-.03, .03), .018 + .012 * (1 - f), .04 + .02 * f
        chute, eh, er = .12 + .14 * (1 - f), .3 + .25 * f, .55 + .4 * (1 - f) + r.uniform(-.04, .04)
        g = lambda e: (sy * math.tanh(e / e0) * (1 - chute * (1 - math.exp(-max(0.0, e - ey) / .03))) + 1.1 * max(0.0, e - eh) ** 2)
        pts = [(8 + 184 * e, 190 - 172 * g(e)) for e in (er * j / 100 for j in range(101))]
        pts = [(x, y) for x, y in pts if y > 8]
        acc = i == ka
        out += [trait(pts, ACC if acc else ENCRE, 2.8 if acc else 1.4), points([pts[-1]], 6.4 if acc else 4.6, ACC if acc else ENCRE)]
    return out


# ---------- réacteurs, procédés et régulation ----------

def cascade(r, d):
    """Cellules rondes en file, chacune un semis où l'accent gagne sur l'encre, puis une longue bande où le mélange
    finit de tourner : génie de la réaction, réacteurs en série, conversion, procédé."""
    k = r.choice((3, 4, 5))
    diam = (176 - 10 * (k - 1)) / k
    da = r.uniform(.4, .9)
    conv = [1 - 1 / (1 + da) ** (i + 1) for i in range(k)]
    out, react, prod = [], [], []
    y0 = r.uniform(58, 76)
    for i in range(k):
        cx = 12 + diam / 2 + i * (diam + 10)
        out.append(cercle(cx, y0, diam / 2, ENCRE, 1.6))
        for p in semis_dans(lambda x, y: math.dist((x, y), (cx, y0)) < diam / 2 - 4, 5, cx - diam / 2, y0 - diam / 2, cx + diam / 2, y0 + diam / 2):
            (prod if r.random() < conv[i] else react).append(p)
    yb, hb = r.uniform(130, 146), r.uniform(34, 44)
    out.append(f'<rect x="12" y="{n(yb)}" width="176" height="{n(hb)}" rx="{n(hb / 2)}" stroke="{ENCRE}" stroke-width="1.6"/>')
    for x, y in semis_dans(lambda x, y: 18 < x < 182 and yb + 4 < y < yb + hb - 4, 4.6, 16, yb, 184, yb + hb):
        t = (x - 16) / 168
        (prod if r.random() < conv[-1] + (.99 - conv[-1]) * t else react).append((x, y))
    return out + [points(react, 2.4, ENCRE), points(prod, 3, ACC)]


def dts(r, d):
    """Crêtes superposées, de la plus étalée (en haut) à la plus pointue (en bas), une crête pleine à l'accent et un
    trait vertical au bout : distribution des temps de séjour, traceur, dispersion."""
    js = sorted(r.sample((1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 22, 30, 45), r.randint(8, 11)))
    K, X = len(js), (lambda t: 8 + 184 * t / 2.6)
    pas = 136 / K
    out = [trait([(X(1), 18), (X(1), 192)], DOUX, 1, ' stroke-dasharray="2 2.6"')]
    ka = r.randrange(1, K - 1)
    for k, j in enumerate(js):
        y0, amp = 38 + k * pas, 40 * (.62 + .38 * k / (K - 1))
        lnmax = (j * math.log(j) + (j - 1) * math.log((j - 1) / j) - (j - 1) - math.lgamma(j)) if j > 1 else 0
        pts = []
        for s in range(0, 157):
            t = 2.6 * s / 156
            e = (j * math.log(j) + (j - 1) * math.log(t) - j * t - math.lgamma(j)) if t > 0 else (0 if j == 1 else -50)
            pts.append((X(t), y0 - amp * math.exp(e - lnmax)))
        acc = k == ka
        out += [plein([(X(0), y0)] + pts + [(X(2.6), y0)], ACC if acc else FOND), trait(pts, ACC if acc else ENCRE, 2.2 if acc else 1.3)]
    yb = 38 + K * pas
    return out + [plein([(X(0), yb + 1), (X(2.6), yb + 1), (X(2.6), 200), (X(0), 200)], FOND), trait([(X(0), yb), (X(2.6), yb)], ENCRE, 1.3),
                  trait([(X(1), yb), (X(1), yb - 44)], ACC, 3.2)]


def arrhenius(r, d):
    """Éventail de droites issues d'un même point, chacune jalonnée de ronds, une à l'accent, sur une grille de
    points : cinétique, énergie d'activation, catalyse."""
    px, py = r.uniform(10, 26), r.uniform(10, 34)
    k = r.randint(9, 15)
    a0, a1 = math.radians(r.uniform(10, 22)), math.radians(r.uniform(58, 76))
    ka = r.randrange(k)
    out = [points([(x, y) for x in range(20, 191, 24) for y in range(20, 191, 24)], 1.6, DOUX)]
    for i in range(k):
        a = a0 + (a1 - a0) * i / (k - 1)
        t = min((192 - px) / math.cos(a), (192 - py) / math.sin(a))
        x1, y1 = px + t * math.cos(a), py + t * math.sin(a)
        acc = i == ka
        out.append(trait([(px, py), (x1, y1)], ACC if acc else ENCRE, 2.2 if acc else 1))
        for j in range(1, 7):
            f = j / 6.6 + r.uniform(-.03, .03)
            out.append(disque(px + f * t * math.cos(a), py + f * t * math.sin(a), 2.4, ACC if acc else FOND, None if acc else ENCRE, 1.1))
    return out + [points([(px, py)], 7, ENCRE)]


def semenov(r, d):
    """Trame de courbes en S de plus en plus raides, traversée de droites parallèles ; aux croisements, des ronds :
    stabilité, emballement thermique, états stationnaires."""
    k, m = r.randint(9, 14), r.randint(4, 6)
    pente, ka = r.uniform(.55, .95), r.randrange(k)
    X, Y = (lambda u: 8 + 184 * u), (lambda v: 192 - 184 * v)
    out, ronds = [], {ENCRE: [], ACC: []}
    droites = [(-.55 + 1.25 * j / (m - 1)) for j in range(m)]
    for j, b in enumerate(droites):
        u0, u1 = max(0.0, -b / pente), min(1.0, (1 - b) / pente)
        if u1 > u0:
            out.append(trait([(X(u0), Y(pente * u0 + b)), (X(u1), Y(pente * u1 + b))], DOUX, 1.2))
    for i in range(k):
        w, um = .02 + .14 * (1 - i / (k - 1)) ** 1.5, .5 + r.uniform(-.06, .06)
        g = lambda u: .04 + .92 / (1 + math.exp(-(u - um) / w))
        acc = i == ka
        out.append(trait([(X(u / 160), Y(g(u / 160))) for u in range(161)], ACC if acc else ENCRE, 2.4 if acc else 1.1))
        for b in droites:
            f = lambda u: pente * u + b - g(u)
            for q in range(120):
                u_a, u_b = q / 120, (q + 1) / 120
                if (f(u_a) > 0) != (f(u_b) > 0):
                    u = bissection(f, u_a, u_b)
                    ronds[ACC if acc else ENCRE].append((X(u), Y(g(u))))
    return out + [points(ronds[ENCRE], 3.4, ENCRE), points(ronds[ACC], 5, ACC)]


def mccabe(r, d):
    """Escaliers en terrasses, copies d'un même escalier aux marches de plus en plus courtes, décalées le long de la
    diagonale ; une terrasse à l'accent : distillation, étages, équilibre liquide-vapeur, cascade, dimensionnement."""
    a = r.uniform(2.2, 3.6)
    eq = lambda x: a * x / (1 + (a - 1) * x)
    inv = lambda y: y / (a - (a - 1) * y)
    x, y, ref = 1.0, 1.0, [(1.0, 1.0)]
    while x > .04 and len(ref) < 40:
        x2 = inv(y)
        ref += [(x2, y), (x2, x2 * r.uniform(.86, .9))]
        x, y = x2, x2 * .88
    k, dec = r.randint(6, 10), r.uniform(.07, .1)
    ka, out = r.randrange(k), []
    for i in range(k):
        o = (i - (k - 1) / 2) * dec
        pts = [(8 + 184 * (px - o), 192 - 184 * (py + o)) for px, py in ref]
        out.append(f'<path d="{morceaux(pts)}" stroke="{ACC if i == ka else ENCRE}" stroke-width="{2.6 if i == ka else 1.4}"/>')
    return out

def amortie(r, d):
    """Rangées d'ondes amorties, de la plus nerveuse à la plus sage, une à l'accent : régulation, réponse indicielle,
    boucle de régulation, dynamique des systèmes."""
    k = r.randint(7, 11)
    pas = 170 / k
    ka, out = r.randrange(k), []
    w0 = r.uniform(.07, .1)
    for i in range(k):
        z = .06 + .7 * (i / (k - 1)) ** 1.4
        y0 = 22 + i * pas + pas * .55
        amp = pas * r.uniform(1.1, 1.5)
        wd = w0 * math.sqrt(max(1e-6, 1 - z * z))
        pts = [(8 + t, y0 - amp * math.exp(-z * w0 * t) * math.cos(wd * t)) for t in range(0, 185, 2)]
        acc = i == ka
        out.append(trait(pts, ACC if acc else ENCRE, 2.8 if acc else 1.5))
    return out


# ---------- calcul et plans d'expériences ----------

def maillage(r, d):
    """Maillage triangulaire resserré autour d'un point chaud, triangles teintés selon le champ calculé : éléments
    finis, différences finies, EDP, simulation numérique."""
    m, gam = r.randint(10, 14), r.uniform(1.3, 1.65)
    fx, fy = r.uniform(.22, .78), r.uniform(.22, .78)

    def resserre(u, v):
        dx, dy = u - fx, v - fy
        lx, ly = (fx if dx < 0 else 1 - fx), (fy if dy < 0 else 1 - fy)
        dist = max(abs(dx) / lx, abs(dy) / ly)
        k = dist ** (gam - 1) if dist > 0 else 0
        return fx + dx * k, fy + dy * k

    noeuds = {}
    for i in range(m + 1):
        for j in range(m + 1):
            u, v = resserre(i / m, j / m)
            if 0 < i < m and 0 < j < m:
                u += r.uniform(-.18, .18) / m * (.4 + abs(u - fx))
                v += r.uniform(-.18, .18) / m * (.4 + abs(v - fy))
            noeuds[i, j] = (8 + 184 * u, 8 + 184 * v)
    sig = r.uniform(.16, .26)
    champ = lambda x, y: math.exp(-(((x - 8) / 184 - fx) ** 2 + ((y - 8) / 184 - fy) ** 2) / sig ** 2)
    tri, aretes = {ACC: [], DOUX: []}, []
    for i in range(m):
        for j in range(m):
            a, b, c, e = noeuds[i, j], noeuds[i + 1, j], noeuds[i + 1, j + 1], noeuds[i, j + 1]
            moities = ((a, b, c), (a, c, e)) if (i + j) % 2 else ((a, b, e), (b, c, e))
            for t in moities:
                v = champ(sum(p[0] for p in t) / 3, sum(p[1] for p in t) / 3)
                if v > .62:
                    tri[ACC].append(trace(t) + "Z")
                elif v > .3:
                    tri[DOUX].append(trace(t) + "Z")
            aretes.append(f"M{n(a[0])} {n(a[1])}L{n(c[0])} {n(c[1])}" if (i + j) % 2 else f"M{n(b[0])} {n(b[1])}L{n(e[0])} {n(e[1])}")
    for i in range(m + 1):
        aretes.append(trace([noeuds[i, j] for j in range(m + 1)]))
        aretes.append(trace([noeuds[j, i] for j in range(m + 1)]))
    return ([f'<path d="{"".join(v)}" fill="{k}"/>' for k, v in tri.items() if v]
            + [f'<path d="{"".join(aretes)}" stroke="{ENCRE}" stroke-width="0.75"/>', boite(8, 8, 184, 184, "none", ENCRE, 1.8),
               points([(8 + 184 * fx, 8 + 184 * fy)], 4.2, ENCRE)])


def tangentes(r, d):
    """Courbes données par leurs seules tangentes, à la façon des fils tendus : chaque nappe joint deux bords du
    carré, l'une à l'accent : méthodes numériques, Newton, itérations, convergence."""
    out = []
    coins = r.sample([((8, 8), (8, 192), (192, 192)), ((8, 192), (192, 192), (192, 8)), ((192, 192), (192, 8), (8, 8)),
                      ((192, 8), (8, 8), (8, 192))], r.choice((2, 2, 3)))
    ka = r.randrange(len(coins))
    for c, (A, B, C) in enumerate(coins):
        k = r.randint(18, 28)
        traits = []
        for i in range(k + 1):
            t = i / k
            p = (A[0] + (B[0] - A[0]) * t, A[1] + (B[1] - A[1]) * t)
            q = (B[0] + (C[0] - B[0]) * t, B[1] + (C[1] - B[1]) * t)
            traits.append(f"M{n(p[0])} {n(p[1])}L{n(q[0])} {n(q[1])}")
        out.append(f'<path d="{"".join(traits)}" stroke="{ACC if c == ka else ENCRE}" stroke-width="{1.4 if c == ka else .9}"/>')
    return out


def cube(r, d):
    """Réseau de points en perspective isométrique, chaque point grand ou petit selon une réponse cachée, les plus
    grands à l'accent : plans d'expériences, facteurs, essais."""
    m = r.choice((3, 4, 5))
    a = 62 / (m - 1)
    coef = [r.uniform(-1, 1) for _ in range(7)]
    rep = lambda x, y, z: coef[0] * x + coef[1] * y + coef[2] * z + coef[3] * x * y + coef[4] * x * z + coef[5] * y * z + coef[6] * x * x
    pts = []
    for i in range(m):
        for j in range(m):
            for k in range(m):
                x, y, z = (2 * i / (m - 1) - 1, 2 * j / (m - 1) - 1, 2 * k / (m - 1) - 1)
                pts.append(((i - j) * a * .866, (i + j) * a * .5 - k * a, rep(x, y, z), i + j - k))
    vals, xs, ys = [p[2] for p in pts], [p[0] for p in pts], [p[1] for p in pts]
    lo, hi = min(vals), max(vals)
    dx, dy = 100 - (min(xs) + max(xs)) / 2, 100 - (min(ys) + max(ys)) / 2
    out = []
    for x, y, v, prof in sorted(pts, key=lambda p: p[3]):
        t = (v - lo) / ((hi - lo) or 1)
        out.append(disque(x + dx, y + dy, 2 + 6.5 * t, ACC if t > .72 else ENCRE if t > .3 else FOND, None if t > .3 else ENCRE, 1.3))
    return out


def isoreponses(r, d):
    """Lignes de niveau emboîtées (ellipses ou col), coupées par le carré, l'intérieur à l'accent : surface de
    réponse, optimisation, modélisation."""
    X, Y = (lambda u: 100 + 72 * u), (lambda v: 100 - 72 * v)
    ux, uy, phi = r.uniform(-.5, .5), r.uniform(-.5, .5), r.uniform(0, math.pi)
    a, b = r.uniform(.28, .5), r.uniform(.5, .95)
    col = r.random() < .3
    cos_, sin_ = math.cos(phi), math.sin(phi)
    vers = lambda p, q: (ux + p * cos_ - q * sin_, uy + p * sin_ + q * cos_)
    out, ka = [], r.randint(2, 5)
    for k in range(1, 15):
        s = math.sqrt(k)
        if col:
            branches = [[(sg * a * s * math.cosh(t), b * s * math.sinh(t)) for t in (x / 20 for x in range(-50, 51))] for sg in (1, -1)]
            branches += [[(a * s * math.sinh(t), sg * b * s * math.cosh(t)) for t in (x / 20 for x in range(-50, 51))] for sg in (1, -1)]
        else:
            branches = [[(a * s * .5 * math.cos(t), b * s * .5 * math.sin(t)) for t in (2 * math.pi * x / 90 for x in range(91))]]
        for br in branches:
            pts = [(X(u), Y(v)) for u, v in (vers(p, q) for p, q in br)]
            out.append(f'<path d="{morceaux(pts)}" stroke="{ACC if k == ka else ENCRE}" stroke-width="{2.4 if k == ka else 1.2}"/>')
    if not col:
        out.insert(0, plein([(X(u), Y(v)) for u, v in (vers(a * .5 * math.cos(t), b * .5 * math.sin(t)) for t in (2 * math.pi * x / 40 for x in range(40)))], ACC))
    return out


def pareto(r, d):
    """Colonnes de points de hauteurs décroissantes ; les premières à l'encre, coiffées d'accent, les autres en trait
    doux : effets, criblage, analyse de variance, qualité."""
    k = r.randint(11, 16)
    vals = sorted((r.expovariate(1) ** 1.3 for _ in range(k)), reverse=True)
    seuil = vals[r.randint(2, min(4, k - 2))] * r.uniform(1.02, 1.2)
    fente, base, pas = 184 / k, 188, 6.6
    classes = defaultdict(list)
    for i, v in enumerate(vals):
        x = 8 + fente * (i + .5)
        nb = max(1, round(170 * v / vals[0] / pas))
        for j in range(nb):
            couleur = (ACC if j == nb - 1 else ENCRE) if v > seuil else DOUX
            classes[couleur].append((x, base - j * pas))
    t = min(5.6, fente * .7)
    return [points(p, t, c) for c, p in classes.items()]


# ---------- risques et sécurité ----------

def braises(r, d):
    """Mosaïque de triangles que chauffe un champ montant du bas : les plus chauds pleins d'accent, les tièdes à
    l'encre, les froids à peine tracés : incendie, combustion, inflammabilité, explosion."""
    cote = r.choice((16, 18.4, 20))
    h = cote * math.sqrt(3) / 2
    x0, foyer = r.uniform(70, 130), r.uniform(.6, 1)
    phases = [r.uniform(0, 6.3) for _ in range(3)]
    champ = lambda x, y: (math.exp(-((x - x0 - 14 * math.sin(y / 23 + phases[0])) / (34 + .35 * (196 - y))) ** 2)
                          * (y / 196) ** foyer * (.85 + .15 * math.sin(x / 11 + phases[1]) * math.cos(y / 13 + phases[2])))
    tri = {ACC: [], ENCRE: [], DOUX: []}
    for j in range(int(200 / h) + 1):
        for i in range(-1, int(200 / (cote / 2)) + 1):
            x, y = i * cote / 2, j * h
            haut = (i + j) % 2 == 0
            t = [(x, y + h), (x + cote / 2, y), (x + cote, y + h)] if haut else [(x, y), (x + cote, y), (x + cote / 2, y + h)]
            v = champ(sum(p[0] for p in t) / 3, sum(p[1] for p in t) / 3) + r.uniform(-.08, .08)
            cle = ACC if v > .62 else ENCRE if v > .3 else DOUX if v > .12 else None
            if cle:
                c = [(sum(p[0] for p in t) / 3, sum(p[1] for p in t) / 3)]
                t2 = [(c[0][0] + (p[0] - c[0][0]) * .82, c[0][1] + (p[1] - c[0][1]) * .82) for p in t]
                tri[cle].append(trace(t2) + "Z")
    return ([f'<path d="{"".join(tri[DOUX])}" stroke="{DOUX}" stroke-width="1"/>']
            + [f'<path d="{"".join(v)}" fill="{k}"/>' for k, v in ((ENCRE, tri[ENCRE]), (ACC, tri[ACC])) if v])


def eventails(r, d):
    """Deux éventails de lignes courbes qui convergent vers un même point puis s'ouvrent de l'autre côté ; quelques
    lignes et le point à l'accent : nœud papillon, scénarios, causes et conséquences, barrières."""
    cx, cy = r.uniform(90, 110), r.uniform(88, 112)
    out, bouts = [], {ENCRE: [], ACC: []}
    for cote in (-1, 1):
        k = r.randint(13, 21)
        for i in range(k):
            y = 10 + 180 * (i + r.uniform(.2, .8)) / k
            x = 8 if cote < 0 else 192
            courbe = r.uniform(-.25, .25)
            mx, my = (x + cx) / 2, (y + cy) / 2 + courbe * abs(x - cx)
            pts = [((1 - t) ** 2 * x + 2 * (1 - t) * t * mx + t * t * cx, (1 - t) ** 2 * y + 2 * (1 - t) * t * my + t * t * cy) for t in (j / 24 for j in range(25))]
            acc = r.random() < .14
            out.append(trait(pts, ACC if acc else ENCRE, 1.8 if acc else 1.1))
            bouts[ACC if acc else ENCRE].append((x, y))
    return out + [points(bouts[ENCRE], 4.4, ENCRE), points(bouts[ACC], 5.4, ACC), disque(cx, cy, 11, ACC), disque(cx, cy, 4.4, FOND)]


def panache(r, d):
    """Nuage de points qui naît d'un coin et s'élargit en montant légèrement, son cœur en aplat d'accent et deux
    contours en tirets : dispersion atmosphérique, rejet, pollution."""
    x0, hc, monte = 8, r.uniform(116, 140), r.uniform(26, 48)
    r_s = r.uniform(.24, .34)
    axe = lambda x: hc - monte * (max(0.0, x - x0) / 184) ** (2 / 3)
    sig = lambda x: 2 + r_s * max(0.0, x - x0) ** .9
    c0 = lambda x: 1 / sig(x) ** 2
    parts = defaultdict(list)
    for _ in range(5000):
        x, y = r.uniform(x0, 194), r.uniform(6, 194)
        p = c0(x) / c0(x0 + 8) * math.exp(-(y - axe(x)) ** 2 / (2 * sig(x) ** 2)) * 12
        if r.random() < p:
            parts[1.4 if p < .3 else 2.2 if p < 1 else 3].append((x, y))
    out = [points(v, k, ENCRE) for k, v in sorted(parts.items())]
    for k, L in enumerate(sorted(r.sample((40, 70, 110, 170, 260), 3))):
        c, haut_, bas_ = c0(x0 + L), [], []
        for i in range(1, 121):
            x = x0 + 186 * i / 120
            if c0(x) <= c:
                break
            h = sig(x) * math.sqrt(2 * math.log(c0(x) / c))
            haut_.append((x, axe(x) - h))
            bas_.append((x, axe(x) + h))
        if len(haut_) < 3:
            continue
        contour = [(x0, axe(x0))] + haut_ + bas_[::-1]
        out.append(plein(contour, ACC) if k == 0 else f'<path d="{trace(contour)}Z" stroke="{ENCRE}" stroke-width="1.2" stroke-dasharray="3 2.6"/>')
    return out


def carreaux(r, d):
    """Grille de carrés dont la taille et la teinte croissent vers un coin : les grands pleins d'accent, les moyens à
    l'encre, les petits en contour : criticité, matrice des risques, fréquence et gravité, prévention."""
    m = r.choice((5, 6, 7))
    s = 184 / m
    coin = r.choice(((1, 1), (1, 0), (0, 1)))
    out, bruit = [], [[r.uniform(-.12, .12) for _ in range(m)] for _ in range(m)]
    for i in range(m):
        for j in range(m):
            u, v = (i if coin[0] else m - 1 - i) / (m - 1), (j if coin[1] else m - 1 - j) / (m - 1)
            t = max(0.0, min(1.0, (u + v) / 2 + bruit[i][j]))
            c = s * (.28 + .58 * t)
            x, y = 8 + i * s + (s - c) / 2, 8 + j * s + (s - c) / 2
            if t > .7:
                out.append(boite(x, y, c, c, ACC, None))
            elif t > .38:
                out.append(boite(x, y, c, c, ENCRE, None))
            else:
                out.append(boite(x, y, c, c, "none", ENCRE, 1.3))
    return out


# ---------- sciences exactes : physique et astronomie, Terre et climat, mathématiques, chimie générale ----------

def lignes_de_niveau(f, niveaux, m=56, x0=8, y0=8, x1=192, y1=192):
    """Lignes de niveau d'une fonction f(x, y) (carrés marchants), raccordées en polylignes : {niveau: [polylignes]}."""
    xs = [x0 + (x1 - x0) * i / m for i in range(m + 1)]
    ys = [y0 + (y1 - y0) * j / m for j in range(m + 1)]
    v = [[f(x, y) for x in xs] for y in ys]
    sortie = {}
    for c in niveaux:
        segs = []
        for j in range(m):
            for i in range(m):
                coins = [(xs[i], ys[j], v[j][i]), (xs[i + 1], ys[j], v[j][i + 1]), (xs[i + 1], ys[j + 1], v[j + 1][i + 1]), (xs[i], ys[j + 1], v[j + 1][i])]
                pts = []
                for k in range(4):
                    (ax, ay, a), (bx, by, b) = coins[k], coins[(k + 1) % 4]
                    if (a > c) != (b > c):
                        t = (c - a) / (b - a)
                        pts.append((round(ax + (bx - ax) * t, 2), round(ay + (by - ay) * t, 2)))
                if len(pts) == 2:
                    segs.append(tuple(pts))
                elif len(pts) == 4:
                    segs += [(pts[0], pts[1]), (pts[2], pts[3])]
        voisins = defaultdict(list)
        for k, (a, b) in enumerate(segs):
            voisins[a].append(k)
            voisins[b].append(k)
        vus, lignes = set(), []
        for k in range(len(segs)):
            if k in vus:
                continue
            vus.add(k)
            ligne = list(segs[k])
            for sens in (0, 1):
                while True:
                    bout = ligne[-1] if sens == 0 else ligne[0]
                    suite = next((q for q in voisins[bout] if q not in vus), None)
                    if suite is None:
                        break
                    vus.add(suite)
                    a, b = segs[suite]
                    autre = b if a == bout else a
                    if sens == 0:
                        ligne.append(autre)
                    else:
                        ligne.insert(0, autre)
            lignes.append(ligne)
        sortie[c] = lignes
    return sortie


# physique et astronomie

def interference(r, d):
    """Champ de points dont la taille suit l'interférence de deux sources : franges en hyperboles, la frange centrale
    à l'accent : ondes, optique, interférences, diffraction."""
    ecart, lam = r.uniform(26, 60), r.uniform(9, 15)
    bas = r.random() < .6
    s1, s2 = ((100 - ecart / 2, 204), (100 + ecart / 2, 204)) if bas else ((-4, 100 - ecart / 2), (-4, 100 + ecart / 2))
    classes = defaultdict(list)
    for x, y in semis_dans(lambda x, y: True, 4.6, 8, 8, 192, 192):
        dd = math.dist((x, y), s1) - math.dist((x, y), s2)
        i = math.cos(math.pi * dd / lam) ** 2
        t = round(.6 + 3.4 * i ** 1.6, 1)
        if t >= .9:
            classes[(ACC if abs(dd) < lam / 2 and i > .5 else ENCRE, t)].append((x, y))
    return [points(p, t, c) for (c, t), p in sorted(classes.items(), key=lambda k: k[0][1])]


def geodesiques(r, d):
    """Quadrillage que creusent une ou deux masses (lignes tirées vers elles), les masses à l'accent : relativité,
    gravitation, espace-temps, courbure."""
    masses_ = [(r.uniform(60, 140), r.uniform(60, 140), r.uniform(1600, 2600))]
    if r.random() < .4:
        masses_ = [(r.uniform(50, 90), r.uniform(70, 130), r.uniform(900, 1500)), (r.uniform(110, 150), r.uniform(70, 130), r.uniform(900, 1500))]

    def tire(x, y):
        dx = dy = 0.0
        fen = math.sin(math.pi * (x - 8) / 184) * math.sin(math.pi * (y - 8) / 184)
        for mx, my, k in masses_:
            ex, ey = mx - x, my - y
            f = min(k / (ex * ex + ey * ey + 260), .85) * fen
            dx, dy = dx + ex * f, dy + ey * f
        return x + dx, y + dy

    m = r.randint(12, 16)
    traits = []
    for i in range(m + 1):
        c = 8 + 184 * i / m
        traits.append(trace([tire(c, 8 + 184 * k / 80) for k in range(81)]))
        traits.append(trace([tire(8 + 184 * k / 80, c) for k in range(81)]))
    return ([f'<path d="{"".join(traits)}" stroke="{ENCRE}" stroke-width="1"/>']
            + [disque(mx, my, 3 + k / 260, ACC) for mx, my, k in masses_])


def ising(r, d):
    """Réseau de spins en domaines : cases pleines (haut) et vides (bas), quelques spins retournés, des cases de paroi
    à l'accent : physique statistique, transition de phase, magnétisme, modèle d'Ising."""
    n = r.choice((28, 32, 36))
    c = 184 / n
    modes = [(r.uniform(-.5, .5), r.uniform(-.5, .5), r.uniform(0, 6.3), r.uniform(.5, 1)) for _ in range(6)]
    champ = lambda i, j: sum(a * math.cos(kx * i + ky * j + p) for kx, ky, p, a in modes)
    seuil = r.uniform(-.4, .4)
    spin = [[(champ(i, j) > seuil) != (r.random() < .05) for j in range(n)] for i in range(n)]
    pleins, accents = [], []
    for i in range(n):
        for j in range(n):
            if not spin[i][j]:
                continue
            paroi = any(0 <= i + a < n and 0 <= j + b < n and not spin[i + a][j + b] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            (accents if paroi and r.random() < .22 else pleins).append((8 + i * c + c * .1, 8 + j * c + c * .1))
    vides = [(8 + (i + .5) * c, 8 + (j + .5) * c) for i in range(n) for j in range(n) if not spin[i][j]]
    return [points(vides, c * .22, DOUX), f'<path d="{carres(pleins, c * .8)}" fill="{ENCRE}"/>',
            f'<path d="{carres(accents, c * .8)}" fill="{ACC}"/>' if accents else ""]


def galaxie(r, d):
    """Spirale de points : bras logarithmiques, bulbe dense, quelques étoiles à l'accent, vue inclinée : astrophysique,
    astronomie, galaxies, étoiles."""
    bras, pas_ = r.choice((2, 2, 3, 4)), r.uniform(.22, .34)
    incl, rot = r.uniform(.62, 1), r.uniform(0, math.pi)
    pts = defaultdict(list)
    for _ in range(2200):
        if r.random() < .22:
            rr, a = abs(r.gauss(0, 12)), r.uniform(0, 2 * math.pi)
            t = 2.6
        else:
            u = r.random() ** .8
            rr = 8 + 88 * u
            a = 2 * math.pi * r.randrange(bras) / bras + math.log(rr / 8) / math.tan(pas_) + r.gauss(0, .2 + .25 * u)
            t = 2 if u < .5 else 1.5
        x, y = rr * math.cos(a), rr * math.sin(a) * incl
        x, y = 100 + x * math.cos(rot) - y * math.sin(rot), 100 + x * math.sin(rot) + y * math.cos(rot)
        if 8 < x < 192 and 8 < y < 192:
            pts[(ACC if r.random() < .025 else ENCRE, t)].append((x, y))
    out = [points(p, t * (1.9 if c == ACC else 1), c) for (c, t), p in sorted(pts.items(), key=lambda k: k[0][0] == ACC)]
    return out + [points([(100, 100)], 9, ENCRE)]


def cosmique(r, d):
    """Toile de filaments : des nœuds denses reliés à leurs voisins par des traînées de points, les plus gros nœuds à
    l'accent, un semis épars dans les vides : cosmologie, grandes structures, univers, matière noire."""
    noeuds = []
    for _ in range(400):
        if len(noeuds) >= r.randint(18, 26):
            break
        p = (r.uniform(14, 186), r.uniform(14, 186))
        if all(math.dist(p, q) > 26 for q in noeuds):
            noeuds.append(p)
    aretes = set()
    for i, p in enumerate(noeuds):
        proches = sorted(range(len(noeuds)), key=lambda j: math.dist(p, noeuds[j]))[1:r.randint(3, 4)]
        aretes |= {tuple(sorted((i, j))) for j in proches}
    degre = Counter(k for a in aretes for k in a)
    fil, amas, acc = [], [], []
    for i, j in aretes:
        (ax, ay), (bx, by) = noeuds[i], noeuds[j]
        for _ in range(int(math.dist(noeuds[i], noeuds[j]) * .9)):
            t = r.random()
            fil.append((ax + (bx - ax) * t + r.gauss(0, 2.4), ay + (by - ay) * t + r.gauss(0, 2.4)))
    gros = {k for k, _ in degre.most_common(3)}
    for k, (x, y) in enumerate(noeuds):
        cible = acc if k in gros else amas
        for _ in range(10 + 6 * degre[k]):
            cible.append((x + r.gauss(0, 3.4), y + r.gauss(0, 3.4)))
    vide = [(r.uniform(8, 192), r.uniform(8, 192)) for _ in range(140)]
    garde = lambda ps: [p for p in ps if 8 < p[0] < 192 and 8 < p[1] < 192]
    return [points(garde(vide), 1.1, DOUX), points(garde(fil), 1.5, ENCRE), points(garde(amas), 2.2, ENCRE), points(garde(acc), 2.6, ACC)]


# sciences de la Terre et climat

def plissement(r, d):
    """Couches plissées en bandes alternées (pleines, en trame, vides), une couche à l'accent, rejetées par une faille
    oblique : géologie, stratigraphie, tectonique, sédiments."""
    k = r.randint(11, 16)
    ep = 184 / k
    lam, amp, phi = r.uniform(110, 220), r.uniform(10, 26), r.uniform(0, 6.3)
    xf, pente, rejet = r.uniform(70, 130), r.uniform(-.5, .5), r.uniform(.6, 1.6) * ep
    ka = r.randrange(2, k - 2)
    pli = lambda x, i: 8 + i * ep + amp * math.sin(2 * math.pi * x / lam + phi) * (.5 + .5 * math.sin(math.pi * i / k))
    out, trame = [], []
    for i in range(-2, k + 2):
        sorte = ACC if i == ka else (ENCRE if i % 3 == 0 else DOUX if i % 3 == 1 else None)
        if sorte is None:
            continue
        for cote in (0, 1):
            ym = 8 + (i + .5) * ep
            xc = xf + pente * (ym - 100)
            xa, xb = (8, xc) if cote == 0 else (xc, 192)
            dec = rejet if cote else 0
            xs = [xa + (xb - xa) * q / 30 for q in range(31)]
            haut_ = [(x, pli(x, i) + dec) for x in xs]
            bas_ = [(x, pli(x, i + 1) + dec - ep * .12) for x in xs[::-1]]
            poly = [(x, min(192.0, max(8.0, y))) for x, y in haut_ + bas_]
            if sorte == DOUX:
                trame += [p for p in semis_dans(lambda x, y: xa < x < xb and pli(x, i) + dec < y < pli(x, i + 1) + dec - ep * .12, 3.6, xa, 8, xb, 192)]
            else:
                out.append(plein(poly, sorte))
    xa_, xb_ = xf + pente * (8 - 100), xf + pente * (192 - 100)
    return [points(trame, 1.5, ENCRE)] + out + [trait([(xa_, 8), (xb_, 192)], FOND, 4), trait([(xa_, 8), (xb_, 192)], ENCRE, 1.4)]


def sismogramme(r, d):
    """Traces superposées, calmes puis secouées par deux arrivées dont les temps s'alignent sur une hyperbole ; une
    trace à l'accent : sismologie, séismes, ondes sismiques, géophysique."""
    k = r.randint(13, 19)
    pas = 176 / k
    t0, v, x0 = r.uniform(20, 46), r.uniform(1.4, 2.4), r.uniform(20, 60)
    ka, out = r.randrange(k), []
    for i in range(k):
        y0 = 14 + i * pas
        dist = math.hypot(x0, (i - k / 2) * 9)
        tp, ts = t0 + dist / v, t0 + dist / v * 1.7
        pts = []
        for s in range(0, 231):
            x = 8 + s * .8
            bruit = r.gauss(0, .35)
            onde = 0.0
            for ta, a, f in ((tp, .5, .9), (ts, 1, .55)):
                if x > ta:
                    onde += a * math.exp(-(x - ta) / 14) * math.sin((x - ta) * f) * (1 - math.exp(-(x - ta) / 1.5))
            pts.append((x, y0 - (bruit + onde * pas * .9)))
        out.append(trait(pts, ACC if i == ka else ENCRE, 1.5 if i == ka else .8))
    return out


def gyres(r, d):
    """Cellules de circulation côte à côte, tournant en sens contraires : lignes de courant fermées en tirets, le cœur
    d'une cellule à l'accent : océanographie, courants marins, circulation, tourbillons."""
    a, b = r.choice(((2, 1), (2, 2), (3, 2), (1, 2), (3, 1)))
    ph, amp = r.uniform(0, 6.3), r.uniform(.15, .35)
    psi = lambda x, y: (math.sin(a * math.pi * (x - 8) / 184) * math.sin(b * math.pi * (y - 8) / 184)
                        + amp * math.sin(math.pi * (x - 8) / 92 + ph) * math.sin(math.pi * (y - 8) / 184))
    niveaux = [s_ * f for s_ in (-1, 1) for f in (.1, .25, .4, .55, .7, .85)]
    lignes = lignes_de_niveau(psi, niveaux, 64)
    ca = r.choice((-.85, .85))
    out = []
    for c, ls in lignes.items():
        acc = c == ca
        for l_ in ls:
            if len(l_) > 3:
                out.append(trait(l_, ACC if acc else ENCRE, 2.4 if acc else 1.2, "" if acc else ' stroke-dasharray="5 3.4"'))
    return out


def isobares(r, d):
    """Lignes de niveau serrées d'un champ à plusieurs creux et bosses ; les plus serrées autour du creux le plus
    profond à l'accent, les centres marqués : météorologie, pression, dépressions, anticyclones, vent."""
    k = r.randint(4, 7)
    centres = [(r.uniform(-10, 210), r.uniform(-10, 210), r.choice((-1, 1)) * r.uniform(.6, 1.3), r.uniform(28, 60)) for _ in range(k)]
    gx, gy = r.uniform(-.004, .004), r.uniform(-.004, .004)
    f = lambda x, y: gx * x + gy * y + sum(s * math.exp(-((x - a) ** 2 + (y - b) ** 2) / (2 * w * w)) for a, b, s, w in centres)
    creux = min(centres, key=lambda c: c[2])
    lo, hi = min(c[2] for c in centres) - .3, max(c[2] for c in centres) + .3
    niveaux = [lo + (hi - lo) * q / 22 for q in range(1, 22)]
    lignes = lignes_de_niveau(f, niveaux)
    out = []
    for c, ls in lignes.items():
        for l_ in ls:
            if len(l_) < 3:
                continue
            pres = min(math.dist(p, creux[:2]) for p in l_[::3])
            acc = c < creux[2] * .45 and pres < 70
            out.append(trait(l_, ACC if acc else ENCRE, 1.8 if acc else 1))
    marques_ = [(a, b) for a, b, s, w in centres if 14 < a < 186 and 14 < b < 186]
    return out + [disque(a, b, 3.4, FOND, ENCRE, 1.4) for a, b in marques_]


def rechauffement(r, d):
    """Bandes verticales d'une série qui se réchauffe : froides à l'encre, tièdes vides, chaudes à l'accent, la moitié
    ou toute la largeur selon l'écart : climat, réchauffement climatique, températures, anomalies."""
    k = r.choice((48, 60, 72))
    l = 184 / k
    serie, x_ = [], 0.0
    pente, ar = r.uniform(.8, 1.6), r.uniform(.4, .7)
    for i in range(k):
        x_ = ar * x_ + r.gauss(0, .55)
        serie.append(pente * (i / k) ** 2.2 * 2 - .5 + x_)
    q = sorted(serie)
    seuils = [q[int(k * f)] for f in (.15, .35, .62, .82)]
    pleins = {ENCRE: [], ACC: []}
    for i, v in enumerate(serie):
        x = 8 + i * l
        if v < seuils[0]:
            pleins[ENCRE].append(f"M{n(x)} 8h{n(l)}V192h{n(-l)}Z")
        elif v < seuils[1]:
            pleins[ENCRE].append(f"M{n(x + l / 4)} 8h{n(l / 2)}V192h{n(-l / 2)}Z")
        elif v < seuils[2]:
            continue
        elif v < seuils[3]:
            pleins[ACC].append(f"M{n(x + l / 4)} 8h{n(l / 2)}V192h{n(-l / 2)}Z")
        else:
            pleins[ACC].append(f"M{n(x)} 8h{n(l)}V192h{n(-l)}Z")
    return [f'<path d="{"".join(v)}" fill="{c}"/>' for c, v in pleins.items() if v]


# mathématiques

def isoclines(r, d):
    """Champ de pentes en petits tirets et quelques courbes intégrales qui le suivent, une à l'accent : équations
    différentielles, analyse, intégration."""
    choix = r.randrange(4)
    a = r.uniform(.6, 1.4)
    fs = (lambda x, y: math.sin(a * x) - .6 * y, lambda x, y: x * x - y * a, lambda x, y: math.sin(x * y * a * .6),
          lambda x, y: y * (1 - y * .45) - .4 * math.cos(a * x * 1.5))
    f = fs[choix]
    U = lambda px: (px - 100) / 46
    P = lambda u: 100 + 46 * u
    m, out = r.choice((14, 16, 18)), []
    tirets = []
    for i in range(m):
        for j in range(m):
            x, y = 8 + 184 * (i + .5) / m, 8 + 184 * (j + .5) / m
            s = f(U(x), -U(y))
            ang = math.atan(s)
            dx, dy = 184 / m * .34 * math.cos(ang), -184 / m * .34 * math.sin(ang)
            tirets.append(f"M{n(x - dx)} {n(y - dy)}L{n(x + dx)} {n(y + dy)}")
    out.append(f'<path d="{"".join(tirets)}" stroke="{DOUX}" stroke-width="1.4"/>')
    k = r.randint(4, 7)
    for q in range(k):
        x, y = -2, -1.8 + 3.6 * (q + .5) / k
        pts = [(P(x), P(-y))]
        h = .02
        for _ in range(240):
            k1 = f(x, y)
            k2 = f(x + h / 2, y + h * k1 / 2)
            k3 = f(x + h / 2, y + h * k2 / 2)
            k4 = f(x + h, y + h * k3)
            x, y = x + h, y + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
            if abs(y) > 2.2:
                break
            pts.append((P(x), P(-y)))
        out.append(f'<path d="{morceaux(pts)}" stroke="{ACC if q == k // 2 else ENCRE}" stroke-width="{2.4 if q == k // 2 else 1.4}"/>')
    return out


def attracteur(r, d):
    """Nuage d'un attracteur étrange (de Jong ou Clifford), points de plus en plus gros là où l'orbite repasse, les plus
    denses à l'accent : systèmes dynamiques, chaos, itérations."""
    jeux = (("j", 1.4, -2.3, 2.4, -2.1), ("j", 2.01, -2.53, 1.61, -.33), ("j", -2.7, -.09, -.86, -2.2), ("j", -.827, -1.637, 1.659, -.943),
            ("c", -1.4, 1.6, 1, .7), ("c", 1.7, 1.7, .06, 1.2), ("c", 1.5, -1.8, 1.6, .9), ("c", -1.7, 1.3, -.1, -1.2))
    sorte, a, b, c, e = r.choice(jeux)
    a, b = a + r.uniform(-.03, .03), b + r.uniform(-.03, .03)
    x = y = .1
    g, m = Counter(), 64
    pts = []
    for i in range(30000):
        if sorte == "j":
            x, y = math.sin(a * y) - math.cos(b * x), math.sin(c * x) - math.cos(e * y)
        else:
            x, y = math.sin(a * y) + c * math.cos(a * x), math.sin(b * x) + e * math.cos(b * y)
        if i > 100:
            pts.append((x, y))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    s = 176 / max(x1 - x0, y1 - y0)
    ox, oy = 100 - s * (x0 + x1) / 2, 100 - s * (y0 + y1) / 2
    for px, py in pts:
        g[(int((px * s + ox - 8) / 184 * m), int((py * s + oy - 8) / 184 * m))] += 1
    haut = max(g.values())
    classes = defaultdict(list)
    for (i, j), k in g.items():
        t = math.log(1 + k) / math.log(1 + haut)
        diam = round(.8 + 2.8 * t, 1)
        classes[(ACC if t > .82 else ENCRE, diam)].append((8 + (i + .5) * 184 / m, 8 + (j + .5) * 184 / m))
    return [points(p, t, col) for (col, t), p in sorted(classes.items(), key=lambda k: k[0][1])]


def modulo(r, d):
    """Table de multiplication sur un cercle : chaque point relié à son multiple modulo n, les cordes dessinant une
    enveloppe (cardioïde, néphroïde…), une famille de cordes à l'accent : algèbre, arithmétique modulaire, groupes."""
    n_ = r.choice((120, 144, 160, 180))
    k = r.choice((2, 3, 4, 5, 7, 9, 34, 51, 61))
    R = 86
    P = lambda i: (100 + R * math.cos(2 * math.pi * i / n_ - math.pi / 2), 100 + R * math.sin(2 * math.pi * i / n_ - math.pi / 2))
    pas_acc = r.choice((6, 8, 10, 12))
    cordes, accents = [], []
    for i in range(n_):
        a, b = P(i), P(i * k % n_)
        (accents if i % pas_acc == 0 else cordes).append(f"M{n(a[0])} {n(a[1])}L{n(b[0])} {n(b[1])}")
    return [cercle(100, 100, R, ENCRE, 1.2), f'<path d="{"".join(cordes)}" stroke="{ENCRE}" stroke-width="0.55"/>',
            f'<path d="{"".join(accents)}" stroke="{ACC}" stroke-width="1.3"/>', points([P(i) for i in range(0, n_, 2)], 1.8, ENCRE)]


def galton(r, d):
    """Planche de Galton : clous en quinconce, billes empilées en cloche dans les cases, le chemin d'une bille et
    sa case à l'accent : probabilités, loi binomiale, hasard, statistique."""
    rangs = r.randint(9, 12)
    pas = 150 / (rangs + 1)
    top, haut_clous = 14, rangs * pas * .52
    clous = []
    for i in range(rangs):
        for j in range(i + 1):
            clous.append((100 + (j - i / 2) * pas, top + 10 + i * haut_clous / rangs))
    yb = top + 10 + haut_clous + 6
    billes = Counter()
    chemin_, case_a = None, None
    for b in range(r.randint(160, 260)):
        pos, chemin = 0, [(100, top)]
        for i in range(rangs):
            pos += r.random() < .5
            chemin.append((100 + (pos - (i + 1) / 2) * pas, top + 10 + (i + .5) * haut_clous / rangs))
        billes[pos] += 1
        if b == 0:
            chemin_, case_a = chemin, pos
    d_b = min(5.2, pas * .42, (190 - yb - 4) / math.ceil(max(billes.values()) / 2) / 1.05)
    tas, acc = [], []
    for pos, nb in billes.items():
        x = 100 + (pos - rangs / 2) * pas
        for q in range(nb):
            col, lig = q % 2, q // 2
            p = (x + (col - .5) * d_b * 1.05, 190 - lig * d_b * 1.05)
            (acc if pos == case_a and q == nb - 1 else tas).append(p)
    cloisons = "".join(f"M{n(100 + (p_ - rangs / 2 - .5) * pas)} {n(yb)}V192" for p_ in range(rangs + 2))
    return [points(clous, 2.4, ENCRE), f'<path d="{cloisons}" stroke="{DOUX}" stroke-width="0.9"/>',
            trait(chemin_, ACC, 1.6), points(tas, d_b, ENCRE), points(acc, d_b * 1.2, ACC)]


def entrelacs(r, d):
    """Nœud torique en ruban épais : le brin repasse dessus et dessous, les passages hauts à l'accent : topologie,
    nœuds, géométrie, invariants."""
    p, q = r.choice(((2, 3), (2, 5), (3, 4), (3, 5), (2, 7), (3, 7), (4, 5)))
    R, rho = r.uniform(50, 58), r.uniform(22, 30)
    rot = r.uniform(0, math.pi)
    seg = []
    N = 720
    prec = None
    for i in range(N + 1):
        t = 2 * math.pi * i / N
        rr = R + rho * math.cos(q * t)
        x, y, z = rr * math.cos(p * t), rr * math.sin(p * t), math.sin(q * t)
        x, y = 100 + x * math.cos(rot) - y * math.sin(rot), 100 + x * math.sin(rot) + y * math.cos(rot)
        if prec:
            seg.append((prec[2] + z, prec[:2], (x, y)))
        prec = (x, y, z)
    couches = defaultdict(list)
    for z, a, b in seg:
        couches[min(9, int((z + 2) / 4 * 10))].append(f"M{n(a[0])} {n(a[1])}L{n(b[0])} {n(b[1])}")
    out = []
    for k in sorted(couches):
        chemin = "".join(couches[k])
        out += [f'<path d="{chemin}" stroke="{FOND}" stroke-width="9" stroke-linecap="butt"/>',
                f'<path d="{chemin}" stroke="{ACC if k >= 8 else ENCRE}" stroke-width="4"/>']
    return out


def ulam(r, d):
    """Spirale d'Ulam : les entiers rangés en spirale carrée (semis clair), les nombres premiers en points ; ceux du
    polynôme d'Euler n² + n + 41 forment une diagonale à l'accent : théorie des nombres, nombres premiers."""
    m = r.choice((41, 45, 49, 53))
    c = 184 / m
    limite = 41 + m * m + 4
    crible = bytearray([1]) * (limite + 1)
    crible[0] = crible[1] = 0
    for i in range(2, int(limite ** .5) + 1):
        if crible[i]:
            crible[i * i::i] = bytearray(len(crible[i * i::i]))
    euler = {q * q + q + 41 for q in range(0, 200)}
    x = y = m // 2
    dx, dy, longueur, k, tour = 1, 0, 1, 41, 0
    prem, acc, tous = [], [], []
    pos = lambda i, j: (8 + (i + .5) * c, 8 + (j + .5) * c)
    while 0 <= x < m and 0 <= y < m:
        for _ in range(longueur):
            if 0 <= x < m and 0 <= y < m:
                p = pos(x, y)
                (acc if k in euler and crible[k] else prem if crible[k] else tous).append(p)
            x, y, k = x + dx, y + dy, k + 1
        dx, dy = -dy, dx
        tour += 1
        if tour % 2 == 0:
            longueur += 1
    return [points(tous, c * .2, DOUX), points(prem, c * .62, ENCRE), points(acc, c * .8, ACC)]


# chimie générale

def raies(r, d):
    """Bandes de raies : chaque bande une série de traits qui se resserrent vers une limite, d'intensités diverses,
    quelques raies à l'accent : spectroscopie, spectres, atomes, émission et absorption."""
    k = r.randint(6, 10)
    h = 176 / k
    out = []
    for j in range(k):
        y0 = 12 + j * h
        lim = r.uniform(120, 186)
        C = r.uniform(70, 150)
        xs = [(lim - C / (q * q) * 4, r.uniform(.3, 1)) for q in range(2, 18)]
        xs += [(r.uniform(10, 190), r.uniform(.15, .6)) for _ in range(r.randint(2, 6))]
        tr = {ENCRE: [], ACC: []}
        for x, i in xs:
            if 9 < x < 191:
                w = .5 + 2.4 * i
                tr[ACC if r.random() < .06 else ENCRE].append((x, w))
        for col, l_ in tr.items():
            for x, w in l_:
                out.append(f'<path d="M{n(x)} {n(y0 + h * .12)}V{n(y0 + h * .88)}" stroke="{col}" stroke-width="{n(w, 2)}" stroke-linecap="butt"/>')
    return out


def electrode(r, d):
    """Une paroi épaisse et, contre elle, une couche serrée de points d'accent ; plus loin, les deux couleurs se
    mêlent à mesure qu'on s'en éloigne : électrochimie, double couche, électrodes, ions, piles."""
    lam = r.uniform(18, 40)
    gauche = r.random() < .7
    classes = defaultdict(list)
    for x, y in semis_dans(lambda x, y: True, 6.2, 24, 8, 192, 192):
        x, y = x + r.uniform(-1.6, 1.6), y + r.uniform(-1.6, 1.6)
        dist = x - 22
        p = .5 + .48 * math.exp(-dist / lam)
        dens = 1 if r.random() < .7 + .3 * math.exp(-dist / lam) else 0
        if not dens:
            continue
        col = ACC if r.random() < p else ENCRE
        classes[(col, round(1.8 + 1.6 * math.exp(-dist / lam), 1))].append((x, y))
    out = [points(p, t, c) for (c, t), p in classes.items()]
    out.append(boite(8, 8, 9, 184, ENCRE, None))
    out.append(points([(21.5, y) for y in range(12, 192, 5)], 3.6, ACC))
    if not gauche:
        out = ['<g transform="translate(200 0) scale(-1 1)">'] + out + ["</g>"]
    return out


def orbitales(r, d):
    """Nuage de points tiré d'une densité orbitale (lobes, nœuds, anneaux), le signe de la fonction donnant la
    couleur : chimie quantique, orbitales, liaisons, mécanique quantique."""
    choix = r.randrange(5)
    a0 = r.uniform(8, 11)

    def psi(x, y):
        rr = math.hypot(x, y) / a0 + 1e-9
        c, s = x / (rr * a0), y / (rr * a0)
        if choix == 0:
            return rr * c * math.exp(-rr / 2)
        if choix == 1:
            return rr * rr * 2 * s * c * math.exp(-rr / 3)
        if choix == 2:
            return rr * rr * (3 * s * s - 1) * math.exp(-rr / 3)
        if choix == 3:
            return (6 - rr) * rr * c * math.exp(-rr / 3)
        return (27 - 18 * rr + 2 * rr * rr) * math.exp(-rr / 3) / 10

    rot = r.uniform(0, math.pi)
    echant = [psi(r.uniform(-92, 92), r.uniform(-92, 92)) ** 2 for _ in range(400)]
    pmax = max(echant) * 1.3
    plus, moins = [], []
    while len(plus) + len(moins) < 2400:
        x, y = r.uniform(-92, 92), r.uniform(-92, 92)
        v = psi(x, y)
        if r.random() * pmax < v * v:
            X = 100 + x * math.cos(rot) - y * math.sin(rot)
            Y = 100 + x * math.sin(rot) + y * math.cos(rot)
            if 8 < X < 192 and 8 < Y < 192:
                (plus if v > 0 else moins).append((X, Y))
    return [points(plus, 1.8, ENCRE), points(moins, 1.8, ACC), points([(100, 100)], 4, ENCRE)]


def chromato(r, d):
    """Pistes superposées de pics étroits, dont certains reviennent au même temps d'une piste à l'autre ; ceux d'un
    même composé pleins d'accent : chimie analytique, chromatographie, séparation, dosage."""
    k = r.randint(6, 9)
    pas = 160 / k
    composes = [(r.uniform(.06, .94), r.uniform(.008, .02)) for _ in range(r.randint(7, 11))]
    ca = r.randrange(len(composes))
    X = lambda t: 8 + 184 * t
    out = []
    for j in range(k):
        y0 = 30 + (j + 1) * pas
        presents = [(t, w, r.uniform(.25, 1) if r.random() < .75 else 0) for t, w in composes]
        f = lambda t: sum(h * math.exp(-((t - t0) / w) ** 2) for t0, w, h in presents)
        ts = [q / 160 for q in range(161)]
        pts = [(X(t), y0 - pas * 1.6 * f(t)) for t in ts]
        out += [plein([(X(0), y0)] + pts + [(X(1), y0)], FOND), trait(pts, ENCRE, 1.2)]
        t0, w, h = composes[ca][0], composes[ca][1], presents[ca][2]
        if h:
            pic = [(X(t), y0 - pas * 1.6 * f(t)) for t in ts if abs(t - t0) < 2.4 * w]
            out.append(plein([(pic[0][0], y0)] + pic + [(pic[-1][0], y0)], ACC))
    return out


# ---------- sciences exactes, suite : outils ----------

def champ_lisse(r, k=7, fmin=.012, fmax=.04):
    """Fonction douce f(x, y) à peu près dans [-1, 1] : somme de quelques ondes planes de fréquences tirées."""
    modes = []
    for _ in range(k):
        f, a = r.uniform(fmin, fmax), r.uniform(0, 2 * math.pi)
        modes.append((f * math.cos(a), f * math.sin(a), r.uniform(0, 2 * math.pi), r.uniform(.5, 1)))
    norme = sum(m[3] for m in modes) * .55
    return lambda x, y: sum(am * math.sin(fx * x + fy * y + ph) for fx, fy, ph, am in modes) / norme


def coupe_poly(poly, a, b, c, etiquette):
    """Le côté a·x + b·y ≤ c d'un polygone [(x, y, étiquette du côté qui part de ce sommet)]."""
    out, m = [], len(poly)
    for k in range(m):
        x1, y1, l1 = poly[k]
        x2, y2, _ = poly[(k + 1) % m]
        d1, d2 = a * x1 + b * y1 - c, a * x2 + b * y2 - c
        if d1 <= 0:
            out.append((x1, y1, l1))
            if d2 > 0:
                t = d1 / (d1 - d2)
                out.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, etiquette))
        elif d2 <= 0:
            t = d1 / (d1 - d2)
            out.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, l1))
    return out


def voronoi(sites, x0=8, y0=8, x1=192, y1=192):
    """Cellules de Voronoï des sites dans le rectangle : [(polygone [(x, y)], voisins {indices})]."""
    cellules = []
    for i, (sx, sy) in enumerate(sites):
        poly = [(x0, y0, None), (x1, y0, None), (x1, y1, None), (x0, y1, None)]
        for j in sorted(range(len(sites)), key=lambda j: (sites[j][0] - sx) ** 2 + (sites[j][1] - sy) ** 2)[1:]:
            tx, ty = sites[j]
            dist = math.hypot(tx - sx, ty - sy)
            if dist > 2 * max(math.hypot(px - sx, py - sy) for px, py, _ in poly) + 1:
                break
            poly = coupe_poly(poly, tx - sx, ty - sy, (tx * tx + ty * ty - sx * sx - sy * sy) / 2, j)
            if len(poly) < 3:
                break
        cellules.append(([(x, y) for x, y, _ in poly], {l for _, _, l in poly if l is not None}))
    return cellules


def retrecit(poly, f):
    cx, cy = sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly)
    return [(cx + (x - cx) * f, cy + (y - cy) * f) for x, y in poly]


# physique et astronomie (suite)

def dipole(r, d):
    """Lignes de champ qui jaillissent de charges et plongent dans d'autres, deux lignes et les charges positives à
    l'accent : électromagnétisme, électrostatique, champ électrique, charges."""
    k = r.choice((2, 2, 3, 4))
    charges = []
    for _ in range(300):
        if len(charges) == k:
            break
        p = (r.uniform(48, 152), r.uniform(48, 152))
        if all(math.dist(p, q[:2]) > 46 for q in charges):
            charges.append((p[0], p[1], 1 if len(charges) % 2 == 0 else -1))

    def champ(x, y):
        ex = ey = 0.0
        for cx, cy, q in charges:
            dx, dy = x - cx, y - cy
            r3 = (dx * dx + dy * dy) ** 1.5 + 1e-9
            ex, ey = ex + q * dx / r3, ey + q * dy / r3
        return ex, ey

    lignes, m = [], r.randint(14, 22)
    for cx, cy, q in charges:
        if q < 0:
            continue
        for i in range(m):
            a = 2 * math.pi * (i + .5) / m
            x, y = cx + 4 * math.cos(a), cy + 4 * math.sin(a)
            pts = [(x, y)]
            for s in range(380):
                ex, ey = champ(x, y)
                nn = math.hypot(ex, ey) or 1
                x, y = x + 1.6 * ex / nn, y + 1.6 * ey / nn
                if s % 3 == 0:
                    pts.append((x, y))
                if not (0 < x < 200 and 0 < y < 200) or any(q2 < 0 and math.hypot(x - c2x, y - c2y) < 4 for c2x, c2y, q2 in charges):
                    pts.append((x, y))
                    break
            lignes.append(pts)
    acc = set(r.sample(range(len(lignes)), 2))
    out = [f'<path d="{morceaux(l_)}" stroke="{ACC if i in acc else ENCRE}" stroke-width="{1.8 if i in acc else 1}"/>' for i, l_ in enumerate(lignes)]
    return out + [disque(cx, cy, 5.4, ACC if q > 0 else FOND, None if q > 0 else ENCRE, 2) for cx, cy, q in charges]


def limaille(r, d):
    """Semis de tirets courts alignés sur le champ de deux pôles, comme de la limaille ; près des pôles, à l'accent :
    magnétisme, champ magnétique, aimants, induction."""
    a, l = r.uniform(0, math.pi), r.uniform(20, 36)
    p1 = (100 + l * math.cos(a), 100 + l * math.sin(a))
    p2 = (100 - l * math.cos(a), 100 - l * math.sin(a))

    def champ(x, y):
        bx = by = 0.0
        for (cx, cy), q in ((p1, 1), (p2, -1)):
            dx, dy = x - cx, y - cy
            r3 = (dx * dx + dy * dy) ** 1.5 + 1e-9
            bx, by = bx + q * dx / r3, by + q * dy / r3
        return bx, by

    traits = {ENCRE: [], ACC: []}
    for x, y in semis_dans(lambda x, y: min(math.dist((x, y), p1), math.dist((x, y), p2)) > 7, 6.6, 8, 8, 192, 192):
        x, y = x + r.uniform(-1.8, 1.8), y + r.uniform(-1.8, 1.8)
        bx, by = champ(x, y)
        nn = math.hypot(bx, by) or 1
        ln = 2.6 + r.uniform(-.4, .6)
        dx, dy = ln * bx / nn, ln * by / nn
        pres = min(math.dist((x, y), p1), math.dist((x, y), p2)) < 22
        traits[ACC if pres else ENCRE].append(f"M{n(x - dx)} {n(y - dy)}L{n(x + dx)} {n(y + dy)}")
    return [f'<path d="{"".join(v)}" stroke="{c}" stroke-width="1.4"/>' for c, v in traits.items() if v]


def kepler(r, d):
    """Ellipses de foyer commun, l'une reprise en rosace par la précession, des points sur chaque orbite, le foyer
    et une orbite à l'accent : mécanique céleste, orbites, gravitation, Kepler, systèmes planétaires."""
    fx, fy = 100 + r.uniform(-16, 16), 100 + r.uniform(-16, 16)
    k = r.randint(5, 8)
    orbites = []
    for i in range(k):
        a_ = 14 + 82 * (i + .5) / k * r.uniform(.9, 1.1)
        e = r.uniform(.05, .55)
        om = r.uniform(0, 2 * math.pi)
        orbites.append((a_, e, om))
    ia, ir = r.randrange(k), r.randrange(k)

    def courbe_(a_, e, om):
        return [(fx + a_ * (1 - e * e) / (1 + e * math.cos(t - om)) * math.cos(t), fy + a_ * (1 - e * e) / (1 + e * math.cos(t - om)) * math.sin(t))
                for t in (2 * math.pi * q / 90 for q in range(91))]

    out = []
    a_, e, om = orbites[ir]
    for q in range(1, r.randint(6, 10)):
        out.append(f'<path d="{morceaux(courbe_(a_, e, om + q * .32))}" stroke="{DOUX}" stroke-width="0.7"/>')
    planetes = []
    for i, (a_, e, om) in enumerate(orbites):
        out.append(f'<path d="{morceaux(courbe_(a_, e, om))}" stroke="{ACC if i == ia else ENCRE}" stroke-width="{1.8 if i == ia else 1.1}"/>')
        t = r.uniform(0, 2 * math.pi)
        rr = a_ * (1 - e * e) / (1 + e * math.cos(t - om))
        planetes.append((fx + rr * math.cos(t), fy + rr * math.sin(t)))
    return out + [points([p for p in planetes if 8 < p[0] < 192 and 8 < p[1] < 192], 5, ENCRE), points([(fx, fy)], 10, ACC)]


def lissajous(r, d):
    """Table de figures de Lissajous, les rapports de fréquences croissant en ligne et en colonne, une figure à
    l'accent : oscillations, vibrations, résonance, signaux, mécanique ondulatoire."""
    m = r.choice((3, 4, 4, 5))
    s, dph = 184 / m, r.choice((math.pi / 2, math.pi / 4, math.pi / 3))
    ia = (r.randrange(m), r.randrange(m))
    out = []
    for i in range(m):
        for j in range(m):
            a_, b_ = i + 1, j + 1
            cx, cy, h = 8 + (i + .5) * s, 8 + (j + .5) * s, s * .4
            pts = [(cx + h * math.sin(a_ * t + dph), cy + h * math.sin(b_ * t)) for t in (2 * math.pi * q / 150 for q in range(151))]
            acc = (i, j) == ia
            out.append(trait(pts, ACC if acc else ENCRE, 1.7 if acc else .9))
    return out


def chladni(r, d):
    """Figure de Chladni : du sable rassemblé le long des lignes nodales d'une plaque qui vibre, quelques grains à
    l'accent : acoustique, vibrations, modes propres, résonance, ondes stationnaires."""
    a_, b_ = r.sample(range(1, 8), 2)
    sg = r.choice((-1, 1))
    f = lambda u, v: math.cos(a_ * math.pi * u) * math.cos(b_ * math.pi * v) + sg * math.cos(b_ * math.pi * u) * math.cos(a_ * math.pi * v)
    grains = {ENCRE: [], ACC: []}
    total = 0
    for _ in range(26000):
        if total >= 2400:
            break
        x, y = r.uniform(8, 192), r.uniform(8, 192)
        v = f((x - 8) / 184, (y - 8) / 184)
        if r.random() < math.exp(-(v / .09) ** 2):
            grains[ACC if r.random() < .05 else ENCRE].append((x, y))
            total += 1
    return [points(grains[ENCRE], 1.7, ENCRE), points(grains[ACC], 2.4, ACC)]


def collision(r, d):
    """Traces en pointillés qui partent d'un même point : spirales qui se resserrent, droites en tirets, une trace à
    l'accent : physique des particules, chambre à bulles, collisions, accélérateurs."""
    vx, vy = 100 + r.uniform(-30, 30), 100 + r.uniform(-30, 30)
    out = []
    k = r.randint(12, 18)
    ka = r.randrange(k)
    for i in range(k):
        a = 2 * math.pi * (i + r.uniform(-.3, .3)) / k
        neutre = r.random() < .2
        courb = 0 if neutre else r.choice((-1, 1)) * r.uniform(.004, .03)
        g = r.uniform(1.004, 1.02)
        x, y, pts = vx, vy, [(vx, vy)]
        for s in range(260):
            a += courb
            courb *= g
            x, y = x + 2 * math.cos(a), y + 2 * math.sin(a)
            if s % 2 == 0:
                pts.append((x, y))
            if not (6 < x < 194 and 6 < y < 194) or abs(courb) > .5:
                break
        acc = i == ka
        extra = ' stroke-dasharray="5 4"' if neutre else ' stroke-dasharray="0 3.2"'
        out.append(f'<path d="{morceaux(pts)}" stroke="{ACC if acc else ENCRE}" stroke-width="{2.6 if acc else 1.9}"{extra}/>')
    return out + [points([(vx, vy)], 6, ENCRE)]


def brillouin(r, d):
    """Zones de Brillouin : un semis de points dont la présence alterne d'une zone à la suivante autour d'une zone
    centrale à l'accent : physique du solide, cristaux, bandes d'énergie, réseau réciproque."""
    a_ = r.uniform(44, 60)
    hexa = r.random() < .45
    rot = r.uniform(0, math.pi / 2)
    G = []
    for i in range(-9, 10):
        for j in range(-9, 10):
            if i == j == 0:
                continue
            x, y = (a_ * (i + .5 * j), a_ * j * math.sqrt(3) / 2) if hexa else (a_ * i, a_ * j)
            x, y = x * math.cos(rot) - y * math.sin(rot), x * math.sin(rot) + y * math.cos(rot)
            if math.hypot(x, y) < 300:
                G.append((x, y, x * x + y * y))
    classes = defaultdict(list)
    for px, py in semis_dans(lambda x, y: True, 3.4, 8, 8, 192, 192):
        x, y = px - 100, py - 100
        zone = 1 + sum(1 for gx, gy, g2 in G if g2 < 2 * (x * gx + y * gy))
        if zone == 1:
            classes[(ACC, 2.2)].append((px, py))
        elif zone > 9:
            continue
        elif zone % 2 == 0:
            classes[(ENCRE, 2.2)].append((px, py))
        else:
            classes[(DOUX, 1)].append((px, py))
    return [points(p, t, c) for (c, t), p in classes.items()]


def chirikov(r, d):
    """Section de Poincaré de l'application standard : courbes invariantes, îlots et mer chaotique en points, quelques
    orbites à l'accent : plasmas, accélérateurs, chaos hamiltonien, mécanique céleste."""
    K = r.choice((.45, .6, .75, .9))
    m, bins = 96, {}
    nb = r.randint(36, 50)
    acc = set(r.sample(range(nb), 4))
    for o in range(nb):
        th, p = r.uniform(0, 2 * math.pi), r.uniform(0, 2 * math.pi)
        for _ in range(300):
            p = (p + K * math.sin(th)) % (2 * math.pi)
            th = (th + p) % (2 * math.pi)
            cle = (int(th / (2 * math.pi) * m), int(p / (2 * math.pi) * m))
            if cle not in bins or o in acc:
                bins[cle] = o in acc
    pts = {True: [], False: []}
    for (i, j), a in bins.items():
        pts[a].append((8 + (i + .5) * 184 / m, 8 + (j + .5) * 184 / m))
    return [points(pts[False], 1.5, ENCRE), points(pts[True], 2.2, ACC)]


def hertzsprung(r, d):
    """Nuage d'étoiles en bande diagonale, un amas à part en haut et une poignée en bas, les plus chaudes à l'accent :
    étoiles, astrophysique stellaire, évolution stellaire, diagramme de Hertzsprung-Russell."""
    classes = defaultdict(list)
    courbe_ = lambda s: (22 + 156 * s, 26 + 150 * (s + .18 * math.sin(math.pi * s * 1.4)) / 1.1)
    for _ in range(r.randint(700, 950)):
        s = r.random() ** .7
        x, y = courbe_(s)
        e = r.gauss(0, 4 + 5 * s)
        x, y = x + e * .6, y - e
        diam = round(4.6 - 3.2 * s + r.uniform(-.4, .4), 1)
        classes[(ACC if s < .12 else ENCRE, max(1.2, diam))].append((x, y))
    gx, gy = r.uniform(130, 165), r.uniform(48, 74)
    for _ in range(r.randint(90, 140)):
        classes[(ENCRE, 3)].append((gx + r.gauss(0, 13), gy + r.gauss(0, 9)))
    for _ in range(r.randint(18, 30)):
        classes[(ENCRE, 4.2)].append((r.uniform(40, 185), r.uniform(18, 32)))
    for _ in range(r.randint(30, 60)):
        classes[(ENCRE, 1.3)].append((r.gauss(62, 9), r.gauss(168, 6)))
    garde = lambda ps: [p for p in ps if 8 < p[0] < 192 and 8 < p[1] < 192]
    return [points(garde(p), t, c) for (c, t), p in sorted(classes.items(), key=lambda k: -k[0][1])]


def circumpolaire(r, d):
    """Arcs concentriques d'égale ouverture autour d'un pôle, d'épaisseurs diverses, quelques arcs et le pôle à
    l'accent : astronomie, rotation de la Terre, ciel nocturne, observation."""
    px, py = r.uniform(30, 170), r.uniform(20, 150)
    ouverture = math.radians(r.uniform(28, 70))
    out, k = [], r.randint(60, 95)
    acc = set(r.sample(range(k), 3))
    for i in range(k):
        rr, a0 = r.uniform(6, 250), r.uniform(0, 2 * math.pi)
        pts = [(px + rr * math.cos(a0 + ouverture * q / 18), py + rr * math.sin(a0 + ouverture * q / 18)) for q in range(19)]
        chemin = morceaux(pts)
        if chemin:
            w = r.choice((.6, .8, 1.1, 1.5, 2.2))
            out.append(f'<path d="{chemin}" stroke="{ACC if i in acc else ENCRE}" stroke-width="{n(w + (.8 if i in acc else 0), 2)}"/>')
    return out + [points([(px, py)], 5, ACC)] if 8 < px < 192 and 8 < py < 192 else out


def lentille(r, d):
    """Un réseau de points vu à travers une lentille : il s'ouvre en anneau, les points de l'anneau grossis et à
    l'accent : lentille gravitationnelle, relativité générale, cosmologie, matière noire."""
    cx, cy = 100 + r.uniform(-14, 14), 100 + r.uniform(-14, 14)
    te = r.uniform(30, 46)
    classes = defaultdict(list)
    for bx, by in semis_dans(lambda x, y: True, r.choice((6.4, 7.2)), -40, -40, 240, 240, decale=False):
        bx, by = bx - cx + r.uniform(-.8, .8), by - cy + r.uniform(-.8, .8)
        b = math.hypot(bx, by) or 1e-6
        for sg in (1, -1):
            th = (b + sg * math.sqrt(b * b + 4 * te * te)) / 2
            x, y = cx + bx / b * th, cy + by / b * th
            if not (8 < x < 192 and 8 < y < 192) or abs(th) < te * .62:
                continue
            mu = abs(1 / (1 - (te / th) ** 4)) if abs(th) != te else 9
            diam = round(min(4.6, 1.1 + .9 * math.sqrt(mu)), 1)
            classes[(ACC if abs(abs(th) - te) < 5 else ENCRE, diam)].append((x, y))
    return [points(p, t, c) for (c, t), p in sorted(classes.items(), key=lambda k: k[0][1])]


def paquets(r, d):
    """Rangées de traits calmes qu'un paquet d'ondes soulève, de plus en plus large et décalé d'une rangée à
    l'autre ; une rangée à l'accent : mécanique quantique, paquets d'ondes, dispersion, fonction d'onde."""
    k = r.randint(11, 16)
    pas = 176 / k
    k0, ka = r.uniform(.24, .42), r.randrange(k)
    x0, v = r.uniform(36, 70), r.uniform(5, 9)
    out = []
    for j in range(k):
        y0 = 14 + (j + .5) * pas
        xc, sig = x0 + v * j, 8 + 3 * j
        pts = [(x, y0 - pas * 1.05 * math.exp(-((x - xc) / sig) ** 2 / 2) * math.cos(k0 * (x - xc))) for x in (8 + 1.6 * q for q in range(116))]
        out.append(trait(pts, ACC if j == ka else ENCRE, 2.2 if j == ka else 1.1))
    return out

def abrikosov(r, d):
    """Réseau triangulaire de petits tourbillons à anneaux, quelques défauts, un tourbillon plein d'accent :
    supraconductivité, vortex, superfluides, matière condensée."""
    a_ = r.uniform(21, 30)
    rot = r.uniform(0, math.pi / 3)
    sites = []
    for i in range(-10, 11):
        for j in range(-10, 11):
            x, y = a_ * (i + .5 * j), a_ * j * math.sqrt(3) / 2
            x, y = 100 + x * math.cos(rot) - y * math.sin(rot) + r.gauss(0, 1), 100 + x * math.sin(rot) + y * math.cos(rot) + r.gauss(0, 1)
            if 8 + a_ * .4 < x < 192 - a_ * .4 and 8 + a_ * .4 < y < 192 - a_ * .4:
                sites.append((x, y))
    for _ in range(r.randint(1, 3)):
        if sites:
            sites.pop(r.randrange(len(sites)))
    ia = r.randrange(len(sites))
    out = []
    for i, (x, y) in enumerate(sites):
        if i == ia:
            out.append(disque(x, y, a_ * .4, ACC))
        out += [cercle(x, y, a_ * .38, ENCRE, .9), cercle(x, y, a_ * .23, DOUX, .9)]
    return out + [points(sites, 2.6, ENCRE)]


# sciences de la Terre et climat (suite)

def hachures(r, d):
    """Relief rendu par des hachures : traits courts dans le sens de la pente, d'autant plus longs et épais qu'elle est
    raide, ceux qui font face à la lumière à l'accent : cartographie, géomorphologie, relief, terrain."""
    h = champ_lisse(r, 6, .01, .03)
    lum = r.uniform(0, 2 * math.pi)
    traits = defaultdict(list)
    for x, y in semis_dans(lambda x, y: True, 5, 8, 8, 192, 192):
        x, y = x + r.uniform(-1.2, 1.2), y + r.uniform(-1.2, 1.2)
        gx, gy = (h(x + .8, y) - h(x - .8, y)) / 1.6, (h(x, y + .8) - h(x, y - .8)) / 1.6
        g = math.hypot(gx, gy)
        pente = min(1.0, g / .042)
        if pente < .2:
            continue
        ux, uy = gx / g, gy / g
        l = 1.2 + 3.2 * pente
        w = (.8, 1.3, 1.9)[min(2, int(pente * 3))]
        cle = (ACC if ux * math.cos(lum) + uy * math.sin(lum) > .6 else ENCRE, w)
        traits[cle].append(f"M{n(x - ux * l)} {n(y - uy * l)}L{n(x + ux * l)} {n(y + uy * l)}")
    return [f'<path d="{"".join(v)}" stroke="{c}" stroke-width="{w}"/>' for (c, w), v in traits.items()]


def orgues(r, d):
    """Prismes vus d'en haut : cellules presque hexagonales, pleines, en trame ou vides, quelques-unes à l'accent :
    volcanologie, basaltes, roches magmatiques, laves."""
    a = r.uniform(20, 26)
    sites = []
    for i in range(-2, 14):
        for j in range(-2, 14):
            x, y = 4 + a * (i + .5 * (j % 2)) + r.gauss(0, 2.2), 4 + a * j * .866 + r.gauss(0, 2.2)
            if -10 < x < 210 and -10 < y < 210:
                sites.append((x, y))
    out = []
    for poly, _ in voronoi(sites):
        if len(poly) < 3:
            continue
        q = r.random()
        poly = retrecit(poly, .88)
        if q < .05:
            out.append(plein(poly, ACC))
        elif q < .4:
            out += [plein(poly, ENCRE), plein(retrecit(poly, .5), "none", f' stroke="{FOND}" stroke-width="0.9"')]
        elif q < .72:
            out.append(plein(poly, DOUX))
        else:
            out.append(plein(poly, "none", f' stroke="{ENCRE}" stroke-width="1.1"'))
    return out


def banquise(r, d):
    """Plaques claires sur une eau sombre : cellules irrégulières qui se détachent, plus petites vers un bord,
    quelques-unes à l'accent : glace de mer, régions polaires, cryosphère, glaciers."""
    bord = r.choice(("haut", "bas", "gauche", "droite"))
    sites = []
    for _ in range(4000):
        if len(sites) >= 110:
            break
        x, y = r.uniform(4, 196), r.uniform(4, 196)
        t = {"haut": y, "bas": 200 - y, "gauche": x, "droite": 200 - x}[bord] / 200
        if all(math.dist((x, y), q) > 7 + 22 * t for q in sites):
            sites.append((x, y))
    out = [boite(8, 8, 184, 184, ENCRE, None)]
    for poly, _ in voronoi(sites):
        if len(poly) < 3:
            continue
        f = r.uniform(.68, .93)
        out.append(plein(retrecit(poly, f), ACC if r.random() < .05 else FOND))
    bris = [(r.uniform(9, 191), r.uniform(9, 191)) for _ in range(160)]
    return out + [points(bris, 1.4, FOND)]


def affluents(r, d):
    """Réseau de rivières qui se ramifie depuis une embouchure, épaisseur selon l'ordre, le cours principal à
    l'accent : hydrologie, bassins versants, rivières, érosion."""
    traits = defaultdict(list)
    prof_max = r.randint(7, 8)

    def branche(x, y, a, w, prof, principal):
        pts = [(x, y)]
        for _ in range(int(r.randint(4, 7) * (1 + .5 * (prof_max - prof) / prof_max) * 1.4)):
            a += r.gauss(0, .2)
            x, y = x + 3.6 * math.cos(a), y + 3.6 * math.sin(a)
            pts.append((x, y))
            if not (8 < x < 192 and 8 < y < 192):
                break
        traits[(ACC if principal else ENCRE, round(w, 1))].append(trace(pts))
        if prof < prof_max and 8 < x < 192 and 8 < y < 192:
            ecart = r.uniform(.35, .75)
            cote = r.choice((-1, 1))
            branche(x, y, a + cote * ecart * r.uniform(.2, .6), w * .82, prof + 1, principal)
            branche(x, y, a - cote * ecart, w * .62, prof + 1, False)

    depart = r.choice(((100, 192, -math.pi / 2), (8, 100, 0), (100, 8, math.pi / 2), (192, 100, math.pi)))
    branche(depart[0] + r.uniform(-20, 20) * (depart[1] != 100), depart[1] + r.uniform(-20, 20) * (depart[0] != 100), depart[2], 4.6, 0, True)
    return [f'<path d="{"".join(v)}" stroke="{c}" stroke-width="{w}"/>' for (c, w), v in sorted(traits.items(), key=lambda k: -k[0][1])]


def rossby(r, d):
    """Anneaux qui ondulent autour d'un pôle, plus agités aux latitudes moyennes, l'anneau du courant-jet à
    l'accent : circulation atmosphérique, courant-jet, ondes de Rossby, vortex polaire."""
    cx, cy = 100 + r.uniform(-10, 10), 100 + r.uniform(-10, 10)
    m, k = r.randint(4, 6), r.randint(8, 12)
    ka = k // 2 + r.randint(-1, 1)
    out = []
    for i in range(k):
        R = 10 + i * 92 / k
        amp = 2 + 11 * math.sin(math.pi * (i + .5) / k) ** 2
        ph, ph2 = .35 * i + r.uniform(-.2, .2), r.uniform(0, 6.3)
        pts = [(cx + (R + amp * math.sin(m * t + ph) + amp * .3 * math.sin(2 * m * t + ph2)) * math.cos(t),
                cy + (R + amp * math.sin(m * t + ph) + amp * .3 * math.sin(2 * m * t + ph2)) * math.sin(t)) for t in (2 * math.pi * q / 180 for q in range(181))]
        acc = i == ka
        out.append(f'<path d="{morceaux(pts)}" stroke="{ACC if acc else ENCRE}" stroke-width="{3 if acc else 1.2}"/>')
    return out + [points([(cx, cy)], 5, ENCRE)]


def averse(r, d):
    """Tirets obliques plus ou moins serrés selon des cellules de pluie, les plus denses à l'accent : météorologie,
    précipitations, pluie, orages, cycle de l'eau."""
    a = math.pi / 2 + r.uniform(-.45, .45)
    f = champ_lisse(r, 5, .01, .028)
    traits = {ENCRE: [], ACC: []}
    nb = 0
    for _ in range(7000):
        if nb >= 620:
            break
        x, y = r.uniform(10, 190), r.uniform(10, 190)
        v = max(0.0, min(1.0, (f(x, y) + 1) / 2))
        if r.random() < v ** 1.7:
            l = r.uniform(3, 6.5)
            traits[ACC if v > .82 else ENCRE].append(f"M{n(x - l * math.cos(a))} {n(y - l * math.sin(a))}L{n(x + l * math.cos(a))} {n(y + l * math.sin(a))}")
            nb += 1
    return [f'<path d="{"".join(v)}" stroke="{c}" stroke-width="1.3"/>' for c, v in traits.items() if v]


def carottes(r, d):
    """Colonnes de couches minces d'épaisseurs variables, la même séquence d'une colonne à l'autre, étirée ; une
    couche repère à l'accent, reliée en tirets : paléoclimat, carottes glaciaires, archives sédimentaires."""
    k = r.randint(6, 9)
    fente = 184 / k
    w = fente * .56
    base = [r.lognormvariate(1.1, .55) for _ in range(70)]
    ia = r.randint(8, 22)
    tons = (ENCRE, DOUX, None, ENCRE, None, DOUX, None)
    out, reperes = [], []
    for c in range(k):
        x = 8 + c * fente + (fente - w) / 2
        y, ech = 8.0, r.uniform(.8, 1.25)
        for i, e in enumerate(base):
            h = e * ech * r.uniform(.75, 1.25) * (1 - .25 * (y - 8) / 184)
            if y + h > 192:
                h = 192 - y
            ton = ACC if i == ia else tons[i % len(tons)]
            if ton:
                out.append(boite(x, y, w, h, ton, None))
            if i == ia:
                reperes.append((x, x + w, y))
            y += h
            if y >= 192:
                break
        out.append(boite(x, 8, w, 184, "none", ENCRE, .9))
    liens = "".join(f"M{n(a[1])} {n(a[2])}L{n(b[0])} {n(b[2])}" for a, b in zip(reperes, reperes[1:]))
    return out + [f'<path d="{liens}" stroke="{ACC}" stroke-width="1" stroke-dasharray="2.4 2"/>']


def dorsale(r, d):
    """Bandes verticales symétriques de part et d'autre d'un axe à l'accent, décalées par des failles transversales :
    tectonique des plaques, dorsales océaniques, paléomagnétisme, inversions magnétiques."""
    largeurs = []
    total = 0
    while total < 100:
        l = r.uniform(2, 10)
        largeurs.append(l)
        total += l
    coupes = sorted(r.sample(range(40, 161, 30), r.randint(2, 4)))
    bornes = [8] + coupes + [192]
    out, failles = [], []
    for y0, y1 in zip(bornes, bornes[1:]):
        xc = 100 + r.uniform(-14, 14)
        x = 0.0
        for i, l in enumerate(largeurs):
            if i % 2 == 0:
                for sg in (1, -1):
                    xa, xb = xc + sg * (x + 1.6), xc + sg * (x + l + 1.6)
                    xa, xb = max(8.0, min(192.0, min(xa, xb))), max(8.0, min(192.0, max(xa, xb)))
                    if xb > xa:
                        out.append(boite(xa, y0 + .8, xb - xa, y1 - y0 - 1.6, ENCRE, None))
            x += l
        out.append(boite(xc - 1.6, y0 + .8, 3.2, y1 - y0 - 1.6, ACC, None))
        failles.append(y1)
    return out + [trait([(8, y), (192, y)], DOUX, .9) for y in failles[:-1]]


def dunes(r, d):
    """Crêtes sinueuses en rangées, chacune ourlée d'une ombre pleine sous le vent, des rides fines entre elles ; une
    crête à l'accent : déserts, dunes, transport éolien, sable."""
    k = r.randint(8, 12)
    pas = 184 / k
    lam, phi = r.uniform(70, 140), r.uniform(0, 6.3)
    ka, out, rides = r.randrange(k), [], []
    for j in range(k):
        y0 = 8 + (j + .55) * pas
        ph = phi + j * r.uniform(.3, .9)
        crete = lambda x, ph=ph, y0=y0: y0 + pas * .28 * math.sin(2 * math.pi * x / lam + ph) + pas * .1 * math.sin(2 * math.pi * x / (lam * .37) + ph * 2)
        xs = [8 + 184 * q / 80 for q in range(81)]
        haut_ = [(x, crete(x)) for x in xs]
        ombre = [(x, crete(x) + pas * (.18 + .14 * (1 + math.sin(2 * math.pi * x / lam + ph + 1.2)) / 2)) for x in xs[::-1]]
        out.append(plein([(x, min(192.0, y)) for x, y in haut_ + ombre], ACC if j == ka else ENCRE))
        for q in range(3):
            yr = y0 + pas * (.45 + .15 * q)
            if yr < 190:
                rides.append(trace([(x, crete(x) - y0 + yr) for x in xs[::4]]))
    return [f'<path d="{"".join(rides)}" stroke="{DOUX}" stroke-width="0.7"/>'] + out


def nebulosite(r, d):
    """Trame de points dont la taille suit une couverture nuageuse : vides là où le ciel se dégage, gros points au
    cœur des nuages, les plus épais à l'accent : nuages, télédétection, imagerie satellite, aérosols."""
    f1, f2 = champ_lisse(r, 7, .01, .03), champ_lisse(r, 7, .03, .08)
    grille = [(x, y, f1(x, y) * .75 + f2(x, y) * .25) for x, y in semis_dans(lambda x, y: True, 4.4, 8, 8, 192, 192)]
    vals = sorted(g[2] for g in grille)
    seuil, haut = vals[int(len(vals) * r.uniform(.4, .6))], vals[-1]
    classes = defaultdict(list)
    for x, y, v in grille:
        v = (v - seuil) / (haut - seuil)
        if v <= .04:
            continue
        diam = round(min(4.6, .8 + 4 * v), 1)
        classes[(ACC if v > .78 else ENCRE, diam)].append((x, y))
    return [points(p, t, c) for (c, t), p in sorted(classes.items(), key=lambda k: k[0][1])]


def poreux(r, d):
    """Grains serrés de tailles diverses, un semis fin dans les vides, et un chemin d'accent qui traverse de part en
    part entre les grains : milieux poreux, perméabilité, aquifères, eaux souterraines."""
    grains = []
    for _ in range(3000):
        if len(grains) >= 70:
            break
        rr = min(18.0, max(5.0, r.lognormvariate(2.2, .35)))
        x, y = r.uniform(8 + rr, 192 - rr), r.uniform(8 + rr, 192 - rr)
        if all(math.dist((x, y), (a, b)) > rr + c + 2.6 for a, b, c in grains):
            grains.append((x, y, rr))
    libre = lambda x, y, m=2.4: all(math.dist((x, y), (a, b)) > c + m for a, b, c in grains)
    pores = semis_dans(lambda x, y: libre(x, y, 1.6), 4.8, 9, 9, 191, 191)

    def chemin(couleur, w):
        meilleur = []
        for _ in range(14):
            y0 = r.uniform(20, 180)
            x, y, a, pts = 8.0, y0, 0.0, [(8.0, y0)]
            if not libre(x + 2, y, 1):
                continue
            for _ in range(520):
                choix_ = [a + da for da in (0, .3, -.3, .6, -.6, .9, -.9, 1.2, -1.2, 1.6, -1.6, 2, -2)]
                choix_ = [b for b in choix_ if abs(b) < 2.2 and libre(x + 2 * math.cos(b), y + 2 * math.sin(b), 1) and 9 < y + 2 * math.sin(b) < 191]
                if not choix_:
                    break
                a = choix_[0] * .85 + r.gauss(0, .1)
                x, y = x + 2 * math.cos(a), y + 2 * math.sin(a)
                pts.append((x, y))
                if x > 191:
                    break
            if pts[-1][0] > meilleur[-1][0] if meilleur else True:
                meilleur = pts
            if meilleur[-1][0] > 190:
                break
        return trait(meilleur, couleur, w) if len(meilleur) > 1 else ""

    out = [points(pores, 1.1, DOUX)]
    out += [cercle(x, y, rr, ENCRE, 1.3) for x, y, rr in grains]
    return out + [chemin(DOUX, 1.3), chemin(ACC, 2.2)]


def epicentres(r, d):
    """Points de tailles très inégales (beaucoup de petits, peu de gros) massés le long de deux ou trois frontières
    invisibles ; les plus gros cerclés à l'accent : aléa sismique, sismicité, failles actives."""
    courbes = []
    for _ in range(r.randint(2, 3)):
        y0, a1, f1, p1 = r.uniform(30, 170), r.uniform(10, 40), r.uniform(.008, .02), r.uniform(0, 6.3)
        verticale = r.random() < .4
        courbes.append((y0, a1, f1, p1, verticale))
    classes = defaultdict(list)
    gros = []
    for _ in range(r.randint(300, 440)):
        y0, a1, f1, p1, vert = r.choice(courbes)
        t = r.uniform(8, 192)
        u = y0 + a1 * math.sin(f1 * t + p1) + r.gauss(0, 5 if r.random() < .8 else 16)
        x, y = (u, t) if vert else (t, u)
        if not (8 < x < 192 and 8 < y < 192):
            continue
        m = 2 + r.expovariate(1 / .55)
        if m > 4.6:
            gros.append((x, y, m))
        else:
            classes[round(1 + (m - 2) * 1.2, 1)].append((x, y))
    out = [points(p, t, ENCRE) for t, p in sorted(classes.items())]
    for x, y, m in gros:
        rr = min(9.0, 2 + (m - 4.6) * 3)
        out += [disque(x, y, rr * .55, ACC), cercle(x, y, rr * 1.4, ACC, 1)]
    return out


# mathématiques (suite)

def mandelbrot(r, d):
    """L'ensemble de Mandelbrot en trame : points pleins dedans, points qui grossissent vers le bord dehors, une bande
    d'échappement sur six à l'accent : fractales, ensemble de Mandelbrot, itérations complexes."""
    cx, cy, demi = -.62 + r.uniform(-.1, .1), r.uniform(-.08, .08), r.uniform(1.25, 1.5)
    m = 60
    grille = []
    for px, py in semis_dans(lambda x, y: True, 3.7, 8, 8, 192, 192):
        c = complex(cx + (px - 100) / 92 * demi, cy + (py - 100) / 92 * demi)
        z, k = 0j, 0
        while k < m and abs(z) <= 2:
            z, k = z * z + c, k + 1
        grille.append((px, py, k))
    kmin = min(g[2] for g in grille)
    classes = defaultdict(list)
    for px, py, k in grille:
        if k == m:
            classes[(ENCRE, 2.6)].append((px, py))
        elif k >= kmin + 2:
            t = ((k - kmin) / (m - kmin)) ** .45
            classes[(ACC if (k - kmin) % 6 == 0 and t > .3 else ENCRE, round(.5 + 2 * t, 1))].append((px, py))
    return [points(p, t, c) for (c, t), p in sorted(classes.items(), key=lambda k: k[0][1])]


def hilbert(r, d):
    """Courbe de Hilbert qui remplit le carré sans jamais se croiser, un tronçon à l'accent : courbes remplissantes,
    récursivité, espaces de Hilbert, ordre et parcours."""
    ordre = r.choice((4, 5, 5))
    m = 2 ** ordre

    def d2xy(dd):
        x = y = 0
        s, t = 1, dd
        while s < m:
            rx = 1 & (t // 2)
            ry = 1 & (t ^ rx)
            if ry == 0:
                if rx == 1:
                    x, y = s - 1 - x, s - 1 - y
                x, y = y, x
            x, y, t, s = x + s * rx, y + s * ry, t // 4, s * 2
        return x, y

    c = 184 / m
    rot = r.randrange(4)
    pts = []
    for dd in range(m * m):
        x, y = d2xy(dd)
        for _ in range(rot):
            x, y = m - 1 - y, x
        pts.append((8 + (x + .5) * c, 8 + (y + .5) * c))
    debut = r.randrange(m * m * 2 // 3)
    fin = debut + m * m // r.choice((5, 6, 8))
    return [trait(pts, ENCRE, 1.6 if ordre == 4 else 1.2), trait(pts[debut:fin], ACC, 3 if ordre == 4 else 2.4)]


def penrose(r, d):
    """Pavage de Penrose : losanges fins et épais sans période, les fins à l'encre, quelques-uns à l'accent :
    pavages apériodiques, quasicristaux, symétrie d'ordre cinq."""
    phi = (1 + 5 ** .5) / 2
    R = r.uniform(150, 230)
    c0 = complex(100 + r.uniform(-30, 30), 100 + r.uniform(-30, 30))
    rot = r.uniform(0, 2 * math.pi)
    tri = []
    for i in range(10):
        B = c0 + R * complex(math.cos((2 * i - 1) * math.pi / 10 + rot), math.sin((2 * i - 1) * math.pi / 10 + rot))
        C = c0 + R * complex(math.cos((2 * i + 1) * math.pi / 10 + rot), math.sin((2 * i + 1) * math.pi / 10 + rot))
        if i % 2 == 0:
            B, C = C, B
        tri.append((0, c0, B, C))
    for _ in range(5 if R > 190 else 4):
        nouv = []
        for col, A, B, C in tri:
            if col == 0:
                P = A + (B - A) / phi
                nouv += [(0, C, P, B), (1, P, C, A)]
            else:
                Q, Rr = B + (A - B) / phi, B + (C - B) / phi
                nouv += [(1, Rr, C, A), (1, Q, Rr, B), (0, Rr, Q, A)]
        tri = nouv
    pleins, accents, bords = [], [], []
    for col, A, B, C in tri:
        if not all(7 < p.real < 193 and 7 < p.imag < 193 for p in (A, B, C)):
            continue
        poly = f"M{n(A.real)} {n(A.imag)}L{n(B.real)} {n(B.imag)}L{n(C.real)} {n(C.imag)}Z"
        if col == 0:
            (accents if r.random() < .06 else pleins).append(poly)
        bords.append(f"M{n(C.real)} {n(C.imag)}L{n(A.real)} {n(A.imag)}L{n(B.real)} {n(B.imag)}")
    return [f'<path d="{"".join(pleins)}" fill="{ENCRE}"/>', f'<path d="{"".join(accents)}" fill="{ACC}"/>',
            f'<path d="{"".join(bords)}" stroke="{DOUX}" stroke-width="0.8"/>']


def apollonius(r, d):
    """Baderne d'Apollonius : cercles tangents qui remplissent chaque interstice, les plus petits en points, un
    cercle plein d'accent : géométrie du cercle, empilements, inversion, fractales."""
    R, cx, cy = 90.0, 100.0, 100.0
    u = r.uniform(.3, .62)
    r1, r2 = R * u, R * (1 - u)
    cercles = [(-1 / R, complex(cx, cy)), (1 / r1, complex(cx - R + r1, cy)), (1 / r2, complex(cx + R - r2, cy))]
    (k0, z0), (k1, z1), (k2, z2) = cercles
    k3 = k0 + k1 + k2 + 2 * math.sqrt(max(0.0, k0 * k1 + k1 * k2 + k2 * k0))
    racine = cmath.sqrt(k0 * k1 * z0 * z1 + k1 * k2 * z1 * z2 + k2 * k0 * z2 * z0)
    z3 = min(((k0 * z0 + k1 * z1 + k2 * z2 + sg * 2 * racine) / k3 for sg in (1, -1)), key=lambda z: abs(abs(z - z1) - (r1 + 1 / k3)))
    c3 = (k3, z3)
    rot = r.uniform(0, 2 * math.pi)
    tous = [cercles[1], cercles[2], c3]
    rmin, limite = .75, 1400

    def reflet(a, b, c, vieux):
        k = 2 * (a[0] + b[0] + c[0]) - vieux[0]
        kz = 2 * (a[0] * a[1] + b[0] * b[1] + c[0] * c[1]) - vieux[0] * vieux[1]
        return k, kz / k

    pile = [(cercles[0], cercles[1], cercles[2], c3), (cercles[0], cercles[1], c3, cercles[2]),
            (cercles[0], cercles[2], c3, cercles[1]), (cercles[1], cercles[2], c3, cercles[0])]
    debut_ = 0
    while debut_ < len(pile) and len(tous) < limite:
        a, b, c, vieux = pile[debut_]
        debut_ += 1
        e = reflet(a, b, c, vieux)
        if e[0] <= 0 or 1 / e[0] < rmin:
            continue
        tous.append(e)
        pile += [(a, b, e, c), (a, c, e, b), (b, c, e, a)]
    tourne = lambda z: complex(cx, cy) + (z - complex(cx, cy)) * cmath.exp(1j * rot)
    ia = max(range(len(tous)), key=lambda i: (1 / tous[i][0]) * (1 if i > 2 else .3))
    out, petits = [cercle(cx, cy, R, ENCRE, 1.6)], defaultdict(list)
    for i, (k, z) in enumerate(tous):
        z = tourne(z)
        rr = 1 / k
        if rr < 3:
            petits[round(max(1.2, rr * 1.8), 1)].append((z.real, z.imag))
        elif i == ia:
            out.append(disque(z.real, z.imag, rr, ACC))
        else:
            out.append(cercle(z.real, z.imag, rr, ENCRE, 1.2 if rr > 12 else .8))
    return out + [points(p, t, ENCRE) for t, p in petits.items()]


def angledor(r, d):
    """Spirale de Vogel : des points posés à l'angle d'or, de plus en plus gros vers le bord, une famille de
    spirales (parastiques) à l'accent : nombre d'or, suite de Fibonacci, phyllotaxie."""
    nb = r.randint(380, 700)
    c = 88 / math.sqrt(nb)
    ga = math.pi * (3 - math.sqrt(5))
    fam, j0 = r.choice((13, 21, 34)), r.randrange(8)
    rot = r.uniform(0, 2 * math.pi)
    classes = defaultdict(list)
    for k in range(1, nb):
        rr, a = c * math.sqrt(k), k * ga + rot
        diam = round(1.2 + 3.4 * (k / nb) ** .6, 1)
        classes[(ACC if k % fam == j0 else ENCRE, diam)].append((100 + rr * math.cos(a), 100 + rr * math.sin(a)))
    return [points(p, t, c_) for (c_, t), p in classes.items()]


def collatz(r, d):
    """Corail de Collatz : chaque suite de Syracuse remonte du même pied en tournant d'un côté pour les pairs, de
    l'autre pour les impairs ; une suite à l'accent : suites récurrentes, conjectures, arithmétique."""
    pair, impair = r.uniform(.12, .2), r.uniform(-.34, -.22)
    nombres = r.sample(range(3, 3000), r.randint(70, 95))
    pos, aretes, chemins = {1: (0.0, 0.0, -math.pi / 2)}, set(), []
    for nb in nombres:
        seq = [nb]
        while seq[-1] != 1 and len(seq) < 400:
            v = seq[-1]
            seq.append(v // 2 if v % 2 == 0 else 3 * v + 1)
        seq = seq[::-1]
        for a, b in zip(seq, seq[1:]):
            if b not in pos:
                x, y, ang = pos[a]
                ang += pair if b % 2 == 0 else impair
                pos[b] = (x + 2 * math.cos(ang), y + 2 * math.sin(ang), ang)
            aretes.add((a, b))
        chemins.append(seq)
    xs, ys = [p[0] for p in pos.values()], [p[1] for p in pos.values()]
    e = 176 / max(max(xs) - min(xs), max(ys) - min(ys))
    ox, oy = 100 - e * (max(xs) + min(xs)) / 2, 100 - e * (max(ys) + min(ys)) / 2
    P = lambda k: (ox + e * pos[k][0], oy + e * pos[k][1])
    traits = "".join(f"M{n(P(a)[0])} {n(P(a)[1])}L{n(P(b)[0])} {n(P(b)[1])}" for a, b in aretes)
    acc = max(chemins, key=len)
    return [f'<path d="{traits}" stroke="{ENCRE}" stroke-width="0.8"/>', trait([P(k) for k in acc], ACC, 2), points([P(1)], 6, ACC)]


def quatrecouleurs(r, d):
    """Carte de régions irrégulières coloriée en quatre tons sans que deux voisines se ressemblent : théorie des
    graphes, coloration, théorème des quatre couleurs, graphes planaires."""
    sites = []
    for _ in range(3000):
        if len(sites) >= 48:
            break
        p = (r.uniform(4, 196), r.uniform(4, 196))
        if all(math.dist(p, q) > 21 for q in sites):
            sites.append(p)
    cell = voronoi(sites)
    couleurs = {}
    ordre_ = sorted(range(len(cell)), key=lambda i: -len(cell[i][1]))
    tons = [ENCRE, ACC, DOUX, FOND]
    for i in ordre_:
        pris = {couleurs.get(j) for j in cell[i][1]}
        couleurs[i] = next((t for t in tons if t not in pris), r.choice(tons))
    out = []
    for i, (poly, _) in enumerate(cell):
        if len(poly) < 3:
            continue
        p = retrecit(poly, .93)
        out.append(plein(p, couleurs[i], f' stroke="{ENCRE}" stroke-width="1"' if couleurs[i] == FOND else ""))
    return out


def epicycles(r, d):
    """Épicycles : une chaîne de cercles, chacun centré sur le bord du précédent, et la courbe fermée que trace le
    dernier ; la plume à l'accent : séries de Fourier, analyse harmonique, transformée de Fourier."""
    k = r.randint(4, 7)
    freqs = r.sample([f for f in range(-7, 8) if f], k)
    rayons = sorted((r.uniform(.3, 1) * .62 ** i for i in range(k)), reverse=True)
    phases = [r.uniform(0, 2 * math.pi) for _ in range(k)]
    somme = lambda t, j=k: sum(rayons[i] * cmath.exp(1j * (freqs[i] * t + phases[i])) for i in range(j))
    courbe_ = [somme(2 * math.pi * q / 600) for q in range(601)]
    t0 = r.uniform(0, 2 * math.pi)
    centres = [somme(t0, j) for j in range(k + 1)]
    xs = [z.real for z in courbe_ + centres] + [c.real + rayons[i] for i, c in enumerate(centres[:-1])] + [c.real - rayons[i] for i, c in enumerate(centres[:-1])]
    ys = [z.imag for z in courbe_ + centres] + [c.imag + rayons[i] for i, c in enumerate(centres[:-1])] + [c.imag - rayons[i] for i, c in enumerate(centres[:-1])]
    e = 176 / max(max(xs) - min(xs), max(ys) - min(ys))
    ox, oy = 100 - e * (max(xs) + min(xs)) / 2, 100 - e * (max(ys) + min(ys)) / 2
    P = lambda z: (ox + e * z.real, oy + e * z.imag)
    out = [trait([P(z) for z in courbe_], ENCRE, 1.5)]
    for i in range(k):
        cx_, cy_ = P(centres[i])
        out.append(cercle(cx_, cy_, rayons[i] * e, DOUX, .9))
    out.append(trait([P(c) for c in centres], ENCRE, 1))
    return out + [points([P(c) for c in centres[:-1]], 3, ENCRE), points([P(centres[-1])], 7, ACC)]


def hyperbolique(r, d):
    """Disque de Poincaré : des familles de géodésiques (arcs perpendiculaires au bord) joignant des points
    équidistants du cercle, une famille à l'accent : géométrie hyperbolique, géométries non euclidiennes."""
    R, cx, cy = 90.0, 100.0, 100.0
    m = r.choice((7, 8, 9, 10, 12))
    sauts = r.sample([s for s in range(2, m // 2 + 1)], min(3, m // 2 - 1))
    fa = r.randrange(len(sauts))
    rot = r.uniform(0, 2 * math.pi)
    out = [cercle(cx, cy, R, ENCRE, 1.8)]
    bouts = []
    for f, s in enumerate(sauts):
        dec = rot + f * math.pi / m * r.choice((0, 1))
        chemins = []
        for i in range(m):
            a, b = dec + 2 * math.pi * i / m, dec + 2 * math.pi * (i + s) / m
            pa, pb = (cx + R * math.cos(a), cy + R * math.sin(a)), (cx + R * math.cos(b), cy + R * math.sin(b))
            bouts.append(pa)
            h = (b - a) / 2
            if abs(math.cos(h)) < 1e-6:
                chemins.append(f"M{n(pa[0])} {n(pa[1])}L{n(pb[0])} {n(pb[1])}")
                continue
            dc, rr = R / math.cos(h), R * abs(math.tan(h))
            ox, oy = cx + dc * math.cos((a + b) / 2), cy + dc * math.sin((a + b) / 2)
            ta, tb = math.atan2(pa[1] - oy, pa[0] - ox), math.atan2(pb[1] - oy, pb[0] - ox)
            dt = math.remainder(tb - ta, 2 * math.pi)
            pts = [(ox + rr * math.cos(ta + dt * q / 36), oy + rr * math.sin(ta + dt * q / 36)) for q in range(37)]
            chemins.append(trace(pts))
        acc = f == fa
        out.append(f'<path d="{"".join(chemins)}" stroke="{ACC if acc else ENCRE}" stroke-width="{2.2 if acc else 1.1}"/>')
    return out + [points(bouts, 3.4, ENCRE)]


def young(r, d):
    """Diagramme de Young d'une partition tirée au hasard : cases en escalier, le carré de Durfee en trame douce, une
    équerre à l'accent : partitions d'entiers, combinatoire algébrique, représentations."""
    lignes = [0] * 40
    for _ in range(r.randint(110, 190)):
        coins = [i for i in range(len(lignes)) if (i == 0 or lignes[i] < lignes[i - 1])]
        i = r.choice(coins)
        lignes[i] += 1
    lignes = [l for l in lignes if l]
    m = max(len(lignes), lignes[0])
    c = 184 / m
    durfee = max(i + 1 for i in range(len(lignes)) if lignes[i] >= i + 1)
    hi, hj = r.randrange(min(4, len(lignes))), r.randrange(min(4, lignes[0]))
    hj = min(hj, lignes[hi] - 1)
    out = []
    for i, l in enumerate(lignes):
        for j in range(l):
            equerre = (i == hi and j >= hj) or (j == hj and i >= hi and lignes[i] > hj)
            fond = ACC if equerre else DOUX if i < durfee and j < durfee else FOND
            out.append(boite(8 + j * c, 8 + i * c, c, c, fond, ENCRE, .9))
    return out


def complexe(r, d):
    """Portrait d'une fonction complexe : lignes d'égal module autour des zéros et des pôles, lignes d'égal argument
    qui en rayonnent ; zéros pleins, pôles cerclés à l'accent : analyse complexe, fonctions holomorphes."""
    zeros = [complex(r.uniform(-.9, .9), r.uniform(-.9, .9)) for _ in range(r.randint(2, 3))]
    poles = [complex(r.uniform(-.9, .9), r.uniform(-.9, .9)) for _ in range(r.randint(1, 2))]
    Z = lambda x, y: complex((x - 100) / 80, (y - 100) / 80)
    k = r.choice((4, 5, 6))

    def module(x, y):
        z = Z(x, y)
        return sum(math.log(abs(z - a) + 1e-9) for a in zeros) - sum(math.log(abs(z - b) + 1e-9) for b in poles)

    def argument(x, y):
        z = Z(x, y)
        return math.sin(k * (sum(cmath.phase(z - a) for a in zeros) - sum(cmath.phase(z - b) for b in poles)))

    out = []
    for c, ls in lignes_de_niveau(module, [-2.4 + .5 * q for q in range(10)], 46).items():
        out += [trait(l_, ENCRE, 1) for l_ in ls if len(l_) > 2]
    for c, ls in lignes_de_niveau(argument, [0.0], 46).items():
        out += [trait(l_, DOUX, 1.1) for l_ in ls if len(l_) > 2]
    P = lambda z: (100 + 80 * z.real, 100 + 80 * z.imag)
    return out + [points([P(a) for a in zeros], 7, ENCRE)] + [cercle(*P(b), 4.4, ACC, 2.2) for b in poles]


def spirographe(r, d):
    """Courbes de spirographe (hypotrochoïdes) superposées, l'une à l'accent : courbes paramétrées, roulettes,
    géométrie des courbes planes."""
    R = r.choice((60, 72, 84, 90, 96, 105))
    rr = r.choice([q for q in range(13, 48) if 3 <= q // math.gcd(R, q) <= 9])
    tours = rr // math.gcd(R, rr)
    out = []
    ds = sorted(r.sample([.45, .6, .75, .9, 1.05], 2))
    ka = r.randrange(2)
    for i, dd in enumerate(ds):
        dd *= rr
        echelle = 88 / (R - rr + dd)
        N = 130 * tours
        pts = [(100 + echelle * ((R - rr) * math.cos(t) + dd * math.cos((R - rr) / rr * t)),
                100 + echelle * ((R - rr) * math.sin(t) - dd * math.sin((R - rr) / rr * t))) for t in (2 * math.pi * tours * q / N for q in range(N + 1))]
        out.append(trait(pts, ACC if i == ka else ENCRE, 1.1 if i == ka else .7))
    return out


def tesseract(r, d):
    """Hypercube projeté de la quatrième dimension : seize sommets, trente-deux arêtes, des sillages de sa rotation en
    trait doux, le cube intérieur à l'accent : géométrie en dimension n, algèbre linéaire, polytopes."""
    som = [(a, b, c, e) for a in (-1, 1) for b in (-1, 1) for c in (-1, 1) for e in (-1, 1)]
    aretes = [(i, j) for i in range(16) for j in range(i + 1, 16) if sum(x != y for x, y in zip(som[i], som[j])) == 1]
    a0, b0, c0 = r.uniform(0, 6.3), r.uniform(0, 6.3), r.uniform(0, 6.3)

    def projete(p, a, b, c):
        x, y, z, w = p
        x, w = x * math.cos(a) - w * math.sin(a), x * math.sin(a) + w * math.cos(a)
        y, z = y * math.cos(b) - z * math.sin(b), y * math.sin(b) + z * math.cos(b)
        x, y = x * math.cos(c) - y * math.sin(c), x * math.sin(c) + y * math.cos(c)
        f = 1 / (3 - w)
        x, y, z = x * f, y * f, z * f
        g = 1 / (3 - z)
        return x * g, y * g, w

    base = [projete(p, a0, b0, c0) for p in som]
    e = 80 / max(max(abs(p[0]), abs(p[1])) for p in base)
    P = lambda p: (100 + e * p[0], 100 + e * p[1])
    out = []
    for q in range(1, 6):
        pr = [projete(p, a0 - .07 * q, b0 - .05 * q, c0) for p in som]
        out.append(f'<path d="{"".join(f"M{n(P(pr[i])[0])} {n(P(pr[i])[1])}L{n(P(pr[j])[0])} {n(P(pr[j])[1])}" for i, j in aretes)}" stroke="{DOUX}" stroke-width="0.6"/>')
    dedans = {i for i in range(16) if base[i][2] < 0}
    for i, j in aretes:
        acc = i in dedans and j in dedans
        out.append(trait([P(base[i]), P(base[j])], ACC if acc else ENCRE, 2.2 if acc else 1.6))
    return out + [points([P(p) for p in base], 5, ENCRE)]


# chimie générale (suite)

def laue(r, d):
    """Cliché de diffraction : taches disposées selon une symétrie d'ordre quatre ou six, plus grosses près du
    centre, les plus fortes à l'accent, des anneaux pâles : cristallographie, diffraction des rayons X."""
    sym = r.choice((4, 6))
    a2 = (0.0, 1.0) if sym == 4 else (.5, math.sqrt(3) / 2)
    ech, rot = r.uniform(13, 18), r.uniform(0, math.pi)
    poids = {}
    out = [cercle(100, 100, rr, DOUX, .7) for rr in sorted(r.sample(range(30, 92, 6), 3))]
    classes = defaultdict(list)
    for h in range(-8, 9):
        for k in range(-8, 9):
            if h == k == 0:
                continue
            gx, gy = h + k * a2[0], k * a2[1]
            g = math.hypot(gx, gy)
            cle = round(g, 3)
            if cle not in poids:
                poids[cle] = r.uniform(.3, 1)
            i = math.exp(-(g * ech / 70) ** 2) * poids[cle]
            rho = g * ech * (1 + .004 * g * ech)
            a = math.atan2(gy, gx) + rot
            x, y = 100 + rho * math.cos(a), 100 + rho * math.sin(a)
            diam = round(1 + 7 * i, 1)
            if diam >= 1.5 and 8 < x < 192 and 8 < y < 192:
                classes[(ACC if i > .62 else ENCRE, diam)].append((x, y))
    return out + [points(p, t, c) for (c, t), p in classes.items()] + [disque(100, 100, 7, ENCRE), cercle(100, 100, 11, ENCRE, 1.2)]


def mendeleiev(r, d):
    """La silhouette du tableau périodique : cases dont la taille suit une tendance (plus grosses vers le bas et la
    gauche), un bloc à l'accent : tableau périodique, éléments chimiques, chimie générale."""
    c = 184 / 18
    lignes = [[1, 18], [1, 2] + list(range(13, 19)), [1, 2] + list(range(13, 19))] + [list(range(1, 19))] * 4
    bloc_acc = r.choice(("s", "p", "d", "f"))
    sens = r.choice(((1, 1), (1, -1), (-1, 1)))
    haut = 9.6 * c
    y0 = 100 - haut / 2
    out = []

    def case(col, lig, bloc, yy):
        t = ((lig / 9) if sens[0] > 0 else 1 - lig / 9) * .55 + ((1 - col / 18) if sens[1] > 0 else col / 18) * .45
        s = c * (.36 + .58 * t)
        x = 8 + (col - 1) * c + (c - s) / 2
        y = yy + (c - s) / 2
        if bloc == bloc_acc:
            return boite(x, y, s, s, ACC, None)
        if bloc == "d":
            return boite(x, y, s, s, ENCRE, None)
        if bloc == "p":
            return boite(x, y, s, s, DOUX, None)
        return boite(x, y, s, s, "none", ENCRE, .9)

    for i, cols in enumerate(lignes):
        for col in cols:
            bloc = "s" if col <= 2 or (i == 0 and col == 18 and False) else "d" if col <= 12 else "p"
            out.append(case(col, i, bloc, y0 + i * c))
    for j in range(2):
        for col in range(3, 18):
            out.append(case(col, 7 + j, "f", y0 + (7.6 + j) * c))
    return out


def belousov(r, d):
    """Ondes chimiques en spirales et en cibles autour de quelques cœurs, en trame de points, les fronts à l'accent :
    réactions oscillantes, Belousov-Zhabotinsky, réaction-diffusion."""
    coeurs = [(r.uniform(30, 170), r.uniform(30, 170), r.choice((-1, 1, 1, 0)), r.uniform(0, 6.3)) for _ in range(r.randint(1, 3))]
    lam = r.uniform(14, 22)
    classes = defaultdict(list)
    for x, y in semis_dans(lambda x, y: True, 3.3, 8, 8, 192, 192):
        cx, cy, s, ph = min(coeurs, key=lambda c: math.hypot(x - c[0], y - c[1]))
        rho = math.hypot(x - cx, y - cy)
        th = math.atan2(y - cy, x - cx)
        v = math.sin(s * th + 2 * math.pi * rho / lam + ph)
        if v > .93:
            classes[(ACC, 2.4)].append((x, y))
        elif v > .2:
            classes[(ENCRE, round(1 + 1.4 * v, 1))].append((x, y))
    return [points(p, t, c) for (c, t), p in classes.items()]


def liesegang(r, d):
    """Anneaux de précipité de plus en plus espacés et de plus en plus minces à partir d'un coin, le premier à
    l'accent : anneaux de Liesegang, précipitation périodique, diffusion dans un gel."""
    ox, oy = r.choice(((8, 8), (8, 192), (192, 8), (192, 192), (100, 196), (4, 100)))
    q, r0 = r.uniform(1.12, 1.2), r.uniform(10, 18)
    out, rr, k = [], r0, 0
    while rr < 290 and k < 30:
        suivant = rr * q
        w = max(.8, (suivant - rr) * r.uniform(.3, .45))
        pts = [(ox + (rr + w / 2) * math.cos(t), oy + (rr + w / 2) * math.sin(t)) for t in (2 * math.pi * i / 240 for i in range(241))]
        chemin = morceaux(pts)
        if chemin:
            out.append(f'<path d="{chemin}" stroke="{ACC if k == 0 else ENCRE}" stroke-width="{n(w, 2)}" stroke-linecap="butt"/>')
        rr, k = suivant + r.uniform(0, 2), k + 1
    return out


def maxwell(r, d):
    """Molécules d'un gaz dans une boîte, chacune avec la traînée de sa vitesse, les plus rapides à l'accent :
    théorie cinétique des gaz, distribution de Maxwell-Boltzmann, pression."""
    parts = []
    for _ in range(3000):
        if len(parts) >= 210:
            break
        p = (r.uniform(14, 186), r.uniform(14, 186))
        if all(math.dist(p, q[:2]) > 7.5 for q in parts):
            parts.append((p[0], p[1], r.gauss(0, 1), r.gauss(0, 1)))
    vit = sorted(math.hypot(p[2], p[3]) for p in parts)
    seuil = vit[int(len(vit) * .93)]
    out, tr = [boite(8, 8, 184, 184, "none", ENCRE, 1.6)], {ENCRE: [], ACC: []}
    pts = {ENCRE: [], ACC: []}
    for x, y, vx, vy in parts:
        v = math.hypot(vx, vy)
        c = ACC if v >= seuil else ENCRE
        x0, y0 = max(9.0, min(191.0, x - vx * 6)), max(9.0, min(191.0, y - vy * 6))
        tr[c].append(f"M{n(x0)} {n(y0)}L{n(x)} {n(y)}")
        pts[c].append((x, y))
    out += [f'<path d="{"".join(v)}" stroke="{c if c == ACC else DOUX}" stroke-width="1.1"/>' for c, v in tr.items() if v]
    return out + [points(pts[ENCRE], 3.4, ENCRE), points(pts[ACC], 4.4, ACC)]


def solvatation(r, d):
    """Ions entourés d'une couronne de molécules de solvant, puis d'une seconde plus lâche, dans un semis : chimie
    des solutions, solvatation, ions en solution, solubilité."""
    ions = []
    for _ in range(2000):
        if len(ions) >= r.randint(10, 15):
            break
        p = (r.uniform(26, 174), r.uniform(26, 174))
        if all(math.dist(p, q[:2]) > 38 for q in ions):
            ions.append((p[0], p[1], r.random() < .5))
    out, coq1, coq2 = [], [], []
    for x, y, anion in ions:
        m1, a0 = r.randint(6, 8), r.uniform(0, 2 * math.pi)
        coq1 += [(x + 9.5 * math.cos(a0 + 2 * math.pi * i / m1), y + 9.5 * math.sin(a0 + 2 * math.pi * i / m1)) for i in range(m1)]
        coq2 += [(x + 16 * math.cos(a0 + 2 * math.pi * i / 13 + .2), y + 16 * math.sin(a0 + 2 * math.pi * i / 13 + .2)) for i in range(13) if r.random() < .8]
    libres = [(x, y) for x, y in ((r.uniform(10, 190), r.uniform(10, 190)) for _ in range(500)) if all(math.dist((x, y), i[:2]) > 21 for i in ions)][:220]
    return [points(libres, 1.6, DOUX), points(coq2, 2, DOUX), points(coq1, 3.2, ENCRE),
            points([(x, y) for x, y, a in ions if a], 8.5, ACC), points([(x, y) for x, y, a in ions if not a], 8.5, ENCRE)]


def miroir(r, d):
    """Crochets semés à gauche d'un axe et leurs images exactes à droite, une paire à l'accent : chiralité,
    énantiomères, stéréochimie, symétrie miroir."""
    out = [trait([(100, 8), (100, 192)], DOUX, 1, ' stroke-dasharray="3 3"')]
    k = r.randint(9, 15)
    ka = r.randrange(k)
    for i in range(k):
        cx, cy, R = r.uniform(18, 86), r.uniform(16, 184), r.uniform(5, 12)
        a0, ouv = r.uniform(0, 2 * math.pi), r.uniform(3.4, 4.8)
        arc_ = [(cx + R * math.cos(a0 + ouv * q / 20), cy + R * math.sin(a0 + ouv * q / 20)) for q in range(21)]
        fin = arc_[-1]
        queue = [(cx, cy), (cx + R * 1.5 * math.cos(a0 - .6), cy + R * 1.5 * math.sin(a0 - .6))]
        for sg in (1, -1):
            m = (lambda p: p) if sg > 0 else (lambda p: (200 - p[0], p[1]))
            col = ACC if i == ka else ENCRE
            out += [trait([m(p) for p in arc_], col, 1.8), trait([m(p) for p in queue], col, 1.2), points([m(fin)], 4.4, col)]
    return out


def nucleation(r, d):
    """Grains nés à des instants différents qui croissent en anneaux jusqu'à se rencontrer en frontières courbes ;
    le plus ancien à l'accent : nucléation, croissance cristalline, solidification, cinétique d'Avrami."""
    germes = [(r.uniform(8, 192), r.uniform(8, 192), r.uniform(0, 70)) for _ in range(r.randint(10, 18))]
    w = r.uniform(5, 7.5)
    ia = min(range(len(germes)), key=lambda i: germes[i][2])
    classes = defaultdict(list)
    for x, y in semis_dans(lambda x, y: True, 3.4, 8, 8, 192, 192):
        g = min(range(len(germes)), key=lambda i: germes[i][2] + math.hypot(x - germes[i][0], y - germes[i][1]))
        rho = math.hypot(x - germes[g][0], y - germes[g][1])
        if int(rho / w) % 2 == 0:
            classes[ACC if g == ia else ENCRE].append((x, y))
    return [points(p, 2.2, c) for c, p in classes.items()] + [points([(x, y) for x, y, _ in germes], 4.4, ENCRE)]


def multiplets(r, d):
    """Arbres de dédoublement : chaque raie se divise en paires, en triplets, puis tombe en barres d'intensités
    binomiales ; un multiplet à l'accent : résonance magnétique nucléaire, couplage spin-spin, déplacement chimique."""
    k = r.randint(3, 5)
    ka = r.randrange(k)
    out = []
    largeur = 184 / k
    for i in range(k):
        xc = 8 + (i + .5) * largeur
        niveaux = [r.choice((1, 1, 2, 3)) for _ in range(r.randint(2, 3))]
        J = largeur * .5 / sum(niveaux)
        pos = [(xc, 1.0)]
        y, pas = 26.0, 110 / (len(niveaux) + 1)
        col = ACC if i == ka else ENCRE
        traits_ = [f"M{n(xc)} 14V{n(y)}"]
        for nn in niveaux:
            nouv = []
            for x, inten in pos:
                for q in range(nn + 1):
                    x2 = x + (q - nn / 2) * J
                    nouv.append((x2, inten * math.comb(nn, q) / 2 ** nn))
                    traits_.append(f"M{n(x)} {n(y)}L{n(x2)} {n(y + pas * .7)}V{n(y + pas)}")
            pos, y = nouv, y + pas
        out.append(f'<path d="{"".join(traits_)}" stroke="{col}" stroke-width="{1.2 if col == ACC else .8}"/>')
        imax = max(p[1] for p in pos)
        barres = "".join(f"M{n(x)} 188V{n(188 - (188 - y - 8) * inten / imax)}" for x, inten in pos)
        out.append(f'<path d="{barres}" stroke="{col}" stroke-width="2.4" stroke-linecap="butt"/>')
    return out


def agregat(r, d):
    """Amas branchu de particules collées les unes aux autres, qui pousse dans toutes les directions par ses pointes,
    comme par agrégation limitée par la diffusion ; les dernières arrivées à l'accent : colloïdes, agrégation,
    nanoparticules, croissance fractale."""
    rad, secteurs = 1.75, 90
    parts = [(100.0, 100.0)]
    case_ = defaultdict(list)
    case_[(100 // 6, 100 // 6)].append(0)
    pointes = [[] for _ in range(secteurs)]
    nb = r.randint(650, 900)
    for _ in range(nb * 10):
        if len(parts) >= nb:
            break
        th = r.uniform(0, 2 * math.pi)
        s0 = int(th / (2 * math.pi) * secteurs)
        cand = [k for q in (-1, 0, 1) for k in pointes[(s0 + q) % secteurs]] or [0]
        i = max(cand, key=lambda k: math.hypot(parts[k][0] - 100, parts[k][1] - 100) + r.uniform(0, 9))
        px, py = parts[i]
        a = th + r.gauss(0, .9)
        x, y = px + 2 * rad * math.cos(a), py + 2 * rad * math.sin(a)
        if not (10 < x < 190 and 10 < y < 190):
            continue
        cx, cy = int(x // 6), int(y // 6)
        voisins = [k for dx in (-1, 0, 1) for dy in (-1, 0, 1) for k in case_[(cx + dx, cy + dy)] if k != i]
        if all(math.hypot(x - parts[k][0], y - parts[k][1]) > 2 * rad * .96 for k in voisins):
            n_ = len(parts)
            case_[(cx, cy)].append(n_)
            parts.append((x, y))
            sb = int((math.atan2(y - 100, x - 100) % (2 * math.pi)) / (2 * math.pi) * secteurs) % secteurs
            pointes[sb] = sorted(pointes[sb] + [n_], key=lambda k: -math.hypot(parts[k][0] - 100, parts[k][1] - 100))[:6]
    seuil = int(len(parts) * .92)
    return [points(parts[:seuil], 2 * rad, ENCRE), points(parts[seuil:], 2 * rad + .6, ACC), points([parts[0]], 6, ENCRE)]

def osmose(r, d):
    """Une paroi en tirets sépare un semis fin (le solvant seul) d'un mélange où se logent de gros points d'accent ;
    le niveau monte du côté chargé : osmose, pression osmotique, membranes, propriétés colligatives."""
    xm = 100 + r.uniform(-12, 12)
    gauche_solvant = r.random() < .5
    haut_s, haut_m = r.uniform(40, 60), r.uniform(18, 34)
    solvant, solute, fin = [], [], []
    for x, y in semis_dans(lambda x, y: True, 5.6, 10, 10, 190, 190):
        x, y = x + r.uniform(-1.6, 1.6), y + r.uniform(-1.6, 1.6)
        cote_solvant = (x < xm) == gauche_solvant
        if abs(x - xm) < 3:
            continue
        if y < (haut_s if cote_solvant else haut_m):
            continue
        if cote_solvant:
            solvant.append((x, y))
        elif r.random() < .14:
            solute.append((x, y))
        elif r.random() < .75:
            fin.append((x, y))
    return [trait([(xm, 10), (xm, 190)], ENCRE, 2, ' stroke-dasharray="6 4"'), points(solvant, 2, ENCRE), points(fin, 2, ENCRE),
            points(solute, 6, ACC), trait([(10, haut_s - 4), (xm - 4, haut_s - 4)] if gauche_solvant else [(xm + 4, haut_s - 4), (190, haut_s - 4)], DOUX, 1),
            trait([(xm + 4, haut_m - 4), (190, haut_m - 4)] if gauche_solvant else [(10, haut_m - 4), (xm - 4, haut_m - 4)], ACC, 1.4)]


def zeolithe(r, d):
    """Réseau d'hexagones (une charpente en nid d'abeilles), quelques cavités en trame douce ou à l'accent, des
    sommets manquants : zéolithes, matériaux poreux, catalyse hétérogène, adsorption."""
    a = r.uniform(9, 13)
    rot = r.uniform(0, math.pi / 3)
    w, h = math.sqrt(3) * a, 1.5 * a
    aretes, cavites, acc, sommets = [], [], [], set()
    for j in range(-14, 15):
        for i in range(-14, 15):
            cx, cy = i * w + (j % 2) * w / 2, j * h
            cx, cy = 100 + cx * math.cos(rot) - cy * math.sin(rot), 100 + cx * math.sin(rot) + cy * math.cos(rot)
            pts = [(cx + a * math.cos(math.pi / 6 + math.pi / 3 * k + rot), cy + a * math.sin(math.pi / 6 + math.pi / 3 * k + rot)) for k in range(6)]
            if not all(8 < x < 192 and 8 < y < 192 for x, y in pts):
                continue
            q = r.random()
            if q < .04:
                acc.append(trace(retrecit(pts, .7)) + "Z")
            elif q < .14:
                cavites.append(trace(retrecit(pts, .7)) + "Z")
            aretes.append(trace(pts) + "Z")
            sommets |= {(round(x, 1), round(y, 1)) for x, y in pts}
    sommets = [s_ for s_ in sommets if r.random() > .06]
    return [f'<path d="{"".join(cavites)}" fill="{DOUX}"/>', f'<path d="{"".join(acc)}" fill="{ACC}"/>',
            f'<path d="{"".join(aretes)}" stroke="{ENCRE}" stroke-width="1.1"/>', points(sommets, 3, ENCRE)]


# ---------- catalogue ----------
# Par domaine : motif → (dessin, mots du sujet qui l'appellent). Un mot finissant par « * » vaut pour tous les mots
# qui commencent ainsi (« régul* » : régulation, réguler…) ; sinon le mot entier, au singulier ou au pluriel. Accents et
# capitales ne comptent pas. Ces mots servent à « couverture: oui », au favicon par défaut et à --motifs SUJET.
CATALOGUE = {
    "Formes générales": {
        "semis": ("semis de points traversé d'une onde pointillée", "signal*, mesure*, bruit*, statisti*, onde*, fréquence*, vibration*, acousti*, spectr*, échantillon*, wave*, noise"),
        "arcs": ("cercles qui se referment case après case", "croissance, progression, apprentissage, évolution, développement, avancement, étapes, growth, progress*"),
        "anneaux": ("anneaux concentriques pleins, pointillés ou ouverts", "diffusion, propagation, cycle*, cercle*, onde de choc, radioacti*, ripple*, circle*"),
        "reseau": ("réseau radial qui s'évase, un chemin à l'accent", "réseau*, graphe*, relation*, social*, internet, network*, connexion*, liens"),
        "automate": ("automate cellulaire né d'une case", "automate*, algorithm*, calcul*, informati*, programmation, turing, comput*, software, code, grafcet, séquenti*, logique, api, plc, industrie 4.0"),
        "trame": ("sphère en trame de points et son orbite", "sphère*, planète*, astro*, soleil, optique*, lumière*, globe*, planet*, light, orbit*"),
        "rayures": ("sphère de rayures et son ombre", "volume*, forme*, objet*, matière, sculpture, shape*"),
        "helice": ("double hélice de points", "adn, dna, gène*, généti*, protéine*, biolog*, molécul*, enzym*, biochimi*"),
        "pavage": ("pavage de Truchet en méandres", "géométri*, pavage*, combinatoire, topolog*, tiling, geometr*, labyrinthe*"),
        "flocon": ("flocon à six branches", "cristal*, cristaux, glace*, neige, symétri*, fractal*, crystal*, snow*, froid"),
        "trajectoires": ("trajectoires de particules dans un champ", "mouvement*, trajectoir*, dynamique, fluide*, particule*, champ*, flux, conflit*, motion, flow*"),
        "taches": ("grille de taches organiques", "cellul*, bactéri*, tissu*, organism*, écolog*, biodivers*, vivant, cells, ecolog*, variation*"),
        "pixels": ("planche de glyphes de pixels", "jeu, jeux, écran*, numérique*, pixel*, game*, screen*, digital*, image*"),
    },
    "Le document lui-même": {
        "colonnes": ("une colonne de texte par section, haute de ses mots ; la plus longue surlignée", "rapport*, bilan, comparaison*, budget*, données, résultats, report*, survey, data"),
        "plan": ("organigramme des sections et sous-sections ; celles à exercices surlignées", "syllabus, programme*, organisation*, méthode*, plan de cours, structure, sommaire, outline"),
        "lettres": ("grille de lettres où un mot du titre croise un mot fréquent du texte", "langue*, linguisti*, vocabulaire*, lexique*, grammaire*, écriture*, traduction*, mots, words, language*, vocab*"),
    },
    "Matière et polymères": {
        "pelote": ("marche aléatoire continue qui s'enroule, ses bouts et son rayon de giration", "chaîne*, pelote*, conformation*, polymère*, macromolécul*, marche aléatoire, rayon de giration, exposant de flory, chaîne idéale, polymer*, random walk"),
        "blobs": ("chaîne de cercles, chacun une petite marche aléatoire", "blob*, semi-dilu*, régime de concentration, régimes de concentration, longueur de corrélation, polyélectrolyte*, solutions de polymères, enchevêtr*, volume exclu, chaîne réelle"),
        "binodale": ("points mêlés en haut, rangés par couleur de part et d'autre d'une brèche en bas", "démixtion, binodale*, spinodal*, miscibilit*, mélanges binaires, mélange binaire, flory-huggins, séparation de phases, mélanges de polymères, point critique, ucst, lcst, blend*"),
        "ternaire": ("trame triangulaire de points, trois dégradés", "ternaire*, trois constituants, solvant*, non-solvant*, extraction liquide, diagramme triangulaire, ternary"),
        "phases": ("trois textures séparées par des frontières vides, réunies en un point", "diagramme de phases, changement d'état, changements d'état, point triple, ébullition, fusion, sublimation, vaporisation, thermodynami*, états de la matière, phase diagram*"),
        "spherolites": ("rayons qui se rencontrent en frontières droites, croix de Malte", "sphérolit*, cristallis*, semi-cristallin*, lamelle*, cristallinit*, morphologi*, microstructure*, spherulit*, crystalliz*"),
        "masses": ("barres fines en cloche, la moyenne à l'accent", "masse molaire, masses molaires, polydispersit*, dispersité, sec, gpc, chromatographi*, exclusion stérique, polymérisation*, molar mass*, molecular weight"),
        "nodules": ("disques à cœur et à écorce dans un semis", "renforcement, résistance au choc, nodule*, cœur-écorce, coeur-ecorce, latex, émulsion*, polymères chargés, toughening, impact"),
        "fibres": ("tirets alignés en haut et en bas, en travers au milieu", "fibre*, composite*, renfort*, orientation*, injection, peau-cœur, peau-coeur, moulage, fiber*"),
    },
    "Mécanique et rhéologie": {
        "traction": ("faisceau de courbes issues d'un coin, chacune finie par un point", "traction, contrainte*, déformation*, rupture*, mécanique des matériaux, module d'young, élasticité, plasticité, ductil*, fragil*, essais mécaniques, endommagement, stress, strain, tensile"),
        "module": ("marches descendantes en faisceau sur une cloche d'accent", "dma, viscoélasti*, transition vitreuse, module*, relaxation, amortissement, tan delta, viscoelastic*, glass transition, dsc"),
        "rheologie": ("faisceau de courbes à plat puis en pente, sur une grille de points", "rhéolog*, viscosit*, cisaillement*, écoulement*, rhéofluidifi*, newtonien*, carreau, mise en forme, extrusion, rheolog*, viscosity, shear"),
    },
    "Réacteurs, procédés et régulation": {
        "cascade": ("cellules en file et longue bande où l'accent gagne sur l'encre", "réacteur*, rac, cstr, piston, pfr, cuve agitée, cuves agitées, génie de la réaction, génie chimique, conversion, batch, reactor*, procédé*, flowsheet, recyclage*, usine*, prosim*, simulation de procédés, opérations unitaires, bilan matière, bilans matière, process*"),
        "dts": ("crêtes superposées, de la plus étalée à la plus pointue", "temps de séjour, dts, traceur*, dispersion axiale, réacteurs réels, réacteur réel, rtd, residence time, bacs en série"),
        "arrhenius": ("éventail de droites jalonnées de ronds", "arrhenius, cinétique*, énergie d'activation, constante de vitesse, vitesse de réaction, catalys*, kinetic*, activation energy"),
        "semenov": ("trame de courbes en S traversée de droites parallèles, ronds aux croisements", "semenov, emballement*, runaway, stabilité thermique, états stationnaires, bilan thermique, bilans thermiques, non isotherme, non-isotherme, exotherm*"),
        "mccabe": ("escaliers en terrasses entre des courbes d'une même famille", "mccabe, thiele, étage théorique, étages théoriques, équilibre liquide-vapeur, volatilité, reflux, distillation*, colonne*, plateau*, rectification, absorption, séparation*, levenspiel, dimensionnement, volume de réacteur, association de réacteurs, réacteurs en série"),
        "amortie": ("rangées d'ondes amorties, de la plus nerveuse à la plus sage", "régul*, boucle*, asservissement*, contrôle-commande, pid, feedback, control*, réponse indicielle, réponses indicielles, échelon*, dépassement*, second ordre, premier ordre, fonction de transfert, bode, fréquentiel*, stabilité, ziegler"),
    },
    "Calcul et plans d'expériences": {
        "maillage": ("triangulation resserrée autour d'un point, triangles teintés", "maillage*, éléments finis, élément fini, différences finies, edp, dérivées partielles, discrétis*, cfd, mesh*, finite element*, simulation numérique"),
        "tangentes": ("nappes de fils tendus entre deux bords, courbes nées de leurs tangentes", "newton, raphson, newton-raphson, résolution numérique, itérati*, convergence, non linéaire*, racine*, méthodes numériques, analyse numérique, solver, tangente*"),
        "cube": ("réseau de points en perspective isométrique, tailles selon une réponse", "plan d'expériences, plans d'expériences, factoriel*, doe, design of experiments, box-behnken, doehlert, criblage, essais, plan composite, fractionnaire*, facteurs"),
        "isoreponses": ("lignes de niveau emboîtées, le cœur à l'accent", "surface de réponse, surfaces de réponse, isoréponse*, optimisation*, optimum, second degré, quadratique*, response surface*, désirabilité, topograph*"),
        "pareto": ("colonnes de points décroissantes, coiffées d'accent", "pareto, effets, significativit*, anova, analyse de variance, qualité, plackett, plackett-burman, sensibilit*"),
    },
    "Risques et sécurité": {
        "braises": ("mosaïque de triangles chauffée par le bas", "incendie*, feu, feux, inflammab*, combusti*, triangle du feu, extinct*, explosi*, point éclair, atex, flamme*, fire"),
        "eventails": ("deux éventails de lignes qui convergent vers un point", "nœud papillon, noeud papillon, bow-tie, analyse des risques, analyse de risques, barrière*, scénario*, arbre de défaillances, arbre d'événements, arbre des causes, hazop, événement redouté"),
        "panache": ("nuage de points qui naît d'un coin et s'élargit", "panache*, dispersion atmosphérique, rejet*, toxique*, pollution, cheminée*, nuage*, gaussien*, émission*, plume"),
        "carreaux": ("grille de carrés qui grandissent vers un coin", "criticit*, matrice de risque*, fréquence-gravité, gravité, apr, amdec, fmea, farmer, maîtrise des risques, prévention, risque*, sécurité, risk*"),
    },
    # sciences exactes : physique et astronomie, Terre et climat, mathématiques, chimie générale
    "Physique et astronomie": {
        "interference": ("champ de points en franges d'interférence, la frange centrale à l'accent", "interférence*, diffraction*, optique ondulatoire, physique des ondes, ondes lumineuses, fentes d'young, franges, cohérence, holograph*, interferen*, wave optics, fringes, young's experiment, coherence, double slit"),
        "geodesiques": ("quadrillage creusé par une ou deux masses", "relativité, relativiste*, espace-temps, gravitation*, géodésique*, einstein, trou noir, trous noirs, ondes gravitationnelles, relativity, relativistic, spacetime, space-time, gravit*, geodesic*, black hole*, gravitational waves"),
        "ising": ("réseau de spins en domaines, parois à l'accent", "physique statistique, mécanique statistique, ising, transition de phase, transitions de phase, magnétisme, ferromagnét*, spins, entropie, statistical physics, statistical mechanics, phase transition*, magnetism, ferromagnet*, entropy, monte carlo"),
        "galaxie": ("spirale de points inclinée, bulbe dense, quelques étoiles à l'accent", "galax*, astrophysi*, étoile*, stellaire*, voie lactée, nébuleuse*, astronomie, télescope*, astrophysics, stars, stellar, milky way, nebula*, astronomy, telescope*"),
        "cosmique": ("toile de filaments entre des nœuds denses", "cosmolog*, univers, big bang, matière noire, énergie noire, grandes structures, fond diffus cosmologique, inflation cosmique, expansion de l'univers, cosmology, universe, dark matter, dark energy, large-scale structure, cosmic web, cosmic microwave background, cmb"),
        # suite
        "dipole": ("lignes de champ entre des charges", "électrostatique, champ électrique, lignes de champ, charges électriques, charge électrique, électromagnétisme, électromagnétique*, électricité, coulomb, electrostatic*, electric field, field lines, electric charge*, electromagnetism, electromagnetic, electricity"),
        "limaille": ("tirets alignés sur le champ de deux pôles", "champ magnétique, aimant*, induction magnétique, magnétostatique, limaille, bobine*, solénoïde*, magnetic field, magnets, magnetic induction, magnetostatic*, solenoid*, coil*"),
        "kepler": ("ellipses de foyer commun et rosace", "mécanique céleste, orbite*, kepler, planétaire*, système solaire, satellite*, problème à deux corps, celestial mechanics, orbital mechanics, planetary, solar system, two-body problem"),
        "lissajous": ("table de figures de Lissajous", "oscillat*, oscillateur*, lissajous, harmonique*, pendule*, mouvement harmonique, oscilloscope*, oscillation*, oscillator*, harmonic*, pendulum*, simple harmonic motion"),
        "chladni": ("sable rassemblé sur les lignes nodales", "chladni, modes propres, mode propre, ondes stationnaires, plaque vibrante, vibrations mécaniques, résonance*, cymatique, standing wave*, normal mode*, eigenmode*, resonance*, vibrating plate*, cymatics"),
        "collision": ("traces en pointillés depuis un vertex", "physique des particules, particules élémentaires, collisionneur*, accélérateur de particules, accélérateurs de particules, chambre à bulles, boson*, quark*, lhc, cern, particle physics, elementary particles, collider*, particle accelerator*, bubble chamber, hadron*"),
        "brillouin": ("zones alternées autour d'une zone centrale", "physique du solide, état solide, brillouin, réseau réciproque, structure de bandes, bandes d'énergie, semi-conducteur*, phonon*, matière condensée, solid state physics, solid-state, reciprocal lattice, band structure, energy bands, semiconductor*, condensed matter"),
        "chirikov": ("îlots et mer chaotique d'une section de Poincaré", "plasma*, fusion nucléaire, tokamak*, confinement magnétique, chaos hamiltonien, application standard, section de poincaré, nuclear fusion, magnetic confinement, hamiltonian chaos, standard map, poincaré section, poincare section"),
        "hertzsprung": ("nuage d'étoiles en bande diagonale", "évolution stellaire, hertzsprung, séquence principale, géante rouge, géantes rouges, naine blanche, naines blanches, diagramme hr, populations stellaires, stellar evolution, main sequence, red giant*, white dwarf*, hr diagram, stellar populations"),
        "circumpolaire": ("arcs concentriques autour d'un pôle", "ciel nocturne, voûte céleste, étoile polaire, rotation de la terre, observation astronomique, astrophotographie, star trail*, night sky, celestial sphere, pole star, polaris, earth's rotation, observational astronomy, astrophotography"),
        "lentille": ("réseau de points ouvert en anneau", "lentille gravitationnelle, lentilles gravitationnelles, anneau d'einstein, mirage gravitationnel, cisaillement gravitationnel, gravitational lens*, einstein ring, weak lensing, strong lensing"),
        "paquets": ("rangées ondulantes dans une enveloppe qui s'élargit", "paquet d'ondes, paquets d'ondes, schrödinger, équation de schrödinger, dualité onde-corpuscule, mécanique ondulatoire, wave packet*, schrödinger equation, wave-particle duality, dispersion relation"),
        "abrikosov": ("réseau triangulaire de petits tourbillons", "supraconduct*, superconduct*, superfluid*, vortex quantiques, abrikosov, effet meissner, hélium superfluide, meissner effect, quantum vortices, type-ii superconductor*"),
    },
    "Terre et climat": {
        "plissement": ("couches plissées en bandes, rejetées par une faille", "géologie, géologique*, strate*, stratigraph*, sédiment*, tectonique*, plis, faille*, roche*, minéralog*, geology, geological, stratigraphy, sediment*, tectonic*, folds, faults, rocks, mineralog*"),
        "sismogramme": ("traces secouées par deux arrivées alignées sur une hyperbole", "sismolog*, séisme*, sismique*, tremblement de terre, tremblements de terre, ondes sismiques, géophysique, sismographe*, seismolog*, earthquake*, seismic, geophysic*, seismograph*"),
        "gyres": ("cellules de circulation, lignes de courant fermées en tirets", "océanograph*, océan*, courants marins, courant marin, courants océaniques, circulation océanique, marée*, gyre*, tourbillon*, oceanograph*, ocean*, ocean currents, ocean circulation, tides, eddies, eddy, vortex, vortices"),
        "isobares": ("lignes de niveau serrées autour de creux et de bosses", "météorolog*, météorologie dynamique, météo, pression atmosphérique, isobare*, dépression atmosphérique, anticyclone*, cyclone*, front froid, fronts froids, vent, vents, prévision météorologique, meteorolog*, weather, atmospheric pressure, isobar*, wind, winds, weather forecast*, dynamic meteorology"),
        "rechauffement": ("bandes verticales froides puis chaudes", "climat*, réchauffement, changement climatique, températures mondiales, anomalies climatiques, giec, gaz à effet de serre, effet de serre, climate, global warming, climate change, global temperature*, ipcc, greenhouse gas*, greenhouse effect, warming stripes"),
        # suite
        "hachures": ("relief en hachures dans le sens de la pente", "cartographie, carte topographique, géomorphologie, relief*, montagne*, modèle numérique de terrain, cartography, topographic map*, geomorphology, terrain, mountain*, hillshade, digital elevation model"),
        "orgues": ("cellules presque hexagonales, prismes vus d'en haut", "basalte*, volcan*, volcanolog*, magma*, lave*, orgues basaltiques, roches volcaniques, basalt*, volcano*, magma, lava, columnar jointing, igneous rock*"),
        "banquise": ("plaques claires sur une eau sombre", "banquise, glace de mer, arctique, antarctique, cryosphère, glacier*, calotte glaciaire, calottes glaciaires, iceberg*, régions polaires, sea ice, arctic, antarctic*, cryosphere, ice sheet*, polar regions"),
        "affluents": ("réseau de rivières qui se ramifie", "hydrolog*, bassin versant, bassins versants, rivière*, fleuve*, cours d'eau, réseau hydrographique, drainage, érosion, hydrology, watershed*, river*, stream network, drainage basin*, catchment*, erosion"),
        "rossby": ("anneaux qui ondulent autour d'un pôle", "circulation atmosphérique, courant-jet, courant jet, jet-stream, ondes de rossby, rossby, vortex polaire, dynamique de l'atmosphère, atmospheric circulation, jet stream, rossby waves, polar vortex, atmospheric dynamics"),
        "averse": ("tirets obliques en cellules de pluie", "précipitation*, pluie*, averse*, orage*, mousson*, cycle de l'eau, hydrométéorolog*, precipitation, rain*, rainfall, storm*, thunderstorm*, monsoon*, water cycle"),
        "carottes": ("colonnes de couches minces, une couche repère", "paléoclimat*, carotte glaciaire, carottes glaciaires, carottes de glace, carottage*, varve*, archives climatiques, quaternaire, glaciation*, paleoclimat*, ice core*, sediment core*, varves, quaternary"),
        "dorsale": ("bandes symétriques autour d'un axe, failles transversales", "tectonique des plaques, dorsale*, expansion océanique, paléomagnétisme, inversions magnétiques, plaques tectoniques, géodynamique, plate tectonics, mid-ocean ridge*, seafloor spreading, paleomagnetism, magnetic reversals, geodynamics"),
        "dunes": ("crêtes sinueuses ourlées d'ombre", "dune*, désert*, sable*, éolien*, transport sédimentaire, désertification, desert*, sand*, aeolian, eolian, sediment transport, desertification"),
        "nebulosite": ("trame de points en couverture nuageuse", "nébulosité, couverture nuageuse, physique des nuages, formation des nuages, télédétection, imagerie satellite, aérosol*, clouds, cloud cover, cloud physics, remote sensing, satellite imagery, aerosol*"),
        "poreux": ("grains serrés et un chemin qui les traverse", "milieux poreux, milieu poreux, porosité, perméabilité, hydrogéolog*, aquifère*, eaux souterraines, percolation, darcy, porous media, porous medium, porosity, permeability, hydrogeolog*, aquifer*, groundwater"),
        "epicentres": ("points très inégaux le long de frontières", "aléa sismique, risque sismique, épicentre*, magnitude*, gutenberg, failles actives, sismicité, seismic hazard, epicent*, seismicity, active faults, earthquake catalog*"),
    },
    "Mathématiques": {
        "isoclines": ("champ de pentes en tirets, courbes intégrales", "équations différentielles, équation différentielle, edo, champ de pentes, isocline*, analyse mathématique, analyse réelle, intégrale*, dérivée*, calcul différentiel, differential equation*, ode, odes, slope field, calculus, integral*, derivative*, real analysis"),
        "attracteur": ("nuage d'un attracteur étrange", "systèmes dynamiques, système dynamique, chaos, chaotique*, attracteur*, bifurcation*, lorenz, dynamical system*, chaos theory, chaotic, attractor*, strange attractor"),
        "modulo": ("cordes d'une table modulo sur un cercle", "algèbre, algébrique*, théorie des groupes, groupes finis, arithmétique modulaire, modulo, congruence*, corps finis, cyclique*, algebra*, group theory, finite groups, modular arithmetic, finite field*, cyclic"),
        "galton": ("clous en quinconce, billes en cloche", "probabilit*, aléatoire*, hasard, loi binomiale, loi normale, variable aléatoire, variables aléatoires, processus stochastique*, galton, probability, probabilities, randomness, binomial*, normal distribution, random variable*, stochastic*"),
        "entrelacs": ("nœud torique en ruban, passages dessus-dessous", "topolog*, théorie des nœuds, entrelacs, tresse*, tore, homotopie, homologie, invariant*, variétés, knot theory, knots, braid*, torus, homotopy, homology, manifold*"),
        "ulam": ("spirale d'Ulam : les nombres premiers en points", "théorie des nombres, nombre premier, nombres premiers, arithmétique, nombres entiers, crible, ulam, riemann, number theory, prime number*, primes, integers, sieve, primality"),
        # suite
        "mandelbrot": ("l'ensemble de Mandelbrot en trame", "ensemble de mandelbrot, mandelbrot, ensemble de julia, géométrie fractale, objets fractals, dimension fractale, auto-similarité, mandelbrot set, julia set*, fractal geometry, fractal dimension, self-similar*"),
        "hilbert": ("courbe de Hilbert qui remplit le carré", "courbe de hilbert, courbe de peano, courbes remplissantes, hilbert, peano, espace de hilbert, espaces de hilbert, récursivité, space-filling curve*, hilbert curve, peano curve, hilbert space*, recursion"),
        "penrose": ("losanges fins et épais sans période", "pavage apériodique, pavages apériodiques, penrose, quasicristal*, quasi-cristal*, symétrie d'ordre cinq, aperiodic tiling*, penrose tiling*, quasicrystal*, fivefold symmetry"),
        "apollonius": ("cercles tangents qui remplissent les interstices", "apollonius, baderne d'apollonius, cercles tangents, empilement de cercles, théorème de descartes, inversion, géométrie du cercle, apollonian gasket, tangent circles, circle packing, descartes theorem, inversive geometry"),
        "angledor": ("points posés à l'angle d'or", "nombre d'or, angle d'or, fibonacci, suite de fibonacci, phyllotaxie, spirale de vogel, proportion dorée, golden ratio, golden angle, fibonacci sequence, phyllotaxis, golden section"),
        "collatz": ("corail des suites de Syracuse", "conjecture de syracuse, syracuse, collatz, suites récurrentes, suite récurrente, problème 3n+1, conjecture*, collatz conjecture, 3n+1, recurrence relation*"),
        "quatrecouleurs": ("carte en quatre tons sans voisines semblables", "théorème des quatre couleurs, quatre couleurs, coloration de graphes, coloriage, graphes planaires, graphe planaire, théorie des graphes, four color theorem, graph coloring, graph colouring, planar graph*, graph theory"),
        "epicycles": ("chaîne de cercles et la courbe qu'elle trace", "séries de fourier, série de fourier, transformée de fourier, fourier, analyse harmonique, épicycle*, fourier series, fourier transform, harmonic analysis, epicycle*"),
        "hyperbolique": ("géodésiques du disque de Poincaré", "géométrie hyperbolique, géométries non euclidiennes, non euclidien*, non-euclidien*, disque de poincaré, plan hyperbolique, géométrie riemannienne, hyperbolic geometry, non-euclidean geometry, non-euclidean, poincaré disk, poincare disk, hyperbolic plane, riemannian geometry"),
        "young": ("diagramme de Young en escalier", "tableaux de young, tableau de young, diagramme de young, diagrammes de young, partitions d'entiers, partition d'un entier, combinatoire algébrique, théorie des représentations, young tableau*, young diagram*, integer partition*, algebraic combinatorics, representation theory"),
        "complexe": ("lignes d'égal module et d'égal argument", "analyse complexe, nombres complexes, nombre complexe, fonctions holomorphes, holomorphe*, théorème des résidus, plan complexe, complex analysis, complex numbers, holomorphic, residue theorem, complex plane"),
        "spirographe": ("courbes de spirographe superposées", "spirographe, courbes paramétrées, courbe paramétrée, roulette*, hypotrochoïde*, épicycloïde*, cycloïde*, courbes planes, spirograph, parametric curve*, hypotrochoid*, epicycloid*, cycloid*, plane curves"),
        "tesseract": ("hypercube projeté et ses sillages", "quatrième dimension, hypercube*, tesseract, géométrie en dimension n, polytope*, grande dimension, algèbre linéaire, espaces vectoriels, fourth dimension, four dimensions, polytopes, high-dimensional, linear algebra, vector space*"),
    },
    "Chimie générale": {
        "raies": ("bandes de raies qui se resserrent vers une limite", "spectroscop*, spectre*, raie*, émission, absorption atomique, infrarouge, uv-visible, raman, fluorescence, spectroscopy, spectrum, spectra, spectral line*, emission spectrum, infrared"),
        "electrode": ("couche serrée contre une paroi, mélange au loin", "électrochim*, électrode*, électrolyse, électrolyte*, pile à combustible, batterie*, accumulateur*, corrosion, oxydoréduction, redox, voltammétrie, double couche, electrochem*, electrode*, electrolysis, electrolyte*, battery, batteries, fuel cell*, voltammetry"),
        "orbitales": ("nuage en lobes d'une densité orbitale", "chimie quantique, orbitale*, mécanique quantique, physique quantique, quantique*, fonction d'onde, liaison chimique, liaisons chimiques, atome*, électron*, quantum chemistry, quantum mechanics, quantum, orbital*, wave function, wavefunction, chemical bond*, atom*, electron*"),
        "chromato": ("pistes de pics, un composé à l'accent", "chimie analytique, chromatograph*, hplc, chromatographie en phase gazeuse, dosage*, titrage*, analyte*, spectrométrie de masse, analytical chemistry, gas chromatography, liquid chromatography, assay*, titration*, mass spectrometry"),
        # suite
        "laue": ("taches de diffraction symétriques autour du faisceau", "cristallographie, cristallographie aux rayons x, diffraction des rayons x, rayons x, laue, bragg, structure cristalline, réseau cristallin, maille cristalline, crystallography, x-ray crystallography, x-ray diffraction, x-rays, crystal structure, crystal lattice, unit cell*"),
        "mendeleiev": ("silhouette du tableau périodique", "tableau périodique, classification périodique, mendeleïev, mendeleiev, éléments chimiques, périodicité, chimie générale, chimie inorganique, periodic table, chemical elements, periodicity, general chemistry, inorganic chemistry"),
        "belousov": ("ondes chimiques en spirales et en cibles", "réaction oscillante, réactions oscillantes, belousov, zhabotinsky, réaction-diffusion, ondes chimiques, autocatalyse, oscillating reaction*, belousov-zhabotinsky, reaction-diffusion, chemical waves, autocatalysis"),
        "liesegang": ("anneaux de plus en plus espacés depuis un coin", "anneaux de liesegang, liesegang, précipitation périodique, précipité*, diffusion dans un gel, liesegang rings, periodic precipitation, precipitate*"),
        "maxwell": ("molécules et traînées de vitesse dans une boîte", "théorie cinétique des gaz, gaz parfait, gaz parfaits, maxwell-boltzmann, distribution des vitesses, pression d'un gaz, kinetic theory of gases, ideal gas*, speed distribution, gas pressure"),
        "solvatation": ("ions entourés de couronnes de solvant", "solvatation, solutions aqueuses, solution aqueuse, ions en solution, hydratation des ions, sphère de solvatation, solubilité, dissolution, chimie des solutions, solvation, aqueous solution*, solvation shell*, hydration shell*, solubility, ions in solution"),
        "miroir": ("crochets et leurs images de part et d'autre d'un axe", "chiralité, chiral*, énantiomère*, stéréochimie, isomérie optique, activité optique, symétrie miroir, chirality, enantiomer*, stereochemistry, optical isomer*, optical activity, mirror symmetry"),
        "nucleation": ("grains en anneaux qui se rencontrent", "nucléation, germination, croissance cristalline, cinétique de cristallisation, avrami, solidification, recristallisation, métallurgie, nucleation, crystal growth, crystallization kinetics, recrystallization, metallurgy"),
        "multiplets": ("arbres de dédoublement et barres binomiales", "résonance magnétique nucléaire, rmn, spectroscopie rmn, couplage spin-spin, multiplet*, déplacement chimique, nuclear magnetic resonance, nmr, nmr spectroscopy, spin-spin coupling, chemical shift*, j-coupling"),
        "agregat": ("amas branchu de particules", "agrégation, agrégats, colloïde*, agrégation limitée par la diffusion, croissance fractale, nanoparticule*, aggregation, aggregates, colloid*, diffusion-limited aggregation, nanoparticle*, fractal growth"),
        "osmose": ("paroi en tirets entre solvant et mélange", "osmose, pression osmotique, membrane semi-perméable, membranes semi-perméables, dialyse, propriétés colligatives, osmosis, osmotic pressure, semipermeable membrane*, dialysis, colligative properties"),
        "zeolithe": ("réseau d'hexagones et ses cavités", "zéolithe*, catalyse hétérogène, matériaux poreux, adsorption, charpentes métallo-organiques, silicates, zeolite*, heterogeneous catalysis, porous materials, metal-organic framework*"),
    },
}
DOMAINE = {m: dom for dom, motifs in CATALOGUE.items() for m in motifs}
MOTIFS = {m: globals()[m] for m in DOMAINE}
ALIAS = {"helix": "helice", "points": "semis", "onde": "semis", "spheres": "trame", "sphere": "trame", "graphe": "reseau",
         "truchet": "pavage", "organigramme": "plan", "mots": "lettres", "cellules": "taches", "grille": "pixels",
         "chaine": "pelote", "polymere": "pelote", "demixtion": "binodale", "spinodale": "binodale", "triangle": "ternaire",
         "spherolite": "spherolites", "sec": "masses", "viscosite": "rheologie", "dma": "module", "contrainte": "traction",
         "composite": "fibres", "coeur": "nodules", "reacteurs": "cascade", "rac": "cascade", "cstr": "cascade", "procede": "cascade",
         "sejour": "dts", "cinetique": "arrhenius", "emballement": "semenov", "distillation": "mccabe", "colonne": "mccabe",
         "regulation": "amortie", "boucle": "amortie", "indicielle": "amortie", "bode": "amortie", "grafcet": "automate",
         "elements": "maillage", "newton": "tangentes", "factoriel": "cube", "plans": "cube", "surface": "isoreponses",
         "feu": "braises", "incendie": "braises", "papillon": "eventails", "bowtie": "eventails", "noeud": "eventails",
         "rejet": "panache", "levenspiel": "mccabe", "escaliers": "mccabe", "criticite": "carreaux", "matrice": "carreaux", "carres": "carreaux", "triple": "phases"}
# sciences exactes
ALIAS.update({"interferences": "interference", "diffraction": "interference", "relativite": "geodesiques", "spins": "ising",
              "galaxies": "galaxie", "cosmologie": "cosmique", "strates": "plissement", "geologie": "plissement",
              "seisme": "sismogramme", "ocean": "gyres", "meteo": "isobares", "climat": "rechauffement", "pentes": "isoclines",
              "chaos": "attracteur", "cardioide": "modulo", "binomiale": "galton", "knot": "entrelacs", "tore": "entrelacs",
              "premiers": "ulam", "spectre": "raies", "electrochimie": "electrode", "orbitale": "orbitales",
              "chromatographie": "chromato"})
ALIAS.update({"magnetisme": "limaille", "aimant": "limaille", "orbites": "kepler", "particules": "collision", "plasma": "chirikov",
              "etoiles": "hertzsprung", "relief": "hachures", "basalte": "orgues", "glace": "banquise", "rivieres": "affluents",
              "jet": "rossby", "pluie": "averse", "tectonique": "dorsale", "nuages": "nebulosite", "fractale": "mandelbrot",
              "fibonacci": "angledor", "syracuse": "collatz", "fourier": "epicycles", "hypercube": "tesseract",
              "periodique": "mendeleiev", "gaz": "maxwell", "chiralite": "miroir", "rmn": "multiplets", "zeolite": "zeolithe"})


def _motif_mot(mot):
    m = sans_accents(mot.strip().lower())
    if m.endswith("*"):
        return r"\b" + re.escape(m[:-1])
    return r"\b" + re.escape(m) + r"[sx]?\b"


INDICES = {m: sorted(((_motif_mot(k), 1 + .6 * k.strip().count(" ")) for k in mots.split(",") if k.strip()), key=lambda x: -x[1])
           for dom in CATALOGUE.values() for m, (_, mots) in dom.items()}


def scores(sujet):
    """{motif: score} pour un texte : chaque mot-clé trouvé compte une fois, une expression de plusieurs mots un peu
    plus ; deux mots-clés d'un même motif qui tombent au même endroit (« polymère… », « polymer… ») ne comptent qu'une."""
    s, total = sans_accents(sujet.lower()), {}
    for m, liste in INDICES.items():
        pris, score = [], 0.0
        for motif, p in liste:
            for x in re.finditer(motif, s):
                if all(x.end() <= a or x.start() >= b for a, b in pris):
                    pris.append(x.span())
                    score += p
                    break
        total[m] = score
    return total
