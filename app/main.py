from fastapi import FastAPI
from app.api.v1.endpoints import invoices

app = FastAPI(
    title="Stark Bank Challenge API",
    description="API for a client that uses Stark Bank (or any other implemented bank)",
    version="1.0.0",
)

# Include routers
app.include_router(invoices.router, prefix="/api/v1/invoices", tags=["invoices"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
