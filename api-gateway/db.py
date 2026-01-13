from pymongo import MongoClient
import os

client = None
db = None

def init_db():
    global client, db
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise RuntimeError("MONGO_URI not set in environment")

    client = MongoClient(mongo_uri)
    db = client["radar_ai"]
