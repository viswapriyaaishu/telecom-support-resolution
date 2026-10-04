from fastapi import FastAPI

from app.api.routes.resolution import router as resolution_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(
    resolution_router,
    prefix="/api/v1",
)


@app.get("/api/v1/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}