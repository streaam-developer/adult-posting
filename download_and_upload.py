import asyncio
import random
import nest_asyncio
import os
import threading
import uvicorn

from main import automated_posting
from generate_homepage import generate_site
from config import POST_INTERVAL_MIN, POST_INTERVAL_MAX

def run_fastapi_server():
    uvicorn.run("api:app", host="0.0.0.0", port=8000, log_level="info")

async def main():
    while True:
        print("Starting automated content processing...")
        await automated_posting()
        
        print("Starting website generation...")
        await generate_site()
        
        # Wait for a random interval before the next post
        sleep_time = random.randint(POST_INTERVAL_MIN, POST_INTERVAL_MAX)
        print(f"Waiting for {sleep_time} seconds until the next run...")
        await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    nest_asyncio.apply()

    # Start the FastAPI server in a separate thread
    server_thread = threading.Thread(target=run_fastapi_server)
    server_thread.daemon = True
    server_thread.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")