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
- **teinte** : `claire` (pastel), `encre` (aplat), `sombre` (nuit teintée). En `claire` et `sombre`, l'accent prend
  la teinte opposée à l'encre, un motif en traits passe en dégradé de l'encre à cette teinte, un motif en formes
  pleines alterne quatre encres ; `mono` garde une seule encre. `encre` reste d'une couleur.
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

**Polymères, chaînes** : `gel` liens qui percolent · `copolymeres` perles de deux sortes · `peignes` chaînes latérales ·
`coupures` chaînes coupées.

**Polymères, mise en œuvre** : `extrudats` rubans rugueux · `striction` fils amincis · `agregats` amas ramifiés ·
`fibrilles` fentes tendues de fils.

**Réaction, transferts** : `selectivite` traits en trois parts · `thiele` grains qui pâlissent au cœur · `barbotage`
colonnes de cercles · `poiseuille` paraboles de points.

**Optimisation, digitalisation** : `simplexe` triangles qui basculent · `compromis` front en escalier · `boole` damier
cerclé · `mli` impulsions en vagues · `jumeau` relief en miroir · `ecarts` carrés des écarts.

**Prévention** : `tranches` tranches percées · `zonage` enveloppes emboîtées.

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
