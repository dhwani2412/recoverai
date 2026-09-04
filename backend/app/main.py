import os
import hmac
import hashlib

from dotenv import load_dotenv
from fastapi import FastAPI, Request

from supabase import create_client, Client

from app.failure_engine import FailureContext, process_failure


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
    raise ValueError("Supabase credentials are missing from .env")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/webhook")
async def razorpay_webhook(request: Request):
    body = await request.body()

    signature = request.headers.get("X-Razorpay-Signature", "")
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

    expected_signature = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        return {"status": "invalid_signature"}
        
    payload = await request.json()

    entity = payload["payload"]["payment"]["entity"]

    ctx = FailureContext(
        payment_id=entity["id"],
        order_id=entity.get("order_id", ""),
        amount=entity["amount"],
        error_code=entity.get("error_code", ""),
        error_reason=entity.get("error_reason", "unknown"),
        error_description=entity.get("error_description", ""),
        retry_count=0,
    )

    result = await process_failure(ctx)

    return result