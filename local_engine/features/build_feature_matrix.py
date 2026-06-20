import os
import sys
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from loguru import logger

# Add parent dir to path to import features
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from features.technical import compute_technical_features
from features.cross_sectional import compute_cross_sectional_features
from features.sentiment_features import compute_sentiment_features

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase URL or Key missing.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def build_feature_matrix():
    logger.info("Starting feature matrix build...")
    
    # 1. Fetch Universe (for sectors)
    uni_res = supabase.table('universe').select('symbol, sector').eq('is_active', True).execute()
    universe_df = pd.DataFrame(uni_res.data)
    if universe_df.empty:
        logger.error("No active universe found.")
        return False
        
    # 2. Fetch OHLCV (all history needed for EMA50, rolling 252 max, etc.)
    # Note: 500 stocks * 500 days = 250k rows. 
    # Supabase default select limit is 1000. We MUST paginate or fetch everything.
    # Since we need all history, we paginate.
    logger.info("Fetching OHLCV history...")
    ohlcv_data = []
    page_size = 1000
    for symbol in universe_df['symbol'].tolist():
        # Fetch per symbol to avoid huge complex queries, or fetch all if possible
        # Actually fetching 250k rows via REST might be slow. 
        # But this runs locally daily, so we can take a minute.
        offset = 0
        while True:
            res = supabase.table('ohlcv_daily').select('*').eq('symbol', symbol).order('trade_date', desc=False).range(offset, offset + page_size - 1).execute()
            ohlcv_data.extend(res.data)
            if len(res.data) < page_size:
                break
            offset += page_size
            
    df = pd.DataFrame(ohlcv_data)
    if df.empty:
        logger.error("No OHLCV data found.")
        return False
        
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values(['symbol', 'trade_date'])
    
    # Join sector
    df = df.merge(universe_df, on='symbol', how='left')
    
    # 3. Compute Technicals (per symbol)
    logger.info("Computing Technical Features...")
    tech_results = []
    for sym, group in df.groupby('symbol'):
        group = group.copy()
        group['symbol'] = sym # Restore symbol column that pandas 3.0 drops
        tech_results.append(compute_technical_features(group))
    
    if tech_results:
        df = pd.concat(tech_results, ignore_index=True)
    else:
        df = pd.DataFrame()
    
    # 4. Fetch Macro
    logger.info("Fetching Macro Data...")
    macro_res = supabase.table('macro_daily').select('*').execute()
    # Pagination might be needed if >1000 days (1000 days = 4 years, so safe for 2 years)
    macro_df = pd.DataFrame(macro_res.data)
    if not macro_df.empty:
        macro_df['trade_date'] = pd.to_datetime(macro_df['trade_date'])
        
    # 5. Compute Cross-Sectional
    logger.info("Computing Cross-Sectional Features...")
    df = compute_cross_sectional_features(df, macro_df)
    
    # 6. Fetch Sentiment
    logger.info("Fetching News Sentiment...")
    # Get recent news (last 2 years approx to match OHLCV)
    # Pagination required if lots of news
    news_data = []
    offset = 0
    while True:
        res = supabase.table('news_sentiment').select('symbol, published_at, sentiment_score').order('published_at', desc=True).range(offset, offset + page_size - 1).execute()
        news_data.extend(res.data)
        if len(res.data) < page_size:
            break
        offset += page_size
        
    news_df = pd.DataFrame(news_data)
    
    # Base trade dates df for sentiment merging
    trade_dates_df = df[['symbol', 'trade_date']].copy()
    
    logger.info("Computing Sentiment Features...")
    sentiment_df = compute_sentiment_features(news_df, trade_dates_df)
    
    # Merge sentiment back
    sentiment_df['trade_date'] = pd.to_datetime(sentiment_df['trade_date'])
    df = df.merge(sentiment_df, on=['symbol', 'trade_date'], how='left')
    
    # 7. Fetch Fundamentals & forward-fill
    logger.info("Fetching Fundamentals...")
    fund_data = []
    offset = 0
    while True:
        res = supabase.table('fundamentals_weekly').select('*').order('as_of_date', desc=False).range(offset, offset + page_size - 1).execute()
        fund_data.extend(res.data)
        if len(res.data) < page_size:
            break
        offset += page_size
        
    fund_df = pd.DataFrame(fund_data)
    if not fund_df.empty:
        fund_df['as_of_date'] = pd.to_datetime(fund_df['as_of_date'])
        # Sort values
        fund_df = fund_df.sort_values(['symbol', 'as_of_date'])
        
        # Merge by exact date or nearest past date. pandas merge_asof is great for this.
        # merge_asof requires sorted keys
        df = df.sort_values('trade_date')
        fund_df = fund_df.sort_values('as_of_date')
        
        # We process symbol by symbol for merge_asof to be safe, or sort by symbol and date
        # merge_asof can take a 'by' parameter
        df = pd.merge_asof(
            df, 
            fund_df.drop(columns=['id'], errors='ignore'), 
            left_on='trade_date', 
            right_on='as_of_date', 
            by='symbol', 
            direction='backward'
        )
        
        # Rename columns to match daily_features schema
        df.rename(columns={
            'return_on_equity': 'roce', 
            'revenue_growth_yoy': 'revenue_growth', 
            'eps_growth_yoy': 'eps_growth'
        }, inplace=True)
    else:
        # Fill empty fundamental columns
        for col in ['trailing_pe', 'debt_equity', 'roce', 'revenue_growth', 'eps_growth', 'current_ratio']:
            df[col] = None
            
    # 8. Drop rows with insufficient history (e.g. before rolling windows populate)
    # 60 days minimum for beta and emas
    # 7. Drop rows with insufficient history (the first ~60 days of a stock will be mostly NaNs)
    logger.info("Dropping insufficient history rows...")
    initial_len = len(df)
    subset_cols = ['ema50', 'beta_60d']
    valid_subset = [c for c in subset_cols if c in df.columns]
    if valid_subset:
        df = df.dropna(subset=valid_subset)
    logger.info(f"Dropped {initial_len - len(df)} rows. {len(df)} remaining valid rows.")
    
    # 9. Upsert to `daily_features` table
    logger.info("Upserting into daily_features...")
    
    # Convert dates to strings
    df['trade_date'] = df['trade_date'].dt.strftime('%Y-%m-%d')
    
    # Replace NaNs with None for JSON serializability
    df = df.replace({pd.NA: None, float('nan'): None})
    
    # Select columns matching schema
    cols = [
        'symbol', 'trade_date', 
        'rsi_14', 'macd', 'atr_14', 'adx_14', 'bb_pct_b', 'ema_dist_pct', 'roc_5', 'roc_10',
        'sector_relative_strength_20d', 'high_52w_proximity', 'beta_60d', 'rsi_sector_rank',
        'mean_sentiment_10', 'sentiment_momentum', 'headline_count_7d',
        'trailing_pe', 'debt_equity', 'roce', 'revenue_growth', 'eps_growth', 'current_ratio'
    ]
    
    # Ensure all columns exist, if not create as None
    for c in cols:
        if c not in df.columns:
            df[c] = None
            
    records = df[cols].to_dict(orient='records')
    
    # Batch upsert
    batch_size = 500
    total_upserted = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        try:
            supabase.table('daily_features').upsert(batch, on_conflict="symbol, trade_date").execute()
            total_upserted += len(batch)
        except Exception as e:
            logger.error(f"Failed to upsert batch at index {i}: {e}")
            
    logger.info(f"Successfully upserted {total_upserted} records into daily_features.")
    return True

if __name__ == "__main__":
    build_feature_matrix()
