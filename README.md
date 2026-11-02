# ザンギの地図

北海道の店のザンギを集め、地図から店を選ぶと、その店のザンギの動画と情報が見られるサイトです。

- 店のデータは `data/shops.json` にまとめ、`scripts/build.py` がそこから `docs/` にページを書き出します。
- 公開は GitHub Pages（`docs/` フォルダー）で行います。
- 載せている動画の ID は、GitHub Actions が週に1回 YouTube Data API で取り直します。

---

## フォルダーの中身

| 場所 | 中身 | 手で直すか |
|---|---|---|
| `data/shops.json` | 店のデータ（店名・住所・位置・動画ID など） | 直す |
| `data/site.json` | サイト名・連絡先・公開URL | 直す |
| `data/areas.json` | 14の総合振興局・振興局と市町村 | 市町村を足すときだけ |
| `data/videos.json` | 動画IDを取り直した結果と日付 | 直さない（Actions が書く） |
| `templates/` | ページの HTML のひな形 | 見た目を変えるとき |
| `assets/css/style.css` | 見た目（CSS） | 見た目を変えるとき |
| `assets/js/map.js` | 地図と動画の切り替え | ふつうは直さない |
| `assets/vendor/leaflet/` | 地図のライブラリ Leaflet 1.9.4（BSD-2 ライセンス） | 直さない |
| `scripts/build.py` | ページを書き出すプログラム | ふつうは直さない |
| `scripts/refresh_videos.py` | 動画IDを取り直すプログラム | ふつうは直さない |
| `.github/workflows/` | GitHub Actions の設定 | ふつうは直さない |
| `docs/` | 書き出したページ（公開されるのはここ） | 直さない（Actions が書く） |

`docs/` は書き出すたびに作り直されます。`docs/` の中を手で直しても消えるので、直すときは `data/`・`templates/`・`assets/` を直してください。

---

## 公開までの手順

### 1. リポジトリを作り、ファイルを置く

1. GitHub にログインし、右上の「＋」→「New repository」を押します。
2. 「Repository name」に名前（例：`zangi-map`）を入れ、「Public」を選んで「Create repository」を押します。
3. できたリポジトリの画面で「uploading an existing file」（または「Add file」→「Upload files」）を押します。
4. ZIP を展開したフォルダーの**中身をすべて**ドラッグして入れ、「Commit changes」を押します。

> **`.github` フォルダーを忘れないでください。** 名前が「.」で始まるフォルダーは、パソコンの初期設定では見えません。
> - Mac：Finder で `command` + `shift` + `.`（ピリオド）を押すと見えます。
> - Windows：エクスプローラーの「表示」→「隠しファイル」にチェックを入れます。
>
> アップロードしたあと、リポジトリの画面に `.github` が出ていることを確かめてください。

### 2. Actions が書き込めるようにする

1. リポジトリの「Settings」→ 左の「Actions」→「General」を開きます。
2. 下の方の「Workflow permissions」で「Read and write permissions」を選び、「Save」を押します。

### 3. GitHub Pages を有効にする

1. 「Settings」→ 左の「Pages」を開きます。
2. 「Build and deployment」の「Source」で「Deploy from a branch」を選びます。
3. 「Branch」で `main` と `/docs` を選び、「Save」を押します。
4. 1〜2分たつと、同じ画面の上に公開URL（例：`https://ユーザー名.github.io/zangi-map/`）が出ます。

### 4. 連絡先と公開URLを書く

「このサイトについて」に載る掲載・削除の連絡先です。**書かないと「（準備中）」と出ます。**

1. リポジトリで `data/site.json` を開き、鉛筆のマーク（Edit）を押します。
2. 次の3か所を書きます。

```json
  "contact_email": "連絡を受けるメールアドレス",
  "repo_url": "https://github.com/ユーザー名/zangi-map",
  "site_url": "https://ユーザー名.github.io/zangi-map",
```

- `contact_email` か `repo_url` のどちらかがあれば連絡先が出ます。`repo_url` を書くと、GitHub の Issues への案内が出ます。メールアドレスを公開したくなければ、`contact_email` は `""` のままで構いません。
- `site_url` は、見つからないページ（404）の表示に使います。

3. 「Commit changes」を押すと、Actions の「ページの書き出し」が動き、1〜2分で公開ページに反映されます。

---

## API キーを GitHub の Secrets に置く（初心者向け）

週1回の動画IDの取り直しには、YouTube Data API の **API キー**が要ります。キーは「パスワードのようなもの」なので、ファイルには書かず、GitHub の **Secrets**（秘密の保管場所）に入れます。

### A. API キーを用意する

試しの収集で作ったキーを消していなければ、まずそれを消し、新しいキーを作ります。試しのキーはチャットに貼ったことがあるからです。

