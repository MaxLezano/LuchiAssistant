/* Prototipo de interfaz de Luchi.
 * - Isla: borde negro arriba + Luchi flotando debajo (usa las animaciones .webp de mockups/animaciones).
 * - Ventana de la app: ajustes, Tu Luchi (editor real que compone las capas de assets/luchi), casa,
 *   apps, grabaciones, privacidad, bienvenida.
 * Nada es funcional: los datos son de ejemplo.
 */
const A = "../../assets/luchi/";
const ANIM = "../animaciones/";
const PIEZAS = "piezas/";
const C = window.LUCHI;
const $ = (q, el = document) => el.querySelector(q);
const $$ = (q, el = document) => [...el.querySelectorAll(q)];

function toast(msg) {
  const t = $("#toast"); t.textContent = msg; t.classList.add("show");
  clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove("show"), 2200);
}
function store(key, val) {
  try { if (val === undefined) return JSON.parse(localStorage.getItem(key)); localStorage.setItem(key, JSON.stringify(val)); }
  catch { return null; }
}

/* ================================================================ composición de Luchi (canvas) */
const DEFAULT_STYLE = { color: "rosa", blush: "rosa", eyes: "brillo", mouth: "linea", pattern: "ninguno", flash: [], accessory: "ninguno" };
const VIEW = { x: 30, y: -40, s: 964 };          // recorte del espacio 1024 que entra en el lienzo (incluye accesorios)
const imgCache = new Map();
function load(src) {
  if (!imgCache.has(src)) {
    imgCache.set(src, new Promise((ok, fail) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => fail(src); i.src = src; }));
  }
  return imgCache.get(src);
}
const byId = (list, id) => list.find(x => x.id === id);

async function drawLuchi(cv, st, pose = "neutral", { shadow = true } = {}) {
  st = { ...DEFAULT_STYLE, ...st };
  const size = cv.width, k = size / VIEW.s;
  const color = byId(C.colores, st.color) || C.colores[0];
  const eyes = byId(C.ojos, st.eyes) || C.ojos[0];
  const pat = st.pattern !== "ninguno" ? byId(C.tatuajes.patrones, st.pattern) : null;
  const acc = st.accessory !== "ninguno" ? byId(C.accesorios, st.accessory) : null;
  const flash = (st.flash || []).map(([id, slot]) => ({ f: byId(C.tatuajes.flash, id), slot: C.tatuajes.posiciones[slot] })).filter(x => x.f && x.slot);
  const [body, eL, eR, happy, mouth, patImg, accImg, ...flashImgs] = await Promise.all([
    load(A + color.archivo),
    load(A + eyes.archivos.izq), load(A + eyes.archivos.der), load(PIEZAS + "ojos_feliz.png"),
    load(`${PIEZAS}boca_${st.mouth}_${pose}.png`),
    pat ? load(A + pat.archivo) : null, acc ? load(A + acc.archivo) : null,
    ...flash.map(x => load(A + x.f.archivo)),
  ]);
  const T = c => c.setTransform(k, 0, 0, k, -VIEW.x * k, -VIEW.y * k);
  const off = document.createElement("canvas"); off.width = off.height = size;
  const o = off.getContext("2d"); T(o);
  o.drawImage(body, 0, 0, 1024, 1024);
  // tatuajes: tinta multiplicada sobre la piel, un poco desenfocada
  const ink = (im, x, y, w, h) => { o.save(); o.globalCompositeOperation = "multiply"; o.globalAlpha = 0.9; o.filter = `blur(${Math.max(0.3, 0.8 * k)}px)`; o.drawImage(im, x, y, w, h); o.restore(); };
  if (patImg) ink(patImg, 0, 0, 1024, 1024);
  flash.forEach(({ slot }, i) => { const s = slot.escala; ink(flashImgs[i], slot.x - 100 * s, slot.y - 100 * s, 200 * s, 200 * s); });
  // mejillas
  const bl = byId(C.mejillas, st.blush);
  if (bl && bl.rgb) {
    o.save(); o.filter = `blur(${7 * k}px)`;
    o.fillStyle = `rgba(${bl.rgb.join(",")},${(150 / 255) * (pose === "feliz" ? 1.35 : 1)})`;
    for (const [x, y] of C.espacio.mejillas) { o.beginPath(); o.ellipse(x, y, 38, 17, 0, 0, Math.PI * 2); o.fill(); }
    o.restore();
  }
  // ojos y boca
  if (pose === "feliz") o.drawImage(happy, 0, 0, 1024, 1024);
  else for (const [im, [x, y]] of [[eL, C.espacio.ojo_izq], [eR, C.espacio.ojo_der]]) o.drawImage(im, x - 70, y - 70, 140, 140);
  o.drawImage(mouth, 0, 0, 1024, 1024);
  // recortar todo a la silueta del cuerpo
  o.globalCompositeOperation = "destination-in"; o.drawImage(body, 0, 0, 1024, 1024);
  // lienzo final: sombra, cuerpo, accesorio
  const ctx = cv.getContext("2d");
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, size, size);
  if (shadow) {
    T(ctx); ctx.save(); ctx.filter = `blur(${16 * k}px)`; ctx.fillStyle = "rgba(25,12,20,.38)";
    ctx.beginPath(); ctx.ellipse(511, 812, 250, 20, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  }
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.drawImage(off, 0, 0);
  if (accImg) { T(ctx); ctx.drawImage(accImg, 0, 0, 1024, 1024); }
}
function luchiCanvas(st, pose, px = 168) {
  const cv = document.createElement("canvas"); cv.width = cv.height = px;
  drawLuchi(cv, st, pose).catch(e => console.warn("No se pudo cargar", e));
  return cv;
}

/* ================================================================ isla */
const notch = $("#notch"), stage = $("#stage"), luchiImg = $("#luchiImg"), bubble = $("#bubble");
let timers = [], recTimer = null, muted = false;
const later = (ms, fn) => timers.push(setTimeout(fn, ms));
function stopAll() { timers.forEach(clearTimeout); timers = []; }
function anim(name) { stage.classList.remove("hidden"); luchiImg.src = `${ANIM}${name}.webp?${Date.now()}`; }
function say(html) { if (!html) { bubble.classList.remove("show"); return; } bubble.innerHTML = html; bubble.classList.add("show"); }
function typeIn(text, total = 1500) {
  let i = 0; const step = total / text.length;
  const tick = () => { i++; say(`<span class="who">Te escucho</span>${text.slice(0, i)}<span style="opacity:.5">▍</span>`); if (i < text.length) later(step, tick); };
  tick();
}
function appear(then) {
  if (!stage.classList.contains("hidden") && notch.classList.contains("show")) { then(); return; }
  notch.classList.add("show"); later(220, () => anim("aparecer")); later(1650, then);
}
function hide() {
  say(null); anim("esconderse");
  later(2500, () => { stage.classList.add("hidden"); notch.classList.remove("show"); });
}
function listenThen(text, then) { anim("escuchando"); typeIn(text); later(text.length * 55 + 900, then); }

const DEMOS = {
  full() {
    appear(() => listenThen("prendé la luz del comedor", () => {
      anim("pensando"); say(`<span class="who">Pensando</span>…`);
      later(1100, () => {
        anim("hablando"); say(`<span class="who">Luchi</span>Listo, prendí la luz del comedor.`);
        later(2300, () => { anim("feliz"); say(null); later(2300, hide); });
      });
    }));
  },
  pregunta() {
    appear(() => listenThen("abrí Hollow Knight", () => {
      anim("pregunta");
      say(`<span class="who">Luchi</span>Encontré dos. ¿Cuál querés abrir?<div class="choices"><span>Hollow Knight</span><span>Hollow Knight: Silksong</span></div>`);
      later(6000, hide);
    }));
  },
  error() {
    appear(() => listenThen("poné Interestelar en la tele", () => {
      anim("pensando"); say(`<span class="who">Pensando</span>…`);
      later(1000, () => { anim("apenado"); say(`<span class="who">Luchi</span>No encontré la tele. ¿Está prendida?`); later(3200, hide); });
    }));
  },
  grabar() {
    appear(() => listenThen("grabá esta reunión", () => {
      anim("hablando"); say(`<span class="who">Luchi</span>Grabando. Acordate de avisarle a los demás.`);
      later(2600, () => {
        say(null); anim("esconderse");
        later(2400, () => { stage.classList.add("hidden"); startRec(); });
      });
    }));
  },
  dormido() {
    muted = !muted; $("#trayMochi").classList.toggle("muted", muted);
    $("#muteBtn").textContent = muted ? "🎙️ Activar micrófono" : "🔇 Silenciar micrófono";
    if (muted) appear(() => { anim("dormido"); say(`<span class="who">Micrófono silenciado</span>No escucho nada hasta que lo actives.`); later(3200, hide); });
    else toast("Micrófono activado: di \"Luchi\"");
  },
  compania() { appear(() => { anim("idle"); say(null); }); },
  ocultar() { if (!stage.classList.contains("hidden")) hide(); },
};
function startRec() {
  const t0 = Date.now(); notch.classList.add("show", "rec");
  const upd = () => { const s = Math.floor((Date.now() - t0) / 1000); $("#recLabel").textContent = `Grabando · ${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")} · tocar para detener`; };
  upd(); recTimer = setInterval(upd, 500);
}
notch.addEventListener("click", () => {
  if (!notch.classList.contains("rec")) return;
  clearInterval(recTimer); notch.classList.remove("rec"); stopAll();
  anim("aparecer");
  later(1500, () => {
    anim("hablando"); say(`<span class="who">Luchi</span>Listo, guardé la grabación y la transcripción.`);
    later(2400, () => { anim("feliz"); say(null); later(2300, hide); });
  });
});

