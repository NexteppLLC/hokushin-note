# 第5回北辰テスト（2026/10/11）対策教材 — ソース一式

中3・埼玉県・志望校 所沢高校／山村学園高校（確約狙い）。目標：5科偏差値60（国50・数62・英62・理60・社60）。
学習期間 9/7〜10/10（34日、平日4時間・土日祝8時間）。

## フォルダ構成

```
editions.json     教材セット（回）の一覧：id / name / test_day / start / app（アプリに載せるか）
src/<回>/<subject>/  教材本文（Markdown、独自マークアップ） subject = plan, japanese, math, english, science, social
  config.json     タイトル・ヘッダ・ルビ設定（"ruby": true, "ruby_dicts": [...]）
  cover.html      表紙（HTML）
  *.md            本文（ファイル名順に連結）。*.inc.md は [[include:...]] で差し込む部品（単独では出力しない）
  figs/*.svg      図（[[svg:name]] で参照）
  ruby.txt        科目別ふりがな辞書（理科・社会）
src/<回>/plan_data.py   学習計画の元データ（開始日・試験日・単元・日別割り当て）
src/<回>/kanji_data.py  国語 漢字データ
src/ruby_common.txt     共通ふりがな辞書
build/            変換スクリプト（Python 3.11 / python-markdown / Playwright Chromium）
data/<回>/        生成データ：plan.json, kanji.json, math_calc.json, export/*.json（構造化JSON）
data/app/content.json  アプリ埋め込み用の全教材（生成物・全回分）
app/              学習アプリのソース（shell.html / app.css / js/*.js）
docs/             公開サイト（index.html, manifest.webmanifest, icons/）← GitHub Pages の配信フォルダ
deliver/<回>/     完成PDF（00_plan 計画 / 01_japanese / 02_math / 03_social / 04_science / 05_english）※Git管理外
out/              一時的なビルド出力（Git管理外）
test/app_test.py  アプリの自動テスト（Playwright）
HANDBOOK.md       ★作業手順書（修正・ビルド・公開・新しい回の追加）
```

現在の回：`h5`（第5回北辰テスト 2026/10/11）。

## ビルド

```
python3 build/build.py h5 <subject> [--png] [--pages a-b] [--nopdf]   # PDF → out/h5/<subject>.pdf
python3 build/gen_plan.py h5          # 計画表（data/h5/plan.json ほか）
python3 build/export_json.py h5       # data/h5/export/*.json
python3 build/export_app.py           # data/app/content.json（全回）
python3 build/build_app.py            # docs/index.html（公開用）/ out/app_standalone.html / out/app_artifact.html
python3 build/gen_sci_figs.py h5      # 理科の図SVGを再生成（かな表記）
python3 test/app_test.py              # アプリの自動テスト
```

回（edition）を省略すると editions.json の末尾の回が使われる。
必要なもの：Python 3.11、`markdown`、`playwright`（Chromium）、Noto Sans CJK JP フォント、poppler（確認用）。アプリのビルドだけなら `markdown` のみ。

## Markdown の独自マークアップ（src/*.md）

- 見出し：`# 章` / `## 単元コード　タイトル`（例 `## R13　電流の性質`、`## N1 …`、`## P1 …`、`## M1 …`）。
  コードの意味：N=新範囲（10月の出題範囲）、R=復習、G=地理、P=小問集合／一問一答、K=計算、W=記述、M=模擬テスト、OR=総復習、FIN=前日確認。
- ブロック：`:::type タイトル` … `:::`（type = box, point, q（問題）, a（解答）, note, warn, ex, memo, plan, tip, summary, goal, step, script（リスニング台本）, passage, dialog, rule, check, data, sub, cols）。
  **`:::q` の直後に `:::a` を置く**のが「演習→解答」の単位。
- インライン：`$…$` 数式（\frac \sqrt ^ _ \pm \times \div \le \ge \ne \pi \to \fallingdotseq）、`\ce{2H2 + O2 -> 2H2O}` 化学式、`{漢字|よみ}` 明示ルビ、`**太字**`、`==マーカー==`、`__下線__`、`[[check]]` チェック欄、`[[pb]]` 改ページ、`[[svg:name]]` 図、`[[include:file]]` 差し込み。
- 番号付き項目は `1. …　2. …`（全角スペース区切り）または行頭 `N. `。連番でない `9. ` などは変換時に自動でエスケープされる。

## ふりがな（理科・社会の総ルビ）

