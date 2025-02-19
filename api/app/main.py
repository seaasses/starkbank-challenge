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

    main_thread = False
    if webhook_id is None:
        print(
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        )
        if redis_client.set(WEBHOOK_LOCK_KEY, "1", nx=True, ex=30):
            # this is the main worker on all workers/instances
            # it will create the webhook and run the jobs
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

            # 01:00 AM (UTC-3)
            # TODO: as env variable
            scheduler.add_job(
                transfer_starkbank_undelivered_credited_invoices, "cron", hour=1
            )

            scheduler.add_job(
                lambda: invoice_random_people(n_min=8, n_max=12),
                "interval",
                minutes=1,
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
    print("baakda")

    yield

    if main_thread:

        # only the main thread started the scheduler
        scheduler.shutdown()

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
app.include_router(invoices.router, prefix="/api/v1/invoices", tags=["invoices"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(health.router, prefix="/health", tags=["health"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
