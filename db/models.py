from sqlalchemy import Column, String, Float, DateTime, Integer, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class PriceData(Base):
    __tablename__ = "price_data"

    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), nullable=False)
    datetime = Column(DateTime, nullable=False)
    time_interval = Column(String(10), nullable=False)

    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

    __table_args__ = (
        UniqueConstraint("ticker", "datetime", "time_interval", name="unique_price"),
    )