1. [Google Cloud コンソール](https://console.cloud.google.com/) を開き、試しのときと同じプロジェクトを選びます。
2. 左のメニュー「API とサービス」→「認証情報」を開きます。
3. 試しのキーがあれば、行の右のゴミ箱マークで削除します。
4. 上の「＋認証情報を作成」→「API キー」を押します。キーが表示されたら、その画面を閉じずに次へ進みます。
5. 「キーを編集」（またはキーの名前を押す）を開き、次のように制限します。
   - **API の制限**：「キーを制限」を選び、「YouTube Data API v3」だけにチェックを入れる。
   - **アプリケーションの制限**：「なし」のまま。GitHub Actions は毎回ちがうサーバーで動くので、IP アドレスでは制限できません。
6. 「保存」を押し、キーの文字列をコピーします。

### B. GitHub の Secrets に入れる

1. リポジトリの「Settings」→ 左の「Secrets and variables」→「Actions」を開きます。
2. 「New repository secret」を押します。
3. 「Name」に **`YOUTUBE_API_KEY`** と入れます（1文字でも違うと動きません）。
4. 「Secret」にコピーしたキーを貼り、「Add secret」を押します。

### C. 動くか確かめる

1. リポジトリの上の「Actions」タブを開きます。「ワークフローを有効にしますか」と出たら、有効にするボタンを押します。
2. 左の「動画IDの取り直し」を選び、右の「Run workflow」→ 緑の「Run workflow」を押します。
3. 1〜2分で緑のチェックが付けば成功です。`data/videos.json` の日付が今日になります。
4. 赤い×が付いたら、その行を押してログを開きます。
   - 「YOUTUBE_API_KEY が設定されていません」→ B の名前が違うか、入れ忘れています。
   - 「HTTP Error 400」「403」→ キーが違うか、A-5 の制限で YouTube Data API v3 を選び忘れています。
   - 「Permission denied」「403」で `git push` が失敗 →「公開までの手順」の 2 を確かめてください。

### キーを安全に扱うために

- キーを `data/` などのファイル、Issues、チャット、メールに書かないでください。公開リポジトリのファイルは誰でも読めます。
- Secrets に入れたキーは、あとから GitHub の画面で見ることはできません（上書きはできます）。Actions のログでも `***` と伏せられます。
- キーが漏れたかもしれないときは、Google Cloud でそのキーを削除して新しく作り、B の手順で同じ名前の Secret を上書きしてください。

---

## 週1回の取り直しについて

- 毎週月曜 12時17分（日本時間）ごろに「動画IDの取り直し」が動きます。GitHub が混んでいると遅れたり飛ばされたりしますが、3回続けて飛ばされても28日目には取り直せます。
- 取り直しで、削除・非公開・埋め込み不可・子ども向けになった動画が見つかると、その動画をサイトから外します。動画が0本になった店は、店ページごと外れます（ページを書き出すときに `docs/` から消えます）。
- 最後に取り直してから30日を超えた動画も、書き出すときに外します。YouTube API のデータは30日を超えて持てないからです（デベロッパー ポリシー III.E.4.d）。
- **今の `data/videos.json` は 2026年11月2日に取り直したものです。12月2日より前に、上の C で1回動かしてください。** 動かさないまま書き出すと、すべての動画が外れます。
- Actions が止まっている間は、書き出しも行われず、古いページが公開されたまま残ります。月に1回は「Actions」タブを開き、「動画IDの取り直し」に緑のチェックが続いているか見てください。止まっていたら「Enable workflow」や「Run workflow」で動かします。

---

## 店を直す・足す

`data/shops.json` の1店は、次の形です。

```json
{
  "id": "s001",                 // 変えない
  "slug": "s001",               // ページのURLの最後の部分（英数字とハイフン）
  "name": "店名",
  "reading": "",                // 読み（ふりがな）。空なら表示しない
  "subprefecture": "ishikari",  // data/areas.json の振興局の slug
  "town": "札幌市",              // data/areas.json の市町村名
  "town_slug": "sapporo",
  "address": "札幌市中央区…",
  "lat": 43.05, "lon": 141.35,   // ピンの位置（緯度・経度）
  "position_method": "ピンの決め方",
  "videos": ["YouTubeの動画ID"],  // 1〜3本
  "menu_name": "",              // 店での呼び方（メニュー表記）。空なら表示しない
  "features": "",               // ザンギの特徴（2〜3行、自分の言葉で）。空なら表示しない
  "official_links": [{"label": "公式サイト", "url": "https://…"}],
  "checked_on": "2026-11-02"     // 店の情報を確かめた日
}
```

- 実際のファイルに `//` の説明は書けません（上は説明のためのものです）。
- 直して「Commit changes」を押すと、「ページの書き出し」が動いて反映されます。
- 動画を足したときは、そのあと「動画IDの取り直し」を手で1回動かしてください。取り直すまで、新しい動画は載りません。
- 今の55店は、`reading`（読み）、`menu_name`（店での呼び方）、`features`（ザンギの特徴）が空です。企画書では自分の言葉で書く項目なので、書いた店から表示されます。

## 自分のパソコンで書き出す（任意）

Python 3 があれば、リポジトリのフォルダーで次を実行すると `docs/` に書き出せます。

```
python3 scripts/build.py
```

## 出典と帰属表示

「このサイトについて」（`templates/about.html`）に、地図（OpenStreetMap）、店の位置（OpenStreetMap・国土交通省 位置参照情報・Nominatim）、動画（YouTube 利用規約）の出典と、プライバシーポリシー、連絡先を載せています。広告は載せない方針です（YouTube API デベロッパー ポリシー III.G.1.d）。
