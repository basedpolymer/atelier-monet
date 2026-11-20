/* TeXtured HTML — moteur minimal. La page est complète sans lui (plan statique, thème du système) :
   il ajoute le bouton de thème, le titre courant, le repère du plan, l'ouverture des replis à l'impression.
   Blocs « @ nom | motif » : textured.py ne garde que ceux dont le motif apparaît dans le document. */

/*@ base */
(() => {
  const racine = document.documentElement;
  // thème : auto (celui du système), clair ou sombre ; le choix est gardé ("tx-theme" : light, dark, rien pour auto)
  // et vaut pour toutes les pages du même site. Le bouton fait tourner les trois états et en montre l'icône.
  const sombre = matchMedia("(prefers-color-scheme: dark)");
  const bouton = document.querySelector(".tete .theme");
  const lire = () => { try { const v = localStorage.getItem("tx-theme"); return v === "light" || v === "dark" ? v : "auto"; } catch { return "auto"; } };
  const ICONES = {
    auto: '<circle cx="8" cy="8" r="5.6"/><path d="M8 2.4a5.6 5.6 0 0 1 0 11.2z" fill="currentColor"/>',
    light: '<circle cx="8" cy="8" r="2.9"/><path d="M8 1.2v1.7M8 13.1v1.7M1.2 8h1.7M13.1 8h1.7M3.2 3.2l1.2 1.2M11.6 11.6l1.2 1.2M12.8 3.2l-1.2 1.2M4.4 11.6l-1.2 1.2"/>',
    dark: '<path d="M13.5 9.6A6 6 0 0 1 6.4 2.5a6 6 0 1 0 7.1 7.1z"/>',
  };
  const NOMS = (racine.lang || "fr").slice(0, 2) === "en"
    ? { auto: "Theme: auto", light: "Theme: light", dark: "Theme: dark" }
    : { auto: "Thème : automatique", light: "Thème : clair", dark: "Thème : sombre" };
  let choix = lire();
  const peindre = () => {
    if (choix === "auto") delete racine.dataset.theme; else racine.dataset.theme = choix;
    if (bouton) {
      bouton.innerHTML = '<svg viewBox="0 0 16 16" aria-hidden="true">' + ICONES[choix] + "</svg>";
      bouton.title = NOMS[choix]; bouton.setAttribute("aria-label", NOMS[choix]); bouton.removeAttribute("aria-pressed");
    }
    const fond = getComputedStyle(document.body).backgroundColor;
    document.querySelectorAll('meta[name="theme-color"]').forEach(m => { m.removeAttribute("media"); m.content = fond; });
    dispatchEvent(new CustomEvent("tx-theme", { detail: { choix, theme: choix === "auto" ? (sombre.matches ? "dark" : "light") : choix } }));
  };
  // sur un site qui charge atelier.js, c'est lui qui tient le thème (il force aussi les @media des autres feuilles)
  if (window.txTheme) { if (bouton) window.txTheme.brancher(bouton); }
  else if (bouton) bouton.addEventListener("click", () => {
    choix = { auto: "light", light: "dark", dark: "auto" }[choix];
    try { if (choix === "auto") localStorage.removeItem("tx-theme"); else localStorage.setItem("tx-theme", choix); } catch {}
    peindre();
  });
  if (!window.txTheme) {
    sombre.addEventListener("change", () => { if (choix === "auto") peindre(); });
    addEventListener("storage", e => { if (e.key === "tx-theme") { choix = lire(); peindre(); } });
    peindre();
  }

  // bouton du sommaire : le montre ou le masque en fondu (sans fondu si l'on préfère le calme), et s'en souvient ;
  // replié par défaut (l'amorce du <head> pose « sans-plan » tant que tx-plan ne vaut pas "1")
  const bPlan = document.querySelector(".tete .plan-bouton");
  if (bPlan) {
    const nav = document.getElementById("plan");
    const dire = () => bPlan.setAttribute("aria-expanded", String(!racine.classList.contains("sans-plan")));
    // le fondu n'existe que si la feuille donne au sommaire une transition (voir « sommaire : apparition »)
    const fondu = () => nav && getComputedStyle(nav).transitionDuration.split(",").some(d => parseFloat(d) > 0);
    let sortie = 0;
    const finir = () => { clearTimeout(sortie); sortie = 0; racine.classList.add("sans-plan"); racine.classList.remove("plan-sortie"); dire(); };
    // sur un écran étroit, le sommaire flotte au-dessus de la page (voir la feuille) : ouvert, il ne s'y rouvre pas seul
    const flottant = () => nav && getComputedStyle(nav).position === "fixed";
    const ouvert = () => !racine.classList.contains("sans-plan") && !sortie;
    bPlan.addEventListener("click", () => {
      const cacher = ouvert();
      try { if (cacher) localStorage.removeItem("tx-plan"); else if (!flottant()) localStorage.setItem("tx-plan", "1"); } catch {}
      if (cacher && fondu()) {
        racine.classList.add("plan-sortie");
        sortie = setTimeout(finir, 400);
        nav.addEventListener("transitionend", e => { if (e.target === nav && sortie) finir(); }, { once: true });
        bPlan.setAttribute("aria-expanded", "false");
      } else if (cacher) {
        finir();
      } else {
        clearTimeout(sortie); sortie = 0;
        racine.classList.remove("plan-sortie");
        if (fondu()) { racine.classList.add("plan-entree"); racine.classList.remove("sans-plan"); void nav.offsetWidth; racine.classList.remove("plan-entree"); }
        else racine.classList.remove("sans-plan");
        dire();
      }
    });
    if (nav) {
      nav.addEventListener("click", e => { if (e.target.closest("a") && flottant() && ouvert()) bPlan.click(); });
      document.addEventListener("click", e => { if (flottant() && ouvert() && !nav.contains(e.target) && !bPlan.contains(e.target)) bPlan.click(); });
      addEventListener("keydown", e => { if (e.key === "Escape" && flottant() && ouvert()) { bPlan.click(); bPlan.focus(); } });
    }
    dire();
  }

  // ancres : au survol d'un titre de section, un « # » dont le clic copie l'adresse de la section (et la met dans la barre)
  const EN = (racine.lang || "fr").slice(0, 2) === "en";
  const DIRE = EN ? ["Copy the link to this section", "Link copied"] : ["Copier le lien vers cette section", "Lien copié"];
  document.querySelectorAll("main :is(h2, h3)[id]").forEach(h => {
    if (h.querySelector(":scope > .ancre")) return;
    const a = document.createElement("a");
    a.className = "ancre"; a.href = "#" + h.id; a.title = DIRE[0]; a.setAttribute("aria-label", DIRE[0]);
    let delai = 0;
    a.addEventListener("click", e => {
      e.preventDefault();
      const url = location.href.split("#")[0] + "#" + encodeURIComponent(h.id);
      history.replaceState(history.state, "", "#" + encodeURIComponent(h.id));
      const fait = () => { a.classList.add("copie"); a.title = DIRE[1]; clearTimeout(delai); delai = setTimeout(() => { a.classList.remove("copie"); a.title = DIRE[0]; }, 1600); };
      const repli = () => { const t = document.createElement("textarea"); t.value = url; t.style.cssText = "position:fixed;opacity:0"; document.body.append(t); t.select(); try { if (document.execCommand("copy")) fait(); } catch {} t.remove(); };
      if (navigator.clipboard && isSecureContext) navigator.clipboard.writeText(url).then(fait, repli); else repli();
    });
    h.append(a);
  });

  // titre courant dans l'en-tête et repère du plan
  const tete = document.querySelector(".tete");
  const courant = tete && tete.querySelector(".courant");
  const titres = [...document.querySelectorAll("main :is(h2, h3)[id]")];
  const liens = new Map([...document.querySelectorAll("nav.plan a[href^='#']")].map(a => [a.getAttribute("href").slice(1), a]));
  const texte = h => { const c = h.cloneNode(true); c.querySelectorAll(".katex-mathml, .ancre, .prio, .prio-conf").forEach(e => e.remove()); c.querySelectorAll(".num").forEach(e => e.append("\u2002")); return c.textContent.trim(); };
  const base = courant ? courant.textContent : "";
  let dernier, attente = false;
  const suivre = () => {
    attente = false;
    const seuil = (tete ? tete.offsetHeight : 0) + 24;
    let vu = null;
    for (const h of titres) { if (h.getBoundingClientRect().top <= seuil) vu = h; else break; }
    if (tete) tete.classList.toggle("premiere", scrollY < 8);
    if (vu === dernier) return;
    dernier = vu;
    if (courant) courant.textContent = vu ? texte(vu.tagName === "H3" ? titres.slice(0, titres.indexOf(vu)).reverse().find(t => t.tagName === "H2") || vu : vu) : base;
    liens.forEach(a => a.removeAttribute("aria-current"));
    const lien = vu && liens.get(vu.id);
    if (lien) { lien.setAttribute("aria-current", "true"); if (lien.offsetParent && getComputedStyle(lien.closest("nav")).position === "sticky") lien.scrollIntoView({ block: "nearest" }); }
  };
  addEventListener("scroll", () => { if (!attente) { attente = true; requestAnimationFrame(suivre); } }, { passive: true });
  suivre();

  // impression : tout déplier, puis remettre en l'état
  let replies = [];
  addEventListener("beforeprint", () => { replies = [...document.querySelectorAll("details:not([open])")]; replies.forEach(d => { d.open = true; }); });
  addEventListener("afterprint", () => { replies.forEach(d => { d.open = false; }); });
})();

/*@ outils | Cours\. */
/* Boîte à outils des jouets, reprise du moteur des cours complets (cours.js) : window.Cours. Référence : jouets.md.
   Une courbe, un marqueur ou une entrée de légende sans couleur prend l'encre de la page (« tirage »).
   Le code d'un jouet s'écrit dans Cours.pret(() => { … }) : l'amorce du <head> met ces fonctions en attente, elles
   s'exécutent une fois la page lue et les polices des canevas chargées. */
