from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.resolution import router as resolution_router
from app.core.config import get_settings
from app.services.evidence_retrieval import get_embedding_model

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_embedding_model()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    resolution_router,
    prefix="/api/v1",
)


@app.get("/api/v1/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}