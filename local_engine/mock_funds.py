import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# Load env
env_path = os.path.join(os.path.dirname(__file__), '..', 'cloud_api', '.env')
load_dotenv(env_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL:
    print("NO SUPABASE URL", env_path)
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

today_str = datetime.now().strftime("%Y-%m-%d")

updates = [
    {
        "symbol": "RELIANCE",
        "as_of_date": today_str,
        "trailing_pe": 22.1,
        "debt_equity": 0.35,
        "return_on_equity": 0.18,
        "revenue_growth_yoy": 0.09,
        "eps_growth_yoy": 0.11,
        "current_ratio": 1.1
    },
    {
        "symbol": "TCS",
        "as_of_date": today_str,
        "trailing_pe": 28.5,
        "debt_equity": 0.05,
        "return_on_equity": 0.45,
        "revenue_growth_yoy": 0.12,
        "eps_growth_yoy": 0.08,
        "current_ratio": 2.1
    }
]

res = supabase.table("fundamentals_weekly").upsert(updates).execute()
print(res)
