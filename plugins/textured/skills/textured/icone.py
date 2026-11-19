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
    # sciences exactes : physique et astronomie, Terre et climat, mathématiques, chimie générale
    G["moire"] = [C(11.5, 16, 7.5, 2.8), C(20.5, 16, 7.5, 2.8, "a")]
    G["courbure"] = [T(courbe(lambda x: 6 + 7 * math.exp(-((x - 16) / 5.5) ** 2), 4, 28, 30), 2.8),
                     T(courbe(lambda x: 13.5 + 7.5 * math.exp(-((x - 16) / 5) ** 2), 4, 28, 30), 2.8), D(16, 26.5, 3.4, "a")]
    G["constellation"] = [T([(7, 23), (14, 10), (25, 14), (21, 25)], 2.2), D(7, 23, 2.8), D(14, 10, 4, "a"), D(25, 14, 2.8), D(21, 25, 2.8)]
    G["secousse"] = [T([(4, 16), (9, 16)], 2.8), T([(9, 16), (11.5, 7), (14, 25), (16.5, 5), (19, 23), (21.5, 11), (23, 16)], 2.6, "a"), T([(23, 16), (28, 16)], 2.8)]
    G["gyres"] = [T(ellipse(10.5, 16, 5.6, 10, 0, 32), 2.8), T(ellipse(21.5, 16, 5.6, 10, 0, 32), 2.8, "a")]
    G["stries"] = [rect(4.5, 5, 4.2, 22), rect(10, 5, 4.2, 22), rect(17.8, 5, 4.2, 22, "a"), rect(23.3, 5, 4.2, 22, "a")]
    G["huit"] = [T([(16 + 11 * math.cos(t) / (1 + math.sin(t) ** 2), 16 + 11 * math.sin(t) * math.cos(t) / (1 + math.sin(t) ** 2) * 1.4)
                    for t in (2 * math.pi * i / 48 for i in range(49))], 2.8), D(27, 16, 3, "a")]
    G["cordes"] = [C(16, 16, 11.5, 2.4), T([(16 + 11.5 * math.cos(math.radians(-90 + 144 * k)), 16 + 11.5 * math.sin(math.radians(-90 + 144 * k))) for k in range(6)], 2.2, "a")]
    G["quinconce"] = [D(16, 7, 2.8), D(11, 14.5, 2.8), D(21, 14.5, 2.8), D(6, 22, 2.8), D(16, 22, 3.6, "a"), D(26, 22, 2.8)]
    G["trefle"] = [T([(16 + 4.4 * (math.sin(t) + 2 * math.sin(2 * t)), 15.5 + 4.4 * (math.cos(t) - 2 * math.cos(2 * t)) * .95)
                      for t in (2 * math.pi * i / 72 for i in range(73))], 2.8, "a")]
    G["ulam"] = [T([(16, 16), (21, 16), (21, 21), (11, 21), (11, 11), (26, 11), (26, 26), (6, 26), (6, 6), (26, 6)], 2.4), D(16, 16, 3, "a")]
    G["raies"] = [rect(5.5, 5, 2.6, 22), rect(10.5, 5, 4.6, 22, "a"), rect(17.5, 5, 2.6, 22), rect(22.5, 5, 3.6, 22)]
    G["borne"] = [rect(5, 4, 5.5, 24), D(15.5, 8.5, 2.6, "a"), D(15.5, 16, 2.6, "a"), D(15.5, 23.5, 2.6, "a"), D(23.5, 12, 2.4), D(24, 21, 2.4)]
    G["orbitale"] = [F(ellipse(16, 10, 5.2, 6.6, 0, 28)), F(ellipse(16, 22, 5.2, 6.6, 0, 28), "a")]
    G["chromato"] = [T(courbe(lambda x: 26 - 17 * math.exp(-((x - 10.5) / 1.9) ** 2) - 7 * math.exp(-((x - 23) / 1.7) ** 2), 3.5, 28.5, 50), 2.6),
                     F([(13.5, 26)] + courbe(lambda x: 26 - 12 * math.exp(-((x - 17) / 1.8) ** 2), 13.5, 20.5, 16) + [(20.5, 26)], "a")]
    # sciences exactes, suite
    quad = lambda p0, p1, p2, k=16: [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
                                     for t in (q / k for q in range(k + 1))]
    G["dipole"] = [T(quad((7, 16), (16, 3), (25, 16)), 2.4), T(quad((7, 16), (16, 29), (25, 16)), 2.4), D(7, 16, 3.6, "a"), D(25, 16, 3.6)]
    G["kepler"] = [T(ellipse(17, 16, 11.5, 7, -25, 36), 2.6), D(12.5, 18, 3.6, "a")]
    G["lissajous"] = [T([(16 + 10.5 * math.sin(t + math.pi / 2), 16 + 10.5 * math.sin(2 * t)) for t in (2 * math.pi * q / 48 for q in range(49))], 2.6),
                      D(26.5, 16, 3, "a")]
    G["zones"] = [T([(16, 4), (28, 16), (16, 28), (4, 16), (16, 4)], 2.4), F([(16, 10), (22, 16), (16, 22), (10, 16)], "a")]
    G["trainees"] = [T(arc(5, 27, 8, -90, 0, 10), 3, "a"), T(arc(5, 27, 14.5, -90, 0, 14), 2.8), T(arc(5, 27, 21, -90, 0, 18), 2.8)]
    G["vortex"] = [C(10, 11, 4.6, 2.4), C(22, 11, 4.6, 2.4), C(16, 21.5, 4.6, 2.4, "a")]
    G["eclats"] = [F([(5, 6), (15, 5), (13, 14), (6, 13)]), F([(18, 5), (27, 7), (26, 15), (17, 13)], "a"), F([(6, 17), (16, 18), (19, 27), (7, 27)]),
                   F([(20, 18), (27, 19), (26, 27), (21, 26)])]
    G["confluence"] = [T([(16, 17), (7, 5)], 2.6), T([(16, 17), (24, 9), (27, 4)], 2.4), T([(24, 9), (20, 4)], 2), T([(16, 28), (16, 17)], 3.6, "a")]
    G["jet"] = [T([(16 + (9.5 + 2.6 * math.sin(5 * t)) * math.cos(t), 16 + (9.5 + 2.6 * math.sin(5 * t)) * math.sin(t)) for t in (2 * math.pi * q / 60 for q in range(61))], 2.6),
                D(16, 16, 3, "a")]
    G["pluie"] = [T([(10, 5), (7, 12)], 2.8), T([(20, 8), (17, 15)], 2.8, "a"), T([(13, 18), (10, 25)], 2.8), T([(25, 19), (22, 26)], 2.8)]
    G["carotte"] = [rect(5, 6, 22, 4.4), rect(5, 13, 22, 6, "a"), rect(5, 22, 22, 3.6)]
    G["grains"] = [C(10, 11, 5.4, 2.4), C(21.5, 10, 4.4, 2.4), C(11.5, 22.5, 4.4, 2.4), C(22, 21.5, 5.2, 2.4), D(16.3, 16.2, 1.9, "a")]
    G["mandelbrot"] = [F([(24 + 15.5 * (math.cos(t) / 2 - math.cos(2 * t) / 4), 16 + 15.5 * (math.sin(t) / 2 - math.sin(2 * t) / 4)) for t in (2 * math.pi * q / 48 for q in range(48))]),
                       D(24 - 15.5 * 1.04, 16, 15.5 * .25, "a")]
    pts_h = []
    for dd in range(16):
        x = y = 0
        s_, t_ = 1, dd
        while s_ < 4:
            rx = 1 & (t_ // 2)
            ry = 1 & (t_ ^ rx)
            if ry == 0:
                if rx == 1:
                    x, y = s_ - 1 - x, s_ - 1 - y
                x, y = y, x
            x, y, t_, s_ = x + s_ * rx, y + s_ * ry, t_ // 4, s_ * 2
        pts_h.append((6 + x * 6.7, 6 + y * 6.7))
    G["hilbert"] = [T(pts_h[:10], 2.6), T(pts_h[9:], 2.6, "a")]
    G["rhombes"] = [F([(4, 18), (11, 7), (24, 7), (17, 18)]), F([(8, 24), (17, 19), (28, 24), (17, 29)], "a")]
    G["apollonius"] = [C(16, 16, 12, 2.2), D(11.3, 16, 6.6), D(23.2, 16, 4.6, "a"), D(19.5, 7.6, 2.6)]
    G["vogel"] = [D(16 + 3.4 * math.sqrt(k) * math.cos(k * 2.39996), 16 + 3.4 * math.sqrt(k) * math.sin(k * 2.39996), 1.3 + .22 * k, "a" if k % 4 == 0 else "g")
                  for k in range(1, 12)]
    G["epicycle"] = [C(12.5, 17, 8, 2.4), C(20.5, 17, 4, 2.2, "a"), T([(12.5, 17), (20.5, 17), (24.5, 17)], 1.8), D(24.5, 17, 2.6, "a")]
    G["poincare"] = [C(16, 16, 12, 2.4), T(arc(16, 33.5, 14, 215, 325, 14), 2.4), T(arc(33.5, 16, 14, 125, 235, 14), 2.4, "a")]
    G["rosace"] = [T([(16 + (7.5 + 4 * math.cos(5 * t)) * math.cos(t), 16 + (7.5 + 4 * math.cos(5 * t)) * math.sin(t)) for t in (2 * math.pi * q / 90 for q in range(91))], 2.6),
                   D(16, 16, 2.6, "a")]
    G["hypercube"] = [T([(5, 5), (27, 5), (27, 27), (5, 27), (5, 5)], 2.4), T([(11, 11), (21, 11), (21, 21), (11, 21), (11, 11)], 2.4, "a"),
                      T([(5, 5), (11, 11)], 1.8), T([(27, 5), (21, 11)], 1.8), T([(27, 27), (21, 21)], 1.8), T([(5, 27), (11, 21)], 1.8)]
    G["laue"] = [D(16, 16, 3.8), D(16, 7, 2.6), D(25, 16, 2.6), D(16, 25, 2.6), D(7, 16, 2.6), D(9.5, 9.5, 1.9, "a"), D(22.5, 9.5, 1.9, "a"),
                 D(22.5, 22.5, 1.9, "a"), D(9.5, 22.5, 1.9, "a")]
    G["tableau"] = [rect(4, 5, 6, 17), rect(20, 9, 8, 13), rect(10, 14, 10, 8, "a"), rect(8, 24.5, 16, 3.2)]
    G["cernes"] = [T(arc(5, 27, 6, -90, 0, 8), 3, "a"), T(arc(5, 27, 12.5, -90, 0, 12), 3), T(arc(5, 27, 20.5, -90, 0, 16), 2.6)]
    G["gaz"] = [T([(5, 9), (13, 9)], 2), D(13, 9, 3.2), T([(15, 23), (24, 23)], 2), D(24, 23, 3.2), T([(6, 17), (19, 15)], 2.4, "a"), D(19.5, 15, 3.6, "a")]
    G["couronne"] = [D(16, 16, 4.8, "a")] + [D(16 + 10 * math.cos(2 * math.pi * k / 7), 16 + 10 * math.sin(2 * math.pi * k / 7), 2.4) for k in range(7)]
    G["multiplet"] = [T([(16, 4), (16, 9), (9, 15)], 2.2), T([(16, 9), (23, 15)], 2.2), rect(6, 19, 2.8, 9), rect(10.8, 17, 2.8, 11, "a"),
                    rect(18.4, 17, 2.8, 11, "a"), rect(23.2, 19, 2.8, 9)]
    G["osmose"] = [T([(16, 4), (16, 9)], 2.4), T([(16, 13.5), (16, 18.5)], 2.4), T([(16, 23), (16, 28)], 2.4), D(8.5, 10, 2), D(6.5, 19, 2), D(10.5, 24.5, 2),
                   D(23.5, 16, 4.4, "a")]
    # sciences du vivant, médecine, informatique, ingénierie, sciences humaines
    G["bifurcation"] = [T([(16, 28), (16, 18.5)], 3.2), T([(6.5, 9), (16, 18.5), (25.5, 9)], 3.2), D(6.5, 8, 3.4), D(25.5, 8, 3.4, "a")]
    G["scission"] = [F(arc(14.5, 16, 11, 90, 270, 18)),
                     F([(17.5, 14.6)] + arc(17.5, 14.6, 11, -90, 0, 9)), F([(17.5, 17.4)] + arc(17.5, 17.4, 11, 0, 90, 9), "a")]
    orbites = []
    for x0 in (2.5, 1.55):
        lv, u, v, tour = [], math.log(x0), 0.0, 0.0
        while tour < 2 * math.pi:
            lv.append((math.exp(u), math.exp(v)))
            a0 = math.atan2(v, u)
            u += .02 * (1 - math.exp(v))
            v += .02 * (math.exp(u) - 1)
            tour += abs(math.remainder(math.atan2(v, u) - a0, 2 * math.pi))
        orbites.append(lv[::5] + lv[:1])
    xs, ys = [p[0] for p in orbites[0]], [p[1] for p in orbites[0]]
    cadre = lambda p: (5 + 22 * (p[0] - min(xs)) / (max(xs) - min(xs)), 27 - 22 * (p[1] - min(ys)) / (max(ys) - min(ys)))
    G["cycles"] = [T([cadre(p) for p in orbites[0]], 3), T([cadre(p) for p in orbites[1]], 3, "a")]
    G["impulsions"] = [T([(x, 5), (x, 12.5)], 3) for x in (7, 14, 25)] + [T([(10.5, 19.5), (10.5, 27)], 3), T([(19.5, 19.5), (19.5, 27)], 3, "a"),
                                                                           T([(25.5, 19.5), (25.5, 27)], 3)]
    G["entaille"] = [T(arc(13.5, 16, 9.5, 40, 320), 3.4), D(25.5, 16, 3.6, "a")]
    G["foyer"] = [D(16 + 11 * math.cos(math.radians(60 * k + 30)), 16 + 11 * math.sin(math.radians(60 * k + 30)), 2.7) for k in range(6)] + [D(16, 16, 4.6, "a")]
    G["seuil"] = [D(8, 16, 4.6), T([(16, 5), (16, 27)], 2.8), C(24, 16, 4, 2.8, "a")]
    G["tresse"] = [T(courbe(lambda x: 16 + 8 * math.sin((x - 5) / 22 * 2 * math.pi), 5, 27), 3),
                   T(courbe(lambda x: 16 - 8 * math.sin((x - 5) / 22 * 2 * math.pi), 5, 27), 3, "a")]
    G["liens"] = [T([(7, 9), (25, 9)], 2.8), T([(7, 9), (25, 23)], 2.8), T([(7, 23), (25, 9)], 2.8), T([(7, 23), (25, 23)], 2.8),
                  D(7, 9, 3.4), D(7, 23, 3.4), D(25, 9, 3.4), D(25, 23, 3.8, "a")]
    G["noyau"] = [T([(6.5, 8), (16, 16), (26, 10)], 2.8), T([(8, 25.5), (16, 16), (25, 25)], 2.8)] + [D(x, y, 2.8) for x, y in ((6.5, 8), (26, 10), (8, 25.5), (25, 25))] + [D(16, 16, 4.8, "a")]
    G["secteurs"] = [T(arc(16, 16, 11.5, a0, a1, 10), 3.2) for a0, a1 in ((-160, -70), (-40, 50), (80, 170))] + [T(arc(16, 16, 5, -110, 50, 12), 3.2, "a")]
    G["rangs"] = [T([(7, 5), (7, 27)], 2.8), T([(14.5, 5), (14.5, 27)], 4.2), T([(23.5, 5), (23.5, 27)], 6.4, "a")]
    G["coude"] = [T([(4, 9), (14, 9), (23, 18), (23, 23)], 3), T([(4, 15.5), (11.3, 15.5), (16.5, 20.7), (16.5, 23)], 3),
                  D(23, 25.5, 3.2, "a"), D(16.5, 25.5, 3.2)]
    G["delta"] = [T([(4, 9), (28, 9)], 3, "a"), T([(4, 15.5), (12, 15.5)] + arc(12, 24.5, 9, -90, 0, 12) + [(21, 28)], 3)]
    G["articule"] = [T([(6, 26.5), (10.5, 14), (21, 8), (27, 17)], 3), D(6, 26.5, 3.6), D(10.5, 14, 2.4), D(21, 8, 2.4), D(27, 17, 3.4, "a")]
    G["pions"] = [D(9.5, 9.5, 5), C(22.5, 9.5, 4.2, 2.8), C(9.5, 22.5, 4.2, 2.8), D(22.5, 22.5, 5, "a")]
    G["etages"] = [rect(4.5, 21.5, 23, 5), rect(7.5, 13.5, 17, 5, "a"), rect(11, 5.5, 10, 5)]
    G["periodes"] = [T([(4.5, 7.5), (19, 7.5)], 2.8), T([(11, 16), (27.5, 16)], 5.4, "a"), T([(6, 24.5), (15, 24.5)], 3.8)]
    lien = lambda a, b: [(a[0] + (b[0] - a[0]) * (3 * t * t - 2 * t ** 3), a[1] + (b[1] - a[1]) * t) for t in (q / 12 for q in range(13))]
    G["lignees"] = [T(lien((6, 26), (16, 6)), 2.8), T(lien((16, 26), (16, 6)), 2.8), T(lien((26, 26), (26, 6)), 2.8), D(16, 6, 3.8, "a"),
                    D(26, 6, 3), D(6, 6, 2), D(6, 26, 3), D(16, 26, 3), D(26, 26, 3)]
    G["diagonales"] = [T([(5, 5), (27, 27)], 3.2), T([(15, 5), (27, 17)], 3.2), T([(6, 26), (12, 20)], 3.4, "a")]
    G["macules"] = [D(9, 9, 4.2), D(22.5, 10, 3), D(6.5, 23, 2.6), D(25, 24, 3.2), D(15.5, 18.5, 5, "a")]
    G["decalage"] = [rect(4 + 4 * k, 4.5 + 7 * k, 13, 3.6, "a" if k == 3 else "g") for k in range(4)]
    G["repli"] = [T([(6, 26), (6, 16), (16, 16), (16, 26), (26, 26), (26, 6), (11, 6)], 3), D(6, 26, 3.4), D(11, 6, 3.4, "a")]
    G["allele"] = [D(9.5, 9.5, 5.6), C(22.5, 9.5, 4.4, 2.8), F(arc(22.5, 9.5, 5.6, 90, 270, 10)), C(9.5, 22.5, 4.4, 2.8),
                   F(arc(9.5, 22.5, 5.6, -90, 90, 10)), C(22.5, 22.5, 4.4, 2.8, "a")]
    G["segments"] = [rect(4, 6, 12, 5.5), rect(18, 6, 10, 5.5, "a"), rect(4, 14.5, 7, 5.5), rect(13, 14.5, 15, 5.5), rect(4, 23, 16, 5.5), rect(22, 23, 6, 5.5, "a")]
    G["parts"] = [C(9, 16, 5.2, 2.8), F([(9, 16)] + arc(9, 16, 6.6, -90, 0, 6)), C(23, 16, 6.2, 2.8, "a"), F([(23, 16)] + arc(23, 16, 7.6, -90, 160, 14), "a")]
    G["paliers"] = [T([(4, 7), (9, 7), (9, 19), (14, 19), (14, 26), (19, 26), (19, 13), (28, 13)], 2.8), T([(21, 13), (27, 13)], 5, "a")]
    G["bandes"] = [rect(4, 6, 6.5, 3.4), rect(4, 15, 6.5, 3.4), rect(4, 24, 6.5, 3.4), rect(13, 9, 6.5, 3.4), rect(13, 19, 6.5, 3.4, "a"),
                   rect(22, 13, 6.5, 3.4), rect(22, 19, 6.5, 3.4, "a")]
    G["consigne"] = [T(courbe(lambda x: 16 - 11 * math.exp(-(x - 4) / 5), 4, 22), 2.8), T(courbe(lambda x: 16 + 11 * math.exp(-(x - 4) / 6) * math.cos((x - 4) / 2.6), 4, 22), 2.8),
                     T([(19, 16), (28, 16)], 3.6, "a")]
    G["masque"] = [rect(4 + 9 * j, 4 + 9 * i, 6.8, 6.8, "a" if (i, j) == (2, 2) else "g") for i in range(3) for j in range(i + 1)]
    G["partition"] = [rect(4, 4, 10, 24), rect(16.5, 4, 11.5, 10.5), rect(16.5, 17, 11.5, 11, "a")]
    G["couloir"] = [T([(5, 27), (5, 5), (27, 5), (27, 27), (12, 27), (12, 12), (20, 12), (20, 19)], 3), D(20, 20, 3, "a")]
    G["subdivision"] = [rect(4, 4, 11, 11), rect(4, 17, 11, 11), rect(17, 17, 11, 11), rect(17, 4, 4.6, 4.6), rect(23.4, 4, 4.6, 4.6, "a"),
                        rect(17, 10.4, 4.6, 4.6), rect(23.4, 10.4, 4.6, 4.6)]
    G["bits"] = [T([(x, 6), (x, 26)], 3, "a" if x == 22 else "g") for x in (5, 16.5, 22)] + [D(x, 16, 2.6) for x in (10.75, 27)]
    vague = lambda y0, a, ph: (lambda x: y0 + a * math.sin((x - 4) / 24 * 2 * math.pi + ph))
    G["flots"] = [F(courbe(vague(6, 1.6, 0), 4, 28) + courbe(vague(12, 1.6, .6), 4, 28)[::-1]),
                  F(courbe(vague(14.5, 1.6, .6), 4, 28) + courbe(vague(19.5, 2, 1.2), 4, 28)[::-1], "a"),
                  F(courbe(vague(21.5, 2, 1.2), 4, 28) + courbe(vague(27, 1.2, 1.8), 4, 28)[::-1])]
    G["glissando"] = [rect(4, 21, 6.5, 6.5), rect(12.75, 13.5, 6.5, 6.5), rect(21.5, 6, 6.5, 6.5, "a"), rect(5.5, 12, 3.6, 3.6), rect(14.2, 4.5, 3.6, 3.6)]
    G["remplissage"] = [T(arc(10, 10, 6, 180, 270, 6) + arc(22, 10, 6, 270, 360, 6) + arc(22, 22, 6, 0, 90, 6) + arc(10, 22, 6, 90, 180, 6) + [(4, 10)], 2.8),
                        T([(10, 10.5), (22, 10.5), (22, 16), (10, 16), (10, 21.5), (22, 21.5)], 2.8, "a")]
    G["arches"] = [T(arc(16, 23, 11, 180, 360, 20), 2.8), T(arc(15.5, 23, 3.5, 180, 360, 10), 2.8), D(5, 23, 2.6), D(12, 23, 2.6), D(19, 23, 2.6),
                   D(27, 23, 3.4, "a")]
    G["trajets"] = [T([(6 + 11 * t + 6 * t * (1 - t), 25 - 18 * t - 10 * t * (1 - t)) for t in (q / 12 for q in range(13))], 2.8),
                    T([(17 + 8 * t + 8 * t * (1 - t), 7 + 15 * t - 4 * t * (1 - t)) for t in (q / 12 for q in range(13))], 2.8),
                    D(6, 25, 3.6), D(25, 22, 2.8), D(17, 7, 4.2, "a")]
    G["ecus"] = [D(12, 13, 8.6, "a"), D(24.5, 21.5, 5.2), D(25.5, 8.5, 3), D(9, 26.5, 3)]
    G["gradins"] = [D(16 + 11 * math.cos(math.radians(a)), 23 - 11 * math.sin(math.radians(a)), 2.3, "a" if a < 50 else "g") for a in (0, 36, 72, 108, 144, 180)] \
        + [D(16 + 5 * math.cos(math.radians(a)), 23 - 5 * math.sin(math.radians(a)), 2.3) for a in (20, 90, 160)]
    G["aieux"] = [F(arc(16, 24, 6, 180, 360, 12)), F(arc(16, 24, 13, 181, 268, 10) + arc(16, 24, 8.4, 268, 181, 8)),
                  F(arc(16, 24, 13, 272, 359, 10) + arc(16, 24, 8.4, 359, 272, 8), "a")]
    G["duel"] = [F([(4, 15), (4, 5), (14, 15)]), F([(28, 4), (19, 4), (28, 13)]), F([(4, 28), (4, 19), (13, 28)], "a"), F([(28, 17), (18, 17), (28, 27)], "a")]
    # cours de M2 : polymères, génie de la réaction, optimisation et digitalisation, prévention des risques
    G["traversee"] = [T([(6.5, 7), (25.5, 7), (25.5, 25), (6.5, 25), (6.5, 7)], 2.6), T([(12, 3.5), (12, 11.5), (19.5, 15.5), (13.5, 21), (20, 28.5)], 3, "a")]
    G["perles"] = [D(6.8, 16, 4.3), D(16, 16, 4.3, "a"), D(25.2, 16, 4.3)]
    G["greffons"] = [T([(4.5, 16), (27.5, 16)], 3.2), T([(9.5, 16), (9.5, 6)], 2.8), T([(16, 16), (16, 26)], 2.8), T([(22.5, 16), (22.5, 6)], 2.8, "a")]
    G["brisure"] = [T([(5, 27), (13, 19)], 3.6), T([(19, 13), (27, 5)], 3.6), D(16, 16, 2.9, "a")]
    G["rugosite"] = [rect(4.5, 6, 23, 6.5), F([(4.5 + 23 * k / 16, 18.5 - (2.6 * k / 16 if k % 2 else 0)) for k in range(17)]
                                          + [(4.5 + 23 * k / 16, 25 + (0 if k % 2 else 2.6 * k / 16)) for k in range(16, -1, -1)], "a")]
    G["amas"] = [D(8.6, 21.5, 4.9), D(18, 21.5, 4.9), D(23.2, 12.6, 4.9, "a")]
    G["fente"] = [T(ellipse(16, 16, 12.5, 6.4, 0, 40), 2.8), T([(12, 12), (12, 20)], 2.6, "a"), T([(20, 12), (20, 20)], 2.6, "a")]
    G["chapelet"] = [T([(4.5, 6), (27.5, 6)], 3), C(19.5, 15.5, 4.8, 2.6, "a"), C(12, 24.5, 3.4, 2.6)]
    G["parabole"] = [T([(5 + 9 * (1 - (i / 12 - 1) ** 2), 16 + 11.5 * (i / 12 - 1)) for i in range(25)], 2.8),
                     T([(5 + 22 * (1 - (i / 12 - 1) ** 2), 16 + 11.5 * (i / 12 - 1)) for i in range(25)], 3, "a")]
    G["simplexe"] = [F([(5.46, 28.8), (18.79, 28.8), (12.12, 17.25)]), F([(19.88, 28.17), (13.21, 16.63), (26.54, 16.63)]), F([(14.14, 14.84), (25.61, 14.84), (19.88, 4.9)], "a")]
    G["karnaugh"] = [D(8.2, 9.5, 3.3), D(8.2, 22.5, 3.3), D(21.6, 9.5, 3.3), D(21.6, 22.5, 3.3),
                 T([(15.4, 9.5)] + arc(21.6, 9.5, 6.2, 180, 360, 10) + arc(21.6, 22.5, 6.2, 0, 180, 10) + [(15.4, 9.5)], 2.4, "a")]
    G["creneaux"] = [T([(4, 23), (8, 23), (8, 9), (12, 9), (12, 23), (15, 23)], 2.8), T([(15, 23), (15, 9), (24, 9), (24, 23), (28, 23)], 2.8, "a")]
    G["jumelage"] = [F(arc(14.5, 16, 10.5, 90, 270, 18)), rect(17.5, 6, 4.6, 4.6, "a"), rect(23, 11.2, 4.6, 4.6, "a"), rect(17.5, 16.4, 4.6, 4.6, "a"), rect(23, 21.6, 4.6, 4.6, "a")]
    G["front"] = [T(arc(29, 29, 21, 180, 270), 3), D(14.2, 14.2, 3.6, "a"), D(6.5, 6.5, 2.8)]
    G["tranches"] = [rect(6, 5, 4.4, 22), rect(13.8, 5, 4.4, 22), rect(21.6, 5, 4.4, 22), T([(3.5, 16), (28.5, 16)], 3, "a")]
    G["ecarts"] = [T([(3.5, 15.5), (28.5, 15.5)], 2.8), T([(7, 15.5), (7, 6), (16.5, 6), (16.5, 15.5)], 2.6), rect(19.5, 15.5, 7.5, 7.5, "a")]
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
# sciences exactes
MARQUE_DE.update({
    "interference": "moire", "geodesiques": "courbure", "ising": "damier", "galaxie": "spirale", "cosmique": "constellation",
    "plissement": "ondes", "sismogramme": "secousse", "gyres": "gyres", "isobares": "anneaux", "rechauffement": "stries",
    "isoclines": "tirets", "attracteur": "huit", "modulo": "cordes", "galton": "quinconce", "entrelacs": "trefle", "ulam": "ulam",
    "raies": "raies", "electrode": "borne", "orbitales": "orbitale", "chromato": "chromato",
})
MARQUE_DE.update({
    "dipole": "dipole", "limaille": "tirets", "kepler": "kepler", "lissajous": "lissajous", "chladni": "croix", "collision": "spirale",
    "brillouin": "zones", "chirikov": "gyres", "hertzsprung": "points", "circumpolaire": "trainees", "lentille": "anneau", "paquets": "onde",
    "abrikosov": "vortex", "hachures": "tirets", "orgues": "hexagone", "banquise": "eclats", "affluents": "confluence", "rossby": "jet",
    "averse": "pluie", "carottes": "carotte", "dorsale": "stries", "dunes": "ondes", "nebulosite": "disques", "poreux": "grains",
    "epicentres": "anneaux", "mandelbrot": "mandelbrot", "hilbert": "hilbert", "penrose": "rhombes", "apollonius": "apollonius",
    "angledor": "vogel", "collatz": "confluence", "quatrecouleurs": "grille", "epicycles": "epicycle", "hyperbolique": "poincare",
    "young": "escalier", "complexe": "etoile", "spirographe": "rosace", "tesseract": "hypercube", "laue": "laue", "mendeleiev": "tableau",
    "belousov": "spirale", "liesegang": "cernes", "maxwell": "gaz", "solvatation": "couronne", "miroir": "sablier", "nucleation": "disques",
    "multiplets": "multiplet", "agregat": "constellation", "osmose": "osmose", "zeolithe": "hexagone",
})
# sciences du vivant, médecine, informatique, ingénierie, sciences humaines
MARQUE_DE.update({
    "phylogenie": "bifurcation", "division": "scission", "proies": "cycles", "influx": "impulsions", "clones": "entaille",
    "contagion": "foyer", "depistage": "seuil", "sinogramme": "tresse", "perceptron": "liens", "grappes": "noyau", "brassage": "secteurs",
    "tri": "rangs", "pistes": "coude", "harmoniques": "ondes", "rubans": "delta", "poses": "articule", "volatilite": "eventail",
    "schelling": "pions", "pyramide": "etages", "frise": "periodes",
    "derive": "lignees", "alignement": "diagonales", "morphogenese": "macules", "circadien": "decalage", "repliement": "repli",
    "mendel": "allele", "recombinaison": "segments", "dose": "parts", "survie": "escalier", "sommeil": "paliers",
    "electrophorese": "bandes", "homeostasie": "consigne", "attention": "masque", "decision": "partition", "dedale": "couloir",
    "quadrants": "subdivision", "debruitage": "points", "binaire": "bits", "symboles": "grille", "isostatiques": "anneau",
    "mix": "flots", "lidar": "eventail", "spectrogramme": "glissando", "parcours": "remplissage", "syntaxe": "arches",
    "migrations": "trajets", "fortunes": "ecus", "hemicycle": "gradins", "ascendance": "aieux", "nash": "duel",
})
# cours de M2 : polymères, génie de la réaction, optimisation et digitalisation, prévention des risques
MARQUE_DE.update({
    "gel": "traversee", "copolymeres": "perles", "peignes": "greffons", "coupures": "brisure",
    "extrudats": "rugosite", "striction": "sablier", "agregats": "amas", "fibrilles": "fente",
    "selectivite": "barres", "thiele": "anneau", "barbotage": "chapelet", "poiseuille": "parabole",
    "simplexe": "simplexe", "compromis": "front", "boole": "karnaugh", "mli": "creneaux", "jumeau": "jumelage", "ecarts": "ecarts",
    "tranches": "tranches", "zonage": "anneaux",
})
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
        pal = dict(pal, ce=couverture.palette(encre, "claire", True)["ca"], ca=couverture.palette(encre, "claire", True)["ca"])
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
