from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict
import uuid

# Internal Imports
from app.db.session import SessionLocal, Project as DBProject, Signal as DBSignal
from app.schemas.project import Project, ProjectCreate, Signal, AnalysisResult
from app.core_logic.models.orchestrator import ModelOrchestrator

app = FastAPI(title="JT Orchestra API")
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

def run_background_analysis(ticker: str, task_id: str):
    try:
        signals_df = orchestrator.run_full_pipeline([ticker])
        if not signals_df.empty:
            res = signals_df.iloc[0].to_dict()
            score = res['final_score']
            analysis_cache[task_id] = {
                "status": "complete",
                "data": {
                    "ticker": ticker,
                    "recommendation": "BUY" if score > 0.3 else "SELL" if score < -0.3 else "HOLD",
                    "confidence": score,
                    "forecasts": {"7d": f"{res['ts_signal']*100:+.1f}%", "14d": f"{res['ts_signal']*140:+.1f}%"},
                    "metrics": {"ts_score": res['ts_signal'], "sent_score": res['sent_signal'], "alpha_score": res['alpha_signal']}
                }
            }
    except Exception as e:
        analysis_cache[task_id] = {"status": "error", "message": str(e)}

@app.get("/api/analyze/{ticker}")
def start_analysis(ticker: str, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    analysis_cache[task_id] = {"status": "processing"}
    background_tasks.add_task(run_background_analysis, ticker, task_id)
    return {"task_id": task_id}

from app.core_logic.backtesting.backtester import Backtester

@app.get("/api/backtest/{project_id}")
def run_project_backtest(project_id: int, db: Session = Depends(get_db)):
    """
    Runs a historical simulation for the last 30 days.
    """
    try:
        # 1. Fetch historical signals from DB
        signals = db.query(DBSignal).filter(DBSignal.project_id == project_id).all()
        signal_df = pd.DataFrame([s.__dict__ for s in signals])
        
        # 2. Fetch historical price data
        price_path = "/home/ubuntu/.openclaw/workspace/data/processed/hk_stocks_features.csv"
        price_df = pd.read_csv(price_path)
        price_df.columns = [c.lower() for c in price_df.columns]
        
        # 3. Run Backtest
        bt = Backtester()
        results, metrics = bt.run(signal_df, price_df)
        
        return {
            "metrics": metrics,
            "equity_curve": results[['date', 'strategy_returns']].tail(30).to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from app.services.macro_service import macro_service

@app.get("/api/macro/pulse")
def get_macro_pulse():
    return macro_service.get_market_pulse()

@app.get("/api/projects", response_model=List[Project])
def get_projects(db: Session = Depends(get_db)): return db.query(DBProject).all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
