import pandas as pd
import pandas_ta as ta

def compute_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes technical indicators for a single stock's OHLCV dataframe.
    Requires columns: open, high, low, close, volume
    Expected to be pre-sorted by trade_date ascending.
    """
    if len(df) < 60:
        # Not enough history for reliable technicals (EMA50 needs 50+ days)
        return df

    # Create a copy to avoid SettingWithCopyWarning
    df = df.copy()

    # pandas-ta computes indicators and appends them if append=True, 
    # but we can explicitly assign them to control naming.
    
    # RSI
    df.ta.rsi(length=14, append=True)
    
    # MACD (adds MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9)
    df.ta.macd(append=True)
    
    # ATR
    df.ta.atr(length=14, append=True)
    
    # ADX (adds ADX_14, DMP_14, DMN_14)
    df.ta.adx(length=14, append=True)
    
    # Bollinger Bands (adds BBL_20_2.0, BBM_20_2.0, BBU_20_2.0, BBB_20_2.0, BBP_20_2.0)
    df.ta.bbands(length=20, append=True)
    
    # EMAs
    df['ema20'] = df.ta.ema(length=20)
    df['ema50'] = df.ta.ema(length=50)
    
    # Derived EMA Distance
    # Safe division: if ema50 is 0 or NaN, it will be NaN
    df['ema_dist_pct'] = (df['ema20'] - df['ema50']) / df['ema50']
    
    # Rate of Change
    df['roc_5'] = df['close'].pct_change(5)
    df['roc_10'] = df['close'].pct_change(10)
    
    # Standardize column names mapping from pandas-ta defaults
    # MACD -> MACD_12_26_9
    # RSI -> RSI_14
    # ATR -> ATR_14
    # ADX -> ADX_14
    # BBP -> BBP_20_2.0 (%B)
    
    rename_map = {
        'RSI_14': 'rsi_14',
        'MACD_12_26_9': 'macd',
        'ATRr_14': 'atr_14',
        'ADX_14': 'adx_14',
        'BBP_20_2.0_2.0': 'bb_pct_b',
        'BBP_20_2.0': 'bb_pct_b'
    }
    
    # Only rename columns that actually exist (to prevent errors if ta fails on some)
    existing_renames = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=existing_renames)
    
    return df
