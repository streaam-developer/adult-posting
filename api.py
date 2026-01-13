from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME, COLLECTION_NAME
import pymongo
from datetime import datetime

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
        post['page_url'] = f"/posts/{post['_id']}.html"
        
    return posts

@app.get("/api/search")
async def search_posts(query: str = "", category: str = "", date_from: str = "", date_to: str = "", page: int = 1, page_size: int = 10):
    find_query = {}
    if query:
        find_query["$text"] = {"$search": query}
    if category:
        find_query["category"] = category
    if date_from or date_to:
        date_query = {}
        if date_from:
            date_query["$gte"] = datetime.fromisoformat(date_from)
        if date_to:
            date_query["$lte"] = datetime.fromisoformat(date_to)
        find_query["upload_date"] = date_query

    skip = (page - 1) * page_size
    cursor = collection.find(find_query).skip(skip).limit(page_size).sort("processed_at", pymongo.DESCENDING)
    posts = await cursor.to_list(length=page_size)

    # Convert ObjectId to string for JSON serialization
    for post in posts:
        post['_id'] = str(post['_id'])
        post['page_url'] = f"/posts/{post['_id']}.html"

    total_results = await collection.count_documents(find_query)

    return {"posts": posts, "total_results": total_results}

app.mount("/", StaticFiles(directory="site", html=True), name="site")