(() => {
  const racine = document.documentElement;
  const attente = (window.Cours && window.Cours._p) || [];
  const CLE = racine.dataset.cle || "tx:";
  const store = {
    get(k) { try { return localStorage.getItem(CLE + k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(CLE + k, v); } catch (e) { /* rien */ } },
    del(k) { try { localStorage.removeItem(CLE + k); } catch (e) { /* rien */ } },
  };

  /* ---------- nombres à la française (à l'anglaise sur une page lang="en") ---------- */
  const EN = (racine.lang || "fr").slice(0, 2) === "en", VIRGULE = EN ? "." : ",";
  const SUP = { "-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹" };
  function fmt(x, d = 3) {
    if (!isFinite(x)) return "—";
    const s = Number(x).toFixed(d).replace(".", VIRGULE).replace(/^-(0[.,]?0*)$/, "$1").replace(/^-/, "−");
    return Math.abs(x) < 1e4 ? s : s.replace(/\d+/, e => e.replace(/\B(?=(\d{3})+$)/g, EN ? "," : " "));
  }
  function fmtE(x, d = 3) {
    if (!isFinite(x)) return "—";
    if (x === 0) return "0";
    let e = Math.floor(Math.log10(Math.abs(x)));
    let m = x / Math.pow(10, e);
    if (Math.abs(+m.toFixed(d - 1)) >= 10) { m /= 10; e += 1; }
    return m.toFixed(d - 1).replace(".", VIRGULE).replace(/^-/, "−") + "·10" + String(e).split("").map(c => SUP[c]).join("");
  }
  function fmtS(x, d = 3) {
    if (!isFinite(x)) return "—";
    if (x === 0) return "0";
    const e = Math.floor(Math.log10(Math.abs(x)));
    return e >= -3 && e <= 4 ? fmt(x, Math.max(0, d - 1 - e)) : fmtE(x, d);
  }

  /* ---------- formules à l'exécution (KaTeX n'est embarqué que si la page appelle Cours.tex ou Cours.renderMath) ---------- */
  const OPTIONS_KATEX = { throwOnError: false, strict: "ignore", trust: false, macros: {} };
  function tex(el, latex, display = false) {
    if (!window.katex) { el.textContent = latex; return; }
    window.katex.render(latex, el, Object.assign({ displayMode: display }, OPTIONS_KATEX));
  }
  const EXCLUS = new Set(["SCRIPT", "STYLE", "TEXTAREA", "CODE", "PRE", "OPTION", "INPUT"]);
  function renderMath(base = document.body) {
    if (!window.katex) return;
    const marcheur = document.createTreeWalker(base, NodeFilter.SHOW_TEXT, {
      acceptNode(n) {
        if (!n.nodeValue || (n.nodeValue.indexOf("\\(") < 0 && n.nodeValue.indexOf("\\[") < 0)) return NodeFilter.FILTER_REJECT;
        for (let p = n.parentNode; p && p !== base.parentNode; p = p.parentNode)
          if (EXCLUS.has(p.nodeName) || (p.classList && p.classList.contains("katex"))) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    const noeuds = [];
    while (marcheur.nextNode()) noeuds.push(marcheur.currentNode);
    const re = /\\\(([\s\S]+?)\\\)|\\\[([\s\S]+?)\\\]/g;
    for (const n of noeuds) {
      const s = n.nodeValue, frag = document.createDocumentFragment();
      let dernier = 0, m;
      re.lastIndex = 0;
      while ((m = re.exec(s))) {
        if (m.index > dernier) frag.appendChild(document.createTextNode(s.slice(dernier, m.index)));
        const bloc = m[2] != null, span = document.createElement("span");
        span.className = bloc ? "formule" : "formule-inline";
        tex(span, bloc ? m[2] : m[1], bloc);
        frag.appendChild(span);
        dernier = re.lastIndex;
      }
      if (dernier < s.length) frag.appendChild(document.createTextNode(s.slice(dernier)));
      n.parentNode.replaceChild(frag, n);
    }
  }
  /* texte avec des formules entre § … § (verdicts) : les morceaux pairs en texte, les impairs en KaTeX */
  function ecrireTexte(el, s) {
    el.textContent = "";
    String(s).split("§").forEach((m, i) => {
      if (i % 2) { const sp = document.createElement("span"); tex(sp, m); el.appendChild(sp); }
      else if (m) el.appendChild(document.createTextNode(m));
    });
  }

  /* ---------- outils numériques ---------- */
  const num = {
    linspace(a, b, n) { const r = []; for (let i = 0; i < n; i++) r.push(a + (b - a) * i / (n - 1)); return r; },
    logspace(a, b, n) { return num.linspace(Math.log10(a), Math.log10(b), n).map(v => Math.pow(10, v)); },
    /* racine de f sur [a, b] par dichotomie (f(a) et f(b) de signes opposés) ; null sinon */
    bisect(f, a, b, tol = 1e-12, it = 200) {
      let fa = f(a), fb = f(b);
      if (!isFinite(fa) || !isFinite(fb) || fa * fb > 0) return null;
      for (let i = 0; i < it; i++) {
        const c = (a + b) / 2, fc = f(c);
        if (fc === 0 || (b - a) / 2 < tol) return c;
        if (fa * fc < 0) { b = c; fb = fc; } else { a = c; fa = fc; }
      }
      return (a + b) / 2;
    },
    /* toutes les racines de f sur [a, b], repérées par changement de signe sur n intervalles */
    racines(f, a, b, n = 400) {
      const r = []; let x0 = a, f0 = f(a);
      for (let i = 1; i <= n; i++) {
        const x1 = a + (b - a) * i / n, f1 = f(x1);
        if (isFinite(f0) && isFinite(f1) && f0 * f1 <= 0 && !(f0 === 0 && i > 1)) { const z = num.bisect(f, x0, x1); if (z != null) r.push(z); }
        x0 = x1; f0 = f1;
      }
      return r;
    },
    /* minimum de f sur [a, b] (section dorée, f unimodale) */
    golden(f, a, b, tol = 1e-10) {
      const g = (Math.sqrt(5) - 1) / 2; let c = b - g * (b - a), d = a + g * (b - a);
      while (Math.abs(b - a) > tol) { if (f(c) < f(d)) b = d; else a = c; c = b - g * (b - a); d = a + g * (b - a); }
      return (a + b) / 2;
    },
    deriv(f, x, h = 1e-6) { return (f(x + h) - f(x - h)) / (2 * h); },
    /* régression linéaire y = a + b x */
    linreg(xs, ys) {
      const n = xs.length; let sx = 0, sy = 0, sxx = 0, sxy = 0, syy = 0;
      for (let i = 0; i < n; i++) { sx += xs[i]; sy += ys[i]; sxx += xs[i] * xs[i]; sxy += xs[i] * ys[i]; syy += ys[i] * ys[i]; }
      const b = (n * sxy - sx * sy) / (n * sxx - sx * sx), a = (sy - b * sx) / n;
      const r = (n * sxy - sx * sy) / Math.sqrt((n * sxx - sx * sx) * (n * syy - sy * sy));
      return { a, b, r2: r * r };
    },
    /* nombres pseudo-aléatoires reproductibles */
    rng(graine = 1) { let s = graine >>> 0 || 1; return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; }; },
    gauss(rand) { let u = 0, v = 0; while (u === 0) u = rand(); while (v === 0) v = rand(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); },
  };

  /* ---------- couleurs ----------
     Les couleurs de la page sont écrites en light-dark() : getComputedStyle rendrait la formule, pas la couleur. Une
     sonde invisible la résout dans le thème courant ; le cache se vide à chaque changement de thème. */
  const NOMS = ["bleu", "rouge", "vert", "orange", "violet", "gris", "cyan", "encre", "doux", "trait", "grille", "papier", "fond",
    "accent", "tirage", "pastel", "pastel-encre", "pastel-fond", "jouet-bord"];
  const cache = new Map();
  let sonde = null;
  function couleur(c) {
    if (!c) c = "encre";
    if (!NOMS.includes(c)) return c;
    if (cache.has(c)) return cache.get(c);
    if (!sonde) { sonde = document.createElement("span"); sonde.style.display = "none"; sonde.setAttribute("aria-hidden", "true"); }
    if (!sonde.isConnected) (document.body || racine).appendChild(sonde);
    sonde.style.color = "";
    sonde.style.color = `var(--${c}, var(--encre))`;
    const v = getComputedStyle(sonde).color || "#333";
    cache.set(c, v);
    return v;
  }

  /* ---------- tracé ---------- */
  const POLICE_GRAPHE = '"TX Sans", "Latin Modern Sans", "Helvetica Neue", Arial, sans-serif';
  /* Latin Modern n'a pas de minuscules grecques : elles s'écrivent en italique mathématique de KaTeX (KaTeX_Math, dont
     textured.py embarque la police dès qu'une page emploie Cours.) ; le point de γ̇ vient de KaTeX_Main. */
  const POLICE_GREC = 'KaTeX_Math, "Times New Roman", serif', POLICE_ACCENT = 'KaTeX_Main, "Times New Roman", serif';
  const GREC = /[α-ωϑϕϖϱϵ]/;
  const UNI_H = { "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "⁻": "-", "⁺": "+", "ⁿ": "n" };
  const UNI_B = { "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9", "₊": "+", "₋": "−",
    "ₐ": "a", "ₑ": "e", "ₒ": "o", "ₓ": "x", "ₕ": "h", "ₖ": "k", "ₗ": "l", "ₘ": "m", "ₙ": "n", "ₚ": "p", "ₛ": "s", "ₜ": "t" };
  const RICHE = /[α-ωϑϕϖϱϵ̇_^\\⁰-ₜ²³¹]/;
  function ticksLin(a, b, cible = 6) {
    const pas0 = (b - a) / cible, p10 = Math.pow(10, Math.floor(Math.log10(pas0)));
    const r = pas0 / p10, pas = (r < 1.5 ? 1 : r < 3 ? 2 : r < 7 ? 5 : 10) * p10;
    const t = []; for (let v = Math.ceil(a / pas - 1e-9) * pas; v <= b + pas * 1e-9; v += pas) t.push(Math.abs(v) < pas * 1e-9 ? 0 : v);
    return { t, pas };
  }
  function ticksPas(a, b, pas) {
    const t = []; for (let k = Math.ceil(a / pas - 1e-9); k * pas <= b + pas * 1e-9; k++) t.push(Math.abs(k * pas) < pas * 1e-9 ? 0 : k * pas);
    return { t, pas };
  }
  function etiquette(v, pas, sci) {
    if (v === 0) return "0";
    if (sci) { const e = Math.floor(Math.log10(Math.abs(pas))); const d = Math.max(1, Math.min(3, Math.floor(Math.log10(Math.abs(v))) - e + 1)); return fmtE(v, d); }
    let d = Math.max(0, -Math.floor(Math.log10(pas) + 1e-9));
    while (d < 6 && Math.abs(pas * 10 ** d - Math.round(pas * 10 ** d)) > 1e-6) d++;
    return fmt(v, d);
  }
  const estSci = (a, b) => { const m = Math.max(Math.abs(a), Math.abs(b)); return m >= 1e5 || m < 1e-2; };
  function etiquetteLog(e) {
    if (e >= 0 && e <= 3) return String(Math.pow(10, e));
    if (e < 0 && e >= -2) return fmt(Math.pow(10, e), -e);
    return "10" + String(e).split("").map(c => SUP[c]).join("");
  }
  function etiquetteLibre(v) {
    if (v === 0) return "0";
    const e = Math.floor(Math.log10(Math.abs(v)) + 1e-9);
    if (e >= -3 && e <= 4) return String(+v.toPrecision(4)).replace(".", VIRGULE);
    const m = +(v / Math.pow(10, e)).toPrecision(3);
    return (m === 1 ? "" : String(m).replace(".", VIRGULE) + "·") + "10" + String(e).split("").map(c => SUP[c]).join("");
  }

  /* ---------- texte des canevas : mini-format ----------
     η_{sp}, R_G^2, C_p, M^(−1/2) : « _ » met en indice, « ^ » en exposant, soit un groupe {…} (ou (…) après ^), soit un
     mot. Un indice suivi d'un exposant s'empilent. \_ \^ \\ donnent le caractère. Grec en KaTeX_Math italique ; un
     caractère suivi de U+0307 reçoit un point au-dessus ; exposants et indices Unicode (10⁻³, φ₂) réécrits de même. */
  const MOT = "[\\p{L}\\p{M}0-9*′∗∞\\u00bc-\\u00be\\u2150-\\u215e]+";
  const RE_IND = new RegExp("^" + MOT, "u"), RE_EXP = new RegExp("^[−+-]?(?:[0-9]+/[0-9]+|" + MOT + ")", "u");
  function groupe(s, i, ouv, ferm) {
    let n = 1, j = i + 1;
    while (j < s.length && n) { if (s[j] === ouv) n++; else if (s[j] === ferm) n--; j++; }
    return n ? null : [s.slice(i + 1, j - 1), j];
  }
  function argument(s, i, exp) {
    if (i >= s.length) return null;
    if (s[i] === "{") return groupe(s, i, "{", "}");
    if (exp && s[i] === "(") return groupe(s, i, "(", ")");
    const m = (exp ? RE_EXP : RE_IND).exec(s.slice(i));
    return m ? [m[0], i + m[0].length] : null;
  }
  function analyser(s) {
    const seg = []; let base = "", dernier = -1;
    for (let i = 0; i < s.length;) {
      const c = s[i];
      if (UNI_H[c] || UNI_B[c]) {
        const t = UNI_H[c] ? UNI_H : UNI_B; let a = "";
        while (i < s.length && t[s[i]]) a += t[s[i++]];
        if (base) { seg.push({ t: base, r: 0 }); base = ""; }
        const r = t === UNI_H ? "h" : "b", prec = seg[seg.length - 1];
        seg.push({ t: a, r, pile: dernier === i - a.length && prec && prec.r && prec.r !== r && !prec.pile });
        dernier = i; continue;
      }
      if (c === "\\" && i + 1 < s.length && "_^\\{}".includes(s[i + 1])) { base += s[i + 1]; i += 2; continue; }
      if (c === "_" || c === "^") {
        const a = argument(s, i + 1, c === "^");
        if (a) {
          if (base) { seg.push({ t: base, r: 0 }); base = ""; }
          const r = c === "_" ? "b" : "h", prec = seg[seg.length - 1];
          seg.push({ t: a[0], r, pile: dernier === i && prec && prec.r && prec.r !== r && !prec.pile });
          i = a[1]; dernier = i; continue;
        }
      }
      base += c; i++;
    }
    if (base) seg.push({ t: base, r: 0 });
    return seg;
  }
  function morceaux(t) {
    const m = []; let cour = "", grec = false;
    const fin = () => { if (cour) m.push({ t: cour, grec }); cour = ""; };
    for (const ch of t) {
      if (ch === "̇") { if (cour) { const d = [...cour].pop(); cour = cour.slice(0, cour.length - d.length); fin(); m.push({ t: d, grec: GREC.test(d), point: true }); } continue; }
      const g = GREC.test(ch);
      if (g !== grec) { fin(); grec = g; }
      cour += ch;
    }
    fin();
    return m;
  }
  const policeTexte = (taille, gras) => (gras ? "600 " : "") + taille + "px " + POLICE_GRAPHE;
  const policeGrec = (taille, gras) => "italic " + (gras ? "700 " : "") + taille + "px " + POLICE_GREC;
  function composer(g, s, o) {
    const T = o.taille || 12, gras = !!o.gras, boites = [];
    let x = 0, debutPile = 0, largPile = 0;
    analyser(String(s)).forEach(sg => {
      const k = sg.r ? 0.77 : 1, dy = sg.r === "b" ? 0.22 * T : sg.r === "h" ? -0.37 * T : 0;
      if (sg.pile) x = debutPile; else debutPile = x;
      let xx = x;
      morceaux(sg.r === "h" ? sg.t.replace(/^-/, "−") : sg.t).forEach(m => {
        const police = m.grec ? policeGrec(T * k, gras) : policeTexte(T * k, gras);
        g.font = police; const w = g.measureText(m.t).width;
        boites.push({ t: m.t, police, x: xx, dy, point: m.point, taille: T * k });
        xx += w;
      });
      if (sg.pile) { const w = xx - x; x = debutPile + Math.max(w, largPile); } else { largPile = xx - x; x = xx; }
    });
    return { boites, larg: x };
  }
  function mesurer(g, s, o = {}) {
    if (!RICHE.test(String(s))) { g.font = policeTexte(o.taille || 12, o.gras); return g.measureText(s).width; }
    g.save(); const l = composer(g, s, o).larg; g.restore(); return l;
  }
  /* écrit s au pixel (x, y) du contexte g : o.taille (12), o.gras, o.align ('left'), o.base ('middle'), o.c, o.rot (degrés) */
  function ecrire(g, x, y, s, o = {}) {
    const T = o.taille || 12, align = o.align || "left", base = o.base || "middle";
    if (o.c) g.fillStyle = couleur(o.c);
    if (!o.rot && !RICHE.test(String(s))) { g.font = policeTexte(T, o.gras); g.textAlign = align; g.textBaseline = base; g.fillText(s, x, y); return; }
    g.save();
    if (o.rot) { g.translate(x, y); g.rotate(o.rot * Math.PI / 180); x = 0; y = 0; }
    g.font = policeTexte(T, o.gras); g.textBaseline = "alphabetic";
    const a0 = g.measureText("H").actualBoundingBoxAscent; g.textBaseline = base;
    let dyB = a0 - g.measureText("H").actualBoundingBoxAscent;
    if (!isFinite(dyB)) dyB = ({ top: 0.8, hanging: 0.6, middle: 0.3, ideographic: -0.2, bottom: -0.2 }[base] || 0) * T;
    const { boites, larg } = composer(g, s, o);
    const x0 = x - (align === "center" ? larg / 2 : align === "right" || align === "end" ? larg : 0), yb = y + dyB;
    g.textAlign = "left"; g.textBaseline = "alphabetic";
    boites.forEach(b => {
      g.font = b.police; g.fillText(b.t, x0 + b.x, yb + b.dy);
      if (b.point) {
        const m = g.measureText(b.t), cx = x0 + b.x + (m.actualBoundingBoxRight - m.actualBoundingBoxLeft) / 2;
        g.font = b.taille + "px " + POLICE_ACCENT; g.textAlign = "center";
        g.fillText("˙", isFinite(cx) ? cx : x0 + b.x + m.width / 2, yb + b.dy); g.textAlign = "left";
      }
    });
    g.restore();
  }

  /* ---------- marqueurs : rond, carre, triangle, triangle-bas, losange, croix, plus, rond-point ; cercle = rond vide ;
     suffixe -vide ; st : c, r (4), vide, fond, w (1,4), alpha ---------- */
  const ALIAS_FORMES = { disque: "rond", cercle: "rond", "cercle-point": "rond-point", carré: "carre" };
  function marque(g, X, Y, forme, st = {}) {
    let f = String(forme || "rond"), vide = !!st.vide;
    if (f.endsWith("-vide")) { vide = true; f = f.slice(0, -5); }
    if (f === "cercle") vide = true;
    f = ALIAS_FORMES[f] || f;
    const r = st.r || 4, c = couleur(st.c || "tirage");
    g.save(); g.strokeStyle = g.fillStyle = c; g.lineWidth = st.w || 1.4; g.setLineDash([]); g.globalAlpha = st.alpha != null ? st.alpha : 1;
    g.beginPath();
    if (f === "carre") g.rect(X - 0.9 * r, Y - 0.9 * r, 1.8 * r, 1.8 * r);
    else if (f === "triangle") { g.moveTo(X, Y - 1.2 * r); g.lineTo(X + 1.05 * r, Y + 0.7 * r); g.lineTo(X - 1.05 * r, Y + 0.7 * r); g.closePath(); }
    else if (f === "triangle-bas") { g.moveTo(X, Y + 1.2 * r); g.lineTo(X + 1.05 * r, Y - 0.7 * r); g.lineTo(X - 1.05 * r, Y - 0.7 * r); g.closePath(); }
    else if (f === "losange") { g.moveTo(X, Y - 1.25 * r); g.lineTo(X + 1.25 * r, Y); g.lineTo(X, Y + 1.25 * r); g.lineTo(X - 1.25 * r, Y); g.closePath(); }
    else if (f === "croix") { g.moveTo(X - r, Y - r); g.lineTo(X + r, Y + r); g.moveTo(X + r, Y - r); g.lineTo(X - r, Y + r); }
    else if (f === "plus") { g.moveTo(X - 1.25 * r, Y); g.lineTo(X + 1.25 * r, Y); g.moveTo(X, Y - 1.25 * r); g.lineTo(X, Y + 1.25 * r); }
    else g.arc(X, Y, r, 0, 2 * Math.PI);
    if (f === "croix" || f === "plus") g.stroke();
    else if (vide || f === "rond-point") { if (st.fond !== false) { g.fillStyle = couleur(st.fond || "papier"); g.fill(); } g.stroke(); }
    else g.fill();
    if (f === "rond-point") { g.fillStyle = c; g.beginPath(); g.arc(X, Y, 1.3, 0, 2 * Math.PI); g.fill(); }
    g.restore();
  }

  class Plot {
    /* o : { x:[min,max], y:[min,max], xlog, ylog, xlabel, ylabel, ratio (hauteur/largeur, 0.6), marge:{g,d,h,b},
             grille (true), zero (true), xinv/yinv, xpas, xticks, xfmt, xlogEtiq, xfin/yfin, xsous/ysous, styleFin,
             styleGrille, y2:[min,max], y2log, y2label, y2inv, y2pas, y2ticks, y2fmt, etroit (560), ratioEtroit }
       Détail des options : jouets.md. */
    constructor(canvas, o = {}) {
      this.c = canvas; this.ctx = canvas.getContext("2d");
      this.o = Object.assign({ x: [0, 1], y: [0, 1], xlog: false, ylog: false, xlabel: "", ylabel: "", ratio: 0.6, grille: true, etroit: 560 }, o);
      this.m = Object.assign({ g: 70, d: o.y2 ? 62 : 16, h: 14, b: 44 }, o.marge || {});
      this._redessin = null; this._ro = null; this._dessus = 0;
    }
    set(o) {
      if (o.y2 && !this.o.y2 && !(o.marge && o.marge.d != null) && this.m.d === 16) this.m.d = 62;
      Object.assign(this.o, o); if (o.marge) Object.assign(this.m, o.marge); return this;
    }
    estEtroit() { return (this.c.clientWidth || 600) < this.o.etroit; }
    _taille() {
      const dpr = window.devicePixelRatio || 1;
      const w = Math.max(240, this.c.clientWidth || this.c.parentNode.clientWidth || 600);
      const h = Math.round(w * (this.o.ratioEtroit && this.estEtroit() ? this.o.ratioEtroit : this.o.ratio));
      if (this.c.width !== Math.round(w * dpr) || this.c.height !== Math.round(h * dpr)) {
        this.c.width = Math.round(w * dpr); this.c.height = Math.round(h * dpr); this.c.style.height = h + "px";
      }
      this.w = w; this.h = h; this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      this.x0 = this.m.g; this.x1 = w - this.m.d; this.y0 = h - this.m.b; this.y1 = this.m.h + this._dessus;
    }
    _tx(v, log) { return log ? Math.log10(v) : v; }
    _ab(axe) { const b = this.o[axe]; return this.o[axe + "inv"] && b[0] < b[1] ? [b[1], b[0]] : b; }
    _lohi(axe) { const b = this.o[axe]; return b[0] <= b[1] ? [b[0], b[1]] : [b[1], b[0]]; }
    X(x) { const [a, b] = this._ab("x"), L = this.o.xlog; return this.x0 + (this._tx(x, L) - this._tx(a, L)) / (this._tx(b, L) - this._tx(a, L)) * (this.x1 - this.x0); }
    Y(y) { const [a, b] = this._ab("y"), L = this.o.ylog; return this.y0 - (this._tx(y, L) - this._tx(a, L)) / (this._tx(b, L) - this._tx(a, L)) * (this.y0 - this.y1); }
    Y2(y) {
      if (!this.o.y2) return this.Y(y);
      const [a, b] = this._ab("y2"), L = this.o.y2log;
      return this.y0 - (this._tx(y, L) - this._tx(a, L)) / (this._tx(b, L) - this._tx(a, L)) * (this.y0 - this.y1);
    }
    _fy(st) { return st && st.y2 ? v => this.Y2(v) : v => this.Y(v); }
    donnees(px, py) {
      const [a, b] = this._ab("x"), [c, d] = this._ab("y"), LX = this.o.xlog, LY = this.o.ylog;
      const x = this._tx(a, LX) + (px - this.x0) / (this.x1 - this.x0) * (this._tx(b, LX) - this._tx(a, LX));
      const y = this._tx(c, LY) + (this.y0 - py) / (this.y0 - this.y1) * (this._tx(d, LY) - this._tx(c, LY));
      const r = { x: LX ? Math.pow(10, x) : x, y: LY ? Math.pow(10, y) : y };
      if (this.o.y2) {
        const [e, f] = this._ab("y2"), L2 = this.o.y2log;
        const z = this._tx(e, L2) + (this.y0 - py) / (this.y0 - this.y1) * (this._tx(f, L2) - this._tx(e, L2));
        r.y2 = L2 ? Math.pow(10, z) : z;
      }
      return r;
    }
    _grad(axe) {
      const o = this.o, [lo, hi] = this._lohi(axe), log = o[axe + "log"], fu = o[axe + "fmt"], liste = o[axe + "ticks"];
      const t = [];
      if (liste) {
        liste.forEach(e => { const v = Array.isArray(e) ? e[0] : e; t.push({ v, maj: true, lab: Array.isArray(e) ? String(e[1]) : fu ? fu(v) : etiquetteLibre(v) }); });
        return { t, pas: 0 };
      }
      if (log) {
        const inter = o[axe + "logEtiq"] || [];
        for (let e = Math.floor(Math.log10(lo)); e <= Math.ceil(Math.log10(hi)); e++)
          for (let k = 1; k < 10; k++) {
            const v = k * Math.pow(10, e);
            if (v >= lo * 0.999 && v <= hi * 1.001) t.push({ v, maj: k === 1, lab: k === 1 ? (fu ? fu(v) : etiquetteLog(e)) : inter.includes(k) ? (fu ? fu(v) : etiquetteLibre(v)) : "" });
          }
        return { t, pas: 0 };
      }
      const cible = axe === "x" ? Math.max(3, Math.round((this.x1 - this.x0) / 85)) : Math.max(3, Math.round((this.y0 - this.y1) / 55));
      const { t: vs, pas } = o[axe + "pas"] ? ticksPas(lo, hi, o[axe + "pas"]) : ticksLin(lo, hi, cible);
      const sci = estSci(lo, hi);
      vs.forEach(v => t.push({ v, maj: true, lab: fu ? fu(v) : etiquette(v, pas, sci) }));
      return { t, pas };
    }
    _grilleFine(axe, gr) {
      const o = this.o, [lo, hi] = this._lohi(axe), r = [], vs = gr.t.map(t => t.v).sort((a, b) => a - b);
      const libre = (v, tol) => !vs.some(t => Math.abs(v - t) < tol);
      if (o[axe + "fin"]) {
        const h = o[axe + "fin"];
        for (let k = Math.ceil(lo / h - 1e-9); k * h <= hi + h * 1e-9; k++) { const v = k * h; if (libre(v, h * 1e-6)) r.push(v); }
      } else if (o[axe + "sous"] > 1) {
        const n = o[axe + "sous"];
        if (!o[axe + "log"] && gr.pas) {
          const h = gr.pas / n;
          for (let k = Math.ceil(lo / h - 1e-9); k * h <= hi + h * 1e-9; k++) { const v = k * h; if (libre(v, h * 1e-6)) r.push(v); }
        } else for (let i = 0; i + 1 < vs.length; i++) {
          const a = vs[i], b = vs[i + 1];
          for (let j = 1; j < n; j++) r.push(a + (b - a) * j / n);
        }
      }
      return r;
    }
    clear() {
      this._taille();
      const g = this.ctx, o = this.o;
      g.clearRect(0, 0, this.w, this.h);
      g.fillStyle = couleur("papier"); g.fillRect(0, 0, this.w, this.h);
      g.font = "12px " + POLICE_GRAPHE; g.lineWidth = 1;
      const traitAxe = couleur("doux");
      const gx = this._grad("x"), gy = this._grad("y");
      const sg = Object.assign({ c: "grille", w: 1, alpha: 1 }, o.styleGrille);
      const sf = Object.assign({ c: "grille", w: 1, alpha: 0.5, lignes: true, dedans: 0 }, o.styleFin);
      const AXE = { c: "doux", w: 1, alpha: 1 };
      const ligne = (s, xa, ya, xb, yb) => {
        g.save(); g.strokeStyle = couleur(s.c); g.lineWidth = s.w; g.globalAlpha = s.alpha; g.setLineDash(s.dash || []);
        g.beginPath(); g.moveTo(xa, ya); g.lineTo(xb, yb); g.stroke(); g.restore();
      };
      const finX = this._grilleFine("x", gx).map(v => ({ v, lig: true })).concat(gx.t.filter(t => !t.maj).map(t => ({ v: t.v, lig: o.grille })));
      const finY = this._grilleFine("y", gy).map(v => ({ v, lig: true })).concat(gy.t.filter(t => !t.maj).map(t => ({ v: t.v, lig: o.grille })));
      finX.forEach(f => { const X = this.X(f.v); if (f.lig && sf.lignes) ligne(sf, X, this.y0, X, this.y1); });
      finY.forEach(f => { const Y = this.Y(f.v); if (f.lig && sf.lignes) ligne(sf, this.x0, Y, this.x1, Y); });
      if (o.grille) {
        gx.t.forEach(t => { if (t.maj) { const X = this.X(t.v); ligne(sg, X, this.y0, X, this.y1); } });
        gy.t.forEach(t => { if (t.maj) { const Y = this.Y(t.v); ligne(sg, this.x0, Y, this.x1, Y); } });
      }
      const d = sf.dedans;
      finX.forEach(f => { const X = this.X(f.v); if (d) { ligne(AXE, X, this.y0, X, this.y0 - d); ligne(AXE, X, this.y1, X, this.y1 + d); } else ligne(AXE, X, this.y0, X, this.y0 + 3); });
      finY.forEach(f => { const Y = this.Y(f.v); if (d) { ligne(AXE, this.x0, Y, this.x0 + d, Y); ligne(AXE, this.x1, Y, this.x1 - d, Y); } else ligne(AXE, this.x0, Y, this.x0 - 3, Y); });
      g.strokeStyle = traitAxe; g.lineWidth = 1;
      for (const t of gx.t) {
        const X = this.X(t.v);
        if (t.maj) { g.beginPath(); g.moveTo(X, this.y0); g.lineTo(X, this.y0 + 5); g.stroke(); }
        if (t.lab) { g.fillStyle = traitAxe; ecrire(g, X, this.y0 + 7, t.lab, { align: "center", base: "top" }); }
      }
      for (const t of gy.t) {
        const Y = this.Y(t.v);
        if (t.maj) { g.beginPath(); g.moveTo(this.x0, Y); g.lineTo(this.x0 - 5, Y); g.stroke(); }
        if (t.lab) { g.fillStyle = traitAxe; ecrire(g, this.x0 - 7, Y, t.lab, { align: "right", base: "middle" }); }
      }
      if (o.y2) {
        for (const t of this._grad("y2").t) {
          const Y = this.Y2(t.v);
          g.strokeStyle = traitAxe; g.beginPath(); g.moveTo(this.x1, Y); g.lineTo(this.x1 + (t.maj ? 5 : 3), Y); g.stroke();
          if (t.lab) { g.fillStyle = traitAxe; ecrire(g, this.x1 + 7, Y, t.lab, { align: "left", base: "middle" }); }
        }
      }
      g.strokeStyle = traitAxe;
      const [ya, yb] = this._lohi("y");
      if (o.zero !== false && !o.ylog && ya < 0 && yb > 0) { g.globalAlpha = 0.6; g.beginPath(); g.moveTo(this.x0, this.Y(0)); g.lineTo(this.x1, this.Y(0)); g.stroke(); g.globalAlpha = 1; }
      g.strokeRect(this.x0, this.y1, this.x1 - this.x0, this.y0 - this.y1);
      g.fillStyle = couleur("encre"); g.font = "13px " + POLICE_GRAPHE;
      if (o.xlabel) ecrire(g, (this.x0 + this.x1) / 2, this.h - 4, o.xlabel, { align: "center", base: "bottom", taille: 13 });
      if (o.ylabel) { g.save(); g.translate(11, (this.y0 + this.y1) / 2); g.rotate(-Math.PI / 2); ecrire(g, 0, 0, o.ylabel, { align: "center", base: "middle", taille: 13 }); g.restore(); }
      if (o.y2 && o.y2label) { g.save(); g.translate(this.w - 11, (this.y0 + this.y1) / 2); g.rotate(-Math.PI / 2); ecrire(g, 0, 0, o.y2label, { align: "center", base: "middle", taille: 13 }); g.restore(); }
      return this;
    }
    _style(st = {}) {
      const g = this.ctx; g.strokeStyle = g.fillStyle = couleur(st.c || "tirage");
      g.lineWidth = st.w != null ? st.w : 2; g.setLineDash(st.dash || []); g.globalAlpha = st.alpha != null ? st.alpha : 1;
    }
    _clip() { const g = this.ctx; g.save(); g.beginPath(); g.rect(this.x0, this.y1, this.x1 - this.x0, this.y0 - this.y1); g.clip(); }
    _fin() { const g = this.ctx; g.restore(); g.setLineDash([]); g.globalAlpha = 1; }
    _ok(x, y, y2) { return isFinite(x) && isFinite(y) && !(this.o.xlog && x <= 0) && !((y2 && this.o.y2 ? this.o.y2log : this.o.ylog) && y <= 0); }
    line(xs, ys, st) {
      const g = this.ctx, FY = this._fy(st), y2 = st && st.y2; this._clip(); this._style(st); g.beginPath(); let lev = true;
      for (let i = 0; i < xs.length; i++) {
        if (!this._ok(xs[i], ys[i], y2)) { lev = true; continue; }
        const X = this.X(xs[i]), Y = Math.max(-1e4, Math.min(1e4, FY(ys[i])));
        if (lev) { g.moveTo(X, Y); lev = false; } else g.lineTo(X, Y);
      }
      g.stroke(); this._fin(); return this;
    }
    trace(pts, st) { return this.line(pts.map(q => q[0]), pts.map(q => q[1]), st); }
    lisse(pts, st = {}) {
      const LX = this.o.xlog, LY = st.y2 ? this.o.y2log : this.o.ylog;
      const [X, Y] = lisse(pts.map(([x, y]) => [LX ? Math.log10(x) : x, LY ? Math.log10(y) : y]), st.k);
      return this.line(LX ? X.map(v => Math.pow(10, v)) : X, LY ? Y.map(v => Math.pow(10, v)) : Y, st);
    }
    fn(f, st = {}, n = 400) {
      const [a, b] = st.dom || this.o.x;
      const xs = this.o.xlog ? num.logspace(a, b, n) : num.linspace(a, b, n);
      return this.line(xs, xs.map(f), st);
    }
    points(xs, ys, st = {}) {
      const g = this.ctx; this._clip(); this._style(st); const r = st.r || 3.5;
      if (st.forme) {
        const FY = this._fy(st);
        for (let i = 0; i < xs.length; i++) if (this._ok(xs[i], ys[i], st.y2)) marque(g, this.X(xs[i]), FY(ys[i]), st.forme, Object.assign({}, st, { r }));
        this._fin(); return this;
      }
      for (let i = 0; i < xs.length; i++) {
        if (!this._ok(xs[i], ys[i])) continue;
        g.beginPath(); g.arc(this.X(xs[i]), this.Y(ys[i]), r, 0, 2 * Math.PI);
        if (st.vide) { g.lineWidth = 1.5; g.stroke(); } else g.fill();
      }
      this._fin(); return this;
    }
    serie(pts, st = {}) {
      const FY = this._fy(st);
      pts.forEach(([x, y]) => {
        if (!this._ok(x, y, st.y2)) return;
        const X = this.X(x), Y = FY(y);
        if (X >= this.x0 - 1 && X <= this.x1 + 1 && Y >= this.y1 - 1 && Y <= this.y0 + 1) marque(this.ctx, X, Y, st.forme, st);
      });
      return this;
    }
    seg(x1, y1, x2, y2, st) { const g = this.ctx, FY = this._fy(st); this._clip(); this._style(st); g.beginPath(); g.moveTo(this.X(x1), FY(y1)); g.lineTo(this.X(x2), FY(y2)); g.stroke(); this._fin(); return this; }
    hline(y, st = {}) { return this.seg(this.o.x[0], y, this.o.x[1], y, Object.assign({ w: 1, dash: [5, 4] }, st)); }
    vline(x, st = {}) { return this.seg(x, this.o.y[0], x, this.o.y[1], Object.assign({ w: 1, dash: [5, 4] }, st, { y2: false })); }
    fleche(x1, y1, x2, y2, st = {}) {
      const g = this.ctx, FY = this._fy(st), X1 = this.X(x1), Y1 = FY(y1), X2 = this.X(x2), Y2 = FY(y2), a = Math.atan2(Y2 - Y1, X2 - X1), L = st.pointe || 8;
      const pointe = (X, Y, b) => { g.beginPath(); g.moveTo(X, Y); g.lineTo(X - L * Math.cos(b - 0.35), Y - L * Math.sin(b - 0.35)); g.lineTo(X - L * Math.cos(b + 0.35), Y - L * Math.sin(b + 0.35)); g.closePath(); g.fill(); };
      g.save(); g.strokeStyle = g.fillStyle = couleur(st.c); g.lineWidth = st.w || 1.1; g.setLineDash(st.dash || []); g.globalAlpha = st.alpha != null ? st.alpha : 1;
      g.beginPath(); g.moveTo(X1, Y1); g.lineTo(X2, Y2); g.stroke(); g.setLineDash([]);
      pointe(X2, Y2, a); if (st.double) pointe(X1, Y1, a + Math.PI);
      g.restore(); return this;
    }
    angle(x1, y1, x2, y2, st) { const FY = this._fy(st); return Math.atan2(FY(y2) - FY(y1), this.X(x2) - this.X(x1)) * 180 / Math.PI; }
    band(xs, ys1, ys2, st = {}) {
      const g = this.ctx, FY = this._fy(st); this._clip(); this._style(Object.assign({ alpha: 0.18 }, st)); g.beginPath();
      const y2 = i => (typeof ys2 === "number" ? ys2 : ys2[i]);
      xs.forEach((x, i) => { const X = this.X(x), Y = FY(ys1[i]); i ? g.lineTo(X, Y) : g.moveTo(X, Y); });
      for (let i = xs.length - 1; i >= 0; i--) g.lineTo(this.X(xs[i]), FY(y2(i)));
      g.closePath(); g.fill(); this._fin(); return this;
    }
    rect(xa, ya, xb, yb, st = {}) { const g = this.ctx, FY = this._fy(st); this._clip(); this._style(Object.assign({ alpha: 0.15 }, st)); g.fillRect(this.X(xa), FY(yb), this.X(xb) - this.X(xa), FY(ya) - FY(yb)); this._fin(); return this; }
    text(x, y, s, st = {}) {
      const g = this.ctx; g.save(); g.fillStyle = couleur(st.c);
      ecrire(g, this.X(x) + (st.dx || 0), this._fy(st)(y) + (st.dy || 0), s, { taille: st.taille || 12, gras: st.gras, align: st.align || "left", base: st.base || "middle", rot: st.rot });
      g.restore(); return this;
    }
    /* légende : items [{ t, c, dash, w, point | forme | formes | ligne, vide, r }] ; pos 'hd' | 'hg' | 'bd' | 'bg' |
       'dessus' | [x, y] (opt.ancre) ; opt : { etroit, cadre, taille } */
    legend(items, pos = "hd", opt = {}) {
      const g = this.ctx;
      if (typeof pos === "string" && pos !== "dessus" && !opt.etroit && !items.some(i => i.forme || i.formes || i.ligne)) {
        g.save(); g.font = "12px " + POLICE_GRAPHE;
        const lh = 17, lw = Math.max(...items.map(i => mesurer(g, i.t))) + 34, hgt = items.length * lh + 8;
        const x = pos.includes("g") ? this.x0 + 8 : this.x1 - lw - 8, y = pos.includes("b") ? this.y0 - hgt - 8 : this.y1 + 8;
        g.fillStyle = couleur("papier"); g.globalAlpha = 0.88; g.fillRect(x, y, lw, hgt); g.globalAlpha = 1;
        g.strokeStyle = couleur("trait"); g.lineWidth = 1; g.strokeRect(x, y, lw, hgt);
        items.forEach((it, k) => {
          const yy = y + 4 + lh * k + lh / 2;
          g.strokeStyle = g.fillStyle = couleur(it.c || "tirage"); g.lineWidth = it.w || 2; g.setLineDash(it.dash || []);
          if (it.point) { g.beginPath(); g.arc(x + 15, yy, 3.5, 0, 2 * Math.PI); g.fill(); }
          else { g.beginPath(); g.moveTo(x + 6, yy); g.lineTo(x + 24, yy); g.stroke(); }
          g.setLineDash([]); g.fillStyle = couleur("encre"); ecrire(g, x + 30, yy, it.t, { align: "left", base: "middle" });
        });
        g.restore(); return this;
      }
      const T = opt.taille || 12, lh = Math.round(1.5 * T);
      const formes = it => it.formes || (it.forme ? [it.forme] : it.point ? ["rond"] : []);
      const nmax = Math.max(1, ...items.map(it => (it.ligne ? 1 : formes(it).length)));
      const tx = Math.max(46, 30 + 16 * (nmax - 1));
      g.save();
      const larg = Math.max(...items.map(i => mesurer(g, i.t, { taille: T }))) + tx + 6, haut = items.length * lh + 8;
      if (opt.etroit && this.estEtroit()) pos = "dessus";
      let x, y;
      if (pos === "dessus") { x = Math.max(4, Math.min(this.x0, this.w - larg - 4)); y = 4; this._besoin = Math.max(this._besoin || 0, haut + 6); }
      else if (Array.isArray(pos)) {
        const an = opt.ancre || "hg";
        x = this.X(pos[0]) - (an.includes("d") ? larg : 0); y = this.Y(pos[1]) - (an.includes("b") ? haut : 0);
      } else { x = pos.includes("g") ? this.x0 + 8 : this.x1 - larg - 8; y = pos.includes("b") ? this.y0 - haut - 8 : this.y1 + 8; }
      if (opt.cadre !== false) {
        g.fillStyle = couleur("papier"); g.globalAlpha = 0.9; g.fillRect(x, y, larg, haut); g.globalAlpha = 1;
        g.strokeStyle = couleur("trait"); g.lineWidth = 1; g.strokeRect(x, y, larg, haut);
      }
      items.forEach((it, k) => {
        const yy = y + 4 + lh * k + lh / 2, fs = formes(it);
        if (it.ligne || !fs.length) { g.save(); g.strokeStyle = couleur(it.c || "tirage"); g.lineWidth = it.w || 1.8; g.setLineDash(it.dash || []); g.beginPath(); g.moveTo(x + 6, yy); g.lineTo(x + 38, yy); g.stroke(); g.restore(); }
        if (it.ligne && fs.length) marque(g, x + 22, yy, fs[0], { c: it.c, r: it.r || 4, vide: it.vide, fond: it.fond });
        else fs.forEach((f, j) => marque(g, x + 13 + 16 * j, yy, f, { c: it.c, r: it.r || 4, vide: it.vide, fond: it.fond }));
        g.fillStyle = couleur("encre"); ecrire(g, x + tx, yy, it.t, { align: "left", base: "middle", taille: T });
      });
      g.restore(); return this;
    }
    /* redessine quand la largeur change ou que le thème bascule ; une légende 'dessus' fait refaire le dessin une fois */
    auto(dessin) {
      this._redessin = () => {
        this._besoin = 0; dessin();
        if (this._besoin !== this._dessus) { this._dessus = this._besoin; this._besoin = 0; dessin(); }
      };
      this._redessin();
      if (!this._ro && window.ResizeObserver) { let l = this.c.clientWidth; this._ro = new ResizeObserver(() => { if (this.c.clientWidth !== l) { l = this.c.clientWidth; this._redessin && this._redessin(); } }); this._ro.observe(this.c); }
      Plot._tous.add(this); return this;
    }
    /* interaction : cb({ x, y, y2, px, py, type: 'down' | 'move' | 'up', bas }) à la souris et au doigt */
    pointeur(cb) {
      let bas = false;
      const ev = (e, type) => { const r = this.c.getBoundingClientRect(); const px = e.clientX - r.left, py = e.clientY - r.top; const d = this.donnees(px, py); cb({ x: d.x, y: d.y, y2: d.y2, px, py, type, bas }); };
      this.c.style.touchAction = "none";
      this.c.addEventListener("pointerdown", e => { bas = true; this.c.setPointerCapture(e.pointerId); ev(e, "down"); });
      this.c.addEventListener("pointermove", e => ev(e, "move"));
      this.c.addEventListener("pointerup", e => { bas = false; ev(e, "up"); });
      return this;
    }
  }
  Plot._tous = new Set();
  function redessinerTout() { cache.clear(); Plot._tous.forEach(p => p._redessin && p._redessin()); }

  /* courbe de Catmull-Rom passant par [[x, y]…] : [X, Y], k sous-segments par intervalle */
  function lisse(pts, k = 12) {
    const X = [], Y = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const a = pts[Math.max(0, i - 1)], b = pts[i], c = pts[i + 1], d = pts[Math.min(pts.length - 1, i + 2)];
      for (let j = 0; j < k; j++) {
        const t = j / k, t2 = t * t, t3 = t2 * t;
        const f = (p0, p1, p2, p3) => 0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (3 * p1 - p0 - 3 * p2 + p3) * t3);
        X.push(f(a[0], b[0], c[0], d[0])); Y.push(f(a[1], b[1], c[1], d[1]));
      }
    }
    const z = pts[pts.length - 1]; X.push(z[0]); Y.push(z[1]);
    return [X, Y];
  }
  const ecrirePx = (g, x, y, s, o) => { g.save(); ecrire(g, x, y, s, o); g.restore(); };
  const mesurerPx = (g, s, o) => { g.save(); const l = mesurer(g, s, o); g.restore(); return l; };

  /* ---------- dessins au pixel : ligne brisée, triangle de composition, planche de panneaux ---------- */
  function trait(g, pts, st = {}) {
    if (pts.length < 2) return;
    g.save(); g.strokeStyle = couleur(st.c || "encre"); g.lineWidth = st.w || 1.5; g.setLineDash(st.dash || []);
    g.globalAlpha = st.alpha == null ? 1 : st.alpha; g.lineJoin = "round";
    g.beginPath(); pts.forEach((q, i) => (i ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1]))); if (st.ferme) g.closePath();
    if (st.remplir) { g.fillStyle = couleur(st.remplir); g.globalAlpha = st.alphaR || 0.15; g.fill(); g.globalAlpha = st.alpha == null ? 1 : st.alpha; }
    g.stroke(); g.restore();
  }
  const S3 = Math.sqrt(3) / 2;
  function triangle(g, bx, by, bw, bh, o = {}) {
    const mh = o.mh == null ? 18 : o.mh, mb = o.mb == null ? 18 : o.mb, mx = o.mx == null ? 12 : o.mx;
    const L = Math.max(10, Math.min(bw - 2 * mx, (bh - mh - mb) / S3));
    const x0 = bx + (bw - L) / 2, y0 = by + mh + (bh - mh - mb - L * S3) / 2;
    const P = (wh, wg, wd) => [x0 + L * (0.5 * wh + wd), y0 + L * S3 * (1 - wh)];
    if (o.pas) for (let k = 1; k * o.pas < 1 - 1e-9; k++) {
      const t = k * o.pas, st = { c: "grille", w: 1 };
      trait(g, [P(t, 1 - t, 0), P(t, 0, 1 - t)], st);
      trait(g, [P(0, t, 1 - t), P(1 - t, t, 0)], st);
      trait(g, [P(0, 1 - t, t), P(1 - t, 0, t)], st);
    }
    trait(g, [P(1, 0, 0), P(0, 1, 0), P(0, 0, 1)], { c: "encre", w: 1.2, ferme: true });
    const tn = o.tn || 11;
    if (o.noms) {
      const [nh, ng, nd] = o.noms, H = P(1, 0, 0), G = P(0, 1, 0), D = P(0, 0, 1);
      if (nh) ecrirePx(g, H[0], H[1] - 4, nh, { base: "bottom", taille: tn, align: "center", c: "encre" });
      const db = o.grad ? 17 : 4;
      if (ng) ecrirePx(g, G[0] - 4, G[1] + db, ng, { base: "top", align: "left", taille: tn, c: "encre" });
      if (nd) ecrirePx(g, D[0] + 4, D[1] + db, nd, { base: "top", align: "right", taille: tn, c: "encre" });
    }
    if (o.grad) {
      const tg = o.tg || 9;
      for (let k = 1; k * o.grad < 1 - 1e-9; k++) {
        const t = k * o.grad, s = o.pct ? String(Math.round(100 * t)) : fmt(t, 1);
        const b = P(0, 1 - t, t); ecrirePx(g, b[0], b[1] + 3, s, { base: "top", taille: tg, c: "doux", align: "center" });
        const d = P(t, 0, 1 - t); ecrirePx(g, d[0] + 4, d[1], s, { align: "left", taille: tg, c: "doux" });
        const l = P(1 - t, t, 0); ecrirePx(g, l[0] - 4, l[1], s, { align: "right", taille: tg, c: "doux" });
      }
    }
    return { P, L, x0, y0 };
  }
  function planche(cible, n, dessin, o = {}) {
    const c = typeof cible === "string" ? document.getElementById(cible) : cible;
    if (!c) return null;
    const p = new Plot(c, { ratio: 1, marge: { g: 0, d: 0, h: 0, b: 0 }, grille: false });
    p.auto(() => {
      const W = c.clientWidth || c.parentNode.clientWidth || 600;
      const cols = Math.max(1, Math.min(o.max || n, Math.floor(W / (o.min || 150))));
      const rows = Math.ceil(n / cols), cw = W / cols, ch = cw * (o.h || 1);
      p.o.ratio = rows * ch / W; p._taille();
      const g = p.ctx; g.fillStyle = couleur("papier"); g.fillRect(0, 0, p.w, p.h);
      for (let k = 0; k < n; k++) dessin(g, k, (k % cols) * cw, Math.floor(k / cols) * ch, cw, ch);
    });
    return p;
  }

  /* ---------- curseurs ----------
     Dans racine : <input type="range" data-k="chi" min max step value [data-log] [data-fmt="3"|"e2"|"s3"] [data-unite]>,
     l'<output> du même <label> affiche la valeur ; aussi <select data-k> et <input type="checkbox" data-k>.
     cb(etat) est appelé au départ et à chaque changement (une fois par image). */
  function sliders(base, cb) {
    const champs = [...base.querySelectorAll("[data-k]")];
    const etat = {};
    const lire = () => {
      for (const c of champs) {
        const k = c.dataset.k;
        if (c.type === "checkbox") etat[k] = c.checked;
        else if (c.tagName === "SELECT") etat[k] = isNaN(+c.value) ? c.value : +c.value;
        else {
          let v = +c.value; if (c.dataset.log != null) v = Math.pow(10, v); etat[k] = v;
          const out = c.closest("label") && c.closest("label").querySelector("output");
          if (out) {
            const f = c.dataset.fmt || "2";
            out.textContent = f[0] === "e" ? fmtE(v, +f.slice(1) || 2) : f[0] === "s" ? fmtS(v, +f.slice(1) || 3) : fmt(v, +f);
            if (c.dataset.unite) out.textContent += " " + c.dataset.unite;
          }
        }
      }
      return etat;
    };
    let enAttente = false;
    const maj = () => { if (enAttente) return; enAttente = true; requestAnimationFrame(() => { enAttente = false; cb(lire()); }); };
    champs.forEach(c => { c.addEventListener("input", maj); c.addEventListener("change", maj); });
    cb(lire());
    return { etat, maj, lire };
  }

  /* ---------- démarrage : fonctions en attente, une fois les polices des canevas chargées (1 s au plus) ---------- */
  const prets = attente.slice();
  let demarre = false, erreurs = 0;
  const lancer = fn => { try { fn(); } catch (e) { erreurs++; racine.dataset.coursErreurs = erreurs; console.error(e); } };
  function pret(fn) { if (demarre) lancer(fn); else prets.push(fn); }
  const POLICES_CANEVAS = ['12px "TX Sans"', '600 12px "TX Sans"', "italic 12px KaTeX_Math", "12px KaTeX_Main"];
  function polices() {
    if (!document.fonts || !document.fonts.load) return { pretes: Promise.resolve(true), toutes: Promise.resolve() };
    const toutes = Promise.all(POLICES_CANEVAS.map(f => document.fonts.load(f))).catch(() => {});
    return { pretes: Promise.race([toutes.then(() => true), new Promise(r => setTimeout(() => r(false), 1000))]), toutes };
  }
  function demarrer() {
    const p = polices();
    p.pretes.then(aTemps => {
      demarre = true; window.Cours.demarre = true;
      prets.splice(0).forEach(lancer);
      racine.dataset.coursPret = "1";
      document.dispatchEvent(new CustomEvent("cours:pret"));
      if (!aTemps) p.toutes.then(redessinerTout);
    });
  }
  /* thème : la page (textured.js ou atelier.js) annonce « tx-theme » ; le système peut aussi basculer */
  addEventListener("tx-theme", redessinerTout);
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", redessinerTout);
  /* papier : toujours en clair (la feuille d'impression aussi), puis retour au thème choisi */
  let themeAvant = null;
  addEventListener("beforeprint", () => { themeAvant = racine.dataset.theme || ""; racine.dataset.theme = "light"; redessinerTout(); });
  addEventListener("afterprint", () => { if (themeAvant === null) return; if (themeAvant) racine.dataset.theme = themeAvant; else delete racine.dataset.theme; themeAvant = null; redessinerTout(); });

  window.Cours = { Plot, sliders, tex, renderMath, ecrireTexte, fmt, fmtS, fmtE, num, couleur, pret, store, redessiner: redessinerTout,
    marque, ecrire: ecrirePx, mesurer: mesurerPx, trait, triangle, planche, lisse, POLICE_GRAPHE, demarre: false };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", demarrer); else demarrer();
})();

