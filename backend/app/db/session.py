from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./trading.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    status = Column(String, default="Active")
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Signal(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    ticker = Column(String, index=True)
    ts_score = Column(Float)
    sent_score = Column(Float)
    alpha_score = Column(Float)
    final_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class PredictionAudit(Base):
    __tablename__ = "prediction_audit"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    predicted_score = Column(Float)
    predicted_price = Column(Float)
    actual_price = Column(Float, nullable=True)
    error_rate = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)
