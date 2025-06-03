from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from fastapi import Response, APIRouter
from constants.prometheus_models import registry

router = APIRouter(tags=['Metrics'])

@router.get("/metrics")
async def metrics():
    data = generate_latest(registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
