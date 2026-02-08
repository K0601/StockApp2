import yfinance as yf
import gspread
import pandas as pd
import sys
from google.oauth2.service_account import Credentials
from datetime import datetime
import numpy as np

# =============================
# 設定
# =============================
TICKERS = [
    "^N225",
    "^TPX",
    "^DJI",
    "^GSPC",
    "7203.T",
    "6758.T",
]
SPREADSHEET_ID = "1uH62nxdCD9SSKSMVNGXC8JQB3NViwF1ElWV_gqyUgWY"
CREDENTIALS_FILE = "credentials.json"

# 実行モード
MODE = "init"  # "init" or "update"

# =============================
# 認証
# =============================
def get_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file"
    ]
    credentials = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=scopes
    )
    return gspread.authorize(credentials)

# =============================
# 指標計算
# =============================
def add_indicators(df):

    df["SMA25"] = df["Close"].rolling(25).mean()
    df["SMA75"] = df["Close"].rolling(75).mean()
    df["GoldenCross"] = (df["SMA25"] > df["SMA75"]).astype(int)

    # ボリンジャーバンド
    sma20 = df["Close"].rolling(20).mean()
    std20 = df["Close"].rolling(20).std()
    df["BB_upper"] = sma20 + 2 * std20
    df["BB_lower"] = sma20 - 2 * std20

    # RSI
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    return df

# =============================
# 配当情報追加
# =============================
def add_dividend_info(df, ticker):

    stock = yf.Ticker(ticker)

    # 配当履歴
    df["Dividend"] = 0.0
    try:
        dividends = stock.dividends
        for date, value in dividends.items():
            if date in df.index:
                df.loc[date, "Dividend"] = value
    except:
        pass

    # 配当利回り
    try:
        info = stock.info
        dividend_yield = info.get("dividendYield", 0)
    except:
        dividend_yield = 0

    df["DividendYield"] = dividend_yield

    return df

# =============================
# データ取得
# =============================
def get_stock_data(ticker, mode):

    stock = yf.Ticker(ticker)

    if mode == "init":
        df = stock.history(period="max")
    else:
        df = stock.history(period="5d")

    if df.empty:
        return None

    df = add_indicators(df)
    df = add_dividend_info(df, ticker)

    df = df.reset_index()
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    return df

# =============================
# 欠損値対策
# =============================
def safe_value(x):
    if pd.isna(x) or x is None:
        return None
    if isinstance(x, (float, np.floating)):
        if np.isinf(x):
            return None
    return float(x) if isinstance(x, (int, float, np.number)) else x


# =============================
# シート作成（init）
# =============================
def create_sheet_if_not_exists(client, ticker):

    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    try:
        worksheet = spreadsheet.worksheet(ticker)
    except:
        worksheet = spreadsheet.add_worksheet(title=ticker, rows="2000", cols="20")

        headers = [
            "Date","Ticker","Open","High","Low","Close","Volume",
            "SMA25","SMA75","GoldenCross",
            "BB_upper","BB_lower",
            "RSI","MACD","MACD_signal",
            "Dividend","DividendYield"
        ]
        worksheet.append_row(headers)

    return worksheet

# =============================
# 重複チェック
# =============================
def get_existing_dates(sheet):
    try:
        dates = sheet.col_values(1)
        return set(dates[1:])  # ヘッダー除外
    except:
        return set()

# =============================
# 書き込み
# =============================
def write_data(sheet, df, ticker):

    existing_dates = get_existing_dates(sheet)
    rows_to_add = []

    for _, row in df.iterrows():

        if row["Date"] in existing_dates:
            continue

        rows_to_add.append([
            row["Date"],
            ticker,
            safe_value(row["Open"]),
            safe_value(row["High"]),
            safe_value(row["Low"]),
            safe_value(row["Close"]),
            safe_value(row["Volume"]),
            safe_value(row["SMA25"]),
            safe_value(row["SMA75"]),
            safe_value(row["GoldenCross"]),
            safe_value(row["BB_upper"]),
            safe_value(row["BB_lower"]),
            safe_value(row["RSI"]),
            safe_value(row["MACD"]),
            safe_value(row["MACD_signal"]),
            safe_value(row["Dividend"]),
            safe_value(row["DividendYield"])
        ])

    if rows_to_add:
        sheet.append_rows(rows_to_add)
        print(f"{ticker}: {len(rows_to_add)}件追加")
    else:
        print(f"{ticker}: 追加データなし")

# =============================
# メイン
# =============================
def main():

    client = get_client()

    for ticker in TICKERS:

        print(f"処理中: {ticker}")

        df = get_stock_data(ticker, MODE)

        if df is None:
            print("データ取得失敗")
            continue

        sheet = create_sheet_if_not_exists(client, ticker)

        write_data(sheet, df, ticker)

    print("完了")

if __name__ == "__main__":
    main()
