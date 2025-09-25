import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGO_URI")
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["telegram_bot_db"]
groups_collection = db["tag_groups"]
