# 作業手順書（HANDBOOK）

北辰テスト → 所沢高校入試（2027年2月）まで、この1つのリポジトリで教材とアプリを育てていくための手順です。
Claude Code / Codex / Cowork のどれから作業しても同じ手順で動きます。

## 0. 全体像

```
editions.json          教材セット（回）の一覧。ここに1行足すと新しい回が始まる
src/<回>/<科目>/*.md   教材本文（Markdown＋独自マークアップ）      例 src/h5/science/32_grade2_phys.md
src/<回>/plan_data.py  学習計画（開始日・試験日・単元と所要分・日別割り当て）
src/<回>/kanji_data.py 国語の漢字データ
src/ruby_common.txt    ふりがな辞書（共通）／ src/<回>/<科目>/ruby.txt（科目別）
build/                 変換スクリプト（PDF・JSON・アプリ）
app/                   アプリ本体（shell.html / app.css / js/*.js）
data/<回>/             生成データ（plan.json, kanji.json, math_calc.json, export/）
data/app/content.json  アプリに埋め込む全教材データ（生成物）
docs/                  公開サイト（index.html＝アプリ、manifest、icons）★GitHub Pages が配信するフォルダ
deliver/<回>/          PDF（納品物・Git管理外。zipには同梱）
out/                   一時的なビルド出力（Git管理外）
test/app_test.py       アプリの自動テスト（Playwright）
```

配信の流れ：`src` を直す → `build/export_app.py` → `build/build_app.py` → `docs/index.html` が更新される → `git push` → 数十秒〜数分で公開URLに反映。

## 1. 最初の1回だけ：環境とリポジトリ

### 1-1. パソコン側の準備（Windows / Mac 共通）

1. Python 3.11 以上をインストール。
2. このフォルダで `pip install -r requirements.txt`（`markdown` と `playwright`）。
3. PDFを作る・自動テストを回す場合だけ `python -m playwright install chromium`。アプリのビルドだけなら不要。
4. PDFを作る場合は Noto Sans CJK JP / Noto Serif CJK JP フォントを入れる（アプリのビルドには不要）。

### 1-2. GitHub にリポジトリを作る

1. GitHub で新しいリポジトリを作成（名前は例：`hokushin-note`。**Public**にすると GitHub Pages が無料で使えます。Private のまま Pages を使うには有料プランが必要）。
2. このフォルダで：
   ```
   git remote add origin https://github.com/<ユーザー名>/hokushin-note.git
   git push -u origin main
   ```
   （このフォルダには最初のコミットまで済んだ `.git` が入っています）
3. GitHub の **Settings → Pages** で、Source を「Deploy from a branch」、Branch を `main`、フォルダを `/docs` にして Save。
4. 数分後に `https://<ユーザー名>.github.io/hokushin-note/` でアプリが開きます。これが**今後ずっと使うURL**です（変えないこと。学習データはこのURLに紐づきます）。

### 1-3. iPad への導入と、旧アプリからのデータ移行

1. 旧アプリ（claude.ai 版）で「設定 → コピー」を押し、メモアプリに貼り付けて保存。
2. 新URLを iPad の Safari で開き、「共有 → ホーム画面に追加」。以後はホーム画面のアイコンから開く。
3. 新アプリで「設定 → 貼り付けて復元」に、1でコピーした文字を貼り付けて復元。
4. 進捗が引き継がれていることを確認したら、旧アプリは使わない。

## 2. ふだんの修正（マイナーチェンジ）

### 2-1. 教材の文章・問題を直す

1. `src/h5/<科目>/*.md` を編集する（マークアップは README.md 参照）。
2. アプリを作り直す：
   ```
   python3 build/export_app.py      # 全教材 → data/app/content.json
   python3 build/build_app.py       # → docs/index.html（公開用）, out/app_standalone.html
   ```
3. 確認：`out/app_standalone.html` をブラウザで開く（PCのChrome/Edgeで十分。ペンはマウスで代用できる）。
   自動テストを回すなら `python3 test/app_test.py`（Playwright が必要。`out/shots/` にスクリーンショットが出る）。
4. `git add -A && git commit -m "理科R13の解答を修正" && git push`。

