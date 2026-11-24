# Licences tierces / Third-party licenses

Le skill embarque le travail d'autres auteurs, sous leurs propres licences.
This skill bundles the work of other authors, under their own licenses.

| Composant | Fichiers | Licence |
|---|---|---|
| [TeXtured](https://github.com/jdujava/TeXtured), gabarit LaTeX de Jonáš Dujava : dessin d'origine des titres, filets, lettrine, tableaux | inspiration de `assets/textured.css` | CC0 1.0 (`assets/LICENSE-TeXtured`) |
| [LaTeX.css](https://github.com/vincentdoerig/latex-css), Vincent Dörig : quelques règles de mise en page | inspiration de `assets/textured.css` | MIT (ci-dessous) |
| [KaTeX](https://katex.org) 0.16.11, Khan Academy et contributeurs | `assets/katex.min.js`, `assets/katex.css` (et ses polices embarquées, écrites à part par `--exporter`) | MIT (ci-dessous) |
| Latin Modern (GUST, B. Jackowski, J. M. Nowacki) et TeX Gyre Chorus (GUST) | `assets/polices/*.woff2` (conversions au format WOFF2 ; `*-base.woff2` et `*-ext.woff2` : leurs sous-ensembles, tirés par `polices.py`, fichiers renommés comme le demande la licence) | GUST Font License (`assets/polices/GUST-FONT-LICENSE.txt`), c'est-à-dire LPPL 1.3c |

## MIT : KaTeX

```
The MIT License (MIT)

Copyright (c) 2013-2020 Khan Academy and other contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## MIT : LaTeX.css

```
MIT License

Copyright (c) 2020 Vincent Dörig

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
