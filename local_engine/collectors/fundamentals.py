import os
import time
import random
import yfinance as yf
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from loguru import logger

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase URL or Key is missing in .env file.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_universe_symbols():
    try:
        response = supabase.table("universe").select("symbol").execute()
        return [row["symbol"] for row in response.data]
    except Exception as e:
        logger.error(f"Failed to fetch universe symbols: {e}")
        return []

def fetch_and_store_fundamentals():
    logger.info("Starting Weekly Fundamentals Collector...")
    symbols = get_universe_symbols()
    
    if not symbols:
        logger.error("No symbols found in the universe table.")
        return False
        
    logger.info(f"Loaded {len(symbols)} active symbols. Fetching fundamentals via yfinance...")
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    updates = []
    failed_symbols = []
    
    # We use a small subset for testing in dev, or all for production
    # Here we process all, with rate-limiting.
    for i, symbol in enumerate(symbols):
        try:
            # Append .NS for Indian NSE stocks in yfinance
            yf_symbol = f"{symbol}.NS"
            ticker = yf.Ticker(yf_symbol)
            
            # Use info dictionary
            info = ticker.info
            
            # If info is empty or fundamentally broken, skip safely.
            if not info or ('trailingPE' not in info and 'returnOnEquity' not in info):
                 logger.debug(f"[{symbol}] No valid fundamentals found via yfinance. Skipping.")
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
            logger.info(f"[{i+1}/{len(symbols)}] {symbol}: Successfully fetched fundamentals.")
            
        except Exception as e:
            logger.warning(f"[{i+1}/{len(symbols)}] {symbol}: Failed to fetch fundamentals: {e}")
            failed_symbols.append(symbol)
            
        # Rate-limiting: Randomized 2-3 second delay to avoid yfinance blacklisting/rate-limits
        delay = random.uniform(2.0, 3.0)
        time.sleep(delay)
        
    if not updates:
        logger.error("No fundamentals collected. Aborting upsert.")
        return False
        
    logger.info(f"Collected fundamentals for {len(updates)}/{len(symbols)} symbols. Upserting to Supabase...")
    
    try:
        # Upsert requires primary key match. (symbol, as_of_date) is the PK.
        supabase.table("fundamentals_weekly").upsert(updates).execute()
        logger.info("Successfully upserted fundamentals to Supabase.")
        return True
    except Exception as e:
        logger.error(f"Failed to upsert fundamentals to Supabase: {e}")
        return False

if __name__ == "__main__":
    fetch_and_store_fundamentals()