/*@ boucle | Cours\.(boucle|criteres) */
/* Simulation d'une boucle de régulation (cours de régulation) : Cours.boucle(options), Cours.criteres(r, { bande }).
   Procédé G·e^(−tau·s)/(theta·s + 1) ou G·e^(−tau·s)/(a2·s² + a1·s + a0) (den), PID parallèle ou tout ou rien, pas
   fixe h, bloqueur d'ordre zéro, retard pur par tampon, saturation, anti-emballement, bruit de mesure. Options : jouets.md. */
(() => {
  const num = window.Cours.num;
  function expm(M) {
    const n = M.length, mul = (A, B) => A.map((r, i) => B[0].map((_, j) => r.reduce((s, _v, k) => s + A[i][k] * B[k][j], 0)));
    let nrm = 0; M.forEach(r => r.forEach(v => { nrm = Math.max(nrm, Math.abs(v)); }));
    let sq = 0; while (nrm * n > 0.5) { nrm /= 2; sq++; }
    const A = M.map(r => r.map(v => v / Math.pow(2, sq)));
    let E = A.map((r, i) => r.map((_, j) => (i === j ? 1 : 0))), T = E.map(r => r.slice());
    for (let k = 1; k <= 20; k++) { T = mul(T, A).map(r => r.map(v => v / k)); E = E.map((r, i) => r.map((v, j) => v + T[i][j])); }
    for (let k = 0; k < sq; k++) E = mul(E, E);
    return E;
  }
  function boucle(o = {}) {
    const h = o.h ?? 0.1, tFin = o.tFin ?? 60, G = o.G ?? 5, theta = o.theta ?? 10, tau = o.tau ?? 2;
    const Kp = o.Kp ?? 1, Ki = o.Ki ?? 0, Kd = o.Kd ?? 0, ferme = o.ferme ?? true, base = o.base ?? 0;
    const umin = o.umin ?? -Infinity, umax = o.umax ?? Infinity, m = Math.max(1, Math.round((o.Te ?? h) / h)), Te = m * h;
    const tSaut = o.tSaut ?? 1, spAv = o.spAvant ?? 0, spAp = o.spApres ?? 1;
    const spf = typeof o.sp === "function" ? o.sp : typeof o.sp === "number" ? () => o.sp : t => (t >= tSaut - 1e-12 ? spAp : spAv);
    let A, B, C;
    if (o.den) { const [a2, a1, a0] = o.den; A = [[0, 1], [-a0 / a2, -a1 / a2]]; B = [0, G / a2]; C = [1, 0]; }
    else { A = [[-1 / theta]]; B = [G / theta]; C = [1]; }
    const nx = A.length, Mb = [];
    for (let i = 0; i <= nx; i++) { Mb.push([]); for (let j = 0; j <= nx; j++) Mb[i].push(i < nx ? (j < nx ? A[i][j] : B[i]) * h : 0); }
    const Ex = expm(Mb), Ad = Ex.slice(0, nx).map(r => r.slice(0, nx)), Bd = Ex.slice(0, nx).map(r => r[nx]);
    const n = Math.round(tFin / h) + 1, nd = Math.round(tau / h), rand = num.rng(o.graine ?? 1), bruit = o.bruit ?? 0;
    const tor = o.toutOuRien ? Object.assign({ haut: 1, bas: 0, hyst: 0 }, o.toutOuRien) : null;
    const r = { t: [], sp: [], pv: [], mes: [], e: [], u: [] }, y = [];
    let x = new Array(nx).fill(0), integ = 0, ePrec = 0, u = tor ? tor.bas : 0, premier = true;
    for (let k = 0; k < n; k++) {
      const t = k * h, sp = spf(t);
      y[k] = C.reduce((s, c, i) => s + c * x[i], 0);
      const pv = base + (k - nd >= 0 ? y[k - nd] : 0);
      const mes = bruit ? pv + bruit * num.gauss(rand) : pv;
      const e = sp - mes;
      if (k % m === 0) {
        if (!ferme) u = Kp * sp;
        else if (tor) { if (mes < sp - tor.hyst / 2) u = tor.haut; else if (mes > sp + tor.hyst / 2) u = tor.bas; }
        else {
          const sig = (o.derivee ?? "erreur") === "mesure" ? -mes : e;
          const de = premier ? 0 : (sig - ePrec) / Te; ePrec = sig; premier = false;
          let iNew = integ + e * Te;
          const brut = Kp * e + Ki * iNew + Kd * de;
          if (o.antiWindup && ((brut > umax && e > 0) || (brut < umin && e < 0))) iNew = integ;
          integ = iNew;
          u = Math.min(umax, Math.max(umin, Kp * e + Ki * integ + Kd * de));
        }
      }
      r.t.push(t); r.sp.push(sp); r.pv.push(pv); r.mes.push(mes); r.e.push(e); r.u.push(u);
      const d = o.perturbation ? o.perturbation(t) : 0;
      x = Ad.map((row, i) => row.reduce((s, a, j) => s + a * x[j], 0) + Bd[i] * (u + d));
    }
    return r;
  }
  function criteres(r, opt = {}) {
    const bande = opt.bande ?? 0.05, pv = r.pv, t = r.t, n = pv.length, v0 = pv[0], vf = pv[n - 1], dv = vf - v0;
    const spf = r.sp[n - 1], res = { valeurFinale: vf, erreurStatique: spf - vf, depassement: 0, depassementRel: 0, tMontee: null, tEtab: null, max: Math.max(...pv) };
    if (!isFinite(vf) || Math.abs(dv) < 1e-12) return res;
    const s = Math.sign(dv), ext = s > 0 ? Math.max(...pv) : Math.min(...pv);
    res.depassement = Math.max(0, s * (ext - vf)); res.depassementRel = res.depassement / Math.abs(dv);
    const at = f => { for (let k = 0; k < n; k++) if (s * (pv[k] - (v0 + f * dv)) >= 0) return t[k]; return null; };
    const t10 = at(0.1), t90 = at(0.9); res.tMontee = t10 != null && t90 != null ? t90 - t10 : null;
    let der = -1; for (let k = 0; k < n; k++) if (Math.abs(pv[k] - vf) > bande * Math.abs(dv)) der = k;
    res.tEtab = der + 1 < n ? t[der + 1] : null;
    return res;
  }
  Object.assign(window.Cours, { boucle, criteres, expm });
})();

