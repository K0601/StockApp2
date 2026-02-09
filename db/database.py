import pandas as pd
from sqlalchemy import create_engine, text
from config import DB_USER, DB_PASSWORD, DB_NAME, DB_SOCKET_PATH
from db.models import Base

def get_engine():
    return create_engine(
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}"
        f"?unix_socket={DB_SOCKET_PATH}"
    )

def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("テーブル作成完了")

def insert_dataframe(df):

    if df.empty:
        print("追加データなし")
        return

    engine = get_engine()

    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    df = df.dropna(subset=['datetime'])

    insert_sql = text("""
        INSERT IGNORE INTO price_data
        (ticker, datetime, `interval`, open, high, low, close, volume)
        VALUES
        (:ticker, :datetime, :interval, :open, :high, :low, :close, :volume)
    """)

    records = df.to_dict(orient="records")

    with engine.begin() as conn:
        conn.execute(insert_sql, records)

    print(f"INSERT試行件数: {len(records)}")

def get_latest_datetime(ticker, interval):

    engine = get_engine()

    query = text("""
        SELECT MAX(datetime)
        FROM price_data
        WHERE ticker=:ticker AND `interval`=:interval
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {
            "ticker": ticker,
            "interval": interval
        }).scalar()

    return result
