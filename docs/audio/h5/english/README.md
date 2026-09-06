# 英語リスニングの練習用音声

`L1.mp3`〜`L8.mp3` は各リスニング演習の No.1〜8、`M1.mp3`・`M2.mp3` は各自作模擬のリスニング No.1〜7 に対応します。教材の英文原稿から作成した合成音声です。北辰図書の公式音声ではありません。

- 各本文・対話と英語の質問を2回再生します。2回の間は3秒、次の問題までは10秒の解答時間があります。
- No.6 の質問の間は5秒あります。No.7 はメモを完成させる英文のみを2回再生します。
- 問題文・図・メモを先に確認し、原稿や解答は答え合わせ時に開いてください。
- 複数の英語音声を使っています。抑揚や固有名詞の発音は人による録音と異なる場合があります。本番の速さ・声・形式の確認には、手元の過去問と対応する公式音声も使ってください。

## 作成方法

外部サービスや認証を使わず、FFmpeg に組み込まれた Flite の `rms`・`slt` 音声で生成しています。本文のソースは `src/h5/english/30_listening.md` と `src/h5/english/60_mock.md` です。`:::script` 内の英語だけを抽出し、設問や解答の本文を読み上げないようにしています。

リポジトリのルートで実行します。Python 3 と、Flite フィルター・libmp3lame エンコーダーを含む FFmpeg が必要です。

```sh
python3 build/generate_listening_audio.py
python3 build/generate_listening_audio.py --check
# 一部の原稿だけ変更した場合
python3 build/generate_listening_audio.py --units M2
```

MP3 はモノラル・22,050 Hz・48 kbps。声の速さは元の合成速度の0.8倍です。`src/h5/english/audio_manifest.json` に原稿ハッシュ、ファイルハッシュ、音声長、問題番号ごとの位置、発話配列を保存しています。発話配列は2回分を展開済みで、日本語の解説や解答は含みません。原稿を変更した場合は音声を再生成してください。

## 使用ソフトウェア

- [FFmpeg: Flite 音声合成フィルター](https://ffmpeg.org/ffmpeg-filters.html#flite)
- [Flite — Carnegie Mellon University](https://github.com/festvox/flite)
- [Flite のライセンス](https://github.com/festvox/flite/blob/master/COPYING)

生成環境の Flite パッケージの著作権表示は `FLITE-NOTICES.txt` に収録しています。ここで配布するのは生成した練習用MP3であり、Flite の実行ファイルや音声モデルは含みません。
