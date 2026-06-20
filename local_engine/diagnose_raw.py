import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('.env')
sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])

# 1. 3 raw rows from forecasts
print("--- 3 RAW ROWS FROM FORECASTS ---")
res_f = sb.table('forecasts').select('symbol, p50_day1, p50_day2, p50_day3, p50_day4, p50_day5, conviction_score, position_pct').limit(3).execute()
print(json.dumps(res_f.data, indent=2))

# 2. 3 raw rows from news_sentiment
print("\n--- 3 RAW ROWS FROM NEWS_SENTIMENT ---")
res_s = sb.table('news_sentiment').select('*').limit(3).execute()
print(json.dumps(res_s.data, indent=2))
