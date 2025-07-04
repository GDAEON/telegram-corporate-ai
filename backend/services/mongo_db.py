from pymongo import MongoClient

from config.settings import MONGO_HOST, MONGO_USERNAME, MONGO_PASSWORD, MONGO_DB

uri = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}"

client = MongoClient(uri)
db = client[str(MONGO_DB)]

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

def save_variable(bot_id: int, user_id: int, name: str, value: any):
    collection = db['variables']

    filter = {
        'bot_id': bot_id,
        'user_id': user_id,
        'name': name
    }

    update = {
        "$set":
            {
                'bot_id': bot_id,
                'user_id': user_id,
                'name': name,
                'value': value
            }
    }

    collection.update_one(filter, update, upsert=True)

def get_variable(bot_id: int, user_id: int, name: str) -> str:
    collection = db['variables']

    document = collection.find_one({
        'bot_id': bot_id,
        'user_id': user_id,
        'name': name
    })

    if document is None:
        return ""

    return str(document['value'])
