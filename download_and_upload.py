import asyncio
import nest_asyncio

from main import automated_posting
from generate_homepage import generate_site

async def main():
    print("Starting automated content processing...")
    await automated_posting()
    
    print("Starting website generation...")
    await generate_site()

if __name__ == "__main__":
    # nest_asyncio is used to allow running asyncio loops within other loops,
    # which can be common in interactive environments or when scripts are run in certain ways.
    nest_asyncio.apply()
    
    # Run the main automated posting loop
    asyncio.run(main())