# -*- coding: utf-8 -*-
import os, sys, re
sys.path.insert(0, os.path.dirname(__file__))
import editions as ED
EDITION, _args = ED.resolve(sys.argv[1:])
_kd = ED.import_module(EDITION, 'kanji_data')
YOMI, KAKI = _kd.YOMI, _kd.KAKI

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARD = {'駆逐', '把持', '脚光', '痕跡', '緻密', '卓越', '逸話', '惰性', '頒布', '享楽', '廉価', '斬新', '折衷', '窮地', '促成', '含蓄', '会得', '功徳',
        '納涼', '暴露', '仮病', '相殺', '出納', '流布', '一矢', '遵守', '脆弱', '凄惨', '辛辣', '漸次', '寡黙', '払拭', '萎縮', '逐次', '恣意',
        '拘束', '放棄', '脱却', '弾劾', '咀嚼', '訃報', '汎用', '曖昧', '語彙', '享受', '皆無', '氾濫', '俯瞰', '葛藤', '疎外', '融和', '共鳴', '衝動', '媒体', '偶像', '逆説', '暁'}


def target(p):
    return re.search(r'__(.+?)__', p).group(1)


yomi_easy = [x for x in YOMI if target(x[0]) not in HARD]
yomi_hard = [x for x in YOMI if target(x[0]) in HARD]
yomi = (yomi_easy + yomi_hard)[:300]
kaki = [(re.sub(r'([ァ-ヶー]+)', r'__\1__', s_, count=1), a) for s_, a in KAKI[:240]]

out = []
out.append('# 1　漢字（読み300・書き240）')
out.append('')
out.append(''':::box 漢字セットのやり方（1セット10分）
1. 読み10問・書き8問を**ノートに書いて**解く（口で言うだけにしない）。
2. すぐに答え合わせ。間違えた語に☐チェックを入れ、**正しい漢字（または読み）を3回書く**。
3. 翌日のセットを始める前に、前日のチェック語だけ30秒で見直す。
4. 復習テスト（KT1〜KT4）は、それまでのセットからの出題。8割取れなかったセットは「漢字 間違いノートの総復習（KR）」の日にもう一度。
- 北辰の**読み**は中学で習う漢字（訓読み・音読み熟語）が中心、**書き**は小学校で習った漢字の熟語が中心です。書きは「とめ・はね・はらい」までていねいに。
- セット25〜30の読みは少し難しい語（発展）を含みます。目標50なら「読めたらラッキー」でOK。
:::''')
out.append('')

for i in range(30):
    y = yomi[i * 10:(i + 1) * 10]
    k = kaki[i * 8:(i + 1) * 8]
    out.append('## K%d　漢字セット%d' % (i + 1, i + 1))
    out.append('')
    out.append(':::q 読み　――線の漢字の読みをひらがなで書きなさい。')
    out.append('| No | 問題 | ☐ | No | 問題 | ☐ |')
    out.append('|--:|:--|:--:|--:|:--|:--:|')
    for j in range(5):
        a = y[j]
        b = y[j + 5]
        out.append('| %d | %s | ☐ | %d | %s | ☐ |' % (j + 1, a[0], j + 6, b[0]))
    out.append(':::')
    out.append(':::q 書き　――線のカタカナを漢字に直しなさい。')
    out.append('| No | 問題 | ☐ | No | 問題 | ☐ |')
    out.append('|--:|:--|:--:|--:|:--|:--:|')
    for j in range(4):
        a = k[j]
        b = k[j + 4]
        out.append('| %d | %s | ☐ | %d | %s | ☐ |' % (j + 1, a[0], j + 5, b[0]))
    out.append(':::')
    out.append(':::a 解答')
    out.append('**読み**　' + '　'.join('%d %s' % (j + 1, y[j][1]) for j in range(10)))
    out.append('')
    out.append('**書き**　' + '　'.join('%d %s' % (j + 1, k[j][1]) for j in range(8)))
    out.append(':::')
    out.append('')
    if (i + 1) in (7, 14, 21, 30):
        n = {7: 1, 14: 2, 21: 3, 30: 4}[i + 1]
        lo = {1: 0, 2: 7, 3: 14, 4: 21}[n]
        hi = i + 1
        ys = yomi[lo * 10:hi * 10]
        ks = kaki[lo * 8:hi * 8]
        # pick every k-th item deterministically
        step_y = max(1, len(ys) // 10)
        step_k = max(1, len(ks) // 10)
        ty = [ys[(m * step_y + 3) % len(ys)] for m in range(10)]
        tk = [ks[(m * step_k + 2) % len(ks)] for m in range(10)]
        out.append('[[pb]]')
        out.append('')
        out.append('## KT%d　漢字復習テスト%s（セット%d〜%d・20問・15分）' % (n, '①②③④'[n - 1], lo + 1, hi))
        out.append('')
        out.append(':::q 読み　――線の漢字の読みをひらがなで書きなさい。')
        out.append('| No | 問題 | ☐ | No | 問題 | ☐ |')
        out.append('|--:|:--|:--:|--:|:--|:--:|')
        for j in range(5):
            out.append('| %d | %s | ☐ | %d | %s | ☐ |' % (j + 1, ty[j][0], j + 6, ty[j + 5][0]))
        out.append(':::')
        out.append(':::q 書き　――線のカタカナを漢字に直しなさい。')
        out.append('| No | 問題 | ☐ | No | 問題 | ☐ |')
        out.append('|--:|:--|:--:|--:|:--|:--:|')
        for j in range(5):
            out.append('| %d | %s | ☐ | %d | %s | ☐ |' % (j + 1, tk[j][0], j + 6, tk[j + 5][0]))
        out.append(':::')
        out.append(':::a 解答')
        out.append('**読み**　' + '　'.join('%d %s' % (j + 1, ty[j][1]) for j in range(10)))
        out.append('')
        out.append('**書き**　' + '　'.join('%d %s' % (j + 1, tk[j][1]) for j in range(10)))
        out.append('')
        out.append('**判定**：16問以上→合格。15問以下→間違えた語をKRの日にもう一度。')
        out.append(':::')
        out.append('')

out.append('''## KR　漢字 間違いノートの総復習（20分）

:::box やり方
- セット1〜30と復習テストで☐がついた語だけを、**読み→書き**の順にノートで再テスト。
- 2回連続で正解した語は卒業（☐を消す）。前日（FIN）は残った語だけ見直す。
- 同音異義語（収める／納める／治める／修める、保証／保障、対象／対照 など）は**意味とセット**で覚える。
:::
''')

os.makedirs(ED.src_dir(EDITION, 'japanese'), exist_ok=True)
open(ED.src_dir(EDITION, 'japanese', '10_kanji.md'), 'w', encoding='utf-8').write('\n'.join(out))

# also export data for the app
import json
json.dump({'yomi': [{'phrase': p, 'target': target(p), 'reading': r} for p, r in yomi],
           'kaki': [{'sentence': s, 'answer': a} for s, a in kaki]},
          open(ED.data_dir(EDITION, 'kanji.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', len(yomi), len(kaki))
