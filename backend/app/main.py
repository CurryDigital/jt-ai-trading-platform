from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict
import io
import pandas as pd
import uuid
import os

# Internal Imports
from app.db.session import SessionLocal, Project as DBProject, Signal as DBSignal
from app.schemas.project import Project, Signal, AnalysisResult
from app.services.macro_service import macro_service
from app.core_logic.models.orchestrator import ModelOrchestrator

app = FastAPI()
orchestrator = ModelOrchestrator()
analysis_cache: Dict[str, dict] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.on_event("startup")
def startup_event():
    # Ensure database is seeded on start
    db = SessionLocal()
    if db.query(DBSignal).count() == 0:
        print("Seeding permanent Top 20 HK assets...")
        seeds = [
            {'t': '0700.HK', 'ts': 0.85, 'f': 0.82}, {'t': '9988.HK', 'ts': 0.72, 'f': 0.78},
            {'t': '3690.HK', 'ts': 0.65, 'f': 0.72}, {'t': '1211.HK', 'ts': 0.58, 'f': 0.65},
            {'t': 'NVDA', 'ts': 0.95, 'f': 0.92}, {'t': '0197.HK', 'ts': 0.12, 'f': 0.62},
            {'t': '0005.HK', 'ts': 0.25, 'f': 0.58}, {'t': 'AAPL', 'ts': 0.35, 'f': 0.75},
            {'t': 'KO', 'ts': 0.05, 'f': 0.55}, {'t': 'JPM', 'ts': 0.15, 'f': 0.68},
            {'t': '1810.HK', 'ts': 0.77, 'f': 0.74}, {'t': '2318.HK', 'ts': 0.44, 'f': 0.51},
            {'t': '0388.HK', 'ts': 0.32, 'f': 0.45}, {'t': '0883.HK', 'ts': 0.61, 'f': 0.68},
            {'t': '1024.HK', 'ts': 0.52, 'f': 0.48}, {'t': '9618.HK', 'ts': 0.41, 'f': 0.38},
            {'t': '2331.HK', 'ts': 0.28, 'f': 0.31}, {'t': '2269.HK', 'ts': 0.15, 'f': 0.22},
            {'t': '0669.HK', 'ts': 0.33, 'f': 0.41}, {'t': '1109.HK', 'ts': 0.45, 'f': 0.49}
        ]
        for s in seeds:
            sig = DBSignal(project_id=1, ticker=s['t'], ts_score=s['ts'], sent_score=0.6, alpha_score=0.5, final_score=s['f'])
            db.add(sig)
        db.commit()
    db.close()

@app.get("/api/status")
def status(): return {"status": "online"}

from app.services.quant_service import quant_service

@app.get("/api/quants/volatility")
def get_fx_volatility():
    return quant_service.calculate_volatility_signals()

@app.get("/api/signals/{project_id}")
def get_signals(db: Session = Depends(get_db)):
    return db.query(DBSignal).all()

@app.get("/api/export/excel")
def export_excel(db: Session = Depends(get_db)):
    try:
        signals = db.query(DBSignal).all()
        data = []
        for s in signals:
            data.append({
                "Ticker": s.ticker,
                "Trend Score": s.ts_score,
                "Sentiment Score": s.sent_score,
                "Alpha Score": s.alpha_score,
                "Final Edge Score": s.final_score,
                "Expected Return (7D)": f"{s.ts_score * 10:+.2f}%",
                "Timestamp": s.timestamp
            })
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Forecasts')
        
        output.seek(0)
        headers = {
            'Content-Disposition': 'attachment; filename="orchestra_forecasts.xlsx"'
        }
        return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analyze/{ticker}")
def start_analysis(ticker: str, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    analysis_cache[task_id] = {"status": "processing"}
    # Background logic here...
    return {"task_id": task_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
