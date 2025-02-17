from fastapi import FastAPI
from app.api.v1.endpoints import invoices
from app.api.v1.endpoints import webhooks
from app.api.v1.endpoints import health
import starkbank
import redis
from app.core.config import settings
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from app.jobs.transfer_starkbank_undelivered_credited_invoices import (
    transfer_starkbank_undelivered_credited_invoices,
)
from app.jobs.invoice_random_people import invoice_random_people
import time

scheduler = BackgroundScheduler()

WEBHOOK_LOCK_KEY = "starkbank_webhook_lock"
WEBHOOK_ID_KEY = "starkbank_webhook_id"
MAX_RETRIES = 5
RETRY_DELAY = 2


def get_or_create_webhook(redis_client, webhook_url: str) -> str:
    """
    Get or create Starkbank webhook with proper error handling and retries
    """
    for attempt in range(MAX_RETRIES):
        try:
            # First try to get from Redis
            webhook_id = redis_client.get(WEBHOOK_ID_KEY)
            if webhook_id:
                return (
                    webhook_id.decode() if isinstance(webhook_id, bytes) else webhook_id
                )

            # Try to acquire lock
            lock_acquired = redis_client.set(WEBHOOK_LOCK_KEY, "1", nx=True, ex=30)

            if not lock_acquired:
                # Another worker is handling it - wait and retry
                time.sleep(RETRY_DELAY)
                continue

            try:
                # Double check Redis after acquiring lock
                webhook_id = redis_client.get(WEBHOOK_ID_KEY)
                if webhook_id:
                    return (
                        webhook_id.decode()
                        if isinstance(webhook_id, bytes)
                        else webhook_id
                    )

                # Check Starkbank webhooks
                webhooks = starkbank.webhook.query()
                for webhook in webhooks:
                    if webhook.url == webhook_url:
                        # Found existing webhook - save and return
                        redis_client.set(WEBHOOK_ID_KEY, str(webhook.id))
                        return str(webhook.id)

                # No webhook exists - create new one
                print(f"Creating Starkbank invoices webhook url: {webhook_url}")
                webhook = starkbank.webhook.create(
                    url=webhook_url,
                    subscriptions=["invoice"],
                )
                redis_client.set(WEBHOOK_ID_KEY, str(webhook.id))
                return str(webhook.id)

            except Exception as e:
                print(f"Error in webhook setup (attempt {attempt + 1}): {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(RETRY_DELAY)
                continue
            finally:
                redis_client.delete(WEBHOOK_LOCK_KEY)

        except Exception as e:
            print(f"Error in attempt {attempt + 1}: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(RETRY_DELAY)

    raise Exception(f"Failed to setup webhook after {MAX_RETRIES} attempts")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Test Redis connection
    redis_client = redis.from_url(settings.REDIS_URL)
    try:
        redis_client.ping()
    except redis.ConnectionError as e:
        raise

    starkbank.user = settings.starkbank_project
    webhook_url = settings.starkbank_invoices_webhook_url
    webhook_id = None

    # Try to acquire lock
    if redis_client.set(WEBHOOK_LOCK_KEY, "1", nx=True, ex=30):
        try:
            # Check if webhook exists
            webhooks = starkbank.webhook.query()
            for webhook in webhooks:
                if webhook.url == webhook_url:
                    webhook_id = webhook.id
                    break

            # Create if it doesn't exist
            if webhook_id is None:
                webhook = starkbank.webhook.create(
                    url=webhook_url,
                    subscriptions=["invoice"],
                )
                webhook_id = webhook.id
        finally:
            redis_client.delete(WEBHOOK_LOCK_KEY)

    # Wait a bit for the webhook to be created if needed
    if webhook_id is None:
        time.sleep(2)
        webhooks = starkbank.webhook.query()
        for webhook in webhooks:
            if webhook.url == webhook_url:
                webhook_id = webhook.id
                break

    if webhook_id is None:
        raise Exception("Could not get webhook ID")

    print(f"Using webhook with ID: {webhook_id}")

    # 01:00 AM (UTC-3)
    # TODO: as env variable
    scheduler.add_job(transfer_starkbank_undelivered_credited_invoices, "cron", hour=1)

    scheduler.add_job(
        lambda: invoice_random_people(n_min=8, n_max=12), "interval", hours=3
    )

    scheduler.start()

    yield

    if settings.ENVIRONMENT == "development":
        print("Cleaning up Starkbank Invoices Webhook")
        starkbank.webhook.delete(webhook_id)

    scheduler.shutdown()


app = FastAPI(
    title="Stark Bank Challenge API",
    description="API for a client that uses Stark Bank (or any other implemented bank)",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(invoices.router, prefix="/api/v1/invoices", tags=["invoices"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(health.router, prefix="/health", tags=["health"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
