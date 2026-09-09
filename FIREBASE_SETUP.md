# 親PC進捗同期 — Firebase設定

北辰ノート本体の学習履歴は、従来どおり子どもの端末内（IndexedDB / localStorage）を主保存先とする。
Firebaseには親用ダッシュボード表示に必要な集計値だけを送信する。

## 送信する情報

- 教科別の単元進捗
- 採点済み問題数、○数、×△数
- 計画の完了数・完了率
- 手入力した学習時間の集計
- 初見・後日再テストの集計
- 最終学習日時

## 送信しない情報

- 問題文
- 解答
- 付箋
- マーカー
- 手書きデータ
- ノート本文

## Firebase Console 側の設定

1. Firebaseプロジェクトを作成する。
2. Webアプリを1つ追加し、表示される `firebaseConfig` を控える。
3. Authentication → Sign-in method で Email/Password を有効化する。
4. Authentication → Users で家族用アカウントを1つ作成する。
   - 子どもの端末と親PCは同じアカウントでログインする。
5. Firestore Database を作成する。
6. Firestore Rules を以下にする。

```text
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId}/{document=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

## 子どもの端末

1. 北辰ノートを開く。
2. 設定 → 「親PCとの同期」→「設定する」。
3. Firebase Consoleの `firebaseConfig` を貼り付けて保存する。
4. 家族用アカウントでログインする。
5. 「今すぐ同期」を押す。
6. 以後は学習中に自動同期する（ローカル保存が主保存先のまま）。

## 親PC

GitHub Pages公開後、次を開く。

`https://nexteppllc.github.io/hokushin-note/parent.html`

1. 「接続設定」を開く。
2. 子どもの端末と同じ `firebaseConfig` を貼り付ける。
3. 同じ家族用アカウントでログインする。
4. 同期済みの最新進捗が表示される。

## 注意

- Firebase設定・認証に失敗しても、北辰ノートの端末内学習履歴は影響を受けない。
- Firebase設定を消しても学習履歴は消えない。
- 週1回程度のJSONバックアップは今までどおり継続する。
