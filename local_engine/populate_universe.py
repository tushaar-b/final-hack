import os
import io
import pandas as pd
import requests
from dotenv import load_dotenv
from supabase import create_client, Client
from loguru import logger

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or SUPABASE_URL == "YOUR_SUPABASE_URL_HERE":
    logger.error("Supabase URL or Key is missing/placeholder in .env file.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_nifty500_universe():
    url = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/csv,application/csv",
    }
    
    logger.info(f"Fetching Nifty 500 list from: {url}")
    session = requests.Session()
    # Ping main site to get cookies to bypass simple bot protection
    session.get("https://www.nseindia.com", headers=headers, timeout=10)
    
    response = session.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    df = pd.read_csv(io.StringIO(response.text))
    return df

def populate_universe():
    df = fetch_nifty500_universe()
    
    # Expected columns: ['Company Name', 'Industry', 'Symbol', 'Series', 'ISIN Code']
    # Map to schema: symbol, company_name, sector, is_active
    
    if "Symbol" not in df.columns:
        logger.error(f"Unexpected CSV format. Columns found: {df.columns.tolist()}")
        return

    # Prepare list of dictionaries for Supabase upsert
    records = []
    for _, row in df.iterrows():
        records.append({
            "symbol": str(row["Symbol"]).strip(),
            "company_name": str(row["Company Name"]).strip(),
            "sector": str(row["Industry"]).strip(),
            "is_active": True
        })
        
    logger.info(f"Prepared {len(records)} records for upsert.")
    
    # Upsert to Supabase
    try:
        # We can upsert in chunks if necessary, but 500 rows is small enough for a single request
        response = supabase.table("universe").upsert(records, on_conflict="symbol").execute()
        logger.info(f"Successfully upserted {len(response.data)} records into the universe table.")
    except Exception as e:
        logger.error(f"Failed to upsert to Supabase: {e}")

if __name__ == "__main__":
    populate_universe()
