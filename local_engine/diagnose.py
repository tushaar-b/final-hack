from dotenv import load_dotenv
import os
load_dotenv('.env')
from supabase import create_client

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])

print("=== ISSUE 1: Entry price vs Target price (checking ATR) ===")
r = sb.table('forecasts').select('symbol,closing_price,target_price,stop_loss,conviction_score,signal_stance').neq('signal_stance','HOLD').limit(5).execute()
for row in r.data:
    print(f"{row['symbol']:12} close={row['closing_price']}  target={row['target_price']}  sl={row['stop_loss']}  stance={row['signal_stance']}")

print()
print("=== Checking ATR values in daily_features ===")
r2 = sb.table('daily_features').select('symbol,atr_14,rsi_14').order('trade_date', desc=True).limit(5).execute()
for row in r2.data:
    print(f"{row['symbol']:12} atr_14={row.get('atr_14')}  rsi_14={row.get('rsi_14')}")

print()
print("=== ISSUE 2: Watchlist table ===")
try:
    r3 = sb.table('watchlists').select('*').limit(1).execute()
    print(f"watchlists table EXISTS, rows: {len(r3.data)}")
except Exception as e:
    print(f"watchlists table ERROR: {e}")

print()
print("=== ISSUE 3: Fundamentals data ===")
r4 = sb.table('daily_features').select('*').eq('symbol', 'TEGA').order('trade_date', desc=True).limit(1).execute()
if r4.data:
    row = r4.data[0]
    fund_keys = ['trailing_pe','debt_equity','roce','revenue_growth','eps_growth','current_ratio']
    for k in fund_keys:
        print(f"  {k}: {row.get(k)}")
    
print()
print("=== Checking fundamentals_weekly table ===")
try:
    r5 = sb.table('fundamentals_weekly').select('*').limit(3).execute()
    print(f"fundamentals_weekly rows: {len(r5.data)}")
    if r5.data:
        print("Sample:", r5.data[0])
except Exception as e:
    print(f"fundamentals_weekly ERROR: {e}")
