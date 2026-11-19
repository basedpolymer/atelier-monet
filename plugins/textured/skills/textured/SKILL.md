---
name: textured
description: Produit un document, un rapport, une note ou un cours complet en HTML avec le gabarit TeXtured (style LaTeX : Latin Modern, titres sans-serif, filets à losanges, tableaux booktabs, encadrés, formules KaTeX, jouets interactifs, thème clair et sombre, PDF A4). Utiliser quand l'utilisateur demande « avec mon template TeXtured », « en TeXtured », « /textured », ou un rapport ou un cours HTML dans ce style.
---

# TeXtured HTML

Tu écris une **source courte** (Markdown) ; `textured.py` en fait une page HTML complète et autonome. N'écris jamais
le `<head>`, les styles ni les scripts. Ne lis ni `assets/` ni la page produite : le bilan dit tout. Fichiers à lire
seulement quand la demande les appelle : `cours.md` (cours complet, priorités), `exercices.md` (exercices, QCM),
`jouets.md` (figure interactive), `couverture.md` (couverture), `exemple.md` (en cas de doute).

## Marche à suivre

1. Écrire `nom.md` à côté de l'endroit où la page doit vivre (on modifie la source pour mettre à jour).
2. `python3 <skill>/textured.py nom.md --ouvrir` → `nom.html` ; `<skill>` est le dossier de ce fichier (sous Windows :
   `python`, `python3` n'y étant qu'un raccourci vers le Microsoft Store).
3. Lire la ligne de bilan ; corriger la source et relancer tant qu'il reste une ligne `erreur :` ou `avis :`.

## En-tête de la source

```
---
titre: Titre du document
soustitre: Une phrase (facultatif)
surtitre: Rubrique en petites capitales (facultatif)
auteur: Prénom Nom
date: 2026-11-15
description: Une phrase pour les moteurs et les aperçus de lien.
tirage: #00a95c
---
```

**Encre (`tirage:`)** : à choisir à chaque page d'après le sujet, une encre de risographie franche (`#0078bf` bleu,
`#00a95c` vert, `#ff48b0` rose, `#ff6c2f` orange, `#00838a` sarcelle, `#765ba7` violet, `#f15060` rouge, `#bb8b41` or…).
La page en tire ses pastels (lettrine, numéros, surlignages, losanges, jouets). Sans elle, une encre tirée du titre ;
`tirage: non` : page grise.

Facultatif : `lang: en` · `plan: non` (sommaire affiché par défaut dès deux titres) · `numeros: non` ·
`densite: compacte` · `lettrine: 3|non` · `court:` (titre courant et onglet) · `pied:` · `prive: oui` (noindex) ·
`avertissement: **Gras.** Texte` (bandeau en haut jusqu'à « J'ai compris ») · `langues: fr=URL, en=URL` ·
`url:`, `image:` (page publiée) · `csp: non`.

**Favicon et titre d'onglet** : posés d'office (marque géométrique à l'encre de la page) ; ne les changer que sur
demande (`icone:`, `onglet:`, voir la fin de `couverture.md`). **Couverture** : seulement sur demande ; choisir le
motif par `python3 <skill>/textured.py --motifs "sujet"`, puis `couverture: motif` dans l'en-tête (`couverture.md`).

## Écrire le corps

Markdown pandoc. Sections `##`, sous-sections `###`, numérotées par le script (`{-}` : sans numéro ; `{#id}` :
identifiant). Pas de `#` : le titre vient de l'en-tête.

| Besoin | Source |
|---|---|
| Formule | `\(…\)`, `\[…\]` (KaTeX : pas de `\ce` ; `\text{kJ}\cdot\text{mol}^{-1}`) |
| Renvoi | `[](#id)` → « § 2.1 », « figure 3 », « tableau 1 » (jamais de numéro tapé) |
| Source citée | `[Thermo 2026, p. 12]{.src}` ; apport extérieur : `[texte]{.hs}` |
| Note | `texte[^1]` puis `[^1]: La note.` |
| Tableau | tableau Markdown, puis `: Légende. {#tab-id}` |
| Image | `![Légende](fichier.png){#fig-id}` seule dans son paragraphe (embarquée) |
| Schéma | `<figure id="fig-id"><svg viewBox="…" role="img" aria-label="…">…</svg><figcaption>Légende.</figcaption></figure>` |
| Bloc large | `::: large` … `:::` (grande figure, grand tableau) |
| Bouton | `[Texte](url){.bouton}` (`.bouton .second`) ; `---` : filet à losange |

Blocs : `::: classe Titre facultatif {attributs}`, contenu, `:::` seul sur sa ligne ; ils s'emboîtent. `chapeau` ·
`def`, `res` (boîtes) · `retenir`, `piege` (filet gauche) · `remarque`, `exemple`, `methode` (terminés par ⌟) ·
`demo`, `plus` (repliables) · `cartes` > `carte` · `figures` (côte à côte).

SVG : `stroke="currentColor"`, puis `var(--tirage)`, `--accent`, `--bleu`, `--rouge`, `--vert`, `--orange`, `--violet`,
`--cyan`, `--gris`, `--doux`, `--trait`, `--papier` (ils suivent le thème) ; jamais de couleur en dur ; `<text>` prend
seul police et couleur.

## Règles de fond

- Prose rédigée, une idée par paragraphe ; encadrés rares. Toute figure a une légende et un texte de remplacement.
- **Exercices, QCM, questions numériques : seulement sur demande** (alors lire `exercices.md`). Sans demande, la
  page explique, démontre et illustre.
- **Rien n'est publié sans demande** (« à partager », « mets-le en ligne ») : si `publier.md` existe dans ce dossier,
  le suivre ; sinon `url:` dans l'en-tête et `--apercu`.

## Options

`--pdf` : `nom.pdf` A4 (Chrome sans interface, ou Edge ; `TEXTURED_NAVIGATEUR=chemin`) ; en regarder une page avant de
le donner (`pdftoppm -r 40 -png -f 1 -l 1 nom.pdf p`). `--apercu` : image de partage 1200 × 630 (`og:image` si `url:`).
`--polices locales` : 100 Ko de moins si Latin Modern est installée. `--assets /chemin` : page légère qui lie l'export
du gabarit (`--exporter DOSSIER`). Source `nom.tx.html` : même en-tête, mêmes classes, en HTML. Un dossier : tout un
cours (`cours.md`). Modifier le gabarit lui-même : `README.md`.
