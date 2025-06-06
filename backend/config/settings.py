import os
import json
from dotenv import load_dotenv

load_dotenv()


WEBHOOK_URL = os.getenv("WEBHOOK_URL")
INTEGRATION_URL = os.getenv("INTEGRATION_URL")
INTEGRATION_CODE = os.getenv("INTEGRATION_CODE")
INTEGRATION_TOKEN = os.getenv("INTEGRATION_TOKEN")

with open('config/scheme.json', 'r', encoding='utf-8') as f:
    SCHEME = json.load(f)


POSTGRES_URL=os.getenv("POSTGRES_URL")
POSTGRES_USER=os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB=os.getenv("POSTGRES_DB")
FERNET_KEY=os.getenv("FERNET_KEY")
POSTGRES_CONNECTION_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_URL}/{POSTGRES_DB}"


REDIS_URL=os.getenv("REDIS_URL")
REDIS_PASSWORD=os.getenv("REDIS_PASSWORD")
REDIS_CACHE_TIME=os.getenv("REDIS_CACHE_TIME", "86400")
REDIS_CONNECTION_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_URL}"

PROMETHEUS_JOBS_PATH = os.getenv("PROMETHEUS_JOBS_PATH", "/app/shared/jobs.json")

#TODO Remove when get from constructor db

USER_NAME=os.getenv("USER_NAME")
USER_EMAIL=os.getenv("USER_EMAIL")

