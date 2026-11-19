// Le fond du thème : un seul SVG fait de caractères ASCII, animé en CSS.
// Les motifs viennent du génie chimique ; les couleurs, de la peinture.
//
//   en haut à droite : des pelotes de polymère qui oscillent et tournent,
//                      leur rayon en pointillé, et le motif du PET dessous
//   en bas à gauche  : un réacteur agité, sa surface, ses bulles, sa pale
//   en bas à droite  : une réponse indicielle qui se trace, et sa boucle
//   à gauche         : un nœud papillon, l'événement central au milieu

const esc = (s: string): string => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

// Couleurs de verre : lisibles sur le plâtre clair comme sur le fond sombre.
const COBALT = '#3e6fc4'
const RUBIS = '#b5452f'
const OR = '#c2912e'
const VIOLET = '#7b5fb0'
const VERT = '#3a8a6a'
const EAU = '#3f8f96'
const ROSE = '#c77a8f'
const CRAIE = '#8a857d'

const CHAR = 8.4 // largeur d'un caractère à 14 px

function lines(rows: readonly string[], x: number, y: number, step: number): string {
  return rows.map((row, i) => `<text x="${x}" y="${y + i * step}">${esc(row)}</text>`).join('')
}

// Un générateur à graine : le même dessin à chaque chargement.
function seeded(seed: number): () => number {
  let state = seed
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296
    return state / 4294967296
  }
}

// Une chaîne : marche aléatoire à angle persistant, ramenée vers le centre
// quand elle s'éloigne, puis lissée ; les monomères suivent le tracé.
function chain(index: number, seed: number, steps: number, color: string, seconds: number): string {
  const random = seeded(seed)
  let x = (random() - 0.5) * 120
  let y = (random() - 0.5) * 120
  let angle = random() * Math.PI * 2
  const points: Array<[number, number]> = [[x, y]]
  for (let i = 0; i < steps; i += 1) {
    angle += (random() - 0.5) * 2.4
    const away = Math.hypot(x, y)
    if (away > 170) {
      const home = Math.atan2(-y, -x)
      angle += Math.atan2(Math.sin(home - angle), Math.cos(home - angle)) * 0.6
    }
    x += Math.cos(angle) * 30
    y += Math.sin(angle) * 30
    points.push([x, y])
  }

  let d = `M ${points[0]![0].toFixed(1)},${points[0]![1].toFixed(1)}`
  let length = 0
  for (let i = 1; i < points.length - 1; i += 1) {
    const [px, py] = points[i]!
    const [nx, ny] = points[i + 1]!
    d += ` Q ${px.toFixed(1)},${py.toFixed(1)} ${((px + nx) / 2).toFixed(1)},${((py + ny) / 2).toFixed(1)}`
    length += 30
  }
  const beads = 'o-'.repeat(Math.floor((length * 0.92) / (2 * CHAR)))

  return (
    `<g style="animation:gonfle ${seconds}s ease-in-out ${-index * 5}s infinite alternate">` +
    `<path id="c${index}" fill="none" d="${d}"/>` +
    `<text fill="${color}" style="animation:respire ${9 + index * 3}s ease-in-out ${-index * 2.1}s infinite">` +
    `<textPath href="#c${index}">${esc(beads)}</textPath></text></g>`
  )
}

function pelotes(): string {
  const radius = 236
  const circumference = 2 * Math.PI * radius
  const dots = '+ . '.repeat(Math.floor(circumference / (4 * CHAR)))

  return (
    `<g class="pelotes">` +
    `<g style="animation:tourne 720s linear infinite">` +
    `<path id="rg" fill="none" d="M ${radius},0 A ${radius},${radius} 0 1,1 -${radius},0 A ${radius},${radius} 0 1,1 ${radius},0"/>` +
    `<text fill="${OR}" textLength="${circumference.toFixed(1)}" lengthAdjust="spacing"><textPath href="#rg">${esc(dots)}</textPath></text></g>` +
    chain(0, 625, 46, COBALT, 23) +
    chain(1, 1925, 40, RUBIS, 29) +
    chain(2, 1888, 34, VIOLET, 19) +
    `<g fill="${CRAIE}" opacity=".8">` +
    `<text x="-70" y="${radius + 34}">${esc('R ~ a.N^(3/5)')}</text>` +
    `<text x="-126" y="${radius + 58}">${esc('-[-O-CH2-CH2-O-CO-C6H4-CO-]n-')}</text></g></g>`
  )
}

