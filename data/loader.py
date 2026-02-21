# data/loader.py

import sqlite3
import pandas as pd


def load_price_data(db_path, ticker, interval, from_date=None, to_date=None):
    conn = sqlite3.connect(db_path)

    query = """
        SELECT *
        FROM price_data
        WHERE ticker = ?
          AND interval = ?
    """

    params = [ticker, interval]

    if from_date:
        query += " AND datetime >= ?"
        params.append(from_date)

    if to_date:
        query += " AND datetime <= ?"
        params.append(to_date)

    query += " ORDER BY datetime"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if df.empty:
        return df

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime").sort_index()

    return df


def load_multi_ticker_data(db_path, tickers, interval):
    dfs = []

    for ticker in tickers:
        df = load_price_data(db_path, ticker, interval)
        if not df.empty:
            df["ticker"] = ticker
            dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs)
