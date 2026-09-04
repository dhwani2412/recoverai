import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)


async def log_event(event_type: str, data: dict):
    payment_id = data.get("payment_id")

    supabase.table("audit_log").insert({
        "event_type": event_type,
        "payment_id": payment_id,
        "data": data,
    }).execute()