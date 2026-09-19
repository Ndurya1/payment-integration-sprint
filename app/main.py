from fastapi import FastAPI
from app.config import settings
from app.payments.routes import router as payments_router

app = FastAPI(
    title="payment intergration API",
    version="1.0.0",
    description="daraja payments intergration learning sprint"
)

app.include_router(payments_router, prefix="/payments", tags=["payments"])

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "fleet-api",
        "cors_origins": settings.allowed_origins,
    }