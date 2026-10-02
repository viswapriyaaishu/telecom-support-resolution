from fastapi import FastAPI

app = FastAPI(
    title="Telecom Support Resolution API",
    version="0.1.0",
)


@app.get("/api/v1/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}