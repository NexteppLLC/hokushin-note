/* ===== text highlights (マーカー) on rendered content ===== */
const HL = (() => {
  const COLORS = { y: '#ffe873', p: '#ffc6d3', b: '#bfe0ff', g: '#c6f0c6' };
  function textNodes(root) {
    const out = [];
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, { acceptNode(n) {
      let p = n.parentNode;
      while (p && p !== root) { if (p.nodeName === 'RT' || p.nodeName === 'RP' || p.nodeName === 'svg' || p.classList && (p.classList.contains('ink') || p.classList.contains('hl-ui') || p.classList.contains('study-record-note') || p.classList.contains('study-reason'))) return NodeFilter.FILTER_REJECT; p = p.parentNode; }
      return NodeFilter.FILTER_ACCEPT;
    } });
    let n; while ((n = w.nextNode())) out.push(n);
    return out;
  }
  /** absolute char offset of (node, offset) inside root (skipping rt) */
  function posOf(root, node, offset) {
    if (node.nodeType !== 3) {
      // element boundary: move to the first text node at/after child index
      const child = node.childNodes[offset];
      const tn = textNodes(root);
      if (!child) { // end of element -> position after its last text
        let last = null; tn.forEach(t => { if (node.contains(t)) last = t; });
        if (!last) return null; node = last; offset = last.data.length;
      } else {
        let first = null; for (const t of tn) { if (child === t || child.contains(t)) { first = t; break; } if (child.compareDocumentPosition(t) & Node.DOCUMENT_POSITION_FOLLOWING) { first = t; break; } }
        if (!first) return null; node = first; offset = 0;
      }
    }
    let pos = 0;
    for (const t of textNodes(root)) { if (t === node) return pos + Math.min(offset, t.data.length); pos += t.data.length; }
    return null;
  }
  function applyOne(root, s, e, cls) {
    let pos = 0;
    const nodes = textNodes(root);
    for (const t of nodes) {
      const len = t.data.length, start = pos, end = pos + len; pos = end;
      if (end <= s || start >= e) continue;
      const a = Math.max(s, start) - start, b = Math.min(e, end) - start;
      let target = t;
      if (b < len) target.splitText(b);
      if (a > 0) target = target.splitText(a);
      const m = document.createElement('mark'); m.className = 'hl-' + cls; m.dataset.hl = '1';
      target.parentNode.insertBefore(m, target); m.appendChild(target);
    }
  }
  // Map normalized text back to DOM text offsets; old backups normalized whitespace.
  function normalizedMap(text) {
    let normalized = '', indices = [], ends = [];
    const parts = text.matchAll(/\s+|\S/g);
    for (const m of parts) {
      const isSpace = /^\s+$/.test(m[0]);
      if (isSpace && !normalized) continue;
      normalized += isSpace ? ' ' : m[0]; indices.push(m.index); ends.push(m.index + m[0].length);
    }
    if (normalized.endsWith(' ')) { normalized = normalized.slice(0, -1); indices.pop(); ends.pop(); }
    return { text: normalized, indices, ends };
  }
  function resolveAnchor(text, h) {
    const needle = String(h.txt || '').replace(/\s+/g, ' ').trim();
    if (!needle) return null; // Unverifiable old offsets must never mark unrelated text.
    const current = text.slice(h.s, h.e).replace(/\s+/g, ' ').trim();
    if (Number.isInteger(h.s) && Number.isInteger(h.e) && h.s >= 0 && h.e <= text.length && h.e > h.s && current === needle) return { s: h.s, e: h.e };
    const norm = normalizedMap(text), at = norm.text.indexOf(needle);
    if (at < 0 || norm.text.indexOf(needle, at + 1) >= 0) return null;
    // Very old records kept only 120 characters: re-anchor only the verified text.
    return { s: norm.indices[at], e: norm.ends[at + needle.length - 1] };
  }
  /** Re-apply only verified highlights. Saved records remain byte-for-byte untouched. */
  function apply(body, ukey, ci) {
    const list = (S.hl[ukey] || []).filter(h => h.b === ci).sort((x, y) => x.s - y.s);
    const text = plain(body); let skipped = 0;
    list.forEach(h => { const range = resolveAnchor(text, h); if (range) applyOne(body, range.s, range.e, h.c); else skipped++; });
    return { applied: list.length - skipped, skipped };
  }
  function add(ukey, ci, s, e, c, txt, bodyText) {
    S.hl[ukey] = S.hl[ukey] || [];
    // remove overlapping same-range pieces
    S.hl[ukey] = S.hl[ukey].filter(h => { const r = bodyText == null ? h : resolveAnchor(bodyText, h); return !(h.b === ci && r && r.s < e && r.e > s); });
    S.hl[ukey].push({ b: ci, s, e, c, txt, t: Date.now() });
    markDirty('hl/' + ukey);
  }
  function removeRange(ukey, ci, s, e, bodyText) {
    if (!S.hl[ukey]) return;
    S.hl[ukey] = S.hl[ukey].filter(h => { const r = bodyText == null ? h : resolveAnchor(bodyText, h); return !(h.b === ci && r && r.s < e && r.e > s); });
    if (!S.hl[ukey].length) delete S.hl[ukey];
    markDirty('hl/' + ukey);
  }
  function plain(body) { return textNodes(body).map(t => t.data).join(''); }

  /* selection popover */
  const pop = () => $('#hl-pop');
  let curSel = null; // {ukey, ci, s, e, body, txt}
  function hide() { pop().hidden = true; curSel = null; }
  function onSelection() {
    if (Ink.isPen()) return;
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0 || sel.isCollapsed) { hide(); return; }
    const r = sel.getRangeAt(0);
    const body = r.commonAncestorContainer.nodeType === 1 ? r.commonAncestorContainer.closest('.cbody[data-ci]') : r.commonAncestorContainer.parentElement.closest('.cbody[data-ci]');
    if (!body) { hide(); return; }
    const s = posOf(body, r.startContainer, r.startOffset), e = posOf(body, r.endContainer, r.endOffset);
    if (s == null || e == null || e <= s) { hide(); return; }
    const card = body.closest('.cblock');
    curSel = { ukey: card.dataset.ukey, ci: +body.dataset.ci, s, e, body, txt: plain(body).slice(s, e) };
    const rect = r.getBoundingClientRect();
    const p = pop();
    p.innerHTML = Object.entries(COLORS).map(([k, v]) => '<button class="sw" data-c="' + k + '" style="background:' + v + '" aria-label="マーカー"></button>').join('') +
      '<button data-a="note">付箋にする</button><button data-a="del">消す</button>';
    p.hidden = false;
    const pw = p.offsetWidth;
    let left = rect.left + rect.width / 2 - pw / 2 + window.scrollX; left = clamp(left, 6, window.innerWidth - pw - 6);
    let top = rect.bottom + window.scrollY + 12; if (top + p.offsetHeight > window.scrollY + window.innerHeight - 10) top = rect.top + window.scrollY - p.offsetHeight - 12;
    p.style.left = left + 'px'; p.style.top = top + 'px';
  }
  let selTimer;
  document.addEventListener('selectionchange', () => { clearTimeout(selTimer); selTimer = setTimeout(onSelection, 250); });
  // act on pointerdown: on iPad the tap itself would clear the selection before a click arrives
  document.addEventListener('pointerdown', e => {
    const b = e.target.closest('#hl-pop button'); if (!b || !curSel) return;
    e.preventDefault(); e.stopPropagation();
    const cs = curSel;
    if (b.dataset.c) { add(cs.ukey, cs.ci, cs.s, cs.e, b.dataset.c, cs.txt, plain(cs.body)); Learn.rerenderBlock(cs.ukey, cs.ci); toast('マーカーをつけました'); }
    else if (b.dataset.a === 'del') { removeRange(cs.ukey, cs.ci, cs.s, cs.e, plain(cs.body)); Learn.rerenderBlock(cs.ukey, cs.ci); }
    else if (b.dataset.a === 'note') { Notes.create({ ukey: cs.ukey, ci: cs.ci, quote: cs.txt }); }
    window.getSelection().removeAllRanges(); hide();
  });
  return { apply, add, removeRange, plain, hide, COLORS, resolveAnchor };
})();
