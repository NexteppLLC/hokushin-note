# 図・資料問題と学習記録の改修

対象：2026年10月11日の第5回北辰テスト対策。

## 変更内容

1. 共通の図・史料・表を、問題一覧・演習・カード・直しリストで参照できるように修復。模擬テストの分離した問題と解答を対応付け、自己採点できるようにした。
2. 社会の公民新範囲を「現代社会と私たち」に修正。東京書籍ではP36までを基準とし、憲法等の先取りは参考学習として区別。2026年度の国語に課題作文がない点も計画・説明に反映。理科の実験条件、グラフの軸、音の振動数、反射、歴史資料の解釈などを訂正した。
3. 既存の細胞分裂・発生・回路・地形図・歴史統計などに実際の図を追加／修復。
4. 理科V1〜V24（96小問）、歴史VH1〜VH12（48小問）、地理／公民VG1〜VG12（48小問）を追加。各セット4問で、資料・解答・根拠・誤りやすい点を収録。歴史では公開利用条件のある写真・実作品5点を使用。架空の統計・模式図には学習用であることを明記した。日別計画は既存の時間枠へ再配分した。
5. 初見・解き直し・後日再テストを分けて記録。自己解答を終えてから答え合わせする流れ、24時間条件、1・3・7日の復習、採点訂正履歴、任意の失点理由、実際の学習時間を追加した。

## 学習記録の扱い

- 従来の3,550問の保存キーと、既存単元の位置・ブロック数を維持。新章はアプリの既存単元の後ろへ追加している。
- 改修前の採点は「改修前の記録」として保存し、新しい初見・後日再テストの正答率から除外する。採点は自己申告・自己採点であり、本番得点や偏差値への換算ではない。
- 最新の自己採点と、各回の採点履歴を区別。過去の採点理由を訂正しても、後の回の採点結果を上書きしない。
- v1・v2バックアップを読み込み可能。新しい書き出し形式はv3で、履歴、付箋、マーカー、手書き、自由帳も含む。
- 本文が変わって元位置を確認できないマーカーは、保存したまま非表示。旧本文上の手書きは、位置ずれを避けて別表示する。旧本文に対する縦位置の完全復元はできない。問題ごとの計算欄と自由帳の保存先は保持する。
- 「必要知識10分」は指定部分の確認であり、単元全体を終えた意味ではない。日別予定の完了と単元の取り組み記録は別。

## 検証と限界

- 全教科の教材変換・単一HTML生成。
- 旧保存キー・既存単元位置、共通資料、模擬解答、カードへの受け渡し。
- 新192小問の設問／解答対応、図表の数値・対照条件を別担当でも確認。
- 全理科・社会SVGの構文と参照、追加画像の利用条件。新しい図・写真は画像へ描画して目視確認。
- 制御した時計を使い、24時間境界、採点訂正・重複・取消、復習間隔、旧バックアップ復元、新形式の往復、マーカー・旧手書き保持を確認。
- ブラウザでの操作通し確認と、利用者のスマートフォン・iPadでの実機確認は未実施。

再生成・回帰確認：

```sh
python build/gen_plan.py h5
python build/export_json.py h5
python build/export_app.py
python -W ignore::ResourceWarning -m unittest discover -s tests -p test_exercise_context.py
node tests/test_history.js
node tests/test_exercise_context.js
python build/build_app.py
```

図の再生成は `build/gen_sci_figs.py h5`、`build/build_geo_visuals.py`、`build/build_geo_mock1_map.py`。歴史画像の出典は `src/h5/social/figs/HISTORY_ASSET_SOURCES.md`。

## 主な確認先

- 北辰図書・出題範囲：https://www.hokushin-t.jp/test/hani/ha_index.html
- 北辰図書・マークシート方式：https://www.hokushin-t.jp/test/mstaisaku/mstaisaku.html
- 北辰図書・試験当日：https://www.hokushin-t.jp/test/toujitu/toujitu.html
- 東京書籍・公民単元構成：https://ten.tokyo-shoseki.co.jp/text/chu/shakai/komin/download/documents/koumin_tangen.pdf
- 東京書籍・理科：https://ten.tokyo-shoseki.co.jp/text/chu/rika/download/documents/R7rika_QR.pdf
- 学校図書・反射の説明：https://r7-kagaku.gakuto-plus.jp/2-2/3-5/2p126/
- 国土地理院・地図記号：https://www.gsi.go.jp/kohokocho/map-sign-tizukigou-2022-itiran.html
