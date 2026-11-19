# textured (plugin)

Le skill TeXtured en plugin Claude Code : une source Markdown courte devient une page HTML autonome au style LaTeX, ou
un cours complet (chapitres reliés, jouets interactifs, priorités de révision), avec PDF A4,
image de partage et couverture sur demande. Il demande Python 3.10+, pandoc et node ; Chrome ou Edge pour le PDF.

Installation, dans une session Claude Code :

```
/plugin marketplace add basedpolymer/atelier-monet
/plugin install textured@atelier-monet
```

Le skill et sa documentation sont dans [`skills/textured`](skills/textured) (README, SKILL.md, exemples). Une fois le
plugin installé, demander à Claude « un rapport en TeXtured sur … » ou taper `/textured:textured`.
