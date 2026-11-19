# Couverture, favicon et titre d'onglet

**Couverture : seulement sur demande** (« avec une couverture »). Favicon et titre d'onglet : posés d'office sur toute
page, à ne changer que sur demande. **Des motifs, pas des illustrations** : champs de points, grilles, faisceaux,
arcs, trames. Le sujet n'en donne que la structure, jamais un objet dessiné, un schéma, un pictogramme ni du texte.

## Poser

Une ligne d'en-tête, chaque mot facultatif : `couverture: motif teinte place nombre`.

```
court: Démixtion
couverture: binodale encre bas
```

- **motif** : choisir par `python3 <skill>/textured.py --motifs "sujet"` (classement en une ligne) ; `oui` le tire de
  l'en-tête. `--planche [domaine]` écrit `nom.couvertures.html`, le document dans chaque motif, pour l'utilisateur.
- **teinte** : `claire` (pastel), `encre` (aplat), `sombre` (nuit teintée).
- **place** : `haut` (titre, illustration cadrée, fiche) · `bas` (illustration puis titre au tiers bas) · `plein`
  (illustration à fond perdu) · `fond` (motif sur toute la couverture, titre en cartouche).
- **nombre** : un autre tirage du même motif (`couverture: reseau 2`). Même titre, même couverture.

Le titre de la couverture est `court:`, sinon `titre:`, en capitales : **un ou deux mots**. `soustitre:` court,
`surtitre:`, `auteur:` et l'année y figurent ; l'encre est celle de la page.

## Catalogue

**Formes** : `semis` points et onde · `arcs` cercles qui se ferment · `anneaux` concentriques · `reseau` radial ·
`automate` cellulaire · `trame` sphère en trame · `rayures` sphère rayée · `helice` hélice de points · `pavage` Truchet
· `flocon` six branches · `trajectoires` particules · `taches` organiques · `pixels` glyphes.

**Le document** : `colonnes` une colonne par section · `plan` organigramme des sections · `lettres` grille de mots.

**Matière, polymères** : `pelote` marche aléatoire · `blobs` chaîne de cercles · `binodale` points qui se séparent ·
`ternaire` trame triangulaire · `phases` trois textures · `spherolites` rayons en croix · `masses` barres en cloche ·
`nodules` disques à cœur · `fibres` tirets orientés.

**Mécanique, rhéologie** : `traction` faisceau depuis un coin · `module` marches en faisceau · `rheologie` courbes à
plat puis en pente.

**Procédés, régulation** : `cascade` cellules en file · `dts` crêtes superposées · `arrhenius` éventail de droites ·
`semenov` courbes en S · `mccabe` escaliers · `amortie` ondes amorties.

**Calcul, plans d'expériences** : `maillage` triangulation · `tangentes` fils tendus · `cube` points en perspective ·
`isoreponses` lignes de niveau · `pareto` colonnes décroissantes.

**Risques** : `braises` triangles chauffés · `eventails` deux éventails convergents · `panache` nuage qui s'élargit ·
`carreaux` carrés croissants.

**Physique, astronomie** : `interference` franges de points · `geodesiques` quadrillage creusé · `ising` domaines de
spins · `galaxie` spirale de points · `cosmique` toile de filaments · `dipole` lignes de champ · `limaille` tirets
alignés · `kepler` ellipses confocales · `lissajous` table de figures · `chladni` sable nodal · `collision` traces en
pointillés · `brillouin` zones alternées · `chirikov` îlots et chaos · `hertzsprung` nuage d'étoiles · `circumpolaire`
arcs autour d'un pôle · `lentille` réseau ouvert en anneau · `paquets` ondes localisées · `abrikosov` réseau de
tourbillons.

**Terre, climat** : `plissement` couches plissées · `sismogramme` traces secouées · `gyres` cellules de courant ·
`isobares` lignes de niveau serrées · `rechauffement` bandes froides puis chaudes · `hachures` relief · `orgues`
prismes · `banquise` plaques sur l'eau · `affluents` réseau ramifié · `rossby` anneaux ondulants · `averse` tirets
obliques · `carottes` colonnes de couches · `dorsale` bandes symétriques · `dunes` crêtes ombrées · `nebulosite` trame
nuageuse · `poreux` grains et chemin · `epicentres` points inégaux.