/* ================================================================ ventana */
const ICONS = {
  general: '<path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/>',
  voz: '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M19 10v1a7 7 0 0 1-14 0v-1M12 18v4M8 22h8"/>',
  tuluchi: '<rect x="3" y="5" width="18" height="15" rx="6"/><circle cx="9" cy="12" r="1" fill="currentColor"/><circle cx="15" cy="12" r="1" fill="currentColor"/><path d="M10.5 15.5c.8.6 2.2.6 3 0"/>',
  casa: '<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1Z"/>',
  apps: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  grabaciones: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3.5" fill="currentColor"/>',
  privacidad: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/>',
  acerca: '<circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/>',
  recordatorios: '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2M5 3 2 6M19 3l3 3"/>',
  escenas: '<path d="M4 4h16v16H4z" stroke-dasharray="0"/><path d="m9 8 7 4-7 4Z" fill="currentColor"/>',
  historial: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/>',
  cuenta: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  estado: '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
  laboratorio: '<path d="M9 3h6M10 3v6L4.5 19a1.5 1.5 0 0 0 1.3 2h12.4a1.5 1.5 0 0 0 1.3-2L14 9V3"/><path d="M7 15h10"/>',
};
const NAV = [
  ["Luchi", [["general", "General"], ["voz", "Voz y micrófono"], ["tuluchi", "Tu Luchi"]]],
  ["Casa y PC", [["casa", "Casa y dispositivos"], ["apps", "Apps y sistema"], ["escenas", "Escenas y atajos"]]],
  ["Tus cosas", [["recordatorios", "Recordatorios"], ["grabaciones", "Grabaciones"], ["historial", "Historial"]]],
  ["Cuenta", [["cuenta", "Cuenta y sincronización"], ["privacidad", "Privacidad"], ["estado", "Estado del sistema"], ["acerca", "Acerca de"]]],
  ["Desarrollo", [["laboratorio", "Laboratorio del personaje"]]],
];
const icon = id => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${ICONS[id]}</svg>`;
let current = "general";
let style = { ...DEFAULT_STYLE, ...(store("luchi.style") || {}) };

function openWin(view) {
  $("#win").classList.add("open"); $("#trayMenu").classList.remove("open"); $("#trayBtn").classList.remove("on");
  show(view);
}
function renderSidebar() {
  const sb = $("#sidebar");
  sb.innerHTML = `<div class="me"><span id="meSlot"></span><div><b>Luchi</b><small>${muted ? "Micrófono silenciado" : "Escuchando · di \"Luchi\""}</small></div></div>` +
    NAV.map(([group, items]) => `<div class="nav-group">${group}</div>` +
      items.map(([id, label]) => `<button class="nav ${id === current ? "active" : ""}" data-view="${id}">${icon(id)}<span>${label}</span></button>`).join("")).join("");
  const cv = luchiCanvas(style, "neutral", 104); $("#meSlot").replaceWith(cv);
}
function show(view) {
  current = view;
  const welcome = view === "bienvenida";
  $("#sidebar").classList.toggle("hidden", welcome);
  if (!welcome) renderSidebar();
  const c = $("#content"); c.scrollTop = 0; c.innerHTML = ""; VIEWS[view](c);
}
document.addEventListener("click", e => {
  const v = e.target.closest("[data-view]"); if (v) show(v.dataset.view);
  const o = e.target.closest("[data-open]"); if (o) openWin(o.dataset.open);
  const d = e.target.closest("[data-demo]"); if (d) { stopAll(); DEMOS[d.dataset.demo](); $("#trayMenu").classList.remove("open"); }
  if (e.target.closest("[data-close]")) $("#win").classList.remove("open");
  const tg = e.target.closest(".toggle"); if (tg) tg.classList.toggle("on");
  const sg = e.target.closest(".seg button"); if (sg && !sg.dataset.keep) { $$("button", sg.parentElement).forEach(b => b.classList.toggle("on", b === sg)); }
});

/* helpers de vistas */
const row = (title, sub, ctrl) => `<div class="row"><div class="txt"><b>${title}</b>${sub ? `<small>${sub}</small>` : ""}</div>${ctrl}</div>`;
const tog = on => `<button class="toggle ${on ? "on" : ""}" aria-label="Activar"></button>`;
const seg = (opts, on = 0) => `<div class="seg">${opts.map((o, i) => `<button class="${i === on ? "on" : ""}">${o}</button>`).join("")}</div>`;
const sel = opts => `<select>${opts.map(o => `<option>${o}</option>`).join("")}</select>`;
const head = (t, lead) => `<h1>${t}</h1><p class="lead">${lead}</p>`;

/* ================================================================ vistas */
const VIEWS = {};

VIEWS.general = c => {
  c.innerHTML = head("General", "Cómo arranca Luchi y cómo se ve la isla en tu escritorio.") + `
  <div class="card rows">
    ${row("Iniciar con Windows", "Luchi queda escuchando en segundo plano desde que prendés la PC", tog(true))}
    ${row("Tema", "", seg(["Oscuro", "Claro", "Sistema"], 2))}
    ${row("Idioma de la interfaz", "", sel(["Español", "English", "Português"]))}
  </div>
  <div class="section-title">La isla</div>
  <div class="card rows">
    ${row("Posición", "Dónde aparece el borde negro y Luchi debajo", seg(["Arriba a la izquierda", "Arriba al centro", "Arriba a la derecha"], 1))}
    ${row("Monitor", "", sel(["Principal · 3440 × 1440", "Seguir al mouse"]))}
    ${row("Tamaño de Luchi", "", `<input type="range" min="60" max="160" value="100">`)}
    ${row("Esconderse después de responder", "", sel(["2 segundos", "3 segundos", "5 segundos", "Nunca"]))}
    ${row("Sonidos cortos", "Un \"pling\" al despertar y un tic al terminar, para cuando no estás mirando", tog(true))}
    ${row("Movimiento reducido", "Sin saltos ni balanceos: solo cambia la cara. Respeta la preferencia de Windows", tog(false))}
    ${row("Ocultar en juegos a pantalla completa", "Luchi sigue respondiendo por voz", tog(true))}
  </div>`;
};

VIEWS.voz = c => {
  c.innerHTML = head("Voz y micrófono", "Cómo despertarla, qué micrófono usa y cómo te responde.") + `
  <div class="section-title">Palabra de activación</div>
  <div class="grid-cards" id="wake">
    <button class="opt on" style="align-items:flex-start;padding:16px;text-align:left"><b style="font-size:18px;color:var(--text)">"Luchi"</b><span>Solo el nombre. Más cómodo.</span><span class="tag">Recomendada</span></button>
    <button class="opt" style="align-items:flex-start;padding:16px;text-align:left"><b style="font-size:18px;color:var(--text)">"Oye Luchi"</b><span>Menos activaciones falsas si hay mucha TV de fondo.</span></button>
  </div>
  <div class="card rows" style="margin-top:12px">
    ${row("Sensibilidad", "Más alta: te escucha más fácil · Más baja: menos activaciones por error", `<input type="range" min="0" max="100" value="60">`)}
    ${row("Probar la palabra", "Decí \"Luchi\" y mirá si la detecta", `<button class="btn" id="testWake">Probar ahora</button>`)}
    ${row("Atajo de teclado", "Para despertarla sin hablar", `<span class="chip">Ctrl + Alt + L</span><button class="btn sm">Cambiar</button>`)}
  </div>
  <div class="section-title">Micrófono</div>
  <div class="card rows">
    ${row("Dispositivo", "", sel(["Micrófono (USB Audio Device)", "Auriculares (Realtek)", "Predeterminado de Windows"]))}
    ${row("Nivel", "Hablá para ver si te escucha", `<div class="meter"><i id="lvl"></i></div>`)}
    ${row("Silenciar micrófono", "Luchi no escucha nada, ni siquiera su nombre", tog(muted))}
  </div>
  <div class="section-title">Voz de Luchi</div>
  <div class="card rows">
    ${row("Voz", "Voces locales en español", sel(["Voz 1 · español", "Voz 2 · español", "Voz de Luchi (clonada, F9)"]))}
    ${row("Velocidad", "", `<input type="range" min="70" max="140" value="100">`)}
    ${row("Volumen", "", `<input type="range" min="0" max="100" value="80">`)}
    ${row("Escuchar un ejemplo", "", `<button class="btn" id="sample">▶ "Listo, prendí la luz"</button>`)}
  </div>
  <div class="section-title">Conversación</div>
  <div class="card rows">
    ${row("Seguir escuchando después de responder", "Para decir \"y bajale el volumen\" sin repetir su nombre", sel(["6 segundos", "3 segundos", "10 segundos", "No"]))}
    ${row("Idioma de las órdenes", "", sel(["Español", "Detectar automáticamente"]))}
    ${row("Responder en voz", "Si lo apagás, solo responde en la isla", tog(true))}
  </div>`;
  $$("#wake .opt").forEach(b => b.onclick = () => $$("#wake .opt").forEach(x => x.classList.toggle("on", x === b)));
  $("#testWake").onclick = () => setTimeout(() => toast("Detectado: \"Luchi\" · confianza 0,93"), 900);
  $("#sample").onclick = () => toast("🔊 \"Listo, prendí la luz\"");
  const lvl = $("#lvl"); const iv = setInterval(() => { if (!document.body.contains(lvl)) return clearInterval(iv); lvl.style.width = `${10 + Math.random() * 55}%`; }, 120);
};

/* ---------------------------------------------------------------- Tu Luchi */
let edTab = "color", edPose = "neutral", edSlot = "panza_der", accCat = "todos";
const MOUTH_NAMES = Object.fromEntries(C.bocas.map(b => [b.id, b.nombre]));
const SEASON_NAMES = { cumpleanos: "cumpleaños", navidad: "Navidad", halloween: "Halloween", san_valentin: "San Valentín", verano: "verano", graduacion: "graduación" };
const SLOT_NAMES = { panza_der: "Panza derecha", panza_izq: "Panza izquierda", frente: "Frente", costado_der: "Costado" };

VIEWS.tuluchi = c => {
  c.innerHTML = head("Tu Luchi", "Elegí cómo se ve. Todas las emociones funcionan con cualquier combinación.") + `
  <div class="editor">
    <div class="preview card">
      <div class="stage" id="pvStage"><canvas id="pv" width="640" height="640"></canvas></div>
      <div class="seg" id="pose"><button data-keep="1" data-p="neutral" class="on">Neutral</button><button data-keep="1" data-p="feliz">Feliz</button><button data-keep="1" data-p="hablando">Hablando</button></div>
      <div class="seg" id="pvBg"><button class="on" data-b="dark">Fondo oscuro</button><button data-b="light">Fondo claro</button></div>
      <div class="actions">
        <button class="btn" id="rnd">🎲 Sorprendeme</button>
        <button class="btn" id="reset">Restablecer</button>
        <button class="btn primary" id="save">Guardar</button>
      </div>
      <small style="color:var(--muted);text-align:center">En la app, la vista previa está animada en vivo.</small>
    </div>
    <div>
      <div class="tabs" id="tabs">${[["color", "Color"], ["mejillas", "Mejillas"], ["ojos", "Ojos"], ["boca", "Boca"], ["tatuajes", "Tatuajes"], ["accesorios", "Accesorios"], ["presets", "Presets"]]
        .map(([id, l]) => `<button data-t="${id}" class="${id === edTab ? "on" : ""}">${l}</button>`).join("")}</div>
      <div id="tabBody"></div>
    </div>
  </div>`;
  $("#tabs").onclick = e => { const b = e.target.closest("button"); if (!b) return; edTab = b.dataset.t; $$("#tabs button").forEach(x => x.classList.toggle("on", x === b)); renderTab(); };
  $("#pose").onclick = e => { const b = e.target.closest("button"); if (!b) return; edPose = b.dataset.p; $$("#pose button").forEach(x => x.classList.toggle("on", x === b)); refresh(); };
  $("#pvBg").onclick = e => { const b = e.target.closest("button"); if (!b) return; $("#pvStage").classList.toggle("light", b.dataset.b === "light"); };
  $("#rnd").onclick = () => { style = randomStyle(); refresh(); };
  $("#reset").onclick = () => { style = { ...DEFAULT_STYLE }; refresh(); };
  $("#save").onclick = () => { store("luchi.style", style); renderSidebar(); toast("Guardado. Así se va a ver Luchi."); };
  refresh();
};
function refresh() { drawLuchi($("#pv"), style, edPose); renderTab(); }
const pick = arr => arr[Math.floor(Math.random() * arr.length)];
function randomStyle() {
  const flashIds = C.tatuajes.flash.map(f => f.id), slots = Object.keys(C.tatuajes.posiciones);
  const n = Math.random() < 0.5 ? 0 : 1 + Math.floor(Math.random() * 2);
  const used = [...slots].sort(() => Math.random() - 0.5).slice(0, n);
  return {
    color: pick(C.colores).id, blush: pick(C.mejillas.filter(m => m.rgb)).id, eyes: pick(C.ojos).id, mouth: pick(C.bocas).id,
    pattern: Math.random() < 0.35 ? pick(C.tatuajes.patrones).id : "ninguno",
    flash: used.map(s => [pick(flashIds), s]), accessory: Math.random() < 0.8 ? pick(C.accesorios).id : "ninguno",
  };
}
function optGrid(items, isOn, apply, thumb) {
  const g = document.createElement("div"); g.className = "opts";
  for (const it of items) {
    const b = document.createElement("button"); b.className = "opt" + (isOn(it) ? " on" : "");
    b.append(thumb(it)); const s = document.createElement("span"); s.innerHTML = it.label; b.append(s);
    if (it.tag) { const t = document.createElement("span"); t.className = "tag"; t.textContent = it.tag; b.append(t); }
    b.onclick = () => { apply(it); refresh(); };
    g.append(b);
  }
  return g;
}
const withStyle = patch => luchiCanvas({ ...style, ...patch }, edPose);
function renderTab() {
  const tb = $("#tabBody"); if (!tb) return; tb.innerHTML = "";
  if (edTab === "color") {
    tb.append(optGrid(C.colores.map(c => ({ ...c, label: c.id })), it => style.color === it.id, it => style.color = it.id, it => withStyle({ color: it.id })));
  } else if (edTab === "mejillas") {
    tb.append(optGrid(C.mejillas.map(m => ({ ...m, label: m.id === "ninguno" ? "sin mejillas" : m.id })), it => style.blush === it.id, it => style.blush = it.id, it => withStyle({ blush: it.id })));
  } else if (edTab === "ojos") {
    tb.append(optGrid(C.ojos.map(o => ({ ...o, label: o.nombre })), it => style.eyes === it.id, it => style.eyes = it.id, it => withStyle({ eyes: it.id })));
  } else if (edTab === "boca") {
    tb.insertAdjacentHTML("beforeend", `<p class="note" style="margin:0 0 12px">Probá la pose <b>Feliz</b> o <b>Hablando</b> para ver los dientes, el colmillo, los labios y la lengua.</p>`);
    tb.append(optGrid(C.bocas.map(b => ({ ...b, label: b.nombre })), it => style.mouth === it.id, it => style.mouth = it.id, it => withStyle({ mouth: it.id })));
  } else if (edTab === "tatuajes") {
    tb.insertAdjacentHTML("beforeend", `<div class="section-title" style="margin-top:0">Patrón de cuerpo completo</div>`);
    tb.append(optGrid([{ id: "ninguno", label: "ninguno" }, ...C.tatuajes.patrones.map(p => ({ ...p, label: p.nombre }))],
      it => style.pattern === it.id, it => style.pattern = it.id, it => withStyle({ pattern: it.id })));
    tb.insertAdjacentHTML("beforeend", `<div class="section-title">Diseños chicos · hasta ${C.tatuajes.max_flash}</div><p class="note" style="margin:0">Elegí una posición y después el diseño.</p>`);
    const slots = document.createElement("div"); slots.className = "slots";
    for (const s of Object.keys(C.tatuajes.posiciones)) {
      const cur = style.flash.find(f => f[1] === s);
      const b = document.createElement("button"); b.className = s === edSlot ? "on" : "";
      b.innerHTML = `${SLOT_NAMES[s]}<small>${cur ? byId(C.tatuajes.flash, cur[0]).nombre : "vacío"}</small>`;
      b.onclick = () => { edSlot = s; renderTab(); };
      slots.append(b);
    }
    tb.append(slots);
    const items = [{ id: "_quitar", label: "quitar" }, ...C.tatuajes.flash.map(f => ({ ...f, label: f.nombre, tag: f.categoria === "codigo" ? "código" : f.categoria === "japones" ? "japonés" : "clásico" }))];
    tb.append(optGrid(items, it => style.flash.some(f => f[0] === it.id && f[1] === edSlot), it => {
      const rest = style.flash.filter(f => f[1] !== edSlot);
      if (it.id === "_quitar") { style.flash = rest; return; }
      if (rest.length >= C.tatuajes.max_flash) { toast(`Máximo ${C.tatuajes.max_flash} diseños: quitá uno primero`); return; }
      style.flash = [...rest, [it.id, edSlot]];
    }, it => it.id === "_quitar" ? withStyle({ flash: style.flash.filter(f => f[1] !== edSlot) }) : withStyle({ flash: [...style.flash.filter(f => f[1] !== edSlot), [it.id, edSlot]] })));
  } else if (edTab === "accesorios") {
    const bar = document.createElement("div"); bar.className = "seg"; bar.style.marginBottom = "12px";
    for (const [id, l] of [["todos", "Todos"], ["diario", "Diario"], ["divertido", "Divertidos"], ["temporada", "De temporada"]]) {
      const b = document.createElement("button"); b.textContent = l; b.dataset.keep = 1; b.className = accCat === id ? "on" : "";
      b.onclick = () => { accCat = id; renderTab(); }; bar.append(b);
    }
    tb.append(bar);
    const list = C.accesorios.filter(a => accCat === "todos" || a.categoria === accCat);
    tb.append(optGrid([{ id: "ninguno", label: "ninguno" }, ...list.map(a => ({ ...a, label: a.nombre, tag: a.temporada ? SEASON_NAMES[a.temporada] : null }))],
      it => style.accessory === it.id, it => style.accessory = it.id, it => withStyle({ accessory: it.id })));
    tb.insertAdjacentHTML("beforeend", `<div class="card rows" style="margin-top:14px">
      ${row("Accesorios de temporada automáticos", "En Navidad, Halloween, San Valentín, verano y tu cumpleaños se pone el de la fecha. No reemplaza uno que hayas elegido", tog(false))}
      ${row("Hemisferio", "Para saber cuándo es verano", seg(["Sur", "Norte"], 0))}
      ${row("Tu cumpleaños", "Para el gorro de fiesta", `<input class="input" type="date">`)}
    </div>`);
  } else if (edTab === "presets") {
    tb.append(optGrid(Object.entries(C.presets).map(([id, p]) => ({ id, p, label: id })),
      it => false, it => style = { ...DEFAULT_STYLE, ...it.p, flash: it.p.flash || [] }, it => luchiCanvas({ ...DEFAULT_STYLE, ...it.p }, edPose)));
  }
}

/* ---------------------------------------------------------------- casa y dispositivos */
const ROOMS = [
  { name: "Comedor", devices: [{ ic: "💡", n: "Luz del comedor", st: "Encendida · 80 %", on: true, al: ["luz del comedor", "comedor"], br: "Philips Hue" }] },
  { name: "Sala", devices: [
    { ic: "📺", n: "Tele de la sala", st: "Apagada", al: ["tele", "la tele"], br: "LG webOS" },
    { ic: "💡", n: "Lámpara de pie", st: "Apagada", al: ["lámpara"], br: "TP-Link Tapo" },
    { ic: "🔌", n: "Enchufe del aire", st: "Encendido", on: true, al: ["aire"], br: "Tapo P110" }] },
  { name: "Dormitorio", devices: [
    { ic: "📺", n: "Google TV del dormitorio", st: "Apagada", al: ["tele del cuarto"], br: "Google Cast" },
    { ic: "💡", n: "Luz del dormitorio", st: "Apagada", al: ["luz del cuarto"], br: "Tuya · nube" }] },
];
const BRANDS = [
  ["Philips Hue", "Local · botón del puente"], ["TP-Link Tapo / Kasa", "Local · cuenta Tapo"], ["Google Cast / Chromecast", "Local · se detecta solo"],
  ["Android TV / Google TV", "Local · código en la tele"], ["LG webOS", "Local · aceptar en la tele"], ["Samsung Smart TV", "Local · aceptar en la tele"],
  ["Shelly", "Local"], ["Sonos", "Local · se detecta solo"], ["Matter", "Local · código QR"], ["Xiaomi / Mi Home", "Nube de Xiaomi"],
  ["Tuya / Smart Life", "Nube de Tuya"], ["Otra marca…", "Buscar entre más de 2000"],
];
let wiz = null;
VIEWS.casa = c => {
  if (wiz) return wizard(c);
  c.innerHTML = head("Casa y dispositivos", "Luces, teles y enchufes que Luchi puede manejar. Se conectan una vez y después alcanza con pedirlo.") + `
  <div class="card" style="display:flex;align-items:center;gap:16px;padding:16px 18px">
    <div style="font-size:28px">🏠</div>
    <div style="flex:1"><b>Home Assistant</b> <span class="chip ok">● Conectado</span><br><small style="color:var(--muted)">Corre en esta PC (máquina virtual) · 6 dispositivos · 3 habitaciones</small></div>
    <button class="btn" id="addDev">＋ Agregar dispositivo</button>
  </div>
  <div class="section-title">Encontrados en tu red</div>
  <div class="card rows">
    ${row("📺 Chromecast «Living»", "Google Cast · se detectó solo", `<button class="btn sm primary" data-add>Agregar</button>`)}
    ${row("🔌 Enchufe Tapo P110", "TP-Link · se detectó solo", `<button class="btn sm primary" data-add>Agregar</button>`)}
  </div>
  <div class="section-title">Tus dispositivos</div>
  ${ROOMS.map(r => `<div class="card room"><div class="room-h">${r.name}<button class="btn sm">Renombrar</button></div>
    ${r.devices.map(d => `<div class="dev"><div class="ic ${d.on ? "on" : ""}">${d.ic}</div>
      <div class="txt"><b>${d.n}</b> <small style="color:var(--muted)">· ${d.st} · ${d.br}</small>
      <div class="aliases">${d.al.map(a => `<span class="chip">"${a}"</span>`).join("")}<span class="chip" style="cursor:pointer">＋ alias</span></div></div>
      ${tog(d.on)}</div>`).join("")}</div>`).join("")}
  <div class="card rows" style="margin-top:6px">
    ${row("Video por defecto", "Dónde pone YouTube o Netflix si no decís dónde", sel(["Esta PC", "Tele de la sala", "Google TV del dormitorio"]))}
    ${row("Abrir Home Assistant", "Para usuarios avanzados: automatizaciones, integraciones raras", `<button class="btn sm">Abrir</button>`)}
  </div>
  <p class="note">Luchi usa <b>Home Assistant</b> por debajo, en tu PC: no hace falta abrirlo ni saber usarlo. Las marcas marcadas como "nube" solo funcionan a través del servidor del fabricante; Luchi avisa antes de conectarlas. Google Home no se puede conectar: no ofrece una forma de hacerlo desde Windows.</p>`;
  $("#addDev").onclick = () => { wiz = { step: 0 }; show("casa"); };
  $$("[data-add]").forEach(b => b.onclick = () => { wiz = { step: 2, brand: "Detectado en tu red" }; show("casa"); });
};
function wizard(c) {
  const steps = `<div class="steps">${[0, 1, 2, 3].map(i => `<span class="${i <= wiz.step ? "on" : ""}"></span>`).join("")}</div>`;
  const back = `<button class="btn" id="wzBack">${wiz.step === 0 ? "Cancelar" : "Atrás"}</button>`;
  if (wiz.step === 0) {
    c.innerHTML = head("Agregar dispositivo", "Elegí la marca. Si no aparece, buscala.") + steps + `
      <input class="input" placeholder="Buscar marca o modelo…" style="width:100%;margin-bottom:14px">
      <div class="brands">${BRANDS.map(([b, s]) => `<button class="brand" data-b="${b}"><b>${b}</b><small>${s}</small></button>`).join("")}</div>
      <div style="margin-top:18px">${back}</div>`;
    $$("[data-b]").forEach(b => b.onclick = () => { wiz = { step: 1, brand: b.dataset.b }; show("casa"); });
  } else if (wiz.step === 1) {
    const cloud = /nube/i.test((BRANDS.find(b => b[0] === wiz.brand) || [])[1] || "");
    c.innerHTML = head(`Conectar ${wiz.brand}`, "Seguí este paso y tocá Continuar.") + steps + `
      <div class="card" style="padding:22px">
        ${cloud ? `<p class="note" style="margin-top:0">⚠️ Esta marca funciona a través de la nube del fabricante: las órdenes salen a internet. ¿Querés seguir igual?</p>` : ""}
        <p style="font-size:16px">${wiz.brand.includes("Hue") ? "Presioná el botón redondo del <b>puente Hue</b>." : wiz.brand.includes("webOS") || wiz.brand.includes("Samsung") ? "Prendé la tele y <b>aceptá el aviso</b> que va a aparecer en la pantalla." : wiz.brand.includes("Android") ? "Escribí el <b>código de 6 dígitos</b> que muestra la tele." : "Ingresá los datos de tu cuenta de la marca."}</p>
        ${wiz.brand.includes("Android") ? `<input class="input" placeholder="123456" style="letter-spacing:.3em;width:160px">` : ""}
        ${!wiz.brand.includes("Hue") && !wiz.brand.includes("webOS") && !wiz.brand.includes("Samsung") && !wiz.brand.includes("Android") ? `<div style="display:flex;gap:10px"><input class="input" placeholder="Usuario o email"><input class="input" type="password" placeholder="Contraseña"></div>` : ""}
        <p style="color:var(--muted);font-size:13px">Buscando en tu red… <span class="chip">● esperando</span></p>
      </div>
      <div style="margin-top:18px;display:flex;gap:10px">${back}<button class="btn primary" id="wzNext">Continuar</button></div>`;
    $("#wzNext").onclick = () => { wiz.step = 2; show("casa"); };
  } else if (wiz.step === 2) {
    c.innerHTML = head("¿Cómo se llama y dónde está?", "Así lo vas a nombrar cuando le hables a Luchi.") + steps + `
      <div class="card rows">
        ${row("Nombre", "", `<input class="input" value="Luz del escritorio">`)}
        ${row("Habitación", "", sel(["Escritorio", "Comedor", "Sala", "Dormitorio", "＋ Nueva habitación"]))}
        ${row("Otras formas de llamarlo", "Separalas con coma", `<input class="input" value="luz del escri, escritorio">`)}
      </div>
      <div style="margin-top:18px;display:flex;gap:10px">${back}<button class="btn primary" id="wzNext">Guardar</button></div>`;
    $("#wzNext").onclick = () => { wiz.step = 3; show("casa"); };
  } else {
    c.innerHTML = head("¡Listo!", "") + steps + `
      <div class="card" style="padding:24px;text-align:center"><div style="font-size:40px">💡</div>
      <p style="font-size:17px">Probalo: <b>"Luchi, prendé la luz del escritorio"</b></p>
      <button class="btn" id="tryIt">Probar ahora</button></div>
      <div style="margin-top:18px"><button class="btn primary" id="wzDone">Terminar</button></div>`;
    $("#tryIt").onclick = () => DEMOS.full();
    $("#wzDone").onclick = () => { wiz = null; show("casa"); toast("Dispositivo agregado"); };
  }
  const bk = $("#wzBack"); if (bk) bk.onclick = () => { if (wiz.step === 0) wiz = null; else wiz.step -= 1; show("casa"); };
}

/* ---------------------------------------------------------------- apps y juegos */
const SOURCES = [["Menú Inicio", 142], ["Steam", 38], ["Epic Games", 12], ["Riot", 2], ["Battle.net", 3], ["EA", 4], ["Ubisoft Connect", 3], ["Google Play Games", 5]];
const APPS = [
  ["Counter-Strike 2", "Steam", ["counter", "cs"]], ["VALORANT", "Riot", ["valo"]], ["League of Legends", "Riot", ["lol", "league"]],
  ["Hollow Knight", "Steam", ["hollow"]], ["Discord", "Menú Inicio", []], ["OBS Studio", "Menú Inicio", ["obs"]],
  ["Blender 5.2", "Menú Inicio", ["blender"]], ["Adobe Photoshop", "Menú Inicio", ["photoshop", "ps"]], ["Godot 4.7", "Menú Inicio", ["godot"]],
  ["Docker Desktop", "Menú Inicio", ["docker"]], ["ComfyUI Desktop", "Menú Inicio", ["comfy"]], ["AION 2", "Epic Games", ["aion"]],
];
VIEWS.apps = c => {
  c.innerHTML = head("Apps y juegos", "Lo que Luchi puede abrir y cerrar por nombre. Se detecta solo; podés agregar apodos.") + `
  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px">${SOURCES.map(([n, k]) => `<span class="chip ok">● ${n} · ${k}</span>`).join("")}</div>
  <div style="display:flex;gap:10px;margin-bottom:12px"><input class="input" placeholder="Buscar…" style="flex:1"><button class="btn">↻ Volver a escanear</button></div>
  <div class="card rows">${APPS.map(([n, s, al]) => row(n, `${s}${al.length ? " · también: " + al.map(a => `"${a}"`).join(", ") : ""}`, `<button class="btn sm">Apodos</button>${tog(true)}`)).join("")}</div>
  <p class="note">El interruptor decide si Luchi puede abrirla. Cerrar siempre es normal (como tocar la ✕), nunca forzado.</p>`;
};

/* ---------------------------------------------------------------- grabaciones */
const RECS = [
  { id: 1, t: "Daily del equipo", d: "1 oct 2026 · 10:02", dur: "18 min", lang: "español", lines: [
    ["00:00:04", "yo", "Buenas, ¿arrancamos?"], ["00:00:07", "otros", "Sí, dale. Ayer terminé el endpoint de pagos y hoy lo paso a staging."],
    ["00:00:15", "yo", "Genial. Yo sigo con la isla de Luchi, me falta el indicador de grabación."], ["00:00:24", "otros", "¿Necesitás ayuda con el audio del sistema?"],
    ["00:00:29", "yo", "Por ahora no, uso WASAPI loopback y anda bien."], ["00:00:35", "otros", "Perfecto. Entonces mañana revisamos el deploy juntos."]] },
  { id: 2, t: "Reunión con cliente", d: "30 sep 2026 · 15:30", dur: "46 min", lang: "inglés", lines: [
    ["00:00:03", "otros", "Hi! Thanks for joining. Shall we go over the timeline?"], ["00:00:09", "yo", "Sure. We plan to ship the first version in November."]] },
  { id: 3, t: "Clase de japonés", d: "28 sep 2026 · 19:00", dur: "1 h 02 min", lang: "japonés", lines: [
    ["00:00:02", "otros", "こんにちは。今日は助詞を勉強しましょう。"], ["00:00:08", "yo", "はい、お願いします。"]] },
];
const TRAD = { en: [
  "Hi, shall we start?", "Sure. Yesterday I finished the payments endpoint and today I'm moving it to staging.",
  "Great. I'm still working on Luchi's island, I'm missing the recording indicator.", "Do you need help with the system audio?",
  "Not for now, I'm using WASAPI loopback and it works fine.", "Perfect. Then tomorrow we review the deploy together."] };
let openRec = null;
VIEWS.grabaciones = c => {
  if (openRec) return recDetail(c, openRec);
  c.innerHTML = head("Grabaciones", "Reuniones grabadas con \"Luchi, grabá esta reunión\". Todo queda en tu PC.") + `
  <div class="rec-list">${RECS.map(r => `<button class="rec-item" data-rec="${r.id}"><div class="ic">●</div><div class="txt"><b>${r.t}</b><br><small>${r.d} · ${r.dur} · ${r.lang}</small></div><span class="chip">Transcripción</span><span style="color:var(--muted)">›</span></button>`).join("")}</div>
  <div class="section-title">Ajustes de grabación</div>
  <div class="card rows">
    ${row("Carpeta", "Documentos\\Luchi\\Grabaciones", `<button class="btn sm">Cambiar</button>`)}
    ${row("Qué se graba", "Tu micrófono y el audio del sistema, en dos pistas (así la transcripción separa \"Yo\" y \"Otros\")", sel(["Micrófono + sistema", "Solo micrófono", "Solo una app (experimental)"]))}
    ${row("Recordarme avisar a los participantes", "En muchos lugares hace falta su consentimiento", tog(true))}
    ${row("Transcribir al terminar", "", tog(true))}
    ${row("Idioma de traducción por defecto", "", sel(["Inglés", "Español", "Portugués", "Japonés", "Francés", "Italiano", "Alemán"]))}
  </div>`;
  $$("[data-rec]").forEach(b => b.onclick = () => { openRec = RECS.find(r => r.id == b.dataset.rec); show("grabaciones"); });
};
function recDetail(c, r) {
  const bars = Array.from({ length: 90 }, (_, i) => `<i class="${i < 30 ? "done" : ""}" style="height:${12 + Math.abs(Math.sin(i * 1.7) * 26 + Math.sin(i * .3) * 8)}px"></i>`).join("");
  c.innerHTML = `<button class="btn sm" id="backRec">‹ Grabaciones</button>` + head(r.t, `${r.d} · ${r.dur} · idioma detectado: ${r.lang}`) + `
  <div class="card"><div class="player"><button class="btn primary">▶</button><span style="font-variant-numeric:tabular-nums;color:var(--muted)">05:31 / 18:04</span><div class="wave">${bars}</div><span class="chip">audio.mp3</span></div></div>
  <div class="card" style="margin-top:12px">
    <div class="trbar"><b style="flex:1">Transcripción</b>
      <span style="color:var(--muted);font-size:13px">Ver en</span>
      <select id="trLang"><option value="orig">Original (${r.lang})</option><option value="en">Inglés</option><option value="pt">Portugués</option><option value="ja">Japonés</option></select>
      <button class="btn sm" id="sum">✨ Resumen</button><button class="btn sm">📂 Abrir carpeta</button><button class="btn sm danger">Borrar</button></div>
    <div class="transcript" id="tr"></div>
  </div>`;
  const draw = lang => {
    $("#tr").innerHTML = r.lines.map(([t, w, txt], i) => {
      const shown = lang === "orig" ? txt : (TRAD[lang] && r.id === 1 ? TRAD[lang][i] : `<span style="color:var(--muted)">[${lang}] </span>${txt}`);
      return `<div class="line"><span class="t">${t}</span><span class="w ${w}">${w === "yo" ? "Yo" : "Otros"}</span><span>${shown}</span></div>`;
    }).join("");
  };
  draw("orig");
  $("#trLang").onchange = e => {
    if (e.target.value === "orig") return draw("orig");
    $("#tr").innerHTML = `<p style="color:var(--muted);padding:14px 0">Traduciendo con el modelo local…</p>`;
    setTimeout(() => { draw(e.target.value); toast(`Guardado como transcripcion.${e.target.value}.txt`); }, 900);
  };
  $("#sum").onclick = () => { $("#tr").insertAdjacentHTML("afterbegin", `<p class="note" style="margin:8px 0 12px"><b>Resumen:</b> el endpoint de pagos pasa hoy a staging; la isla de Luchi solo necesita el indicador de grabación; mañana revisan el deploy juntos.</p>`); };
  $("#backRec").onclick = () => { openRec = null; show("grabaciones"); };
}

/* ---------------------------------------------------------------- privacidad y acerca de */
VIEWS.privacidad = c => {
  c.innerHTML = head("Privacidad", "Todo corre en esta PC. Nada sale a internet salvo lo que vos pedís (abrir YouTube, Netflix, una búsqueda).") + `
  <div class="card rows">
    ${row("Silenciar micrófono", "Luchi no escucha ni su nombre. También desde la bandeja o diciendo \"Luchi, no escuches\"", tog(muted))}
    ${row("Guardar historial de órdenes", "Sirve para mejorar el reconocimiento. Nunca se guarda audio de las órdenes", sel(["7 días", "30 días", "No guardar"]))}
    ${row("Borrar historial", "", `<button class="btn sm danger">Borrar</button>`)}
    ${row("Registros técnicos", "Para diagnosticar errores. Sin audio ni texto de tus órdenes", `<button class="btn sm">Abrir carpeta</button>`)}
  </div>
  <p class="note">🔒 El detector de "Luchi" corre en tu PC y no graba nada hasta escuchar su nombre. Mientras te escucha, la isla está visible.</p>`;
};
VIEWS.acerca = c => {
  c.innerHTML = `<div class="welcome"><img src="../../assets/branding/luchi_portada.png" alt="Luchi"><h1>Luchi</h1>
  <p class="lead">Asistente de voz para Windows · versión 0.1 (prototipo)</p>
  <p>100 % local y 100 % gratis. Hecho con openWakeWord, faster-whisper, Piper, Ollama, Home Assistant y Tauri.</p>
  <p style="color:var(--muted)">Luz + mochi = Luchi 💗</p></div>`;
};

/* ---------------------------------------------------------------- bienvenida */
let wstep = 0;
VIEWS.bienvenida = c => {
  const nav = (next = "Siguiente") => `<div class="row-c"><button class="btn" id="wBack">${wstep === 0 ? "Más tarde" : "Atrás"}</button><button class="btn primary" id="wNext">${next}</button></div>`;
  const dots = `<div class="steps" style="max-width:240px;margin:18px auto">${[0, 1, 2, 3, 4].map(i => `<span class="${i <= wstep ? "on" : ""}"></span>`).join("")}</div>`;
  if (wstep === 0) c.innerHTML = `<div class="welcome"><img src="../../assets/branding/luchi_portada.png" alt=""><h1>¡Hola! Soy Luchi</h1>
    <p class="lead">Tu asistente de voz. Manejo la PC, la tele y las luces sin que toques nada, y puedo grabar tus reuniones. Todo queda en tu PC.</p>${dots}${nav("Empezar")}</div>`;
  if (wstep === 1) c.innerHTML = `<div class="welcome"><h1>Tu micrófono</h1><p class="lead">Elegí el micrófono y decí algo para probarlo.</p>
    ${sel(["Micrófono (USB Audio Device)", "Auriculares (Realtek)"])}<div class="big-meter"><i id="wl"></i></div>
    <p>Ahora decí <b>"Luchi"</b>… <span class="chip ok" id="wok" style="opacity:0">✓ Te escuché</span></p>${dots}${nav()}</div>`;
  if (wstep === 2) c.innerHTML = `<div class="welcome"><h1>Tu casa</h1><p class="lead">Si tenés luces o teles inteligentes, las conectamos ahora. Podés hacerlo después en Ajustes.</p>
    <div class="card" style="padding:18px;text-align:left"><b>🏠 Home Assistant</b> <span class="chip warn">● no encontrado</span><p style="color:var(--muted);margin:6px 0 12px">Luchi lo usa por debajo para hablar con tus dispositivos. Lo instalamos en tu PC con un clic.</p><button class="btn primary">Instalar y buscar dispositivos</button></div>${dots}${nav()}</div>`;
  if (wstep === 3) c.innerHTML = `<div class="welcome" style="max-width:760px"><h1>¿Cómo querés que sea?</h1><p class="lead">Elegí uno para empezar. Después podés cambiar todo en "Tu Luchi".</p><div class="opts" id="wPresets"></div>${dots}${nav()}</div>`;
  if (wstep === 4) c.innerHTML = `<div class="welcome"><h1>¡Listo!</h1><p class="lead">Probá decir:</p>
    <div class="card rows" style="text-align:left">${row('"Luchi, prendé la luz del comedor"', "", "")}${row('"Luchi, poné música de Daft Punk"', "", "")}${row('"Luchi, quiero jugar Hollow Knight"', "", "")}${row('"Luchi, grabá esta reunión"', "", "")}</div>
    ${dots}${nav("Terminar")}</div>`;
  if (wstep === 1) {
    const wl = $("#wl"); let n = 0;
    const iv = setInterval(() => { if (!document.body.contains(wl)) return clearInterval(iv); wl.style.width = `${8 + Math.random() * 70}%`; if (++n === 25) $("#wok").style.opacity = 1; }, 120);
  }
  if (wstep === 3) {
    const g = $("#wPresets");
    for (const [id, p] of Object.entries(C.presets).slice(0, 6)) {
      const b = document.createElement("button"); b.className = "opt" + (id === "clasica" ? " on" : "");
      b.append(luchiCanvas({ ...DEFAULT_STYLE, ...p }, "neutral")); b.append(id);
      b.onclick = () => { $$(".opt", g).forEach(x => x.classList.toggle("on", x === b)); style = { ...DEFAULT_STYLE, ...p, flash: p.flash || [] }; store("luchi.style", style); };
      g.append(b);
    }
  }
  $("#wNext").onclick = () => { if (wstep === 4) { wstep = 0; show("general"); DEMOS.full(); return; } wstep++; show("bienvenida"); };
  $("#wBack").onclick = () => { if (wstep === 0) { $("#win").classList.remove("open"); return; } wstep--; show("bienvenida"); };
};

/* ================================================================ arranque */
$("#trayBtn").onclick = e => { e.stopPropagation(); $("#trayMenu").classList.toggle("open"); $("#trayBtn").classList.toggle("on"); };
$("#muteBtn").onclick = () => DEMOS.dormido();
$("#themeBtn").onclick = () => { const r = document.documentElement; r.dataset.theme = r.dataset.theme === "light" ? "dark" : "light"; };
$("#protoMin").onclick = () => $("#proto").classList.toggle("collapsed");
setInterval(() => { const d = new Date(); $("#clock").textContent = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`; }, 10000);

