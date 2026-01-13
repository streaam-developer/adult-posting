import asyncio
import nest_asyncio

from main import automated_posting

if __name__ == "__main__":
    print("Starting automated content processing and website generation...")
    
    # nest_asyncio is used to allow running asyncio loops within other loops,
    # which can be common in interactive environments or when scripts are run in certain ways.
    nest_asyncio.apply()
    
    # Run the main automated posting loop
    asyncio.run(automated_posting())