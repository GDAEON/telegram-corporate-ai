import logging
import os

from logging_loki import LokiHandler

LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)


handlers = [
    logging.FileHandler(os.path.join(LOG_DIR, "interactions.log")),
    logging.StreamHandler(),
]

loki_url = os.getenv("LOKI_URL")
if loki_url:
    handlers.append(
        LokiHandler(
            url=f"{loki_url.rstrip('/')}/loki/api/v1/push",
            tags={"app": "telegram-corp-ai"},
            version="1",
        )
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=handlers,
)

interaction_logger = logging.getLogger("interaction")
