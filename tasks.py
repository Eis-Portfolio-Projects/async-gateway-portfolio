import time
from celery import Celery
import httpx
from config import settings

celery_app = Celery("tasks", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

@celery_app.task(bind=True, max_retries=5, default_retry_delay=2)
def process_webhook_payload(self, payload: dict) -> dict:
    transformed_payload = {
        "source": "async_gateway_service",
        "processed_timestamp": time.time(),
        "payload_data": payload
    }
    try:
        with httpx.Client() as client:
            response = client.post(
                settings.TARGET_API_URL, 
                json=transformed_payload, 
                timeout=10.0
            )
            response.raise_for_status()
            return {"status": "dispatched", "status_code": response.status_code}
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code >= 500 or exc.response.status_code == 429:
            backoff_delay = 2 ** self.request.retries
            raise self.retry(exc=exc, countdown=backoff_delay)
        raise exc
    except httpx.RequestError as exc:
        backoff_delay = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=backoff_delay)