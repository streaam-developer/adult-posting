import os
import re
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME, COLLECTION_NAME

async def extract_and_update_upload_dates():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    posts_dir = 'site/posts'
    for filename in os.listdir(posts_dir):
        if filename.endswith('.html'):
            post_id = filename[:-5]  # Remove .html
            filepath = os.path.join(posts_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Extract uploadDate using regex
            match = re.search(r'<meta itemprop="uploadDate" content="([^"]+)"', html_content)
            if match:
                upload_date_str = match.group(1)
                try:
                    # Parse the datetime, handling timezone
                    upload_date = datetime.fromisoformat(upload_date_str)
                    # Update DB
                    await collection.update_one(
                        {'_id': ObjectId(post_id)},
                        {'$set': {'upload_date': upload_date}}
                    )
                    print(f"Updated {post_id} with upload_date {upload_date}")
                except ValueError as e:
                    print(f"Failed to parse upload_date for {post_id}: {upload_date_str} - {e}")
            else:
                print(f"No uploadDate found in {filename}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(extract_and_update_upload_dates())