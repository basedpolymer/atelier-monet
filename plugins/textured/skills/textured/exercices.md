# Exercices, QCM, questions numériques

À lire seulement quand l'utilisateur en demande.

```
::: exo Titre de l'exercice {prio=2}
Énoncé.

::: indice
Piste.
:::

::: corr
Correction. [Réponse : \(x = 2\).]{.reponse}
:::
:::
```

`indice` et `corr` sont repliés ; `{prio=…}` est facultatif (voir `cours.md`). QCM et question numérique, en HTML dans
la source (propositions mélangées, bouton « Recommencer » ; `data-tol` : tolérance relative, 3 % par défaut ;
`data-unite` : unité affichée) :

```html
<div class="qcm" data-bonne="2"><p class="q">Question ?</p><ol><li>A</li><li>B</li></ol><div class="explication"><p>Pourquoi.</p></div></div>
<div class="qnum" data-rep="0.020" data-tol="0.02"><p class="q">Valeur ?</p><div class="explication"><p>Calcul.</p></div></div>
```
