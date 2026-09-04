/* ===== sticky notes (付箋) ===== */
const Notes = (() => {
  const COLORS = ['y', 'p', 'b', 'g'];
  const CNAME = { y: '黄', p: 'ピンク', b: '青', g: '緑' };
  function all() { return S.notes.list; }
  function forUnit(ukey) { return all().filter(n => n.ukey === ukey); }
  function save() { markDirty('notes/all'); }
  function create(opts) {
    opts = opts || {};
    const n = { id: uid(), ukey: opts.ukey || null, ci: opts.ci == null ? null : opts.ci, quote: opts.quote || '', text: '', c: opts.c || 'y', t: Date.now(), u: Date.now() };
    edit(n, true);
  }
  function edit(n, isNew) {
    const u = n.ukey ? unitByKey(n.ukey) : null;
    const body = el('<div>' +
      (n.quote ? '<div class="nq" style="border-left:3px solid #999;padding-left:8px;color:#4a5160;margin-bottom:8px">「' + esc(n.quote) + '」</div>' : '') +
      '<textarea class="ntext" placeholder="気になったこと・覚えたいこと・先生に聞くことなど" rows="5">' + esc(n.text) + '</textarea>' +
      '<div class="row" style="margin-top:8px"><span class="sm muted">色：</span>' + COLORS.map(c => '<button class="sw ncol ' + (n.c === c ? 'on' : '') + '" data-c="' + c + '" style="width:34px;height:34px;border-radius:50%;background:var(--note-' + c + ');border:2px solid ' + (n.c === c ? '#1b1f26' : 'transparent') + '" aria-label="' + CNAME[c] + '"></button>').join('') +
      '<span class="grow"></span><span class="sm muted">' + (u ? esc(SUBJ[u.subject].name + '・' + unitLabel(u)) : '（単元に属さない付箋）') + '</span></div></div>');
    const m = openModal(isNew ? '付箋を追加' : '付箋を編集', body, { footer: '<button class="primary" data-save>保存</button>' + (isNew ? '' : '<button data-del>削除</button>') + '<button data-cancel>キャンセル</button>', sticky: true });
    let color = n.c;
    $$('.ncol', m).forEach(b => b.onclick = () => { color = b.dataset.c; $$('.ncol', m).forEach(x => x.style.borderColor = x.dataset.c === color ? '#1b1f26' : 'transparent'); });
    $('[data-save]', m).onclick = () => {
      const text = $('.ntext', m).value.trim();
      if (!text && !n.quote) { toast('内容を入力してください'); return; }
      n.text = text; n.c = color; n.u = Date.now();
      if (isNew) S.notes.list.push(n);
      save(); m.close(); Learn.refreshNotes(); if (typeof NotesView !== 'undefined') NotesView.refresh(); toast(isNew ? '付箋を追加しました' : '保存しました');
    };
    $('[data-cancel]', m).onclick = () => m.close();
    if (!isNew) $('[data-del]', m).onclick = async () => { if (await confirmBox('この付箋を削除しますか？')) { remove(n.id); m.close(); } };
    setTimeout(() => { const ta = $('.ntext', m); ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length); }, 50);
  }
  function remove(id) { S.notes.list = S.notes.list.filter(n => n.id !== id); save(); Learn.refreshNotes(); if (typeof NotesView !== 'undefined') NotesView.refresh(); }
  function render(n, opts) {
    opts = opts || {};
    const u = n.ukey ? unitByKey(n.ukey) : null;
    const d = new Date(n.u || n.t);
    return '<div class="note ' + n.c + '" data-id="' + n.id + '">' +
      (n.quote ? '<div class="nq">「' + esc(n.quote) + '」</div>' : '') +
      '<div class="nt">' + esc(n.text) + '</div>' +
      '<div class="nfoot"><span>' + (d.getMonth() + 1) + '/' + d.getDate() + '</span>' +
      (opts.showUnit && u ? '<span class="nlink" data-go="' + esc(n.ukey) + '" data-ci="' + (n.ci == null ? '' : n.ci) + '">' + esc(SUBJ[u.subject].short + '・' + (u.code || '') + ' ' + u.title) + '</span>' : '') +
      '<button class="nx" data-edit="' + n.id + '">編集</button></div></div>';
  }
  document.addEventListener('click', e => {
    const b = e.target.closest('[data-edit]'); if (b) { const n = all().find(x => x.id === b.dataset.edit); if (n) edit(n, false); return; }
    const g = e.target.closest('.nlink[data-go]'); if (g) { Learn.open(g.dataset.go, g.dataset.ci === '' ? null : +g.dataset.ci); }
  });
  return { all, forUnit, create, edit, remove, render, COLORS, CNAME };
})();
