from fastapi import FastAPI
from app.api.v1.endpoints import invoices
from app.api.v1.endpoints import webhooks
import starkbank
from app.core.config import settings
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
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

    yield

    if settings.ENVIRONMENT == "development":
        print("Cleaning up Starkbank Invoices Webhook")
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
