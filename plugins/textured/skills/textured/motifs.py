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
        "geodesiques": ("quadrillage creusé par une ou deux masses", "relativité, relativiste*, espace-temps, gravitation*, géodésique*, einstein, trou noir, trous noirs, lentille gravitationnelle, ondes gravitationnelles, relativity, relativistic, spacetime, space-time, gravit*, geodesic*, black hole*, gravitational lensing, gravitational waves"),
        "ising": ("réseau de spins en domaines, parois à l'accent", "physique statistique, mécanique statistique, ising, transition de phase, transitions de phase, magnétisme, ferromagnét*, spins, entropie, statistical physics, statistical mechanics, phase transition*, magnetism, ferromagnet*, entropy, monte carlo"),
        "galaxie": ("spirale de points inclinée, bulbe dense, quelques étoiles à l'accent", "galax*, astrophysi*, étoile*, stellaire*, voie lactée, nébuleuse*, astronomie, télescope*, astrophysics, stars, stellar, milky way, nebula*, astronomy, telescope*"),
        "cosmique": ("toile de filaments entre des nœuds denses", "cosmolog*, univers, big bang, matière noire, énergie noire, grandes structures, fond diffus cosmologique, inflation cosmique, expansion de l'univers, cosmology, universe, dark matter, dark energy, large-scale structure, cosmic web, cosmic microwave background, cmb"),
    },
    "Terre et climat": {
        "plissement": ("couches plissées en bandes, rejetées par une faille", "géologie, géologique*, strate*, stratigraph*, sédiment*, tectonique*, plis, faille*, roche*, minéralog*, geology, geological, stratigraphy, sediment*, tectonic*, folds, faults, rocks, mineralog*"),
        "sismogramme": ("traces secouées par deux arrivées alignées sur une hyperbole", "sismolog*, séisme*, sismique*, tremblement de terre, tremblements de terre, ondes sismiques, géophysique, sismographe*, seismolog*, earthquake*, seismic, geophysic*, seismograph*"),
        "gyres": ("cellules de circulation, lignes de courant fermées en tirets", "océanograph*, océan*, courants marins, courant marin, courants océaniques, circulation océanique, marée*, gyre*, tourbillon*, oceanograph*, ocean*, ocean currents, ocean circulation, tides, eddies, eddy, vortex, vortices"),
        "isobares": ("lignes de niveau serrées autour de creux et de bosses", "météorolog*, météorologie dynamique, météo, pression atmosphérique, isobare*, dépression atmosphérique, anticyclone*, cyclone*, front froid, fronts froids, vent, vents, prévision météorologique, meteorolog*, weather, atmospheric pressure, isobar*, wind, winds, weather forecast*, dynamic meteorology"),
        "rechauffement": ("bandes verticales froides puis chaudes", "climat*, réchauffement, changement climatique, températures mondiales, anomalies climatiques, giec, gaz à effet de serre, effet de serre, climate, global warming, climate change, global temperature*, ipcc, greenhouse gas*, greenhouse effect, warming stripes"),
    },
    "Mathématiques": {
        "isoclines": ("champ de pentes en tirets, courbes intégrales", "équations différentielles, équation différentielle, edo, champ de pentes, isocline*, analyse mathématique, analyse réelle, intégrale*, dérivée*, calcul différentiel, differential equation*, ode, odes, slope field, calculus, integral*, derivative*, real analysis"),
        "attracteur": ("nuage d'un attracteur étrange", "systèmes dynamiques, système dynamique, chaos, chaotique*, attracteur*, bifurcation*, lorenz, dynamical system*, chaos theory, chaotic, attractor*, strange attractor"),
        "modulo": ("cordes d'une table modulo sur un cercle", "algèbre, algébrique*, théorie des groupes, groupes finis, arithmétique modulaire, modulo, congruence*, corps finis, cyclique*, algebra*, group theory, finite groups, modular arithmetic, finite field*, cyclic"),
        "galton": ("clous en quinconce, billes en cloche", "probabilit*, aléatoire*, hasard, loi binomiale, loi normale, variable aléatoire, variables aléatoires, processus stochastique*, galton, probability, probabilities, randomness, binomial*, normal distribution, random variable*, stochastic*"),
        "entrelacs": ("nœud torique en ruban, passages dessus-dessous", "topolog*, théorie des nœuds, entrelacs, tresse*, tore, homotopie, homologie, invariant*, variétés, knot theory, knots, braid*, torus, homotopy, homology, manifold*"),
        "ulam": ("spirale d'Ulam : les nombres premiers en points", "théorie des nombres, nombre premier, nombres premiers, arithmétique, nombres entiers, crible, ulam, riemann, number theory, prime number*, primes, integers, sieve, primality"),
    },
    "Chimie générale": {
        "raies": ("bandes de raies qui se resserrent vers une limite", "spectroscop*, spectre*, raie*, émission, absorption atomique, infrarouge, uv-visible, rmn, raman, fluorescence, spectroscopy, spectrum, spectra, spectral line*, emission spectrum, infrared, nmr"),
        "electrode": ("couche serrée contre une paroi, mélange au loin", "électrochim*, électrode*, électrolyse, électrolyte*, pile à combustible, batterie*, accumulateur*, corrosion, oxydoréduction, redox, voltammétrie, double couche, electrochem*, electrode*, electrolysis, electrolyte*, battery, batteries, fuel cell*, voltammetry"),
        "orbitales": ("nuage en lobes d'une densité orbitale", "chimie quantique, orbitale*, mécanique quantique, physique quantique, quantique*, fonction d'onde, liaison chimique, liaisons chimiques, atome*, électron*, quantum chemistry, quantum mechanics, quantum, orbital*, wave function, wavefunction, chemical bond*, atom*, electron*"),
        "chromato": ("pistes de pics, un composé à l'accent", "chimie analytique, chromatograph*, hplc, chromatographie en phase gazeuse, dosage*, titrage*, analyte*, spectrométrie de masse, analytical chemistry, gas chromatography, liquid chromatography, assay*, titration*, mass spectrometry"),
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
