#!/usr/bin/env python3
"""Vérification du skill : construit exemple.md et le cours d'exemple dans un dossier temporaire et exige des bilans
propres (« OK », aucune ligne « erreur : » ni « avis : »), avec une couverture et sa planche ; compose chaque motif dans
chaque place et chaque teinte, sur plusieurs tirages ; contrôle favicons et titres d'onglet (le même favicon sur tout le
cours, l'icône d'écran d'accueil d'une page publiée, les clés icone: et onglet:, les dessins sur mesure) ; si un
navigateur Chromium est là, ouvre chaque page à jouets sans interface et exige que leur code ait tourné sans erreur ;
avec --pdf, produit aussi le PDF de exemple.md et celui d'une page à couverture.

    python3 tests/verifier.py [--pdf]

Code de sortie : 0 si tout est propre, 1 sinon.
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent
sys.path.insert(0, str(RACINE))
import textured  # noqa: E402
import couverture  # noqa: E402
import icone  # noqa: E402
import motifs  # noqa: E402

echecs = []

ENTIERE = """---
titre: Une couverture entière
court: Essai
soustitre: dessinée à la main
auteur: A. Auteur
date: 2026-11-19
description: Couverture entière dessinée, favicon dessiné, titre d'onglet choisi.
tirage: #765ba7
couverture: claire
onglet: Essai de couverture
url: https://exemple.org/essai.html
---

::: couverture
<svg viewBox="0 0 200 300">
<rect width="200" height="300" fill="var(--cf)"/>
<circle cx="100" cy="110" r="60" fill="var(--ca)"/>
<text x="16" y="250" font-size="24">{TITRE}</text>
<text x="16" y="270" font-size="9" font-weight="400">{auteur} · {annee}</text>
</svg>
:::

::: icone
<svg viewBox="0 0 32 32"><circle cx="16" cy="16" r="9" stroke="currentColor" stroke-width="3"/><circle cx="16" cy="16" r="3" fill="var(--ca)"/></svg>
:::

## Une section

Du texte.

## Une autre

