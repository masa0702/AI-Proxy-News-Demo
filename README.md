# AI-Proxy-News-Demo

FastAPI と Jinja2 で構築した簡易ニュース生成アプリのデモです。会見のトピックとバイアスを選ぶと、サンプルデータから質問と模範回答を取得し、Gemini (Google Generative AI) を利用してニュース記事を生成します。実際の API 呼び出しは `gemini_api` 関数でモック化されており、`.env` に API キーを設定することで本物の Gemini API を使うこともできます。

## 特長
- プルダウンメニューからトピックとバイアスを選択してニュース記事を生成
- 生成の進捗をリアルタイムで確認できるログ＆プログレスバー表示
- `data/` 配下の JSON/TXT を編集することで独自データに差し替え可能

## 必要環境
- Docker
- Docker Compose

## セットアップ
1. プロジェクトのルートに `.env` ファイルを作成し、以下のように Gemini API キーを設定します。
   ```
   GEMINI_API_KEY=あなたのAPIキー
   ```
2. リポジトリをクローンしたディレクトリで次のコマンドを実行し、コンテナを起動します。
   ```bash
   docker compose up --build
   ```
3. ブラウザで `http://localhost:8000` にアクセスするとアプリが表示されます。

## 使い方
1. トピックとバイアスをプルダウンから選択します。
2. **生成** ボタンを押すと、質問生成→回答取得→記事作成の順に処理が進みます。
3. 画面右側のログとプログレスバーで進行状況を確認できます。完了後、生成された記事が表示されます。
4. 終了する際は `Ctrl+C` で Docker Compose を停止してください。

## ファイル構成
- `app/main.py` … FastAPI アプリケーション本体
- `app/data.py` … サンプルデータ読み込みユーティリティ
- `app/templates/index.html` … フロントエンドテンプレート
- `data/` … トピックやバイアスなどのサンプル JSON/TXT
- `Dockerfile` … アプリイメージのビルド定義
- `docker-compose.yml` … コンテナ起動設定
- `requirements.txt` … 依存 Python パッケージ

Gemini API を利用する場合は `app/main.py` の `gemini_api` 関数をそのまま使用し、`.env` に API キーを指定してください。