/* ================================================================ funciones aprobadas (v3.3) */

/* ---------------------------------------------------------------- demos nuevas de la isla */
Object.assign(DEMOS, {
  recordatorio() {
    appear(() => {
      anim("hablando");
      say(`<span class="who">⏰ Recordatorio</span>Pasaron 10 minutos: sacar la pizza del horno.<div class="choices"><span>"Posponé 5 minutos"</span><span>"Listo"</span></div>`);
      later(3600, () => { anim("feliz"); say(null); later(2300, hide); });
    });
  },
  corregir() {
    appear(() => listenThen("eso no es lo que quería", () => {
      anim("apenado"); say(`<span class="who">Luchi</span>Perdón. Volví a apagar la luz del comedor. ¿Qué querías?`);
      later(2800, () => listenThen("la luz del escritorio", () => {
        anim("hablando"); say(`<span class="who">Luchi</span>Listo, prendí la luz del escritorio. Lo anoto para la próxima.`);
        later(2600, () => { anim("feliz"); say(null); later(2300, hide); });
      }));
    }));
  },
  dictado() {
    appear(() => listenThen("escribí: llego en 10 minutos", () => {
      anim("hablando"); say(`<span class="who">Escribiendo en Discord</span>llego en 10 minutos`);
      later(2400, () => { anim("feliz"); say(null); later(2200, hide); });
    }));
  },
  preguntar() {
    appear(() => listenThen("¿cuántos gramos tiene una taza de harina?", () => {
      anim("pensando"); say(`<span class="who">Pensando</span>…`);
      later(1100, () => {
        anim("hablando"); say(`<span class="who">Luchi</span>Más o menos 125 gramos.`);
        later(2300, () => { anim("feliz"); say(null); later(2200, hide); });
      });
    }));
  },
});

