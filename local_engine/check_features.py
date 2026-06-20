from dotenv import load_dotenv
import os
load_dotenv('.env')
from supabase import create_client

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])

# Check what columns actually exist and have values for TEGA
r = sb.table('daily_features').select('*').eq('symbol', 'TEGA').order('trade_date', desc=True).limit(1).execute()
if r.data:
    row = r.data[0]
    print("=== All columns for TEGA latest features ===")
    for k, v in row.items():
        if v is not None:
            print(f"  {k}: {v}")
    print()
    print("=== Null columns ===")
    for k, v in row.items():
        if v is None:
            print(f"  {k}: NULL")

# Also check if ATR14 column name is something else
print()
print("=== Checking for any ATR-related columns ===")
if r.data:
    row = r.data[0]
    atr_cols = [k for k in row.keys() if 'atr' in k.lower() or 'ATR' in k]
    print(f"ATR columns found: {atr_cols}")
