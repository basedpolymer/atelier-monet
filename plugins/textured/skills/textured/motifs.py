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


# ---------- sciences du vivant ----------

def rond(x, y, rayon):
    """Sous-chemin d'un cercle, pour en réunir beaucoup dans un seul <path>."""
    return f"M{n(x - rayon)} {n(y)}a{n(rayon)} {n(rayon)} 0 1 0 {n(2 * rayon)} 0a{n(rayon)} {n(rayon)} 0 1 0 {n(-2 * rayon)} 0"


def phylogenie(r, d):
    """Arbre binaire en éventail : chaque nœud se partage en deux le long d'un arc, les feuilles en points au
    pourtour, un clade à l'accent : évolution, phylogénie, spéciation."""
    nf, R = r.randint(26, 40), 84
    trou, debut = math.radians(r.uniform(30, 70)), r.uniform(0, 2 * math.pi)
    angle = lambda i: debut + trou / 2 + (2 * math.pi - trou) * (i + .5) / nf
    P = lambda a, rho: f"{n(100 + rho * math.cos(a))} {n(100 + rho * math.sin(a))}"
    segs, internes = [], []

    def pousse(lo, hi, rho):
        if hi - lo == 1:
            return angle(lo)
        k, angs = r.randint(lo + 1, hi - 1), []
        for a, b in ((lo, k), (k, hi)):
            rc = R if b - a == 1 else rho + (R - rho) * r.uniform(.1, .42)
            s0 = len(segs)
            ac = pousse(a, b, rc)
            segs.append((f"M{P(ac, rho)}L{P(ac, rc)}", rho))
            if b - a > 1:
                internes.append((b - a, s0, len(segs), a, b))
            angs.append(ac)
        segs.append((f"M{P(angs[0], rho)}A{n(rho)} {n(rho)} 0 {int(angs[1] - angs[0] > math.pi)} 1 {P(angs[1], rho)}", rho))
        return (angs[0] + angs[1]) / 2

    pousse(0, nf, r.uniform(5, 9))
    choix = [x for x in internes if 4 <= x[0] <= max(6, nf // 3)] or internes
    _, s0, s1, fa, fb = r.choice(choix)
    traits = defaultdict(list)
    for i, (chemin, rho) in enumerate(segs):
        w = round((1 + 1.6 * (1 - rho / R)) * 2) / 2
        traits[(ACC, w + .6) if s0 <= i < s1 else (ENCRE, w)].append(chemin)
    feuilles = defaultdict(list)
    for i in range(nf):
        a = angle(i)
        feuilles[(ACC, 4.6) if fa <= i < fb else (ENCRE, r.choice((2.4, 3.2, 4.2)))].append((100 + (R + 3) * math.cos(a), 100 + (R + 3) * math.sin(a)))
    return ([f'<path d="{"".join(v)}" stroke="{c}" stroke-width="{n(w)}"/>' for (c, w), v in sorted(traits.items(), key=lambda x: x[0][0] == ACC)]
            + [points(v, t, c) for (c, t), v in feuilles.items()] + [points([(100, 100)], 5, ENCRE)])


def division(r, d):
    """Un disque fendu en travers de son grand axe, chaque moitié fendue à son tour, les fentes de plus en plus fines,
    les morceaux arrondis en galets ; la plupart pleins, d'autres en contour, un à l'accent : division cellulaire,
    mitose, prolifération, partage."""
    def tranche(poly, f):
        out = []
        for i, p in enumerate(poly):
            q = poly[(i + 1) % len(poly)]
            fp, fq = f(p), f(q)
            if fp >= 0:
                out.append(p)
            if (fp >= 0) != (fq >= 0):
                t = fp / (fp - fq)
                out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
        return out

    def centre(poly):
        a = cx = cy = 0.0
        for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
            c = x0 * y1 - x1 * y0
            a, cx, cy = a + c, cx + (x0 + x1) * c, cy + (y0 + y1) * c
        return (cx / (3 * a), cy / (3 * a), abs(a) / 2) if a else (poly[0][0], poly[0][1], 0)

    def retrait(poly, e):
        """Le polygone convexe rentré de e de chaque côté."""
        cx, cy, _ = centre(poly)
        out = poly
        for p, q in zip(poly, poly[1:] + poly[:1]):
            lg = math.dist(p, q)
            if lg < 1e-6 or len(out) < 3:
                continue
            nx, ny = (p[1] - q[1]) / lg, (q[0] - p[0]) / lg
            if (cx - p[0]) * nx + (cy - p[1]) * ny < 0:
                nx, ny = -nx, -ny
            out = tranche(out, lambda z: (z[0] - p[0]) * nx + (z[1] - p[1]) * ny - e)
        return out

    pieces, fin = [], r.choice((5, 6, 6))

    def coupe(poly, prof):
        cx, cy, aire = centre(poly)
        if prof >= fin or (prof >= 3 and r.random() < .16) or aire < 40:
            pieces.append((poly, aire))
            return
        etendue = lambda a: max((p[0] - cx) * math.cos(a) + (p[1] - cy) * math.sin(a) for p in poly) \
            - min((p[0] - cx) * math.cos(a) + (p[1] - cy) * math.sin(a) for p in poly)
        a = max((k * math.pi / 12 for k in range(12)), key=etendue) + r.gauss(0, .15)
        ux, uy = math.cos(a), math.sin(a)
        off, g = r.gauss(0, .05) * etendue(a), 4.4 * .66 ** prof
        for s in (1, -1):
            moitie = tranche(poly, lambda p: s * ((p[0] - cx) * ux + (p[1] - cy) * uy - off))
            if len(moitie) >= 3:
                coupe([(x + s * g * ux, y + s * g * uy) for x, y in moitie], prof + 1)

    coupe([(100 + 80 * math.cos(2 * math.pi * k / 120), 100 + 80 * math.sin(2 * math.pi * k / 120)) for k in range(120)], 0)
    grands = sorted(range(len(pieces)), key=lambda i: -pieces[i][1])[:max(1, len(pieces) // 3)]
    ia, classes = r.choice(grands), defaultdict(list)
    for i, (poly, aire) in enumerate(pieces):
        rond_ = min(2.6, .3 + math.sqrt(aire) * .09)
        p = retrait(poly, rond_)
        if len(p) < 3:
            continue
        tirage = r.random()
        cle = "a" if i == ia else "p" if tirage < .72 or aire < 160 else "c" if tirage < .9 else "d"
        classes[(cle, round(rond_ * 2, 1))].append(trace(p) + "Z")
        creux = retrait(p, 1.5) if cle == "c" else []
        if len(creux) >= 3:
            classes[("f", round(rond_ * 2, 1))].append(trace(creux) + "Z")
    couleurs = {"p": ENCRE, "c": ENCRE, "f": FOND, "d": DOUX, "a": ACC}
    return [f'<path d="{"".join(v)}" fill="{couleurs[k]}" stroke="{couleurs[k]}" stroke-width="{n(w)}"/>'
            for (k, w), v in sorted(classes.items(), key=lambda x: "pcdfa".index(x[0][0]))]


def proies(r, d):
    """Orbites fermées en pointillé autour d'un point fixe, les points serrés là où le temps ralentit, une orbite à
    l'accent : proies et prédateurs, cycles de populations, écologie."""
    b, c, e = r.uniform(.7, 1.3), r.uniform(.7, 1.3), r.uniform(.6, 1.2)
    xe, ye = e / c, 1 / b
    f = lambda x, y: (x - b * x * y, c * x * y - e * y)

    def pas(x, y, h=.02):
        k1 = f(x, y)
        k2 = f(x + h / 2 * k1[0], y + h / 2 * k1[1])
        k3 = f(x + h / 2 * k2[0], y + h / 2 * k2[1])
        k4 = f(x + h * k3[0], y + h * k3[1])
        return x + h / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]), y + h / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])

    orbites = []
    for i in range(r.randint(6, 9)):
        x, y = xe * (1 + .28 * (i + 1) ** 1.35), ye
        pts, tour, prec = [(x, y)], 0.0, 0.0
        while tour < 2 * math.pi and len(pts) < 3000:
            for _ in range(4):
                x, y = pas(x, y)
            a = math.atan2(y - ye, x - xe)
            tour, prec = tour + abs(math.remainder(a - prec, 2 * math.pi)), a
            pts.append((x, y))
        orbites.append(pts)
    xs, ys = [p[0] for o in orbites for p in o], [p[1] for o in orbites for p in o]
    sx, sy = r.choice((1, -1)), r.choice((1, -1))
    X = lambda x: 100 + sx * (176 * (x - min(xs)) / (max(xs) - min(xs)) - 88)
    Y = lambda y: 100 - sy * (176 * (y - min(ys)) / (max(ys) - min(ys)) - 88)
    ka, out = r.randrange(len(orbites) // 2, len(orbites)), []
    for k, o in enumerate(orbites):
        garde = []
        for x, y in o:
            p = (X(x), Y(y))
            if not garde or math.dist(p, garde[-1]) > 1.3:
                garde.append(p)
        out.append(points(garde, 3.4 if k == ka else 2.1, ACC if k == ka else ENCRE))
    return out + [disque(X(xe), Y(ye), 4.2, ACC)]


def influx(r, d):
    """Rangées de tirets brefs, plus serrés par vagues ; une salve traverse les rangées en biais, à l'accent :
    neurones, potentiels d'action, influx nerveux, neurosciences."""
    k = r.randint(22, 32)
    pas = 184 / k
    h = pas * .32
    om, ph = r.uniform(.03, .07), r.uniform(0, 2 * math.pi)
    vagues = [(r.uniform(16, 184), r.uniform(3, 8)) for _ in range(r.randint(2, 4))]
    xa, pente = r.uniform(50, 150), r.uniform(-2.4, 2.4) * pas / 7
    encre, accent = [], []
    for i in range(k):
        y = 8 + pas * (i + .5)
        taux, part = r.uniform(.02, .09), [r.random() < .65 for _ in vagues]
        xi = xa + pente * (i - k / 2) + r.gauss(0, .7)
        accent.append(f"M{n(xi)} {n(y - h)}v{n(2 * h)}")
        x, dernier = 8.0, -9.0
        while x < 192:
            lam = taux * (1 + .75 * math.sin(om * x + ph)) + sum(.55 * math.exp(-((x - cv) / w) ** 2) for (cv, w), p in zip(vagues, part) if p)
            if x - dernier > 2.6 and abs(x - xi) > 3 and r.random() < lam * .5:
                encre.append(f"M{n(x)} {n(y - h)}v{n(2 * h)}")
                dernier = x
            x += .5
    return [f'<path d="{"".join(encre)}" stroke="{ENCRE}" stroke-width="1.25"/>',
            f'<path d="{"".join(accent)}" stroke="{ACC}" stroke-width="1.9"/>']


def clones(r, d):
    """Trame d'anneaux ouverts dans tous les sens ; autour d'un point, des anneaux à l'accent tournent tous leur
    ouverture vers lui : immunologie, sélection clonale, anticorps, reconnaissance."""
    s = r.uniform(15, 19)
    rho, ouv = s * .33, math.radians(r.uniform(60, 85))
    pos, j = [], 0
    while 8 + s * .5 + j * s * .866 <= 192 - s * .45:
        x = 8 + s * .5 + (s / 2 if j % 2 else 0)
        while x <= 192 - s * .45:
            pos.append((x, 8 + s * .5 + j * s * .866))
            x += s
        j += 1
    dx, dy = 100 - (min(p[0] for p in pos) + max(p[0] for p in pos)) / 2, 100 - (min(p[1] for p in pos) + max(p[1] for p in pos)) / 2
    pos = [(x + dx, y + dy) for x, y in pos]
    ia = r.choice([i for i, p in enumerate(pos) if math.dist(p, (100, 100)) < 52])
    ax, ay = pos[ia]
    rc = r.uniform(30, 46)
    P = lambda x, y, a: f"{n(x + rho * math.cos(a))} {n(y + rho * math.sin(a))}"
    encre, accent, vides = [], [], []
    for i, (x, y) in enumerate(pos):
        if i == ia:
            continue
        if r.random() < math.exp(-(math.dist((x, y), (ax, ay)) / rc) ** 2):
            g, cible = math.atan2(ay - y, ax - x), accent
        elif r.random() < .06:
            vides.append((x, y))
            continue
        else:
            g, cible = r.randrange(8) * math.pi / 4, encre
        cible.append(f"M{P(x, y, g + ouv / 2)}A{n(rho)} {n(rho)} 0 1 1 {P(x, y, g + 2 * math.pi - ouv / 2)}")
    return [f'<path d="{"".join(encre)}" stroke="{ENCRE}" stroke-width="1.6"/>', points(vides, 2, DOUX),
            f'<path d="{"".join(accent)}" stroke="{ACC}" stroke-width="2.6"/>', disque(ax, ay, rho * .62, ACC)]


# ---------- médecine et épidémiologie ----------

def contagion(r, d):
    """Semis de points où une contagion avance de proche en proche : le front à l'accent, derrière lui les points
    touchés et les liens de transmission, devant eux les points encore intacts : épidémie, propagation, infection."""
    pas = r.uniform(7.8, 9.2)
    noeuds = [(x + r.uniform(-1.5, 1.5), y + r.uniform(-1.5, 1.5)) for x, y in semis_dans(lambda x, y: True, pas, 10, 10, 190, 190)]
    m = len(noeuds)
    voisins = [[] for _ in range(m)]
    for i in range(m):
        for j in range(i + 1, m):
            if math.dist(noeuds[i], noeuds[j]) < pas * 1.45:
                voisins[i].append(j)
                voisins[j].append(i)
    beta, cible = r.uniform(.24, .4), r.uniform(.35, .55) * m
    for _ in range(8):
        gx, gy = r.uniform(45, 155), r.uniform(45, 155)
        graine = min(range(m), key=lambda i: math.dist(noeuds[i], (gx, gy)))
        quand, source, malades = {graine: 0}, {}, {graine: 3}
        t = 0
        while malades and len(quand) < cible:
            t += 1
            nouveaux = {}
            for i in malades:
                for j in voisins[i]:
                    if j not in quand and j not in nouveaux and r.random() < beta:
                        nouveaux[j] = i
            malades = {i: v - 1 for i, v in malades.items() if v > 1}
            for j, i in nouveaux.items():
                quand[j], source[j], malades[j] = t, i, r.randint(2, 4)
        if len(quand) > cible * .8:
            break
    liens, front = [], []
    for j, i in source.items():
        (front if j in malades else liens).append(f"M{n(noeuds[i][0])} {n(noeuds[i][1])}L{n(noeuds[j][0])} {n(noeuds[j][1])}")
    return [points([p for i, p in enumerate(noeuds) if i not in quand], 1.7, DOUX),
            f'<path d="{"".join(liens)}" stroke="{ENCRE}" stroke-width="0.8"/>',
            f'<path d="{"".join(front)}" stroke="{ACC}" stroke-width="1.2"/>',
            points([noeuds[i] for i in quand if i not in malades], 2.8, ENCRE),
            points([noeuds[i] for i in malades], 4.6, ACC), disque(*noeuds[graine], 4.2, ENCRE), disque(*noeuds[graine], 1.8, FOND)]


def sinogramme(r, d):
    """Bandes sinueuses de toutes amplitudes, de même période, qui se croisent et se tressent ; une bande à l'accent :
    imagerie médicale, tomographie, scanner, reconstruction."""
    k, tours = r.randint(9, 14), r.choice((1, 1.5, 2))
    ka, out = r.randrange(k), []
    for i in range(k):
        rho, phi = 74 * math.sqrt(r.uniform(.04, 1)), r.uniform(0, 2 * math.pi)
        brins = r.choice((1, 1, 2, 3, 4))
        acc = i == ka
        if acc:
            brins = max(brins, 3)
        d_ = "".join(trace([(8 + 184 * t / 120, 100 + rho * math.cos(2 * math.pi * tours * t / 120 - phi) + (j - (brins - 1) / 2) * 2.6)
                            for t in range(121)]) for j in range(brins))
        out.append((acc, f'<path d="{d_}" stroke="{ACC if acc else ENCRE}" stroke-width="{1.5 if acc else 1.05}"/>'))
    return [x for _, x in sorted(out, key=lambda x: x[0])]


def depistage(r, d):
    """Champ de points pleins et d'anneaux séparés par une fente courbe, le seuil ; près d'elle, ceux qui sont du
    mauvais côté à l'accent : dépistage, diagnostic, biomarqueurs, sensibilité et spécificité, médecine."""
    a = r.uniform(0, 2 * math.pi)
    ux, uy, vx, vy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    courbe, recouvre, seuil = r.uniform(-.007, .007), r.uniform(8, 14), r.uniform(-16, 16)
    score = lambda x, y: (x - 100) * ux + (y - 100) * uy + courbe * ((x - 100) * vx + (y - 100) * vy) ** 2
    pas = r.uniform(6.8, 7.8)
    sains, malades, faux_pos, faux_neg = [], [], [], []
    for x, y in semis_dans(lambda x, y: True, pas, 10, 10, 190, 190):
        x, y = x + r.uniform(-.8, .8), y + r.uniform(-.8, .8)
        s = score(x, y)
        if abs(s - seuil) < pas * .75:
            continue
        malade = r.random() < 1 / (1 + math.exp(-(s - seuil) / recouvre))
        if malade:
            (malades if s > seuil else faux_neg).append((x, y))
        else:
            (faux_pos if s > seuil else sains).append((x, y))
    return [points(sains, pas * .4, ENCRE), f'<path d="{"".join(rond(x, y, pas * .23) for x, y in malades)}" stroke="{ENCRE}" stroke-width="1.2"/>',
            points(faux_pos, pas * .5, ACC), f'<path d="{"".join(rond(x, y, pas * .26) for x, y in faux_neg)}" stroke="{ACC}" stroke-width="1.7"/>']


# ---------- informatique et IA ----------

def couches(r, d):
    """Colonnes de points reliées de l'une à l'autre par des faisceaux de courbes fines, quelques liens plus forts et
    un chemin à l'accent : réseaux de neurones, apprentissage profond, intelligence artificielle."""
    L = r.randint(4, 6)
    tailles = [r.randint(4, 7)] + [r.randint(7, 11) for _ in range(L - 2)] + [r.randint(2, 4)]
    X = lambda l: 16 + 168 * l / (L - 1)
    noeuds = []
    for l, m in enumerate(tailles):
        e = min(17, 168 / max(1, m - 1))
        noeuds.append([(X(l), 100 + (j - (m - 1) / 2) * e) for j in range(m)])
    chemin = [r.randrange(m) for m in tailles]
    doux, forts, acc = [], [], []
    for l in range(L - 1):
        for i, (x1, y1) in enumerate(noeuds[l]):
            for j, (x2, y2) in enumerate(noeuds[l + 1]):
                c = (x2 - x1) * .5
                p = f"M{n(x1)} {n(y1)}C{n(x1 + c)} {n(y1)} {n(x2 - c)} {n(y2)} {n(x2)} {n(y2)}"
                (acc if chemin[l] == i and chemin[l + 1] == j else forts if r.random() < .08 else doux).append(p)
    out = [f'<path d="{"".join(doux)}" stroke="{DOUX}" stroke-width="0.55"/>', f'<path d="{"".join(forts)}" stroke="{ENCRE}" stroke-width="1.1"/>',
           f'<path d="{"".join(acc)}" stroke="{ACC}" stroke-width="2.4"/>']
    for l, couche in enumerate(noeuds):
        for j, (x, y) in enumerate(couche):
            if chemin[l] == j:
                out.append(disque(x, y, 5.2, ACC))
            else:
                a = r.random()
                out.append(disque(x, y, 2.6 + 2.4 * a, ENCRE if a > .5 else FOND, None if a > .5 else ENCRE, 1.3))
    if r.random() < .5:
        out = ['<g transform="rotate(90 100 100)">'] + out + ["</g>"]
    return out


def grappes(r, d):
    """Nuages de points, chacun relié par des traits fins à son centre ; les centres à l'accent, avec le chemin
    qu'ils ont suivi pour s'y poser : apprentissage automatique, classification, partitionnement, données."""
    centres, essais = [], 0
    k = r.randint(5, 7)
    while len(centres) < k and essais < 800:
        essais += 1
        c = (r.uniform(30, 170), r.uniform(30, 170))
        if all(math.dist(c, q) > 48 for q in centres):
            centres.append(c)
    pts = []
    for cx, cy in centres:
        sx, sy, a = r.uniform(12, 22), r.uniform(7, 14), r.uniform(0, math.pi)
        for _ in range(r.randint(32, 56)):
            u, v = r.gauss(0, sx), r.gauss(0, sy)
            x, y = cx + u * math.cos(a) - v * math.sin(a), cy + u * math.sin(a) + v * math.cos(a)
            if 12 < x < 188 and 12 < y < 188:
                pts.append((x, y))
    cents = r.sample(pts, len(centres))
    traces = [[c] for c in cents]
    for _ in range(14):
        groupes = [[] for _ in cents]
        for p in pts:
            groupes[min(range(len(cents)), key=lambda i: math.dist(p, cents[i]))].append(p)
        cents = [(sum(p[0] for p in g) / len(g), sum(p[1] for p in g) / len(g)) if g else c for g, c in zip(groupes, cents)]
        for t, c in zip(traces, cents):
            if math.dist(t[-1], c) > .6:
                t.append(c)
    liens = "".join(f"M{n(p[0])} {n(p[1])}L{n(c[0])} {n(c[1])}" for g, c in zip(groupes, cents) for p in g)
    return ([f'<path d="{liens}" stroke="{DOUX}" stroke-width="0.7"/>', points(pts, 2.8, ENCRE)]
            + [f'<path d="{trace(t)}" stroke="{ACC}" stroke-width="1.2" stroke-dasharray="0 3.4"/>' for t in traces if len(t) > 1]
            + [points([p for t in traces for p in t[:-1]], 2.6, ACC)]
            + [x for c in cents for x in (disque(c[0], c[1], 6, ACC), disque(c[0], c[1], 2.2, FOND))])


def brassage(r, d):
    """Anneaux de bits brassés tour après tour ; un seul bit changé au centre gagne peu à peu, en spirale, une part
    de l'anneau, à l'accent : cryptographie, chiffrement, hachage, diffusion."""
    W, tours = r.choice((40, 48, 56)), r.randint(13, 17)
    r0, r1 = 18, 90
    pas, rot = (r1 - r0) / tours, r.choice((1, 2, 3, 5))
    cles = [[r.random() < .5 for _ in range(W)] for _ in range(tours)]
    bloc = r.choice((2, 3, 4))
    a = [(i // bloc) % 2 == 0 for i in range(W)]
    b = a[:]
    b[r.randrange(W)] ^= True

    def tour(x, k):
        y = [x[i] ^ (x[i - 1] and not x[(i + 1) % W]) for i in range(W)]
        y = y[-rot:] + y[:-rot]
        return [u ^ v for u, v in zip(y, cles[k])]

    dec, g = r.uniform(0, 2 * math.pi), .2 * math.pi / W
    P = lambda t, rr: f"{n(100 + rr * math.cos(t))} {n(100 + rr * math.sin(t))}"
    encre, accent = [], []
    for t in range(tours + 1):
        rr = r0 + t * pas
        for i in range(W):
            t0, t1 = dec + 2 * math.pi * i / W + g, dec + 2 * math.pi * (i + 1) / W - g
            arc_ = f"M{P(t0, rr)}A{n(rr)} {n(rr)} 0 0 1 {P(t1, rr)}"
            if a[i] != b[i]:
                accent.append(arc_)
            elif a[i]:
                encre.append(arc_)
        if t < tours:
            a, b = tour(a, t), tour(b, t)
    w = n(pas * .64, 2)
    return [f'<path d="{"".join(encre)}" stroke="{ENCRE}" stroke-width="{w}" stroke-linecap="butt"/>',
            f'<path d="{"".join(accent)}" stroke="{ACC}" stroke-width="{w}" stroke-linecap="butt"/>']


def tri(r, d):
    """Fils qui se croisent tour après tour jusqu'à se ranger du plus fin au plus épais ; un fil à l'accent :
    algorithmes, tri, permutations, ordre."""
    nn = r.randint(12, 18)
    perm = list(range(nn))
    r.shuffle(perm)
    etats, k = [perm[:]], 0
    while perm != sorted(perm) or len(etats) < 6:
        for i in range(k % 2, nn - 1, 2):
            if perm[i] > perm[i + 1]:
                perm[i], perm[i + 1] = perm[i + 1], perm[i]
        etats.append(perm[:])
        k += 1
    T = len(etats) - 1
    X, Y = (lambda p: 14 + 172 * p / (nn - 1)), (lambda t: 12 + 176 * t / T)
    dy = 176 / T / 2
    chemins = {}
    for v in range(nn):
        pos = [e.index(v) for e in etats]
        chemins[v] = f"M{n(X(pos[0]))} {n(Y(0))}" + "".join(
            f"C{n(X(pos[t]))} {n(Y(t) + dy)} {n(X(pos[t + 1]))} {n(Y(t + 1) - dy)} {n(X(pos[t + 1]))} {n(Y(t + 1))}" for t in range(T))
    va = max(range(nn // 2, nn), key=lambda v: abs(etats[0].index(v) - v) + r.random())
    out = []
    for v in sorted(range(nn), key=lambda v: (v == va, -v)):
        w = .7 + 3.3 * v / (nn - 1)
        out += [f'<path d="{chemins[v]}" stroke="{FOND}" stroke-width="{n(w + 2.6, 2)}"/>',
                f'<path d="{chemins[v]}" stroke="{ACC if v == va else ENCRE}" stroke-width="{n(w, 2)}"/>']
    return out


# ---------- ingénierie ----------

def decale(chemin, o):
    """Polyligne parallèle à une autre, à la distance o (à gauche du sens de parcours), sommets en onglet."""
    normale = lambda p, q: ((p[1] - q[1]) / math.dist(p, q), (q[0] - p[0]) / math.dist(p, q))
    out = []
    for i, (x, y) in enumerate(chemin):
        ns = ([normale(chemin[i - 1], chemin[i])] if i else []) + ([normale(chemin[i], chemin[i + 1])] if i < len(chemin) - 1 else [])
        if len(ns) == 1:
            (nx, ny), k = ns[0], 1
        else:
            nx, ny = ns[0][0] + ns[1][0], ns[0][1] + ns[1][1]
            k = 1 / (1 + ns[0][0] * ns[1][0] + ns[0][1] * ns[1][1])
        out.append((x + o * nx * k, y + o * ny * k))
    return out


def pistes(r, d):
    """Bandes de pistes parallèles parties de pastilles en escalier, qui obliquent à 45 degrés, sur une trame de
    points ; une piste à l'accent : électronique, circuits, semi-conducteurs."""
    K = r.choice((3, 3, 4))
    bande, sp = 184 / K, 4.4
    encre, accent, pastilles, pa = [], [], [], []
    ka = r.randrange(K)
    for b in range(K):
        m = r.randint(max(6, int((bande - 18) / sp) - 3), max(6, min(12, int((bande - 18) / sp))))
        demi = (m - 1) * sp / 2
        haut, bas = 8 + b * bande + demi + 4, 8 + (b + 1) * bande - demi - 4
        y = r.uniform(haut, bas)
        x0 = r.uniform(12, 40) + (m - 1) * 2.6
        chemin, x = [(x0, y)], x0 + 30 + r.uniform(4, 24)
        for _ in range(r.randint(1, 3)):
            y2 = r.uniform(haut, bas)
            if abs(y2 - y) < 6 or x + abs(y2 - y) > 178:
                continue
            chemin += [(x, y), (x + abs(y2 - y), y2)]
            x, y = x + abs(y2 - y) + r.uniform(8, 28), y2
        chemin.append((192, y))
        miroir, sens = r.random() < .5, r.choice((1, -1))
        ja = r.randrange(m) if b == ka else -1
        for j in range(m):
            ligne = decale(chemin, (j - (m - 1) / 2) * sp)
            ligne[0] = (x0 + sens * (j - (m - 1) / 2) * 5.2, ligne[0][1])
            if miroir:
                ligne = [(200 - x_, y_) for x_, y_ in ligne]
            (accent if j == ja else encre).append(trace(ligne))
            (pa if j == ja else pastilles).append(ligne[0])
    fond = [(x, y) for x in range(12, 190, 8) for y in range(12, 190, 8)]
    return ([points(fond, 1.2, DOUX), f'<path d="{"".join(encre)}" stroke="{ENCRE}" stroke-width="1.5"/>',
             f'<path d="{"".join(accent)}" stroke="{ACC}" stroke-width="2.2"/>']
            + [disque(x, y, 2.4, FOND, ENCRE, 1.4) for x, y in pastilles] + [disque(x, y, 3.2, ACC) for x, y in pa])


def harmoniques(r, d):
    """Rangées d'ondes en hachures, de la fondamentale aux harmoniques de plus en plus fines, et au bout leur somme à
    l'accent : traitement du signal, séries de Fourier, filtrage, spectre."""
    sorte = r.choice(("carre", "scie", "triangle"))
    rangs = {"carre": [1, 3, 5, 7, 9, 11, 13], "scie": [1, 2, 3, 4, 5, 6, 7], "triangle": [1, 3, 5, 7, 9, 11]}[sorte]
    rangs = rangs[:r.randint(5, len(rangs))]
    coef = lambda k: (1 / k ** 2 if sorte == "triangle" else 1 / k) * (-1 if (sorte == "scie" and k % 2 == 0) or (sorte == "triangle" and k % 4 == 3) else 1)
    cycles, ph = r.choice((1.5, 2, 2.5)), r.uniform(0, 2 * math.pi)
    K = len(rangs)
    pas = 184 / (K + 1.7)
    xs = [8 + 2.3 * i for i in range(int(184 / 2.3) + 1)]
    u = lambda x: 2 * math.pi * cycles * (x - 8) / 184 + ph
    somme = [sum(coef(k) * math.sin(k * u(x)) for k in rangs) for x in xs]
    smax = max(abs(s) for s in somme)
    haut = r.random() < .5
    out = []
    for i, k in enumerate(rangs):
        y0 = 8 + pas * (i + .5) + (pas * 1.7 if haut else 0)
        a = pas * .46 * abs(coef(k)) ** .45
        out.append("".join(f"M{n(x)} {n(y0)}V{n(y0 - a * math.copysign(1, coef(k)) * math.sin(k * u(x)))}" for x in xs))
    y0 = 8 + pas * .85 if haut else 8 + pas * (K + .85)
    acc = "".join(f"M{n(x)} {n(y0)}V{n(y0 - pas * .8 * s / smax)}" for x, s in zip(xs, somme))
    return [f'<path d="{"".join(out)}" stroke="{ENCRE}" stroke-width="1.1"/>', f'<path d="{acc}" stroke="{ACC}" stroke-width="1.3"/>']


def rubans(r, d):
    """Fils parallèles venus de quelques sources, réunis en un ruban dont des faisceaux se détachent en quarts de
    cercle ; ce qui reste va au bout, à l'accent : énergie, rendement, pertes, bilans."""
    N, sp = r.randint(30, 42), 2.8
    H = (N - 1) * sp
    yb = max(16.0, min(184 - H, r.uniform(84, 112) - H / 2))
    S = r.randint(2, 4)
    coupes = sorted(r.sample(range(3, N - 3), S - 1))
    tailles = [b - a for a, b in zip([0] + coupes, coupes + [N])]
    reste = 176 - (N - S) * sp
    ecarts = [r.uniform(.5, 1.5) for _ in range(S - 1)]
    ysrc, y = [], 12.0
    for g, t in enumerate(tailles):
        ysrc += [y + q * sp for q in range(t)]
        y += (t - 1) * sp + (reste * ecarts[g] / sum(ecarts) if g < S - 1 else 0)
    xm = r.uniform(46, 66)
    yband = [yb + j * sp for j in range(N)]
    debut = [f"M8 {n(ysrc[j])}C{n((8 + xm) / 2)} {n(ysrc[j])} {n((8 + xm) / 2)} {n(yband[j])} {n(xm)} {n(yband[j])}" for j in range(N)]
    lo, hi, x, fins = 0, N, xm + r.uniform(8, 24), {}
    while hi - lo > N * .3 and x < 168:
        np_ = r.randint(3, max(3, (hi - lo) // 4))
        rmin = r.uniform(5, 10)
        if r.random() < .5:
            cy = yband[hi - 1] + rmin
            for j in range(hi - np_, hi):
                rho = cy - yband[j]
                fins[j] = f"L{n(x)} {n(yband[j])}A{n(rho)} {n(rho)} 0 0 1 {n(x + rho)} {n(cy)}V192"
            hi -= np_
        else:
            cy = yband[lo] - rmin
            for j in range(lo, lo + np_):
                rho = yband[j] - cy
                fins[j] = f"L{n(x)} {n(yband[j])}A{n(rho)} {n(rho)} 0 0 0 {n(x + rho)} {n(cy)}V8"
            lo += np_
        x += rmin + (np_ - 1) * sp + r.uniform(8, 26)
    encre = "".join(debut[j] + fins[j] for j in fins)
    accent = "".join(debut[j] + "H192" for j in range(N) if j not in fins)
    return [f'<path d="{encre}" stroke="{ENCRE}" stroke-width="1.1"/>', f'<path d="{accent}" stroke="{ACC}" stroke-width="1.3"/>']


def poses(r, d):
    """Une chaîne de segments articulés saisie à intervalles réguliers, comme en chronophotographie ; la dernière
    pose à l'accent, le chemin du bout en pointillé : robotique, cinématique, bras manipulateur."""
    for _ in range(12):
        nl = r.choice((3, 4))
        L = sorted((r.uniform(.55, 1) for _ in range(nl)), reverse=True)
        th0 = [r.uniform(-math.pi, math.pi)] + [r.uniform(-1.1, 1.1) for _ in range(nl - 1)]
        A = [r.uniform(.4, .9)] + [r.uniform(.5, 1.2) for _ in range(nl - 1)]
        f, ph = [r.choice((.5, 1, 1)) for _ in range(nl)], [r.uniform(0, 2 * math.pi) for _ in range(nl)]

        def pose(t):
            x = y = a = 0.0
            pts = [(0.0, 0.0)]
            for i in range(nl):
                a += th0[i] + A[i] * math.sin(2 * math.pi * f[i] * t + ph[i])
                x, y = x + L[i] * math.cos(a), y + L[i] * math.sin(a)
                pts.append((x, y))
            return pts

        chemin = [pose(.55 * u / 200)[-1] for u in range(201)]
        if sum(math.dist(p, q) for p, q in zip(chemin, chemin[1:])) > 1.3 * sum(L):
            break
    F = r.randint(13, 20)
    cadres = [pose(.55 * i / (F - 1)) for i in range(F)]
    tout = [p for c in cadres for p in c] + chemin
    xs, ys = [p[0] for p in tout], [p[1] for p in tout]
    e = 168 / max(max(xs) - min(xs), max(ys) - min(ys))
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    M = lambda p: (100 + (p[0] - cx) * e, 100 + (p[1] - cy) * e)
    cadres = [[M(p) for p in c] for c in cadres]
    return ([f'<path d="{trace([M(p) for p in chemin])}" stroke="{DOUX}" stroke-width="1.4" stroke-dasharray="0 3.4"/>',
             f'<path d="{"".join(trace(c) for c in cadres[:-1])}" stroke="{ENCRE}" stroke-width="0.9"/>',
             points([p for c in cadres[:-1] for p in c[1:]], 2.6, ENCRE), trait(cadres[-1], ACC, 2.6)]
            + [disque(x, y, 3, FOND, ACC, 1.8) for x, y in cadres[-1][1:]] + [disque(*cadres[0][0], 6, ENCRE)])


# ---------- sciences humaines et sociales ----------

def volatilite(r, d):
    """Faisceau de marches aléatoires parties d'un même point, qui s'évase vers la droite entre deux tirets ; un
    chemin à l'accent : économie, finance, marchés, prévision, incertitude."""
    y0, mu, sig = r.uniform(84, 116), r.uniform(-.16, .16), r.uniform(2.6, 3.3)
    doux, encre, bouts, chemins = [], [], [], []
    for _ in range(r.randint(26, 38)):
        y, pts = y0, [(8, y0)]
        for x in range(10, 193, 2):
            y += -mu * 2 + r.gauss(0, sig * math.sqrt(2))
            if not 8 < y < 192:
                break
            pts.append((x, y))
        chemins.append(pts)
    finis = [c for c in chemins if c[-1][0] >= 192]
    ca = r.choice(finis) if finis else max(chemins, key=len)
    for c in chemins:
        if c is not ca:
            (encre if r.random() < .3 else doux).append(trace(c))
            if c[-1][0] >= 192:
                bouts.append(c[-1])
    env = [[(x, y0 - mu * (x - 8) + s * 1.7 * sig * math.sqrt(x - 8)) for x in range(8, 193, 2)] for s in (-1, 1)]
    return ([f'<path d="{"".join(doux)}" stroke="{DOUX}" stroke-width="0.8"/>', f'<path d="{"".join(encre)}" stroke="{ENCRE}" stroke-width="1"/>']
            + [f'<path d="{morceaux(e)}" stroke="{ENCRE}" stroke-width="1.2" stroke-dasharray="3 2.6"/>' for e in env]
            + [points(bouts, 2.8, ENCRE), trait(ca, ACC, 2.2), points([ca[-1]], 6, ACC), points([(8, y0)], 6, ENCRE)])


def schelling(r, d):
    """Grille de points pleins et d'anneaux qui, chacun cherchant assez de voisins pareils, se regroupent en plaques ;
    les derniers à bouger à l'accent : sociologie, ségrégation, quartiers, voisinage."""
    c = r.randint(17, 23)
    s, tol = 184 / c, r.uniform(.4, .62)
    cases = [r.choices((1, 2, 0), (.45, .45, .1))[0] for _ in range(c * c)]
    vois = [[(i + di) * c + j + dj for di in (-1, 0, 1) for dj in (-1, 0, 1) if (di or dj) and 0 <= i + di < c and 0 <= j + dj < c]
            for i in range(c) for j in range(c)]

    def content(i):
        v = [cases[j] for j in vois[i] if cases[j]]
        return not v or sum(x == cases[i] for x in v) / len(v) >= tol

    vides, derniers = [i for i in range(c * c) if not cases[i]], []
    for _ in range(80):
        mecontents = [i for i in range(c * c) if cases[i] and not content(i)]
        if not mecontents:
            break
        r.shuffle(mecontents)
        derniers = []
        for i in mecontents:
            if not cases[i] or content(i):
                continue
            k = r.randrange(len(vides))
            j = vides[k]
            cases[j], cases[i], vides[k] = cases[i], 0, i
            derniers.append(j)
    acc = set(derniers[:6]) if derniers else set(r.sample([i for i in range(c * c) if cases[i]], 3))
    P = lambda i: (8 + s * (i % c + .5), 8 + s * (i // c + .5))
    return [points([P(i) for i in range(c * c) if cases[i] == 1 and i not in acc], s * .62, ENCRE),
            f'<path d="{"".join(rond(*P(i), s * .24) for i in range(c * c) if cases[i] == 2 and i not in acc)}" stroke="{ENCRE}" stroke-width="{n(s * .13, 2)}"/>',
            points([P(i) for i in acc], s * .62, ACC)]


def pyramide(r, d):
    """Rangées de points de part et d'autre d'un axe vide, plus longues ou plus courtes selon les générations, qui
    s'amenuisent vers le haut ; une génération à l'accent : démographie, population, pyramide des âges."""
    k = r.randint(28, 36)
    p = 184 / k
    bosses = [(r.uniform(10, 85), r.uniform(3, 9), r.uniform(-.35, .4)) for _ in range(r.randint(2, 4))]
    tendance, forme = r.uniform(-.5, .7), r.uniform(4, 7)
    naiss = lambda a: max(.15, 1 - tendance * (.5 - a / 100) + sum(h * math.exp(-((a - c) / w) ** 2) for c, w, h in bosses))
    vals = [(naiss(a) * math.exp(-(a / 80) ** forme), naiss(a) * math.exp(-(a / 86) ** forme)) for a in (100 * (i + .5) / k for i in range(k))]
    vmax = max(max(v) for v in vals)
    ia = max(range(2, k - 6), key=lambda i: sum(vals[i]) + r.uniform(0, .3))
    classes = defaultdict(list)
    for i, (h, f) in enumerate(vals):
        y = 192 - p * (i + .5)
        for cote, v in ((-1, h), (1, f)):
            nb = 84 * v / vmax / p
            for j in range(int(nb) + 1):
                t = min(1.0, nb - j)
                if t > .2:
                    classes[(ACC if i == ia else ENCRE, round(p * .66 * (1 if t >= 1 else .4 + .6 * t), 1))].append((100 + cote * (2.6 + p * (j + .5)), y))
    return [points(v, t, c) for (c, t), v in classes.items()]


def frise(r, d):
    """Couloirs de traits de toutes longueurs, comme des vies sur une frise, plus serrés à certaines époques et
    prolongés de pointillés quand leurs bouts sont incertains ; un trait à l'accent : histoire, chronologie."""
    nv = r.randint(14, 20)
    pas = 176 / (nv - 1)
    epoques = [(r.uniform(.12, .88), r.uniform(.07, .16)) for _ in range(r.randint(1, 3))]
    dense = lambda u: .15 + sum(math.exp(-((u - c) / w) ** 2) for c, w in epoques)
    spans = []
    for v in range(nv):
        u = r.uniform(-.1, .3)
        while u < .97:
            l = min(.5, r.lognormvariate(math.log(.12), .55))
            if min(1.0, u + l) - max(0.0, u) > .025:
                spans.append((v, max(0.0, u), min(1.0, u + l)))
            u += l + r.uniform(.02, .08) / dense(u + l)
    ia = max(range(len(spans)), key=lambda i: spans[i][2] - spans[i][1] + r.uniform(0, .08))
    X = lambda u: 12 + 176 * u
    debuts, epais, minces, pointilles = [], [], [], []
    for i, (v, s, e) in enumerate(spans):
        if i == ia:
            continue
        y = 12 + v * pas
        (epais if r.random() < .16 else minces).append(f"M{n(X(s))} {n(y)}H{n(X(e))}")
        if r.random() < .25 and e < .96:
            pointilles.append(f"M{n(X(e) + 3)} {n(y)}h{n(r.uniform(5, 12))}")
        if r.random() < .2 and s > .04:
            pointilles.append(f"M{n(X(s) - 3)} {n(y)}h{n(-r.uniform(5, 12))}")
        if s > 0:
            debuts.append((X(s), y))
    v, s, e = spans[ia]
    ya = 12 + v * pas
    return [f'<path d="{"".join(pointilles)}" stroke="{DOUX}" stroke-width="1.6" stroke-dasharray="0 3"/>',
            f'<path d="{"".join(minces)}" stroke="{ENCRE}" stroke-width="1.5"/>',
            f'<path d="{"".join(epais)}" stroke="{ENCRE}" stroke-width="3.6"/>', points(debuts, 3.6, ENCRE),
            trait([(X(s), ya), (X(e), ya)], ACC, 3.8), points([(X(s), ya), (X(e), ya)], 6.6, ACC)]


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
    # ---------- sciences du vivant, médecine, informatique, ingénierie, sciences humaines ----------
    "Sciences du vivant": {
        "phylogenie": ("arbre binaire en éventail, un clade à l'accent", "phylogén*, évolution des espèces, évolution biologique, theory of evolution, evolutionary, évolutionn*, spéciation, speciation, cladisti*, cladogram*, clade*, taxonomi*, darwin*, sélection naturelle, natural selection, ancêtre commun, common ancestor, arbre du vivant, tree of life, paléontolog*, paleontolog*, génétique des populations, population genetics"),
        "division": ("disque fendu et refendu en galets", "division cellulaire, cell division, mitose, mitosis, méiose, meiosis, cycle cellulaire, cell cycle, prolifération, proliferation, biologie cellulaire, cell biology, cytolog*, embryo*, développement embryonnaire, cellule souche, cellules souches, stem cell*, cancer*, tumeur*, tumor*, tumour*, oncolog*, cancérolog*"),
        "proies": ("orbites fermées en pointillé autour d'un point", "proie*, prey, prédat*, lotka, volterra, lotka-volterra, dynamique des populations, population dynamics, écologie des populations, population ecology, écosystème*, ecosystem*, chaîne alimentaire, chaînes alimentaires, food web*, food chain*, réseau trophique, réseaux trophiques, trophique*, trophic, compétition interspécifique, interspecific competition"),
        "influx": ("rangées de tirets brefs, une salve en biais", "neuro*, synap*, potentiel d'action, potentiels d'action, action potential*, spike*, influx nerveux, nerve impulse*, système nerveux, nervous system, cortex, cortical, cerveau, brain, électrophysiolog*, eeg, plasticité synaptique, synaptic plasticity"),
        "clones": ("anneaux ouverts, tournés vers un point", "immun*, anticorps, antibod*, antigen*, lymphocyte*, vaccin*, sélection clonale, clonal selection, clonal*, inflammat*, allerg*, pathogène*, pathogen*, globules blancs, white blood cell*, auto-immun*, autoimmun*"),
    },
    "Médecine et épidémiologie": {
        "contagion": ("semis où une contagion avance de proche en proche", "épidémi*, contagi*, infecti*, pandémi*, modèle sir, sir model, seir, r0, virus, viral, virale*, transmission virale, chaîne de transmission, disease transmission, outbreak*, santé publique, public health, covid*, grippe, influenza, quarantaine, quarantine"),
        "depistage": ("points et anneaux de part et d'autre d'une fente", "dépistage*, screening, diagnos*, biomarqueur*, biomarker*, spécificité, specificity, sensibilité et spécificité, sensitivity and specificity, faux positif*, faux négatif*, false positive*, false negative*, courbe roc, roc curve, test diagnostique, tests diagnostiques, médecine, medicine, médical*, clinique*, clinic*, patient*, santé, health, hôpita*, hospital*, épidémiologie clinique, clinical epidemiology"),
        "sinogramme": ("bandes sinueuses qui se tressent", "imagerie médicale, medical imaging, imagerie par résonance, irm, mri, scanner*, tomograph*, tomodensitom*, ct scan*, radiolog*, radiograph*, échograph*, ultrasound, ultrason*, transformée de radon, radon transform, reconstruction tomographique, tomographic reconstruction, rétroprojection, backprojection"),
    },
    "Informatique et IA": {
        "couches": ("colonnes de points reliées par des faisceaux", "réseau de neurones, réseaux de neurones, neural net*, deep learning, apprentissage profond, perceptron*, couches cachées, hidden layer*, intelligence artificielle, artificial intelligence, ia, llm*, grands modèles de langage, large language model*, rétropropagation, backpropagation, descente de gradient, gradient descent, réseau convolutif, réseaux convolutifs, convolutional, transformer architecture"),
        "grappes": ("nuages de points tirés vers leurs centres", "apprentissage automatique, machine learning, apprentissage statistique, statistical learning, apprentissage supervisé, apprentissage non supervisé, supervised learning, unsupervised learning, clustering, k-means, k-moyennes, partitionnement, classifieur*, classifier*, classification supervisée, fouille de données, data mining, science des données, data science, big data, mégadonnées, données massives, regroupement*"),
        "brassage": ("anneaux de bits, un écart qui gagne en spirale", "cryptograph*, cryptolog*, cryptanaly*, chiffrement*, encrypt*, déchiffr*, decrypt*, cipher*, hachage, hash*, aes, rsa, clé publique, clés publiques, public key*, cybersécurité, cybersecurity, sécurité informatique, computer security, blockchain*, signature numérique, digital signature*, cryptomonnaie*, cryptocurrenc*"),
        "tri": ("fils croisés qui se rangent du fin à l'épais", "algorithmique, algorithme de tri, algorithmes de tri, sorting, tri, tri rapide, quicksort, tri fusion, merge sort, complexité algorithmique, computational complexity, structures de données, structure de données, data structure*, ordonnancement, scheduling, récursi*"),
    },
    "Ingénierie": {
        "pistes": ("bandes de pistes à 45 degrés, pastilles en escalier", "électronique numérique, électronique analogique, électronique de puissance, power electronics, electronics, composants électroniques, electronic components, circuits électroniques, electronic circuit*, systèmes embarqués, embedded system*, circuit*, circuit imprimé, circuits imprimés, printed circuit*, pcb, transistor*, semi-conducteur*, semiconductor*, microcontrôleur*, microcontroller*, microprocesseur*, microprocessor*, puce*, chip*, vlsi, fpga, cmos, hardware, digital electronics, conception de circuits, circuit design"),
        "harmoniques": ("rangées d'ondes en hachures et leur somme", "traitement du signal, signal processing, série de fourier, séries de fourier, fourier series, analyse de fourier, fourier analysis, transformée de fourier, fourier transform, fft, harmoniques, harmonics, filtrage, filtering, filtre numérique, filtres numériques, digital filter*, filtre passe-bas, low-pass, convolution*, ondelette*, wavelet*, échantillonnage, sampling, nyquist, modulation*, analyse spectrale, spectral analysis, audio"),
        "rubans": ("fils réunis en ruban, des faisceaux qui s'en détachent", "énergétique*, systèmes énergétiques, energy systems, efficacité énergétique, rendement énergétique, energy efficiency, sankey, bilan énergétique, bilans énergétiques, energy balance, transition énergétique, energy transition, mix énergétique, energy mix, réseau électrique, power grid, production d'électricité, electricity generation, énergies renouvelables, énergie renouvelable, stockage de l'énergie, energy storage, renouvelable*, renewable*, centrale électrique, centrales électriques, power plant*, cogénération, cogeneration, photovolta*, éolien*, wind power, énergie solaire, solar energy, solar power"),
        "poses": ("chaîne articulée saisie pose après pose", "robot*, cinématique des robots, cinématique inverse, inverse kinematics, chaîne cinématique, kinematic chain*, bras manipulateur, bras robotisé, robot arm*, manipulateur*, manipulator*, mécatronique, mechatronic*, actionneur*, actuator*, degrés de liberté, degrees of freedom, cobot*, drone*, automatisme*, locomotion, biomécanique, biomechanic*, mouvement humain, human motion"),
    },
    "Sciences humaines et sociales": {
        "volatilite": ("faisceau de marches aléatoires qui s'évase", "économi*, economy, finance*, financi*, bourse*, stock market*, marchés financiers, marché financier, financial market*, volatilité des marchés, volatilité financière, market volatility, spéculat*, speculat*, cours de bourse, taux d'inflation, inflation rate, monnaie*, monétaire*, monetary, crise financière, financial crisis, macroéconomi*, microéconomi*, investissement*, investment*, trading"),
        "schelling": ("points et anneaux qui se regroupent en plaques", "sociolog*, ségrégation spatiale, ségrégation urbaine, ségrégation sociale, ségrégation résidentielle, residential segregation, racial segregation, schelling, mixité sociale, social mix, quartier*, urbain*, urban*, ville*, city, cities, inégalités sociales, social inequalit*, inégalités de revenu, income inequalit*, societ*, communaut*, communit*, sciences sociales, social science*, discrimination*, ghetto*, gentrification, sciences politiques, political science, élection*, vote*, opinion*"),
        "pyramide": ("rangées de points de part et d'autre d'un axe", "démograph*, population*, pyramide des âges, age pyramid*, population pyramid*, natalité, birth rate*, mortalité, mortality, fécondité, fertility, vieillissement de la population, vieillissement démographique, population ageing, population aging, cohort*, recensement*, census, espérance de vie, life expectancy, générations, baby-boom, baby boom, transition démographique, demographic transition"),
        "frise": ("couloirs de traits comme des vies sur une frise", "histoire, history, histori*, chronolog*, frise*, timeline*, siècle*, century, centuries, époque moderne, époque contemporaine, early modern, dynasti*, dynasty, reign*, archive*, antiquité, antiquity, moyen âge, moyen-âge, middle ages, médiéval*, medieval, renaissance, révolution française, french revolution, révolution industrielle, industrial revolution, guerre*, war, empire*, généalog*, genealog*, biograph*, mémoire collective"),
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
# sciences du vivant, médecine, informatique, ingénierie, sciences humaines
ALIAS.update({"phylogenetique": "phylogenie", "mitose": "division", "lotka": "proies", "predateurs": "proies", "neurones": "influx",
              "raster": "influx", "immunite": "clones", "anticorps": "clones", "epidemie": "contagion", "sir": "contagion",
              "diagnostic": "depistage", "tomographie": "sinogramme", "irm": "sinogramme", "perceptron": "couches", "kmeans": "grappes",
              "clusters": "grappes", "chiffrement": "brassage", "crypto": "brassage", "permutation": "tri", "circuits": "pistes",
              "electronique": "pistes", "fourier": "harmoniques", "sankey": "rubans", "energie": "rubans", "robot": "poses",
              "robotique": "poses", "bourse": "volatilite", "finance": "volatilite", "segregation": "schelling",
              "demographie": "pyramide", "ages": "pyramide", "chronologie": "frise", "histoire": "frise"})


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
