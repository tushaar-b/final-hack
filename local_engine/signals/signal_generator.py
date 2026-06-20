import os
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from loguru import logger
import sys

# Ensure local_engine is in path if running directly
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from signals.position_sizer import size_position

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase URL or Key missing.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

FEATURE_COLS = [
    'rsi_14', 'macd', 'atr_14', 'adx_14', 'bb_pct_b', 'ema_dist_pct', 'roc_5', 'roc_10',
    'sector_relative_strength_20d', 'high_52w_proximity', 'beta_60d', 'rsi_sector_rank',
    'mean_sentiment_10', 'sentiment_momentum', 'headline_count_7d',
    'trailing_pe', 'debt_equity', 'roce', 'revenue_growth', 'eps_growth', 'current_ratio'
]

HORIZONS = [1, 2, 3, 4, 5]
QUANTILES = [0.1, 0.5, 0.9]

def load_champion_models():
    models = {}
    model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'champion')
    
    if not os.path.exists(model_dir):
        logger.error(f"Champion model directory not found: {model_dir}")
        return None
        
    for horizon in HORIZONS:
        for q in QUANTILES:
            filename = os.path.join(model_dir, f'lgbm_h{horizon}_q{int(q*100)}.pkl')
            if not os.path.exists(filename):
                logger.error(f"Missing champion model: {filename}")
                return None
            models[(horizon, q)] = joblib.load(filename)
            
    logger.info("Successfully loaded all 15 champion models.")
    return models

def fetch_latest_features():
    logger.info("Fetching latest features for active universe...")
    
    # First, get active universe
    res = supabase.table('universe').select('symbol, sector').eq('is_active', True).execute()
    universe_dict = {row['symbol']: row['sector'] for row in res.data}
    symbols = list(universe_dict.keys())
    
    if not symbols:
        logger.warning("No active symbols found.")
        return None, None
        
    # Find the most recent date in daily_features
    res = supabase.table('daily_features').select('trade_date').order('trade_date', desc=True).limit(1).execute()
    if not res.data:
        logger.warning("No features found in daily_features.")
        return None, None
        
    latest_date = res.data[0]['trade_date']
    logger.info(f"Using features from date: {latest_date}")
    
    # Fetch features for this date
    page_size = 1000
    features_data = []
    offset = 0
    while True:
        res = supabase.table('daily_features').select('*').eq('trade_date', latest_date).range(offset, offset + page_size - 1).execute()
        features_data.extend(res.data)
        if len(res.data) < page_size:
            break
        offset += page_size
        
    df = pd.DataFrame(features_data)
    if df.empty:
        return None, None
        
    df['sector'] = df['symbol'].map(universe_dict)
    
    # We also need the actual close price from ohlcv_daily for today
    # We can fetch it
    ohlcv_data = []
    offset = 0
    while True:
        res = supabase.table('ohlcv_daily').select('symbol, close').eq('trade_date', latest_date).range(offset, offset + page_size - 1).execute()
        ohlcv_data.extend(res.data)
        if len(res.data) < page_size:
            break
        offset += page_size
        
    df_ohlcv = pd.DataFrame(ohlcv_data)
    df = df.merge(df_ohlcv, on='symbol', how='left')
    
    # Also fetch latest macro regime (india_vix)
    res = supabase.table('macro_daily').select('india_vix').eq('trade_date', latest_date).execute()
    current_vix = res.data[0]['india_vix'] if res.data else 15.0
    
    return df, current_vix

