import os
import json
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

with open('config/scheme.json', 'r', encoding='utf-8') as f:
    SCHEME = json.load(f)

#TODO Move to PostgreSQL Database
BOT_TOKENS: dict[int, str] = {}