/*@ qcm | class="(qcm|qnum)\b */
/* QCM et questions numériques des cours : propositions mélangées à chaque affichage (sauf data-ordre="fixe", ou une
   explication qui cite une proposition par son numéro), plusieurs bonnes réponses possibles (data-bonne="1,3"),
   bouton « Recommencer » ; question numérique : tolérance relative data-tol (3 %), unité data-unite, « Voir la réponse ». */
(() => {
  const EN = (document.documentElement.lang || "fr").slice(0, 2) === "en";
  const T = EN
    ? { rec: "↺ Start again", tRec: "Clear the answer and shuffle the options", eff: "↺ Clear", tEff: "Clear the answer and hide the explanation",
        rep: "Your answer", ver: "Check", voir: "Show the answer", nombre: "a number is expected", juste: "correct", faux: "not yet", j: " — correct", f: " — wrong" }
    : { rec: "↺ Recommencer", tRec: "Effacer la réponse et mélanger à nouveau les propositions", eff: "↺ Effacer", tEff: "Effacer la réponse et cacher l’explication",
        rep: "Votre réponse", ver: "Vérifier", voir: "Voir la réponse", nombre: "nombre attendu", juste: "juste", faux: "pas encore", j: " — juste", f: " — faux" };
  const bouton = (texte, classe, titre) => { const b = document.createElement("button"); b.type = "button"; b.className = classe; b.textContent = texte; if (titre) b.title = titre; return b; };
  document.querySelectorAll(".qcm").forEach(q => {
    const bonnes = String(q.dataset.bonne || "").split(",").map(s => +s.trim());
    const items = [...q.querySelectorAll(":scope > ol > li")];
    if (!items.length) return;
    const ol = items[0].parentNode, justes = new Set(bonnes.map(b => items[b - 1]).filter(Boolean));
    const expl = q.querySelector(".explication");
    if (expl) expl.setAttribute("aria-live", "polite");
    const melangeable = q.dataset.ordre !== "fixe" && !(expl && /(réponse|proposition|answer|option)s?\s+(\d|[a-d]\b)/i.test(expl.textContent)) && items.length > 1;
    const melanger = () => {
      if (!melangeable) return;
      const ordre = items.slice();
      for (let i = ordre.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [ordre[i], ordre[j]] = [ordre[j], ordre[i]]; }
      ordre.forEach(li => ol.appendChild(li));
    };
    melanger();
    items.forEach(li => {
      const b = document.createElement("button"); b.type = "button";
      while (li.firstChild) b.appendChild(li.firstChild);
      li.appendChild(b);
      b.addEventListener("click", () => {
        const juste = justes.has(li);
        b.classList.add(juste ? "juste" : "faux");
        b.setAttribute("aria-label", b.textContent + (juste ? T.j : T.f));
        if (juste || q.dataset.montrer !== "non") justes.forEach(l2 => l2.firstChild.classList.add("juste"));
        q.classList.add("repondu");
      });
    });
    const r = bouton(T.rec, "reinit discret", T.tRec);
    q.insertBefore(r, q.firstChild);
    q._reinit = () => {
      q.classList.remove("repondu");
      items.forEach(li => { li.firstChild.classList.remove("juste", "faux"); li.firstChild.removeAttribute("aria-label"); });
      melanger();
    };
    r.addEventListener("click", q._reinit);
  });
  document.querySelectorAll(".qnum").forEach(q => {
    const rep = parseFloat(String(q.dataset.rep).replace(",", "."));
    const tol = q.dataset.tol ? parseFloat(q.dataset.tol) : 0.03;
    const saisie = document.createElement("div"); saisie.className = "saisie";
    saisie.innerHTML = `<input type="text" inputmode="decimal" autocomplete="off" aria-label="${T.rep}"><span class="unite"></span><button type="button">${T.ver}</button><button type="button" class="voir">${T.voir}</button><span class="etat" role="status"></span>`;
    const expl = q.querySelector(".explication");
    if (expl) expl.setAttribute("aria-live", "polite");
    q.insertBefore(saisie, expl || null);
    saisie.querySelector(".unite").textContent = q.dataset.unite || "";
    const inp = saisie.querySelector("input"), etat = saisie.querySelector(".etat");
    const verifier = () => {
      const s = inp.value.trim().replace(/\s/g, "").replace(",", ".").replace(/[×x]10\^?/i, "e").replace("·10^", "e");
      const v = parseFloat(s);
      q.classList.add("essaye");
      if (!isFinite(v)) { etat.textContent = T.nombre; etat.className = "etat faux"; return; }
      const ok = rep === 0 ? Math.abs(v) < tol : Math.abs(v - rep) / Math.abs(rep) <= tol;
      etat.textContent = ok ? T.juste : T.faux; etat.className = "etat " + (ok ? "juste" : "faux");
      if (ok) q.classList.add("repondu");
    };
    saisie.querySelector("button:not(.voir)").addEventListener("click", verifier);
    inp.addEventListener("keydown", e => { if (e.key === "Enter" && !e.isComposing) verifier(); });
    saisie.querySelector(".voir").addEventListener("click", () => q.classList.add("repondu"));
    const r = bouton(T.eff, "reinit discret", T.tEff);
    q.insertBefore(r, q.firstChild);
    q._reinit = () => { inp.value = ""; etat.textContent = ""; etat.className = "etat"; q.classList.remove("repondu", "essaye"); };
    r.addEventListener("click", q._reinit);
  });
})();

