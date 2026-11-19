---
titre: Gabarit TeXtured HTML
soustitre: Tous les composants, dans l'ordre où un document les rencontre
surtitre: Exemple de référence
auteur: basedpolymer
date: 2026-11-15
description: Page d'exemple du gabarit TeXtured HTML, avec chaque composant et la source qui le produit.
tirage: #0078bf
---

::: chapeau
Ce paragraphe est un chapeau : il annonce le document en deux phrases. Il se place avant le premier titre.
:::

## Texte courant

Le texte est en Latin Modern, justifié et coupé. L'*emphase* est en romain penché, le **gras** reste rare. Un lien externe est encadré de corail ([TeXtured](https://github.com/jdujava/TeXtured)), un renvoi interne de gris : voir [](#encadres), la [](#fig-schema) et le [](#tab-regimes). Une source se cite ainsi [Thermo 2026, p. 12]{.src}, un apport extérieur ainsi : [la constante de Boltzmann vaut \(1{,}381\cdot 10^{-23}\ \text{J/K}\)]{.hs}. Une note de bas de page[^1] et du `code en ligne` complètent le tout.

[^1]: Le texte de la note.

1. Premier point d'une énumération ;
2. second point, avec deux sous-points :
   a. le premier ;
   b. le second.

- Une puce ;
- une autre.

### Formules

Une formule en ligne, \(\chi_{12}^c = 2/m\), et une formule en bloc :

\[\frac{\Delta g_m V_{ref}}{RT} = \underbrace{\frac{\phi_1}{m_1}\ln\phi_1 + \frac{\phi_2}{m_2}\ln\phi_2}_{\text{entropique}} + \underbrace{\chi_{12}\,\phi_1\phi_2}_{\text{enthalpique}}\]

### Code

```python
def spinodale(phi, m):
    return 1 / (m * phi) + 1 / (m * (1 - phi))
```

## Encadrés {#encadres}

::: def Définition — paramètre d'interaction
Le paramètre \(\chi_{12}\) mesure, en unités de \(kT\), l'énergie d'échange d'un contact 1-2.
:::

::: res Résultat — point critique
\[\chi_{12}^c = \frac{1}{2}\left(\frac{1}{\sqrt{m_1}}+\frac{1}{\sqrt{m_2}}\right)^2\]
:::

::: retenir À retenir
Deux minima de \(\Delta g_m\) signifient que le mélange se sépare.
:::

::: piege Piège
La tangente commune n'est horizontale que si \(m_1 = m_2\).
:::

::: remarque Remarque
Une remarque, sans cadre.
:::

::: methode Méthode
Une méthode, sans cadre.
:::

::: exemple Exemple
Un exemple chiffré, sans cadre.
:::

::: demo point critique à partir de \(\Delta g_m\)
On écrit la condition de spinodale, puis on annule la dérivée troisième.

::: cqfd
CQFD
:::
:::

::: plus
Un complément replié.
:::

## Tableaux et figures

| Régime | Loi | Exposant |
|---|---|--:|
| solvant \(\Theta\) | \(R \sim N^{1/2}\) | 0,50 |
| bon solvant | \(R \sim N^{3/5}\) | 0,60 |

: Lois d'échelle du rayon d'une chaîne. {#tab-regimes}

<figure id="fig-schema">
<svg viewBox="0 0 320 90" width="420" role="img" aria-label="Deux boîtes reliées par une flèche : source, puis page">
<rect x="10" y="20" width="110" height="50" rx="4" fill="none" stroke="currentColor"/>
<text x="65" y="50" text-anchor="middle">source .md</text>
<path d="M125 45h60m-8-6 8 6-8 6" fill="none" stroke="var(--accent)" stroke-width="1.6"/>
<rect x="195" y="20" width="110" height="50" rx="4" fill="none" stroke="currentColor"/>
<text x="250" y="50" text-anchor="middle">page .html</text>
</svg>
<figcaption>La source courte devient une page complète.</figcaption>
</figure>

## Exercices

::: exo Exercice 1 — Point critique d'un mélange symétrique
Calculer \(\chi_{12}^c\) pour \(m_1 = m_2 = 100\).

::: indice
Utiliser le résultat de la [](#encadres).
:::

::: corr
Avec \(m_1 = m_2 = m\), \(\chi_{12}^c = 2/m\). [Réponse : \(\chi_{12}^c = 0{,}020\).]{.reponse}
:::
:::

<div class="qcm" data-bonne="2">
<p class="q">Pour un polymère de masse infinie dans un solvant, \(\chi_{12}^c\) tend vers :</p>
<ol><li>0</li><li>\(1/2\)</li><li>1</li></ol>
<div class="explication"><p>Avec \(m_1 = 1\) et \(m_2 \to \infty\), \(\chi_{12}^c \to 1/2\).</p></div>
</div>

<div class="qnum" data-rep="0.020" data-tol="0.02">
<p class="q">Valeur de \(\chi_{12}^c\) pour \(m_1 = m_2 = 100\) ?</p>
<div class="explication"><p>\(2/100 = 0{,}020\).</p></div>
</div>

## Cartes et boutons

::: cartes
::: carte Première carte
Un texte court.
:::

::: carte Seconde carte
Un autre texte court.
:::
:::

[Un bouton](#encadres){.bouton} [Un second](#encadres){.bouton .second}

---

Un filet à losange sépare deux parties.
