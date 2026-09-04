/* ===== ink: Apple Pencil / pointer drawing on SVG overlays =====
   Overlays never take pointer events themselves; a document-level controller routes
   pen (and, optionally, finger) input to the .inkhost under the pointer. Fingers keep
   scrolling and tapping buttons as usual. */
const Ink = (() => {
  const PEN_COLORS = ['#1b1f26', '#c93c3c', '#1f5fbf', '#2e8b57', '#d98a00'];
  const MARKER_COLORS = ['#ffe873', '#ffb3c6', '#a8d4ff', '#b9f0b9'];
  const WIDTHS = [1.6, 2.5, 4];
  let penMode = false;
  const tool = () => S.settings.tool || 'pen';
  const SVGNS = 'http://www.w3.org/2000/svg';

  function pathD(pts) {
    if (pts.length < 2) return '';
    if (pts.length === 2) return 'M' + pts[0] + ' ' + pts[1] + ' l0.1 0';
    let d = 'M' + pts[0] + ' ' + pts[1];
    if (pts.length === 4) return d + ' L' + pts[2] + ' ' + pts[3];
    for (let i = 2; i < pts.length - 2; i += 2) {
      const mx = (pts[i] + pts[i + 2]) / 2, my = (pts[i + 1] + pts[i + 3]) / 2;
      d += ' Q' + pts[i] + ' ' + pts[i + 1] + ' ' + mx.toFixed(1) + ' ' + my.toFixed(1);
    }
    d += ' L' + pts[pts.length - 2] + ' ' + pts[pts.length - 1];
    return d;
  }
  function strokeEl(st) {
    const p = document.createElementNS(SVGNS, 'path');
    p.setAttribute('d', pathD(st.p));
    p.setAttribute('stroke', st.c);
    p.setAttribute('stroke-width', st.w);
    if (st.t === 'marker') { p.setAttribute('class', 'marker'); p.setAttribute('stroke-opacity', '0.55'); }
    return p;
  }
  /** attach an ink surface to a host element (.inkhost). getData()->{w,strokes}|undefined, onChange(data) */
  function attach(host, getData, onChange, opts) {
    opts = opts || {};
    host.classList.add('inkhost');
    if (opts.always) host.classList.add('always');
    const svg = document.createElementNS(SVGNS, 'svg');
    svg.setAttribute('class', 'ink');
    const g = document.createElementNS(SVGNS, 'g');
    svg.appendChild(g);
    host.appendChild(svg);
    let data = null, scale = 1;
    function baseW() { return opts.fixedW || host.clientWidth || 1; }
    function render() {
      data = getData() || { w: 0, strokes: [] };
      const cw = host.clientWidth || 1;
      scale = opts.fixedW ? cw / opts.fixedW : ((data.w && data.w > 0) ? cw / data.w : 1);
      g.setAttribute('transform', 'scale(' + scale.toFixed(4) + ')');
      g.innerHTML = '';
      (data.strokes || []).forEach(st => g.appendChild(strokeEl(st)));
    }
    render();
    let cur = null, curEl = null, erasing = false;
    const pt = (e) => { const r = svg.getBoundingClientRect(); return [+((e.clientX - r.left) / scale).toFixed(1), +((e.clientY - r.top) / scale).toFixed(1)]; };
    function eraseAt(x, y) {
      const rr = 12 / scale, r2 = rr * rr; let changed = false;
      data.strokes = (data.strokes || []).filter(st => { for (let i = 0; i < st.p.length; i += 2) { const dx = st.p[i] - x, dy = st.p[i + 1] - y; if (dx * dx + dy * dy < r2) { changed = true; return false; } } return true; });
      if (changed) { onChange(data); render(); }
    }
    const api = {
      svg, host, render,
      down(e) {
        data = getData() || { w: 0, strokes: [] };
        if (!(data.strokes || []).length || !data.w) { data.w = baseW(); scale = opts.fixedW ? (host.clientWidth || 1) / opts.fixedW : 1; g.setAttribute('transform', 'scale(' + scale.toFixed(4) + ')'); }
        const [x, y] = pt(e);
        if (tool() === 'eraser') { erasing = true; eraseAt(x, y); return; }
        const pressure = (e.pointerType === 'pen' && e.pressure) ? (0.75 + e.pressure * 0.5) : 1;
        const w = tool() === 'marker' ? 14 : +((S.settings.penWidth || 2.5) * pressure).toFixed(1);
        cur = { c: tool() === 'marker' ? (S.settings.markerColor || MARKER_COLORS[0]) : (S.settings.penColor || PEN_COLORS[0]), w, t: tool(), p: [x, y] };
        curEl = strokeEl(cur); g.appendChild(curEl);
      },
      move(e) {
        if (erasing) { const [x, y] = pt(e); eraseAt(x, y); return; }
        if (!cur) return;
        const evs = e.getCoalescedEvents ? e.getCoalescedEvents() : [e];
        evs.forEach(ev => { const [x, y] = pt(ev); const n = cur.p.length; if (n >= 2 && Math.abs(cur.p[n - 2] - x) < 0.5 && Math.abs(cur.p[n - 1] - y) < 0.5) return; cur.p.push(x, y); });
        curEl.setAttribute('d', pathD(cur.p));
      },
      up() {
        if (erasing) { erasing = false; return; }
        if (!cur) return;
        if (cur.p.length === 2) cur.p.push(cur.p[0] + 0.6, cur.p[1]);
        data.strokes = data.strokes || []; data.strokes.push(cur);
        cur = null; curEl = null;
        onChange(data); render();
      },
      undo() { data = getData() || { strokes: [] }; if (data.strokes && data.strokes.length) { data.strokes.pop(); onChange(data); render(); } },
      clear() { data = getData() || { strokes: [] }; data.strokes = []; onChange(data); render(); },
      hasInk() { const d = getData(); return !!(d && d.strokes && d.strokes.length); }
    };
    host._ink = api;
    return api;
  }

  /* ---- document-level routing ---- */
  let active = null; // {api, pointerId}
  let penTapTs = 0;
  function canDraw(e, host) {
    const always = host.classList.contains('always');
    if (!(penMode || always)) return false;
    if (e.pointerType === 'touch' && !S.settings.fingerDraw) return false;
    return true;
  }
  document.addEventListener('touchstart', e => {
    const host = e.target.closest && e.target.closest('.inkhost'); if (!host) return;
    const stylus = Array.from(e.changedTouches).some(t => t.touchType === 'stylus');
    const always = host.classList.contains('always');
    if ((stylus && (penMode || always)) || (S.settings.fingerDraw && (penMode || always))) { if (!e.target.closest('button, select, input, textarea, a')) e.preventDefault(); }
  }, { passive: false });
  document.addEventListener('touchmove', e => { if (active) e.preventDefault(); }, { passive: false });
  document.addEventListener('pointerdown', e => {
    const host = e.target.closest && e.target.closest('.inkhost'); if (!host || !host._ink) return;
    if (e.target.closest('button, select, input, textarea, a, .sc-tools')) return;
    if (!canDraw(e, host)) return;
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    e.preventDefault();
    Ink.lastHost = host;
    active = { api: host._ink, id: e.pointerId };
    if (e.pointerType === 'pen') penTapTs = Date.now();
    try { host.setPointerCapture(e.pointerId); } catch (err) {}
    host._ink.down(e);
  }, { passive: false });
  document.addEventListener('pointermove', e => { if (active && e.pointerId === active.id) { e.preventDefault(); active.api.move(e); } }, { passive: false });
  const endStroke = e => { if (active && e.pointerId === active.id) { active.api.up(e); active = null; if (e.pointerType === 'pen') penTapTs = Date.now(); } };
  document.addEventListener('pointerup', endStroke); document.addEventListener('pointercancel', endStroke);
  // in pen mode, a pen tap must not also trigger a click on the text below
  document.addEventListener('click', e => { if (penMode && Date.now() - penTapTs < 400 && !e.target.closest('button, select, input, textarea, a, #pen-toolbar')) { e.stopPropagation(); e.preventDefault(); } }, true);

  /* pen toolbar */
  const bar = () => $('#pen-toolbar');
  function renderBar() {
    const b = bar(); if (!b) return;
    const t = tool();
    b.innerHTML = '' +
      '<button data-tool="pen" class="' + (t === 'pen' ? 'on' : '') + '">✎ ペン</button>' +
      '<button data-tool="marker" class="' + (t === 'marker' ? 'on' : '') + '">▬ マーカー</button>' +
      '<button data-tool="eraser" class="' + (t === 'eraser' ? 'on' : '') + '">◻ 消しゴム</button>' +
      '<span class="sep"></span>' +
      (t === 'marker' ? MARKER_COLORS.map(c => '<button class="sw ' + ((S.settings.markerColor || MARKER_COLORS[0]) === c ? 'on' : '') + '" data-mcolor="' + c + '" style="background:' + c + '" aria-label="色"></button>').join('')
        : PEN_COLORS.map(c => '<button class="sw ' + ((S.settings.penColor || PEN_COLORS[0]) === c ? 'on' : '') + '" data-color="' + c + '" style="background:' + c + '" aria-label="色"></button>').join('')) +
      '<span class="sep"></span>' +
      WIDTHS.map(w => '<button class="wd ' + ((S.settings.penWidth || 2.5) === w ? 'on' : '') + '" data-width="' + w + '" aria-label="太さ"><i style="width:' + (w * 3) + 'px;height:' + (w * 3) + 'px;' + ((S.settings.penWidth || 2.5) === w ? 'background:#1b1f26' : '') + '"></i></button>').join('') +
      '<span class="sep"></span>' +
      '<button data-act="undo">↶ 戻す</button>' +
      '<button data-act="finger" class="' + (S.settings.fingerDraw ? 'on' : '') + '">☝ 指でも書く</button>' +
      '<button data-act="close">✓ 終了</button>';
  }
  function setPenMode(on) {
    penMode = on;
    document.body.classList.toggle('pen-on', on);
    document.body.classList.toggle('finger', !!S.settings.fingerDraw);
    bar().hidden = !on;
    if (on) renderBar();
    $$('[data-act="pen"]').forEach(b => b.classList.toggle('on', on));
    if (on) { const sel = window.getSelection(); if (sel) sel.removeAllRanges(); HL.hide(); }
  }
  document.addEventListener('click', e => {
    const b = e.target.closest('#pen-toolbar button'); if (!b) return;
    if (b.dataset.tool) { S.settings.tool = b.dataset.tool; }
    else if (b.dataset.color) { S.settings.penColor = b.dataset.color; }
    else if (b.dataset.mcolor) { S.settings.markerColor = b.dataset.mcolor; }
    else if (b.dataset.width) { S.settings.penWidth = +b.dataset.width; }
    else if (b.dataset.act === 'undo') { const last = Ink.lastHost; if (last && last._ink) last._ink.undo(); else toast('取り消せる書き込みがありません'); }
    else if (b.dataset.act === 'finger') { S.settings.fingerDraw = !S.settings.fingerDraw; document.body.classList.toggle('finger', S.settings.fingerDraw); toast(S.settings.fingerDraw ? '指でも書けます（画面は余白か2本指でスクロール）' : 'ペンだけで書きます'); }
    else if (b.dataset.act === 'close') { setPenMode(false); }
    markDirty('settings/main'); renderBar();
  });
  return { attach, setPenMode, isPen: () => penMode, renderBar, PEN_COLORS, MARKER_COLORS, lastHost: null };
})();
