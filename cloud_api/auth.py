import os
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase URL or Anon Key missing from environment")

# We use the anon key for the public client. We will pass the user's JWT to authenticate them.
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        # Verify JWT with Supabase Auth
        res = supabase.auth.get_user(token)
        user = res.user
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"uid": user.id, "email": user.email, "token": token}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
