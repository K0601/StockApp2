# Python 3.11 ベース
FROM python:3.11-slim

# 作業ディレクトリ
WORKDIR /app

# 依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# Cloud Run が PORT 環境変数を提供
ENV PORT 8080
EXPOSE 8080

# Flask アプリを起動
CMD ["python", "-u", "main.py"]