理科・社会で新しい漢字を使ったときは、ビルド時に `unmatched kanji runs` が 0 か確認する（PDFビルド時に表示）。
0 でなければ `src/ruby_common.txt` か `src/h5/<科目>/ruby.txt` に `漢字=よみ` の行を足す（書式は README.md）。
アプリ側のビルド（export_app.py）は未登録の漢字を**ふりがな無しのまま**通すので、PDFを作らない場合は
`python3 build/build.py h5 science --nopdf` で未登録漢字だけ確認できる。

### 2-2. 計画表（日程）を直す

- `src/h5/plan_data.py` の `DAYS`（日別の割り当て）や `UNITS`（単元名・分数）を編集。
- `python3 build/gen_plan.py h5` で `data/h5/plan.json` と各科目の `plan_table.inc.md`、`src/h5/plan/90_days.md` が作り直される。
- そのあと 2-1 の手順でアプリをビルド。PDFの計画表も直すなら `python3 build/build.py h5 plan`。

### 2-3. アプリの見た目・機能を直す

- 画面の骨組み `app/shell.html`、見た目 `app/app.css`、動作 `app/js/*.js`（番号順に連結される）。
- 直したら `python3 build/build_app.py` → 確認 → push。教材を触っていなければ `export_app.py` は不要。
- 学習データの保存形式（キーの付け方）は README.md の「学習アプリ」の項にあります。**保存形式を変えるときは必ず `migrateV1` のような移行処理を書く**（子どものデータを消さないため）。

### 2-4. PDF も作り直す（必要なときだけ）

```
python3 build/build.py h5 science          # out/h5/science.pdf
python3 build/build.py h5 science --png    # ページ画像も出す（確認用）
```
できた PDF は `deliver/h5/` にコピーして納品（`deliver/` は容量が大きいので Git には入れない設定）。

## 3. 新しい回（第6回北辰、入試直前…）を追加する

1. `editions.json` に追加する（**末尾に追加**。順番がアプリの並び順）：
   ```json
   { "id": "h6", "name": "第6回北辰テスト", "short": "第6回（11/2）", "test_day": "2026-11-02", "start": "2026-10-12", "app": true, "note": "…" }
   ```
   （日付は例。実際の実施日に合わせる）
   `id` は英数字（保存データのキーに使うので**あとから変えない**）。
2. `src/h5` を `src/h6` にコピーして、教材と `plan_data.py`（開始日・試験日・DAYS・UNITS）を書きかえる。
   共通で使い回す単元（漢字セット、計算ドリル、単語）はそのまま残してよい。
3. `python3 build/gen_plan.py h6`（計画）→ 必要なら `gen_kanji.py h6` / `gen_calc.py h6`（データ生成）
   → `python3 build/export_app.py`（全回まとめて）→ `python3 build/build_app.py` → push。
4. アプリ上部に「教材セット」の切りかえが現れ、今日の日付に合う回が自動で選ばれる。
   前の回の○×・付箋・書き込みはそのまま残り、「ノート」タブでは回のラベル付きで一覧できる。
5. 古い回をアプリから外したいときは `editions.json` の `"app": false` にする（データは消えない）。

入試本番用（2月）も同じ仕組みで `"id": "nyushi"` などを追加すればよい。単元コード（R13 など）は回ごとに独立なので、番号の付け直しは不要。

## 4. こまったとき

- **ビルドで `unclosed blocks` エラー**：`:::box` などのブロックを `:::` で閉じ忘れている。
- **表が崩れる**：表の前に空行を入れる。番号付きリストの直前も空行。
- **数式が崩れる**：`$…$` の中で使える記号は README.md 参照。`$` を文章中で使う場合は全角の＄にする。
- **アプリで進捗が消えた**：iPad の「ホーム画面のアイコン」と「Safari」ではデータが別々。いつも同じ方から開く。バックアップ（設定 → コピー）から復元できる。
- **公開URLが更新されない**：GitHub の Actions/Pages のデプロイに数分かかる。ブラウザのキャッシュは再読み込みで消える（ホーム画面アプリは一度完全に閉じて開き直す）。
- **テストが途中で止まる**：初回起動の「はじめに」ダイアログが原因のことが多い。`test/app_test.py` は自動で閉じる処理を入れてある。

## 5. コミットメッセージの書き方（例）

- `理科 R13 一問一答の解答を修正`
- `社会 N7 総合演習を追加`
- `app: 日程表に週合計を表示`
- `h6: 第6回北辰の教材セットを追加`