**Mathématiques** : `isoclines` champ de pentes · `attracteur` nuage chaotique · `modulo` cordes sur un cercle ·
`galton` billes en cloche · `entrelacs` nœud en ruban · `ulam` spirale des premiers · `mandelbrot` ensemble en trame ·
`hilbert` courbe remplissante · `penrose` losanges apériodiques · `apollonius` cercles tangents · `angledor` spirale
de Vogel · `collatz` corail · `quatrecouleurs` carte en quatre tons · `epicycles` cercles en chaîne · `hyperbolique`
disque de Poincaré · `young` cases en escalier · `complexe` module et argument · `spirographe` roulettes ·
`tesseract` hypercube.

**Chimie générale** : `raies` bandes de raies · `electrode` couche contre une paroi · `orbitales` lobes de points ·
`chromato` pistes de pics · `laue` taches de diffraction · `mendeleiev` silhouette périodique · `belousov` ondes en
spirale · `liesegang` anneaux espacés · `maxwell` molécules et vitesses · `solvatation` ions et couronnes · `miroir`
paires symétriques · `nucleation` grains en anneaux · `multiplets` arbres de dédoublement · `agregat` amas branchu ·
`osmose` paroi et mélange · `zeolithe` nid d'abeilles.

Détail (dessins et mots du sujet) : `textured.py --motifs` sans sujet.

## Dessin sur mesure

Quand aucun motif ne dit le sujet : un bloc `::: couverture` (retiré du corps) avec **un seul SVG**, sans ligne vide.
`viewBox="0 0 200 200"` remplace l'illustration ; `viewBox="0 0 200 300"` fait **la couverture entière**, ses textes
reprenant `{TITRE}`, `{titre}`, `{soustitre}`, `{surtitre}`, `{auteur}`, `{annee}`, `{mots}`. Couleurs :
`currentColor`, `var(--ca)` (accent, une ou deux touches), `var(--cd)` (trait doux), `var(--cf)` (fond) ; rien
d'autre. Trouver la structure du sujet (partage, progression, convergence, répétition, amortissement), la traduire en
points, grille, faisceau ou trame, à 8 unités du bord, traits de 1 à 3 unités.

```
::: couverture
<svg viewBox="0 0 200 200">
<path d="M20 20h0M50 20h0M80 20h0M110 20h0M140 20h0M170 20h0M20 50h0M50 50h0M80 50h0M110 50h0" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
<path d="M140 50h0M170 50h0M50 80h0M80 80h0M110 80h0M140 80h0M80 110h0M110 110h0" stroke="currentColor" stroke-width="7" stroke-linecap="round"/>
<path d="M170 80h0M110 140h0M140 140h0M140 170h0" stroke="currentColor" stroke-width="13" stroke-linecap="round"/>
<circle cx="170" cy="170" r="12" fill="var(--ca)"/>
</svg>
:::
```

Couverture entière : même bloc en `viewBox="0 0 200 300"`, avec un fond `<rect width="200" height="300"
fill="var(--cf)"/>`, puis `<text x="16" y="250" font-size="24">{TITRE}</text>` (24 tient une dizaine de capitales ;
`font-weight="400"` allège, `style="font-family: var(--texte)"` passe en romain).

## Favicon et titre d'onglet

Par défaut : la marque géométrique du motif de la couverture, sinon celle du sujet, à l'encre de la page ; un cours
porte le favicon de son accueil. Sur demande :

- `icone: nom` : une marque (`losange`, `anneau`, `anneaux`, `arc`, `onde`, `ondes`, `points`, `grille`, `damier`,
  `barres`, `triangle`, `quarts`, `etoile`, `disques`, `demi`, `escalier`, `eventail`, `sablier`, `hexagone`, `carre`,
  `chevrons`, `spirale`, `tirets`, `croix`, `lune`) ou un nom de motif ; `lettre` (ou `lettre Ω`) ; une adresse ;
  `non`. À la suite, une teinte (`claire|encre|sombre`), une forme (`carre|rond|nu`) ou une encre :
  `icone: anneau sombre rond`. `--icones` montre toutes les marques.
- Bloc `::: icone` : un `<svg viewBox="0 0 32 32">`, deux ou trois formes, mêmes couleurs que la couverture.
- `onglet: texte` remplace le titre d'onglet (par défaut : `court:` ou le titre ; « Chapitre 2 · Titre court — Cours »
  pour un chapitre).
