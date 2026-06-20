import os
from dotenv import load_dotenv
load_dotenv('.env')
from supabase import create_client

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])
r = sb.table('daily_features').select('symbol,trade_date,atr_14').eq('trade_date', '2026-06-18').limit(5).execute()
for row in r.data:
    print(f"{row['symbol']} atr={row.get('atr_14')}")
