import time
from fastapi import FastAPI, HTTPException, Security, status, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import redis
from config import settings
from tasks import process_webhook_payload

app = FastAPI(title="Resilient Async API Integration Gateway", version="1.0.0")

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)
redis_client = redis.Redis.from_url(settings.REDIS_URL)

class WebhookPayload(BaseModel):
    event: str
    payload_id: str
    data: dict

def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key Credentials provided."
        )
    return api_key

def enforce_rate_limit(api_key: str) -> None:
    current_time = int(time.time())
    window_start = current_time - settings.RATE_LIMIT_PERIOD
    rate_key = f"rate_limit:{api_key}"
    
    pipeline = redis_client.pipeline()
    pipeline.zremrangebyscore(rate_key, 0, window_start)
    pipeline.zcard(rate_key)
    pipeline.zadd(rate_key, {str(current_time): current_time})
    pipeline.expire(rate_key, settings.RATE_LIMIT_PERIOD)
    execution_results = pipeline.execute()
    
    current_request_count = execution_results[1]
    if current_request_count >= settings.RATE_LIMIT_CALLS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Transient throttling active."
        )

def enforce_idempotency(payload_id: str) -> None:
    idempotency_key = f"idempotency:{payload_id}"
    is_unique = redis_client.set(idempotency_key, "locked", ex=86400, nx=True)
    if not is_unique:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate transactional payload detected for ID: {payload_id}"
        )

@app.post("/v1/webhook", status_code=status.HTTP_202_ACCEPTED)
async def accept_webhook_endpoint(
    payload: WebhookPayload, 
    api_key: str = Depends(verify_api_key)
) -> dict:
    enforce_rate_limit(api_key)
    enforce_idempotency(payload.payload_id)
    
    process_webhook_payload.delay(payload.model_dump())
    
    return {
        "status": "accepted", 
        "message": "Payload verified and passed to the asynchronous processing pool."
    }