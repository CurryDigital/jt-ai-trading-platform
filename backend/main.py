from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add root to path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.orchestrator import ModelOrchestrator

app = FastAPI()

# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = ModelOrchestrator()

@app.get("/api/signals")
def get_signals():
    # In a real app, we'd cache this or load from DB
    # For now, we'll run a subset for the UI
    try:
        tickers = ["0700.HK", "9988.HK", "3690.HK", "1211.HK", "2318.HK"]
        signals_df = orchestrator.run_full_pipeline(tickers)
        return signals_df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/status")
def get_status():
    return {"status": "online", "model": "gpt-4.1-nano"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
