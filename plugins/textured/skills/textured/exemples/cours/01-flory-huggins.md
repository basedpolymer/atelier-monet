---
titre: Le modèle de Flory-Huggins
chapitre: 1
priorite: 3 — le point critique tombe à chaque examen
description: Enthalpie libre de mélange de deux polymères, spinodale et point critique, avec un jouet.
---

::: retenir Ce qu'il faut savoir faire à la fin du chapitre
- écrire \(\Delta g_m\) de Flory-Huggins et nommer ses deux termes ;
- calculer le point critique \(\chi_{12}^c\) d'un mélange.
:::

## L'enthalpie libre de mélange {prio=3}

On place les chaînes sur un réseau dont chaque site a le volume \(V_{ref}\). Le terme entropique compte les façons de
ranger les chaînes ; le terme d'interaction compte les contacts entre les deux espèces, pondérés par \(\chi_{12}\).

\[ \frac{\Delta g_m V_{ref}}{RT} = \underbrace{\frac{\phi_1}{m_1}\ln\phi_1 + \frac{\phi_2}{m_2}\ln\phi_2}_{\text{entropique}} + \underbrace{\chi_{12}\,\phi_1\phi_2}_{\text{enthalpique}} \]

::: def Définition — paramètre d'interaction
\(\chi_{12}\) mesure, en unités de \(kT\), l'énergie d'échange d'un contact 1-2.
:::

<div class="jouet" id="jouet-dgm">
<h4>Courbe \(\Delta g_m(\phi_2)\) d'un mélange symétrique</h4>
<div class="commandes">
<label>\(\chi_{12}\) <input type="range" data-k="chi" min="0.010" max="0.030" step="0.0005" value="0.022" data-fmt="4"><output></output></label>
<label>\(m_1 = m_2 = m\) <input type="range" data-k="m" min="1" max="3" step="0.01" value="2" data-log data-fmt="s3"><output></output></label>
</div>
<canvas></canvas>
<div class="legende"><span>\(\Delta g_m V_{ref}/RT\)</span><span class="tirets" style="--c:var(--rouge)">points d'inflexion (spinodale)</span></div>
<p class="lire">la courbe est l'enthalpie libre de mélange ; deux minima séparés par une bosse signifient que le mélange
se sépare en deux phases. Les tirets marquent les points d'inflexion, bornes de la zone instable.</p>
<p class="verdict"></p>
</div>

<script>
Cours.pret(() => {
  const j = document.getElementById("jouet-dgm");
  const p = new Cours.Plot(j.querySelector("canvas"), { x: [0, 1], xlabel: "φ₂", ylabel: "Δg_m V_{ref}/RT", ratio: 0.55 });
  const verdict = j.querySelector(".verdict");
  Cours.sliders(j, s => {
    const g = f => (f / s.m) * Math.log(f) + ((1 - f) / s.m) * Math.log(1 - f) + s.chi * f * (1 - f);
    const d2 = f => 1 / (s.m * f) + 1 / (s.m * (1 - f)) - 2 * s.chi;
    const infl = Cours.num.racines(d2, 1e-4, 0.5).concat(Cours.num.racines(d2, 0.5, 1 - 1e-4));
    const ymin = Math.min(...Cours.num.linspace(0.001, 0.999, 200).map(g));
    p.set({ y: [ymin * 1.15 - 1e-5, -ymin * 0.4 + 1e-5] });
    p.auto(() => { p.clear(); p.fn(g, { dom: [1e-4, 1 - 1e-4] }); infl.forEach(x => p.vline(x, { c: "rouge" })); });
    const chic = 2 / s.m;
    verdict.textContent = s.chi > chic
      ? `χ₁₂ = ${Cours.fmt(s.chi, 4)} dépasse χc = ${Cours.fmt(chic, 4)} : la courbe a deux minima, le mélange se sépare.`
      : `χ₁₂ = ${Cours.fmt(s.chi, 4)} reste sous χc = ${Cours.fmt(chic, 4)} : la courbe est convexe, le mélange est homogène.`;
  });
});
</script>

## Le point critique {prio=3}

La spinodale annule la dérivée seconde de \(\Delta g_m\) ; le point critique annule aussi la dérivée troisième.

::: res Résultat — point critique
\[ \chi_{12}^c = \frac{1}{2}\left(\frac{1}{\sqrt{m_1}}+\frac{1}{\sqrt{m_2}}\right)^2, \qquad \phi_2^c = \frac{\sqrt{m_1}}{\sqrt{m_1}+\sqrt{m_2}} \]
:::

::: demo point critique à partir de \(\Delta g_m\)
On écrit \(\partial^2 \Delta g_m/\partial\phi_2^2 = 0\), puis \(\partial^3 \Delta g_m/\partial\phi_2^3 = 0\) ; la seconde
équation donne \(\phi_2^c\), la première \(\chi_{12}^c\).
:::

::: piege Piège
Deux longues chaînes se séparent pour un \(\chi_{12}\) minuscule : avec \(m_1 = m_2 = 1000\), \(\chi_{12}^c = 0{,}002\).
:::

::: exo Exercice 1 — Point critique d'un mélange symétrique {prio=3}
Calculer \(\chi_{12}^c\) pour \(m_1 = m_2 = 100\).

::: indice
Avec \(m_1 = m_2 = m\), la formule se simplifie beaucoup.
:::

::: corr
\(\chi_{12}^c = \tfrac{1}{2}(2/\sqrt{m})^2 = 2/m\). [Réponse : \(\chi_{12}^c = 0{,}020\).]{.reponse}
:::
:::

<div class="qcm" data-bonne="2">
<p class="q">Pour un polymère de masse infinie dans un solvant (\(m_1 = 1\)), \(\chi_{12}^c\) tend vers :</p>
<ol><li>0</li><li>\(1/2\)</li><li>1</li></ol>
<div class="explication"><p>Avec \(m_2 \to \infty\), \(\chi_{12}^c \to \tfrac{1}{2}\).</p></div>
</div>

## Pour aller plus loin {prio=1 confirmer="hors programme cette année ?"}

::: plus Au-delà du champ moyen
Près du point critique, les fluctuations de composition corrigent les exposants ; pour des chaînes longues, le champ
moyen reste une très bonne approximation, parce que chaque chaîne interagit avec beaucoup d'autres.
:::
