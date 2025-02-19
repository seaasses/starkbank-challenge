from fastapi import FastAPI
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
from app.services.thread_lock.implementation import RedisThreadLock
import time

scheduler = BackgroundScheduler()

WEBHOOK_LOCK_KEY = "starkbank_webhook_lock"
WEBHOOK_ID_KEY = "starkbank_webhook_id"
GET_WEBHOOK_ID_DELAY = 3
MAX_GET_WEBHOOK_ID_ATTEMPTS = 20


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = redis.from_url(settings.REDIS_URL)
    try:
        redis_client.ping()
    except redis.ConnectionError as e:
        raise

    starkbank.user = settings.starkbank_project
    webhook_url = settings.starkbank_invoices_webhook_url
    webhook_id = None

    webhook_id = redis_client.get(WEBHOOK_ID_KEY)
    if webhook_id:
        webhook_id = webhook_id.decode("utf-8")

    main_thread = False
    if webhook_id is None:
        thread_lock = RedisThreadLock(redis_client)
        if thread_lock.lock(WEBHOOK_LOCK_KEY):
            main_thread = True
            webhooks = starkbank.webhook.query()
            for webhook in webhooks:
                if webhook.url == webhook_url:
                    webhook_id = webhook.id
                    break

            if webhook_id is None:
                webhook = starkbank.webhook.create(
                    url=webhook_url,
                    subscriptions=["invoice"],
                )
                webhook_id = webhook.id

            if webhook_id:
                redis_client.set(WEBHOOK_ID_KEY, webhook_id)

            thread_lock.unlock(WEBHOOK_LOCK_KEY)

    scheduler.add_job(
        lambda: transfer_starkbank_undelivered_credited_invoices(
            RedisThreadLock(redis_client)
        ),
        "cron",
        hour=1,
    )

    scheduler.add_job(
        lambda: invoice_random_people(8, 12, RedisThreadLock(redis_client)),
        "interval",
        hours=3,
    )

    scheduler.start()

    # the other threads will wait for the webhook ID to be set
    get_webhook_id_attempts = 0
    while webhook_id is None and get_webhook_id_attempts < MAX_GET_WEBHOOK_ID_ATTEMPTS:
        time.sleep(GET_WEBHOOK_ID_DELAY)
        webhook_id = redis_client.get(WEBHOOK_ID_KEY)
        if webhook_id:
            webhook_id = webhook_id.decode("utf-8")
        get_webhook_id_attempts += 1

    # if the webhook ID is not set, it will raise an exception
    if webhook_id is None:
        raise Exception("Could not get webhook ID")

    print(f"Using webhook with ID: {webhook_id}")

    yield
    scheduler.shutdown()

    if main_thread:
        if settings.ENVIRONMENT == "development":
            print("Cleaning up Starkbank Invoices Webhook")
            redis_client.delete(WEBHOOK_ID_KEY)
            starkbank.webhook.delete(webhook_id)


app = FastAPI(
    title="Stark Bank Challenge API",
    description="API for a client that uses Stark Bank (or any other implemented bank)",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(health.router, prefix="/health", tags=["health"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
