import os
from dotenv import load_dotenv
from supabase import create_client

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

test_row = {
    "symbol": "RELIANCE",
    "entry_price": 2450.0,
    "quantity": 5,
    "entry_date": "2026-06-10",
    "notes": "Test insert",
    "side": "BUY"
}

try:
    res = supabase.table('portfolio_log').insert(test_row).execute()
    print("INSERT WITH SIDE SUCCESS:", res.data)
except Exception as e:
    print("INSERT WITH SIDE FAILED:", e)
    # Let's try without 'side'
    test_row_no_side = {
        "symbol": "RELIANCE",
        "entry_price": 2450.0,
        "quantity": 5,
        "entry_date": "2026-06-10",
        "notes": "Test insert"
    }
    try:
        res2 = supabase.table('portfolio_log').insert(test_row_no_side).execute()
        print("INSERT WITHOUT SIDE SUCCESS:", res2.data)
    except Exception as e2:
        print("INSERT WITHOUT SIDE FAILED:", e2)