/* ---------------------------------------------------------------- recordatorios */
const REMINDERS = [
  { ic: "⏱️", t: "Sacar la pizza del horno", w: "Temporizador · en 7 min", kind: "timer" },
  { ic: "⏰", t: "Daily del equipo", w: "Hoy 10:00 · todos los días hábiles", kind: "rem" },
  { ic: "🧺", t: "Sacar la ropa del lavarropas", w: "Mañana 09:00", kind: "rem" },
];
VIEWS.recordatorios = c => {
  c.innerHTML = head("Recordatorios", "\"Luchi, avisame en 10 minutos\" o \"recordame mañana a las 9…\". Luchi aparece y te lo dice.") + `
  <div class="card" style="border-color:#f2c46d55">
    <div class="list-item missed"><div class="ic">⚠️</div><div class="txt"><b>Mientras la PC estaba apagada venció 1 recordatorio</b><br><small>"Llamar al dentista" · ayer 18:00. Luchi te lo dijo al prender la PC.</small></div><button class="btn sm">Ya está</button><button class="btn sm">Posponer</button></div>
  </div>
  <div class="section-title">Próximos</div>
  <div class="card">${REMINDERS.map(r => `<div class="list-item"><div class="ic">${r.ic}</div><div class="txt"><b>${r.t}</b><br><small>${r.w}</small></div><button class="btn sm">Editar</button><button class="btn sm danger">Borrar</button></div>`).join("")}</div>
  <div style="margin-top:12px"><button class="btn primary" id="newRem">＋ Nuevo recordatorio</button> <button class="btn" data-demo="recordatorio">Ver cómo avisa</button></div>
  <div class="section-title">Ajustes</div>
  <div class="card rows">
    ${row("Despertar la PC de la suspensión para avisar", "Funciona si la PC está suspendida, no si está apagada", tog(false))}
    ${row("Al prender la PC, contarme lo que venció", "Si estuvo apagada cuando tocaba avisar", tog(true))}
    ${row("Sonido del aviso", "", sel(["Campanita", "Suave", "Solo voz"]))}
    ${row("Posponer por defecto", "", sel(["5 minutos", "10 minutos", "15 minutos"]))}
  </div>
  <p class="note">Los recordatorios viven en tu PC: si está apagada no puede avisarte en el momento. Para eso conviene usarlos mientras usás la PC (temporizadores, "en una hora…").</p>`;
  $("#newRem").onclick = () => toast("Tip: también podés decir \"Luchi, recordame…\"");
};

