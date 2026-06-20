import pandas as pd
import numpy as np

def compute_sentiment_features(news_df: pd.DataFrame, trade_dates_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes sentiment features.
    news_df: DataFrame of news_sentiment table.
             Expected columns: symbol, published_at, sentiment_score
    trade_dates_df: DataFrame of unique (symbol, trade_date) from OHLCV 
                    to ensure we carry forward sentiment on days without news.
    """
    if news_df.empty:
        # Return trade_dates_df with 0s for sentiment features
        df = trade_dates_df.copy()
        df['mean_sentiment_10'] = 0.0
        df['sentiment_momentum'] = 0.0
        df['headline_count_7d'] = 0
        return df

    # Convert published_at to date
    news_df['news_date'] = pd.to_datetime(news_df['published_at']).dt.date
    news_df['news_date'] = pd.to_datetime(news_df['news_date'])
    
    # Fill NaN sentiment with 0 (neutral) before aggregation
    news_df['sentiment_score'] = news_df['sentiment_score'].fillna(0)

    # Aggregate by symbol and date
    daily_news = news_df.groupby(['symbol', 'news_date']).agg(
        daily_mean_sentiment=('sentiment_score', 'mean'),
        daily_headline_count=('sentiment_score', 'count')
    ).reset_index()

    # We need to merge this with trade_dates to ensure continuous rolling windows
    # trade_dates_df should have 'symbol' and 'trade_date' (as datetime)
    trade_dates_df['trade_date_dt'] = pd.to_datetime(trade_dates_df['trade_date'])
    
    df = pd.merge(
        trade_dates_df,
        daily_news,
        left_on=['symbol', 'trade_date_dt'],
        right_on=['symbol', 'news_date'],
        how='left'
    )
    
    # Fill days without news
    df['daily_mean_sentiment'] = df['daily_mean_sentiment'].fillna(0.0)
    df['daily_headline_count'] = df['daily_headline_count'].fillna(0)
    
    # Sort for rolling
    df = df.sort_values(['symbol', 'trade_date_dt'])
    
    # Compute rolling features
    # mean_sentiment_10: rolling 10-day mean of daily mean sentiment
    df['mean_sentiment_10'] = df.groupby('symbol')['daily_mean_sentiment'].transform(lambda x: x.rolling(10, min_periods=1).mean())
    
    # mean_sentiment_3
    df['mean_sentiment_3'] = df.groupby('symbol')['daily_mean_sentiment'].transform(lambda x: x.rolling(3, min_periods=1).mean())
    
    # sentiment_momentum
    df['sentiment_momentum'] = df['mean_sentiment_3'] - df['mean_sentiment_10']
    
    # headline_count_7d
    df['headline_count_7d'] = df.groupby('symbol')['daily_headline_count'].transform(lambda x: x.rolling(7, min_periods=1).sum())
    
    # Clean up
    df.drop(columns=['trade_date_dt', 'news_date', 'daily_mean_sentiment', 'daily_headline_count', 'mean_sentiment_3'], inplace=True, errors='ignore')
    
    # Ensure 0.0 instead of NaN for completely empty windows (though min_periods=1 handles most)
    df['mean_sentiment_10'] = df['mean_sentiment_10'].fillna(0.0)
    df['sentiment_momentum'] = df['sentiment_momentum'].fillna(0.0)
    df['headline_count_7d'] = df['headline_count_7d'].fillna(0).astype(int)
    
    return df
