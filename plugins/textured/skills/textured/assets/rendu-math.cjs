// Rend des formules KaTeX hors navigateur. Entrée (stdin) : JSON [[tex, bloc], …] ; sortie : JSON [{h: html} | {e: erreur}, …].
'use strict';
const katex = require('./katex.min.js');
let brut = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', d => { brut += d; });
process.stdin.on('end', () => {
  const sortie = JSON.parse(brut).map(([tex, bloc]) => {
    try {
      return { h: katex.renderToString(tex, { displayMode: !!bloc, throwOnError: true, strict: 'ignore', trust: false }) };
    } catch (e) {
      return { e: String(e.message || e).replace(/^KaTeX parse error: /, '') };
    }
  });
  process.stdout.write(JSON.stringify(sortie));
});
