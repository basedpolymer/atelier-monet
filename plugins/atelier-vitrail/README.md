# atelier-vitrail

Thème pour Claude Code, dans l'esprit LaTeX et ASCII : plâtre d'atelier le jour, nuit de vitrail le soir, avec des pelotes de polymère, un réacteur agité, une réponse indicielle et un nœud papillon en caractères, doucement animés.

![L'app de bureau Claude avec le thème, de jour : le fond en caractères derrière la conversation](docs/app-jour.webp)

![La même conversation de nuit](docs/app-nuit.webp)

<details>
<summary>Le fond seul</summary>

![Le fond de jour : plâtre clair, caractères en couleurs de vitrail](docs/jour.png)

![Le fond de nuit : fond sombre, les mêmes motifs plus lumineux](docs/nuit.png)

</details>

Le fond est un seul SVG fait de caractères, animé en CSS par des transformations et des changements d'opacité, que le compositeur prend en charge sans les redessiner. Ces caractères sont des formes, pas du texte : chaque lettre est le contour d'un caractère de Latin Modern Mono (`glyphes.py` les écrit dans `hooks/scene.ts`), si bien que rien ne se sélectionne, ne se copie ni ne se lit à voix haute. Il s'immobilise si le système demande moins d'animations ; en portrait, seules les pelotes et le réacteur restent.

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
