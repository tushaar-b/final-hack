import os
import re
import random
from datetime import datetime
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from loguru import logger
import feedparser

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase URL or Key is missing in .env file.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

RSS_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "https://www.moneycontrol.com/rss/buzzingstocks.xml",
    "https://www.livemint.com/rss/markets"
]

def clean_company_name(name: str) -> str:
    """Strip corporate suffixes to improve substring matching."""
    # Remove things like " Limited", " Ltd.", " Corporation", etc.
    pattern = r'(?i)\s*(limited|ltd\.?|corporation|corp\.?|company|co\.?|l\.t\.d|inc\.?)\s*$'
    cleaned = re.sub(pattern, '', name).strip()
    return cleaned

def fetch_universe():
    try:
        response = supabase.table("universe").select("symbol, company_name").eq("is_active", True).execute()
        universe = response.data
        
        # Pre-compute cleaned names
        for row in universe:
            row['cleaned_name'] = clean_company_name(row['company_name'])
            
        logger.info(f"Loaded {len(universe)} active symbols from universe.")
        return universe
    except Exception as e:
        logger.error(f"Failed to fetch universe: {e}")
        return []

def match_headline_to_symbols(headline: str, universe: list) -> list:
    """
    Returns a list of unique symbols that match the headline.
    Handles subset collisions (e.g. "Reliance Industries" beats "Reliance").
    """
    matches = []
    
    for row in universe:
        symbol = row['symbol']
        cleaned_name = row['cleaned_name']
        
        match_found = False
        match_string = ""
        
        # 1. Company Name Match (Case-Insensitive, but with Word Boundaries to prevent 'Bitcoin' matching 'ITC')
        if cleaned_name and re.search(rf'\b{re.escape(cleaned_name)}\b', headline, re.IGNORECASE):
            match_found = True
            match_string = cleaned_name
            
        # 2. Symbol Match (Case-Sensitive Word Boundary)
        # We only do this if we haven't already matched the name, or we can check both.
        if not match_found:
            # Case-sensitive to avoid 'IDEA' matching 'idea'
            if re.search(rf'\b{re.escape(symbol)}\b', headline):
                match_found = True
                match_string = symbol
                
        if match_found:
            matches.append({
                'symbol': symbol,
                'match_string': match_string
            })
            
    # Resolve Collisions (Subset elimination)
    # Sort matches by length descending so longer strings process first
    matches.sort(key=lambda x: len(x['match_string']), reverse=True)
    
    final_symbols = set()
    accepted_strings = []
    
    for m in matches:
        m_str_lower = m['match_string'].lower()
        is_subset = False
        
        for acc_str in accepted_strings:
            if m_str_lower in acc_str.lower() and m_str_lower != acc_str.lower():
                is_subset = True
                break
                
        if not is_subset:
            final_symbols.add(m['symbol'])
            accepted_strings.append(m['match_string'])
            
    return list(final_symbols)

def run_news_collector():
    logger.info("Starting News RSS Collector...")
    universe = fetch_universe()
    
    if not universe:
        logger.error("Empty universe. Aborting.")
        return False
        
    all_records = []
    matched_pairs_for_verification = []
    
    for feed_url in RSS_FEEDS:
        logger.info(f"Fetching RSS feed: {feed_url}")
        feed = feedparser.parse(feed_url)
        
        if feed.bozo:
            logger.warning(f"Feed {feed_url} may be malformed. Error: {feed.bozo_exception}")
            
        for entry in feed.entries:
            headline = entry.get('title', '')
            link = entry.get('link', '')
            pub_date_str = entry.get('published', '')
            
            if not headline:
                continue
                
            # Parse published date
            try:
                dt = parsedate_to_datetime(pub_date_str)
                # Ensure it's in a format Postgres likes
                published_at = dt.isoformat()
            except Exception:
                published_at = datetime.now().isoformat()
                
            matched_symbols = match_headline_to_symbols(headline, universe)
            
            for sym in matched_symbols:
                all_records.append({
                    "symbol": sym,
                    "headline": headline,
                    "source": feed_url,
                    "published_at": published_at,
                    "sentiment_score": None # explicitly NULL to be processed by FinBERT
                })
                matched_pairs_for_verification.append((headline, sym))
                
    if not all_records:
        logger.info("No matching headlines found across feeds. Nothing to insert.")
        return True
        
    # Deduplicate records (in case multiple feeds have the same headline for the same symbol)
    # We use a tuple of (symbol, headline) to uniquely identify
    unique_records = []
    seen = set()
    for rec in all_records:
        identifier = (rec['symbol'], rec['headline'])
        if identifier not in seen:
            seen.add(identifier)
            unique_records.append(rec)
            
    logger.info(f"Found {len(unique_records)} mapped news records to insert.")
    
    # Print random pairs for verification
    num_to_print = min(15, len(unique_records))
    logger.info(f"--- VERIFICATION: Printing {num_to_print} random mapped pairs ---")
    
    # We use the unique_records list for verification printing
    sample_records = random.sample(unique_records, num_to_print)
    for i, rec in enumerate(sample_records, 1):
        logger.info(f"Pair {i}: [{rec['symbol']}] <- \"{rec['headline']}\"")
        
    logger.info("----------------------------------------------------------")
    
    # Upload to Supabase
    try:
        # Since id is BIGSERIAL, we just insert. We don't upsert because we don't have a unique constraint
        # on (symbol, headline). But insert is fine.
        response = supabase.table("news_sentiment").insert(unique_records).execute()
        logger.info(f"Successfully inserted {len(response.data)} records into news_sentiment.")
        return True
    except Exception as e:
        logger.error(f"Failed to insert records into news_sentiment: {e}")
        return False

if __name__ == "__main__":
    run_news_collector()
