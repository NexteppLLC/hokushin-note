# -*- coding: utf-8 -*-
"""Functional smoke test of the app with Playwright (Chromium)."""
import asyncio, os, sys, json
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'file://' + os.path.join(ROOT, 'out', 'app_standalone.html')
SHOT = os.path.join(ROOT, 'out', 'shots')
os.makedirs(SHOT, exist_ok=True)

async def main():
    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={'width': 1180, 'height': 820}, device_scale_factor=1, has_touch=True, locale='ja-JP')
        page = await ctx.new_page()
        page.on('console', lambda m: errors.append(m.text) if m.type in ('error',) else None)
        page.on('pageerror', lambda e: errors.append('PAGEERROR ' + str(e)))
        await page.goto(URL)
        await page.wait_for_selector('.today-date', timeout=15000)
        await page.wait_for_timeout(700)
        await page.screenshot(path=os.path.join(SHOT, '00_intro.png'))
        if await page.is_visible('.modal-bg [data-ok]'):
            await page.click('.modal-bg [data-ok]')
        await page.screenshot(path=os.path.join(SHOT, '01_today.png'))
        # navigate to a plan day & open a task
        await page.click('[data-nav="cal"]')
        await page.screenshot(path=os.path.join(SHOT, '02_today_cal.png'))
        await page.click('.cal .cd[data-date="2026-09-08"]')
        n_tasks = await page.locator('.task').count()
        print('tasks on 9/8:', n_tasks)
        await page.click('.task .chk >> nth=0')
        done = await page.locator('.task.done').count()
        print('done after check:', done)
        await page.click('.task [data-open] >> nth=1')
        await page.wait_for_selector('.unit-head')
        await page.screenshot(path=os.path.join(SHOT, '03_learn_from_task.png'), full_page=False)
        title = await page.locator('.unit-head .ut').inner_text()
        print('opened unit:', title)
        # switch to science, a unit with items
        await page.select_option('#sel-subj', 'science')
        await page.wait_for_timeout(200)
        opts = await page.eval_on_selector_all('#sel-unit option', 'els => els.map(e => [e.value, e.textContent])')
        r13 = [v for v, t in opts if v.endswith('/R13')]
        await page.select_option('#sel-unit', r13[0])
        await page.wait_for_selector('.cblock.t-ex')
        await page.screenshot(path=os.path.join(SHOT, '04_learn_science.png'))
        # reveal + grade first item
        item = page.locator('.cblock.t-ex .item').first
        await item.locator('[data-act="ans"]').click()
        await item.locator('.gbtn.g2').click()
        cls = await item.get_attribute('class')
        print('item class after grade:', cls)
        score = await page.locator('.exscore').first.inner_text()
        print('score:', score)
        # scratch pad + draw with mouse (always host)
        await item.locator('[data-act="scratch"]').click()
        sc = item.locator('.scratch')
        box = await sc.bounding_box()
        await page.mouse.move(box['x'] + 30, box['y'] + 60)
        await page.mouse.down()
        for i in range(10):
            await page.mouse.move(box['x'] + 30 + i * 12, box['y'] + 60 + (i % 3) * 8)
        await page.mouse.up()
        paths = await sc.locator('path').count()
        print('scratch paths:', paths)
        # pen mode drawing on a knowledge block
        await page.click('.tools [data-act="pen"]')
        await page.wait_for_selector('#pen-toolbar:not([hidden])')
        blk = page.locator('.cblock.t-box').first
        await blk.scroll_into_view_if_needed()
        await page.evaluate('window.scrollBy(0, -200)')
        await page.wait_for_timeout(200)
        bb = await blk.bounding_box()
        await page.mouse.move(bb['x'] + 100, bb['y'] + 80)
        await page.mouse.down()
        for i in range(15):
            await page.mouse.move(bb['x'] + 100 + i * 10, bb['y'] + 80 + (i % 4) * 5)
        await page.mouse.up()
        pcount = await blk.locator('path').count()
        print('block ink paths:', pcount)
        await page.screenshot(path=os.path.join(SHOT, '05_learn_pen.png'))
        await page.click('#pen-toolbar [data-act="close"]')
        # highlight via selection
        await page.evaluate('''() => {
          const body = document.querySelector('.cblock.t-box .cbody');
          const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
          let n, nodes=[]; while((n=walker.nextNode())) { if (n.parentNode.nodeName!=='RT' && n.data.trim().length>4) nodes.push(n); }
          const t = nodes[1]; const r = document.createRange(); r.setStart(t, 0); r.setEnd(t, Math.min(6, t.data.length));
          const sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(r);
        }''')
        await page.wait_for_timeout(500)
        vis = await page.is_visible('#hl-pop')
        print('hl popover visible:', vis)
        if vis:
            await page.dispatch_event("#hl-pop [data-c=\"y\"]", "pointerdown")
            await page.wait_for_timeout(200)
            marks = await page.locator('.cblock.t-box mark').count()
            print('marks:', marks)
        # note via block button
        await page.click('.cblock.t-box [data-act="bnote"]')
        await page.fill('.ntext', 'テストの付箋です')
        await page.click('[data-save]')
        await page.wait_for_timeout(200)
        notes = await page.locator('.note').count()
        print('notes rendered:', notes)
        await page.screenshot(path=os.path.join(SHOT, '06_learn_note_hl.png'))
        # cards
        await page.click('.tools [data-act="cards"]')
        await page.wait_for_selector('.fc-card')
        await page.click('.fc-card')
        await page.wait_for_selector('.fc-ctl .gbtn')
        await page.click('.fc-ctl .gbtn.g0')
        await page.screenshot(path=os.path.join(SHOT, '07_cards.png'))
        await page.click('.modal .mx')
        # notebook
        await page.click('.tools [data-act="nb"]')
        await page.wait_for_selector('.nb-page')
        pg = page.locator('.nb-page')
        pb = await pg.bounding_box()
        await page.mouse.move(pb['x'] + 100, pb['y'] + 100); await page.mouse.down()
        for i in range(10): await page.mouse.move(pb['x'] + 100 + i * 15, pb['y'] + 100 + i * 6)
        await page.mouse.up()
        print('nb paths:', await pg.locator('path').count())
        await page.screenshot(path=os.path.join(SHOT, '08_notebook.png'))
        await page.click('.modal .mx')
        # english vocab cards
        await page.select_option('#sel-subj', 'english')
        await page.wait_for_timeout(200)
        opts = await page.eval_on_selector_all('#sel-unit option', 'els => els.map(e => e.value)')
        v1 = [v for v in opts if v.endswith('/V1')][0]
        await page.select_option('#sel-unit', v1)
        await page.wait_for_selector('[data-act="vcards"]')
        await page.click('[data-act="vcards"]')
        await page.wait_for_selector('.fc-card')
        await page.screenshot(path=os.path.join(SHOT, '09_vocab_card.png'))
        await page.click('.modal .mx')
        # japanese kanji set
        await page.select_option('#sel-subj', 'japanese')
        await page.wait_for_timeout(200)
        opts = await page.eval_on_selector_all('#sel-unit option', 'els => els.map(e => e.value)')
        k1 = [v for v in opts if v.endswith('/K1')][0]
        await page.select_option('#sel-unit', k1)
        await page.wait_for_selector('.kitem')
        await page.click('.kitem .kq >> nth=0')
        await page.click('.kitem .gbtn.g0 >> nth=0')
        await page.screenshot(path=os.path.join(SHOT, '10_kanji.png'))
        # math unit rendering (fractions)
        await page.select_option('#sel-subj', 'math')
        await page.wait_for_timeout(200)
        opts = await page.eval_on_selector_all('#sel-unit option', 'els => els.map(e => e.value)')
        q3 = [v for v in opts if v.endswith('/Q3')]
        if q3:
            await page.select_option('#sel-unit', q3[0])
            await page.wait_for_timeout(300)
            await page.screenshot(path=os.path.join(SHOT, '11_math.png'))
        # search
        await page.click('#btn-search')
        await page.fill('#q', 'オームの法則')
        await page.wait_for_timeout(500)
        print('search hits:', await page.locator('.sr-item').count())
        await page.screenshot(path=os.path.join(SHOT, '12_search.png'))
        await page.click('.sr-item >> nth=0')
        await page.wait_for_timeout(300)
        # progress
        await page.click('#tabs [data-view="progress"]')
        await page.wait_for_selector('.stat-grid')
        await page.screenshot(path=os.path.join(SHOT, '13_progress.png'))
        await page.click('[data-weak="science"]')
        await page.wait_for_timeout(300)
        print('weak items:', await page.locator('.witem').count())
        await page.screenshot(path=os.path.join(SHOT, '14_weak.png'))
        await page.click('.modal .mx')
        # notes view
        await page.click('#tabs [data-view="notes"]')
        await page.wait_for_selector('.nlist')
        print('note entries:', await page.locator('.nlist .ni').count())
        await page.screenshot(path=os.path.join(SHOT, '15_notes.png'))
        # settings
        await page.click('#tabs [data-view="settings"]')
        await page.wait_for_selector('#bk-save')
        await page.screenshot(path=os.path.join(SHOT, '16_settings.png'))
        # persistence: reload and check grade persists
        await page.reload()
        await page.wait_for_selector('.today-date')
        persisted = await page.evaluate("() => JSON.stringify(Object.keys(S.progress['h5:science'].items)) + ' notes=' + S.notes.list.length + ' hl=' + Object.keys(S.hl).join(',') + ' ink=' + Object.keys(S.ink).join(',') + ' nb=' + Object.keys(S.nb).join(',') + ' plan=' + Object.keys(S.plan.done).join(',')")
        print('persisted:', persisted)
        # v1 backup migration
        v1 = json.dumps({'app': 'hokushin-note', 'v': 1, 'exported': '2026-09-04T00:00:00Z',
            'progress': {'science': {'items': {'science/R13#3:1': {'g': 0, 't': 1}, 'science/R13#3:2': {'g': 2, 't': 2}}, 'units': {'science/R13': {'v': 1}}}},
            'plan': {'done': {'2:S:N2': 5}, 'log': {'2026-09-08': {'m': 40, 'g': 1}}},
            'notes': {'list': [{'id': 'n1', 'ukey': 'science/R13', 'ci': 0, 'quote': '', 'text': 'v1 note', 'c': 'y', 't': 1, 'u': 1}]},
            'settings': {'last': {'ukey': 'science/R13'}}, 'hl': {'science/R13': [{'b': 0, 's': 0, 'e': 3, 'c': 'y', 'txt': 'abc', 't': 1}]},
            'ink': {'science/R13': {'blocks': {}, 'scratch': {'science/R13#3:1': {'w': 100, 'strokes': [{'c': '#000', 'w': 2, 't': 'pen', 'p': [1, 1, 2, 2]}]}}}}, 'nb': {}})
        await page.evaluate("t => { Settings.importBackup(t); return true; }", v1)
        await page.wait_for_timeout(300)
        await page.click('.modal-bg [data-ok]')
        await page.wait_for_timeout(800)
        mig = await page.evaluate("() => JSON.stringify({p: Object.keys(S.progress['h5:science'].items), u: Object.keys(S.progress['h5:science'].units), plan: Object.keys(S.plan.done), note: S.notes.list[0].ukey, hl: Object.keys(S.hl), ink: Object.keys(S.ink), sc: Object.keys(S.ink['h5:science/R13'].scratch), last: S.settings.last.ukey, weak: Progress.weakItems('science').length})")
        print('migrated:', mig)
        await page.reload(); await page.wait_for_selector('.today-date'); await page.wait_for_timeout(400)
        mig2 = await page.evaluate("() => Object.keys(S.progress).join(',') + ' | ' + Object.keys(S.hl).join(',')")
        print('after reload:', mig2)
        # portrait iPad
        await page.set_viewport_size({'width': 834, 'height': 1194})
        await page.click('#tabs [data-view="learn"]')
        await page.wait_for_selector('.unit-head')
        await page.screenshot(path=os.path.join(SHOT, '17_portrait_learn.png'))
        await page.click('#tabs [data-view="today"]')
        await page.wait_for_selector('.today-date')
        await page.screenshot(path=os.path.join(SHOT, '18_portrait_today.png'))
        await browser.close()
    print('console errors:', len(errors))
    for e in errors[:20]: print('  ', e[:300])

asyncio.run(main())
