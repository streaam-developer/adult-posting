from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME, COLLECTION_NAME
import pymongo

app = FastAPI()

# MongoDB connection
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

@app.on_event("startup")
async def startup_event():
    await collection.create_index([("title", pymongo.TEXT), ("description", pymongo.TEXT)])

@app.get("/api/posts")
async def get_posts(page: int = 1, page_size: int = 10):
    skip = (page - 1) * page_size
    cursor = collection.find().skip(skip).limit(page_size).sort("processed_at", pymongo.DESCENDING)
    posts = await cursor.to_list(length=page_size)
    
    # Convert ObjectId to string for JSON serialization
    for post in posts:
        post['_id'] = str(post['_id'])
        
    return posts

@app.get("/api/search")
async def search_posts(query: str):
    cursor = collection.find({"$text": {"$search": query}})
    posts = await cursor.to_list(length=None)
    
    # Convert ObjectId to string for JSON serialization
    for post in posts:
        post['_id'] = str(post['_id'])
        
    return posts

app.mount("/", StaticFiles(directory="site", html=True), name="site")
