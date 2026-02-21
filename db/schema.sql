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

CREATE TABLE IF NOT EXISTS training_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT,
    interval TEXT,
    episode INTEGER,
    reward REAL,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS trade_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT,
    datetime TEXT,
    action TEXT,
    price REAL
);

