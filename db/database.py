import sqlite3
import pandas as pd
from data.config import DB_NAME

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    with open("db/schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

def insert_dataframe(df):
    """
    DataFrame を SQLite に挿入する関数。
    - ticker, datetime, interval の組み合わせが UNIQUE 制約
    - 既存データと重複する行はログに表示して挿入しない
    - datetime 型とタイムゾーンを安全に統一
    """

    conn = get_connection()

    try:
        # ===============================
        # 1. データ型の統一
        # ===============================
        # df['datetime'] を datetime 型に変換
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce', utc=True)
        if df['datetime'].isnull().any():
            print("警告: df['datetime'] に NaT が含まれています")

        # 既存データを取得
        existing = pd.read_sql(
            "SELECT ticker, datetime, interval FROM price_data",
            conn
        )

        if not existing.empty:
            existing['datetime'] = pd.to_datetime(existing['datetime'], errors='coerce', utc=True)
            existing = existing.dropna(subset=['datetime'])

            # ===============================
            # 2. タイムゾーンを df に合わせる
            # ===============================
            if df['datetime'].dt.tz is not None:
                existing['datetime'] = existing['datetime'].dt.tz_convert(df['datetime'].dt.tz)

            # ===============================
            # 3. 新規データだけ抽出
            # ===============================
            merged = pd.merge(
                df,
                existing,
                on=["ticker", "datetime", "interval"],
                how="left",
                indicator=True
            )
            new_rows = merged[merged["_merge"] == "left_only"]
            new_rows = new_rows[df.columns]  # 元の列順に戻す
        else:
            print("既存データなし")
            new_rows = df

        # ===============================
        # 4. 新規データ挿入
        # ===============================
        if not new_rows.empty:
            # 重複がある場合を先にチェックしてログ出力
            if not existing.empty:
                conflict_rows = pd.merge(
                    new_rows,
                    existing[['ticker', 'datetime', 'interval']],
                    on=['ticker', 'datetime', 'interval'],
                    how='inner'
                )
                if not conflict_rows.empty:
                    print("重複行があるため挿入できません:")
                    print(conflict_rows)

            # 重複を削除してから挿入
            insert_rows = new_rows.drop_duplicates(subset=['ticker', 'datetime', 'interval'])

            # SQLite に追加
            try:
                insert_rows.to_sql("price_data", conn, if_exists="append", index=False)
                print(f"追加された行数: {len(insert_rows)}")
            except sqlite3.IntegrityError as e:
                print("SQLite 挿入エラー:", e)
        else:
            print("追加する新規データはありませんでした")

    finally:
        conn.close()


def get_latest_datetime(ticker, interval):
    conn = get_connection()

    query = """
    SELECT MAX(datetime)
    FROM price_data
    WHERE ticker=? AND interval=?
    """

    result = conn.execute(query, (ticker, interval)).fetchone()
    conn.close()

    return result[0]
