import os
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from supabase import create_client, Client
from loguru import logger

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase URL or Key is missing in .env file.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TICKERS = {
    "nifty_50": "^NSEI",
    "india_vix": "^INDIAVIX",
    "usd_inr": "USDINR=X"
}

def fetch_macro_data(months=24):
    logger.info(f"Starting {months}-month Macro Data backfill...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30 * months)
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    # DataFrame to hold combined data
    combined_df = pd.DataFrame()
    
    for key, symbol in TICKERS.items():
        logger.info(f"Downloading {symbol} ({key})...")
        try:
            df = yf.download(symbol, start=start_str, end=end_str, progress=False)
            if df.empty:
                logger.warning(f"No data found for {symbol}!")
                continue
                
            # yfinance returns MultiIndex columns if multiple tickers are passed, 
            # but single ticker returns standard columns. Let's safely extract Close.
            if isinstance(df.columns, pd.MultiIndex):
                # Flatten or select the specific ticker
                close_series = df['Close'][symbol]
            else:
                close_series = df['Close']
                
            close_series.name = key
            
            if combined_df.empty:
                combined_df = close_series.to_frame()
            else:
                combined_df = combined_df.join(close_series, how="outer")
                
        except Exception as e:
            logger.error(f"Failed to download {symbol}: {e}")
            
    if combined_df.empty:
        logger.error("No macro data could be fetched. Aborting.")
        return
        
    # Forward fill missing values (e.g. holidays in one market but not another)
    combined_df = combined_df.ffill()
    # Drop rows where Nifty 50 is missing (since Nifty calendar is our master calendar)
    combined_df = combined_df.dropna(subset=['nifty_50'])
    
    # Prepare records for Supabase
    records = []
    for date_idx, row in combined_df.iterrows():
        # yfinance index is timezone-aware or naive datetime. Convert to string date.
        trade_date = date_idx.strftime("%Y-%m-%d")
        
        records.append({
            "trade_date": trade_date,
            "nifty_50": float(row.get('nifty_50', 0)),
            "india_vix": float(row.get('india_vix', 0)),
            "usd_inr": float(row.get('usd_inr', 0))
        })
        
    if not records:
        logger.error("No valid macro records prepared for upload.")
        return
        
    logger.info(f"Prepared {len(records)} macro records for Supabase. Upserting...")
    
    # Upload to Supabase (upsert)
    # We can batch them if there are too many, but 2 years is ~500 rows, easily fits in one call.
    try:
        response = supabase.table("macro_daily").upsert(records, on_conflict="trade_date").execute()
        logger.info(f"Successfully upserted {len(response.data)} macro rows into macro_daily.")
    except Exception as e:
        logger.error(f"Supabase upsert failed: {e}")

if __name__ == "__main__":
    # We might need to pip install yfinance if not installed
    fetch_macro_data(24)
