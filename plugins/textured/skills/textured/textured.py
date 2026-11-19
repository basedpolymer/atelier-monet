#!/usr/bin/env python3
"""TeXtured HTML : assemble une page complète à partir d'une source courte (Markdown ou fragment HTML).

    textured.py doc.md [-o doc.html] [--ouvrir] [--pdf] [--apercu] [--couverture [MOTIF]] [--planche] [--polices embarquees|locales] [--assets URL] [--images liees]
    textured.py --exporter DOSSIER      # feuille de style, moteur, KaTeX et polices, pour un site (mode --assets)

La source commence par un en-tête « clé: valeur » entre deux lignes « --- » (voir SKILL.md). Le script numérote
titres, figures et tableaux, construit le plan, rend les formules (KaTeX, par node), embarque polices et images,
ne garde que les styles utilisés, pose les métadonnées et la politique de sécurité, puis contrôle le résultat.
--pdf (doc.pdf, A4) et --apercu (image de partage 1200 × 630) passent par Chrome sans interface, ou Edge sous Windows ;
TEXTURED_NAVIGATEUR (chemin d'un exécutable Chromium) impose le navigateur.
Code de sortie : 0 (page écrite, avertissements éventuels), 1 (erreur d'usage), 2 (page écrite avec des erreurs).
"""
import argparse
import base64
import hashlib
import html
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import couverture

ICI = Path(__file__).resolve().parent
ASSETS = ICI / "assets"
FEUILLES = ("textured.css", "couverture.css")  # lues à la suite : mêmes blocs « /*@ nom | motif */ »

TEXTES = {
    "fr": {"plan": "Sommaire", "evite": "Aller au contenu", "fig": "Figure", "tab": "Tableau", "theme": "Thème", "bplan": "Sommaire : afficher ou masquer",
           "reffig": "figure", "reftab": "tableau", "demo": "Démonstration", "corr": "Correction", "indice": "Indice",
           "plus": "Pour aller plus loin", "deplier": "Tout déplier ou tout replier", "reinit": "Réinitialiser QCM et jouets",
           "prio": "Priorités : tout", "chapitre": "Chapitre", "prec": "← précédent", "suiv": "suivant →", "accueil": "Accueil du cours",
           "prio_pour": "Priorités pour", "prio_titre": "Priorités de révision", "ce_chap": "Ce chapitre",
           "niveaux": {3: "incontournable", 2: "important", 1: "approfondissement"}, "prio_mot": "Priorité",
           "avert": "Avertissement", "compris": "J’ai compris"},
    "en": {"plan": "Contents", "evite": "Skip to content", "fig": "Figure", "tab": "Table", "theme": "Theme", "bplan": "Contents: show or hide",
           "reffig": "Figure", "reftab": "Table", "demo": "Proof", "corr": "Solution", "indice": "Hint",
           "plus": "Going further", "deplier": "Expand or collapse all", "reinit": "Reset quizzes and toys",
           "prio": "Priorities: all", "chapitre": "Chapter", "prec": "← previous", "suiv": "next →", "accueil": "Course home",
           "prio_pour": "Priorities for", "prio_titre": "Revision priorities", "ce_chap": "This chapter",
           "niveaux": {3: "essential", 2: "important", 1: "further"}, "prio_mot": "Priority",
           "avert": "Warning", "compris": "Got it"},
}
# encres de risographie : celle d'une page sans « tirage: » est tirée de son titre (du nom du cours pour un cours)
ENCRES = ["#0078bf", "#00a95c", "#ff48b0", "#ff6c2f", "#00838a", "#765ba7", "#f15060", "#3255a4", "#bb8b41", "#62a8e5",
          "#a75154", "#4a9d7f"]
# ce qu'un chapitre reprend de l'en-tête de l'accueil de son cours, s'il ne le dit pas lui-même
HERITES = ("tirage", "densite", "auteur", "lang", "pied", "prive", "icone", "polices", "numeros", "epreuve", "avertissement")
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
REPLIS = ("demo", "corr", "indice", "plus")
TITRE_H4 = ("exo", "jouet", "carte")
VIDES = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
FERMETURE_LIBRE = {"p", "li", "td", "th", "tr", "dt", "dd", "thead", "tbody", "tfoot", "colgroup", "option", "caption"}
LOCALES = {
    "lmroman10-regular": "LMRoman10-Regular", "lmroman10-bold": "LMRoman10-Bold", "lmroman10-italic": "LMRoman10-Italic",
    "lmroman10-bolditalic": "LMRoman10-BoldItalic", "lmromanslant10-regular": "LMRomanSlant10-Regular",
    "lmromanslant10-bold": "LMRomanSlant10-Bold", "lmsans10-regular": "LMSans10-Regular", "lmsans10-bold": "LMSans10-Bold",
    "lmsans10-oblique": "LMSans10-Oblique", "lmsans10-boldoblique": "LMSans10-BoldOblique",
    "lmmono10-regular": "LMMono10-Regular", "texgyrechorus-mediumitalic": "TeXGyreChorus-MediumItalic",
}
TOUJOURS = {"lmroman10-regular", "lmroman10-bold", "lmromanslant10-regular", "lmsans10-regular", "lmsans10-bold"}
PROTEGE = re.compile(r"<(script|style|pre|textarea)\b[^>]*>.*?</\1\s*>", re.S | re.I)
PROTEGE_MATH = re.compile(r"<(script|style|pre|textarea|code)\b[^>]*>.*?</\1\s*>", re.S | re.I)
ICONE = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cpath d='M16 4l12 12-12 12L4 16z' "
         "fill='%23fff' stroke='%23777' stroke-width='3'/%3E%3C/svg%3E")
LISTE = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M2.5 4h1M6 4h7.5M2.5 8h1M6 8h7.5M2.5 12h1M6 12h7.5"/></svg>'
AUTO = '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="5.6"/><path d="M8 2.4a5.6 5.6 0 0 1 0 11.2z" fill="currentColor"/></svg>'
LUNE = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M13.5 9.6A6 6 0 0 1 6.4 2.5a6 6 0 1 0 7.1 7.1z"/></svg>'
DEPLIER = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4.5 6.2 8 2.7l3.5 3.5M4.5 9.8 8 13.3l3.5-3.5"/></svg>'
REINIT = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.2 8a4.8 4.8 0 1 0 1.5-3.5M3 2.6v2.6h2.6"/></svg>'
ETOILE = ('<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.9l1.8 3.8 4.1.5-3 2.9.8 4.1L8 11.2l-3.7 2 .8-4.1-3-2.9 '
          '4.1-.5z"/></svg>')
# amorce des jouets : Cours.pret(fn) met fn en attente jusqu'à l'arrivée de la boîte à outils (fin de page)
AMORCE_COURS = "window.Cours=window.Cours||{_p:[],pret:function(f){this._p.push(f)}};"

avis, erreurs = [], []


def hors(motif, texte, fn):
    """Applique fn aux portions de texte situées hors des blocs protégés (script, style, pre…)."""
    morceaux, fin = [], 0
    for m in motif.finditer(texte):
        morceaux.append(fn(texte[fin:m.start()]))
        morceaux.append(m.group(0))
        fin = m.end()
    morceaux.append(fn(texte[fin:]))
    return "".join(morceaux)


