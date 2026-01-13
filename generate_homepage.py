import asyncio
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

from config import MONGO_URI, DB_NAME, COLLECTION_NAME

async def generate_homepage():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    posts = await collection.find({'url': {'$exists': True}}).to_list(None)
    posts.sort(key=lambda x: x.get('processed_at', 0), reverse=True)

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Adult Posting Homepage</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .post { border: 1px solid #ccc; margin: 10px; padding: 10px; display: inline-block; width: 300px; vertical-align: top; background-color: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .thumbnail { max-width: 100%; height: auto; border-radius: 5px; }
        h1 { text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>All Posts</h1>
"""
    for post in posts:
        title = post.get('title', 'No Title')
        description = post.get('description', 'No Description')[:200] + '...'
        upload_date = post.get('upload_date')
        if upload_date:
            try:
                dt = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                human_date = dt.strftime('%B %d, %Y at %I:%M %p')
            except:
                human_date = upload_date
        else:
            human_date = 'Unknown'
        thumbnail_path = post.get('thumbnail_local_path')
        if thumbnail_path and os.path.exists(thumbnail_path):
            img_tag = f'<img src="{thumbnail_path}" alt="Thumbnail" class="thumbnail">'
        else:
            img_tag = '<p>No Thumbnail</p>'
        html += f"""
        <div class="post">
            {img_tag}
            <h2>{title}</h2>
            <p>{description}</p>
            <p><strong>Uploaded:</strong> {human_date}</p>
        </div>
"""
    html += """
    </div>
</body>
</html>
"""
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Homepage generated: index.html")

if __name__ == '__main__':
    asyncio.run(generate_homepage())