def generate_signals():
    logger.info("Starting Signal Generation...")
    
    models = load_champion_models()
    if not models:
        return False
        
    df, current_vix = fetch_latest_features()
    if df is None or df.empty:
        return False
        
    # We'll need a way to track current sector exposure for position sizing.
    # In a real system, you'd fetch active portfolio. For now, assume 0.
    sector_exposures = {sector: 0.0 for sector in df['sector'].unique()}
    
    forecasts = []
    
    # LightGBM prefers float data
    X = df[FEATURE_COLS].astype(float)
    
    for i, row in df.iterrows():
        symbol = row['symbol']
        trade_date = row['trade_date']
        close_price = row.get('close', 0.0)
        sector = row.get('sector', 'Unknown')
        
        if pd.isna(close_price) or close_price <= 0:
            logger.warning(f"Skipping {symbol}: missing valid close price.")
            continue
            
        record = {
            "symbol": symbol,
            "forecast_date": trade_date,
            "closing_price": float(close_price),
            "model_version": "v1.0-initial-backfill"
        }
        
        # 1. Run Inference
        preds = {}
        for horizon in HORIZONS:
            p10 = models[(horizon, 0.1)].predict(X.iloc[[i]])[0]
            p50 = models[(horizon, 0.5)].predict(X.iloc[[i]])[0]
            p90 = models[(horizon, 0.9)].predict(X.iloc[[i]])[0]
            
            # 2. Sort-correct quantile crossing
            p10, p50, p90 = sorted([p10, p50, p90])
            
            # Save into record
            record[f"p10_day{horizon}"] = float(p10)
            record[f"p50_day{horizon}"] = float(p50)
            record[f"p90_day{horizon}"] = float(p90)
            
            # 3. Convert back to price levels
            preds[horizon] = {
                'p10_price': close_price * np.exp(p10),
                'p50_price': close_price * np.exp(p50),
                'p90_price': close_price * np.exp(p90)
            }
            
        # 4. Compute Conviction Score
        # PRD 8.4
        
        # We need historical realized volatility (60d).
        # We don't have exactly "realized volatility" in features, but we have atr_14.
        # Let's approximate volatility using ATR / Close * 100
        atr = row.get('atr_14')
        if atr is None: atr = 0
        
        # Calculate expected volatility as a % of price. Floor at 1%
        vol_approx = atr / close_price if close_price > 0 else 0.01
        if vol_approx == 0: vol_approx = 0.01
        
        p50_d5 = record['p50_day5']
        p10_d5 = record['p10_day5']
        p90_d5 = record['p90_day5']
        
        # 1. Magnitude Score (0-10) -> scaled back to 0-1
        # Real ATR is typically 2-5%. A strong move is 1x ATR over 5 days.
        # We scale p50_d5 by dividing by (vol_approx / 2) to normalize it.
        magnitude_score = min(abs(p50_d5) / (vol_approx * 0.5), 1.0)
        
        # band tightness score: narrower P10-P90 band = more confident model
        # Real LightGBM quantile bands for 5-day horizon are typically 10-25% wide.
        # Map: band<=5% -> score=1.0, band>=20% -> score=0.0
        band_width = p90_d5 - p10_d5
        band_tightness_score = max(0.0, 1.0 - (band_width / 0.20))
        
        # sentiment alignment: does news sentiment agree with forecast direction?
        mean_sentiment = row.get('mean_sentiment_10', None)
        if mean_sentiment is None or (mean_sentiment == 0):
            # No sentiment data → neutral score
            sentiment_alignment_score = 0.5
        elif (p50_d5 > 0 and mean_sentiment > 0) or (p50_d5 < 0 and mean_sentiment < 0):
            sentiment_alignment_score = 1.0  # aligned
        else:
            sentiment_alignment_score = 0.2  # opposing signals
            
        # macro regime score: is VIX supportive of new positions?
        if current_vix < 15.0:
            macro_regime_score = 1.0   # very calm
        elif current_vix < 20.0:
            macro_regime_score = 0.8   # normal
        elif current_vix < 25.0:
            macro_regime_score = 0.5   # elevated
        else:
            macro_regime_score = 0.2   # high volatility
        
        # PRD §8.4 weights: 0.35 / 0.25 / 0.20 / 0.20
        raw_conviction = (
            magnitude_score      * 0.35 +
            band_tightness_score * 0.25 +
            sentiment_alignment_score * 0.20 +
            macro_regime_score   * 0.20
        )
        # scale to 1-10
        conviction_score = min(round(raw_conviction * 10, 1), 10.0)
        
        # 5. Signal Stance
        # Lowered threshold to 5.0 due to missing sentiment data dragging down scores.
        # Added a 0.5% minimum expected move to avoid BUY/SELL on flat forecasts.
        if conviction_score >= 5.0 and p50_d5 > 0.005:
            stance = 'BUY'
        elif conviction_score >= 5.0 and p50_d5 < -0.005:
            stance = 'SELL'
        else:
            stance = 'HOLD'
            
        # 6. Stop Loss / Target Price
        if stance == 'BUY':
            stop_loss = close_price - (1.5 * atr)
            target_price = close_price + (2.0 * atr)
        elif stance == 'SELL':
            stop_loss = close_price + (1.5 * atr)
            target_price = close_price - (2.0 * atr)
        else:
            stop_loss = None
            target_price = None
            
        # 7. Position Sizer
        current_exp = sector_exposures.get(sector, 0.0)
        pos_pct = size_position(conviction_score, current_exp) if stance != 'HOLD' else 0.0
        
        if pos_pct > 0:
            sector_exposures[sector] += pos_pct
            
        record['conviction_score'] = float(conviction_score)
        record['signal_stance'] = stance
        record['stop_loss'] = float(stop_loss) if stop_loss is not None else None
        record['target_price'] = float(target_price) if target_price is not None else None
        record['position_pct'] = float(pos_pct)
        
        forecasts.append(record)
        
    # 8. Write to Supabase
    logger.info(f"Inserting {len(forecasts)} forecasts into Supabase...")
    
    # Chunk inserts to avoid payload limits
    chunk_size = 500
    for i in range(0, len(forecasts), chunk_size):
        chunk = forecasts[i:i + chunk_size]
        try:
            supabase.table('forecasts').upsert(chunk, on_conflict="symbol, forecast_date").execute()
        except Exception as e:
            logger.error(f"Failed to insert forecast chunk: {e}")
            return False
            
    logger.info("Signal generation completed successfully.")
    return True

if __name__ == "__main__":
    generate_signals()
