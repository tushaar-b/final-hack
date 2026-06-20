import os
import sys
import numpy as np
import pandas as pd
import lightgbm as lgb
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from loguru import logger
import joblib

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase URL or Key missing.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Define features used for training
FEATURE_COLS = [
    'rsi_14', 'macd', 'atr_14', 'adx_14', 'bb_pct_b', 'ema_dist_pct', 'roc_5', 'roc_10',
    'sector_relative_strength_20d', 'high_52w_proximity', 'beta_60d', 'rsi_sector_rank',
    'mean_sentiment_10', 'sentiment_momentum', 'headline_count_7d',
    'trailing_pe', 'debt_equity', 'roce', 'revenue_growth', 'eps_growth', 'current_ratio'
]

QUANTILES = [0.1, 0.5, 0.9]
HORIZONS = [1, 2, 3, 4, 5]

def fetch_training_data():
    logger.info("Fetching daily_features for model training...")
    
    # We need OHLCV to compute the target (future returns)
    # The target is log(close_t+h / close_t)
    # We can fetch daily_features and ohlcv_daily and join them
    
    page_size = 1000
    
    # Fetch features
    features_data = []
    offset = 0
    while True:
        res = supabase.table('daily_features').select('*').range(offset, offset + page_size - 1).execute()
        features_data.extend(res.data)
        if len(res.data) < page_size:
            break
        offset += page_size
        
    df_features = pd.DataFrame(features_data)
    if df_features.empty:
        logger.error("No daily_features found! Did you run build_feature_matrix.py?")
        return None
        
    df_features['trade_date'] = pd.to_datetime(df_features['trade_date'])
    
    # Fetch OHLCV
    logger.info("Fetching OHLCV for target calculation...")
    ohlcv_data = []
    offset = 0
    while True:
        res = supabase.table('ohlcv_daily').select('symbol, trade_date, close').range(offset, offset + page_size - 1).execute()
        ohlcv_data.extend(res.data)
        if len(res.data) < page_size:
            break
        offset += page_size
        
    df_ohlcv = pd.DataFrame(ohlcv_data)
    df_ohlcv['trade_date'] = pd.to_datetime(df_ohlcv['trade_date'])
    
    # Merge close price into features
    df = df_features.merge(df_ohlcv, on=['symbol', 'trade_date'], how='inner')
    
    # Sort for shift
    df = df.sort_values(['symbol', 'trade_date'])
    
    return df

def make_target(df, horizon):
    # cumulative log return from day t to day t+horizon
    # Make sure we only shift within the same symbol
    future_close = df.groupby('symbol')['close'].shift(-horizon)
    return np.log(future_close / df['close'])

def train_models():
    df = fetch_training_data()
    if df is None or df.empty:
        return
        
    logger.info(f"Loaded {len(df)} rows for training.")
    
    # Ensure challenger directory exists
    model_dir = os.path.join(os.path.dirname(__file__), 'challenger')
    os.makedirs(model_dir, exist_ok=True)
    
    trained_models = {}
    
    for horizon in HORIZONS:
        logger.info(f"--- Training Horizon {horizon} ---")
        # Target variable
        y = make_target(df, horizon)
        
        # Valid rows are those where target is not NaN (i.e. not the end of the time series)
        # and where features are not completely NaN
        valid_idx = y.dropna().index
        
        y_valid = y.loc[valid_idx]
        X_valid = df.loc[valid_idx, FEATURE_COLS]
        
        # LightGBM handles NaN in features automatically, but we ensure correct types
        X_valid = X_valid.astype(float)
        
        for q in QUANTILES:
            logger.info(f"Training Quantile {q}")
            model = lgb.LGBMRegressor(
                objective='quantile', alpha=q,
                n_estimators=200, learning_rate=0.03, max_depth=5,
                num_leaves=31, min_child_samples=30,
                random_state=42, verbosity=-1
            )
            
            model.fit(X_valid, y_valid)
            trained_models[(horizon, q)] = model
            
            # Save to challenger
            model_filename = os.path.join(model_dir, f'lgbm_h{horizon}_q{int(q*100)}.pkl')
            joblib.dump(model, model_filename)
            
    logger.info(f"All 15 models trained and saved to {model_dir}")
    
    # Dummy step: in reality we'd log metrics and update model_registry
    # We will expand this during walk-forward backtesting build
    
if __name__ == "__main__":
    train_models()
