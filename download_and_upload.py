import asyncio
import random
import nest_asyncio

from main import automated_posting
from generate_homepage import generate_site
from config import POST_INTERVAL_MIN, POST_INTERVAL_MAX

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
    
    # Run the main automated posting loop
    asyncio.run(main())