import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from loguru import logger
import json

# Ensure local_engine is in path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from models.train_quantile_lgbm import train_models

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Supabase URL or Key missing.")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_full_data():
    logger.info("Fetching daily_features and ohlcv_daily for Walk-Forward Backtest...")
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
        
    df_feat = pd.DataFrame(features_data)
    if df_feat.empty:
        return pd.DataFrame()
        
    # Fetch OHLCV
    ohlcv_data = []
    offset = 0
    while True:
        res = supabase.table('ohlcv_daily').select('symbol, trade_date, close').range(offset, offset + page_size - 1).execute()
        ohlcv_data.extend(res.data)
        if len(res.data) < page_size:
            break
        offset += page_size
        
    df_ohlcv = pd.DataFrame(ohlcv_data)
    
    # Merge and build targets
    df = df_feat.merge(df_ohlcv, on=['symbol', 'trade_date'], how='left')
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values(['symbol', 'trade_date']).reset_index(drop=True)
    
    # Calculate horizons
    horizons = [1, 2, 3, 4, 5]
    for h in horizons:
        df[f'target_h{h}'] = df.groupby('symbol')['close'].shift(-h)
        df[f'return_h{h}'] = np.log(df[f'target_h{h}'] / df['close'])
        
    df = df.dropna(subset=[f'return_h{h}' for h in horizons])
    return df

def simulate_holdout_trading(models, holdout_df, horizon=5):
    # This simulates inference over the holdout set and calculates returns.
    if holdout_df.empty:
        return 0.0, 0.0, 0.0
        
    FEATURE_COLS = [
        'rsi_14', 'macd', 'atr_14', 'adx_14', 'bb_pct_b', 'ema_dist_pct', 'roc_5', 'roc_10',
        'sector_relative_strength_20d', 'high_52w_proximity', 'beta_60d', 'rsi_sector_rank',
        'mean_sentiment_10', 'sentiment_momentum', 'headline_count_7d',
        'trailing_pe', 'debt_equity', 'roce', 'revenue_growth', 'eps_growth', 'current_ratio'
    ]
    
    X_holdout = holdout_df[FEATURE_COLS].astype(float)
    
    # Predict Day 5 median quantile
    p50_h5 = models[(horizon, 0.5)].predict(X_holdout)
    
    # Simulate basic trading logic: BUY if p50_h5 > 0, SELL if p50_h5 < 0
    # True return
    actual_returns = holdout_df[f'return_h{horizon}'].values
    
    correct_directions = (np.sign(p50_h5) == np.sign(actual_returns)).sum()
    total_trades = len(actual_returns)
    accuracy = correct_directions / total_trades if total_trades > 0 else 0
    
    # Simulate return (if BUY, you get actual return, if SELL, you get -actual return)
    # Simple strategy return without sizing
    strategy_returns = np.sign(p50_h5) * actual_returns
    
    mean_ret = np.mean(strategy_returns)
    std_ret = np.std(strategy_returns)
    # Annualized sharpe approximation (roughly 50 non-overlapping 5-day periods in a year)
    sharpe = (mean_ret / std_ret) * np.sqrt(50) if std_ret > 0 else 0
    
    return accuracy, sharpe, mean_ret

def run_walk_forward():
    logger.info("Starting Walk-Forward Backtest...")
    df = get_full_data()
    if df.empty:
        logger.error("Not enough data to run backtest.")
        return
        
    min_date = df['trade_date'].min()
    max_date = df['trade_date'].max()
    
    logger.info(f"Data range: {min_date.date()} to {max_date.date()}")
    
    # Folds definitions (12 mo train + 3 mo holdout)
    # Fold 1: train up to min_date + 12 months, holdout +3
    # Fold 2: train up to min_date + 15 months, holdout +3
    # ...
    
    folds = []
    train_end = min_date + pd.DateOffset(months=12)
    while train_end < max_date:
        holdout_end = train_end + pd.DateOffset(months=3)
        if holdout_end > max_date:
            holdout_end = max_date
            
        folds.append((train_end, holdout_end))
        train_end += pd.DateOffset(months=3)
        
    if not folds:
        logger.warning("Data range too short for even one fold.")
        return
        
    overall_accuracy = []
    overall_sharpe = []
    
    for i, (te, he) in enumerate(folds):
        logger.info(f"--- Fold {i+1} ---")
        logger.info(f"Train: {min_date.date()} to {te.date()}")
        logger.info(f"Holdout: {(te + pd.DateOffset(days=5)).date()} to {he.date()}") # 5 day gap to prevent leak
        
        train_df = df[df['trade_date'] <= te].copy()
        
        # 5-day gap to prevent leakage
        leak_safe_start = te + pd.DateOffset(days=5)
        holdout_df = df[(df['trade_date'] >= leak_safe_start) & (df['trade_date'] <= he)].copy()
        
        # Train
        logger.info(f"Training on {len(train_df)} records...")
        
        FEATURE_COLS = [
            'rsi_14', 'macd', 'atr_14', 'adx_14', 'bb_pct_b', 'ema_dist_pct', 'roc_5', 'roc_10',
            'sector_relative_strength_20d', 'high_52w_proximity', 'beta_60d', 'rsi_sector_rank',
            'mean_sentiment_10', 'sentiment_momentum', 'headline_count_7d',
            'trailing_pe', 'debt_equity', 'roce', 'revenue_growth', 'eps_growth', 'current_ratio'
        ]
        
        models = {}
        for h in [5]: # Just train horizon 5 for fast simulation
            for q in [0.1, 0.5, 0.9]:
                from lightgbm import LGBMRegressor
                X = train_df[FEATURE_COLS].astype(float)
                y = train_df[f'return_h{h}']
                
                model = LGBMRegressor(
                    objective='quantile',
                    alpha=q,
                    n_estimators=100,
                    learning_rate=0.05,
                    max_depth=5,
                    verbose=-1
                )
                model.fit(X, y)
                models[(h, q)] = model
                
        # Simulate
        acc, sharpe, ret = simulate_holdout_trading(models, holdout_df, horizon=5)
        logger.info(f"Fold {i+1} Results: Accuracy={acc:.4f}, Sharpe={sharpe:.2f}, Mean Return={ret:.4f}")
        
        overall_accuracy.append(acc)
        overall_sharpe.append(sharpe)
        
    final_acc = np.mean(overall_accuracy)
    final_sharpe = np.mean(overall_sharpe)
    
    logger.info(f"--- Walk-Forward Complete ---")
    logger.info(f"Final Aggregated Accuracy: {final_acc:.4f}")
    logger.info(f"Final Aggregated Sharpe: {final_sharpe:.2f}")
    
    # Save to registry
    # We find the latest model registry entry and update it
    res = supabase.table('model_registry').select('id').order('trained_at', desc=True).limit(1).execute()
    if res.data:
        metrics = {
            "folds_evaluated": len(folds),
            "fold_accuracies": overall_accuracy,
            "fold_sharpes": overall_sharpe
        }
        supabase.table('model_registry').update({
            'backtest_accuracy': float(final_acc),
            'backtest_sharpe': float(final_sharpe),
            'backtest_metrics_json': metrics
        }).eq('id', res.data[0]['id']).execute()
        logger.info("Updated Model Registry with Backtest Metrics.")

if __name__ == "__main__":
    run_walk_forward()
