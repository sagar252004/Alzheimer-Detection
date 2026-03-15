from pymongo import MongoClient
import os

# MongoDB Atlas connection string
MONGO_URI = "mongodb+srv://sagarrv152_db_user:ZT54gSFR8LedNnC9@cluster0.qnidgrt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# connect to MongoDB
client = MongoClient(MONGO_URI)

# database
db = client["alzheimers_db"]

# collection
patients_collection = db["patients"]

print("✅ MongoDB connected successfully")