function reacteur(): string {
  const vessel = [
    '   A ==>==+',
    '          |',
    ' .--------+-----------------.',
    ' |                          |',
    ' |                          |',
    ' |                          |',
    ' |                          |',
    ' |                          |',
    " '-------------.------------'",
    '               |',
    '               +==>== A + B',
  ]
  const surface =
    `<text x="${4 * CHAR}" y="54" fill="${EAU}" style="animation:glisse 14s ease-in-out infinite alternate">` +
    `${esc('~~ ~ ~~~ ~ ~~ ~~~ ~ ~~')}</text>`

  // L'arbre et la pale, en deux poses qui alternent.
  const shaft = `<g fill="${RUBIS}">${lines(['|', '|', '|'], 10 * CHAR, 68, 17)}`
  const blades =
    `<text x="${6 * CHAR}" y="119" style="animation:pale 2.8s steps(1) infinite">${esc('----+----')}</text>` +
    `<text class="pose2" x="${6 * CHAR}" y="119" style="animation:pale 2.8s steps(1) -1.4s infinite">${esc(' \\--+--/ ')}</text></g>`

  const spots: ReadonlyArray<readonly [number, string, string, number]> = [
    [4, 'o', COBALT, 9],
    [8, '.', VIOLET, 7],
    [14, 'o', ROSE, 11],
    [18, 'O', COBALT, 13],
    [22, '.', VERT, 8],
    [25, 'o', VIOLET, 10],
  ]
  const bubbles = spots
    .map(
      ([column, glyph, color, seconds], i) =>
        `<text x="${column * CHAR}" y="130" fill="${color}" ` +
        `style="animation:bulle ${seconds}s ease-in ${(-i * 1.9).toFixed(1)}s infinite">${glyph}</text>`,
    )
    .join('')

  return `<g class="reacteur"><g fill="${CRAIE}">${lines(vessel, 0, 0, 17)}</g>${surface}${shaft}${blades}${bubbles}</g>`
}

function boucle(): string {
  // Réponse indicielle d'un second ordre sous-amorti, point par point.
  const columns = 34
  const cycle = 16
  let curve = ''
  for (let i = 0; i < columns; i += 1) {
    const t = i / (columns - 1)
    const value = 1 - Math.exp(-4.2 * t) * Math.cos(13 * t)
    const px = 3 * CHAR + i * CHAR
    const py = 120 - 72 * value
    curve +=
      `<text x="${px.toFixed(1)}" y="${py.toFixed(1)}" fill="${i % 2 === 0 ? COBALT : VIOLET}" ` +
      `style="animation:trace ${cycle}s linear ${(i * 0.16).toFixed(2)}s infinite backwards">*</text>`
  }

  const axes = ['^', '|', '|', '|', '|', '|', '|', '+-------------------------------------> t']
  const setpoint = `<text x="${3 * CHAR}" y="48" fill="${OR}">${esc('- - - - - - - - - - - - - - - - - -')}</text>`
  const diagram = [
    'yc -->(+)-->[ C(p) ]-->[ G(p) ]--+--> y',
    '       ^                         |',
    "       '-------------------------'",
  ]

  return (
    `<g class="boucle"><g fill="${CRAIE}">${lines(axes, CHAR, 6, 17)}${lines(diagram, 0, 168, 17)}</g>` +
    `${setpoint}${curve}</g>`
  )
}

function papillon(): string {
  const tie = [
    'o--.                 .--o',
    'o---\\               /---o',
    'o----+-->       >--+----o',
    'o---/               \\---o',
    "o--'                 '--o",
  ]

  return (
    `<g class="papillon"><g fill="${CRAIE}">${lines(tie, 0, 0, 17)}</g>` +
    `<text x="${10 * CHAR}" y="34" fill="${RUBIS}" style="animation:respire 8s ease-in-out infinite">${esc('(ERC)')}</text></g>`
  )
}

// gonfle : rotation seule. Une échelle animée (scale) oblige Chromium à rastériser de nouveau le texte des pelotes à
// chaque image (près d'un cœur de processeur en continu) ; rotation et opacité restent au compositeur. En portrait, la
// boucle et le papillon sont masqués : leurs animations sont arrêtées aussi (!important : elles sont dans l'attribut style).
const STYLE = `
text{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:14px;white-space:pre}
.scene{opacity:.62}
@media (prefers-color-scheme:dark){.scene{opacity:.8}}
.boucle,.papillon,.reacteur{opacity:.8}
@keyframes tourne{to{transform:rotate(360deg)}}
@keyframes respire{0%,100%{opacity:.45}50%{opacity:1}}
@keyframes gonfle{from{transform:rotate(-5deg)}to{transform:rotate(6deg)}}
@keyframes glisse{from{transform:translateX(-12px)}to{transform:translateX(12px)}}
@keyframes pale{0%{opacity:1}50%,100%{opacity:0}}
@keyframes bulle{0%{transform:translate(0,0);opacity:0}15%{opacity:.9}100%{transform:translate(5px,-72px);opacity:0}}
@keyframes trace{0%{opacity:0}2%{opacity:1}80%{opacity:1}90%,100%{opacity:0}}
@media (max-aspect-ratio:1/1){.pelotes-place{transform:translate(800px,280px) scale(.8)}.boucle-place,.papillon-place{display:none}:is(.boucle-place,.papillon-place) *{animation:none!important}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}.pose2{display:none}}
`

export const SCENE: string =
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid slice" xml:space="preserve">` +
  `<style>${STYLE}</style><g class="scene">` +
  `<g class="pelotes-place" transform="translate(1290 300)">${pelotes()}</g>` +
  `<g class="reacteur-place" transform="translate(50 760)">${reacteur()}</g>` +
  `<g class="boucle-place" transform="translate(1180 730)">${boucle()}</g>` +
  `<g class="papillon-place" transform="translate(50 330)">${papillon()}</g>` +
  `</g></svg>`
