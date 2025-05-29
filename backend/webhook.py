import requests

def set_webhook(TOKEN: str, WEBHOOK_URL:str):
    response = requests.post(f'https://api.telegram.org/bot{TOKEN}/setWebhook', data={"url": WEBHOOK_URL})

    return response.status_code

