import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

client = None
db = None


@asynccontextmanager
async def lifespan(app):
    global client, db
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB URI is not required")
    
    client = AsyncIOMotorClient(uri)
    await client.admin.command("ping")

    db = client(os.getenv("MONGODB_DB", "inventory"))
    await db.products.create_index(
        [("sku", ASC)],
        unqiue = True
    )

    await db.orders.create()

    yield
    client.close()
    
