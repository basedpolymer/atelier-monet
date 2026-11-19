# Cours complet

À lire quand l'utilisateur demande un cours (plusieurs chapitres) ou des priorités de révision.

Un cours est un dossier : `index.md` (accueil) et une source par chapitre (`01-nom.md`, `02-nom.md`… : l'ordre des noms
de fichier est celui du cours). Construire tout le dossier d'un coup, la navigation changeant avec chaque chapitre :
`python3 <skill>/textured.py dossier/` (`-o sortie/` pour écrire ailleurs). Exemple : `exemples/cours/`.

- **Accueil** : `cours: Nom court` dans l'en-tête, et en général `tirage:`, `densite: compacte`, `epreuve: l'écrit 1`,
  `avertissement:` ; les chapitres en héritent (comme `auteur`, `lang`, `pied`, `prive`, `icone`) s'ils ne disent pas
  autre chose ; tout le cours porte le favicon de l'accueil. Le bloc vide `::: chapitres` puis `:::` place la liste des chapitres et leur priorité (sinon : en fin
  de page). `cle:` fixe la clé du stockage local du cours (filtre des priorités, bandeau lu).
- **Chapitre** : `chapitre: 3` dans l'en-tête. Surtitre « Nom du cours · Chapitre 3 » relié à l'accueil, lettrine au
  numéro, bas de page vers le précédent et le suivant.
- **Priorités** : `## Titre {prio=3}` (★★★ incontournable ; 2 : ★★ ; 1 : ★), aussi `::: exo Titre {prio=2}` ; un
  titre donne son niveau à ce qui le suit. `{prio=3 confirmer="raison"}` : réserve « à confirmer ». Dans l'en-tête
  d'un chapitre, `priorite: 3 — raison` ouvre la page (après un `::: retenir` initial) sur l'encadré « Priorités pour
  <epreuve> » : niveau, raison, ce qui est ★★★ et les réserves.
- L'en-tête des pages a seul les boutons utiles : tout déplier, remettre QCM et jouets à zéro, filtrer par priorité.
- Exercices et QCM en fin de chapitre seulement si l'utilisateur les demande (`exercices.md`) ; jouets : `jouets.md`.