/*@ jouets | class="jouet\b */
/* Jouets : bouton « Réinitialiser » (réglages de départ, relevés une fois le code du jouet exécuté ; un jouet qui garde
   un état à lui écoute « cours:reinit » sur son élément) ; libellés des commandes regroupés (formule et texte). */
(() => {
  const EN = (document.documentElement.lang || "fr").slice(0, 2) === "en";
  const champs = j => [...j.querySelectorAll("input, select, textarea")].filter(c => c.type !== "button" && c.type !== "submit");
  const relever = j => { j._depart = new Map(champs(j).map(c => [c, c.type === "checkbox" || c.type === "radio" ? c.checked : c.tagName === "SELECT" ? c.selectedIndex : c.value])); };
  function reinit(j) {
    j.dispatchEvent(new CustomEvent("cours:reinit"));
    const cs = champs(j), depart = j._depart || new Map();
    cs.forEach(c => {
      const v = depart.get(c);
      if (c.type === "checkbox" || c.type === "radio") c.checked = v != null ? v : c.defaultChecked;
      else if (c.tagName === "SELECT") c.selectedIndex = v != null ? v : Math.max(0, [...c.options].findIndex(o => o.defaultSelected));
      else c.value = v != null ? v : c.defaultValue;
    });
    cs.filter(c => !c.dataset.k).forEach(c => c.dispatchEvent(new Event("change", { bubbles: true })));
    cs.filter(c => c.dataset.k).forEach(c => c.dispatchEvent(new Event("input", { bubbles: true })));
  }
  /* un libellé qui mêle formule et texte ferait plusieurs cellules de la grille : on le réunit en un <span> */
  const champ = n => n.nodeType === 1 && n.matches("input, select, output, button, textarea, meter, progress");
  document.querySelectorAll(".commandes label").forEach(label => {
    let groupe = [];
    const fermer = () => {
      const pleins = groupe.filter(n => n.nodeType === 1 || n.textContent.trim());
      if (pleins.length && !(pleins.length === 1 && pleins[0].nodeType === 1 && pleins[0].tagName === "SPAN" && !pleins[0].classList.contains("katex"))) {
        const s = document.createElement("span"); s.className = "libelle";
        pleins[0].before(s); groupe.forEach(n => s.appendChild(n));
        s.normalize();
        if (s.firstChild && s.firstChild.nodeType === 3) s.firstChild.textContent = s.firstChild.textContent.replace(/^\s+/, "");
        if (s.lastChild && s.lastChild.nodeType === 3) s.lastChild.textContent = s.lastChild.textContent.replace(/\s+$/, "");
      }
      groupe = [];
    };
    [...label.childNodes].forEach(n => { if (champ(n)) fermer(); else groupe.push(n); });
    fermer();
  });
  document.querySelectorAll(".jouet").forEach(j => {
    const b = document.createElement("button"); b.type = "button"; b.className = "reinit discret";
    b.textContent = EN ? "↺ Reset" : "↺ Réinitialiser"; b.title = EN ? "Back to the starting settings" : "Remettre les réglages de départ";
    const titre = j.querySelector(":scope > h4, :scope > .jouet-titre");
    if (titre) titre.after(b); else j.insertBefore(b, j.firstChild);
    j._reinit = () => reinit(j);
    b.addEventListener("click", j._reinit);
  });
  const tous = () => document.querySelectorAll(".jouet").forEach(relever);
  if (window.Cours && !window.Cours.demarre) document.addEventListener("cours:pret", tous, { once: true }); else tous();
})();

