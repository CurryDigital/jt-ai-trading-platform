from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.session import Base
import datetime

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    purchase_price = Column(Float)
    quantity = Column(Integer)
    purchase_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="held") # held, sold
