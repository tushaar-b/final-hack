import os
import time
import yfinance as yf
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from loguru import logger

load_dotenv('.env')

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch top 20 symbols from forecasts + TEGA
res = supabase.table('forecasts').select('symbol').order('conviction_score', desc=True).limit(20).execute()
symbols = [r['symbol'] for r in res.data]
if 'TEGA' not in symbols:
    symbols.append('TEGA')

logger.info(f"Fetching fundamentals for {len(symbols)} symbols quickly...")
today_str = datetime.now().strftime("%Y-%m-%d")
updates = []

for i, symbol in enumerate(symbols):
    try:
        yf_symbol = f"{symbol}.NS"
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info
        
        if not info or ('trailingPE' not in info and 'returnOnEquity' not in info):
             continue

        updates.append({
            "symbol": symbol,
            "as_of_date": today_str,
            "trailing_pe": info.get("trailingPE"),
            "debt_equity": info.get("debtToEquity"),
            "return_on_equity": info.get("returnOnEquity"),
            "revenue_growth_yoy": info.get("revenueGrowth"),
            "eps_growth_yoy": info.get("earningsGrowth"),
            "current_ratio": info.get("currentRatio")
        })
        logger.info(f"Fetched {symbol}")
    except Exception as e:
        logger.warning(f"Failed {symbol}: {e}")

if updates:
    supabase.table("fundamentals_weekly").upsert(updates).execute()
    logger.info("Successfully upserted fundamentals.")