/*@ actions | data-action="(deplier|reinit)" */
/* Boutons de l'en-tête : tout déplier ou replier ; remettre QCM et jouets à zéro. On garde sous les yeux ce qu'on lisait. */
(() => {
  const EN = (document.documentElement.lang || "fr").slice(0, 2) === "en";
  const statut = t => { const s = document.querySelector(".tete .statut"); if (s) { s.textContent = ""; setTimeout(() => { s.textContent = t; }, 30); } };
  function avecAncre(fn) {
    const main = document.querySelector("main");
    let el = null;
    if (main) {
      const r = main.getBoundingClientRect(), x = r.left + r.width / 2;
      for (const y of [80, 140, 220, 320, 440]) { const e = document.elementFromPoint(x, y); if (e && main.contains(e)) { el = e; break; } }
    }
    const avant = el ? el.getBoundingClientRect().top : 0;
    fn();
    if (!el) return;
    let cible = el;
    for (let d = cible.closest("details:not([open])"); d; d = d.parentElement && d.parentElement.closest("details:not([open])")) cible = d.querySelector(":scope > summary") || d;
    window.scrollBy(0, cible.getBoundingClientRect().top - avant);
  }
  document.addEventListener("click", e => {
    const b = e.target.closest(".tete [data-action]"); if (!b) return;
    if (b.dataset.action === "deplier") {
      const tous = [...document.querySelectorAll("main details")], ouvrir = tous.some(d => !d.open);
      avecAncre(() => tous.forEach(d => { d.open = ouvrir; }));
      statut(ouvrir ? (EN ? "Everything expanded." : "Tout est déplié.") : (EN ? "Everything collapsed." : "Tout est replié."));
    } else if (b.dataset.action === "reinit") {
      const q = [...document.querySelectorAll("main :is(.qcm, .qnum)")].filter(x => x._reinit), j = [...document.querySelectorAll("main .jouet")].filter(x => x._reinit);
      avecAncre(() => { q.forEach(x => x._reinit()); j.forEach(x => x._reinit()); });
      statut(EN ? `${q.length} question(s) and ${j.length} toy(s) reset.` : `${q.length} question(s) et ${j.length} jouet(s) remis à zéro.`);
    }
  });
})();

