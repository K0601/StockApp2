CREATE TABLE IF NOT EXISTS price_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    ticker TEXT NOT NULL,
    datetime TEXT NOT NULL,
    interval TEXT NOT NULL,

    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,

    -- ボリンジャーバンド
    bb_middle REAL,
    bb_std REAL,
    bb_upper REAL,
    bb_lower REAL,

    -- MACD
    macd REAL,
    macd_signal REAL,

    -- ゴールデンクロス
    golden_cross INTEGER,

    UNIQUE(ticker, datetime, interval)
);