/* ---------------------------------------------------------------- escenas y atajos de voz */
const SCENES = [
  { n: "Modo stream", tr: "modo stream", steps: ["Abrir OBS Studio", "Abrir Discord", "Luces del escritorio al 30 %", "Silenciar notificaciones de Windows"] },
  { n: "Modo cine", tr: "modo cine", steps: ["Prender la tele de la sala", "Apagar la luz del comedor", "Lámpara de pie al 10 %"] },
  { n: "Buenas noches", tr: "buenas noches", steps: ["Apagar todas las luces", "Apagar la tele", "Suspender la PC en 5 minutos (con confirmación)"] },
];
let editScene = null;
VIEWS.escenas = c => {
  if (editScene) return sceneEditor(c, editScene);
  c.innerHTML = head("Escenas y atajos de voz", "Una frase, varias acciones. Sin código.") + `
  <div class="card">${SCENES.map((s, i) => `<div class="list-item"><div class="ic">▶️</div><div class="txt"><b>${s.n}</b><br><small>"Luchi, ${s.tr}" · ${s.steps.length} acciones</small></div><button class="btn sm" data-try="${i}">Probar</button><button class="btn sm" data-edit="${i}">Editar</button></div>`).join("")}</div>
  <div style="margin-top:12px"><button class="btn primary" id="newScene">＋ Nueva escena</button></div>
  <div class="section-title">Horarios</div>
  <div class="card rows">
    ${row("Buenas noches", "Todos los días a las 23:30", tog(false))}
    ${row("Modo cine", "Sin horario", `<button class="btn sm">Agregar horario</button>`)}
  </div>`;
  $$("[data-edit]").forEach(b => b.onclick = () => { editScene = SCENES[b.dataset.edit]; show("escenas"); });
  $$("[data-try]").forEach(b => b.onclick = () => toast(`Ejecutando "${SCENES[b.dataset.try].n}"…`));
  $("#newScene").onclick = () => { editScene = { n: "Nueva escena", tr: "", steps: [] }; show("escenas"); };
};
function sceneEditor(c, sc) {
  c.innerHTML = `<button class="btn sm" id="scBack">‹ Escenas</button>` + head(sc.n, "Qué decís y qué hace Luchi, en orden.") + `
  <div class="section-title" style="margin-top:0">Cuando diga</div>
  <input class="trigger" value="${sc.tr}" placeholder="por ejemplo: modo stream">
  <small style="color:var(--muted);display:block;margin-top:6px">Se dice después de "Luchi". También podés sumar otras frases para lo mismo.</small>
  <div class="section-title">Hacer esto</div>
  <div id="steps">${sc.steps.map((st, i) => `<div class="step"><span class="n">${i + 1}</span><span class="grow">${st}</span><button class="btn sm">↑</button><button class="btn sm">↓</button><button class="btn sm danger">✕</button></div>`).join("")}</div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:6px">
    <button class="btn sm">💡 Dispositivo de la casa</button><button class="btn sm">🖥️ Abrir o cerrar app</button><button class="btn sm">🔊 Volumen o salida de audio</button>
    <button class="btn sm">🎵 Reproducir algo</button><button class="btn sm">⏳ Esperar</button><button class="btn sm">💬 Que Luchi diga algo</button>
  </div>
  <div style="margin-top:20px;display:flex;gap:10px"><button class="btn" id="scTry">Probar</button><button class="btn primary" id="scSave">Guardar</button></div>`;
  $("#scBack").onclick = () => { editScene = null; show("escenas"); };
  $("#scTry").onclick = () => toast(`Ejecutando "${sc.n}"…`);
  $("#scSave").onclick = () => { editScene = null; show("escenas"); toast("Escena guardada"); };
}

