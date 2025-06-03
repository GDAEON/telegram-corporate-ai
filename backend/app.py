from fastapi import FastAPI, Request
from routers.telegram import router as telegram_router
from routers.constructor import router as constructor_router
from routers.api import router as api_router
from routers.metrics import router as metrics_router

import time
from constants.prometheus_models import REQUEST_COUNT, REQUEST_LATENCY

app = FastAPI(
    title="Telegram CORP AI Integration API",
)

app.include_router(telegram_router)
app.include_router(constructor_router)
app.include_router(api_router)
app.include_router(metrics_router)

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    method = request.method
    endpoint = request.url.path

    start = time.time()
    response = await call_next(request)
    latency = time.time() - start

    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)

    return response