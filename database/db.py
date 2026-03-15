from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")

client = MongoClient(mongo_uri)

# Check connection
client.server_info()

db = client["alzheimers_db"]
patients_collection = db["patients"]

print("✅ MongoDB Atlas connected successfully")