/* ---------------------------------------------------------------- historial */
const HIST = [
  ["15:42", "prendé la luz del escritorio", "Prendió: Luz del escritorio", "ok", "Corregido por voz"],
  ["15:41", "prendé la luz", "Prendió: Luz del comedor", "fix", "Dijiste \"eso no es lo que quería\""],
  ["15:30", "poné lofi", "YouTube en esta PC: lofi hip hop radio", "ok", ""],
  ["15:12", "abrí Hollow Knight", "Preguntó cuál · abrió Hollow Knight (Steam)", "ok", ""],
  ["14:58", "poné Interestelar en la tele", "No encontró la tele (apagada)", "err", ""],
  ["14:20", "grabá esta reunión", "Grabación de 18 min · transcripción lista", "ok", ""],
];
VIEWS.historial = c => {
  c.innerHTML = head("Historial", "Qué pediste, qué entendió Luchi y qué hizo.") + `
  <div style="display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap"><input class="input" placeholder="Buscar…" style="flex:1">
    <div class="seg"><button class="on">Todo</button><button>Con errores</button><button>Corregidos</button></div></div>
  <div class="card hist">${HIST.map(([w, said, did, st, note]) => `<div class="line2"><span class="when">${w}</span>
    <div><div class="said">"${said}"</div><div class="did">${st === "err" ? "⚠️ " : st === "fix" ? "↩️ " : "✓ "}${did}${note ? ` · <i>${note}</i>` : ""}</div></div>
    ${st === "ok" ? `<button class="btn sm" data-wrong>Esto estuvo mal</button>` : `<span class="chip ${st === "err" ? "warn" : ""}">${st === "err" ? "Error" : "Corregido"}</span>`}</div>`).join("")}</div>
  <p class="note">También podés decir <b>"Luchi, eso no es lo que quería"</b> o <b>"eso está mal"</b> justo después de una orden: Luchi deshace lo que se pueda (apagar lo que prendió, cerrar lo que abrió), te pregunta qué querías y lo anota. Cada corrección se suma al set de pruebas para que se equivoque menos.
  <button class="btn sm" data-demo="corregir" style="margin-left:6px">Ver cómo funciona</button></p>
  <div class="card rows" style="margin-top:12px">
    ${row("Guardar historial", "Nunca se guarda audio, solo el texto", sel(["7 días", "30 días", "No guardar"]))}
    ${row("Borrar historial", "", `<button class="btn sm danger">Borrar</button>`)}
  </div>`;
  $$("[data-wrong]").forEach(b => b.onclick = () => { b.outerHTML = `<span class="chip">Anotado · ¿qué querías?</span>`; toast("Gracias: Luchi lo usa para mejorar"); });
};

