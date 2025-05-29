import requests
from dotenv import load_dotenv
import os
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

def send_message(chat_id: str, text: str):
    payload = {"chat_id": chat_id, "text": text}

    send_message_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    response = requests.post(send_message_url, json=payload)
    
    response.raise_for_status()