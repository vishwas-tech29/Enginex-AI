from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import router as v1_router
from app.config import settings
from app.core.logging import setup_logging
from app.core.rate_limit import limiter
from app.middleware.error_handler import rate_limit_exceeded_handler, register_error_handlers
from app.middleware.logging import register_request_logging
from app.websockets.ai_streaming import router as ai_websocket_router
from app.websockets.handlers import router as websocket_router

setup_logging()

app = FastAPI(title=settings.app_name, version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
register_request_logging(app)
app.include_router(v1_router)
app.include_router(websocket_router)
app.include_router(ai_websocket_router)


@app.get("/health")
async def healthcheck():
    return {"status": "ok"}
