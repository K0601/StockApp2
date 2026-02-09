from config import TICKERS, INTERVALS
from db.database import init_db, insert_dataframe, get_latest_datetime
from data.fetcher import fetch_data
from indicators.technicals import add_technicals
import pandas as pd
from flask import Flask

app = Flask(__name__)

def clean_nan(df):
    return df.ffill()

def process_ticker(ticker, time_interval):
    print(f"処理中: {ticker} ({time_interval})")

    latest = get_latest_datetime(ticker, time_interval)

    df = fetch_data(ticker, time_interval, start=latest)

    if df is None or df.empty:
        print("データ取得失敗 or データなし")
        return

    # ★ ここ超重要
    df["ticker"] = ticker
    df["time_interval"] = time_interval

    df = add_technicals(df)
    df = clean_nan(df)

    try:
        insert_dataframe(df)
        print("保存完了")
    except Exception as e:
        print("保存エラー:", e)


def run_update():
    init_db()
    for ticker in TICKERS:
        for time_interval in INTERVALS:
            process_ticker(ticker, time_interval)
    print("全処理完了")


# HTTP リクエストで実行
@app.route('/')
def index():
    run_update()
    return "Stock data update completed!"


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting Flask on port {port}...", flush=True)
    app.run(host="0.0.0.0", port=port)