Encore du texte.
"""


# Sujets, en français et en anglais : chacun doit désigner son motif (premier ex aequo admis) ; à droite de « ≠ »,
# un sujet d'un autre domaine qui ne doit pas tomber sur ce motif.
SUJETS = {
    # sciences du vivant, médecine, informatique, ingénierie, sciences humaines
    "Phylogénie des primates": "phylogenie", "Natural selection and speciation": "phylogenie",
    "Mitose et cycle cellulaire": "division", "Stem cells and cancer": "division",
    "Proies et prédateurs": "proies", "Ecosystems and food webs": "proies",
    "Neurosciences cognitives": "influx", "Synaptic plasticity": "influx",
    "Immunologie des vaccins": "clones", "Antibodies and antigens": "clones",
    "Épidémiologie des maladies infectieuses": "contagion", "Epidemic modelling": "contagion",
    "Dépistage et biomarqueurs": "depistage", "Clinical medicine": "depistage",
    "Imagerie médicale": "sinogramme", "Medical imaging: MRI and CT": "sinogramme",
    "Réseaux de neurones": "perceptron", "Artificial intelligence": "perceptron",
    "Apprentissage automatique": "grappes", "Machine learning": "grappes",
    "Cryptographie": "brassage", "Hash functions and encryption": "brassage",
    "Algorithmes de tri": "tri", "Data structures": "tri",
    "Électronique numérique": "pistes", "Printed circuit boards": "pistes",
    "Traitement du signal": "harmoniques", "Signal processing and filtering": "harmoniques",
    "Transition énergétique": "rubans", "Renewable energy": "rubans",
    "Robotique": "poses", "Robot kinematics": "poses",
    "Macroéconomie": "volatilite", "Economics of financial markets": "volatilite",
    "Sociologie urbaine": "schelling", "Residential segregation": "schelling",
    "Démographie": "pyramide", "Population ageing": "pyramide",
    "Histoire contemporaine": "frise", "Medieval history": "frise",
    "Dérive génétique et coalescence": "derive", "Population genetics": "derive",
    "Génomique comparée": "alignement", "Sequence alignment": "alignement",
    "Morphogenèse et motifs de Turing": "morphogenese", "Developmental biology": "morphogenese",
    "Rythmes circadiens": "circadien", "Biological clocks and jet lag": "circadien",
    "Repliement des protéines": "repliement", "Protein folding": "repliement",
    "Lois de Mendel": "mendel", "Mendelian inheritance": "mendel",
    "Recombinaison et crossing-over": "recombinaison", "Chromosome recombination": "recombinaison",
    "Pharmacologie": "dose", "Dose-response curves": "dose",
    "Analyse de survie": "survie", "Clinical trials": "survie",
    "Troubles du sommeil": "sommeil", "Sleep medicine": "sommeil",
    "Électrophorèse et PCR": "electrophorese", "Gel electrophoresis and PCR": "electrophorese",
    "Physiologie et homéostasie": "homeostasie", "Endocrinology": "homeostasie",
    "Les grands modèles de langage": "attention", "Large language models": "attention",
    "Arbres de décision": "decision", "Random forests": "decision",
    "Plus courts chemins": "dedale", "Shortest path algorithms": "dedale",
    "Traitement d'images": "quadrants", "Image compression": "quadrants",
    "IA générative": "debruitage", "Diffusion models": "debruitage",
    "Numération binaire": "binaire", "Computer architecture": "binaire",
    "Télécommunications numériques": "symboles", "Wireless communications": "symboles",
    "Génie civil": "isostatiques", "Structural engineering": "isostatiques",
    "Mix énergétique": "mix", "Electricity consumption": "mix",
    "Robotique mobile et SLAM": "lidar", "Autonomous vehicles": "lidar",
    "Reconnaissance vocale": "spectrogramme", "Speech processing": "spectrogramme",
    "Fabrication additive": "parcours", "3D printing": "parcours",
    "Analyse syntaxique": "syntaxe", "Dependency parsing": "syntaxe",
    "Migrations internationales": "migrations", "International trade": "migrations",
    "Inégalités de revenu": "fortunes", "Wealth inequality": "fortunes",
    "Élections législatives": "hemicycle", "Political science": "hemicycle",
    "Généalogie": "ascendance", "Family history": "ascendance",
    "Théorie des jeux": "nash", "Game theory": "nash",
}
HORS_SUJET = {
    # sciences du vivant, médecine, informatique, ingénierie, sciences humaines
    "Microscopie électronique à balayage": "pistes", "Vieillissement des polymères": "pyramide", "Volatilité relative": "volatilite",
    "Inégalités de Cauchy-Schwarz": "schelling", "Période d'un pendule": "frise", "Énergie libre de mélange": "rubans",
    "Électricité et magnétisme": "rubans", "Cinématique du point": "poses", "Loi de Fourier et conduction thermique": "harmoniques",
    "Harmonic oscillator": "harmoniques", "Diffraction des rayons X": "sinogramme", "Espèces endémiques": "contagion",
    "Essai de compression": "quadrants", "Diagrammes binaires liquide-vapeur": "binaire", "Ponts hydrogène": "isostatiques",
    "Mobilité des porteurs de charge": "migrations", "Attracteur de Lorenz": "fortunes", "Nuage de points et régression": "lidar",
    "Dosage acido-basique": "dose", "Laser beam focusing": "isostatiques", "Diffusion de la chaleur": "debruitage",
    "Classification périodique": "decision", "Inflation cosmique": "volatilite", "Énergie libre de mélange": "mix",
}


def sujets():
    """Les mots du sujet désignent le bon motif, en français et en anglais, sans prendre ceux d'un autre domaine ;
    chaque motif a sa marque de favicon."""
    avant = len(echecs)
    for sujet, attendu in SUJETS.items():
        sc = couverture.proposer(sujet)
        if attendu not in [m for m, s in sc if s == sc[0][1]]:
            echecs.append(f"sujet « {sujet} » : {attendu} attendu, {', '.join(m for m, _ in sc[:3]) or 'aucun motif'}")
    for sujet, exclu in HORS_SUJET.items():
        sc = couverture.proposer(sujet)
        if exclu in [m for m, s in sc if s == sc[0][1]]:
            echecs.append(f"sujet « {sujet} » : {exclu} ne devrait pas venir")
    sans_marque = [m for m in motifs.MOTIFS if not icone.marque(m)]
    if sans_marque:
        echecs.append("motifs sans marque de favicon : " + ", ".join(sans_marque))
    print(f"  {len(SUJETS)} sujets, {len(HORS_SUJET)} hors sujet, marques des motifs : {'erreur' if len(echecs) > avant else 'ok'}")


def balise(page, motif):
    m = re.search(motif, page)
    return m.group(0) if m else ""


def motifs_et_glyphes():
    """Chaque motif dans chaque place et chaque teinte, sur quelques tirages ; chaque glyphe en SVG et en PNG."""
    d = couverture.mesurer("<p>Un texte de quelques mots pour mesurer.</p>", [], "Essai")
    meta = {"titre": "Essai de couverture", "auteur": "A. Auteur", "date": "2026", "soustitre": "un sous-titre"}
    for nom in motifs.MOTIFS:
        for k, (teinte, place) in enumerate((t, p) for t in ("claire", "encre", "sombre") for p in ("haut", "bas", "plein", "fond")):
            try:
                h = couverture.composer(meta, d, "fr", nom, teinte, place, "#0078bf", 1000 + 37 * k)
                if "<svg" not in h:
                    echecs.append(f"motif {nom} ({teinte}, {place}) : pas de dessin")
            except Exception as x:  # noqa: BLE001
                echecs.append(f"motif {nom} ({teinte}, {place}) : {x!r}")
    sans_mots = [m for m, liste in motifs.INDICES.items() if not liste]
    if sans_mots:
        echecs.append("motifs sans mots du sujet : " + ", ".join(sans_mots))
    pal = couverture.palette("#00a95c", "encre")
    for nom, prims in icone.GLYPHES.items():
        try:
            if not icone.png(prims, pal, 32).startswith(b"\x89PNG") or "<svg" not in icone.dessiner(nom, pal):
                echecs.append(f"glyphe {nom} : rendu vide")
        except Exception as x:  # noqa: BLE001
            echecs.append(f"glyphe {nom} : {x!r}")
    print(f"  {len(motifs.MOTIFS)} motifs × 4 places × 3 teintes, {len(icone.GLYPHES)} marques : "
          f"{'erreur' if any(x.startswith(('motif', 'glyphe')) for x in echecs) else 'ok'}")


# Le sujet d'un document (en français et en anglais) doit désigner son motif, seul en tête de --motifs ; un bloc par
# domaine.
CHOIX = {}
# sciences exactes : physique et astronomie, Terre et climat, mathématiques, chimie générale
CHOIX.update({
    "Interférences et diffraction de la lumière": "interference", "Wave optics and interference": "interference",
    "Relativité générale et trous noirs": "geodesiques", "General relativity and spacetime": "geodesiques",
    "Physique statistique : le modèle d'Ising": "ising", "Statistical mechanics of magnetism": "ising",
    "Formation des galaxies": "galaxie", "Stellar astrophysics": "galaxie",
    "Introduction à la cosmologie": "cosmique", "Dark matter and the cosmic web": "cosmique",
    "Géologie structurale : plis et failles": "plissement", "Sedimentary geology": "plissement",
    "Sismologie et ondes sismiques": "sismogramme", "Earthquake seismology": "sismogramme",
    "Océanographie physique": "gyres", "Ocean circulation and eddies": "gyres",
    "Météorologie dynamique": "isobares", "Weather forecasting": "isobares",
    "Le changement climatique": "rechauffement", "Climate change and global warming": "rechauffement",
    "Équations différentielles ordinaires": "isoclines", "Ordinary differential equations": "isoclines",
    "Systèmes dynamiques et chaos": "attracteur", "Chaos theory and strange attractors": "attracteur",
    "Algèbre : théorie des groupes": "modulo", "Modular arithmetic": "modulo",
    "Probabilités et variables aléatoires": "galton", "Probability theory": "galton",
    "Théorie des nœuds": "entrelacs", "Knot theory and braids": "entrelacs",
    "Théorie des nombres : les nombres premiers": "ulam", "Prime numbers": "ulam",
    "Spectroscopie infrarouge et RMN": "raies", "Infrared spectroscopy": "raies",
    "Électrochimie et corrosion": "electrode", "Batteries and electrochemistry": "electrode",
    "Chimie quantique : orbitales moléculaires": "orbitales", "Quantum chemistry": "orbitales",
    "Chimie analytique : chromatographie": "chromato", "Gas chromatography": "chromato",
})
# sciences exactes, suite
CHOIX.update({
    "Électrostatique et champ électrique": "dipole", "Electric fields and charges": "dipole",
    "Champ magnétique et aimants": "limaille", "Magnetic fields and solenoids": "limaille",
    "Mécanique céleste": "kepler", "Orbital mechanics": "kepler",
    "Oscillateurs harmoniques": "lissajous", "Harmonic oscillators and pendulums": "lissajous",
    "Modes propres et ondes stationnaires": "chladni", "Standing waves and normal modes": "chladni",
    "Physique des particules": "collision", "Particle physics at the LHC": "collision",
    "Physique du solide": "brillouin", "Solid state physics and band structure": "brillouin",
    "Physique des plasmas et fusion nucléaire": "chirikov", "Hamiltonian chaos and the standard map": "chirikov",
    "Évolution stellaire": "hertzsprung", "Stellar evolution and the main sequence": "hertzsprung",
    "Observer le ciel nocturne": "circumpolaire", "Astrophotography of the night sky": "circumpolaire",
    "Lentilles gravitationnelles": "lentille", "Strong and weak lensing": "lentille",
    "Paquets d'ondes et équation de Schrödinger": "paquets", "Wave packets and dispersion": "paquets",
    "Supraconductivité": "abrikosov", "Superconductors and quantum vortices": "abrikosov",
    "Cartographie et géomorphologie": "hachures", "Terrain and hillshade": "hachures",
    "Volcanologie": "orgues", "Basalt and columnar jointing": "orgues",
    "La banquise arctique": "banquise", "Sea ice and the cryosphere": "banquise",
    "Hydrologie des bassins versants": "affluents", "River networks and watersheds": "affluents",
    "Circulation atmosphérique et courant-jet": "rossby", "The jet stream and Rossby waves": "rossby",
    "Précipitations et orages": "averse", "Rainfall and monsoons": "averse",
    "Paléoclimat et carottes glaciaires": "carottes", "Ice cores and paleoclimate": "carottes",
    "Tectonique des plaques": "dorsale", "Plate tectonics and seafloor spreading": "dorsale",
    "Les dunes du désert": "dunes", "Aeolian sand transport": "dunes",
    "Physique des nuages": "nebulosite", "Cloud cover from satellite imagery": "nebulosite",
    "Hydrogéologie des milieux poreux": "poreux", "Groundwater and aquifers": "poreux",
    "Aléa sismique": "epicentres", "Seismicity and active faults": "epicentres",
    "L'ensemble de Mandelbrot": "mandelbrot", "Fractal geometry": "mandelbrot",
    "Courbes de Hilbert et de Peano": "hilbert", "Space-filling curves": "hilbert",
    "Pavages apériodiques": "penrose", "Penrose tilings and quasicrystals": "penrose",
    "La baderne d'Apollonius": "apollonius", "Circle packing": "apollonius",
    "Le nombre d'or": "angledor", "The golden ratio and Fibonacci": "angledor",
    "La conjecture de Syracuse": "collatz", "The Collatz conjecture": "collatz",
    "Théorie des graphes et coloration": "quatrecouleurs", "Graph coloring": "quatrecouleurs",
    "Séries de Fourier": "epicycles", "Fourier series and harmonic analysis": "epicycles",
    "Géométrie hyperbolique": "hyperbolique", "Non-Euclidean geometry": "hyperbolique",
    "Tableaux de Young": "young", "Integer partitions": "young",
    "Analyse complexe": "complexe", "Complex analysis": "complexe",
    "Courbes paramétrées": "spirographe", "Spirograph curves": "spirographe",
    "Algèbre linéaire": "tesseract", "The fourth dimension": "tesseract",
    "Cristallographie et diffraction des rayons X": "laue", "X-ray crystallography": "laue",
    "Le tableau périodique": "mendeleiev", "The periodic table of elements": "mendeleiev",
    "Réactions oscillantes": "belousov", "The Belousov-Zhabotinsky reaction": "belousov",
    "Anneaux de Liesegang": "liesegang", "Periodic precipitation": "liesegang",
    "Théorie cinétique des gaz": "maxwell", "Kinetic theory of gases": "maxwell",
    "Chimie des solutions": "solvatation", "Solvation and solubility": "solvatation",
    "Chiralité et stéréochimie": "miroir", "Chirality and enantiomers": "miroir",
    "Nucléation et croissance cristalline": "nucleation", "Crystal growth and nucleation": "nucleation",
    "Spectroscopie RMN": "multiplets", "NMR spectroscopy": "multiplets",
    "Agrégation des colloïdes": "agregat", "Colloid aggregation": "agregat",
    "Osmose et pression osmotique": "osmose", "Osmosis": "osmose",
    "Zéolithes et catalyse hétérogène": "zeolithe", "Zeolites and porous materials": "zeolithe",
})


def choix_par_sujet():
    """Chaque sujet de CHOIX désigne son motif, seul en tête ; chaque motif a sa marque de favicon."""
    faux = []
    for sujet, attendu in CHOIX.items():
        p = couverture.proposer(sujet, 4)
        tete = [m for m, sc in p if p and sc == p[0][1]]
        if tete != [attendu]:
            faux.append(f"« {sujet} » → {', '.join(tete) or 'rien'} (attendu : {attendu})")
    echecs.extend("choix du motif : " + f for f in faux)
    sans_marque = [m for m in motifs.MOTIFS if m not in icone.MARQUE_DE]
    if sans_marque:
        echecs.append("motifs sans marque de favicon : " + ", ".join(sans_marque))
    print(f"  {len(CHOIX)} sujets → motif : {'erreur' if faux or sans_marque else 'ok'}")


def favicons(tmp):
    """Le même favicon sur tout le cours, titres d'onglet, clés icone: et onglet:, dessins sur mesure."""
    pages = {f.name: f.read_text(encoding="utf-8") for f in (tmp / "cours").glob("*.html")}
    icones = {n: balise(p, r'<link rel="icon" type="image/svg\+xml" href="[^"]+">') for n, p in pages.items()}
    if not all(icones.values()) or len(set(icones.values())) != 1:
        echecs.append("cours : favicon absent ou différent d'une page à l'autre")
    if "<title>Chapitre 1 · " not in pages.get("01-flory-huggins.html", ""):
        echecs.append("chapitre : titre d'onglet « Chapitre 1 · … — cours » absent")
    src = tmp / "essai.md"
    src.write_text(ENTIERE, encoding="utf-8")
    lancer([str(src), "-o", str(tmp / "essai.html"), "--icones"])
    page = (tmp / "essai.html").read_text(encoding="utf-8")
    for attendu, quoi in (('class="couverture couv-entiere', "couverture entière"), ("<title>Essai de couverture</title>", "onglet:"),
                          ('property="og:title" content="Essai de couverture"', "og:title"),
                          ('rel="apple-touch-icon" href="data:image/png;base64,', "apple-touch-icon"), ("ESSAI</text>", "{TITRE}")):
        if attendu not in page:
            echecs.append(f"page d'essai : {quoi} absent")
    if "A. Auteur · 2026" not in page:
        echecs.append("page d'essai : {auteur} · {annee} non remplacés")
    if 'class="icone"' in page or "%3Ccircle cx='16' cy='16' r='9'" not in page:
        echecs.append("page d'essai : favicon dessiné (::: icone) absent ou bloc resté dans la page")
    if not (tmp / "essai.icones.html").is_file():
        echecs.append("planche des favicons absente")
    for valeur, attendu in (("icone: lettre", "font-weight='700'"), ("icone: non", None), ("icone: https://exemple.org/i.png", 'href="https://exemple.org/i.png"')):
        f = tmp / "icone.md"
        f.write_text(f"---\ntitre: Essai\ndescription: Essai.\n{valeur}\n---\n\nTexte.\n", encoding="utf-8")
        lancer([str(f), "-o", str(tmp / "icone.html")])
        p = (tmp / "icone.html").read_text(encoding="utf-8")
        if attendu is None and 'rel="icon"' in p:
            echecs.append("icone: non : un favicon est posé")
        elif attendu and attendu not in p:
            echecs.append(f"{valeur} : favicon attendu absent")


