---
titre: Réguler la température du réacteur
chapitre: 2
priorite: 2 — le réglage d'un PI se demande en TP plus qu'à l'écrit
description: Boucle de régulation PI d'un réacteur de polymérisation, avec un jouet de simulation.
---

## La boucle fermée {prio=3}

Le réacteur est un procédé du premier ordre avec retard : gain \(G\), constante de temps \(\theta\), retard pur
\(\tau\). Le régulateur PI calcule la commande à partir de l'écart entre consigne et mesure :

\[ u(t) = K_p\, e(t) + K_i \int_0^t e(s)\,\mathrm{d}s, \qquad e = SP - PV \]

<figure id="fig-boucle">
<svg viewBox="0 0 640 150" role="img" aria-label="Boucle fermée : la consigne SP et la mesure PV donnent l'écart e ; le régulateur PI en tire la commande u, qui agit sur le réacteur ; un capteur mesure la température et la renvoie au comparateur.">
<circle cx="70" cy="60" r="14" fill="none" stroke="currentColor"/>
<text x="70" y="65" text-anchor="middle" font-size="13">±</text>
<text x="8" y="52" font-size="13">SP</text>
<path d="M30 60h24m-6-5 6 5-6 5" fill="none" stroke="currentColor"/>
<path d="M84 60h56m-6-5 6 5-6 5" fill="none" stroke="currentColor"/>
<text x="110" y="52" text-anchor="middle" font-size="13">e</text>
<rect x="142" y="38" width="130" height="44" rx="4" fill="none" stroke="var(--tirage)" stroke-width="1.5"/>
<text x="207" y="65" text-anchor="middle" font-size="13">régulateur PI</text>
<path d="M272 60h76m-6-5 6 5-6 5" fill="none" stroke="currentColor"/>
<text x="310" y="52" text-anchor="middle" font-size="13">u</text>
<rect x="350" y="38" width="150" height="44" rx="4" fill="none" stroke="currentColor"/>
<text x="425" y="58" text-anchor="middle" font-size="13">réacteur</text>
<text x="425" y="73" text-anchor="middle" font-size="11" style="fill: var(--doux)">G e^(−τs)/(θs + 1)</text>
<path d="M500 60h90m-6-5 6 5-6 5" fill="none" stroke="currentColor"/>
<text x="600" y="64" font-size="13">PV</text>
<path d="M560 60v60H70V74" fill="none" stroke="currentColor" stroke-dasharray="4 3"/>
<rect x="275" y="105" width="110" height="30" rx="4" fill="var(--papier)" stroke="currentColor"/>
<text x="330" y="125" text-anchor="middle" font-size="13">capteur</text>
<text x="58" y="96" text-anchor="end" font-size="13">−</text>
</svg>
<figcaption>La boucle fermée : le régulateur agit sur l'écart entre consigne et mesure.</figcaption>
</figure>

La boucle est schématisée par la [](#fig-boucle).

<div class="jouet" id="jouet-pi">
<h4>Échelon de consigne de 20 à 60 °C</h4>
<div class="commandes">
<label>\(K_p\) <input type="range" data-k="kp" min="0.05" max="1" step="0.01" value="0.5" data-fmt="2"><output></output></label>
<label>\(K_i\) <input type="range" data-k="ki" min="0" max="0.15" step="0.002" value="0.06" data-fmt="3" data-unite="s⁻¹"><output></output></label>
<label>retard \(\tau\) <input type="range" data-k="tau" min="0" max="6" step="0.5" value="2" data-fmt="1" data-unite="s"><output></output></label>
</div>
<canvas></canvas>
<div class="legende"><span>température mesurée (PV)</span><span class="tirets" style="--c:var(--doux)">consigne (SP)</span></div>
<p class="lire">procédé \(G = 5\), \(\theta = 10\ \text{s}\), simulé pas à pas. Un \(K_p\) fort accélère la montée mais
fait dépasser la consigne ; le retard rend la boucle plus nerveuse, jusqu'à l'instabilité.</p>
<p class="verdict"></p>
</div>

<script>
Cours.pret(() => {
  const j = document.getElementById("jouet-pi");
  const p = new Cours.Plot(j.querySelector("canvas"), { x: [0, 120], y: [15, 80], xlabel: "t (s)", ylabel: "T (°C)", ratio: 0.5 });
  const verdict = j.querySelector(".verdict");
  Cours.sliders(j, s => {
    const r = Cours.boucle({ G: 5, theta: 10, tau: s.tau, Kp: s.kp, Ki: s.ki, h: 0.1, tFin: 120, base: 20, spAvant: 20, spApres: 60, tSaut: 5 });
    const c = Cours.criteres(r, { bande: 0.05 });
    const haut = Math.max(80, Math.min(160, Math.max(...r.pv) * 1.08));
    p.set({ y: [15, haut] });
    p.auto(() => { p.clear(); p.line(r.t, r.sp, { c: "doux", w: 1.2, dash: [5, 4] }); p.line(r.t, r.pv); });
    const instable = Math.max(...r.pv) > 150 || c.tEtab == null || c.tEtab > 110;
    verdict.textContent = instable
      ? "La température oscille sans se stabiliser dans la fenêtre : réduire Kp ou Ki."
      : `Dépassement de ${Cours.fmt(100 * c.depassementRel, 0)} % ; température établie à ± 5 % en ${Cours.fmt(c.tEtab - 5, 0)} s après l'échelon.`;
  });
});
</script>

## Régler sans dépasser {prio=2}

::: methode Méthode
Partir d'un \(K_p\) prudent, monter \(K_i\) jusqu'à annuler l'écart statique sans oscillation, puis ajuster \(K_p\).
:::

::: demo erreur statique nulle avec un intégrateur
En régime établi, \(u\) est constante ; si \(e\) ne s'annulait pas, l'intégrale croîtrait sans fin, et \(u\) avec elle.
:::
