# config.py

TICKERS = [
    "^N225",
    #"^TPX",TOPIXのデータは取得できない模様
    "^DJI",
    "^GSPC", #S&P500
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

DB_NAME = "stock.db"
