# config.py

TICKERS = [
    "^N225",
    #"^TPX",TOPIXのデータは取得できない模様
    "^DJI",
    "^GSPC",
    "7203.T",
]

INTERVALS = [
    "1m",
    "5m",
    "15m",
    "1h",
    "1d",
    "1wk",
    "1mo",
]

DB_NAME = "stockdb"


DB_USER = "StockDB"
DB_PASSWORD = "Kenken0601"

DB_SOCKET_PATH = "/cloudsql/stockextract-486708:asia-northeast1:free-trial-first-project"

