from pymongo import MongoClient

# MongoDB Atlas connection string
MONGO_URI = "mongodb+srv://sagarrv152_db_user:ZT54gSFR8LedNnC9@cluster0.qnidgrt.mongodb.net/alzheimers_db?retryWrites=true&w=majority&appName=Cluster0"

# Connect to MongoDB
client = MongoClient(MONGO_URI)

# Database
db = client["alzheimers_db"]

# Collection
patients_collection = db["patients"]

print("✅ MongoDB Atlas connected successfully")