import os
import sys
from loguru import logger
from datetime import datetime

import models.train_quantile_lgbm as trainer
import backtest.walk_forward as walk_forward

def run_weekly():
    logger.add("logs/weekly_retrain.log", rotation="10 MB", retention="4 weeks")
    logger.info("Starting Weekly Retrain Pipeline")
    
    start_time = datetime.now()
    
    # 1. Train models on full dataset (creates new challenger)
    logger.info("Phase 1: Training new Challenger Models")
    try:
        trainer.train_models()
        logger.info("Challenger models trained successfully.")
    except Exception as e:
        logger.error(f"Failed to train models: {e}")
        return
        
    # 2. Run walk forward to evaluate accuracy and sharpe
    logger.info("Phase 2: Walk-Forward Backtest")
    try:
        walk_forward.run_walk_forward()
        logger.info("Walk forward completed successfully.")
    except Exception as e:
        logger.error(f"Failed during walk forward backtest: {e}")
        return
        
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info(f"Weekly Retrain Pipeline completed in {duration:.1f} seconds.")
    logger.info("Awaiting manual admin approval to promote Challenger to Champion.")

if __name__ == "__main__":
    run_weekly()
