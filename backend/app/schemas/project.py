from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

class SignalBase(BaseModel):
    ticker: str
    ts_score: float
    sent_score: float
    alpha_score: float
    final_score: float

class SignalCreate(SignalBase):
    project_id: int

class Signal(SignalBase):
    id: int
    project_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "Active"

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    created_at: datetime
    signals: List[Signal] = []

    class Config:
        from_attributes = True

class AnalysisResult(BaseModel):
    ticker: str
    recommendation: str
    confidence: float
    forecasts: Dict[str, str]
    metrics: Dict[str, float]