/* ---------------------------------------------------------------- cuenta y sincronización */
let signedIn = false;
VIEWS.cuenta = c => {
  c.innerHTML = head("Cuenta y sincronización", "Opcional. Sin cuenta, todo se guarda solo en esta PC.") + `
  <div class="card" style="padding:20px;display:flex;align-items:center;gap:18px">
    ${signedIn
      ? `<div style="width:48px;height:48px;border-radius:50%;background:var(--lavender);display:grid;place-items:center;font-weight:700;color:#2a2238">T</div>
         <div style="flex:1"><b>tu.nombre@gmail.com</b><br><small style="color:var(--muted)">Sincronizado hace 2 minutos · en tu Google Drive (carpeta oculta de la app)</small></div>
         <button class="btn" id="syncNow">↻ Sincronizar ahora</button><button class="btn danger" id="signOut">Cerrar sesión</button>`
      : `<div style="flex:1"><b>Guardá tus preferencias en tu cuenta de Google</b><br><small style="color:var(--muted)">Para tener tu Luchi y tus ajustes en otra PC o recuperarlos si reinstalás.</small></div>
         <button class="google" id="signIn"><i></i>Iniciar sesión con Google</button>`}
  </div>
  <div class="section-title">Qué se sincroniza</div>
  <div class="card rows">
    ${row("Diseño de Tu Luchi", "Color, ojos, boca, tatuajes, accesorios", tog(true))}
    ${row("Ajustes", "Isla, voz, sensibilidad, atajos", tog(true))}
    ${row("Apodos de apps y dispositivos", "", tog(true))}
    ${row("Escenas y recordatorios", "", tog(true))}
    ${row("Grabaciones y transcripciones", "Desactivado por defecto: son datos sensibles", tog(false))}
  </div>
  <p class="note">Luchi usa una <b>carpeta oculta de la app</b> en tu Google Drive: solo puede ver lo que guarda ella misma, no el resto de tus archivos. Nunca se suben contraseñas, tokens ni el historial de órdenes. Es la única función que usa internet de forma permanente, y solo si iniciás sesión.</p>
  <div class="section-title">Copia local (sin cuenta)</div>
  <div class="card rows">
    ${row("Exportar a un archivo", "Guarda ajustes y diseño en un .luchi para llevar o compartir", `<button class="btn sm" id="exp">Exportar</button>`)}
    ${row("Importar desde un archivo", "", `<button class="btn sm" id="imp">Importar</button>`)}
    ${row("Copia automática local", "Cada semana en Documentos\\Luchi\\Copias", tog(true))}
  </div>`;
  const si = $("#signIn"); if (si) si.onclick = () => { signedIn = true; show("cuenta"); toast("Sesión iniciada: tus preferencias se guardan en tu Drive"); };
  const so = $("#signOut"); if (so) so.onclick = () => { signedIn = false; show("cuenta"); toast("Sesión cerrada: todo queda en esta PC"); };
  const sn = $("#syncNow"); if (sn) sn.onclick = () => toast("Sincronizado");
  $("#exp").onclick = () => toast("Guardado como mi-luchi.luchi");
  $("#imp").onclick = () => toast("Elegí un archivo .luchi");
};