def lancer(args):
    r = subprocess.run([sys.executable, str(RACINE / "textured.py"), *args], capture_output=True, text=True)
    sortie = r.stdout + r.stderr
    print(sortie.rstrip())
    for ligne in sortie.splitlines():
        if ligne.startswith(("ERREURS ", "textured :")) or ligne.strip().startswith(("erreur :", "avis :")):
            echecs.append(ligne.strip())
    if r.returncode not in (0,):
        echecs.append(f"code de sortie {r.returncode} pour {' '.join(args)}")
    return sortie


def jouets(page, nav, tmp):
    """Ouvre la page sans interface et lit les drapeaux posés par la boîte à outils."""
    r = subprocess.run([nav, "--headless", "--disable-gpu", "--no-first-run", f"--user-data-dir={tmp / ('profil-' + page.stem)}",
                        "--virtual-time-budget=8000", "--dump-dom", page.resolve().as_uri()], capture_output=True, text=True, timeout=180)
    racine = re.search(r"<html[^>]*>", r.stdout)
    attributs = racine.group(0) if racine else ""
    if 'data-cours-pret="1"' not in attributs:
        echecs.append(f"{page.name} : la boîte à outils n'a pas démarré")
    m = re.search(r'data-cours-erreurs="(\d+)"', attributs)
    if m:
        echecs.append(f"{page.name} : {m.group(1)} erreur(s) dans le code des jouets")
    print(f"  jouets de {page.name} : {'erreur' if m or 'data-cours-pret' not in attributs else 'ok'}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pdf", action="store_true", help="produire aussi le PDF de exemple.md")
    o = p.parse_args()
    with tempfile.TemporaryDirectory(prefix="textured-test-", ignore_cleanup_errors=True) as tmp:
        tmp = Path(tmp)
        lancer([str(RACINE / "exemple.md"), "-o", str(tmp / "exemple.html")] + (["--pdf"] if o.pdf else []))
        if o.pdf and not (tmp / "exemple.pdf").is_file():
            echecs.append("exemple.pdf absent")
        lancer([str(RACINE / "exemples" / "cours"), "-o", str(tmp / "cours")])
        motifs_et_glyphes()
        choix_par_sujet()
        sujets()
        favicons(tmp)
        # couverture sur un chapitre (encre et densité héritées de l'accueil) et planche de tous les motifs
        chap = RACINE / "exemples" / "cours" / "01-flory-huggins.md"
        lancer([str(chap), "-o", str(tmp / "couv" / "chapitre.html"), "--couverture", "oui", "--planche"] + (["--pdf"] if o.pdf else []))
        if o.pdf and not (tmp / "couv" / "chapitre.pdf").is_file():
            echecs.append("PDF de la page à couverture absent")
        planche = (tmp / "couv" / "chapitre.couvertures.html").read_text(encoding="utf-8") if (tmp / "couv" / "chapitre.couvertures.html").is_file() else ""
        n_cases = planche.count('class="couv-case"')
        if n_cases < len(motifs.MOTIFS):
            echecs.append(f"planche : {n_cases} couvertures pour {len(motifs.MOTIFS)} motifs")
        if 'class="couverture ' not in (tmp / "couv" / "chapitre.html").read_text(encoding="utf-8"):
            echecs.append("couverture absente de la page")
        if not (tmp / "couv" / "chapitre.couvertures.html").is_file():
            echecs.append("planche des couvertures absente")
        nav = textured.navigateur()
        if nav:
            for page in sorted((tmp / "cours").glob("*.html")):
                if 'class="jouet' in page.read_text(encoding="utf-8"):
                    jouets(page, nav, tmp)
        else:
            print("  (pas de navigateur Chromium : jouets non exécutés)")
            if o.pdf:
                echecs.append("--pdf demandé, mais aucun navigateur trouvé")
    if echecs:
        print("\nÉCHEC :")
        for x in echecs:
            print("  " + x)
        return 1
    print("\nTout est propre.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
