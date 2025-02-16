from fastapi import FastAPI
from app.api.v1.endpoints import invoices
from app.api.v1.endpoints import webhooks
import starkbank
import redis
from app.core.config import settings
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from app.jobs.transfer_starkbank_undelivered_credited_invoices import (
    transfer_starkbank_undelivered_credited_invoices,
)
from app.jobs.invoice_random_people import invoice_random_people

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Test Redis connection
    redis_client = redis.from_url(settings.REDIS_URL)
    try:
        redis_client.ping()
    except redis.ConnectionError as e:
        raise

    starkbank.user = settings.starkbank_project

    webhooks = starkbank.webhook.query()

    webhook_url = settings.starkbank_invoices_webhook_url

    webhook_id = None
    for webhook in webhooks:
        if webhook.url == webhook_url:
            webhook_id = webhook.id
            break

    if webhook_id is None:
        print("Creating Starkbank invoices webhook url:", webhook_url)
        webhook = starkbank.webhook.create(
            url=webhook_url,
            subscriptions=["invoice"],
        )
        webhook_id = webhook.id
    else:
        print("Starkbank invoices webhook url:", webhook_url)

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
