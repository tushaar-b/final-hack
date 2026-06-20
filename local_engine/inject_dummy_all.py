import os
import random
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv('.env')
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))

today_str = datetime.now().strftime("%Y-%m-%d")

# Get all symbols that have a forecast
res = supabase.table('forecasts').select('symbol').execute()
symbols = [r['symbol'] for r in res.data]

updates = []
for sym in symbols:
    updates.append({
        "symbol": sym,
        "as_of_date": today_str,
        "trailing_pe": round(random.uniform(10, 80), 1),
        "debt_equity": round(random.uniform(0.0, 2.5), 2),
        "return_on_equity": round(random.uniform(5.0, 30.0), 1),
        "revenue_growth_yoy": round(random.uniform(-0.1, 0.4), 3),
        "eps_growth_yoy": round(random.uniform(-0.2, 0.6), 3),
        "current_ratio": round(random.uniform(0.8, 3.5), 2)
    })

# Upsert in chunks
for i in range(0, len(updates), 100):
    chunk = updates[i:i+100]
    supabase.table("fundamentals_weekly").upsert(chunk).execute()

print(f"Injected dummy fundamentals for {len(updates)} symbols.")
