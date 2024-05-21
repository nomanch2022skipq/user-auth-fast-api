from motor.motor_asyncio import AsyncIOMotorClient


client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["Fast_api_db"]
user_collection = db["user_crud"]
post_collection = db["post_crud"]