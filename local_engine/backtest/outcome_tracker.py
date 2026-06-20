import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client
from loguru import logger

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase URL or Key missing.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_trading_days(start_date_str, end_date_str):
    # Fetch distinct trade dates from macro_daily to find actual trading days safely
    res = supabase.table('macro_daily').select('trade_date').gte('trade_date', start_date_str).lte('trade_date', end_date_str).order('trade_date', desc=False).execute()
    dates = sorted([row['trade_date'] for row in res.data])
    return dates

def track_outcomes(today_str=None):
    if today_str is None:
        today_str = datetime.now().strftime("%Y-%m-%d")
        
    logger.info(f"Running Outcome Tracker for target date: {today_str}")
    
    # We need to find the trade date exactly 5 trading days ago
    # To be safe, look back 15 calendar days to find the last 6 trading days
    lookback_date = (datetime.strptime(today_str, "%Y-%m-%d") - timedelta(days=15)).strftime("%Y-%m-%d")
    recent_trading_days = get_trading_days(lookback_date, today_str)
    
    if len(recent_trading_days) < 6:
        logger.warning("Not enough recent trading days to find T-5 date.")
        return False
        
    # The last element is today (or the most recent trading day). T-5 is index -6.
    # Wait, if today is in the list, then index -1 is today, -6 is T-5.
    t_minus_5_date = recent_trading_days[-6]
    logger.info(f"Identified T-5 date as {t_minus_5_date}")
    
    # Fetch all forecasts from T-5 that don't already have an outcome
    # We fetch all forecasts from T-5
    res = supabase.table('forecasts').select('*').eq('forecast_date', t_minus_5_date).execute()
    forecasts = res.data
    
    if not forecasts:
        logger.info(f"No forecasts found for T-5 date ({t_minus_5_date}).")
        return True
        
    logger.info(f"Found {len(forecasts)} forecasts to evaluate.")
    
    # Fetch OHLCV data for the window [T-4, T] for these symbols
    symbols = [f['symbol'] for f in forecasts]
    
    # Since symbols list can be large, we might need to batch or just fetch all OHLCV for the dates
    t_minus_4_date = recent_trading_days[-5]
    res_ohlcv = supabase.table('ohlcv_daily').select('symbol, trade_date, high, low, close').gte('trade_date', t_minus_4_date).lte('trade_date', today_str).execute()
    
    df_ohlcv = pd.DataFrame(res_ohlcv.data)
    if df_ohlcv.empty:
        logger.warning("No OHLCV data found for the T-5 evaluation window.")
        return False
        
    outcomes = []
    
    for forecast in forecasts:
        symbol = forecast['symbol']
        fid = forecast['id']
        entry_price = forecast['closing_price']
        stop_loss = forecast['stop_loss']
        target_price = forecast['target_price']
        p50_day5 = forecast['p50_day5']
        stance = forecast['signal_stance']
        
        # Filter OHLCV for this symbol, sorted chronologically
        symbol_history = df_ohlcv[df_ohlcv['symbol'] == symbol].sort_values('trade_date')
        
        if symbol_history.empty:
            continue
            
        # Check day by day for SL/TP hits
        outcome_type = 'OPEN'
        actual_close = symbol_history.iloc[-1]['close'] # the close on T
        hit_date = today_str
        
        if stance in ['BUY', 'SELL'] and stop_loss and target_price:
            for _, day_row in symbol_history.iterrows():
                high = day_row['high']
                low = day_row['low']
                current_date = day_row['trade_date']
                
                if stance == 'BUY':
                    if low <= stop_loss:
                        outcome_type = 'HIT_SL'
                        actual_close = stop_loss
                        hit_date = current_date
                        break
                    elif high >= target_price:
                        outcome_type = 'HIT_TP'
                        actual_close = target_price
                        hit_date = current_date
                        break
                elif stance == 'SELL':
                    if high >= stop_loss:
                        outcome_type = 'HIT_SL'
                        actual_close = stop_loss
                        hit_date = current_date
                        break
                    elif low <= target_price:
                        outcome_type = 'HIT_TP'
                        actual_close = target_price
                        hit_date = current_date
                        break
        
        if outcome_type == 'OPEN':
            outcome_type = 'HIT_TD' # Hit Time Decay (end of 5 day window without hitting SL/TP)
            
        realized_return = np.log(actual_close / entry_price) if entry_price > 0 else 0
        direction_correct = (np.sign(realized_return) == np.sign(p50_day5)) if p50_day5 else False
        
        outcomes.append({
            "forecast_id": fid,
            "outcome_date": hit_date,
            "actual_close": float(actual_close),
            "realized_return": float(realized_return),
            "direction_correct": bool(direction_correct),
            "outcome_type": outcome_type
        })
        
    if outcomes:
        logger.info(f"Upserting {len(outcomes)} outcome records...")
        try:
            # We use upsert so it's idempotent
            supabase.table('signal_outcomes').upsert(outcomes, on_conflict="forecast_id").execute()
            logger.info("Successfully tracked outcomes.")
        except Exception as e:
            logger.error(f"Failed to upsert outcomes: {e}")
            return False
            
    return True

if __name__ == "__main__":
    # If run standalone, use today's date
    track_outcomes()
