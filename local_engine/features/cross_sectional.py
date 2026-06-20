import pandas as pd
import numpy as np

def compute_cross_sectional_features(df: pd.DataFrame, nifty_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes cross-sectional features.
    df: DataFrame containing ALL stocks for a given period or panel.
        Expected columns: symbol, trade_date, close, rsi_14, sector
    nifty_df: DataFrame containing Nifty 50 data.
        Expected columns: trade_date, nifty_50
    """
    # 1. 52-week high proximity (requires panel data sorted by symbol, date)
    # 252 trading days in a year
    df['rolling_max_252'] = df.groupby('symbol')['close'].transform(lambda x: x.rolling(252, min_periods=60).max())
    df['high_52w_proximity'] = (df['close'] - df['rolling_max_252']) / df['rolling_max_252']
    
    # 2. Beta 60d
    # Merge Nifty 50 close to compute beta
    # Assume nifty_df has 'nifty_50' which is the close price of the index
    if not nifty_df.empty and 'trade_date' in nifty_df.columns:
        nifty_df = nifty_df[['trade_date', 'nifty_50']].copy()
        nifty_df['nifty_ret'] = nifty_df['nifty_50'].pct_change()
        
        df = df.merge(nifty_df[['trade_date', 'nifty_ret']], on='trade_date', how='left')
        
        df['stock_ret'] = df.groupby('symbol')['close'].transform(lambda x: x.pct_change())
        
        # Compute rolling covariance and variance
        def rolling_cov(x, y, window=60):
            return x.rolling(window, min_periods=60).cov(y)
            
        def rolling_var(x, window=60):
            return x.rolling(window, min_periods=60).var()
            
        # We need to compute this per symbol. A standard way in pandas:
        # Calculate 60-day beta
        # beta = cov(stock_ret, nifty_ret) / var(nifty_ret)
        # Using a loop to calculate covariance to avoid pandas 3.0 apply() issues
        covar_list = []
        for sym, group in df.groupby('symbol'):
            res = group['stock_ret'].rolling(60, min_periods=60).cov(group['nifty_ret'])
            covar_list.append(res)
        
        if covar_list:
            df['covar_stock_nifty'] = pd.concat(covar_list)
        else:
            df['covar_stock_nifty'] = np.nan
            
        var_nifty = df.groupby('symbol')['nifty_ret'].transform(lambda x: x.rolling(60, min_periods=60).var())
        
        df['beta_60d'] = df['covar_stock_nifty'] / var_nifty
        
        # clean up intermediate columns
        df.drop(['stock_ret', 'nifty_ret'], axis=1, inplace=True)
    else:
        df['beta_60d'] = np.nan
        
    # 3. Sector Relative Strength 20d & RSI Sector Rank
    # We compute these per trade_date
    if 'sector' in df.columns:
        df['ret_20d'] = df.groupby('symbol')['close'].transform(lambda x: x.pct_change(20))
        
        # Sector mean 20d return per day
        sector_mean_ret = df.groupby(['trade_date', 'sector'])['ret_20d'].transform('mean')
        df['sector_relative_strength_20d'] = df['ret_20d'] - sector_mean_ret
        
        # RSI Sector Rank (percentile rank per day, per sector)
        if 'rsi_14' in df.columns:
            df['rsi_sector_rank'] = df.groupby(['trade_date', 'sector'])['rsi_14'].rank(pct=True)
        else:
            df['rsi_sector_rank'] = np.nan
            
        df.drop(['ret_20d'], axis=1, inplace=True)
    else:
        df['sector_relative_strength_20d'] = np.nan
        df['rsi_sector_rank'] = np.nan

    return df
