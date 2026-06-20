from dotenv import load_dotenv
import os
load_dotenv('.env')
from supabase import create_client

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])

# Top 15 by conviction
r = sb.table('forecasts').select('symbol,signal_stance,conviction_score,closing_price,target_price,stop_loss').order('conviction_score', desc=True).limit(15).execute()
print("=== TOP 15 BY CONVICTION ===")
for row in r.data:
    print(f"{row['symbol']:15} {row['signal_stance']:5} conv={row['conviction_score']} close={row['closing_price']}")

print()

# Total counts
r2 = sb.table('forecasts').select('signal_stance').execute()
total_buy = sum(1 for x in r2.data if x['signal_stance'] == 'BUY')
total_sell = sum(1 for x in r2.data if x['signal_stance'] == 'SELL')
total_hold = sum(1 for x in r2.data if x['signal_stance'] == 'HOLD')
print(f"TOTAL => BUY: {total_buy}  SELL: {total_sell}  HOLD: {total_hold}")
