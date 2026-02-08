import pandas as pd


def add_technicals(df):

    # ボリンジャーバンド
    df["bb_middle"] = df["close"].rolling(20).mean()
    df["bb_std"] = df["close"].rolling(20).std()
    df["bb_upper"] = df["bb_middle"] + 2 * df["bb_std"]
    df["bb_lower"] = df["bb_middle"] - 2 * df["bb_std"]

    # MACD
    ema12 = df["close"].ewm(span=12).mean()
    ema26 = df["close"].ewm(span=26).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9).mean()

    # ゴールデンクロス
    sma_short = df["close"].rolling(5).mean()
    sma_long = df["close"].rolling(25).mean()
    df["golden_cross"] = ((sma_short > sma_long) &
                          (sma_short.shift(1) <= sma_long.shift(1))).astype(int)

    return df
