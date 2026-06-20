import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv('.env')
supabase: Client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))

today_str = datetime.now().strftime("%Y-%m-%d")

updates = [
    {
        "symbol": "TEGA",
        "as_of_date": today_str,
        "trailing_pe": 45.2,
        "debt_equity": 0.15,
        "return_on_equity": 18.5,
        "revenue_growth_yoy": 0.22,
        "eps_growth_yoy": 0.35,
        "current_ratio": 2.1
    }
]

supabase.table("fundamentals_weekly").upsert(updates).execute()
print("Injected dummy fundamentals for TEGA")
