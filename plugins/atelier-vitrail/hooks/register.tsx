import type { Register, ThemeSetArgs } from 'claude-code'

import { makeColors } from './make-colors.js'
import { ETAT_INITIAL, scene, type Etat } from './scene'

// Catppuccin : Latte le jour, Frappé la nuit. Les trois fonds de la palette, du plus sombre au plus clair : crust,
// mantle (le fond de la fenêtre), base. Les rôles prennent ses couleurs : mauve pour l'accent, peach pour
// l'avertissement (le jaune se lit mal sur Latte).
const { theme, problems } = makeColors({
  label: 'Atelier et vitrail',
  light: {
    gray: {
      anchors: {
        'surface-0': '#dce0e8', // crust
        'surface-1': '#e6e9ef', // mantle
        'surface-2': '#eff1f5', // base
        'text-primary': '#4c4f69', // text
        'text-secondary': '#5c5f77', // subtext 1
        'text-muted': '#6c6f85', // subtext 0
      },
    },
    roles: { accent: '#8839ef', danger: '#d20f39', success: '#40a02b', warning: '#fe640b', pro: '#ea76cb' },
    git: {
      added: '#40a02b',
      removed: '#d20f39',
      modified: '#df8e1d',
      merged: '#8839ef',
      closed: '#d20f39',
      conflicting: '#fe640b',
      draft: '#8c8fa1',
    },
  },
  dark: {
    gray: {
      anchors: {
        'surface-0': '#232634', // crust
        'surface-1': '#292c3c', // mantle
        'surface-2': '#303446', // base
        'surface-3': '#363a4f', // entre base et surface 0 : plus clair, l'app refuse de peindre le thème (contraste)
        'text-primary': '#c6d0f5', // text
        'text-secondary': '#b5bfe2', // subtext 1
        'text-muted': '#a5adce', // subtext 0
      },
    },
    roles: { accent: '#ca9ee6', danger: '#e78284', success: '#a6d189', warning: '#ef9f76', pro: '#f4b8e4' },
    git: {
      added: '#a6d189',
      removed: '#e78284',
      modified: '#e5c890',
      merged: '#ca9ee6',
      closed: '#e78284',
      conflicting: '#ef9f76',
      draft: '#838ba7',
    },
  },
})

const LOOK: ThemeSetArgs = {
  colors: theme,
  // Presque pas de flou : les caractères doivent rester des caractères.
  backdrop: { scene: 'atelier', glass: { blur: 1, opacity: 0.74 } },
}

// Le mot de la ligne d'attente, quand l'app n'en dit pas plus que « Working » : un geste d'atelier ou de laboratoire par
// mode, qui change à chaque tour (et non à chaque affichage : le mot clignoterait).
const GESTES = {
  thinking: ['Annealing', 'Nucleating', 'Equilibrating', 'Relaxing the chains', 'Sketching'],
  requesting: ['Purging with nitrogen', 'Charging the reactor', 'Warming the jacket', 'Feeding the reactor'],
  'tool-input': ['Weighing the reagents', 'Titrating'],
  'tool-use': ['Stirring the reactor', 'Sampling the batch', 'Quenching', 'Firing the glass'],
  responding: ['Extruding', 'Casting the film', 'Leading the panes', 'Laying the colour'],
} as const

// Ce que le fond sait de la session. Ces variables repartent de zéro quand le thème est rechargé : la session reçoit
// alors un nouveau tirage, rien de plus.
let graine = ETAT_INITIAL.graine
let debut: number | null = null
let temps = 0
let travail = false
let tours = 0
// La longueur des chaînes, en tours : un de plus à chaque tour, la moitié après une compaction.
let longueur = 0

// Les chaînes sont déjà à moitié là au premier tour, et complètes vers le quinzième.
const etat = (): Etat => ({ graine, temps, travail, croissance: 1 - 0.55 * Math.exp(-longueur / 5) })

// Le dernier fond dessiné, par orientation : un nouveau dessin seulement quand l'état a changé.
const dessins = new Map<boolean, readonly [Etat, string]>()
function fond(portrait: boolean): string {
  const now = etat()
  const last = dessins.get(portrait)
  if (last !== undefined && last[0].temps === now.temps && last[0].travail === now.travail && last[0].graine === now.graine) {
    return last[1]
  }
  const drawn = scene(now, portrait)
  dessins.set(portrait, [now, drawn])
  return drawn
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const unpainted = problems.find(line => line.startsWith("Desktop won't paint"))

    if (unpainted !== undefined) {
      $.ui.toast(unpainted)
    }
    // La graine de la session : l'heure de son début. Elle tire les motifs, la réaction, les conformations.
    debut = await $.clock.now()
    graine = Math.floor(debut / 1000) % 2147483647
    const set = await $.theme.set(LOOK)

    // Sans requestId, le thème n'a pas pu être posé. Avec, il attend seulement qu'une fenêtre s'ouvre (session lancée
    // en arrière-plan) et s'appliquera alors : pas de quoi prévenir.
    if (!set.isDrawn && set.requestId === undefined) {
      $.ui.status(set.reason)
    }

    return next(e)
  })

  // Le fond suit le travail de Claude : il est redessiné au début et à la fin de chaque tour de la boucle principale
  // (pas ceux des sous-agents), jamais entre les deux. Chaque mouvement continu reprend où il en était (scene.ts).
  on('turn.start', async ($, e, next) => {
    if (e.agentId === undefined) {
      tours += 1
      longueur += 1
      const now = await $.clock.now()
      debut ??= now
      temps = Math.round((now - debut) / 1000)
      travail = true
      $.ui.invalidate('ui.render')
    }

    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    if (e.agentId === undefined) {
      const now = await $.clock.now()
      debut ??= now
      temps = Math.round((now - debut) / 1000)
      travail = false
      $.ui.invalidate('ui.render')
    }

    return next(e)
  })

  on('session.compact', ($, e, next) => {
    longueur /= 2

    return next(e)
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'Backdrop' }, ($, e, next) => {
    if (e.surface !== 'desktop' && e.surface !== 'mobile') {
      return next(e)
    }

    const { Svg } = $.ui.resolve(e)

    // Le téléphone a la scène en portrait ; la fenêtre, la scène entière.
    return (
      <Svg
        source={fond(e.surface === 'mobile')}
        alt="Des pelotes de polymère, une réaction en formule topologique et quelques schémas de génie chimique dessinés en caractères"
        isInteractive
      />
    )
  })

  on('ui.render', { component: 'Spinner' }, ($, e, next) => {
    if (e.props.message !== null || e.props.word !== 'Working') {
      return next(e)
    }
    const words = GESTES[e.props.mode]

    return next({ ...e, props: { ...e.props, word: words[tours % words.length]!, suffix: ' <>' } })
  })
}