/*@ prio | data-prio= */
/* Priorités de révision : ★★★ incontournable, ★★ important, ★ approfondissement. Un titre {prio=n} donne son niveau à
   ce qui le suit jusqu'au titre suivant de même rang ; un bloc (exo, demo…) peut avoir le sien ; confirmer="raison"
   ajoute la réserve « à confirmer ». L'encadré .priorites du chapitre (posé par textured.py) reçoit les sections,
   exercices et démonstrations ★★★ et les réserves. Le bouton de l'en-tête masque ce qui est sous le niveau choisi
   (réglage gardé par cours) ; une ancre vers un passage masqué lève le filtre. */
(() => {
  const racine = document.documentElement, main = document.querySelector("main"); if (!main) return;
  const EN = (racine.lang || "fr").slice(0, 2) === "en", CLE = racine.dataset.cle || "tx:";
  const NIVEAUX = EN ? { 3: ["★★★", "essential"], 2: ["★★", "important"], 1: ["★", "further"] } : { 3: ["★★★", "incontournable"], 2: ["★★", "important"], 1: ["★", "approfondissement"] };
  const FILTRES = EN ? { 1: "Priorities: all", 2: "Priorities: ★★ and up", 3: "Priorities: ★★★ only" } : { 1: "Priorités : tout", 2: "Priorités : ★★ et ★★★", 3: "Priorités : ★★★ seulement" };
  const lire = () => { try { const t = +localStorage.getItem(CLE + "prio"); return t === 2 || t === 3 ? t : 1; } catch (e) { return 1; } };
  const garder = t => { try { localStorage.setItem(CLE + "prio", String(t)); } catch (e) { /* rien */ } };
  const badge = n => { const s = document.createElement("span"); s.className = "prio p" + n; s.textContent = NIVEAUX[n][0]; s.title = (EN ? "Priority: " : "Priorité : ") + NIVEAUX[n][1]; return s; };
  const propre = e => +e.dataset.prio || 0;
  const reserve = t => { const s = document.createElement("span"); s.className = "prio-conf"; s.textContent = EN ? "to be confirmed" : "à confirmer"; s.title = t; return s; };
  const poser = (el, ou, n) => { if (n) ou.append(badge(n)); if (el.dataset.confirmer) ou.append(reserve(el.dataset.confirmer)); };
  let n2 = 0, n3 = 0;
  [...main.children].forEach(e => {
    if (e.tagName === "H2") { n2 = propre(e); n3 = 0; poser(e, e, n2); return; }
    if (e.tagName === "H3") { n3 = propre(e) || n2; if (n3) e.dataset.prio = n3; poser(e, e, n3); return; }
    if (!e.dataset.prio && (n3 || n2)) e.dataset.prio = n3 || n2;
  });
  const herite = e => { const a = e.parentElement && e.parentElement.closest("[data-prio]"); return a ? +a.dataset.prio : 0; };
  main.querySelectorAll("details.demo, .exo").forEach((d, k) => {
    const n = propre(d) || herite(d), ou = d.matches("details") ? d.querySelector(":scope > summary") : d.querySelector(":scope > h4");
    if (n) d.dataset.prio = n;
    if (ou) poser(d, ou, n);
    if (!d.id) d.id = (d.matches("details") ? "demo-" : "exo-") + (k + 1);
  });

  /* encadré du chapitre : ce qui est ★★★, puis les réserves */
  const z = main.querySelector(".priorites");
  if (z) {
    const para = (cl, ...contenu) => { const p = document.createElement("p"); if (cl) p.className = cl; p.append(...contenu); z.append(p); return p; };
    const lien = (id, ...contenu) => { const a = document.createElement("a"); a.href = "#" + id; a.append(...contenu); return a; };
    const liste = (titre, items) => { if (!items.length) return; const p = para("prio-liste", titre + " : "); items.forEach((it, i) => { if (i) p.append(" · "); p.append(it); }); };
    const num = h => { const s = h.querySelector(".num"); return s ? s.textContent.trim() : ""; };
    const sections = [], titres = [...main.children].filter(e => e.matches("h2, h3"));
    titres.forEach((h, i) => {
      if (h.tagName !== "H2" || !num(h)) return;
      const sous = []; for (let j = i + 1; j < titres.length && titres[j].tagName === "H3"; j++) sous.push(titres[j]);
      if (h.dataset.prio === "3" && sous.every(s => s.dataset.prio === "3")) sections.push(lien(h.id, "§ " + num(h)));
      else sous.filter(s => s.dataset.prio === "3" && num(s)).forEach(s => sections.push(lien(s.id, "§ " + num(s))));
    });
    liste(EN ? "Sections ★★★" : "Sections ★★★", sections);
    const exos = [...main.querySelectorAll(".exo[data-prio='3']")].map(x => {
      const m = (x.querySelector("h4") || x).textContent.match(/(?:Exercice|Exercise)\s+([^\s—–.:]+)/);
      return lien(x.id, x.dataset.court || (m ? m[1] : x.id));
    });
    liste(EN ? "Exercises ★★★" : "Exercices ★★★", exos);
    const demos = [...main.querySelectorAll("details.demo[data-prio='3']")];
    if (demos.length) {
      const d = document.createElement("details"); d.className = "plus prio-demos";
      const s = document.createElement("summary");
      s.textContent = EN ? (demos.length > 1 ? `The ${demos.length} ★★★ proofs of the chapter` : "The ★★★ proof of the chapter")
        : (demos.length > 1 ? `Les ${demos.length} démonstrations ★★★ du chapitre` : "La démonstration ★★★ du chapitre");
      const ul = document.createElement("ul");
      demos.forEach(dm => {
        const li = document.createElement("li"), contenu = dm.querySelector(":scope > summary").cloneNode(true);
        contenu.querySelectorAll(".etiq, .prio, .prio-conf").forEach(e => e.remove());
        li.append(lien(dm.id, ...contenu.childNodes)); ul.append(li);
      });
      const corps = document.createElement("div"); corps.className = "corps"; corps.append(ul);
      d.append(s, corps); z.append(d);
    }
    main.querySelectorAll("[data-confirmer]").forEach(el => {
      const cible = el.matches("h2, h3") ? (num(el) ? "§ " + num(el) : el.textContent.trim()) : (el.querySelector("h4, summary") || el).textContent.trim().slice(0, 50);
      para("prio-reserve", reserve(el.dataset.confirmer), " ", lien(el.id, cible), " : " + el.dataset.confirmer);
    });
    para("petit", EN ? "The star button in the header hides what is below the chosen level." : "Le bouton étoile de l’en-tête masque ce qui est sous le niveau choisi.");
  }
  function filtrer(t) {
    const garde = [3, 2, 1].filter(n => n >= t).map(n => `[data-prio="${n}"]`).join(", ");
    main.querySelectorAll("[data-prio]").forEach(e => {
      const bas = +e.dataset.prio < t;
      if (e.matches("h2, h3")) { e.classList.toggle("prio-sous", bas); return; }
      e.classList.toggle("prio-cache", bas && !e.querySelector(garde));
    });
    racine.dataset.filtrePrio = t;
    document.querySelectorAll('.tete [data-action="prio"]').forEach(b => { b.title = FILTRES[t]; b.setAttribute("aria-label", FILTRES[t]); b.setAttribute("aria-pressed", String(t > 1)); b.dataset.niveau = t; });
    garder(t);
    if (window.Cours && window.Cours.redessiner) window.Cours.redessiner();
  }
  const montrerCible = () => {
    const id = decodeURIComponent(location.hash.slice(1)), el = id && document.getElementById(id);
    if (!el || !(el.closest(".prio-cache") || el.matches(".prio-sous"))) return false;
    filtrer(1); return true;
  };
  filtrer(lire());
  if (montrerCible()) { const el = document.getElementById(decodeURIComponent(location.hash.slice(1))); if (el) el.scrollIntoView(); }
  addEventListener("hashchange", () => { if (montrerCible()) { const el = document.getElementById(decodeURIComponent(location.hash.slice(1))); if (el) el.scrollIntoView(); } });
  document.addEventListener("click", e => { const b = e.target.closest('.tete [data-action="prio"]'); if (b) filtrer(lire() % 3 + 1); });
})();

