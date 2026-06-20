import os
import argparse
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
from loguru import logger
from nselib import capital_market

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase URL or Key is missing in .env file.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_universe_symbols():
    """Fetch active symbols from the Supabase universe table."""
    try:
        response = supabase.table("universe").select("symbol").eq("is_active", True).execute()
        symbols = [row["symbol"] for row in response.data]
        logger.info(f"Loaded {len(symbols)} active symbols from universe.")
        return symbols
    except Exception as e:
        logger.error(f"Failed to fetch universe from Supabase: {e}")
        return []

def fetch_and_store_bhavcopy(trade_date_str: str):
    """
    Fetch bhavcopy for the given date, filter by universe, and upload to Supabase.
    trade_date_str should be in 'DD-MM-YYYY' format for nselib.
    """
    logger.info(f"Fetching Bhavcopy for date: {trade_date_str}")
    try:
        df = capital_market.bhav_copy_with_delivery(trade_date_str)
    except Exception as e:
        logger.error(f"Failed to fetch bhavcopy for {trade_date_str}: {e}")
        # Return False to indicate failure to the orchestrator
        return False
        
    if df is None or df.empty:
        logger.error(f"Bhavcopy returned empty for date: {trade_date_str}")
        return False

    # Get active universe
    universe = get_universe_symbols()
    if not universe:
        logger.error("Universe is empty or could not be loaded. Aborting.")
        return False
        
    universe_set = set(universe)
    
    # Filter bhavcopy to only include universe symbols
    # Note: nselib usually returns 'SYMBOL' column
    if 'SYMBOL' not in df.columns:
        logger.error(f"Expected 'SYMBOL' column in bhavcopy but found: {df.columns.tolist()}")
        return False
        
    # Convert nselib date string to standard YYYY-MM-DD for postgres
    # nselib date format depends on the specific endpoint, but 'DATE1' is usually something like '17-Jun-2026' or '17-06-2026'
    # We will use the input trade_date_str to construct our standard DATE format, 
    # but first let's parse it properly.
    try:
        parsed_date = datetime.strptime(trade_date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
    except ValueError:
        logger.error(f"Invalid date format for {trade_date_str}. Expected DD-MM-YYYY")
        return False
        
    # Filter
    df_filtered = df[df['SYMBOL'].isin(universe_set)].copy()
    
    # Drop rows that aren't the primary equity series (EQ) to prevent duplicates (e.g., BE, SM, IL)
    if 'SERIES' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['SERIES'] == 'EQ']
        
    logger.info(f"Filtered bhavcopy from {len(df)} down to {len(df_filtered)} universe stocks.")
    
    if df_filtered.empty:
        logger.warning(f"No universe stocks found in bhavcopy for {trade_date_str}. Was it a trading holiday?")
        return False
        
    # Prepare records for Supabase
    # Target schema: symbol, trade_date, open, high, low, close, volume, delivery_pct
    records = []
    
    # Clean up column names and convert types
    # nselib columns typically: ['SYMBOL', 'SERIES', 'DATE1', 'PREV_CLOSE', 'OPEN_PRICE', 'HIGH_PRICE', 'LOW_PRICE', 'LAST_PRICE', 'CLOSE_PRICE', 'AVG_PRICE', 'TTL_TRD_QNTY', 'TURNOVER_LACS', 'NO_OF_TRADES', 'DELIV_QTY', 'DELIV_PER']
    
    # Fill NaN values for DELIV_PER, etc. with 0
    df_filtered.fillna({'DELIV_PER': 0, 'TTL_TRD_QNTY': 0}, inplace=True)
    
    for _, row in df_filtered.iterrows():
        try:
            # Safely handle 'DELIV_PER' which might be strings like '-' if no delivery occurred
            deliv_per = str(row.get('DELIV_PER', 0)).replace('-', '0')
            try:
                deliv_per_val = float(deliv_per)
            except ValueError:
                deliv_per_val = 0.0
                
            records.append({
                "symbol": str(row['SYMBOL']).strip(),
                "trade_date": parsed_date,
                "open": float(row['OPEN_PRICE']),
                "high": float(row['HIGH_PRICE']),
                "low": float(row['LOW_PRICE']),
                "close": float(row['CLOSE_PRICE']),
                "volume": int(row['TTL_TRD_QNTY']),
                "delivery_pct": deliv_per_val
            })
        except Exception as e:
            logger.error(f"Error parsing row for {row.get('SYMBOL', 'UNKNOWN')}: {e}")
            continue
            
    if not records:
        logger.error("No valid records prepared for upload.")
        return False
        
    logger.info(f"Prepared {len(records)} records for Supabase.")
    
    # Upload to Supabase
    try:
        response = supabase.table("ohlcv_daily").upsert(records, on_conflict="symbol, trade_date").execute()
        logger.info(f"Successfully upserted {len(response.data)} bhavcopy rows into ohlcv_daily.")
        return True
    except Exception as e:
        logger.error(f"Supabase upsert failed: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and store bhavcopy for universe stocks")
    parser.add_argument("--date", type=str, help="Date in DD-MM-YYYY format. Defaults to today.")
    
    args = parser.parse_args()
    
    if args.date:
        target_date = args.date
    else:
        target_date = datetime.now().strftime("%d-%m-%Y")
        
    fetch_and_store_bhavcopy(target_date)