def nu(fragment):
    """Texte d'un fragment HTML, sans balises ni formules."""
    t = re.sub(r"<[^>]+>", "", fragment)
    t = re.sub(r"\\\((.+?)\\\)", lambda m: m.group(1), t, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def slug(texte):
    t = unicodedata.normalize("NFD", texte.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60].strip("-") or "section"
    return "s-" + t if t[0].isdigit() else t


def attributs(chaine):
    return {m.group(1).lower(): (m.group(2) if m.group(2) is not None else "") for m in re.finditer(r'([\w:-]+)(?:\s*=\s*"([^"]*)")?', chaine)}


def fin_balise(texte, debut, balise):
    """Position du </balise> qui ferme l'élément dont le contenu commence à « debut »."""
    niveau = 1
    for m in re.compile(rf"<(/?){balise}\b[^>]*>", re.I).finditer(texte, debut):
        niveau += -1 if m.group(1) else 1
        if niveau == 0:
            return m.start(), m.end()
    return None


# ---------- source ----------

def lire_source(chemin):
    brut = sys.stdin.read() if str(chemin) == "-" else Path(chemin).read_text(encoding="utf-8")
    return entete(brut)


def entete(brut):
    """En-tête « clé: valeur » entre deux lignes « --- » : (meta, reste du texte)."""
    meta = {}
    m = re.match(r"\s*---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)", brut, re.S)
    if m:
        for ligne in m.group(1).splitlines():
            if ":" in ligne and not ligne.lstrip().startswith("#"):
                cle, valeur = ligne.split(":", 1)
                meta[cle.strip().lower()] = valeur.strip().strip('"')
        brut = brut[m.end():]
    return meta, brut


def markdown(texte):
    """Markdown vers HTML par pandoc. « ::: classe Titre » ouvre un bloc, « ::: » le ferme."""
    if not shutil.which("pandoc"):
        sys.exit("textured : pandoc est introuvable ; écrire la source en HTML (.tx.html) ou installer pandoc.")
    lignes, cloture = [], None
    source = texte.splitlines()
    i = -1
    while i + 1 < len(source):
        i += 1
        ligne = source[i]
        m = re.match(r"\s*(```+|~~~+)", ligne)
        if m:
            if cloture is None:
                cloture = m.group(1)[0]
            elif m.group(1)[0] == cloture:
                cloture = None
        elif cloture is None and re.match(r'\s*<div\b[^>]*\bclass="(?:[^"]*\s)?(?:jouet|qcm|qnum)\b', ligne):
            # jouet, QCM, question numérique : passés tels quels (bloc brut), sinon pandoc lit leur contenu comme du
            # Markdown et casse les <label> écrits sur plusieurs lignes ; les formules \( \) y sont rendues plus tard
            bloc, niveau = [], 0
            while i < len(source):
                bloc.append(source[i])
                niveau += len(re.findall(r"<div\b", source[i])) - len(re.findall(r"</div\s*>", source[i]))
                if niveau <= 0:
                    break
                i += 1
            barre = "~" * max(8, 1 + max((len(x) for x in re.findall(r"~+", "\n".join(bloc))), default=0))
            lignes += ["", barre + "{=html}"] + bloc + [barre, ""]
            continue
        elif cloture is None:
            # « ::: exo Titre {prio=3} » → « ::: {.exo titre="Titre" prio=3} » ; « ::: exo {prio=3} » aussi
            m = re.match(r"^(\s*:{3,})\s*([A-Za-z][\w-]*)\s+(\S.*?)\s*:*\s*$", ligne)
            if m:
                titre, attrs = m.group(3), ""
                a = re.fullmatch(r"(.*?)\s*\{([^{}]*)\}", titre)
                if a:
                    titre, attrs = a.group(1), " " + a.group(2).strip()
                titre = titre.replace("\\", "\\\\").replace('"', '\\"')
                titre_attr = f' titre="{titre}"' if titre else ""
                ligne = f"{m.group(1)} {{.{m.group(2)}{titre_attr}{attrs}}}"
        lignes.append(ligne)
    commande = ["pandoc", "-f", "markdown+fenced_divs+bracketed_spans+smart+tex_math_single_backslash", "-t", "html5", "--mathjax", "--wrap=none"]
    r = subprocess.run(commande + ["--syntax-highlighting=none"], input="\n".join(lignes), capture_output=True, text=True)
    if r.returncode != 0:
        r = subprocess.run(commande + ["--no-highlight"], input="\n".join(lignes), capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("textured : pandoc a échoué : " + r.stderr.strip())
    return r.stdout


# ---------- transformations du corps ----------

class Structure(HTMLParser):
    """Repère, dans l'ordre, les titres « de structure » (hors encadré, carte, figure…)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pile, self.titres, self.pre = [], [], 0

    def handle_starttag(self, tag, attrs):
        if tag in VIDES:
            return
        if tag == "pre":
            self.pre += 1
        if re.fullmatch(r"h[1-6]", tag) and not self.pre:
            self.titres.append(all(t in ("section", "main", "article") for t in self.pile))
        self.pile.append(tag)

    def handle_endtag(self, tag):
        if tag in self.pile:
            while self.pile and self.pile.pop() != tag:
                pass
            if tag == "pre":
                self.pre -= 1


def blocs_titres(corps, T):
    """data-titre → titre réel (lisible, sélectionnable) ; div.demo, .corr, .indice, .plus → <details>."""
    motif = re.compile(r"<(div|section|aside|details)\b([^>]*)>", re.I)
    for m in reversed(list(motif.finditer(corps))):
        a = attributs(m.group(2))
        classes = a.get("class", "").split()
        titre = a.get("data-titre")
        repli = next((c for c in classes if c in REPLIS), None) if m.group(1).lower() == "div" else None
        if titre is None and not repli:
            continue
        reste = re.sub(r'\s*data-titre="[^"]*"', "", m.group(2))
        if repli:
            fin = fin_balise(corps, m.end(), "div")
            if not fin:
                continue
            if repli == "demo":
                resume = f'<span class="etiq">{T["demo"]}</span>' + (f" {titre}" if titre else "")
            else:
                resume = titre or T[repli]
            dedans = corps[m.end():fin[0]]
            corps = (corps[:m.start()] + f"<details{reste}><summary>{resume}</summary><div class=\"corps\">{dedans}</div></details>"
                     + corps[fin[1]:])
        elif any(c in TITRE_H4 for c in classes):
            corps = corps[:m.start()] + f"<{m.group(1)}{reste}><h4>{titre}</h4>" + corps[m.end():]
        else:
            point = "" if re.search(r"[.?!:…]$", nu(titre)) else "."
            corps = corps[:m.start()] + f'<{m.group(1)}{reste}><p class="bloc-titre">{titre}{point}</p>' + corps[m.end():]
    return corps


def titres(corps, meta):
    """Identifiants, numéros et plan. Rend (corps, plan, étiquettes des renvois)."""
    s = Structure()
    s.feed(PROTEGE.sub("", corps))
    structure = iter(s.titres)
    numeroter = meta.get("numeros", "oui") != "non"
    vus, plan, etiquettes, compte = set(re.findall(r'\bid="([^"]+)"', corps)), [], {}, [0, 0]

    def un(m):
        niveau, attrs, dedans = int(m.group(1)), m.group(2), m.group(3)
        if not next(structure, False) or niveau not in (2, 3):
            return m.group(0)
        a = attributs(attrs)
        ident = a.get("id")
        if not ident:
            ident = base = slug(nu(dedans))
            n = 2
            while ident in vus:
                ident, n = f"{base}-{n}", n + 1
            vus.add(ident)
            attrs += f' id="{ident}"'
        numero = ""
        hors_numeros = re.search(r"\b(unnumbered|sans-num)\b", a.get("class", ""))
        if numeroter and not hors_numeros and 'class="num"' not in dedans:
            if niveau == 2:
                compte[0] += 1
                compte[1] = 0
                numero = str(compte[0])
            elif compte[0]:
                compte[1] += 1
                numero = f"{compte[0]}.{compte[1]}"
        deja = re.match(r'\s*<span class="num">(.*?)</span>', dedans)
        if deja:
            numero, dedans = nu(deja.group(1)), dedans[deja.end():]
        prefixe = f'<span class="num">{numero}</span>' if numero else ""
        plan.append((niveau, ident, prefixe + dedans.strip()))
        etiquettes[ident] = f"§ {numero}" if numero else nu(dedans)
        return f"<h{niveau}{attrs}>{prefixe}{dedans}</h{niveau}>"

    corps = hors(PROTEGE, corps, lambda t: re.sub(r"<h([1-6])\b([^>]*)>(.*?)</h\1\s*>", un, t, flags=re.S))
    return corps, plan, etiquettes


def figures_tableaux(corps, T, etiquettes):
    compte = {"fig": 0, "tab": 0}

    def figure(m):
        attrs, dedans = m.group(1), m.group(2)
        leg = re.search(r"<figcaption\b([^>]*)>(.*?)</figcaption>", dedans, re.S)
        if not leg:
            return m.group(0)
        compte["fig"] += 1
        n = compte["fig"]
        ident = attributs(attrs).get("id")
        if not ident:
            ident = f"fig-{n}"
            attrs += f' id="{ident}"'
        etiquettes[ident] = f'{T["reffig"]} {n}'
        texte = leg.group(2).strip()
        if not re.match(rf'(<b>|{T["fig"]}\b)', texte):
            texte = f'<b>{T["fig"]} {n} /</b> {texte}'
        lattrs = re.sub(r'\s*aria-hidden="true"', "", leg.group(1))
        dedans = dedans[:leg.start()] + f"<figcaption{lattrs}>{texte}</figcaption>" + dedans[leg.end():]
        return f"<figure{attrs}>{dedans}</figure>"

    def tableau(m):
        attrs, dedans = m.group(1), m.group(2)
        leg = re.search(r"<caption\b([^>]*)>(.*?)</caption>", dedans, re.S)
        nom = f' aria-label="{T["tab"]}"'
        if leg:
            compte["tab"] += 1
            n = compte["tab"]
            ident = attributs(attrs).get("id")
            # pandoc d'avant 3.2 laisse « {#tab-id} » dans le texte de la légende : on le reprend comme identifiant
            reste = re.search(r"\s*\{#([\w:.-]+)\}\s*((?:</p>)?)\s*$", leg.group(2))
            if reste:
                texte_leg = leg.group(2)[:reste.start()] + reste.group(2)
                dedans = dedans[:leg.start(2)] + texte_leg + dedans[leg.end(2):]
                leg = re.search(r"<caption\b([^>]*)>(.*?)</caption>", dedans, re.S)
                if not ident:
                    ident = reste.group(1)
                    attrs += f' id="{ident}"'
            if not ident:
                ident = f"tab-{n}"
                attrs += f' id="{ident}"'
            etiquettes[ident] = f'{T["reftab"]} {n}'
            texte = re.sub(r"^<p>(.*)</p>$", r"\1", leg.group(2).strip(), flags=re.S)
            if not re.match(rf'(<b>|{T["tab"]}\b)', texte):
                texte = f'<b>{T["tab"]} {n} /</b> {texte}'
            dedans = dedans[:leg.start()] + f'<caption id="{ident}-legende">{texte}</caption>' + dedans[leg.end():]
            nom = f' aria-labelledby="{ident}-legende"'
        table = f"<table{attrs}>{dedans}</table>"
        avant = corps[:m.start()].rstrip()
        if re.search(r'<div\b[^>]*class="[^"]*\btableau\b[^"]*"[^>]*>$', avant):
            return table
        return f'<div class="tableau" role="region" tabindex="0"{nom}>{table}</div>'

    corps = hors(PROTEGE, corps, lambda t: re.sub(r"<figure\b([^>]*)>(.*?)</figure>", figure, t, flags=re.S))
    corps = re.sub(r"<table\b([^>]*)>(.*?)</table>", tableau, corps, flags=re.S)
    return corps


def renvois(corps, etiquettes):
    def un(m):
        cible = m.group(2)
        if cible in etiquettes:
            return f"{m.group(1)}{etiquettes[cible]}</a>"
        avis.append(f"renvoi vide vers #{cible} : cible sans numéro ni titre")
        return m.group(0)
    return re.sub(r'(<a\b[^>]*href="#([^"]+)"[^>]*>)\s*</a>', un, corps)


def taille_image(d):
    try:
        if d[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", d[16:24])
        if d[:6] in (b"GIF87a", b"GIF89a"):
            return struct.unpack("<HH", d[6:10])
        if d[:4] == b"RIFF" and d[8:12] == b"WEBP":
            if d[12:16] == b"VP8X":
                return (int.from_bytes(d[24:27], "little") + 1, int.from_bytes(d[27:30], "little") + 1)
            if d[12:16] == b"VP8 ":
                l, h = struct.unpack("<HH", d[26:30])
                return (l & 0x3FFF, h & 0x3FFF)
            if d[12:16] == b"VP8L":
                b = int.from_bytes(d[21:25], "little")
                return ((b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1)
        if d[:2] == b"\xff\xd8":
            i = 2
            while i < len(d) - 9:
                if d[i] != 0xFF:
                    i += 1
                    continue
                marque = d[i + 1]
                if 0xC0 <= marque <= 0xCF and marque not in (0xC4, 0xC8, 0xCC):
                    h, l = struct.unpack(">HH", d[i + 5:i + 9])
                    return (l, h)
                i += 2 + int.from_bytes(d[i + 2:i + 4], "big")
    except (struct.error, IndexError):
        pass
    return None


def images(corps, dossier, embarquer):
    types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp",
             ".svg": "image/svg+xml", ".avif": "image/avif"}
    rang = [0]

    def un(m):
        attrs = m.group(1)
        a = attributs(attrs)
        src = a.get("src", "")
        rang[0] += 1
        if "alt" not in a:
            avis.append(f"image sans alt : {src[:60]} (alt=\"\" si elle est décorative)")
        if "decoding" not in a:
            attrs += ' decoding="async"'
        if rang[0] > 1 and "loading" not in a:
            attrs += ' loading="lazy"'
        # adresse web (y compris « /chemin » depuis la racine d'un site) : laissée telle quelle, sans contrôle
        if src and not re.match(r"(https?:|data:|/|blob:)", src):
            chemin = (dossier / html.unescape(src)).resolve()
            if not chemin.is_file():
                avis.append(f"image introuvable : {src}")
            else:
                donnees = chemin.read_bytes()
                t = taille_image(donnees)
                if t and "width" not in a and "height" not in a:
                    l, h = (t[0] // 2, t[1] // 2) if "@2x" in chemin.name else t
                    attrs += f' width="{l}" height="{h}"'
                mime = types.get(chemin.suffix.lower())
                if embarquer and mime and len(donnees) <= 1_500_000:
                    uri = f"data:{mime};base64,{base64.b64encode(donnees).decode()}"
                    attrs = attrs.replace(f'src="{src}"', f'src="{uri}"')
                elif embarquer:
                    avis.append(f"image laissée en lien (plus de 1,5 Mo ou format inconnu) : {src}")
        return f"<img{attrs}>"

    return hors(PROTEGE, corps, lambda t: re.sub(r"<img\b([^>]*?)\s*/?>", un, t))


def formules(page):
    """Rend \\( … \\) et \\[ … \\] avec KaTeX (HTML et MathML). Rend (page, nombre de formules)."""
    trouvees = []

    def reperer(texte):
        def un(m):
            bloc = m.group(1) is not None
            trouvees.append([html.unescape(m.group(1) if bloc else m.group(2)).strip(), bloc])
            return f"\x00{len(trouvees) - 1}\x00"
        return re.sub(r"\\\[(.+?)\\\]|\\\((.+?)\\\)", un, texte, flags=re.S)

    # pandoc enveloppe chaque formule dans <span class="math …"> : l'enveloppe part avant le rendu
    page = re.sub(r'<span class="math (?:inline|display)">(\\[(\[].*?\\[)\]])</span>', r"\1", page, flags=re.S)
    page = hors(PROTEGE_MATH, page, reperer)
    if not trouvees:
        return page, 0
    if not shutil.which("node"):
        sys.exit("textured : node est introuvable, il rend les formules (KaTeX).")
    r = subprocess.run(["node", str(ASSETS / "rendu-math.cjs")], input=json.dumps(trouvees), capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("textured : rendu des formules impossible : " + r.stderr.strip()[:400])
    rendus = json.loads(r.stdout)

    def poser(m):
        i = int(m.group(1))
        if "e" in rendus[i]:
            erreurs.append(f"formule refusée par KaTeX : {trouvees[i][0][:70]} → {rendus[i]['e'][:110]}")
            return f'<code class="katex-erreur">{html.escape(trouvees[i][0])}</code>'
        return rendus[i]["h"]

    page = re.sub(r"\x00(\d+)\x00", poser, page)
    return page, len(trouvees)


# ---------- contrôle ----------

class Controle(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pile, self.ids, self.cibles, self.classes = [], {}, [], set()
        self.niveau, self.polices, self.scripts_externes, self._classes = 2, set(), False, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        ligne = self.getpos()[0]
        if a.get("id"):
            if a["id"] in self.ids:
                avis.append(f'identifiant en double : id="{a["id"]}" (lignes {self.ids[a["id"]]} et {ligne} de la sortie)')
            self.ids[a["id"]] = ligne
        self.classes.update((a.get("class") or "").split())
        if tag == "a" and (a.get("href") or "").startswith("#") and len(a["href"]) > 1:
            self.cibles.append(a["href"][1:])
        if any(k.startswith("on") for k in a):
            avis.append(f"attribut d'événement en ligne sur <{tag}> (ligne {ligne}) : bloqué par la politique de sécurité, passer par addEventListener")
        if tag == "script" and a.get("src"):
            self.scripts_externes = True
        if tag == "svg" and "figure" in self.pile and "aria-hidden" not in a and not ("role" in a and ("aria-label" in a or "aria-labelledby" in a)):
            if "katex" not in " ".join(self._classes):
                avis.append(f'schéma SVG sans nom accessible (ligne {ligne}) : role="img" aria-label="…", ou aria-hidden="true" si la légende suffit')
        m = re.fullmatch(r"h([1-6])", tag)
        dedans = self.pile[self.pile.index("main") + 1:] if "main" in self.pile else ["div"]
        if m and not any(t in ("div", "aside", "details", "figure", "li", "td", "nav", "blockquote") for t in dedans):
            n = int(m.group(1))
            if n > self.niveau + 1:
                avis.append(f"saut de niveau de titre : h{self.niveau} puis h{n} (ligne {ligne} de la sortie)")
            self.niveau = n
        if tag in ("em", "i"):
            if any(t in ("strong", "b") for t in self.pile):
                self.polices.add("lmromanslant10-bold")
            if any(t in ("em", "i") for t in self.pile):
                self.polices.add("lmroman10-italic")
        if tag in ("strong", "b") and any(t in ("em", "i") for t in self.pile):
            self.polices.add("lmromanslant10-bold")
        if tag in ("code", "pre", "kbd", "samp"):
            self.polices.add("lmmono10-regular")
        if tag not in VIDES:
            self.pile.append(tag)
            self._classes.append(a.get("class") or "")

    def handle_endtag(self, tag):
        if tag in VIDES:
            return
        if tag not in self.pile:
            avis.append(f"</{tag}> sans ouverture (ligne {self.getpos()[0]} de la sortie)")
            return
        while self.pile:
            t = self.pile.pop()
            self._classes.pop()
            if t == tag:
                break
            if t not in FERMETURE_LIBRE:
                avis.append(f"<{t}> non fermé avant </{tag}> (ligne {self.getpos()[0]} de la sortie)")

    def bilan(self):
        for t in self.pile:
            if t not in FERMETURE_LIBRE and t not in ("html", "body"):
                avis.append(f"<{t}> jamais fermé")
        for c in dict.fromkeys(self.cibles):
            if c not in self.ids:
                avis.append(f"lien interne sans cible : #{c}")


# ---------- styles, polices, scripts ----------

def decouper(texte):
    """Blocs « /*@ nom | motif */ » d'un fichier de styles ou de script : liste (nom, motif, contenu)."""
    blocs, parties = [], re.split(r"/\*@\s*([\w-]+)\s*(?:\|\s*(.*?))?\s*\*/", texte)
    for i in range(1, len(parties), 3):
        blocs.append((parties[i], parties[i + 1], parties[i + 2]))
    return blocs


def minifier(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    morceaux = re.split(r'("(?:[^"\\]|\\.)*")', css)
    for i in range(0, len(morceaux), 2):
        m = re.sub(r"\s+", " ", morceaux[i])
        m = re.sub(r"\s*([{};,])\s*", r"\1", m)
        morceaux[i] = re.sub(r":\s+", ":", m).replace(";}", "}")
    return "".join(morceaux).strip()


def styles(corps, mode, utiles):
    garde = []
    for nom, motif, contenu in decouper("\n".join((ASSETS / f).read_text(encoding="utf-8") for f in FEUILLES)):
        if nom == "polices":
            def face(m):
                fichier = re.search(r'url\("polices/([\w-]+)\.woff2"\)', m.group(0))
                if not fichier:
                    return m.group(0)
                nomf = fichier.group(1)
                if mode == "locales":
                    return m.group(0).replace(f'url("polices/{nomf}.woff2") format("woff2")', f'local("{LOCALES[nomf]}")')
                if nomf not in utiles:
                    return ""
                donnees = base64.b64encode((ASSETS / "polices" / f"{nomf}.woff2").read_bytes()).decode()
                return m.group(0).replace(f'url("polices/{nomf}.woff2")', f'url("data:font/woff2;base64,{donnees}")')
            garde.append(re.sub(r"@font-face\s*\{[^}]*\}", face, contenu))
        elif not motif or re.search(motif, corps):
            garde.append(contenu)
    return minifier("\n".join(garde))


def katex_css(corps, large=False):
    """Règles de KaTeX et seules polices que les formules de la page emploient (large : aussi celles que des formules
    écrites à l'exécution, par Cours.tex, peuvent demander)."""
    css = (ASSETS / "katex.css").read_text(encoding="utf-8")
    faces = re.findall(r"@font-face\{[^}]*\}", css)
    regles = re.sub(r"@font-face\{[^}]*\}", "", css)
    classes = set(" ".join(re.findall(r'class="([^"]*)"', corps)).split())
    familles, gras, italique = {"KaTeX_Main", "KaTeX_Math"}, large, large
    if large:
        familles |= {"KaTeX_AMS", "KaTeX_Size1", "KaTeX_Size2", "KaTeX_Size3", "KaTeX_Size4", "KaTeX_Caligraphic"}
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", regles):
        selecteurs, decl = m.group(1), m.group(2)
        applique = any(all(c in classes for c in re.findall(r"\.([\w-]+)", s) if c != "katex") and "." in s
                       for s in selecteurs.split(","))
        if not applique:
            continue
        for f in re.findall(r"font-family:\s*\"?(KaTeX_\w+)", decl):
            familles.add(f)
        gras = gras or bool(re.search(r"font-weight:\s*(700|bold)", decl))
        italique = italique or "font-style:italic" in decl.replace(" ", "")
    garde = []
    for f in faces:
        famille = re.search(r'font-family:\s*"?(KaTeX_\w+)', f).group(1)
        if famille not in familles:
            continue
        est_gras, est_ital = "font-weight:700" in f, "font-style:italic" in f
        seule_italique = famille == "KaTeX_Math"
        if (est_gras and not gras) or (est_ital and not italique and not seule_italique):
            continue
        garde.append(f)
    return "".join(garde) + regles


def scripts(corps):
    garde = [c for _, motif, c in decouper((ASSETS / "textured.js").read_text(encoding="utf-8")) if not motif or re.search(motif, corps)]
    return "\n".join(c.strip() for c in garde)


def date_lisible(valeur, lang):
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", valeur)
    if not m:
        return html.escape(valeur)
    a, mo, j = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if lang == "en":
        texte = f"{MONTHS[mo - 1]} {j}, {a}"
    else:
        texte = f"{'1er' if j == 1 else j} {MOIS[mo - 1]} {a}"
    return f'<time datetime="{valeur}">{texte}</time>'


# ---------- assemblage ----------

def niveau_priorite(valeur):
    """« priorite: 3 — raison » → (3, "raison") ; (0, "") sans niveau lisible."""
    m = re.match(r"\s*([123])\b\s*(?:[—–:|-]\s*)?(.*)$", valeur or "")
    if not m:
        return 0, ""
    raison = m.group(2).strip()
    if raison:
        raison = raison[0].upper() + raison[1:] + ("" if re.search(r"[.!?…]$", raison) else ".")
    return int(m.group(1)), raison


def encre_par_defaut(nom):
    return ENCRES[int(hashlib.sha256(nom.encode()).hexdigest(), 16) % len(ENCRES)]


def sans_code(html_):
    """Le HTML sans le texte des <code> et <pre> (balises gardées) : ce qui est cité en exemple ne déclenche rien."""
    return re.sub(r"(<(code|pre)\b[^>]*>).*?(</\2\s*>)", r"\1\3", html_, flags=re.S)


def nom_sortie(src):
    return src.with_name(re.sub(r"\.(tx|src)$", "", src.stem) + ".html") if src.suffix.lower() in (".html", ".htm") else src.with_suffix(".html")


def cours_de(src):
    """Le cours d'une source : son dossier a un index.md (ou index.tx.html) dont l'en-tête porte « cours: ». Rend None
    ou { nom, cle, index (en-tête), fichier_index, chapitres: [{ f, n, titre }] }, chapitres dans l'ordre des noms de
    fichier : les sources du dossier dont l'en-tête porte « chapitre: »."""
    if src is None:
        return None
    dossier = src.resolve().parent
    idx = next((dossier / n for n in ("index.md", "index.tx.html") if (dossier / n).is_file()), None)
    if idx is None:
        return None
    mi = entete(idx.read_text(encoding="utf-8"))[0]
    if not mi.get("cours"):
        return None
    chapitres = []
    for f in sorted(dossier.iterdir()):
        if f == idx or not (f.suffix.lower() == ".md" or f.name.lower().endswith((".tx.html", ".src.html"))):
            continue
        m = entete(f.read_text(encoding="utf-8"))[0]
        if m.get("chapitre"):
            chapitres.append({"f": nom_sortie(f).name, "n": m["chapitre"], "titre": m.get("titre") or f.stem,
                              "prio": niveau_priorite(m.get("priorite", ""))[0]})
    return {"nom": mi["cours"], "cle": mi.get("cle") or f"tx:{slug(mi['cours'])}:", "index": mi,
            "fichier_index": nom_sortie(idx).name, "chapitres": chapitres}


def construire(meta, corps, dossier, options, cours=None, page_nom="page.html"):
    lang = meta.get("lang", "fr")[:2].lower()
    T = TEXTES.get(lang, TEXTES["en"])
    e = html.escape

    # titre : en-tête, sinon l'unique h1 du corps ; plusieurs h1 → tous les titres descendent d'un niveau
    h1 = re.findall(r"<h1\b[^>]*>(.*?)</h1\s*>", corps, re.S)
    titre_html = e(meta["titre"]) if meta.get("titre") else None
    if titre_html is None and len(h1) == 1:
        titre_html = h1[0].strip()
        corps = re.sub(r"<h1\b[^>]*>.*?</h1\s*>", "", corps, count=1, flags=re.S)
        h1 = []
    if h1:
        corps = hors(PROTEGE, corps, lambda t: re.sub(r"<(/?)h([1-5])\b", lambda m: f"<{m.group(1)}h{int(m.group(2)) + 1}", t))
    if titre_html is None:
        titre_html = "Sans titre"
        avis.append("pas de titre : ajouter « titre: … » dans l'en-tête de la source")
    titre_nu = nu(titre_html)
    brut = corps
    # encre : celle de l'en-tête, sinon une encre tirée du titre (du nom du cours) ; « tirage: non » : page grise
    tirage, encre_auto = meta.get("tirage", "").strip(), False
    if tirage.lower() in ("non", "no", "aucun", "none"):
        tirage = ""
    elif not tirage:
        tirage, encre_auto = encre_par_defaut(cours["nom"] if cours else titre_nu), True

    corps = blocs_titres(corps, T)
    corps, plan, etiquettes = titres(corps, meta)
    corps = figures_tableaux(corps, T, etiquettes)
    corps = renvois(corps, etiquettes)
    corps = images(corps, dossier, options.images != "liees")
    # couverture (sur demande seulement) : module à part, à l'encre de la page (la sienne si la page est grise)
    couv = couverture.preparer(dict(meta, tirage=tirage), corps, plan, lang, avis, brut)
    if couv:
        corps = couv["corps"]

    # priorités : encadré du chapitre (niveau et raison de l'en-tête ; textured.js y ajoute ce qui est ★★★ et les réserves)
    niveau, raison = niveau_priorite(meta.get("priorite", ""))
    if niveau:
        epreuve = meta.get("epreuve", "").strip()
        titre_enc = T["prio_pour"] + " " + e(epreuve) if epreuve else T["prio_titre"]
        enc = (f'<div class="priorites" data-niveau="{niveau}"><p class="bloc-titre">{titre_enc}.</p>'
               f'<p>{T["ce_chap"]} : <span class="prio p{niveau}" title="{T["prio_mot"]} : {T["niveaux"][niveau]}">{"★" * niveau}</span> '
               f'{T["niveaux"][niveau]}.{" " + e(raison) if raison else ""}</p></div>\n')
        tete_retenir = re.match(r'\s*<div class="retenir"[^>]*>', corps)
        fin = fin_balise(corps, tete_retenir.end(), "div") if tete_retenir else None
        corps = corps[:fin[1]] + "\n" + enc + corps[fin[1]:] if fin else enc + corps
    elif meta.get("priorite"):
        avis.append("priorite : attendre « priorite: 3 » (1, 2 ou 3), suivi si on veut d'un tiret et de la raison")

    # cours : liste des chapitres sur l'accueil, navigation de chapitre en chapitre en bas des pages
    chapitre = meta.get("chapitre", "").strip()
    if cours:
        suite = [{"f": cours["fichier_index"], "n": "", "titre": e(T["accueil"])}] + [
            {"f": c["f"], "n": c["n"], "titre": e(c["titre"]), "prio": c.get("prio", 0)} for c in cours["chapitres"]]
        if page_nom == cours["fichier_index"]:
            etoiles = lambda n: (f' <span class="prio p{n}" title="{T["prio_mot"]} : {T["niveaux"][n]}">{"★" * n}</span>' if n else "")
            liste = "".join(f'<li><span class="n">{e(c["n"])}</span><a href="{e(c["f"])}">{c["titre"]}</a>'
                            f'{etoiles(c["prio"])}</li>' for c in suite[1:])
            liste = f'<ol class="chapitres">{liste}</ol>' if liste else ""
            if not liste:
                avis.append("cours sans chapitre : les sources voisines doivent porter « chapitre: n » dans leur en-tête")
            place = re.search(r'<div class="chapitres">\s*</div>', corps)
            corps = corps[:place.start()] + liste + corps[place.end():] if place else corps + "\n" + liste
        i = next((k for k, c in enumerate(suite) if c["f"] == page_nom), None)
        if i is not None and len(suite) > 1:
            lien = lambda c: f'{e(c["n"])}. {c["titre"]}' if c["n"] else c["titre"]
            nav_bas = ""
            if i > 0:
                nav_bas += f'<a class="prec" href="{e(suite[i - 1]["f"])}"><small>{T["prec"]}</small>{lien(suite[i - 1])}</a>'
            if i + 1 < len(suite):
                nav_bas += f'<a class="suiv" href="{e(suite[i + 1]["f"])}"><small>{T["suiv"]}</small>{lien(suite[i + 1])}</a>'
            corps += f'\n<nav class="pied-nav" aria-label="{T["chapitre"]}s">{nav_bas}</nav>'
        elif i is None:
            avis.append(f"page hors de la suite du cours : construire « {page_nom} » sous le nom de sa source")

    # plan
    # sommaire affiché par défaut dès deux titres (sections ou sous-sections) ; « plan: non » l'ôte, « plan: oui » le force
    voulu = meta.get("plan", "auto").strip().lower()
    nav = ""
    if voulu in ("oui", "yes") or (voulu not in ("non", "no") and len(plan) >= 2):
        lignes, ouvert = [], False
        for niveau, ident, texte in plan:
            texte = re.sub(r"<a\b[^>]*>(.*?)</a>", r"\1", texte, flags=re.S)
            if niveau == 2:
                lignes.append(("</ol></li>" if ouvert else "</li>" if lignes else "") + f'<li><a href="#{ident}">{texte}</a>')
                ouvert = False
            else:
                lignes.append(("" if ouvert else "<ol>") + f'<li><a href="#{ident}">{texte}</a></li>')
                ouvert = True
        if lignes:
            lignes.append("</ol></li>" if ouvert else "</li>")
            nav = (f'<nav class="plan" id="plan" aria-labelledby="plan-titre"><p class="plan-titre" id="plan-titre">{T["plan"]}</p>'
                   f'<ol>{"".join(lignes)}</ol></nav>\n')

    # bloc de titre
    lettrine = meta.get("lettrine", "") or chapitre
    if lettrine.lower() in ("non", "no", "false"):
        lettrine = ""
    elif not lettrine:
        premier = next((c for c in unicodedata.normalize("NFD", titre_nu) if c.isalnum() and c.isascii()), "")
        lettrine = premier.upper()
    tete = ['<header class="titre">']
    if lettrine:
        tete.append(f'<span class="lettrine" aria-hidden="true">{e(lettrine)}</span>')
    if cours and chapitre and not meta.get("surtitre"):
        tete.append(f'<p class="surtitre"><a href="{e(cours["fichier_index"])}">{e(cours["nom"])}</a> · {T["chapitre"]} {e(chapitre)}</p>')
    elif meta.get("surtitre"):
        tete.append(f'<p class="surtitre">{e(meta["surtitre"])}</p>')
    tete.append(f"<h1>{titre_html}</h1>")
    if meta.get("soustitre"):
        tete.append(f'<p class="soustitre">{e(meta["soustitre"])}</p>')
    ligne = [e(meta["auteur"])] if meta.get("auteur") else []
    if meta.get("date"):
        ligne.append(date_lisible(meta["date"], lang))
    if ligne:
        tete.append(f'<p class="meta">{" · ".join(ligne)}</p>')
    tete.append("</header>")
    pied = f'<footer class="pied"><p>{e(meta["pied"])}</p></footer>\n' if meta.get("pied") else ""

    court = e(meta.get("court") or titre_nu)
    bouton_plan = (f'<button class="plan-bouton" type="button" aria-expanded="true" aria-controls="plan" aria-label="{T["bplan"]}" '
                   f'title="{T["bplan"]}">{LISTE}</button>') if nav else ""
    # actions de l'en-tête, seulement si la page a de quoi : replis, QCM et jouets, priorités
    actions, vu = [], sans_code(corps)
    if re.search(r"<details\b", vu):
        actions.append(("deplier", T["deplier"], DEPLIER))
    if re.search(r'class="(?:[^"]*\s)?(?:qcm|qnum|jouet)\b', vu):
        actions.append(("reinit", T["reinit"], REINIT))
    if "data-prio=" in vu:
        actions.append(("prio", T["prio"], ETOILE))
    boutons = "".join(f'<button class="action" type="button" data-action="{a}" aria-label="{t}" title="{t}">{i}</button>'
                      for a, t, i in actions)
    if actions:
        boutons += '<span class="statut sr" role="status" aria-live="polite"></span>'
    avertissement = meta.get("avertissement", "").strip()
    bandeau = ""
    if avertissement:
        texte = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", e(avertissement))
        bandeau = (f'<aside class="avertissement" aria-label="{T["avert"]}"><div class="avert-corps"><p>{texte}</p></div>'
                   f'<button type="button" class="avert-ok">{T["compris"]}</button></aside>\n')
    page = (
        f'<a class="evite" href="#contenu">{T["evite"]}</a>\n'
        + bandeau +
        f'<div class="page{" a-plan" if nav else ""}">\n'
        f'<div class="tete premiere"><span class="courant">{court}</span>'
        f'<span class="outils">{boutons}{bouton_plan}'
        f'<button class="theme" type="button" aria-label="{T["theme"]}" title="{T["theme"]}">{AUTO}</button></span>'
        f'<span class="filet" aria-hidden="true"></span></div>\n'
        + (couv["html"] if couv else "") + "\n".join(tete) + "\n" + nav
        + f'<main id="contenu" tabindex="-1">\n{corps.strip()}\n</main>\n{pied}</div>'
    )
    page, n_formules = formules(page)

    controle = Controle()
    controle.feed(page)
    controle.bilan()

    # styles, polices, scripts
    assets = (options.assets or meta.get("assets") or "").rstrip("/")
    mode = options.polices or meta.get("polices") or "embarquees"
    utiles = (set(TOUJOURS) | controle.polices | ({"texgyrechorus-mediumitalic"} if lettrine else set())
              | ({"lmroman10-italic"} if 'class="couv-sous"' in page else set()))
    motifs = sans_code(page)
    js = scripts(motifs)
    amorce = ('try{var t=localStorage.getItem("tx-theme");if(t==="light"||t==="dark")document.documentElement.dataset.theme=t;'
              'if(localStorage.getItem("tx-plan")==="0")document.documentElement.classList.add("sans-plan")}catch(e){}'
              'document.documentElement.classList.add("js")')
    # jouets : boîte à outils (Cours.) ; KaTeX dans la page seulement pour des formules écrites à l'exécution
    outils = bool(re.search(r"\bCours\.", motifs))
    katex_direct = bool(re.search(r"\bCours\.(?:tex|renderMath|ecrireTexte)\b", motifs))
    if outils:
        amorce = AMORCE_COURS + amorce
    if meta.get("avertissement", "").strip():
        amorce += (';try{var r=document.documentElement;if(localStorage.getItem(r.dataset.cle+"avertissement")==="1")'
                   'r.classList.add("avert-lu")}catch(e){}')
    kjs = ""
    if assets:
        liens = "".join(f'<link rel="preload" href="{assets}/polices/{f}.woff2" as="font" type="font/woff2" crossorigin>\n'
                        for f in ("lmroman10-regular", "lmsans10-bold"))
        if n_formules or outils:
            liens += f'<link rel="stylesheet" href="{assets}/katex.css">\n'
        liens += f'<link rel="stylesheet" href="{assets}/textured.css">\n'
        # sur un site : atelier.js (thème commun à tout le site, mesure d'audience) passe avant le premier rendu
        liens += f'<script src="{assets}/atelier.js"></script>\n'
        bloc_styles = liens
        bloc_script = (f'<script src="{assets}/katex.min.js" defer></script>\n' if katex_direct else "") + \
            f'<script src="{assets}/textured.js" defer></script>'
    else:
        css = (katex_css(page, katex_direct) if n_formules or outils else "") + styles(motifs, mode, utiles)
        kjs = (ASSETS / "katex.min.js").read_text(encoding="utf-8") if katex_direct else ""
        bloc_styles = f"<style>{css}</style>\n"
        bloc_script = (f"<script>{kjs}</script>\n" if kjs else "") + f"<script>\n{js}\n</script>"

    # politique de sécurité : scripts de la page par empreinte, rien d'autre que la page elle-même et des images https
    csp = ""
    if meta.get("csp", "oui") != "non":
        if controle.scripts_externes:
            avis.append("script externe (src=…) : politique de sécurité non posée ; embarquer le script ou assumer « csp: non »")
        else:
            en_ligne = [amorce] + re.findall(r"<script\b(?![^>]*\bsrc=)[^>]*>(.*?)</script>", page, re.S)
            if not assets:
                en_ligne.append(f"\n{js}\n")
            if kjs:
                en_ligne.append(kjs)
            empreintes = " ".join("'sha256-" + base64.b64encode(hashlib.sha256(s.encode()).digest()).decode() + "'" for s in en_ligne)
            soi = " 'self'" if assets else ""
            regles = (f"default-src 'none'; script-src {empreintes}{soi}; style-src 'unsafe-inline'{soi}; "
                      f"img-src 'self' data: https:; font-src 'self' data:; media-src 'self' data: https:; frame-src https:; "
                      + ("connect-src 'self'; " if assets else "") + "base-uri 'none'; form-action 'none'")
            csp = f'<meta http-equiv="Content-Security-Policy" content="{regles}">\n'

    description = meta.get("description", "")
    if not description:
        avis.append("pas de description : ajouter « description: … » (une phrase, pour les moteurs et les aperçus de lien)")
    tetiere = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{e(titre_nu)}</title>",
        csp.strip(),
        '<meta name="color-scheme" content="light dark">',
        '<meta name="text-scale" content="scale">',
        '<meta name="theme-color" content="#f9fafb" media="(prefers-color-scheme: light)">',
        '<meta name="theme-color" content="#292929" media="(prefers-color-scheme: dark)">',
        f'<meta name="description" content="{e(description)}">' if description else "",
        f'<meta name="author" content="{e(meta["auteur"])}">' if meta.get("auteur") else "",
        '<meta name="robots" content="noindex, nofollow">' if meta.get("prive", "non") == "oui" else "",
        '<meta name="generator" content="TeXtured HTML">',
    ]
    if meta.get("url"):
        tetiere += [f'<link rel="canonical" href="{e(meta["url"])}">', '<meta property="og:type" content="article">',
                    f'<meta property="og:title" content="{e(titre_nu)}">', f'<meta property="og:url" content="{e(meta["url"])}">']
        if description:
            tetiere.append(f'<meta property="og:description" content="{e(description)}">')
        if meta.get("image"):
            tetiere.append(f'<meta property="og:image" content="{e(meta["image"])}">')
            if meta.get("_apercu"):
                tetiere += ['<meta property="og:image:width" content="1200">', '<meta property="og:image:height" content="630">']
            tetiere.append('<meta name="twitter:card" content="summary_large_image">')
    versions = [(c.strip(), a.strip()) for c, _, a in (p.partition("=") for p in meta.get("langues", "").split(",") if p.strip())]
    # x-default : la première version citée (le français, sur le site), si l'en-tête n'en nomme pas
    if versions and not any(c == "x-default" for c, _ in versions):
        versions.append(("x-default", versions[0][1]))
    for code, adresse in versions:
        tetiere.append(f'<link rel="alternate" hreflang="{e(code)}" href="{e(adresse)}">')
    tetiere.append(f'<link rel="icon" href="{e(meta.get("icone") or ICONE)}">')
    densite = ' data-densite="compacte"' if meta.get("densite", "").startswith("compact") else ""
    if tirage and re.fullmatch(r"#[0-9a-fA-F]{3,8}", tirage):
        densite += f' data-tirage style="--tirage:{tirage}"'
    elif tirage:
        avis.append("tirage : attendre une couleur hexadécimale, par exemple « tirage: #00a95c »")
    # stockage local (filtre des priorités, bandeau lu, jouets) : par cours, sinon par page
    if cours or outils or avertissement or "data-prio=" in motifs:
        cle = cours["cle"] if cours else f"tx:{slug(titre_nu)}:"
        densite += f' data-cle="{e(cle)}" data-page="{e(page_nom)}"'
    sortie = (
        f'<!doctype html>\n<html lang="{e(meta.get("lang", "fr"))}"{densite}>\n<head>\n'
        + "\n".join(t for t in tetiere if t) + f"\n<script>{amorce}</script>\n{bloc_styles}</head>\n<body>\n{page}\n{bloc_script}\n</body>\n</html>\n"
    )
    bilan = {"sections": sum(1 for p in plan if p[0] == 2), "formules": n_formules, "plan": bool(nav),
             "polices": "liées" if assets else mode, "encre": (tirage or "aucune") + (" (auto)" if encre_auto else ""),
             "jouets": len(re.findall(r'class="jouet\b', motifs)), "cours": cours, "couverture": couv["resume"] if couv else ""}
    return sortie, bilan


# ---------- PDF et image de partage (navigateur sans interface) ----------

def navigateur():
    """Chrome ou Chromium ; à défaut Edge (toujours là sous Windows) ou Brave. TEXTURED_NAVIGATEUR impose un chemin."""
    impose = os.environ.get("TEXTURED_NAVIGATEUR")
    if impose:
        return impose if Path(impose).is_file() else shutil.which(impose)
    if sys.platform == "darwin":
        noms = ("Google Chrome", "Chromium", "Microsoft Edge", "Brave Browser")
        candidats = [Path(r) / f"{n}.app/Contents/MacOS/{n}" for n in noms for r in ("/Applications", Path.home() / "Applications")]
    elif sys.platform == "win32":
        racines = [os.environ[v] for v in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA") if os.environ.get(v)]
        candidats = ([Path(r) / "Google/Chrome/Application/chrome.exe" for r in racines]
                     + [Path(r) / "Microsoft/Edge/Application/msedge.exe" for r in racines])
    else:
        candidats = [shutil.which(n) for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                                               "microsoft-edge", "microsoft-edge-stable", "brave-browser")]
    return next((str(c) for c in candidats if c and Path(c).is_file()), None)


def autonome(sortie, meta, corps, dossier, options, base, cours=None, page_nom="page.html"):
    """La page telle que le navigateur sans interface l'ouvre depuis un dossier temporaire : tout embarqué (en mode
    --assets, elle est reconstruite sans les liens vers le site), politique de sécurité ôtée pour que <base> renvoie
    les images liées au dossier de la page."""
    if options.assets or meta.get("assets"):
        n_avis, n_erreurs = len(avis), len(erreurs)
        seule = argparse.Namespace(**{**vars(options), "assets": None})
        sortie, _ = construire({k: v for k, v in meta.items() if k != "assets"}, corps, dossier, seule, cours, page_nom)
        del avis[n_avis:], erreurs[n_erreurs:]
    sortie = re.sub(r'<meta http-equiv="Content-Security-Policy"[^>]*>\n?', "", sortie, count=1)
    return sortie.replace("<head>\n", f'<head>\n<base href="{html.escape(base)}">\n', 1)


def rendre(page, cible, mode):
    """Ouvre la page dans le navigateur sans interface et écrit cible : PDF (mode « pdf ») ou capture JPEG 1200 × 630
    du haut de la page, en thème clair (mode « apercu »). Rend une description de ce qui a été écrit, ou None."""
    nav = navigateur()
    if not nav:
        erreurs.append(f"{mode} : ni Chrome ni Edge trouvé (TEXTURED_NAVIGATEUR=chemin de l'exécutable pour en désigner un)")
        return None
    with tempfile.TemporaryDirectory(prefix="textured-", ignore_cleanup_errors=True) as tmp:
        tmp = Path(tmp)
        source, produit = tmp / "page.html", tmp / ("page.pdf" if mode == "pdf" else "page.jpg")
        if mode == "apercu":
            # l'image montre le document, pas les boutons de l'en-tête ; une couverture s'y pose à droite du titre
            page = page.replace("</head>", "<style>.tete .outils{visibility:hidden}</style>\n</head>", 1)
            if 'class="couverture ' in page:
                page = page.replace("<html ", '<html class="tx-apercu" ', 1)
        source.write_text(page, encoding="utf-8")
        commande = [nav, "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                    f"--user-data-dir={tmp / 'profil'}", "--virtual-time-budget=8000"]
        if mode == "pdf":
            commande += ["--no-pdf-header-footer", "--print-to-pdf-no-header", f"--print-to-pdf={produit}"]
        else:
            # 800 × 420 vus à 1,5 : la colonne de lecture remplit l'image et le titre reste lisible en vignette
            commande += ["--hide-scrollbars", "--window-size=800,420", "--force-device-scale-factor=1.5", f"--screenshot={produit}"]
        try:
            subprocess.run(commande + [source.as_uri()], capture_output=True, timeout=180)
        except (OSError, subprocess.TimeoutExpired) as x:
            erreurs.append(f"{mode} : {Path(nav).name} a échoué ({x.__class__.__name__})")
            return None
        if not produit.is_file() or produit.stat().st_size == 0:
            erreurs.append(f"{mode} : {Path(nav).name} n'a rien écrit")
            return None
        donnees = produit.read_bytes()
        try:
            cible.write_bytes(donnees)
        except OSError as x:
            erreurs.append(f"{mode} : impossible d'écrire {cible} ({x.strerror or x} ; fichier ouvert ailleurs ?)")
            return None
    if mode == "pdf":
        pages = len(re.findall(rb"/Type\s*/Page(?![a-zA-Z])", donnees))
        return f"{cible} · {pages} page{'s' if pages > 1 else ''} A4 · {Path(nav).stem}" if pages else f"{cible} · {Path(nav).stem}"
    taille = taille_image(donnees)
    return f"{cible} · {taille[0]} × {taille[1]}" if taille else str(cible)


def exporter(dossier):
    dossier = Path(dossier).expanduser()
    (dossier / "polices").mkdir(parents=True, exist_ok=True)
    css = "\n".join((ASSETS / f).read_text(encoding="utf-8") for f in FEUILLES)
    (dossier / "textured.css").write_text(minifier(re.sub(r"/\*@.*?\*/", "", css)), encoding="utf-8")
    js = (ASSETS / "textured.js").read_text(encoding="utf-8")
    (dossier / "textured.js").write_text(re.sub(r"/\*.*?\*/\n?", "", js, flags=re.S).strip() + "\n", encoding="utf-8")
    shutil.copy(ASSETS / "katex.css", dossier / "katex.css")
    shutil.copy(ASSETS / "katex.min.js", dossier / "katex.min.js")   # formules écrites à l'exécution (Cours.tex)
    for f in (ASSETS / "polices").glob("*.woff2"):
        shutil.copy(f, dossier / "polices" / f.name)
    print(f"textured : feuille de style, moteur, KaTeX et polices exportés dans {dossier}")


def page(src, cible, o):
    """Construit une page : source (Path, ou None pour l'entrée standard), cible .html ; rend le code de sortie."""
    avis.clear(); erreurs.clear()
    meta, brut = lire_source(src if src else "-")
    if o.couverture:
        meta["couverture"] = o.couverture
    est_html = src is not None and src.suffix.lower() in (".html", ".htm")
    corps = brut if est_html else markdown(brut)
    # cours : un chapitre reprend de l'accueil ce qu'il ne dit pas (encre, densité, auteur, langue…)
    cours = cours_de(src)
    if cours and (meta.get("chapitre") or nom_sortie(src).name == cours["fichier_index"]):
        for k in HERITES:
            if k not in meta and k in cours["index"]:
                meta[k] = cours["index"][k]
    else:
        cours = None
    # image de partage : preview.jpg à côté d'un index.html (comme les autres pages du site), nom.preview.jpg sinon
    apercu = cible.with_name("preview.jpg" if cible.name == "index.html" else cible.stem + ".preview.jpg") if o.apercu else None
    if apercu and not meta.get("url"):
        avis.append("--apercu sans « url: » dans l'en-tête : image écrite, mais sans balises de partage (og:image veut une adresse absolue)")
    elif apercu and not meta.get("image"):
        adresse = meta["url"].rstrip("/") + "/" if cible.name == "index.html" else meta["url"]
        meta["image"], meta["_apercu"] = urljoin(adresse, apercu.name), "oui"
    dossier = src.parent if src else Path.cwd()
    page_nom = nom_sortie(src).name if src else cible.name
    if o.planche:
        lang = meta.get("lang", "fr")[:2].lower()
        encre = meta.get("tirage") or encre_par_defaut(cours["nom"] if cours else nu(html.escape(meta.get("titre", ""))))
        meta_p = {"titre": "Couvertures", "soustitre": meta.get("titre", ""), "surtitre": "Planche", "plan": "non",
                  "lettrine": "non", "prive": "oui", "lang": lang, "tirage": encre,
                  "description": "Chaque motif de couverture, pour choisir la ligne « couverture: » de l'en-tête."}
        corps_t, plan_t, _ = titres(blocs_titres(corps, TEXTES.get(lang, TEXTES["en"])), dict(meta))
        planche = couverture.planche(dict(meta, tirage=encre), corps_t, plan_t, lang, avis, corps)
        ecrite, _ = construire(meta_p, planche, dossier, o)
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.with_name(cible.stem + ".couvertures.html").write_text(ecrite, encoding="utf-8")
    sortie, bilan = construire(meta, corps, dossier, o, cours, page_nom)
    cible.parent.mkdir(parents=True, exist_ok=True)
    cible.write_text(sortie, encoding="utf-8")
    produits = []
    if o.pdf or apercu:
        rendu = autonome(sortie, meta, corps, dossier, o, cible.resolve().parent.as_uri() + "/", cours, page_nom)
        if o.pdf:
            produits.append(("pdf", rendre(rendu, cible.with_suffix(".pdf"), "pdf")))
        if apercu:
            produits.append(("aperçu", rendre(rendu, apercu, "apercu")))
    poids = len(sortie.encode()) / 1024
    etat = "ERREURS" if erreurs else "OK"
    extra = f" · {bilan['jouets']} jouet{'s' if bilan['jouets'] > 1 else ''}" if bilan["jouets"] else ""
    if bilan["cours"]:
        extra += f" · cours « {bilan['cours']['nom']} » ({len(bilan['cours']['chapitres'])} chapitres)"
    print(f"{etat} {cible} · {poids:.0f} Ko · {bilan['sections']} sections · {bilan['formules']} formules · "
          f"plan {'oui' if bilan['plan'] else 'non'} · polices {bilan['polices']} · encre {bilan['encre']}{extra}")
    if bilan["couverture"]:
        print(f"  couverture : {bilan['couverture']}")
    for nom, ecrit in produits:
        if ecrit:
            print(f"  {nom} : {ecrit}")
    for x in erreurs[:30]:
        print("  erreur : " + x)
    for x in list(dict.fromkeys(avis))[:30]:
        print("  avis : " + x)
    if o.ouvrir:
        if sys.platform == "win32":
            os.startfile(str(cible))
        else:
            subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", str(cible)], check=False)
    return 2 if erreurs else 0


def main():
    p = argparse.ArgumentParser(description="Assemble une page TeXtured HTML à partir d'une source Markdown ou HTML.")
    p.add_argument("source", nargs="?", help="fichier .md ou .tx.html (« - » : entrée standard, Markdown), ou un dossier "
                                             "(toutes ses sources : un cours entier)")
    p.add_argument("-o", "--sortie", help="fichier produit (défaut : même nom, en .html) ; pour un dossier, dossier de sortie")
    p.add_argument("--ouvrir", action="store_true", help="ouvrir la page dans le navigateur")
    p.add_argument("--polices", choices=["embarquees", "locales"], help="embarquees (défaut) ou locales (Latin Modern du système)")
    p.add_argument("--assets", help="adresse d'un dossier exporté (site) : styles, moteur et polices liés au lieu d'être embarqués")
    p.add_argument("--images", choices=["embarquees", "liees"], default="embarquees")
    p.add_argument("--pdf", action="store_true", help="écrire aussi nom.pdf (A4) à côté de la page : Chrome sans interface, ou Edge")
    p.add_argument("--apercu", action="store_true",
                   help="image de partage 1200 × 630 (haut de la page, thème clair) à côté de la page ; og:image si l'en-tête a url:")
    p.add_argument("--couverture", nargs="?", const="oui", metavar="MOTIF",
                   help="couverture du document (comme « couverture: » dans l'en-tête, qu'elle remplace) ; voir couverture.md")
    p.add_argument("--planche", action="store_true", help="écrire aussi nom.couvertures.html : la couverture dans chaque motif, pour choisir")
    p.add_argument("--exporter", metavar="DOSSIER", help="écrire les fichiers partagés pour un site, puis quitter")
    o = p.parse_args()
    if o.exporter:
        exporter(o.exporter)
        return 0
    if not o.source:
        p.error("source manquante")
    if o.source == "-":
        if not o.sortie:
            p.error("avec « - », préciser -o")
        return page(None, Path(o.sortie), o)
    src = Path(o.source)
    if src.is_dir():
        sources = sorted(f for f in src.iterdir() if f.suffix.lower() == ".md" or f.name.lower().endswith((".tx.html", ".src.html")))
        if not sources:
            p.error(f"aucune source (.md, .tx.html) dans {src}")
        sortie = Path(o.sortie) if o.sortie else src
        ouvrir, codes = o.ouvrir, []
        for f in sources:
            o.ouvrir = ouvrir and nom_sortie(f).name == "index.html"
            codes.append(page(f, sortie / nom_sortie(f).name, o))
        return max(codes)
    if src.suffix.lower() in (".html", ".htm") and not o.sortie and nom_sortie(src) == src:
        p.error("source HTML : la nommer « nom.tx.html » ou préciser -o, pour ne pas l'écraser")
    return page(src, Path(o.sortie) if o.sortie else nom_sortie(src), o)


if __name__ == "__main__":
    sys.exit(main())