/*@ avertissement | class="avertissement\b */
/* Bandeau d'avertissement (« avertissement: » dans l'en-tête) : collé en haut, il repousse l'en-tête courant ; « J'ai
   compris » le ferme pour tout le cours (ou la page), et l'amorce du <head> ne le montre plus. */
(() => {
  const racine = document.documentElement, b = document.querySelector(".avertissement"); if (!b) return;
  const CLE = racine.dataset.cle || "tx:";
  if (racine.classList.contains("avert-lu")) { b.remove(); return; }
  const hauteur = () => racine.style.setProperty("--avert-h", b.offsetHeight + "px");
  hauteur();
  const ro = window.ResizeObserver ? new ResizeObserver(hauteur) : null;
  if (ro) ro.observe(b);
  b.querySelector(".avert-ok").addEventListener("click", () => {
    try { localStorage.setItem(CLE + "avertissement", "1"); } catch (e) { /* rien */ }
    if (ro) ro.disconnect();
    racine.style.removeProperty("--avert-h");
    b.classList.add("ferme");
    const fin = () => b.remove();
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) fin(); else setTimeout(fin, 260);
    const m = document.querySelector("main"); if (m) m.focus({ preventScroll: true });
  });
})();

/*@ schemas | <svg\b */
/* Schémas SVG sur un écran étroit : si le plus petit texte d'un schéma tomberait sous 8,5 px, le schéma garde la largeur
   où ce texte fait 10 px et défile dans un cadre (bord estompé du côté où il continue). Sur grand écran, un exercice dont
   un schéma aurait un texte trop fin s'élargit (.elargi). Refait au redimensionnement et à l'ouverture d'un repli. */
(() => {
  const TROP_FIN = 8.5, LISIBLE = 10;
  const candidat = s => !(s.closest(".katex") || s.parentElement.closest("svg") || !s.viewBox || !s.viewBox.baseVal || s.viewBox.baseVal.width < 200);
  const plusPetit = s => { let fs = Infinity; s.querySelectorAll("text").forEach(t => { const f = parseFloat(getComputedStyle(t).fontSize); if (f > 0) fs = Math.min(fs, f); }); return fs; };
  function bords(c) {
    if (!c.classList.contains("actif")) return;
    c.classList.toggle("suite-g", c.scrollLeft > 2);
    c.classList.toggle("suite-d", c.scrollLeft + c.clientWidth < c.scrollWidth - 2);
  }
  function elargirExos() {
    const large = innerWidth >= 1100;
    document.querySelectorAll("main .exo").forEach(exo => {
      if (!large) { exo.classList.remove("elargi"); return; }
      if (exo.classList.contains("elargi")) return;
      const fin = [...exo.querySelectorAll("svg")].filter(candidat).some(s => {
        const l = s.getBoundingClientRect().width; if (!l) return false;
        const fs = plusPetit(s); return isFinite(fs) && fs * l / s.viewBox.baseVal.width < TROP_FIN;
      });
      if (fin) exo.classList.add("elargi");
    });
  }
  function ajuster() {
    elargirExos();
    const etroit = innerWidth < 760;
    document.querySelectorAll("main svg").forEach(s => {
      if (!candidat(s)) return;
      const cadre = s.parentElement.classList.contains("schema-defile") ? s.parentElement : null;
      s.style.width = "";
      if (cadre) cadre.classList.remove("actif", "suite-g", "suite-d");
      if (!etroit) return;
      const largeur = s.getBoundingClientRect().width, W = s.viewBox.baseVal.width;
      if (!s.querySelector("text") || !largeur) return;
      const fs = plusPetit(s), besoin = Math.min(W, W * LISIBLE / fs);
      if (!isFinite(fs) || fs * largeur / W >= TROP_FIN || besoin <= largeur + 4) return;
      let c = cadre;
      if (!c) {
        c = document.createElement("div"); c.className = "schema-defile"; s.parentElement.insertBefore(c, s); c.appendChild(s);
        c.addEventListener("scroll", () => bords(c), { passive: true });
      }
      c.classList.add("actif");
      s.style.width = Math.ceil(besoin) + "px";
      bords(c);
    });
  }
  ajuster();
  let minuterie = 0;
  addEventListener("resize", () => { clearTimeout(minuterie); minuterie = setTimeout(ajuster, 150); });
  document.addEventListener("toggle", e => { if (e.target.open && e.target.querySelector("svg")) ajuster(); }, true);
})();
