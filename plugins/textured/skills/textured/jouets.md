# Jouets interactifs : la boîte à outils `Cours`

À lire avant d'écrire un jouet (figure interactive). La boîte à outils vient du moteur des cours complets ; `textured.py`
ne l'embarque que dans une page dont un script appelle `Cours.`.

## Squelette

```html
<div class="jouet" id="jouet-dgm">
<h4>Titre du jouet, formules permises : \(\Delta g_m(\phi_2)\)</h4>
<div class="commandes">
<label>\(\chi_{12}\) <input type="range" data-k="chi" min="0.010" max="0.030" step="0.0005" value="0.022" data-fmt="4"><output></output></label>
<label>\(m\) <input type="range" data-k="m" min="1" max="3" step="0.01" value="2" data-log data-fmt="s3"><output></output></label>
<label>Modèle <select data-k="mod"><option value="a">premier</option><option value="b">second</option></select></label>
<label><input type="checkbox" data-k="grille" checked> grille</label>
</div>
<canvas></canvas>
<div class="legende"><span>courbe à l'encre de la page</span><span class="tirets" style="--c:var(--rouge)">tirets rouges</span></div>
<p class="lire">ce que montre la figure, en une ou deux phrases (« Comment lire. » est ajouté).</p>
<p class="verdict"></p>
</div>

<script>
Cours.pret(() => {
  const j = document.getElementById("jouet-dgm");
  const p = new Cours.Plot(j.querySelector("canvas"), { x: [0, 1], y: [-0.004, 0.004], xlabel: "φ₂", ylabel: "Δg_m V_{ref}/RT", ratio: 0.55 });
  const verdict = j.querySelector(".verdict");
  Cours.sliders(j, s => {                       // s.chi, s.m (10^valeur : data-log), s.mod, s.grille
    const g = f => (f / s.m) * Math.log(f) + ((1 - f) / s.m) * Math.log(1 - f) + s.chi * f * (1 - f);
    p.auto(() => { p.clear(); p.fn(g, { dom: [1e-4, 1 - 1e-4] }); p.vline(0.5, { c: "rouge" }); });
    verdict.textContent = `χ₁₂ = ${Cours.fmt(s.chi, 4)}`;
  });
});
</script>
```

Règles :

- Le bloc `<div class="jouet">` est écrit en HTML, tel quel dans la source Markdown : `textured.py` le passe à pandoc
  sans le transformer. Les formules `\(…\)` du titre, des libellés et de « Comment lire » sont rendues à la construction.
- Tout le code d'un jouet va dans `Cours.pret(() => { … })` : il s'exécute une fois la page prête et les polices des
  canevas chargées. Pas d'attribut `onclick` (la politique de sécurité les bloque) : `addEventListener`.
- Le bouton « ↺ Réinitialiser » est ajouté tout seul ; il remet les commandes à leur valeur de départ. Un jouet qui
  garde un état à lui (point cliqué, graine) le remet à zéro en écoutant `j.addEventListener("cours:reinit", …)`.
- Deux graphes côte à côte : `<div class="deux-graphes"><figure><canvas></canvas><figcaption>…</figcaption></figure>…</div>`.
  Des boutons dans les commandes : `<div class="ligne-boutons"><button type="button">Nouveau tirage</button></div>`.
- Jouet plus large que la colonne : `<div class="jouet large">`.
- Le titre s'écrit `<h4>` : `textured.py` lui donne le niveau de sa place (h3 sous une section `##`), et décale
  d'autant les titres écrits dans le jouet. Un libellé fait d'une formule (`\(k\)`) donne aussi son nom au curseur
  (`aria-label`, posé à la construction) ; un titre créé par le script du jouet prend le niveau du titre plus un.
- Couleurs : noms `bleu`, `rouge`, `vert`, `orange`, `violet`, `gris`, `cyan`, `encre`, `doux`, `trait`, `grille`,
  `papier`, `fond`, `accent`, et l'encre de la page `tirage`, `pastel`, `pastel-encre`, `pastel-fond`. Une courbe, un
  marqueur ou une entrée de légende sans couleur prend `tirage`. Tout suit le thème clair ou sombre (redessin
  automatique par `p.auto`), et le papier est toujours clair.

## Curseurs : `Cours.sliders(racine, cb)`

