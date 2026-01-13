import asyncio
import random
import nest_asyncio
import os
import multiprocessing
from http.server import HTTPServer, SimpleHTTPRequestHandler

from main import automated_posting
from generate_homepage import generate_site
from config import POST_INTERVAL_MIN, POST_INTERVAL_MAX

def start_server():
    os.chdir('site')
    server = HTTPServer(('127.0.0.1', 8000), SimpleHTTPRequestHandler)
    server.serve_forever()

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
    # nest_asyncio is used to allow running asyncio loops within other loops,
    # which can be common in interactive environments or when scripts are run in certain ways.
    nest_asyncio.apply()

    # Start the web server in a separate process
    multiprocessing.Process(target=start_server, daemon=True).start()

    # Run the main automated posting loop
    asyncio.run(main())