import type { Register, ThemeSetArgs } from 'claude-code'

import { makeColors } from './make-colors.js'
import { SCENE } from './scene'

// Jour : le plâtre et la craie d'Utrillo, l'encre et les couleurs d'un article composé en LaTeX.
// Nuit : le fond sombre de Derain, où les couleurs de la rosace prennent la lumière.
const { theme, problems } = makeColors({
  label: 'Atelier et vitrail',
  roles: { accent: '#2f5fae', danger: '#c0392b', success: '#2e7d4f', warning: '#b8660f', pro: '#7b4fa3' },
  light: {
    gray: {
      anchors: {
        'surface-0': '#efebe2',
        'surface-1': '#f6f3ec',
        'surface-2': '#fcfaf6',
        'text-primary': '#1b1616',
        'text-secondary': '#4a4340',
        'text-muted': '#625a55',
      },
    },
  },
  dark: {
    gray: {
      anchors: {
        'surface-0': '#18151a',
        'surface-1': '#1f1b21',
        'surface-2': '#262229',
        'surface-3': '#2a252d',
        'text-primary': '#ece4d4',
        'text-secondary': '#cdc4b4',
        'text-muted': '#aaa193',
      },
    },
  },
})

const LOOK: ThemeSetArgs = {
  colors: theme,
  // Presque pas de flou : les caractères doivent rester des caractères.
  backdrop: { scene: 'atelier', glass: { blur: 1, opacity: 0.74 } },
}

// Le mot de la ligne d'attente, quand l'app n'en dit pas plus que « Working ».
const GESTES = {
  thinking: 'Sketching',
  requesting: 'Feeding the reactor',
  'tool-input': 'Weighing the reagents',
  'tool-use': 'Stirring the reactor',
  responding: 'Laying the colour',
} as const

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const unpainted = problems.find(line => line.startsWith("Desktop won't paint"))

    if (unpainted !== undefined) {
      $.ui.toast(unpainted)
    }
    const set = await $.theme.set(LOOK)

    // Sans requestId, le thème n'a pas pu être posé. Avec, il attend seulement qu'une fenêtre s'ouvre (session lancée
    // en arrière-plan) et s'appliquera alors : pas de quoi prévenir.
    if (!set.isDrawn && set.requestId === undefined) {
      $.ui.status(set.reason)
    }

    return next(e)
  })

  on('ui.render', { component: 'Backdrop' }, ($, e, next) => {
    if (e.surface !== 'desktop' && e.surface !== 'mobile') {
      return next(e)
    }

    const { Svg } = $.ui.resolve(e)

    return (
      <Svg
        source={SCENE}
        alt="Des pelotes de polymère, un réacteur agité, une réponse indicielle et un nœud papillon dessinés en caractères"
        isInteractive
      />
    )
  })

  on('ui.render', { component: 'Spinner' }, ($, e, next) => {
    if (e.props.message !== null || e.props.word !== 'Working') {
      return next(e)
    }

    return next({ ...e, props: { ...e.props, word: GESTES[e.props.mode], suffix: ' <>' } })
  })
}
