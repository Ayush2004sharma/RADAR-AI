from .redis_stream import read_logs
from .aggregator import increment_error
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import time

load_dotenv()

def start_consumer():
    mongo = MongoClient(os.getenv("MONGO_URI"))
    db = mongo[os.getenv("MONGO_DB")]
    logs_collection = db[os.getenv("MONGO_COLLECTION")]

    last_id = "0-0"

    print("Consumer started...")

    while True:
        streams = read_logs(last_id)

        for stream, messages in streams:
            for msg_id, log in messages:
                print("Consumed:", log)

                logs_collection.insert_one(log)

                if log.get("level") == "ERROR":
                    increment_error(log.get("service"))

                last_id = msg_id

        time.sleep(0.1)

if __name__ == "__main__":
    start_consumer()
