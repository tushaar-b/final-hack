import os
from dotenv import load_dotenv
load_dotenv('.env')
from supabase import create_client

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])
r = sb.table('forecasts').select('symbol,signal_stance,closing_price,target_price,stop_loss,conviction_score').neq('signal_stance', 'HOLD').limit(5).execute()
for row in r.data:
    print(f"{row['symbol']:12} {row['signal_stance']:5} entry={row['closing_price']} TP={row['target_price']} SL={row['stop_loss']} conv={row['conviction_score']}")
