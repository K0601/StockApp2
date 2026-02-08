from config import TICKERS, INTERVALS
from db.database import init_db, insert_dataframe, get_latest_datetime
from data.fetcher import fetch_data
from indicators.technicals import add_technicals
import pandas as pd


def clean_nan(df):
    return df.fillna(method="ffill")

def process_ticker(ticker, interval):

    print(f"処理中: {ticker} ({interval})")

    latest = get_latest_datetime(ticker, interval)

    df = fetch_data(ticker, interval, start=latest)

    if df is None:
        print("データ取得失敗")
        return

    df = add_technicals(df)
    df = clean_nan(df)

    try:
        insert_dataframe(df)
        print("保存完了")
    except Exception as e:
        print("重複 or 保存エラー:", e)


def main():

    init_db()

    for ticker in TICKERS:
        for interval in INTERVALS:
            process_ticker(ticker, interval)

    print("全処理完了")


if __name__ == "__main__":
    main()
