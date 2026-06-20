import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

print(f"URL: {url}")
print(f"KEY: {key}")
print(f"KEY LENGTH: {len(key) if key else 0}")
print(f"KEY TYPE: {type(key)}")

try:
    from supabase import create_client
    create_client(url, key)
    print("CREATE CLIENT SUCCESS")
except Exception as e:
    print("CREATE CLIENT FAILED:", type(e), e)
