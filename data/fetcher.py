import yfinance as yf
import pandas as pd


def get_period_by_interval(interval, ticker=None):
    if interval == "1m":
        return "7d"
    elif interval in ["5m", "15m"]:
        return "60d"
    elif interval == "1h":
        return "730d"
    else:
        return "max"


def fetch_data(ticker, interval, start=None):
    stock = yf.Ticker(ticker)

    period = get_period_by_interval(interval, ticker)
    df = None

    if start:
        # 🔥 タイムゾーン除去
        start_clean = pd.to_datetime(start).tz_localize(None)
        df = stock.history(start=start_clean, interval=interval)
    else:
        df = stock.history(period=period, interval=interval)
    df = df.reset_index()

    # Datetime列統一
    if "Datetime" in df.columns:
        df.rename(columns={"Datetime": "datetime"}, inplace=True)
    elif "Date" in df.columns:
        df.rename(columns={"Date": "datetime"}, inplace=True)

    df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    }, inplace=True)

    df["ticker"] = ticker
    df["interval"] = interval

    df = df[[
        "ticker",
        "datetime",
        "interval",
        "open",
        "high",
        "low",
        "close",
        "volume"
    ]]

    df = df.dropna()

    return df
