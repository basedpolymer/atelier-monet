# Couverture

À lire avant de poser une couverture. **Seulement sur demande** (« avec une couverture », « fais-lui une
couverture ») : sans demande, pas de clé `couverture:`.

## Poser la couverture

Une ligne dans l'en-tête de la source : `couverture: motif teinte place nombre`, chaque mot facultatif.

```
court: Démixtion
soustitre: ou pourquoi deux polymères se mélangent si mal
tirage: #ff6c2f
couverture: taches encre
```

- **motif** : un nom du tableau ci-dessous, choisi pour le sujet (c'est ton travail ; `oui` seul le tire des mots du
  titre et de la description, sinon au hasard).
- **teinte** : `claire` (pastel de l'encre, texte noir), `encre` (aplat de l'encre, texte noir ou crème), `sombre`
  (nuit teintée de l'encre, texte crème). Sans teinte, tirée du titre.
- **place** du titre : `haut` (titre, illustration cadrée, fiche) ou `bas` (illustration, filet, ligne en italique
  puis titre au tiers bas).
- **nombre** : un autre tirage aléatoire du même motif (`couverture: reseau 2`).

Même document, même couverture : le hasard a pour graine le titre. `--couverture "motif …"` en ligne de commande vaut
la clé (et la remplace). `--planche` écrit en plus `nom.couvertures.html` : la couverture du document dans les seize
motifs, chacune sous la ligne d'en-tête qui la donne. Utile quand l'utilisateur veut choisir.

Ce que la couverture reprend : `court:` s'il existe, sinon `titre:`, en capitales grasses. **Un ou deux mots, c'est là
qu'elle est la plus belle** : donne un `court:` (il sert aussi à l'en-tête courant). `soustitre:` en italique, court
lui aussi (« vs. Control », « of Transport ») ; `surtitre:` en petites capitales ; `auteur:` et l'année de `date:` au
pied, le nombre de mots à droite ; une fiche (sections, figures, formules, exercices, temps de lecture) quand la place
le permet. L'encre est celle de la page (`tirage:`, ou celle que la page tire de son titre) ; avec `tirage: non`, la
couverture garde une encre à elle.

## Motifs

| Motif | Dessin | Pour |
|---|---|---|
| `semis` | semis de points traversé d'une onde pointillée | signal, mesure, bruit, statistique |
| `arcs` | cercles qui se referment case après case | progression, apprentissage, croissance |
| `anneaux` | anneaux concentriques pleins, pointillés ou ouverts | ondes, diffusion, cycles |
| `reseau` | réseau radial qui s'évase, un chemin à l'accent | graphes, relations, réseaux |
| `automate` | automate cellulaire né d'une case | calcul, algorithmes, émergence |
| `trame` | sphère en trame de points et son orbite | volume, lumière, astronomie, optique |
| `rayures` | sphère de rayures et son ombre | forme, matière, matériaux |
| `helice` | double hélice de points | biologie, ADN, chimie |
| `pavage` | pavage de Truchet en méandres | géométrie, combinatoire, topologie |
| `flocon` | flocon à six branches | symétrie, cristaux, fractales |
| `trajectoires` | trajectoires de particules dans un champ | mouvement, dynamique, flux, conflits |
| `taches` | grille de taches organiques | cellules, vivant, écologie, démixtion |
| `pixels` | planche de glyphes de pixels | numérique, écran, jeu |
| `colonnes` | **le document** : une colonne de texte par section, haute de ses mots ; la plus longue surlignée | rapport, bilan, comparaison |
| `plan` | **le document** : organigramme des sections et sous-sections ; celles à exercices surlignées | cours, méthode, structure |
| `lettres` | **le document** : grille de lettres où un mot du titre croise un mot fréquent du texte | langue, vocabulaire, écriture |

## Dessin personnel

Quand aucun motif ne dit le sujet, dessine l'illustration : un bloc `::: couverture` n'importe où dans le corps
(il en est retiré), contenant un seul SVG carré.

```
::: couverture
<svg viewBox="0 0 200 200"><path d="M100 20V140" stroke="currentColor" stroke-width="1.5"/><circle cx="100" cy="150" r="12" fill="var(--ca)"/></svg>
:::
```

Couleurs : `currentColor` (l'encre du texte), `var(--ca)` (accent, une ou deux touches), `var(--cd)` (trait doux),
`var(--cf)` (le fond, pour évider). Rien d'autre : les couleurs suivent la teinte. Traits de 1 à 3 unités, formes
simples et franches, pas de texte ; le dessin occupe le carré à 5 unités du bord. Un motif nommé dans `couverture:`
est alors ignoré, la teinte et la place restent.

## Où elle apparaît

À l'écran, à droite du titre : dans la colonne libre à côté du plan ou dans la marge sur grand écran, au-dessus du
titre sur un téléphone, avec une tranche de pages dont l'épaisseur suit le nombre de mots. Sur papier (`--pdf`),
c'est la première page, A4 à fond perdu, sans numéro ; le texte reprend à la page 1. Dans `--apercu`, elle se pose à
droite du titre. La couverture garde ses couleurs dans les deux thèmes : c'est un objet posé sur la page.
