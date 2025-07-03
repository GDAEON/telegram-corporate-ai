from pymongo import MongoClient

from config.settings import MONGO_HOST, MONGO_USERNAME, MONGO_PASSWORD, MONGO_DB

uri = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}"

client = MongoClient(uri)
db = client[MONGO_DB]

def insert_message(
        source: str,
        bot_id: int, 
        user_id: int, 
        message_id: int, 
        participant_name: str, 
        text: str = "", 
        attachments: list = [], 
        received_body: dict = {}, 
        sent_body: dict = {}
        ) -> None:
    collection = db[source]

    document = {
        'bot_id': bot_id,
        'user_id': user_id,
        'message_id': message_id,
        'participant_name': participant_name,
        'text': text,
        'attachments': attachments,
        'received_body': received_body,
        'sent_body': sent_body
    }

    collection.insert_one(document)