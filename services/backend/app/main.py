from fastapi import FastAPI
from app.api.v1.router import router as v1_router

app = FastAPI(title="Enginex AI API", version="1.0.0")
app.include_router(v1_router)

@app.get("/health")
async def healthcheck():
    return {"status": "ok"}