`build/ruby_engine.py` が辞書ベースで漢字の連続（漢字ラン）ごとに最長一致で読みを付ける。辞書行の形式：

```
漢字列=よみ                 例 電流=でんりゅう、大きい=おお（送り仮名を含む key 可。漢字ランが2つ以上なら読みを | で区切る：藤原道長=ふじわらの|みちなが）
#漢字列=よみ                直前が数字のときだけ   例 #人=にん
~接頭語漢字列=よみ          直前が接頭語のときだけ 例 ~の方=ほう、~*方=かた（* は任意のひらがな1文字）、~_日=にち（_ は空白）
```

読みの誤りを直すときは辞書に行を追加してビルドし直す。`out/<subject>_unmatched.txt` が空（0行）なら全漢字に読みが付いている。
SVG 内の文字はルビ処理の対象外なので、図のラベルはかなで書いてある。

## data/<回>/export/<subject>.json（構造化JSON）

```
{ "subject", "title", "ruby", "sections": [
   { "level": 1|2|3, "code": "R13", "title": "電流の性質", "heading": "R13　電流の性質",
     "path": ["5　中2 物理", "R13　電流の性質"], "file": "32_grade2_phys.md",
     "blocks": [
        {"type": "box"|"point"|"note"|…, "title": "要点", "md": "…"},      # :::ブロック本文（Markdown のまま）
        {"type": "text", "md": "…"},                                          # ブロック外の段落
        {"type": "exercise", "title": "一問一答（15問）",
         "question_md": "…", "answer_title": "解答", "answer_md": "…",
         "items": [ {"no": 1, "label": "1."|"(1)"|"問1", "q": "…", "a": "…"}, … ]   # 1問ずつ対応づけできた場合のみ
         "question_parts": [ … ]                                              # 大問形式で問題ブロックが複数のとき
        } ] } ] }
```

`items` が無い演習（長文・会話文・作文など）は `question_md` / `answer_md` をそのまま表示する。
`data/<回>/export/index.json` に教科ごとの件数と単元コード一覧。

## 学習アプリ（app/）

`app/shell.html`（画面の骨組み）＋ `app/app.css` ＋ `app/js/*.js`（番号順に連結）を `build/build_app.py` が1つのHTMLに束ねる。
教材データは `build/export_app.py` が `data/app/content.json`（回ごとに、ブロック単位の描画済みHTML・ルビ付き・問／答ペア・単語カード・漢字カード・学習計画）として出力し、HTMLに埋め込む。

- 画面：今日（日別計画・チェック・カレンダー）／日程（全日程表・週合計・未完了フィルタ）／学ぶ（科目→単元プルダウン、要点・演習、○△×自己採点、Apple Pencil 書き込み、計算スペース、手書きノート、付箋、マーカー、カード練習、検索）／進捗（計画達成率・単元完了率・正答率・直しリスト・学習時間）／ノート（付箋・マーカー・手書きの集約、全回）／設定（バックアップ・復元、指で書く、ふりがな、文字サイズ）。回が2つ以上あると画面上部に「教材セット」の切りかえが出る。
- 保存：IndexedDB（キー＝ `progress/<回>:<科目>`, `plan/main`, `notes/all`, `settings/main`, `hl/<単元キー>`, `ink/<単元キー>`, `nb/<単元キー>`）。バックアップJSONは同じ構造（`app: "hokushin-note", v: 2`）。v1（回の接頭辞なし）のデータは読み込み時に `migrateV1` で自動変換。
- 単元キー `ukey` は `<回>:<科目id>/<単元コード>`（例 `h5:science/R13`）。問題キーは `<ukey>#<ブロック番号>:<問番号>`（漢字は `:読み:<番号>`、単語は `#v<ブロック番号>:<番号>`、大問まるごとは `:all`）。計画のチェックは `<回>|<Day>:<科目記号>:<コード>`。
- ペン入力：`.inkhost` 要素の上で pointerType=pen のときだけ線を描く（指はスクロール）。iPad Safari では touchstart の `touchType === 'stylus'` で preventDefault してスクロールを止めている。

## 補足

- 配点・大問構成は過去の北辰テストの形式に合わせた目安。理科の新範囲（生命の連続性）・社会の新範囲（現代社会と私たち・日本国憲法）は10月号の出題範囲表で確認のこと（教科書会社で進度差あり）。
- 統計値は「目安」として丸めた値。ASEAN は 2025 年に東ティモールが加盟し 11 か国。
- 確約基準（山村学園）は学校説明会・個別相談で最新情報を確認。
