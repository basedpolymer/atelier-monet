# atelier-vitrail

Thème pour Claude Code, dans l'esprit LaTeX et ASCII, aux couleurs de [Catppuccin](https://catppuccin.com) : Latte le jour, Frappé la nuit. Le fond est fait de caractères doucement animés : des pelotes de polymère, une réaction en formule topologique et des schémas de génie chimique. Chaque session a le sien.

![L'app de bureau Claude avec le thème, de jour : une fiche de chimie et sa courbe de pH, le fond en caractères autour](docs/app-jour.webp)

![La même conversation de nuit](docs/app-nuit.webp)

<details>
<summary>Le fond seul</summary>

![Un fond de jour, en Latte](docs/jour.png)

![Un autre tirage, de nuit, en Frappé](docs/nuit.png)

</details>

## Un fond par session

L'heure de début de la session sert de graine. Elle tire :

- la conformation des trois pelotes, toujours présentes, et les rythmes de leurs replis ;
- une réaction, toujours présente elle aussi, parmi quatre ;
- un à trois motifs parmi huit, leur place à l'écran et leurs paramètres.

Deux sessions n'ont donc ni les mêmes dessins ni les mêmes mouvements. Le thème change de couleurs avec le système : Latte le jour, Frappé la nuit.

## Ce qui bouge

Toujours là :

- **Les pelotes de polymère.** Trois chaînes de monomères (`o-o-o`). Chaque moitié de chaîne est faite de quatre segments emboîtés qui pivotent autour de leurs jointures : de quelques degrés et lentement près du centre (une oscillation en 23 à 31 s), plus largement et plus vite vers le bout libre (6 à 8 s). Les périodes ne se recoupent pas, la pelote ne repasse pas par la même pose. Chaque chaîne balance aussi d'un bloc et s'éclaircit puis s'assombrit, comme si elle respirait. Autour, un cercle de croix et de points marque le rayon de la pelote et fait un tour en douze minutes.
- **La réaction**, en formule topologique : les liaisons sont des traits, un sommet sans lettre est un carbone. Elle se joue en boucle de 22 s : les réactifs, la liaison qui se rompt, les fragments qui se déplacent, les liaisons qui se forment (en doré), les produits, puis tout s'efface et recommence.
  - Estérification : l'alcool prend la place de OH, qui part en eau.
  - Diels-Alder : un diène et un alcène ferment un cycle à six, trois doubles liaisons en donnent une.
  - Ouverture de l'oxyde d'éthylène par un alcoolate : le cycle s'ouvre, la charge passe au bout de la chaîne.
  - Addition d'un radical sur le styrène : le radical passe au carbone qui porte le cycle.

Tirés au sort, un à trois par session :

- **Réacteur agité.** La surface du liquide ondule. La pale et les bulles dépendent du travail de Claude (voir plus bas).
- **Réponse indicielle** d'une boucle de régulation. La courbe se trace point par point pendant que Claude travaille. Son amortissement est tiré : tantôt elle oscille, tantôt elle rejoint la consigne presque sans la dépasser.
- **Décomposition spinodale**, vue au microscope : sept instants d'une simulation de Cahn-Hilliard (`spinodale.py`) se fondent l'un dans l'autre. Le mélange homogène se module, se sépare en deux phases entrelacées, puis les domaines grossissent de plus en plus lentement, avant le retour au mélange homogène. Un cycle dure une minute.
- **Diagramme de Semenov.** La droite d'évacuation de la chaleur glisse vers l'exponentielle d'Arrhenius ; les points stable et instable se rapprochent et se rejoignent à la tangence ; puis la température s'emballe le long de la courbe, avec une traînée, et sort du cadre en gerbe. La pente de la droite est tirée.
- **Distillation de McCabe et Thiele**, à reflux total. Les étages théoriques se tracent un à un, du distillat au résidu, puis s'effacent. Leur nombre dépend de la volatilité relative tirée, et s'affiche (« N min »).
- **Distribution des temps de séjour** d'une cascade de réacteurs. Quatre courbes apparaissent l'une après l'autre, d'un seul réacteur à une quinzaine : la distribution se resserre vers l'écoulement piston.
- **Plan d'expériences 2³.** Les huit essais sont les sommets d'un cube ; ils s'allument un à un, numérotés, dans un ordre tiré au sort.
- **Boucle de synthèse de l'ammoniac.** Trois bulles de gaz font le trajet : réacteur, séparateur, recyclage, second passage, sortie.

## Ce qui réagit à la session

Le fond ne répond ni au clic ni à la souris. Il suit la conversation :

- **Pendant un tour de Claude**, la pale du réacteur tourne et des bulles montent ; la réponse indicielle se trace depuis le début, puis recommence. Entre deux tours, la pale s'arrête, les bulles disparaissent et la courbe reste posée, entière. Chaque session a au moins l'un de ces deux motifs. Les tours des sous-agents ne comptent pas.
- **Au fil des tours**, les pelotes s'allongent par les deux bouts, et leur cercle grandit avec elles (R ~ a.N^(3/5)). Elles sont à moitié là au premier tour et complètes vers le quinzième.
- **Une compaction de la conversation** coupe les chaînes en deux.
- **La ligne d'attente** remplace « Working » par un geste d'atelier ou de laboratoire, selon ce que fait Claude : « Annealing » ou « Nucleating » quand il réfléchit, « Purging with nitrogen » quand il envoie sa requête, « Stirring the reactor » ou « Sampling the batch » pendant un outil, « Extruding » ou « Casting the film » quand il écrit. Le mot change à chaque tour.

Le fond n'est redessiné qu'au début et à la fin d'un tour ; les mouvements continus reprennent où ils en étaient. L'app montre d'abord le nouveau dessin en image fixe quelques secondes, puis il s'anime.

## Comment il est fait

Le fond est un seul SVG, animé en CSS par des transformations et des changements d'opacité. Ses caractères sont des formes, pas du texte : chaque lettre est le contour d'un caractère de Latin Modern Mono (`glyphes.py` les écrit dans `hooks/scene.ts`), et les plus nombreux (`-`, `.`, `o`, `+`) sont tracés au trait. Rien ne se sélectionne, ne se copie ni ne se lit à voix haute. Il s'immobilise si le système demande moins d'animations ; sur téléphone, seuls restent les pelotes et un motif.

L'app de bureau surveille le fond et l'immobilise s'il lui coûte trop à redessiner (plus de 5,56 ms par image), s'il clignote ou s'il dépasse 131 072 caractères. Celui-ci coûte de 2 à 4 ms selon le tirage et ne dépasse pas 97 000 caractères. Sur une machine au calme, il tourne sans s'arrêter (plus de sept minutes mesurées, 0,4 ms par image dans l'app). Si la machine sature et que l'affichage saccade, l'app peut l'immobiliser ; le début ou la fin du tour suivant le relance.

## Installation

Dans une session de terminal :

```
/plugin install atelier-vitrail --marketplace basedpolymer/atelier-monet
```

Claude Code demande d'ajouter le marketplace (répondre `y`), puis la portée : choisir « user » pour que le thème s'applique à toutes les sessions.

Depuis un shell :

```
claude plugin install atelier-vitrail --marketplace basedpolymer/atelier-monet
```

Dans l'app de bureau, où `/plugin` ne s'exécute pas : cliquer sur + à côté de la zone de saisie, puis Plugins, Add marketplace avec `basedpolymer/atelier-monet`, puis Add plugin.

## Essai depuis un dossier local

```
claude --plugin-dir /chemin/vers/atelier-vitrail
```

Ou, pour toutes les sessions, dans `~/.claude/settings.json` :

```json
"env": { "CLAUDE_CODE_PLUGIN_DIRS": "~/.claude/mods/atelier-vitrail" }
```