Lit tous les `[data-k]` de `racine` et appelle `cb(etat)` au départ puis à chaque changement (une fois par image).
`<input type="range">` : `data-log` (le curseur porte log₁₀ de la grandeur), `data-fmt` (`"3"` : trois décimales,
`"s3"` : trois chiffres significatifs, `"e2"` : écriture scientifique), `data-unite` (affichée après la valeur dans
l'`<output>` du même `<label>`). `<select data-k>` donne la valeur de l'option (nombre si c'en est un), une case à
cocher `data-k` un booléen. Rend `{ etat, maj, lire }` (`maj()` force un recalcul).

## Graphe : `new Cours.Plot(canvas, o)`

Options `o` : `x`, `y` (bornes ; de max à min pour un axe inversé), `xlog`, `ylog`, `xlabel`, `ylabel`, `ratio`
(hauteur/largeur, 0,6), `marge: { g, d, h, b }` (px), `grille` (true), `zero` (ligne y = 0, true), `xpas` / `ypas`
(pas imposé), `xticks: [v…]` ou `[[v, "texte"]…]`, `xfmt: v => "texte"`, `xlogEtiq: [2, 5]`, `xfin` / `yfin` ou
`xsous` / `ysous` (quadrillage fin), second axe `y2: [min, max]` avec `y2log`, `y2label`, `y2pas`… (une série s'y trace
avec `st.y2 = true`), `etroit` (560 px) et `ratioEtroit`.

Méthodes (toutes rendent le graphe, donc s'enchaînent) ; `st` = `{ c, w, dash, alpha, y2 }` :

| Méthode | Trace |
|---|---|
| `p.clear()` | fond, grille, graduations, titres d'axes : à appeler en tête de chaque dessin |
| `p.fn(f, { dom: [a, b], …st }, n = 400)` | la fonction f |
| `p.line(xs, ys, st)`, `p.trace([[x, y]…], st)` | une ligne brisée (valeurs non finies : levée du crayon) |
| `p.lisse([[x, y]…], st)` | courbe lisse passant par des points relevés |
| `p.points(xs, ys, { r, vide, forme })`, `p.serie([[x, y]…], { forme, r, vide })` | marqueurs : `rond`, `carre`, `triangle`, `triangle-bas`, `losange`, `croix`, `plus`, `rond-point`, `cercle` |
| `p.seg(x1, y1, x2, y2, st)`, `p.hline(y, st)`, `p.vline(x, st)` | segment, horizontale et verticale (tirets par défaut) |
| `p.fleche(x1, y1, x2, y2, { double, pointe })` | flèche |
| `p.band(xs, ys1, ys2, st)`, `p.rect(xa, ya, xb, yb, st)` | zone entre deux courbes (ys2 peut être un nombre), rectangle |
| `p.text(x, y, "η_{sp}", { align, base, taille, gras, dx, dy, rot })` | texte en coordonnées de données |
| `p.legend([{ t, c, dash, point, forme, ligne }], "hd" \| "hg" \| "bd" \| "bg" \| "dessus" \| [x, y])` | légende dans le cadre |
| `p.set(o)` | change des options (bornes recalculées…) |
| `p.auto(() => { … })` | dessine et redessine au changement de largeur ou de thème |
| `p.pointeur(e => …)` | souris et doigt : `e.x`, `e.y`, `e.type` (`down`, `move`, `up`), `e.bas` |
| `p.donnees(px, py)`, `p.X(x)`, `p.Y(y)` | conversions pixel ↔ données |

Texte des canevas (titres d'axes, `text`, légendes) : mini-format `η_{sp}`, `R_G^2`, `M^(−1/2)` ; les lettres grecques
passent en italique mathématique, les indices et exposants Unicode (`φ₂`, `10⁻³`) aussi.

Au pixel, sur un contexte 2D : `Cours.ecrire(g, x, y, texte, o)`, `Cours.mesurer(g, texte, o)`,
`Cours.marque(g, X, Y, forme, st)`, `Cours.trait(g, [[X, Y]…], { ferme, remplir })`,
`Cours.triangle(g, bx, by, bw, bh, { noms, grad, pas, pct })` (diagramme ternaire ; rend `P(w_haut, w_gauche, w_droite)`),
`Cours.planche(canvas, n, (g, k, x, y, w, h) => …, { min, max, h })` (n panneaux sur un canevas).

## Calcul et texte

- `Cours.num` : `linspace(a, b, n)`, `logspace(a, b, n)`, `bisect(f, a, b)`, `racines(f, a, b, n)`, `golden(f, a, b)`
  (minimum), `deriv(f, x)`, `linreg(xs, ys)` → `{ a, b, r2 }`, `rng(graine)` (tirage reproductible), `gauss(rand)`.
- `Cours.fmt(x, d)` (virgule décimale, signe moins, espace des milliers), `Cours.fmtS(x, d)` (d chiffres significatifs),
  `Cours.fmtE(x, d)` (écriture scientifique `1,23·10⁻⁴`). Sur une page `lang: en`, point décimal.
- `Cours.couleur("bleu")` : la couleur résolue dans le thème courant.
- `Cours.store.get / set / del(clé)` : stockage local propre au cours (ou à la page).
- Formules à l'exécution : `Cours.tex(el, "\\frac{a}{b}")`, `Cours.ecrireTexte(el, "texte §\\chi_{12}§ texte")` (morceaux
  entre § en KaTeX), `Cours.renderMath(el)`. Elles font embarquer KaTeX dans la page (≈ 280 Ko) : à réserver aux
  verdicts qui en ont vraiment besoin ; sinon, caractères Unicode (`χ₁₂`).

## Simulation d'une boucle de régulation : `Cours.boucle(o)`

Procédé `G·e^(−tau·s)/(theta·s + 1)` (ou `den: [a2, a1, a0]` pour un second ordre) en boucle ouverte ou fermée par un
PID parallèle `u = Kp·e + Ki·∫e + Kd·de/dt`, ou par un tout ou rien. Options (défaut) : `G` (5), `theta` (10), `tau` (2),
`h` (0,1), `tFin` (60), consigne `sp` (nombre ou fonction de t ; sinon échelon de `spAvant` 0 à `spApres` 1 à `tSaut`
1 s), `base` (valeur de PV au repos), `Kp` (1), `Ki` (0), `Kd` (0), `ferme` (true), `derivee` (`"erreur"` ou
`"mesure"`), `umin`, `umax`, `antiWindup`, `Te` (échantillonnage), `perturbation` (t → d), `bruit`, `graine`,
`toutOuRien: { haut, bas, hyst }`. Rend `{ t, sp, pv, mes, e, u }`. `Cours.criteres(r, { bande: 0.05 })` → valeur finale,
erreur statique, dépassement (`depassementRel`), temps de montée 10-90 %, temps d'établissement (`tEtab`).

## Vérifier

Après la construction, ouvrir la page et toucher chaque commande, en clair et en sombre. Une erreur dans le code d'un
jouet est écrite dans la console et comptée sur `<html data-cours-erreurs>` ; `tests/verifier.py` la cherche.
