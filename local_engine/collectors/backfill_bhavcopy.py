import os
import time
import random
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
from loguru import logger
import bhavcopy

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase URL or Key is missing in .env file.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_existing_dates():
    """Fetch distinct dates already present in ohlcv_daily to avoid redundant fetching."""
    try:
        # Supabase API doesn't have a distinct operator natively without RPC,
        # but we can fetch dates from a highly active symbol, or just fetch all and dedup.
        # NIFTY 50 top symbol like RELIANCE is a good proxy, or we just fetch all trade_dates and set().
        # Due to limit (1000 rows default), we might need to loop or use RPC.
        # Alternatively, if we just want a rough skip, we can query a known symbol's dates.
        response = supabase.table("ohlcv_daily").select("trade_date").eq("symbol", "RELIANCE").execute()
        existing_dates = {row["trade_date"] for row in response.data}
        logger.info(f"Found {len(existing_dates)} existing dates based on RELIANCE proxy.")
        return existing_dates
    except Exception as e:
        logger.error(f"Failed to fetch existing dates from Supabase: {e}")
        return set()

def run_backfill(months=24):
    logger.info(f"Starting 24-month Bhavcopy backfill...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30 * months)
    
    # Get all business days (Mon-Fri) in the window
    b_days = pd.bdate_range(start=start_date, end=end_date)
    
    existing_dates = get_existing_dates()
    
    # Sort backwards (newest to oldest)
    b_days = sorted(b_days, reverse=True)
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for dt in b_days:
        pg_date_str = dt.strftime("%Y-%m-%d")
        nse_date_str = dt.strftime("%d-%m-%Y")
        
        if pg_date_str in existing_dates:
            logger.info(f"Skipping {pg_date_str}: already exists in DB.")
            skip_count += 1
            continue
            
        logger.info(f"Fetching bhavcopy for {nse_date_str}...")
        success = bhavcopy.fetch_and_store_bhavcopy(nse_date_str)
        
        if success:
            success_count += 1
            logger.info(f"Successfully processed {nse_date_str}.")
        else:
            # Often false because it's a holiday, but could be an API block.
            fail_count += 1
            logger.warning(f"Failed to fetch or process {nse_date_str} (might be a holiday).")
            
        # Real randomized delay to respect NSE rate limits
        delay = random.uniform(2.5, 5.5)
        logger.info(f"Sleeping for {delay:.2f} seconds...")
        time.sleep(delay)
        
    logger.info(f"Backfill Complete! Fetched: {success_count}, Skipped: {skip_count}, Failed/Holidays: {fail_count}")

if __name__ == "__main__":
    run_backfill(24)