/* ---------------------------------------------------------------- estado del sistema */
const SERVICES = [
  ["🎙️", "Micrófono", "USB Audio Device · nivel OK", "ok"],
  ["👂", "Detector de \"Luchi\"", "openWakeWord · 0,4 % de CPU", "ok"],
  ["📝", "Voz a texto", "faster-whisper large-v3-turbo · GPU", "ok"],
  ["🧠", "Modelo de lenguaje", "Ollama · qwen3:8b cargado", "ok"],
  ["🔊", "Voz de Luchi", "Piper · voz 1", "ok"],
  ["🏠", "Home Assistant", "VM Hyper-V · responde en 38 ms", "ok"],
  ["📺", "Tele de la sala", "Apagada · no responde", "warn"],
];
VIEWS.estado = c => {
  c.innerHTML = head("Estado del sistema", "Si algo no anda, empezá por acá.") + `
  <div class="status-grid">${SERVICES.map(([ic, n, d, st]) => `<div class="card status-card"><div class="top"><b>${ic} ${n}</b><span class="chip ${st === "ok" ? "ok" : "warn"}">● ${st === "ok" ? "OK" : "Revisar"}</span></div><small>${d}</small></div>`).join("")}
    <div class="card status-card"><div class="top"><b>🎮 GPU · RTX 3080</b><span class="chip ok">● OK</span></div><small>VRAM 8,9 / 12 GB (modelo 6,1 · whisper 2,2 · otros 0,6)</small><div class="bar"><i style="width:74%"></i></div></div>
  </div>
  <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap"><button class="btn primary" id="diag">🩺 Diagnóstico guiado</button><button class="btn">Reiniciar servicios</button><button class="btn">Abrir registros</button></div>
  <div id="diagOut"></div>
  <div class="card rows" style="margin-top:14px">
    ${row("Modo juego automático", "Con un juego a pantalla completa: libera el modelo de la GPU y baja la sensibilidad", tog(true))}
    ${row("Latencia de la última orden", "Voz → acción: 1,2 s (objetivo < 1,5 s con router)", `<span class="chip ok">Bien</span>`)}
  </div>`;
  $("#diag").onclick = () => {
    $("#diagOut").innerHTML = `<div class="card" style="margin-top:12px;padding:16px">
      <b>Tele de la sala no responde</b>
      <ol style="color:var(--muted);margin:8px 0 0;padding-left:18px;line-height:1.7">
        <li>¿Está prendida o en espera? Algunas teles se desconectan de la red al apagarse del todo.</li>
        <li>En la tele, activá "Encender por red" (Wake on LAN) para que Luchi pueda prenderla.</li>
        <li>Probá de nuevo: <button class="btn sm">Probar conexión</button></li>
      </ol></div>`;
  };
};

/* ---------------------------------------------------------------- laboratorio del personaje (desarrollo) */
const LAB_EMOS = ["idle", "aparecer", "atento", "escuchando", "pensando", "hablando", "feliz", "guino", "pregunta", "apenado", "cansado", "mareado", "enojado", "dormido", "amor", "esconderse"];
const LAB_PARAMS = [["open_l", 0, 1, 1], ["open_r", 0, 1, 1], ["look_x", -20, 20, 0], ["look_y", -15, 15, 0], ["eye_scale", 0.8, 1.2, 1],
  ["lid_l / lid_r", 0, 0.6, 0], ["lid_tilt", -20, 30, 0], ["blush", 0, 1.8, 1], ["talk_open", 0, 1, 0], ["body sx", 0.7, 1.3, 1], ["body sy", 0.7, 1.3, 1], ["lift", 0, 60, 3], ["rot", -15, 15, 0]];
let labEmo = "idle";
VIEWS.laboratorio = c => {
  c.innerHTML = head("Laboratorio del personaje", "Herramienta de desarrollo: disparar emociones y mover parámetros del renderer. No aparece en la versión para usuarios.") + `
  <div class="lab">
    <div><div class="view"><img id="labImg" src="${ANIM}${labEmo}.webp" alt=""></div>
      <div class="seg" style="margin-top:10px"><button class="on">Prototipo (referencia)</button><button>Renderer de la app</button><button>Diferencia</button></div>
      <small style="display:block;color:var(--muted);margin-top:8px">En la app, "Diferencia" resalta en rojo los píxeles que no coinciden con el prototipo.</small></div>
    <div>
      <div class="emos" id="emos">${LAB_EMOS.map(e => `<button class="${e === labEmo ? "on" : ""}" data-e="${e}">${e}</button>`).join("")}</div>
      <div class="card" style="padding:14px 18px"><b style="font-size:13px">Parámetros de expresión y del cuerpo</b>
        ${LAB_PARAMS.map(([n, a, b, v]) => `<div class="param"><span>${n}</span><input type="range" min="${a}" max="${b}" step="0.01" value="${v}"><span style="color:var(--muted)">${v}</span></div>`).join("")}
        <div style="display:flex;gap:8px;margin-top:8px"><button class="btn sm">Copiar como JSON</button><button class="btn sm">Restablecer</button><button class="btn sm">⏸ Pausa</button><button class="btn sm">Cuadro a cuadro</button></div>
      </div>
      <div class="card rows" style="margin-top:12px">
        ${row("Estilo", "Probar cualquier combinación de Tu Luchi", `<button class="btn sm" data-view="tuluchi">Abrir editor</button>`)}
        ${row("Simular datos en vivo", "Nivel de micrófono y amplitud de la voz de Luchi", tog(true))}
        ${row("Tests visuales", "16 emociones · 0 diferencias por encima de la tolerancia", `<span class="chip ok">✓ Pasan</span>`)}
      </div>
    </div>
  </div>`;
  $("#emos").onclick = e => { const b = e.target.closest("button"); if (!b) return; labEmo = b.dataset.e; $$("#emos button").forEach(x => x.classList.toggle("on", x === b)); $("#labImg").src = `${ANIM}${labEmo}.webp?${Date.now()}`; };
  $$(".param input").forEach(i => i.oninput = () => { i.nextElementSibling.textContent = (+i.value).toFixed(2); });
};

/* ---------------------------------------------------------------- ampliaciones de pantallas existentes */
const _general = VIEWS.general;
VIEWS.general = c => {
  _general(c);
  c.insertAdjacentHTML("beforeend", `<div class="section-title">Accesibilidad</div>
  <div class="card rows">
    ${row("Subtítulos grandes", "El texto de lo que dice Luchi se ve más grande", tog(false))}
    ${row("Dejar los subtítulos visibles", "Cuánto tiempo queda el texto en pantalla después de hablar", sel(["Lo normal", "5 segundos más", "Hasta que lo cierre"]))}
    ${row("Alto contraste en la isla", "Globo con borde y texto más marcados", tog(false))}
  </div>`);
};
const _voz = VIEWS.voz;
VIEWS.voz = c => {
  _voz(c);
  c.insertAdjacentHTML("beforeend", `<div class="section-title">Dictado</div>
  <div class="card rows">
    ${row("Escribir en la app activa", "\"Luchi, escribí: …\" escribe el texto donde esté el cursor", tog(true))}
    ${row("Confirmar antes de enviar", "En chats, Luchi escribe pero no aprieta Enter salvo que digas \"y mandalo\"", tog(true))}
    ${row("Puntuación automática", "", tog(true))}
    ${row("Probar", "", `<button class="btn sm" data-demo="dictado">Ver cómo funciona</button>`)}
  </div>
  <div class="section-title">Preguntas generales</div>
  <div class="card rows">
    ${row("Responder preguntas", "Con el modelo local, sin internet. Respuestas cortas en voz", tog(true))}
    ${row("Largo de las respuestas", "", seg(["Muy cortas", "Cortas", "Detalladas"], 1))}
    ${row("Probar", "", `<button class="btn sm" data-demo="preguntar">"¿Cuántos gramos tiene una taza de harina?"</button>`)}
  </div>`);
};
const _apps = VIEWS.apps;
VIEWS.apps = c => {
  _apps(c);
  const h = $("h1", c); if (h) h.textContent = "Apps y sistema";
  c.insertAdjacentHTML("beforeend", `<div class="section-title">Acciones del sistema</div>
  <div class="card rows">
    ${row("Cambiar la salida de audio", "\"Luchi, pasá el audio a los auriculares\"", `<span class="chip">Auriculares (Realtek) · Parlantes</span>${tog(true)}`)}
    ${row("Capturas de pantalla", "\"Luchi, sacá una captura\" · se guardan en Imágenes\\Capturas", tog(true))}
    ${row("Carpetas favoritas", "\"Luchi, abrí descargas\"", `<span class="chip">"descargas"</span><span class="chip">"proyectos"</span><button class="btn sm">＋</button>`)}
    ${row("Bloquear la PC", "\"Luchi, bloqueá la compu\"", tog(true))}
    ${row("Suspender o apagar", "Siempre pide confirmación en voz", tog(true))}
  </div>`);
};

/* enlaces directos: index.html#<pantalla> (#tuluchi:accesorios abre una pestaña del editor), #isla (Luchi visible) */
function fromHash() {
  const [h, tab] = location.hash.slice(1).split(":");
  if (h === "tuluchi" && tab) edTab = tab;
  if (VIEWS[h]) openWin(h);
  else if (h === "isla") DEMOS.compania();
}
window.addEventListener("hashchange", fromHash);
fromHash();
