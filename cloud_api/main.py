import os
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)
print("ENV LOADED FROM", env_path, "KEY:", os.environ.get('SUPABASE_SERVICE_ROLE_KEY')[:5] if os.environ.get('SUPABASE_SERVICE_ROLE_KEY') else None)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import forecasts, stocks, market

app = FastAPI(title="TradeSignal Pro API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For local testing, allow all
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(forecasts.router, prefix="/api/forecasts", tags=["Forecasts"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(market.router, prefix="/api/market", tags=["Market"])

@app.get("/")
def health_check():
    return {"status": "ok", "service": "TradeSignal Pro API"}
