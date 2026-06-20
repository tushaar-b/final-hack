import os
from dotenv import load_dotenv
load_dotenv('.env')
from supabase import create_client

sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])
r = sb.table('forecasts').select('signal_stance').execute()

stances = [x['signal_stance'] for x in r.data]
print("Total records:", len(stances))
print("BUY:", stances.count("BUY"))
print("SELL:", stances.count("SELL"))
print("HOLD:", stances.count("HOLD"))
