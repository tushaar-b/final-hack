import os
from dotenv import load_dotenv
from supabase import create_client
import json
import urllib.request
import urllib.error

load_dotenv('.env')
sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])

print('\n=== 1. Forecasts Table Row Count ===')
r = sb.table('forecasts').select('id', count='exact').limit(1).execute()
print(f'Count: {r.count}')

print('\n=== 2. Most Recent pipeline_runs Row ===')
try:
    p = sb.table('pipeline_runs').select('*').order('started_at', desc=True).limit(1).execute()
    if p.data:
        print(f'Status: {p.data[0].get("status")}')
        print(f'Finished At: {p.data[0].get("finished_at")}')
        print(f'Raw Row: {json.dumps(p.data[0], indent=2)}')
    else:
        print('No rows found in pipeline_runs.')
except Exception as e:
    print(f'Error fetching pipeline_runs: {e}')

print('\n=== 3. Raw Response from /api/forecasts/latest?limit=1 ===')
try:
    req = urllib.request.urlopen('http://localhost:8000/api/forecasts/latest?limit=1')
    data = req.read().decode('utf-8')
    print(f'HTTP Status: {req.getcode()}')
    print(f'Response Body: {data}')
except urllib.error.HTTPError as e:
    print(f'HTTP Status: {e.code}')
    print(f'Response Body: {e.read().decode("utf-8")}')
except Exception as e:
    print(f'HTTP Request Error: {e}')

print('\n=== Exact Date Filter in Supabase Query ===')
with open('routers/forecasts.py', 'r') as f:
    for line in f:
        if 'query' in line and 'execute' in line:
            print(f'Line: {line.strip()}')
        elif 'order(' in line or 'eq(' in line:
            print(f'Line: {line.strip()}')
