# 1. 公式のPython軽量イメージをベースにする
FROM python:3.12-slim

# 2. コンテナ内の作業ディレクトリを設定
WORKDIR /app

# 3. 依存ライブラリのリストをコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. ローカルのコードをすべてコンテナ内にコピー
COPY . .

# 5. FastAPIサーバーを起動するコマンド（0.0.0.0で外部からの接続を許可）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]